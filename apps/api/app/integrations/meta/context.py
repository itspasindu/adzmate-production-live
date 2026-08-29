from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MetaConnection
from app.services import meta as meta_svc


@dataclass
class MetaPublishContext:
    access_token: str
    ad_account_id: str
    page_id: str
    instagram_id: str | None
    connection_id: str
    business_id: str
    is_real: bool = True

    @property
    def ad_account_path(self) -> str:
        act = self.ad_account_id
        if act.startswith("act_"):
            return act
        return f"act_{act}"


async def resolve_publish_context(
    db: AsyncSession,
    workspace_id: str,
) -> MetaPublishContext | None:
    """First connected (non-demo) Meta link in the workspace with ad account + page selected."""
    result = await db.execute(
        select(MetaConnection)
        .where(
            MetaConnection.workspace_id == workspace_id,
            MetaConnection.status == "connected",
        )
        .order_by(MetaConnection.connected_at.asc())
        .limit(1)
    )
    conn = result.scalar_one_or_none()
    if not conn:
        return None

    token = meta_svc.get_connection_access_token(conn)
    if not token or token == "demo-token":
        return None
    if not conn.selected_ad_account_id or not conn.selected_page_id:
        return None
    if not meta_svc.meta_oauth_configured():
        return None

    return MetaPublishContext(
        access_token=token,
        ad_account_id=conn.selected_ad_account_id,
        page_id=conn.selected_page_id,
        instagram_id=conn.selected_instagram_id,
        connection_id=conn.id,
        business_id=conn.business_id,
        is_real=True,
    )
