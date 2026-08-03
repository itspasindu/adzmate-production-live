"""Audience automation: types, AI recommendations, selection."""
from __future__ import annotations

from typing import Any

from app.models import Campaign
from app.services.llm import chat_json, llm_enabled

AUDIENCE_TYPES = [
    "location",
    "demographic",
    "interest",
    "behavior",
    "custom",
    "lookalike",
    "website_visitors",
    "retargeting",
    "customer_list",
]


def _place(campaign: Campaign) -> str:
    loc = getattr(campaign, "target_location", "") or ""
    country = getattr(campaign, "target_country", "") or "United States"
    return f"{loc}, {country}" if loc else country


def recommend_audiences_from_product(campaign: Campaign, creative_suggestions: list[dict] | None = None) -> list[dict]:
    """Rule-based audience pack covering all supported automation types."""
    product = campaign.product_name
    desc = (getattr(campaign, "product_description", None) or campaign.brief or "").lower()
    place = _place(campaign)
    age_min = getattr(campaign, "age_min", 18) or 18
    age_max = getattr(campaign, "age_max", 65) or 65
    gender = getattr(campaign, "gender", "all") or "all"
    language = getattr(campaign, "language", "en") or "en"
    objective = getattr(campaign, "objective", "sales") or "sales"

    interest_seeds = [product]
    if any(w in desc for w in ("run", "trail", "shoe", "fitness", "sport")):
        interest_seeds += ["Running", "Fitness", "Outdoor recreation", "Marathons"]
    elif any(w in desc for w in ("watch", "tech", "smart", "battery")):
        interest_seeds += ["Wearables", "Consumer electronics", "Gadgets"]
    elif any(w in desc for w in ("beauty", "skin", "care", "cosmetic")):
        interest_seeds += ["Beauty", "Skincare", "Self care"]
    else:
        interest_seeds += ["Online shopping", "Brand discovery", "E-commerce"]

    behaviors = ["Engaged shoppers", "Facebook Page engagers"]
    if objective == "sales":
        behaviors.append("Online purchasers")
    if objective == "leads":
        behaviors.append("Form completers")

    pack: list[dict[str, Any]] = [
        {
            "id": "aud_location",
            "type": "location",
            "name": f"{place} geo core",
            "rationale": "Location targeting from campaign setup.",
            "age_min": age_min,
            "age_max": age_max,
            "gender": gender,
            "locations": [place],
            "languages": [language],
            "interests": [],
            "behaviors": [],
            "estimated_reach": "broad",
            "selected": True,
        },
        {
            "id": "aud_demo",
            "type": "demographic",
            "name": f"Ages {age_min}–{age_max} · {gender}",
            "rationale": "Age/gender filters from the brief.",
            "age_min": age_min,
            "age_max": age_max,
            "gender": gender,
            "locations": [place],
            "languages": [language],
            "interests": [],
            "behaviors": [],
            "estimated_reach": "medium",
            "selected": True,
        },
        {
            "id": "aud_interest",
            "type": "interest",
            "name": f"{product} interest stack",
            "rationale": "Interests inferred from product description.",
            "age_min": age_min,
            "age_max": age_max,
            "gender": gender,
            "locations": [place],
            "languages": [language],
            "interests": interest_seeds[:6],
            "behaviors": [],
            "estimated_reach": "medium",
            "selected": True,
        },
        {
            "id": "aud_behavior",
            "type": "behavior",
            "name": "Purchase-intent behaviors",
            "rationale": "People showing shopping and engagement behaviors.",
            "age_min": age_min,
            "age_max": age_max,
            "gender": gender,
            "locations": [place],
            "languages": [language],
            "interests": interest_seeds[:3],
            "behaviors": behaviors,
            "estimated_reach": "medium",
            "selected": False,
        },
        {
            "id": "aud_custom",
            "type": "custom",
            "name": "Custom — CRM engagers",
            "rationale": "Custom audience from people who engaged with your brand assets.",
            "age_min": age_min,
            "age_max": age_max,
            "gender": gender,
            "locations": [place],
            "languages": [language],
            "custom_audiences": ["Page engagers 180d", "Video viewers 50%"],
            "estimated_reach": "narrow",
            "selected": False,
        },
        {
            "id": "aud_lal",
            "type": "lookalike",
            "name": "1% Lookalike — purchasers",
            "rationale": "Lookalike of high-value buyers / converters.",
            "age_min": max(18, age_min - 2),
            "age_max": min(65, age_max + 2),
            "gender": gender,
            "locations": [place],
            "languages": [language],
            "lookalikes": ["LAL 1% Purchasers", "LAL 2% Add-to-cart"],
            "estimated_reach": "broad",
            "selected": False,
        },
        {
            "id": "aud_web",
            "type": "website_visitors",
            "name": "Website visitors 30d",
            "rationale": "People who visited your product or landing page.",
            "age_min": age_min,
            "age_max": age_max,
            "gender": gender,
            "locations": [place],
            "languages": [language],
            "retargeting": ["Site visitors 30d", f"Viewed {product} page"],
            "estimated_reach": "narrow",
            "selected": False,
        },
        {
            "id": "aud_retarget",
            "type": "retargeting",
            "name": "Cart / checkout retargeting",
            "rationale": "Retarget users who added to cart or started checkout.",
            "age_min": age_min,
            "age_max": age_max,
            "gender": gender,
            "locations": [place],
            "languages": [language],
            "retargeting": ["Add to cart 14d", "Initiate checkout 7d"],
            "estimated_reach": "narrow",
            "selected": objective == "sales",
        },
        {
            "id": "aud_list",
            "type": "customer_list",
            "name": "Customer list — past buyers",
            "rationale": "Hashed customer list for exclusion or upsell.",
            "age_min": age_min,
            "age_max": age_max,
            "gender": gender,
            "locations": [place],
            "languages": [language],
            "custom_audiences": ["Customer list — email hash"],
            "estimated_reach": "narrow",
            "selected": False,
        },
    ]

    # Merge AI creative suggestions if present
    if creative_suggestions:
        for idx, sug in enumerate(creative_suggestions[:3]):
            pack.append(
                {
                    "id": f"aud_ai_{idx}",
                    "type": "interest",
                    "name": sug.get("name") or f"AI suggestion {idx + 1}",
                    "rationale": sug.get("rationale") or "From Creative Agent",
                    "age_min": sug.get("age_min", age_min),
                    "age_max": sug.get("age_max", age_max),
                    "gender": sug.get("gender", gender),
                    "locations": sug.get("locations") or [place],
                    "languages": sug.get("languages") or [language],
                    "interests": sug.get("interests") or interest_seeds[:4],
                    "estimated_reach": sug.get("estimated_reach") or "medium",
                    "selected": False,
                    "source": "creative_agent",
                }
            )

    return pack


