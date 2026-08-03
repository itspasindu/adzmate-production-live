from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.creative import run_creative_agent
from app.agents.sentiment import run_sentiment_agent
from app.agents.strategy import (
    apply_pause,
    apply_resume,
    compute_metrics,
    load_base_ads,
    run_strategy_agent,
)
from app.events import event_bus
from app.models import AgentRun, Campaign, Recommendation, SignalSnapshot, utcnow
from app.services.actions import log_action
from app.services.aggregator import aggregate_signals, enrich_decision_reason
from app.services.audiences import build_audience_state, enrich_audiences_with_llm
from app.services.deployer import deploy_landing_page
from app.services.meta_publish import build_draft_structure, mark_in_review, publish_structure
from app.services.optimization import init_optimization_from_structure


async def _emit(campaign_id: str, event_type: str, data: dict | None = None) -> None:
    await event_bus.publish(
        campaign_id,
        {"type": event_type, "campaign_id": campaign_id, "data": data or {}, "at": utcnow().isoformat()},
    )


async def _upsert_agent(
    db: AsyncSession,
    campaign_id: str,
    agent: str,
    health: str,
    payload: dict | None = None,
    message: str | None = None,
    start: bool = False,
    finish: bool = False,
) -> AgentRun:
    result = await db.execute(
        select(AgentRun).where(AgentRun.campaign_id == campaign_id, AgentRun.agent == agent)
    )
    run = result.scalar_one_or_none()
    if not run:
        run = AgentRun(id=str(uuid.uuid4()), campaign_id=campaign_id, agent=agent)
        db.add(run)

    run.health = health
    if payload is not None:
        run.payload = payload
    if message is not None:
        run.message = message
    if start:
        run.started_at = utcnow()
    if finish:
        run.finished_at = utcnow()
    await db.flush()
    return run


