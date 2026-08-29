from __future__ import annotations

import asyncio
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.agents.sentiment import run_sentiment_agent
from app.agents.strategy import (
    apply_demo_tick,
    apply_pause,
    compute_metrics,
    load_base_ads,
    run_strategy_agent,
)
from app.auth import (
    APPROVER_ROLES,
    WRITER_ROLES,
    AuthUser,
    WorkspaceContext,
    auth_enabled,
    ensure_default_workspace,
    get_current_user,
    get_workspace_context,
    require_role,
)
from app.config import settings
from app.db import SessionLocal, get_db
from app.events import event_bus
from app.integrations.meta.context import resolve_publish_context
from app.integrations.meta.metrics_sync import sync_campaign_metrics
from app.integrations.meta.pause import pause_meta_structure
from app.jobs.enqueue import enqueue_campaign_pipeline, enqueue_metrics_sync
from app.models import AgentRun, Campaign, Recommendation, SignalSnapshot, Workspace, WorkspaceMember, utcnow
from app.models import ActionEvent
from app.schemas import (
    ApprovalAction,
    AudienceSelectRequest,
    AutoPauseUpdate,
    CampaignCreate,
    CampaignDetail,
    CampaignOut,
    DemoTickRequest,
    MeOut,
    OptimizationTickRequest,
    OptimizationUpdateRequest,
    RecommendationOut,
    WorkspaceCreate,
    WorkspaceOut,
)
from app.serializers import build_campaign, campaign_to_out
from app.services.actions import log_action
from app.services.audiences import apply_audience_selection, build_audience_state, enrich_audiences_with_llm
from app.services.meta_publish import (
    build_draft_for_workspace,
    mark_in_review,
    publish_structure,
)
from app.services.optimization import (
    init_optimization_from_structure,
    run_optimization_tick,
    update_rules,
)
from app.services.orchestrator import approve_recommendation, reject_recommendation, run_pipeline

router = APIRouter()


def _agent_out(run: AgentRun) -> dict:
    return {
        "id": run.id,
        "campaign_id": run.campaign_id,
        "agent": run.agent,
        "health": run.health,
        "payload": run.payload,
        "message": run.message,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
    }


def _rec_out(r: Recommendation) -> dict:
    return {
        "id": r.id,
        "campaign_id": r.campaign_id,
        "type": r.type,
        "status": r.status,
        "title": r.title,
        "detail": r.detail,
        "created_at": r.created_at,
    }


def _signal_out(s: SignalSnapshot) -> dict:
    return {
        "campaign_id": s.campaign_id,
        "creative_ready": s.creative_ready,
        "brand_sentiment": s.brand_sentiment,
        "roas": s.roas,
        "spend_burn": s.spend_burn,
        "spend": s.spend,
        "updated_at": s.updated_at,
    }


async def _get_campaign_in_workspace(
    db: AsyncSession, campaign_id: str, workspace_id: str
) -> Campaign:
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.workspace_id == workspace_id,
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    return campaign


async def _pipeline_job(campaign_id: str) -> None:
    async with SessionLocal() as db:
        result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
        campaign = result.scalar_one_or_none()
        if not campaign:
            return
        await run_pipeline(db, campaign)


async def _schedule_pipeline(campaign_id: str, background: BackgroundTasks) -> None:
    """Prefer ARQ worker when Redis is configured; fall back to in-process background task."""
    if not await enqueue_campaign_pipeline(campaign_id):
        background.add_task(_pipeline_job, campaign_id)


