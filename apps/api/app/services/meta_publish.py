"""Build Meta campaign structure: Draft → Review → Publish (mock Marketing API)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.models import Campaign

OBJECTIVE_TO_META = {
    "sales": "OUTCOME_SALES",
    "leads": "OUTCOME_LEADS",
    "traffic": "OUTCOME_TRAFFIC",
    "engagement": "OUTCOME_ENGAGEMENT",
}

CTA_TO_META = {
    "Shop Now": "SHOP_NOW",
    "Learn More": "LEARN_MORE",
    "Sign Up": "SIGN_UP",
    "Book Now": "BOOK_TRAVEL",
    "Contact Us": "CONTACT_US",
    "Download": "DOWNLOAD",
    "Get Offer": "GET_OFFER",
}

DEFAULT_PLACEMENTS = [
    "facebook_feed",
    "instagram_feed",
    "instagram_stories",
    "facebook_reels",
    "audience_network",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _selected_audiences(campaign: Campaign) -> list[dict]:
    data = campaign.audiences or {}
    selected = data.get("selected") or []
    if selected:
        return selected
    recommended = data.get("recommended") or []
    return recommended[:1] if recommended else []


def build_draft_structure(
    campaign: Campaign,
    *,
    assets: list[dict] | None = None,
    ad_account_id: str | None = None,
    page_id: str | None = None,
    instagram_id: str | None = None,
) -> dict[str, Any]:
    """Create campaign → ad set → ads as a draft (not published)."""
    assets = assets or []
    meta_assets = [a for a in assets if a.get("format") == "meta_feed"] or assets[:3]
    if not meta_assets and assets:
        meta_assets = assets[:1]
    # Always aim for 3 creatives for optimization demo
    while len(meta_assets) < 3 and assets:
        meta_assets.append(assets[len(meta_assets) % len(assets)])
    if not meta_assets:
        meta_assets = [
            {
                "format": "meta_feed",
                "headline": f"{campaign.product_name}",
                "primary_text": campaign.product_description or campaign.brief,
                "description": campaign.brief[:90],
                "cta": "Shop Now",
                "url": campaign.product_url or "",
            }
        ]

    daily = float(getattr(campaign, "daily_budget", None) or 20.0)
    audiences = _selected_audiences(campaign)
    primary_audience = audiences[0] if audiences else {
        "name": "Core buyers",
        "type": "interest",
        "age_min": campaign.age_min,
        "age_max": campaign.age_max,
        "gender": campaign.gender,
        "locations": [campaign.target_country or "United States"],
        "interests": [campaign.product_name],
    }

    campaign_node = {
        "id": f"draft_camp_{uuid.uuid4().hex[:10]}",
        "name": campaign.name,
        "objective": OBJECTIVE_TO_META.get(campaign.objective or "sales", "OUTCOME_SALES"),
        "status": "DRAFT",
        "special_ad_categories": [],
        "is_adset_budget_sharing_enabled": False,
        "ad_account_id": ad_account_id or "act_demo",
    }

    adset = {
        "id": f"draft_adset_{uuid.uuid4().hex[:10]}",
        "name": f"{campaign.product_name} — Ad set",
        "status": "DRAFT",
        "daily_budget": daily,
        "billing_event": "IMPRESSIONS",
        "optimization_goal": (
            "LEAD_GENERATION"
            if (campaign.objective or "sales") == "leads"
            else "OFFSITE_CONVERSIONS"
            if (campaign.objective or "sales") == "sales"
            else "LINK_CLICKS"
        ),
        "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
        "advantage_audience": 0,
        "placements": list(DEFAULT_PLACEMENTS),
        "audience": primary_audience,
        "targeting": {
            "age_min": primary_audience.get("age_min", campaign.age_min),
            "age_max": primary_audience.get("age_max", campaign.age_max),
            "genders": primary_audience.get("gender", campaign.gender),
            "geo_locations": primary_audience.get("locations")
            or [x for x in [campaign.target_location, campaign.target_country] if x],
            "locales": [campaign.language or "en"],
            "interests": primary_audience.get("interests") or [],
            "behaviors": primary_audience.get("behaviors") or [],
            "custom_audiences": primary_audience.get("custom_audiences") or [],
            "lookalikes": primary_audience.get("lookalikes") or [],
            "retargeting": primary_audience.get("retargeting") or [],
            "targeting_automation": {"advantage_audience": 0},
        },
        "start_time": _now(),
        "page_id": page_id,
        "instagram_actor_id": instagram_id,
    }

    per_ad_budget = round(daily / max(len(meta_assets), 1), 2)
    ads = []
    for idx, asset in enumerate(meta_assets[:6]):
        ads.append(
            {
                "id": f"draft_ad_{uuid.uuid4().hex[:10]}",
                "name": f"{campaign.product_name} — Creative {idx + 1}",
                "status": "DRAFT",
                "adset_id": adset["id"],
                "creative": {
                    "headline": asset.get("headline"),
                    "primary_text": asset.get("primary_text"),
                    "description": asset.get("description"),
                    "cta": asset.get("cta") or "Shop Now",
                    "image_url": asset.get("url"),
                    "link_url": campaign.product_url,
                    "format": asset.get("format") or "meta_feed",
                },
                "budget_share": per_ad_budget,
                "uploaded": False,
            }
        )

    steps = [
        {"step": "create_campaign", "status": "done", "at": _now()},
        {"step": "create_ad_set", "status": "done", "at": _now()},
        {"step": "set_daily_budget", "status": "done", "detail": f"${daily}/day"},
        {"step": "select_audience", "status": "done", "detail": primary_audience.get("name")},
        {"step": "set_placements", "status": "done", "detail": ", ".join(DEFAULT_PLACEMENTS[:3]) + "…"},
        {"step": "upload_creative", "status": "done", "detail": f"{len(ads)} creatives prepared"},
        {"step": "create_ads", "status": "done", "detail": f"{len(ads)} ads in draft"},
        {"step": "publish_campaign", "status": "pending", "detail": "Awaiting review & publish"},
    ]

    return {
        "workflow": "draft_review_publish",
        "status": "draft",
        "mode": "demo_mock" if not ad_account_id or ad_account_id == "act_demo" else "meta_ready",
        "built_at": _now(),
        "reviewed_at": None,
        "published_at": None,
        "campaign": campaign_node,
        "ad_set": adset,
        "ads": ads,
        "steps": steps,
        "notes": (
            "Draft created locally. Review targeting and creatives, then Publish. "
            "With a connected Meta Ad Account, publish maps to Marketing API objects "
            "(demo uses simulated IDs)."
        ),
    }


def mark_in_review(structure: dict) -> dict:
    structure = dict(structure or {})
    structure["status"] = "in_review"
    structure["reviewed_at"] = _now()
    return structure


def publish_structure_mock(structure: dict) -> dict:
    """Flip draft → published with simulated Meta object IDs."""
    structure = dict(structure or {})
    if not structure.get("campaign"):
        raise ValueError("No Meta draft to publish — build draft first")

    pub_id = uuid.uuid4().hex[:12]
    camp = dict(structure["campaign"])
    camp["status"] = "ACTIVE"
    camp["meta_id"] = f"meta_camp_{pub_id}"
    structure["campaign"] = camp

    adset = dict(structure.get("ad_set") or {})
    adset["status"] = "ACTIVE"
    adset["meta_id"] = f"meta_adset_{pub_id}"
    structure["ad_set"] = adset

    ads = []
    for i, ad in enumerate(structure.get("ads") or []):
        item = dict(ad)
        item["status"] = "ACTIVE"
        item["uploaded"] = True
        item["meta_id"] = f"meta_ad_{pub_id}_{i + 1}"
        ads.append(item)
    structure["ads"] = ads

    steps = []
    for step in structure.get("steps") or []:
        s = dict(step)
        if s.get("step") == "publish_campaign":
            s["status"] = "done"
            s["detail"] = f"Published as {camp['meta_id']}"
            s["at"] = _now()
        steps.append(s)
    structure["steps"] = steps
    structure["status"] = "published"
    structure["published_at"] = _now()
    return structure


async def publish_structure(
    structure: dict,
    *,
    publish_ctx=None,
    prefer_live: bool = True,
    require_live: bool = False,
) -> dict:
    """Publish draft — uses Meta Marketing API when a real connection is available."""
    can_live = (
        prefer_live
        and publish_ctx
        and getattr(publish_ctx, "is_real", False)
        and (structure or {}).get("mode") in ("meta_ready", "meta_live", None)
    )
    if require_live and not can_live:
        raise ValueError(
            "Cannot publish to Meta Ads Manager yet. Connect Meta under Account settings, "
            "select an Ad Account and Facebook Page, then rebuild the draft and publish again."
        )
    if can_live:
        from app.integrations.meta.publisher import publish_to_meta

        return await publish_to_meta(structure, publish_ctx)
    return publish_structure_mock(structure)


async def build_draft_for_workspace(
    db,
    campaign: Campaign,
    *,
    assets: list[dict] | None = None,
    workspace_id: str,
) -> dict:
    from app.integrations.meta.context import resolve_publish_context

    ctx = await resolve_publish_context(db, workspace_id)
    return build_draft_structure(
        campaign,
        assets=assets,
        ad_account_id=ctx.ad_account_id if ctx else None,
        page_id=ctx.page_id if ctx else None,
        instagram_id=ctx.instagram_id if ctx else None,
    )


# Backward-compatible alias
publish_structure_sync = publish_structure_mock