async def run_pipeline(db: AsyncSession, campaign: Campaign) -> Campaign:
    campaign.status = "agents_running"
    campaign.warnings = []
    campaign.updated_at = utcnow()
    if not campaign.mock_ads:
        campaign.mock_ads = load_base_ads(campaign.scenario)
    await db.commit()
    await _emit(campaign.id, "status", {"status": campaign.status})
    await log_action(
        db,
        campaign.id,
        actor="orchestrator",
        action="pipeline_started",
        summary="Orchestrator started parallel Creative, Sentiment, and Strategy agents",
        level="info",
    )

    for agent in ("creative", "sentiment", "strategy"):
        await _upsert_agent(db, campaign.id, agent, "running", start=True, message="Running…")
    await db.commit()
    await _emit(campaign.id, "agents_started", {})

    async def creative_task():
        return await run_creative_agent(
            campaign.id,
            campaign.product_image_path,
            campaign.brand_name,
            campaign.product_name,
            campaign.brief,
            campaign.brand_primary,
            campaign.brand_accent,
            context={
                "product_description": getattr(campaign, "product_description", "") or campaign.brief,
                "product_url": getattr(campaign, "product_url", None),
                "objective": getattr(campaign, "objective", None) or "sales",
                "daily_budget": getattr(campaign, "daily_budget", None) or campaign.budget,
                "duration_days": getattr(campaign, "duration_days", None) or 14,
                "target_country": getattr(campaign, "target_country", None) or "",
                "target_location": getattr(campaign, "target_location", None) or "",
                "age_min": getattr(campaign, "age_min", None) or 18,
                "age_max": getattr(campaign, "age_max", None) or 65,
                "gender": getattr(campaign, "gender", None) or "all",
                "language": getattr(campaign, "language", None) or "en",
            },
        )

    async def sentiment_task():
        return await run_sentiment_agent(campaign.scenario)

    async def strategy_task():
        return await run_strategy_agent(campaign.scenario, campaign.mock_ads)

    results = await asyncio.gather(
        creative_task(),
        sentiment_task(),
        strategy_task(),
        return_exceptions=True,
    )

    payloads: dict[str, dict | None] = {"creative": None, "sentiment": None, "strategy": None}
    warnings: list[str] = []

    for name, result in zip(("creative", "sentiment", "strategy"), results):
        if isinstance(result, Exception):
            warnings.append(f"{name} agent failed: {result}")
            await _upsert_agent(
                db,
                campaign.id,
                name,
                "failed",
                payload={"error": str(result)},
                message=str(result),
                finish=True,
            )
            await log_action(
                db,
                campaign.id,
                actor=name,
                action="agent_failed",
                summary=f"{name.title()} agent failed — pipeline continues with remaining agents",
                detail=str(result),
                level="warning",
            )
        else:
            payloads[name] = result
            await _upsert_agent(
                db,
                campaign.id,
                name,
                "ok",
                payload=result,
                message=result.get("message"),
                finish=True,
            )
            await log_action(
                db,
                campaign.id,
                actor=name,
                action="agent_completed",
                summary=result.get("message") or f"{name.title()} agent finished",
                detail=str(result.get("engine") or ""),
                level="success",
            )
            if name == "strategy" and result.get("recommendation"):
                rec = result["recommendation"]
                db.add(
                    Recommendation(
                        id=str(uuid.uuid4()),
                        campaign_id=campaign.id,
                        type=rec["type"],
                        status="pending",
                        title=rec["title"],
                        detail=rec["detail"],
                    )
                )
                await log_action(
                    db,
                    campaign.id,
                    actor="strategy",
                    action="recommend_pause",
                    summary=rec["title"],
                    detail=rec["detail"],
                    level="action",
                )

    campaign.status = "aggregating"
    campaign.warnings = warnings
    await db.commit()
    await _emit(campaign.id, "agents_finished", {"warnings": warnings})

    agg = aggregate_signals(payloads["creative"], payloads["sentiment"], payloads["strategy"], warnings)
    agg = await enrich_decision_reason(
        agg, payloads["creative"], payloads["sentiment"], payloads["strategy"]
    )

    # Upsert signals
    existing = await db.execute(select(SignalSnapshot).where(SignalSnapshot.campaign_id == campaign.id))
    snap = existing.scalar_one_or_none()
    if not snap:
        snap = SignalSnapshot(id=str(uuid.uuid4()), campaign_id=campaign.id)
        db.add(snap)
    snap.creative_ready = agg["creative_ready"]
    snap.brand_sentiment = agg["brand_sentiment"]
    snap.roas = agg["roas"]
    snap.spend_burn = agg["spend_burn"]
    snap.spend = agg["spend"]
    snap.updated_at = utcnow()

    campaign.decision = agg["decision"]
    campaign.decision_reason = agg["decision_reason"]
    campaign.decision_confidence = agg["decision_confidence"]
    campaign.status = "awaiting_approval"
    if warnings and campaign.decision == "LAUNCH":
        # still awaiting approval but flag degraded path
        pass
    elif warnings and not payloads["creative"] and not payloads["sentiment"] and not payloads["strategy"]:
        campaign.status = "failed"

    # Audience automation + Meta draft structure (Draft → Review → Publish)
    creative_payload = payloads.get("creative") or {}
    creative_audiences = creative_payload.get("audience_suggestions") or []
    audience_state = build_audience_state(campaign, creative_audiences)
    try:
        audience_state["recommended"] = await enrich_audiences_with_llm(
            campaign, audience_state["recommended"]
        )
        audience_state["selected"] = [
            a for a in audience_state["recommended"] if a.get("selected")
        ] or audience_state["selected"]
    except Exception:
        pass
    campaign.audiences = audience_state

    title_map = {
        "LAUNCH": "Approve campaign launch",
        "HALT": "Approve campaign halt",
        "HOLD": "Manager decision required",
    }
    rec_type = {"LAUNCH": "launch", "HALT": "halt", "HOLD": "launch"}[campaign.decision or "HOLD"]
    rec_title = title_map.get(campaign.decision or "HOLD", "Review campaign")
    rec_detail = campaign.decision_reason or ""

    if campaign.decision in ("LAUNCH", "HOLD") and campaign.status != "failed":
        structure = build_draft_structure(
            campaign,
            assets=creative_payload.get("assets") or [],
        )
        campaign.meta_structure = structure
        campaign.publish_status = "draft"
        rec_title = "Review Meta draft & publish"
        rec_detail = (
            f"{campaign.decision_reason or ''} "
            "Meta campaign, ad set, placements, audiences, and creatives are ready as a DRAFT. "
            "Review, then approve to publish."
        ).strip()

    db.add(
        Recommendation(
            id=str(uuid.uuid4()),
            campaign_id=campaign.id,
            type=rec_type,
            status="pending",
            title=rec_title,
            detail=rec_detail,
        )
    )

    await log_action(
        db,
        campaign.id,
        actor="aggregator",
        action=f"decision_{campaign.decision or 'HOLD'}",
        summary=f"Signal Aggregator decided {campaign.decision}: {rec_title}",
        detail=rec_detail,
        level="action" if campaign.decision in ("LAUNCH", "HALT") else "warning",
    )
    if campaign.publish_status == "draft":
        await log_action(
            db,
            campaign.id,
            actor="system",
            action="meta_draft_built",
            summary="Built Meta draft (campaign → ad set → ads) — waiting for Review & Publish",
            level="info",
        )

    await db.commit()
    await _emit(
        campaign.id,
        "decision",
        {
            "decision": campaign.decision,
            "reason": campaign.decision_reason,
            "signals": {
                "creative_ready": snap.creative_ready,
                "brand_sentiment": snap.brand_sentiment,
                "roas": snap.roas,
                "spend_burn": snap.spend_burn,
                "spend": snap.spend,
            },
        },
    )
    return campaign