@router.get("/health")
async def health():
    from app.services.llm import llm_enabled, llm_provider
    from app.redis_client import redis_health

    db_ok = True
    db_detail = "ok"
    try:
        async with SessionLocal() as session:
            await session.execute(select(Campaign.id).limit(1))
    except Exception as exc:
        db_ok = False
        db_detail = str(exc)[:200]

    storage_ok = True
    try:
        if settings.effective_storage_backend() == "r2":
            storage_ok = settings.r2_configured()
        else:
            settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        storage_ok = False

    redis_status = await redis_health()
    using_postgres = not str(settings.database_url).startswith("sqlite")

    return {
        "ok": db_ok and storage_ok,
        "service": "adzmate-api",
        "environment": settings.environment,
        "auth_enabled": auth_enabled(),
        "database": {
            "ok": db_ok,
            "engine": "postgresql" if using_postgres else "sqlite",
            "detail": db_detail,
            "migrations": "alembic" if using_postgres else "sqlite_create_all",
        },
        "storage": {
            "ok": storage_ok,
            "backend": settings.effective_storage_backend(),
        },
        "redis": redis_status,
        "llm_enabled": llm_enabled(),
        "llm_provider": llm_provider() if llm_enabled() else None,
        "llm_model": settings.llm_model if llm_enabled() else None,
        "ai_images": settings.use_ai_images,
        "token_encryption": bool(settings.token_encryption_key),
        "meta_oauth_configured": bool(settings.meta_app_id and settings.meta_app_secret),
        "capabilities": {
            "orchestrator": "real",
            "creative_agent": "real",
            "sentiment_agent": "real",
            "strategy_agent": "real",
            "signal_aggregator": "real",
            "landing_deployer": settings.effective_storage_backend(),
            "llm_enrichment": "real" if llm_enabled() else "offline_templates",
            "ad_platform_metrics": "simulated_fixtures",
            "meta_campaign_publish": "simulated_ids",
            "meta_oauth": "real" if (settings.meta_app_id and settings.meta_app_secret) else "demo_connect",
            "auto_pause": "supported",
        },
    }


