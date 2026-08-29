"""Business profiles + Meta account connection APIs."""
from __future__ import annotations

import uuid
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import WRITER_ROLES, WorkspaceContext, get_workspace_context, require_role
from app.config import resolve_meta_oauth_redirect_uri, settings
from app.db import get_db
from app.models import (
    Business,
    MetaAdAccount,
    MetaConnection,
    MetaInstagramAccount,
    MetaPage,
    utcnow,
)
from app.schemas import (
    BusinessCreate,
    BusinessOut,
    BusinessUpdate,
    MetaConnectionOut,
    MetaSelectionUpdate,
)
from app.services import meta as meta_svc

router = APIRouter(tags=["account"])


def _business_out(b: Business, conn: MetaConnection | None = None) -> BusinessOut:
    return BusinessOut(
        id=b.id,
        workspace_id=b.workspace_id,
        name=b.name,
        legal_name=b.legal_name,
        website=b.website,
        industry=b.industry,
        country=b.country,
        timezone=b.timezone,
        contact_email=b.contact_email,
        logo_url=b.logo_url,
        notes=b.notes,
        created_at=b.created_at,
        updated_at=b.updated_at,
        meta_status=conn.status if conn else None,
        selected_page_id=conn.selected_page_id if conn else None,
        selected_instagram_id=conn.selected_instagram_id if conn else None,
        selected_ad_account_id=conn.selected_ad_account_id if conn else None,
    )