async def enrich_audiences_with_llm(campaign: Campaign, base: list[dict]) -> list[dict]:
    if not llm_enabled():
        return base
    system = (
        "You recommend Meta Ads audiences from a product description. Return JSON only."
    )
    user = (
        f"Product: {campaign.product_name}\n"
        f"Description: {getattr(campaign, 'product_description', None) or campaign.brief}\n"
        f"Objective: {getattr(campaign, 'objective', 'sales')}\n"
        f"Country: {getattr(campaign, 'target_country', '')}\n\n"
        "Return JSON with key audience_suggestions — array of up to 4 objects with keys:\n"
        "type (interest|behavior|lookalike|retargeting|website_visitors|custom|customer_list),\n"
        "name, rationale, interests (array), behaviors (array), estimated_reach (narrow|medium|broad)."
    )
    data = await chat_json(system, user, temperature=0.4, max_tokens=700)
    if not data or not isinstance(data, dict):
        return base
    extras = data.get("audience_suggestions") or data.get("audiences") or []
    if not isinstance(extras, list):
        return base
    out = list(base)
    for idx, item in enumerate(extras[:4]):
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "id": f"aud_llm_{idx}",
                "type": str(item.get("type") or "interest"),
                "name": str(item.get("name") or f"LLM audience {idx + 1}")[:80],
                "rationale": str(item.get("rationale") or "")[:240],
                "age_min": getattr(campaign, "age_min", 18),
                "age_max": getattr(campaign, "age_max", 65),
                "gender": getattr(campaign, "gender", "all"),
                "locations": [_place(campaign)],
                "languages": [getattr(campaign, "language", "en") or "en"],
                "interests": item.get("interests") or [],
                "behaviors": item.get("behaviors") or [],
                "estimated_reach": item.get("estimated_reach") or "medium",
                "selected": False,
                "source": "llm",
            }
        )
    return out


def build_audience_state(campaign: Campaign, creative_suggestions: list[dict] | None = None) -> dict:
    recommended = recommend_audiences_from_product(campaign, creative_suggestions)
    selected = [a for a in recommended if a.get("selected")]
    return {
        "supported_types": AUDIENCE_TYPES,
        "recommended": recommended,
        "selected": selected or recommended[:3],
        "updated_at": None,
    }


def apply_audience_selection(state: dict, selected_ids: list[str]) -> dict:
    state = dict(state or {})
    recommended = list(state.get("recommended") or [])
    id_set = set(selected_ids)
    for item in recommended:
        item["selected"] = item.get("id") in id_set
    selected = [a for a in recommended if a.get("selected")]
    if not selected and recommended:
        recommended[0]["selected"] = True
        selected = [recommended[0]]
    state["recommended"] = recommended
    state["selected"] = selected
    return state
