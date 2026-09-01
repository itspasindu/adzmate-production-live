"""Real Meta Marketing API — publish campaign structure via Graph API."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from app.integrations.meta.context import MetaPublishContext
from app.integrations.meta import ads_manager as ads_manager_links
from app.services import meta as meta_svc
from app.services.meta_publish import CTA_TO_META, OBJECTIVE_TO_META, _now

logger = logging.getLogger(__name__)


def _normalize_ad_account(ad_account_id: str) -> str:
    return ad_account_id if ad_account_id.startswith("act_") else f"act_{ad_account_id}"


async def _download_image(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        res = await client.get(url)
        res.raise_for_status()
        return res.content


async def _upload_ad_image(ctx: MetaPublishContext, image_url: str) -> str:
    """Return image hash for Ad Creative."""
    image_bytes = await _download_image(image_url)
    act = _normalize_ad_account(ctx.ad_account_id)
    data = await meta_svc.graph_post_multipart(
        f"{act}/adimages",
        ctx.access_token,
        files={"filename": ("creative.png", image_bytes, "image/png")},
    )
    images = data.get("images") or {}
    if images:
        first = next(iter(images.values()))
        if isinstance(first, dict) and first.get("hash"):
            return str(first["hash"])
    raise ValueError("Meta did not return an image hash")


def _build_targeting(adset: dict) -> dict:
    targeting = dict(adset.get("targeting") or {})
    geo = targeting.get("geo_locations")
    if isinstance(geo, list):
        countries = []
        for item in geo:
            if len(item) == 2 and item.isalpha():
                countries.append(item.upper())
            elif item:
                countries.append("US")
        targeting["geo_locations"] = {"countries": countries or ["US"]}
    elif not geo:
        targeting["geo_locations"] = {"countries": ["US"]}

    gender = targeting.pop("genders", None) or adset.get("audience", {}).get("gender", "all")
    if gender == "male":
        targeting["genders"] = [1]
    elif gender == "female":
        targeting["genders"] = [2]

    for drop in ("locales", "interests", "behaviors", "custom_audiences", "lookalikes", "retargeting"):
        targeting.pop(drop, None)
    return targeting


async def publish_to_meta(structure: dict, ctx: MetaPublishContext) -> dict:
    """Create campaign, ad set, creatives, and ads in Meta (starts PAUSED for safety)."""
    structure = dict(structure or {})
    camp_node = dict(structure.get("campaign") or {})
    adset_node = dict(structure.get("ad_set") or {})
    ads = list(structure.get("ads") or [])
    if not camp_node or not adset_node or not ads:
        raise ValueError("Incomplete Meta draft structure")

    act = _normalize_ad_account(ctx.ad_account_id)
    objective = camp_node.get("objective") or OBJECTIVE_TO_META.get("sales", "OUTCOME_SALES")

    camp_payload = {
        "name": camp_node.get("name") or "AdzMate Campaign",
        "objective": objective,
        "status": "PAUSED",
        "special_ad_categories": camp_node.get("special_ad_categories") or [],
    }
    camp_res = await meta_svc.graph_post(f"{act}/campaigns", ctx.access_token, data=camp_payload)
    meta_campaign_id = str(camp_res["id"])

    daily = float(adset_node.get("daily_budget") or 20.0)
    daily_cents = max(100, int(daily * 100))
    targeting = _build_targeting(adset_node)

    adset_payload = {
        "name": adset_node.get("name") or "AdzMate Ad Set",
        "campaign_id": meta_campaign_id,
        "daily_budget": daily_cents,
        "billing_event": adset_node.get("billing_event") or "IMPRESSIONS",
        "optimization_goal": adset_node.get("optimization_goal") or "OFFSITE_CONVERSIONS",
        "bid_strategy": adset_node.get("bid_strategy") or "LOWEST_COST_WITHOUT_CAP",
        "targeting": targeting,
        "status": "PAUSED",
    }
    adset_res = await meta_svc.graph_post(f"{act}/adsets", ctx.access_token, data=adset_payload)
    meta_adset_id = str(adset_res["id"])

    published_ads: list[dict] = []
    for idx, ad in enumerate(ads[:6]):
        creative = dict(ad.get("creative") or {})
        image_url = creative.get("image_url")
        if not image_url:
            raise ValueError(f"Ad {idx + 1} missing creative image_url for Meta upload")

        image_hash = await _upload_ad_image(ctx, image_url)
        link = creative.get("link_url") or creative.get("url") or "https://example.com"
        cta_type = CTA_TO_META.get(creative.get("cta") or "Shop Now", "SHOP_NOW")

        creative_payload = {
            "name": ad.get("name") or f"AdzMate Creative {idx + 1}",
            "object_story_spec": {
                "page_id": ctx.page_id,
                "link_data": {
                    "message": creative.get("primary_text") or creative.get("description") or "",
                    "link": link,
                    "name": creative.get("headline") or "",
                    "description": creative.get("description") or "",
                    "image_hash": image_hash,
                    "call_to_action": {"type": cta_type, "value": {"link": link}},
                },
            },
        }
        creative_res = await meta_svc.graph_post(
            f"{act}/adcreatives", ctx.access_token, data=creative_payload
        )
        creative_id = str(creative_res["id"])

        ad_payload = {
            "name": ad.get("name") or f"AdzMate Ad {idx + 1}",
            "adset_id": meta_adset_id,
            "creative": {"creative_id": creative_id},
            "status": "PAUSED",
        }
        ad_res = await meta_svc.graph_post(f"{act}/ads", ctx.access_token, data=ad_payload)

        item = dict(ad)
        item["status"] = "PAUSED"
        item["uploaded"] = True
        item["meta_id"] = str(ad_res["id"])
        item["creative_id"] = creative_id
        published_ads.append(item)

    camp_node["status"] = "PAUSED"
    camp_node["meta_id"] = meta_campaign_id
    adset_node["status"] = "PAUSED"
    adset_node["meta_id"] = meta_adset_id

    steps = []
    for step in structure.get("steps") or []:
        s = dict(step)
        if s.get("step") == "publish_campaign":
            s["status"] = "done"
            s["detail"] = f"Published to Meta as {meta_campaign_id} (PAUSED — activate in Ads Manager)"
            s["at"] = _now()
        steps.append(s)

    structure["campaign"] = camp_node
    structure["ad_set"] = adset_node
    structure["ads"] = published_ads
    structure["steps"] = steps
    structure["status"] = "published"
    structure["mode"] = "meta_live"
    structure["published_at"] = datetime.now(timezone.utc).isoformat()
    structure["ads_manager_url"] = ads_manager_links.campaign_url(ctx.ad_account_id, meta_campaign_id)
    structure["ads_manager_account_url"] = ads_manager_links.ad_account_url(ctx.ad_account_id)
    structure["notes"] = (
        "Published via Meta Marketing API. Campaign, ad set, and ads are PAUSED until you activate "
        "them in Meta Ads Manager."
    )
    logger.info("Published Meta campaign %s for ad account %s", meta_campaign_id, act)
    return structure
