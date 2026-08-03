"""Persistent agent / system action timeline for campaigns."""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActionEvent, utcnow


async def log_action(
    db: AsyncSession,
    campaign_id: str,
    *,
    actor: str,
    action: str,
    summary: str,
    detail: str | None = None,
    level: str = "info",
) -> ActionEvent:
    event = ActionEvent(
        id=str(uuid.uuid4()),
        campaign_id=campaign_id,
        actor=actor,
        action=action,
        summary=summary[:280],
        detail=(detail or "")[:2000] or None,
        level=level,
        created_at=utcnow(),
    )
    db.add(event)
    await db.flush()
    return event
