from __future__ import annotations

import logging

from sqlalchemy import select

from app.db import SessionLocal
from app.integrations.meta.metrics_sync import sync_campaign_metrics
from app.models import Campaign
from app.services.orchestrator import run_pipeline

logger = logging.getLogger(__name__)


async def run_campaign_pipeline(_ctx, campaign_id: str) -> dict:
    """ARQ job: execute agent pipeline for a campaign."""
    async with SessionLocal() as db:
        result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
        campaign = result.scalar_one_or_none()
        if not campaign:
            logger.warning("Pipeline job: campaign %s not found", campaign_id)
            return {"ok": False, "reason": "not_found"}
        await run_pipeline(db, campaign)
        return {"ok": True, "campaign_id": campaign_id, "status": campaign.status}


async def sync_campaign_metrics_job(_ctx, campaign_id: str) -> dict:
    """ARQ job: pull Meta Insights into campaign.mock_ads."""
    async with SessionLocal() as db:
        result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
        campaign = result.scalar_one_or_none()
        if not campaign:
            return {"ok": False, "reason": "not_found"}
        ads = await sync_campaign_metrics(db, campaign)
        await db.commit()
        return {"ok": True, "campaign_id": campaign_id, "meta_spend": ads.get("meta", {}).get("spend")}


async def sync_all_live_metrics(_ctx) -> dict:
    """Cron: refresh metrics for all live/published campaigns."""
    from app.config import settings

    if settings.use_fixture_metrics:
        return {"ok": True, "skipped": "fixtures_mode", "count": 0}

    synced = 0
    async with SessionLocal() as db:
        rows = (
            await db.execute(
                select(Campaign).where(
                    Campaign.status.in_(("live", "halted")),
                    Campaign.publish_status == "published",
                )
            )
        ).scalars().all()
        for campaign in rows:
            try:
                await sync_campaign_metrics(db, campaign)
                synced += 1
            except Exception as exc:
                logger.warning("Cron metrics sync failed for %s: %s", campaign.id, exc)
        await db.commit()
    return {"ok": True, "count": synced}