async def _get_business_in_workspace(
    db: AsyncSession, business_id: str, workspace_id: str
) -> Business:
    result = await db.execute(
        select(Business).where(Business.id == business_id, Business.workspace_id == workspace_id)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(404, "Business not found")
    return business


async def _connection_out(db: AsyncSession, conn: MetaConnection) -> MetaConnectionOut:
    pages = (
        await db.execute(select(MetaPage).where(MetaPage.connection_id == conn.id))
    ).scalars().all()
    igs = (
        await db.execute(
            select(MetaInstagramAccount).where(MetaInstagramAccount.connection_id == conn.id)
        )
    ).scalars().all()
    ads = (
        await db.execute(select(MetaAdAccount).where(MetaAdAccount.connection_id == conn.id))
    ).scalars().all()

    return MetaConnectionOut(
        id=conn.id,
        business_id=conn.business_id,
        status=conn.status,
        meta_user_id=conn.meta_user_id,
        meta_user_name=conn.meta_user_name,
        scopes=conn.scopes or "",
        oauth_configured=meta_svc.meta_oauth_configured(),
        selected_page_id=conn.selected_page_id,
        selected_instagram_id=conn.selected_instagram_id,
        selected_ad_account_id=conn.selected_ad_account_id,
        pages=[
            {
                "page_id": p.page_id,
                "name": p.name,
                "category": p.category,
                "picture_url": p.picture_url,
                "selected": p.page_id == conn.selected_page_id,
            }
            for p in pages
        ],
        instagram_accounts=[
            {
                "ig_user_id": i.ig_user_id,
                "username": i.username,
                "name": i.name,
                "page_id": i.page_id,
                "profile_picture_url": i.profile_picture_url,
                "selected": i.ig_user_id == conn.selected_instagram_id,
            }
            for i in igs
        ],
        ad_accounts=[
            {
                "ad_account_id": a.ad_account_id,
                "name": a.name,
                "currency": a.currency,
                "timezone_name": a.timezone_name,
                "account_status": a.account_status,
                "selected": a.ad_account_id == conn.selected_ad_account_id,
            }
            for a in ads
        ],
        connected_at=conn.connected_at,
        updated_at=conn.updated_at,
    )


@router.get("/account/meta/status")
async def meta_status():
    config_err = meta_svc.meta_oauth_env_error()
    return {
        "oauth_configured": config_err is None and meta_svc.meta_oauth_configured(),
        "app_id_set": bool(settings.meta_app_id),
        "demo_connect_available": True,
        "config_error": config_err,
    }


@router.get("/businesses", response_model=list[BusinessOut])
async def list_businesses(
    ctx: WorkspaceContext = Depends(get_workspace_context),
    db: AsyncSession = Depends(get_db),
):
    rows = (
        await db.execute(
            select(Business)
            .where(Business.workspace_id == ctx.workspace.id)
            .order_by(Business.created_at.desc())
        )
    ).scalars().all()
    out: list[BusinessOut] = []
    for b in rows:
        conn = (
            await db.execute(select(MetaConnection).where(MetaConnection.business_id == b.id))
        ).scalar_one_or_none()
        out.append(_business_out(b, conn))
    return out


@router.post("/businesses", response_model=BusinessOut)
async def create_business(
    body: BusinessCreate,
    ctx: WorkspaceContext = Depends(require_role(*WRITER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    business = Business(
        id=str(uuid.uuid4()),
        workspace_id=ctx.workspace.id,
        name=body.name.strip(),
        legal_name=body.legal_name,
        website=body.website,
        industry=body.industry,
        country=body.country,
        timezone=body.timezone or "UTC",
        contact_email=body.contact_email or ctx.user.email,
        notes=body.notes,
        created_by=ctx.user.id,
    )
    db.add(business)
    await db.commit()
    await db.refresh(business)
    return _business_out(business)


@router.get("/businesses/{business_id}", response_model=BusinessOut)
async def get_business(
    business_id: str,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    db: AsyncSession = Depends(get_db),
):
    business = await _get_business_in_workspace(db, business_id, ctx.workspace.id)
    conn = (
        await db.execute(select(MetaConnection).where(MetaConnection.business_id == business.id))
    ).scalar_one_or_none()
    return _business_out(business, conn)


@router.patch("/businesses/{business_id}", response_model=BusinessOut)
async def update_business(
    business_id: str,
    body: BusinessUpdate,
    ctx: WorkspaceContext = Depends(require_role(*WRITER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    business = await _get_business_in_workspace(db, business_id, ctx.workspace.id)
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(business, key, value)
    business.updated_at = utcnow()
    await db.commit()
    await db.refresh(business)
    conn = (
        await db.execute(select(MetaConnection).where(MetaConnection.business_id == business.id))
    ).scalar_one_or_none()
    return _business_out(business, conn)


@router.delete("/businesses/{business_id}")
async def delete_business(
    business_id: str,
    ctx: WorkspaceContext = Depends(require_role("owner", "admin")),
    db: AsyncSession = Depends(get_db),
):
    business = await _get_business_in_workspace(db, business_id, ctx.workspace.id)
    conn = (
        await db.execute(select(MetaConnection).where(MetaConnection.business_id == business.id))
    ).scalar_one_or_none()
    if conn:
        for model in (MetaPage, MetaInstagramAccount, MetaAdAccount):
            rows = (
                await db.execute(select(model).where(model.connection_id == conn.id))
            ).scalars().all()
            for row in rows:
                await db.delete(row)
        await db.delete(conn)
    await db.delete(business)
    await db.commit()
    return {"ok": True}


@router.get("/businesses/{business_id}/meta", response_model=MetaConnectionOut)
async def get_meta_connection(
    business_id: str,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    db: AsyncSession = Depends(get_db),
):
    await _get_business_in_workspace(db, business_id, ctx.workspace.id)
    conn = (
        await db.execute(select(MetaConnection).where(MetaConnection.business_id == business_id))
    ).scalar_one_or_none()
    if not conn:
        raise HTTPException(404, "Meta account not connected")
    return await _connection_out(db, conn)


@router.get("/businesses/{business_id}/meta/oauth/start")
async def meta_oauth_start(
    business_id: str,
    ctx: WorkspaceContext = Depends(require_role(*WRITER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    await _get_business_in_workspace(db, business_id, ctx.workspace.id)
    config_err = meta_svc.meta_oauth_env_error()
    if config_err:
        raise HTTPException(400, config_err)
    redirect_uri = resolve_meta_oauth_redirect_uri()
    url = await meta_svc.build_oauth_url(
        business_id=business_id,
        workspace_id=ctx.workspace.id,
        user_id=ctx.user.id,
        redirect_uri=redirect_uri,
    )
    return {"authorize_url": url, "redirect_uri": redirect_uri}


@router.get("/meta/oauth/callback")
async def meta_oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    frontend = settings.web_app_url.rstrip("/")
    if error:
        qs = urlencode({"meta": "error", "message": error_description or error})
        return RedirectResponse(f"{frontend}/settings?{qs}")
    if not code or not state:
        return RedirectResponse(f"{frontend}/settings?meta=error&message=missing_code")

    payload = await meta_svc.pop_oauth_state(state)
    if not payload:
        return RedirectResponse(f"{frontend}/settings?meta=error&message=invalid_state")

    try:
        meta_svc.assert_meta_oauth_ready()
        token_data = await meta_svc.exchange_code_for_token(code, payload["redirect_uri"])
        access_token = token_data["access_token"]
        business_id = payload["business_id"]
        workspace_id = payload["workspace_id"]

        conn = (
            await db.execute(select(MetaConnection).where(MetaConnection.business_id == business_id))
        ).scalar_one_or_none()
        if not conn:
            conn = MetaConnection(
                id=str(uuid.uuid4()),
                business_id=business_id,
                workspace_id=workspace_id,
            )
            db.add(conn)
            await db.flush()

        await meta_svc.sync_connection_from_token(db, conn, access_token, status="connected")
    except Exception as exc:
        qs = urlencode({"meta": "error", "message": str(exc)[:180]})
        return RedirectResponse(f"{frontend}/settings?{qs}")

    return RedirectResponse(
        f"{frontend}/settings?meta=connected&business_id={payload['business_id']}"
    )


@router.post("/businesses/{business_id}/meta/demo-connect", response_model=MetaConnectionOut)
async def meta_demo_connect(
    business_id: str,
    ctx: WorkspaceContext = Depends(require_role(*WRITER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """Seed a demo Meta connection (Pages, Instagram, Ad Accounts) without Facebook OAuth."""
    if settings.is_production() and not settings.allow_demo_user:
        raise HTTPException(403, "Demo Meta connect is disabled in production.")
    await _get_business_in_workspace(db, business_id, ctx.workspace.id)
    conn = await meta_svc.upsert_demo_connection(
        db, business_id=business_id, workspace_id=ctx.workspace.id
    )
    return await _connection_out(db, conn)


@router.post("/businesses/{business_id}/meta/sync", response_model=MetaConnectionOut)
async def meta_sync(
    business_id: str,
    ctx: WorkspaceContext = Depends(require_role(*WRITER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    await _get_business_in_workspace(db, business_id, ctx.workspace.id)
    conn = (
        await db.execute(select(MetaConnection).where(MetaConnection.business_id == business_id))
    ).scalar_one_or_none()
    if not conn:
        raise HTTPException(404, "Meta account not connected")
    token = meta_svc.get_connection_access_token(conn)
    if conn.status == "demo" or not token or token == "demo-token":
        if settings.is_production() and not settings.allow_demo_user:
            raise HTTPException(400, "Connect a real Meta account in production.")
        conn = await meta_svc.upsert_demo_connection(
            db, business_id=business_id, workspace_id=ctx.workspace.id
        )
        return await _connection_out(db, conn)
    if not meta_svc.meta_oauth_configured():
        raise HTTPException(400, "Cannot sync real Meta assets without META_APP_ID/SECRET")
    try:
        await meta_svc.sync_connection_from_token(db, conn, token, status="connected")
    except Exception as exc:
        raise HTTPException(400, f"Meta sync failed: {exc}") from exc
    return await _connection_out(db, conn)


@router.patch("/businesses/{business_id}/meta/selection", response_model=MetaConnectionOut)
async def meta_selection(
    business_id: str,
    body: MetaSelectionUpdate,
    ctx: WorkspaceContext = Depends(require_role(*WRITER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    await _get_business_in_workspace(db, business_id, ctx.workspace.id)
    conn = (
        await db.execute(select(MetaConnection).where(MetaConnection.business_id == business_id))
    ).scalar_one_or_none()
    if not conn:
        raise HTTPException(404, "Meta account not connected")

    if body.page_id is not None:
        page = (
            await db.execute(
                select(MetaPage).where(
                    MetaPage.connection_id == conn.id, MetaPage.page_id == body.page_id
                )
            )
        ).scalar_one_or_none()
        if not page:
            raise HTTPException(400, "Invalid Facebook Page")
        conn.selected_page_id = body.page_id
        # Prefer IG linked to that page
        ig = (
            await db.execute(
                select(MetaInstagramAccount).where(
                    MetaInstagramAccount.connection_id == conn.id,
                    MetaInstagramAccount.page_id == body.page_id,
                )
            )
        ).scalar_one_or_none()
        if ig:
            conn.selected_instagram_id = ig.ig_user_id

    if body.instagram_id is not None:
        ig = (
            await db.execute(
                select(MetaInstagramAccount).where(
                    MetaInstagramAccount.connection_id == conn.id,
                    MetaInstagramAccount.ig_user_id == body.instagram_id,
                )
            )
        ).scalar_one_or_none()
        if not ig:
            raise HTTPException(400, "Invalid Instagram account")
        conn.selected_instagram_id = body.instagram_id
        if ig.page_id:
            conn.selected_page_id = ig.page_id

    if body.ad_account_id is not None:
        ad = (
            await db.execute(
                select(MetaAdAccount).where(
                    MetaAdAccount.connection_id == conn.id,
                    MetaAdAccount.ad_account_id == body.ad_account_id,
                )
            )
        ).scalar_one_or_none()
        if not ad:
            raise HTTPException(400, "Invalid Meta Ad Account")
        conn.selected_ad_account_id = body.ad_account_id

    conn.updated_at = utcnow()
    await db.commit()
    await db.refresh(conn)
    return await _connection_out(db, conn)


@router.delete("/businesses/{business_id}/meta")
async def meta_disconnect(
    business_id: str,
    ctx: WorkspaceContext = Depends(require_role(*WRITER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    await _get_business_in_workspace(db, business_id, ctx.workspace.id)
    conn = (
        await db.execute(select(MetaConnection).where(MetaConnection.business_id == business_id))
    ).scalar_one_or_none()
    if not conn:
        return {"ok": True}
    for model in (MetaPage, MetaInstagramAccount, MetaAdAccount):
        rows = (
            await db.execute(select(model).where(model.connection_id == conn.id))
        ).scalars().all()
        for row in rows:
            await db.delete(row)
    await db.delete(conn)
    await db.commit()
    return {"ok": True}