@router.get("/me", response_model=MeOut)
async def me(
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await ensure_default_workspace(db, user)
    rows = (
        await db.execute(
            select(WorkspaceMember, Workspace)
            .join(Workspace, Workspace.id == WorkspaceMember.workspace_id)
            .where(WorkspaceMember.user_id == user.id)
            .order_by(Workspace.created_at.asc())
        )
    ).all()
    workspaces = [
        WorkspaceOut(id=ws.id, name=ws.name, role=member.role, created_at=ws.created_at)
        for member, ws in rows
    ]
    return MeOut(
        id=user.id,
        email=user.email,
        auth_enabled=auth_enabled(),
        workspaces=workspaces,
    )


@router.get("/workspaces", response_model=list[WorkspaceOut])
async def list_workspaces(
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await ensure_default_workspace(db, user)
    rows = (
        await db.execute(
            select(WorkspaceMember, Workspace)
            .join(Workspace, Workspace.id == WorkspaceMember.workspace_id)
            .where(WorkspaceMember.user_id == user.id)
            .order_by(Workspace.created_at.asc())
        )
    ).all()
    return [
        WorkspaceOut(id=ws.id, name=ws.name, role=member.role, created_at=ws.created_at)
        for member, ws in rows
    ]


@router.post("/workspaces", response_model=WorkspaceOut)
async def create_workspace(
    body: WorkspaceCreate,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspace = Workspace(
        id=str(uuid.uuid4()),
        name=body.name.strip() or "My Workspace",
        created_by=user.id,
    )
    db.add(workspace)
    db.add(
        WorkspaceMember(
            id=str(uuid.uuid4()),
            workspace_id=workspace.id,
            user_id=user.id,
            role="owner",
        )
    )
    await db.commit()
    await db.refresh(workspace)
    return WorkspaceOut(
        id=workspace.id,
        name=workspace.name,
        role="owner",
        created_at=workspace.created_at,
    )


@router.get("/campaigns", response_model=list[CampaignOut])
async def list_campaigns(
    ctx: WorkspaceContext = Depends(get_workspace_context),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Campaign)
        .where(Campaign.workspace_id == ctx.workspace.id)
        .order_by(Campaign.created_at.desc())
    )
    return [campaign_to_out(c) for c in result.scalars().all()]


@router.post("/campaigns", response_model=CampaignOut)
async def create_campaign(
    background: BackgroundTasks,
    payload: str = Form(...),
    product_image: UploadFile | None = File(None),
    ctx: WorkspaceContext = Depends(require_role(*WRITER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    import json
    from io import BytesIO

    from PIL import Image

    from app.storage import get_storage

    data = CampaignCreate.model_validate(json.loads(payload))
    campaign_id = str(uuid.uuid4())
    image_path = None

    if product_image and product_image.filename:
        raw = await product_image.read()
        max_bytes = settings.max_upload_mb * 1024 * 1024
        if len(raw) > max_bytes:
            raise HTTPException(400, f"Product image must be under {settings.max_upload_mb}MB")
        content_type = (product_image.content_type or "").lower()
        if content_type and not content_type.startswith("image/"):
            raise HTTPException(400, "Product file must be an image")
        try:
            img = Image.open(BytesIO(raw))
            img.verify()
            img = Image.open(BytesIO(raw)).convert("RGBA")
        except Exception as exc:
            raise HTTPException(400, f"Invalid image upload: {exc}") from exc

        img.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
        buf = BytesIO()
        img.save(buf, "PNG")
        storage = get_storage()
        key = storage.upload_key(campaign_id)
        await storage.save(key, buf.getvalue(), content_type="image/png")
        image_path = key

    campaign = build_campaign(
        campaign_id=campaign_id,
        workspace_id=ctx.workspace.id,
        data=data,
        product_image_path=image_path,
        mock_ads=load_base_ads(data.scenario),
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)

    if not await enqueue_campaign_pipeline(campaign_id):
        background.add_task(_pipeline_job, campaign_id)
    return campaign_to_out(campaign)


@router.post("/campaigns/json", response_model=CampaignOut)
async def create_campaign_json(
    data: CampaignCreate,
    background: BackgroundTasks,
    ctx: WorkspaceContext = Depends(require_role(*WRITER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """JSON-only create (no image) for quick demos / seed."""
    campaign_id = str(uuid.uuid4())
    campaign = build_campaign(
        campaign_id=campaign_id,
        workspace_id=ctx.workspace.id,
        data=data,
        mock_ads=load_base_ads(data.scenario),
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    if not await enqueue_campaign_pipeline(campaign_id):
        background.add_task(_pipeline_job, campaign_id)
    return campaign_to_out(campaign)


@router.get("/campaigns/{campaign_id}", response_model=CampaignDetail)
async def get_campaign(
    campaign_id: str,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    db: AsyncSession = Depends(get_db),
):
    campaign = await _get_campaign_in_workspace(db, campaign_id, ctx.workspace.id)
    agents = (
        await db.execute(select(AgentRun).where(AgentRun.campaign_id == campaign_id))
    ).scalars().all()
    signals = (
        await db.execute(select(SignalSnapshot).where(SignalSnapshot.campaign_id == campaign_id))
    ).scalar_one_or_none()
    recs = (
        await db.execute(
            select(Recommendation)
            .where(Recommendation.campaign_id == campaign_id)
            .order_by(Recommendation.created_at.desc())
        )
    ).scalars().all()
    actions = (
        await db.execute(
            select(ActionEvent)
            .where(ActionEvent.campaign_id == campaign_id)
            .order_by(ActionEvent.created_at.desc())
            .limit(80)
        )
    ).scalars().all()
    return {
        "campaign": campaign_to_out(campaign),
        "agents": [_agent_out(a) for a in agents],
        "signals": _signal_out(signals) if signals else None,
        "recommendations": [_rec_out(r) for r in recs],
        "timeline": [
            {
                "id": e.id,
                "campaign_id": e.campaign_id,
                "actor": e.actor,
                "action": e.action,
                "summary": e.summary,
                "detail": e.detail,
                "level": e.level,
                "created_at": e.created_at,
            }
            for e in actions
        ],
    }


@router.post("/campaigns/{campaign_id}/meta/rebuild-draft", response_model=CampaignOut)
async def rebuild_meta_draft(
    campaign_id: str,
    ctx: WorkspaceContext = Depends(require_role(*WRITER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """Rebuild Meta campaign/ad set/ads draft from creatives + selected audiences."""
    campaign = await _get_campaign_in_workspace(db, campaign_id, ctx.workspace.id)
    if (campaign.publish_status or "none") == "published":
        raise HTTPException(400, "Campaign already published — pause/create a new draft instead")
    creative = (
        await db.execute(
            select(AgentRun).where(AgentRun.campaign_id == campaign_id, AgentRun.agent == "creative")
        )
    ).scalar_one_or_none()
    assets = (creative.payload if creative else {}).get("assets") or []
    if not (campaign.audiences or {}).get("recommended"):
        campaign.audiences = build_audience_state(
            campaign, (creative.payload if creative else {}).get("audience_suggestions")
        )
    campaign.meta_structure = await build_draft_for_workspace(
        db, campaign, assets=assets, workspace_id=ctx.workspace.id
    )
    campaign.publish_status = "draft"
    await db.commit()
    await db.refresh(campaign)
    return campaign_to_out(campaign)


@router.post("/campaigns/{campaign_id}/meta/submit-review", response_model=CampaignOut)
async def submit_meta_review(
    campaign_id: str,
    ctx: WorkspaceContext = Depends(require_role(*WRITER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    campaign = await _get_campaign_in_workspace(db, campaign_id, ctx.workspace.id)
    if not campaign.meta_structure:
        raise HTTPException(400, "No Meta draft — rebuild draft first")
    campaign.meta_structure = mark_in_review(campaign.meta_structure)
    campaign.publish_status = "in_review"
    await db.commit()
    await db.refresh(campaign)
    return campaign_to_out(campaign)


@router.post("/campaigns/{campaign_id}/meta/publish", response_model=CampaignOut)
async def publish_meta_campaign(
    campaign_id: str,
    ctx: WorkspaceContext = Depends(require_role(*APPROVER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """Publish Meta draft without going through recommendation (manual publish)."""
    campaign = await _get_campaign_in_workspace(db, campaign_id, ctx.workspace.id)
    if not campaign.meta_structure:
        raise HTTPException(400, "No Meta draft to publish")
    if (campaign.publish_status or "") == "published":
        return campaign_to_out(campaign)
    publish_ctx = await resolve_publish_context(db, ctx.workspace.id)
    published = await publish_structure(campaign.meta_structure, publish_ctx=publish_ctx)
    campaign.meta_structure = published
    campaign.publish_status = "published"
    daily = float(getattr(campaign, "daily_budget", None) or 20.0)
    campaign.optimization = init_optimization_from_structure(published, daily)
    if campaign.status in ("awaiting_approval", "received", "draft"):
        campaign.status = "live"
        campaign.decision = campaign.decision or "LAUNCH"
    await db.commit()
    await db.refresh(campaign)
    return campaign_to_out(campaign)


@router.post("/campaigns/{campaign_id}/meta/sync-metrics", response_model=CampaignOut)
async def sync_meta_metrics(
    campaign_id: str,
    ctx: WorkspaceContext = Depends(require_role(*WRITER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """Pull live spend/ROAS from Meta Insights into campaign metrics (requires connected Meta account)."""
    campaign = await _get_campaign_in_workspace(db, campaign_id, ctx.workspace.id)
    publish_ctx = await resolve_publish_context(db, ctx.workspace.id)
    if not publish_ctx:
        raise HTTPException(
            400,
            "No connected Meta ad account in this workspace. Connect Meta under Account settings.",
        )
    try:
        ads = await fetch_account_insights(publish_ctx)
    except Exception as exc:
        raise HTTPException(400, f"Meta Insights sync failed: {exc}") from exc
    campaign.mock_ads = ads
    metrics = compute_metrics(ads)
    snap = (
        await db.execute(select(SignalSnapshot).where(SignalSnapshot.campaign_id == campaign_id))
    ).scalar_one_or_none()
    if snap:
        snap.spend = metrics["spend"]
        snap.roas = metrics["roas"]
        snap.spend_burn = metrics["spend_burn"]
        snap.updated_at = utcnow()
    await log_action(
        db,
        campaign.id,
        actor="strategy",
        action="meta_metrics_synced",
        summary=f"Synced Meta Insights — ROAS {metrics['roas']:.2f}x",
        detail=f"Spend ${metrics['spend']:.0f} · Revenue ${metrics['revenue']:.0f}",
        level="info",
    )
    await db.commit()
    await db.refresh(campaign)
    return campaign_to_out(campaign)


@router.post("/campaigns/{campaign_id}/audiences/select", response_model=CampaignOut)
async def select_audiences(
    campaign_id: str,
    body: AudienceSelectRequest,
    ctx: WorkspaceContext = Depends(require_role(*WRITER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    campaign = await _get_campaign_in_workspace(db, campaign_id, ctx.workspace.id)
    state = campaign.audiences or build_audience_state(campaign)
    campaign.audiences = apply_audience_selection(state, body.selected_ids)
    # Rebuild draft targeting if still editable
    if (campaign.publish_status or "none") in ("none", "draft", "in_review"):
        creative = (
            await db.execute(
                select(AgentRun).where(AgentRun.campaign_id == campaign_id, AgentRun.agent == "creative")
            )
        ).scalar_one_or_none()
        assets = (creative.payload if creative else {}).get("assets") or []
        if assets or campaign.meta_structure:
            campaign.meta_structure = await build_draft_for_workspace(
                db, campaign, assets=assets, workspace_id=ctx.workspace.id
            )
            campaign.publish_status = campaign.publish_status or "draft"
    await db.commit()
    await db.refresh(campaign)
    return campaign_to_out(campaign)


@router.post("/campaigns/{campaign_id}/audiences/recommend", response_model=CampaignOut)
async def recommend_audiences(
    campaign_id: str,
    ctx: WorkspaceContext = Depends(require_role(*WRITER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    campaign = await _get_campaign_in_workspace(db, campaign_id, ctx.workspace.id)
    creative = (
        await db.execute(
            select(AgentRun).where(AgentRun.campaign_id == campaign_id, AgentRun.agent == "creative")
        )
    ).scalar_one_or_none()
    state = build_audience_state(
        campaign, (creative.payload if creative else {}).get("audience_suggestions")
    )
    state["recommended"] = await enrich_audiences_with_llm(campaign, state["recommended"])
    state["selected"] = [a for a in state["recommended"] if a.get("selected")] or state["selected"]
    campaign.audiences = state
    await db.commit()
    await db.refresh(campaign)
    return campaign_to_out(campaign)


@router.patch("/campaigns/{campaign_id}/optimization", response_model=CampaignOut)
async def patch_optimization(
    campaign_id: str,
    body: OptimizationUpdateRequest,
    ctx: WorkspaceContext = Depends(require_role(*WRITER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    campaign = await _get_campaign_in_workspace(db, campaign_id, ctx.workspace.id)
    state = campaign.optimization or {}
    if not state.get("ads") and campaign.meta_structure:
        daily = float(getattr(campaign, "daily_budget", None) or 20.0)
        state = init_optimization_from_structure(campaign.meta_structure, daily)
    state = update_rules(state, rules=body.rules, targets=body.targets)
    if body.enabled is not None:
        state["enabled"] = body.enabled
    campaign.optimization = state
    await db.commit()
    await db.refresh(campaign)
    return campaign_to_out(campaign)


@router.patch("/campaigns/{campaign_id}/auto-pause", response_model=CampaignOut)
async def set_auto_pause(
    campaign_id: str,
    body: AutoPauseUpdate,
    ctx: WorkspaceContext = Depends(require_role(*WRITER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    campaign = await _get_campaign_in_workspace(db, campaign_id, ctx.workspace.id)
    campaign.auto_pause_enabled = bool(body.enabled)
    await log_action(
        db,
        campaign.id,
        actor="manager",
        action="auto_pause_toggled",
        summary=f"Auto-pause {'enabled' if body.enabled else 'disabled'}",
        level="info",
    )
    await db.commit()
    await db.refresh(campaign)
    return campaign_to_out(campaign)


@router.post("/campaigns/{campaign_id}/optimization/tick", response_model=CampaignOut)
async def optimization_tick(
    campaign_id: str,
    body: OptimizationTickRequest,
    ctx: WorkspaceContext = Depends(require_role(*WRITER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """Simulate N days of performance and apply automated optimization rules."""
    campaign = await _get_campaign_in_workspace(db, campaign_id, ctx.workspace.id)
    state = campaign.optimization or {}
    if not state.get("ads"):
        if not campaign.meta_structure:
            raise HTTPException(400, "Publish Meta campaign first to enable optimization")
        daily = float(getattr(campaign, "daily_budget", None) or 20.0)
        state = init_optimization_from_structure(campaign.meta_structure, daily)
    days = max(1, min(int(body.days or 1), 14))
    for _ in range(days):
        state = run_optimization_tick(state, scenario=body.scenario or "mixed")
    campaign.optimization = state
    # Mirror ad-set budget onto campaign daily_budget for display
    if state.get("ad_set_daily_budget"):
        campaign.daily_budget = float(state["ad_set_daily_budget"])
    await db.commit()
    await db.refresh(campaign)
    return campaign_to_out(campaign)


@router.post("/campaigns/{campaign_id}/rerun", response_model=CampaignOut)
async def rerun_campaign(
    campaign_id: str,
    background: BackgroundTasks,
    ctx: WorkspaceContext = Depends(require_role(*WRITER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    campaign = await _get_campaign_in_workspace(db, campaign_id, ctx.workspace.id)
    runs = (await db.execute(select(AgentRun).where(AgentRun.campaign_id == campaign_id))).scalars().all()
    for r in runs:
        await db.delete(r)
    campaign.status = "received"
    campaign.decision = None
    campaign.decision_reason = None
    await db.commit()
    if not await enqueue_campaign_pipeline(campaign_id):
        background.add_task(_pipeline_job, campaign_id)
    return campaign_to_out(campaign)


@router.get("/recommendations", response_model=list[RecommendationOut])
async def list_recommendations(
    status: str | None = "pending",
    ctx: WorkspaceContext = Depends(get_workspace_context),
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(Recommendation)
        .join(Campaign, Campaign.id == Recommendation.campaign_id)
        .where(Campaign.workspace_id == ctx.workspace.id)
        .order_by(Recommendation.created_at.desc())
    )
    if status:
        q = q.where(Recommendation.status == status)
    recs = (await db.execute(q)).scalars().all()
    return [_rec_out(r) for r in recs]


@router.post("/recommendations/{rec_id}/action", response_model=RecommendationOut)
async def recommendation_action(
    rec_id: str,
    body: ApprovalAction,
    ctx: WorkspaceContext = Depends(require_role(*APPROVER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Recommendation)
        .join(Campaign, Campaign.id == Recommendation.campaign_id)
        .where(
            Recommendation.id == rec_id,
            Campaign.workspace_id == ctx.workspace.id,
        )
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(404, "Recommendation not found")
    campaign = await _get_campaign_in_workspace(db, rec.campaign_id, ctx.workspace.id)
    if body.action == "approve":
        await approve_recommendation(db, campaign, rec)
    elif body.action == "reject":
        await reject_recommendation(db, rec)
    else:
        raise HTTPException(400, "action must be approve or reject")
    await db.refresh(rec)
    return _rec_out(rec)


@router.post("/campaigns/{campaign_id}/demo-tick")
async def demo_tick(
    campaign_id: str,
    body: DemoTickRequest,
    ctx: WorkspaceContext = Depends(require_role(*WRITER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """Simulate mid-demo events: negative comment flood, spend spike, or recover."""
    campaign = await _get_campaign_in_workspace(db, campaign_id, ctx.workspace.id)
    ads = apply_demo_tick(campaign.mock_ads or load_base_ads(campaign.scenario), body.event)
    campaign.mock_ads = ads

    extra = None
    if body.event == "negative_flood":
        extra = [
            {"id": "live1", "platform": "meta", "text": "This ad is toxic. Boycott now.", "author": "live_user"},
            {"id": "live2", "platform": "x", "text": "Worst brand experience of 2026", "author": "trend_x"},
            {"id": "live3", "platform": "tiktok", "text": "Do not buy — quality is awful", "author": "tok_live"},
        ]

    sentiment = await run_sentiment_agent(
        campaign.scenario if body.event != "recover" else "healthy",
        extra_comments=extra,
    )
    if body.event == "recover":
        sentiment = await run_sentiment_agent("healthy")

    strategy = await run_strategy_agent(campaign.scenario, ads)

    for name, payload in (("sentiment", sentiment), ("strategy", strategy)):
        run = (
            await db.execute(
                select(AgentRun).where(AgentRun.campaign_id == campaign_id, AgentRun.agent == name)
            )
        ).scalar_one_or_none()
        if run:
            run.payload = payload
            run.message = payload.get("message")
            run.health = "ok"
            run.finished_at = utcnow()

    snap = (
        await db.execute(select(SignalSnapshot).where(SignalSnapshot.campaign_id == campaign_id))
    ).scalar_one_or_none()
    if snap:
        snap.brand_sentiment = sentiment["brand_sentiment"]
        snap.roas = strategy["roas"]
        snap.spend = strategy["spend"]
        snap.spend_burn = strategy["spend_burn"]
        snap.updated_at = utcnow()

    if strategy.get("recommendation") and body.event in ("spend_spike", "negative_flood"):
        rec = strategy["recommendation"]
        auto_pause = bool(getattr(campaign, "auto_pause_enabled", True))
        if auto_pause and rec["type"] == "pause_ads":
            campaign.mock_ads = apply_pause(campaign.mock_ads)
            metrics = compute_metrics(campaign.mock_ads)
            if snap:
                snap.spend = metrics["spend"]
                snap.roas = metrics["roas"]
                snap.spend_burn = metrics["spend_burn"]
                snap.updated_at = utcnow()
            if campaign.status == "live":
                campaign.status = "halted"
            db.add(
                Recommendation(
                    id=str(uuid.uuid4()),
                    campaign_id=campaign.id,
                    type=rec["type"],
                    status="approved",
                    title=rec["title"] + " (auto-paused)",
                    detail=rec["detail"] + f" Auto-pause enabled. Trigger: {body.event}.",
                )
            )
            await log_action(
                db,
                campaign.id,
                actor="strategy",
                action="auto_paused",
                summary=f"Auto-paused ads after {body.event} — ROAS {metrics['roas']:.2f}x",
                detail=rec["detail"],
                level="action",
            )
        else:
            db.add(
                Recommendation(
                    id=str(uuid.uuid4()),
                    campaign_id=campaign.id,
                    type=rec["type"],
                    status="pending",
                    title=rec["title"],
                    detail=rec["detail"] + f" (triggered by demo event: {body.event})",
                )
            )
            await log_action(
                db,
                campaign.id,
                actor="strategy",
                action="recommend_pause",
                summary=f"Recommended pause after {body.event} (waiting for manager)",
                detail=rec["detail"],
                level="warning",
            )
    else:
        await log_action(
            db,
            campaign.id,
            actor="system",
            action=f"demo_{body.event}",
            summary=f"Demo event applied: {body.event}",
            level="info",
        )

    await db.commit()
    await event_bus.publish(
        campaign_id,
        {
            "type": "demo_tick",
            "campaign_id": campaign_id,
            "data": {"event": body.event, "sentiment": sentiment, "strategy": strategy},
            "at": utcnow().isoformat(),
        },
    )
    return {"ok": True, "event": body.event, "sentiment": sentiment, "strategy": strategy}


@router.get("/campaigns/{campaign_id}/events")
async def campaign_events(
    campaign_id: str,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    db: AsyncSession = Depends(get_db),
):
    await _get_campaign_in_workspace(db, campaign_id, ctx.workspace.id)
    queue = event_bus.subscribe(campaign_id)

    async def generator():
        try:
            yield {"event": "connected", "data": '{"ok":true}'}
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=20)
                    import json

                    yield {"event": item.get("type", "message"), "data": json.dumps(item)}
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": "{}"}
        finally:
            event_bus.unsubscribe(campaign_id, queue)

    return EventSourceResponse(generator())