async def approve_recommendation(db: AsyncSession, campaign: Campaign, recommendation: Recommendation) -> Campaign:
    recommendation.status = "approved"
    await db.flush()
    await log_action(
        db,
        campaign.id,
        actor="manager",
        action=f"approved_{recommendation.type}",
        summary=f"Manager approved: {recommendation.title}",
        detail=recommendation.detail,
        level="action",
    )

    if recommendation.type in ("launch", "deploy"):
        campaign.status = "deploying"
        if campaign.meta_structure:
            campaign.meta_structure = mark_in_review(campaign.meta_structure)
            campaign.publish_status = "in_review"
        await db.commit()
        await _emit(campaign.id, "status", {"status": "deploying"})

        result = await db.execute(
            select(AgentRun).where(AgentRun.campaign_id == campaign.id, AgentRun.agent == "creative")
        )
        creative_run = result.scalar_one_or_none()
        assets = (creative_run.payload if creative_run else {}).get("assets", [])
        headline = assets[0]["headline"] if assets else f"Meet {campaign.product_name}"
        cta = assets[0]["cta"] if assets else "Shop Now"
        image_url = assets[0]["url"] if assets else None
        if campaign.product_image_path:
            image_url = image_url or f"http://localhost:8000/uploads/{campaign.id}/product.png"

        deployed = deploy_landing_page(
            campaign.id,
            campaign.brand_name,
            campaign.product_name,
            campaign.brief,
            headline,
            cta,
            campaign.brand_primary,
            campaign.brand_accent,
            image_url,
        )
        campaign.landing_page_path = deployed["path"]
        campaign.cloudfront_url = deployed["cloudfront_url"]
        await log_action(
            db,
            campaign.id,
            actor="deployer",
            action="landing_deployed",
            summary="Landing page built and published to preview CDN",
            detail=deployed.get("preview_url"),
            level="success",
        )

        if campaign.meta_structure:
            published = publish_structure(campaign.meta_structure)
            campaign.meta_structure = published
            campaign.publish_status = "published"
            daily = float(getattr(campaign, "daily_budget", None) or 20.0)
            campaign.optimization = init_optimization_from_structure(published, daily)
            await log_action(
                db,
                campaign.id,
                actor="system",
                action="meta_published",
                summary="Published Meta draft structure and started optimization rules",
                detail=(published.get("campaign") or {}).get("meta_id"),
                level="success",
            )

        campaign.status = "live"
        campaign.decision = "LAUNCH"
        await db.commit()
        await _emit(
            campaign.id,
            "deployed",
            {
                "preview_url": deployed["preview_url"],
                "cloudfront_url": deployed["cloudfront_url"],
                "publish_status": campaign.publish_status,
                "meta_campaign_id": (campaign.meta_structure or {}).get("campaign", {}).get("meta_id"),
            },
        )

    elif recommendation.type == "halt":
        campaign.status = "halted"
        campaign.decision = "HALT"
        campaign.mock_ads = apply_pause(campaign.mock_ads)
        await log_action(
            db,
            campaign.id,
            actor="strategy",
            action="ads_halted",
            summary="All mock platform ads paused (HALT)",
            level="action",
        )
        await db.commit()
        await _emit(campaign.id, "status", {"status": "halted"})

    elif recommendation.type == "pause_ads":
        campaign.mock_ads = apply_pause(campaign.mock_ads)
        metrics = compute_metrics(campaign.mock_ads)
        existing = await db.execute(select(SignalSnapshot).where(SignalSnapshot.campaign_id == campaign.id))
        snap = existing.scalar_one_or_none()
        if snap:
            snap.spend = metrics["spend"]
            snap.roas = metrics["roas"]
            snap.spend_burn = metrics["spend_burn"]
            snap.updated_at = utcnow()
        if campaign.status == "live":
            campaign.status = "halted"
        await log_action(
            db,
            campaign.id,
            actor="strategy",
            action="ads_paused",
            summary=f"Paused ads — ROAS {metrics['roas']:.2f}x · spend ${metrics['spend']:.0f}",
            level="action",
        )
        await db.commit()
        await _emit(campaign.id, "ads_paused", metrics)

    elif recommendation.type == "resume_ads":
        campaign.mock_ads = apply_resume(campaign.mock_ads)
        metrics = compute_metrics(campaign.mock_ads)
        existing = await db.execute(select(SignalSnapshot).where(SignalSnapshot.campaign_id == campaign.id))
        snap = existing.scalar_one_or_none()
        if snap:
            snap.spend = metrics["spend"]
            snap.roas = metrics["roas"]
            snap.spend_burn = metrics["spend_burn"]
            snap.updated_at = utcnow()
        if campaign.status == "halted":
            campaign.status = "live"
        await log_action(
            db,
            campaign.id,
            actor="strategy",
            action="ads_resumed",
            summary="Resumed mock platform ads",
            level="success",
        )
        await db.commit()
        await _emit(campaign.id, "ads_resumed", metrics)

    return campaign


async def reject_recommendation(db: AsyncSession, recommendation: Recommendation) -> None:
    recommendation.status = "rejected"
    await db.commit()
