from __future__ import annotations

from app.config import settings
from app.models import Campaign
from app.schemas import CampaignCreate
from app.storage import resolve_asset_url


OBJECTIVE_TO_GOAL = {
    "sales": "conversions",
    "leads": "leads",
    "traffic": "traffic",
    "engagement": "engagement",
}


def normalize_create(data: CampaignCreate) -> CampaignCreate:
    """Fill derived fields (brief, budget, goal) from product/targeting inputs."""
    objective = (data.objective or "sales").lower().strip()
    if objective not in OBJECTIVE_TO_GOAL:
        objective = "sales"
    description = (data.product_description or data.brief or "").strip()
    brief = data.brief.strip() if data.brief and data.brief.strip() else description
    if not brief:
        brief = f"Promote {data.product_name} by {data.brand_name}."
    daily = float(data.daily_budget or 50.0)
    days = max(1, int(data.duration_days or 14))
    total = daily * days
    goal = OBJECTIVE_TO_GOAL[objective]
    age_min = max(13, min(int(data.age_min or 18), 65))
    age_max = max(age_min, min(int(data.age_max or 65), 65))
    return data.model_copy(
        update={
            "objective": objective,
            "product_description": description,
            "brief": brief,
            "daily_budget": daily,
            "duration_days": days,
            "budget": total,
            "goal": goal,
            "gender": (data.gender or "all").lower(),
            "language": (data.language or "en").lower(),
            "age_min": age_min,
            "age_max": age_max,
        }
    )


def build_campaign(
    *,
    campaign_id: str,
    workspace_id: str,
    data: CampaignCreate,
    product_image_path: str | None = None,
    mock_ads: dict | None = None,
) -> Campaign:
    data = normalize_create(data)
    campaign = Campaign(
        id=campaign_id,
        workspace_id=workspace_id,
        name=data.name,
        client_name=data.client_name,
        brand_name=data.brand_name,
        product_name=data.product_name,
        brief=data.brief,
        product_description=data.product_description,
        product_url=data.product_url,
        goal=data.goal,
        objective=data.objective,
        budget=data.budget,
        daily_budget=data.daily_budget,
        duration_days=data.duration_days,
        target_country=data.target_country or "",
        target_location=data.target_location or "",
        age_min=data.age_min,
        age_max=max(data.age_min, data.age_max),
        gender=data.gender,
        language=data.language,
        brand_primary=data.brand_primary,
        brand_accent=data.brand_accent,
        scenario=data.scenario,
        status="received",
        product_image_path=product_image_path,
        mock_ads=mock_ads or {},
        auto_pause_enabled=True,
    )
    campaign.platforms = data.platforms
    return campaign


def campaign_to_out(c: Campaign) -> dict:
    image_url = resolve_asset_url(c.product_image_path)
    if not image_url and c.product_image_path:
        image_url = f"{settings.public_base_url.rstrip('/')}/uploads/{c.id}/product.png"

    landing_url = c.cloudfront_url or resolve_asset_url(
        f"previews/{c.id}/index.html" if c.landing_page_path else None
    )
    if not landing_url and c.landing_page_path:
        landing_url = f"{settings.public_base_url.rstrip('/')}/previews/{c.id}/"

    return {
        "id": c.id,
        "workspace_id": c.workspace_id or None,
        "name": c.name,
        "client_name": c.client_name,
        "brand_name": c.brand_name,
        "product_name": c.product_name,
        "brief": c.brief,
        "product_description": getattr(c, "product_description", "") or "",
        "product_url": getattr(c, "product_url", None),
        "goal": c.goal,
        "objective": getattr(c, "objective", None) or "sales",
        "budget": c.budget,
        "daily_budget": getattr(c, "daily_budget", None) or 50.0,
        "duration_days": getattr(c, "duration_days", None) or 14,
        "target_country": getattr(c, "target_country", None) or "",
        "target_location": getattr(c, "target_location", None) or "",
        "age_min": getattr(c, "age_min", None) or 18,
        "age_max": getattr(c, "age_max", None) or 65,
        "gender": getattr(c, "gender", None) or "all",
        "language": getattr(c, "language", None) or "en",
        "platforms": c.platforms,
        "brand_primary": c.brand_primary,
        "brand_accent": c.brand_accent,
        "scenario": c.scenario,
        "status": c.status,
        "product_image_url": image_url,
        "decision": c.decision,
        "decision_reason": c.decision_reason,
        "decision_confidence": c.decision_confidence,
        "landing_page_url": landing_url,
        "cloudfront_url": c.cloudfront_url,
        "warnings": c.warnings,
        "publish_status": getattr(c, "publish_status", None) or "none",
        "auto_pause_enabled": bool(getattr(c, "auto_pause_enabled", True)),
        "meta_structure": getattr(c, "meta_structure", None) or {},
        "audiences": getattr(c, "audiences", None) or {},
        "optimization": getattr(c, "optimization", None) or {},
        "created_at": c.created_at,
        "updated_at": c.updated_at,
    }
