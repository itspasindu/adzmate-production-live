"""Pause / resume Meta ads via Marketing API."""

from __future__ import annotations

import logging

from app.integrations.meta.context import MetaPublishContext
from app.services import meta as meta_svc

logger = logging.getLogger(__name__)


async def pause_meta_structure(structure: dict, ctx: MetaPublishContext) -> list[str]:
    """Pause campaign, ad set, and ads that have meta_id. Returns paused object IDs."""
    paused: list[str] = []
    token = ctx.access_token

    for key in ("campaign", "ad_set"):
        node = structure.get(key) or {}
        meta_id = node.get("meta_id")
        if meta_id and not str(meta_id).startswith("meta_"):
            try:
                await meta_svc.graph_post(str(meta_id), token, data={"status": "PAUSED"})
                paused.append(str(meta_id))
            except Exception as exc:
                logger.warning("Failed to pause %s: %s", meta_id, exc)

    for ad in structure.get("ads") or []:
        meta_id = ad.get("meta_id")
        if meta_id and not str(meta_id).startswith("meta_ad_"):
            try:
                await meta_svc.graph_post(str(meta_id), token, data={"status": "PAUSED"})
                paused.append(str(meta_id))
            except Exception as exc:
                logger.warning("Failed to pause ad %s: %s", meta_id, exc)

    return paused


async def pause_ad_ids(ad_ids: list[str], ctx: MetaPublishContext) -> list[str]:
    paused: list[str] = []
    for ad_id in ad_ids:
        if not ad_id or str(ad_id).startswith("meta_ad_"):
            continue
        try:
            await meta_svc.graph_post(str(ad_id), ctx.access_token, data={"status": "PAUSED"})
            paused.append(str(ad_id))
        except Exception as exc:
            logger.warning("Failed to pause ad %s: %s", ad_id, exc)
    return paused
