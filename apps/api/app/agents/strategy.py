from __future__ import annotations

import asyncio
import copy
import json

from app.config import settings
from app.services.llm import chat_json, llm_enabled


def load_base_ads(scenario: str) -> dict:
    path = settings.fixtures_dir / "ads" / "performance.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return copy.deepcopy(data.get(scenario, data["healthy"]))


def compute_metrics(ads: dict) -> dict:
    spend = sum(p["spend"] for p in ads.values())
    revenue = sum(p["revenue"] for p in ads.values())
    roas = (revenue / spend) if spend > 0 else 0.0
    spend_burn = min(1.0, spend / 1500.0)
    return {
        "spend": round(spend, 2),
        "revenue": round(revenue, 2),
        "roas": round(roas, 3),
        "spend_burn": round(spend_burn, 3),
        "platforms": ads,
    }


async def _llm_strategy_narrative(metrics: dict, scenario: str) -> dict | None:
    platforms = {
        name: {
            "spend": p.get("spend"),
            "revenue": p.get("revenue"),
            "status": p.get("status"),
        }
        for name, p in (metrics.get("platforms") or {}).items()
    }
    system = (
        "You are a media strategy agent for multi-platform paid ads. "
        "Be decisive and concise for a marketing manager. Return JSON only."
    )
    user = (
        f"Scenario hint: {scenario}\n"
        f"Blended ROAS: {metrics['roas']:.3f}x (floor {settings.roas_floor}x)\n"
        f"Spend: ${metrics['spend']:.0f} · Revenue: ${metrics['revenue']:.0f}\n"
        f"Spend burn index: {metrics['spend_burn']:.2f}\n"
        f"Platforms: {json.dumps(platforms)}\n\n"
        "Return JSON with keys:\n"
        "summary (1-2 sentences),\n"
        "priority_actions (array of short strings),\n"
        "budget_note (short string)."
    )
    data = await chat_json(system, user, temperature=0.35, max_tokens=450)
    return data if isinstance(data, dict) else None


async def run_strategy_agent(scenario: str, ads_state: dict | None = None) -> dict:
    await asyncio.sleep(0.3)

    if settings.force_fail_agent == "strategy":
        raise RuntimeError("Strategy agent forced failure (demo)")

    ads = ads_state or load_base_ads(scenario)
    metrics = compute_metrics(ads)

    actions: list[dict] = []
    recommendation = None
    engine = "rules"

    if metrics["roas"] < settings.roas_floor:
        recommendation = {
            "type": "pause_ads",
            "title": "Pause low-ROAS campaigns",
            "detail": (
                f"Blended ROAS is {metrics['roas']:.2f}x, below floor {settings.roas_floor}x. "
                "Recommend pausing Meta/Google/TikTok ads within minutes."
            ),
        }
        actions.append({"action": "recommend_pause", "reason": "roas_below_floor"})
    elif metrics["roas"] >= settings.roas_floor * 1.5:
        actions.append({"action": "maintain", "reason": "strong_roas"})
    else:
        actions.append({"action": "watch", "reason": "roas_near_floor"})

    narrative = None
    if llm_enabled():
        narrative = await _llm_strategy_narrative(metrics, scenario)
        if narrative:
            engine = f"rules+llm:{settings.llm_model}"
            if recommendation and narrative.get("summary"):
                recommendation = {
                    **recommendation,
                    "detail": (
                        f"{recommendation['detail']} "
                        f"AI note: {narrative['summary']}"
                    ),
                }

    message = f"Monitored spend ${metrics['spend']:.0f} · ROAS {metrics['roas']:.2f}x"
    if narrative and narrative.get("summary"):
        message = str(narrative["summary"])

    return {
        **metrics,
        "actions": actions,
        "recommendation": recommendation,
        "narrative": narrative,
        "engine": engine,
        "message": message,
    }


def apply_pause(ads: dict) -> dict:
    updated = copy.deepcopy(ads)
    for platform in updated.values():
        platform["status"] = "paused"
    return updated


def apply_resume(ads: dict) -> dict:
    updated = copy.deepcopy(ads)
    for platform in updated.values():
        platform["status"] = "active"
    return updated


def apply_demo_tick(ads: dict, event: str) -> dict:
    updated = copy.deepcopy(ads)
    if event == "spend_spike":
        for platform in updated.values():
            platform["spend"] *= 1.45
            platform["revenue"] *= 0.85
    elif event == "recover":
        for platform in updated.values():
            platform["spend"] *= 0.9
            platform["revenue"] *= 1.35
            platform["status"] = "active"
    elif event == "negative_flood":
        for platform in updated.values():
            platform["revenue"] *= 0.92
    return updated
