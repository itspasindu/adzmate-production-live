"""Resolve platform ad metrics — Meta Insights when connected, fixtures otherwise."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.strategy import load_base_ads
from app.config import settings
from app.integrations.meta.context import resolve_publish_context
from app.integrations.meta.insights import fetch_account_insights, fetch_campaign_insights
from app.models import Campaign

logger = logging.getLogger(__name__)


def _is_simulated_meta_id(meta_id: str | None) -> bool:
    if not meta_id:
        return True
    mid = str(meta_id)
    return mid.startswith("meta_camp_") or mid.startswith("draft_")


async def sync_campaign_metrics(db: AsyncSession, campaign: Campaign) -> dict[str, Any]:
    """Refresh campaign.mock_ads from Meta Insights when live integration is available."""
    base = campaign.mock_ads or load_base_ads(campaign.scenario)

    if settings.use_fixture_metrics:
        return base

    ctx = await resolve_publish_context(db, campaign.workspace_id)
    if not ctx:
        return base

    try:
        structure = campaign.meta_structure or {}
        meta_campaign_id = (structure.get("campaign") or {}).get("meta_id")

        if meta_campaign_id and not _is_simulated_meta_id(meta_campaign_id):
            row = await fetch_campaign_insights(ctx, str(meta_campaign_id))
            spend = row.get("spend", 0.0)
            revenue = row.get("revenue", 0.0)
            live_meta = {
                "spend": round(float(spend), 2),
                "revenue": round(float(revenue), 2),
                "status": "active",
                "source": "meta_insights_campaign",
            }
        else:
            account_ads = await fetch_account_insights(ctx)
            live_meta = account_ads.get("meta") or {}

        merged = dict(base)
        if live_meta:
            merged["meta"] = {**(merged.get("meta") or {}), **live_meta}
        campaign.mock_ads = merged
        logger.info(
            "Synced live Meta metrics for campaign %s (spend=%s)",
            campaign.id,
            merged.get("meta", {}).get("spend"),
        )
        return merged
    except Exception as exc:
        logger.warning("Meta metrics sync failed for %s: %s", campaign.id, exc)
        return base
