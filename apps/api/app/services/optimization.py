"""Automated optimization rules for Meta ad sets / creatives (demo simulation)."""
from __future__ import annotations

import copy
import uuid
from datetime import datetime, timezone
from typing import Any

DEFAULT_RULES: list[dict[str, Any]] = [
    {
        "id": "rule_cpa_high",
        "name": "If CPA > target → reduce budget",
        "metric": "cpa",
        "operator": ">",
        "target_key": "target_cpa",
        "action": "reduce_budget",
        "amount_pct": 20,
        "enabled": True,
    },
    {
        "id": "rule_roas_high",
        "name": "If ROAS > target → increase budget",
        "metric": "roas",
        "operator": ">",
        "target_key": "target_roas",
        "action": "increase_budget",
        "amount_pct": 15,
        "enabled": True,
    },
    {
        "id": "rule_ctr_low",
        "name": "If CTR is low → pause creative",
        "metric": "ctr",
        "operator": "<",
        "target_key": "min_ctr",
        "action": "pause_ad",
        "enabled": True,
    },
    {
        "id": "rule_cpc_high",
        "name": "If CPC is high → test new creative",
        "metric": "cpc",
        "operator": ">",
        "target_key": "max_cpc",
        "action": "flag_new_creative",
        "enabled": True,
    },
    {
        "id": "rule_no_conv",
        "name": "If ad spent $X without conversion → pause",
        "metric": "spend_no_conversion",
        "operator": ">",
        "target_key": "max_spend_no_conversion",
        "action": "pause_ad",
        "enabled": True,
    },
    {
        "id": "rule_winner",
        "name": "If ad performs well → increase budget gradually",
        "metric": "roas",
        "operator": ">",
        "target_key": "winner_roas",
        "action": "increase_ad_budget",
        "amount_pct": 10,
        "enabled": True,
    },
    {
        "id": "rule_frequency",
        "name": "If frequency too high → rotate creative",
        "metric": "frequency",
        "operator": ">",
        "target_key": "max_frequency",
        "action": "rotate_creative",
        "enabled": True,
    },
]


def default_targets(daily_budget: float = 20.0) -> dict[str, float]:
    return {
        "target_cpa": 25.0,
        "target_roas": 2.0,
        "min_ctr": 0.008,
        "max_cpc": 1.5,
        "max_spend_no_conversion": max(15.0, daily_budget * 0.6),
        "winner_roas": 3.0,
        "max_frequency": 3.5,
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_optimization_from_structure(structure: dict, daily_budget: float) -> dict:
    ads = []
    for ad in structure.get("ads") or []:
        share = float(ad.get("budget_share") or (daily_budget / max(len(structure.get("ads") or [1]), 1)))
        ads.append(
            {
                "ad_id": ad.get("id"),
                "meta_id": ad.get("meta_id"),
                "name": ad.get("name"),
                "status": "active",
                "daily_budget": share,
                "spend": 0.0,
                "impressions": 0,
                "clicks": 0,
                "conversions": 0,
                "revenue": 0.0,
                "ctr": 0.0,
                "cpc": 0.0,
                "cpa": 0.0,
                "roas": 0.0,
                "frequency": 1.0,
            }
        )
    return {
        "enabled": True,
        "targets": default_targets(daily_budget),
        "rules": copy.deepcopy(DEFAULT_RULES),
        "ads": ads,
        "ad_set_daily_budget": daily_budget,
        "actions_log": [
            {
                "id": str(uuid.uuid4()),
                "at": _now(),
                "action": "init",
                "detail": f"Started {len(ads)} creatives at ${daily_budget:.0f}/day total",
            }
        ],
        "day": 0,
        "needs_new_creative": False,
    }


def _compare(value: float, operator: str, target: float) -> bool:
    if operator == ">":
        return value > target
    if operator == "<":
        return value < target
    if operator == ">=":
        return value >= target
    if operator == "<=":
        return value <= target
    return False


def simulate_performance_day(state: dict, scenario: str = "mixed") -> dict:
    """Advance one simulated day of ad performance (running-shoes style)."""
    import random

    state = copy.deepcopy(state)
    state["day"] = int(state.get("day") or 0) + 1
    rng = random.Random(1000 + state["day"] * 17)
    ads = state.get("ads") or []
    active = [a for a in ads if a.get("status") == "active"]
    if not active:
        return state

    for idx, ad in enumerate(ads):
        if ad.get("status") != "active":
            continue
        budget = float(ad.get("daily_budget") or 5.0)
        # Vary quality so winners emerge
        quality = 0.55 + (idx % 3) * 0.18
        if scenario == "decline" and state["day"] > 3:
            quality *= 0.7
        spend = round(min(budget, budget * (0.85 + rng.random() * 0.2)), 2)
        impressions = int(spend / 0.012 * (0.8 + rng.random() * 0.4))
        ctr = max(0.002, quality * 0.02 * (0.7 + rng.random() * 0.6))
        clicks = max(0, int(impressions * ctr))
        cvr = max(0.005, quality * 0.04 * (0.6 + rng.random() * 0.8))
        conversions = max(0, int(clicks * cvr)) if clicks else 0
        # Occasionally zero conversions for no-conv rule
        if idx == len(ads) - 1 and state["day"] < 3:
            conversions = 0
        aov = 60 + rng.random() * 40
        revenue = round(conversions * aov, 2)
        ad["spend"] = round(float(ad.get("spend") or 0) + spend, 2)
        ad["impressions"] = int(ad.get("impressions") or 0) + impressions
        ad["clicks"] = int(ad.get("clicks") or 0) + clicks
        ad["conversions"] = int(ad.get("conversions") or 0) + conversions
        ad["revenue"] = round(float(ad.get("revenue") or 0) + revenue, 2)
        ad["ctr"] = round((ad["clicks"] / ad["impressions"]) if ad["impressions"] else 0.0, 4)
        ad["cpc"] = round((ad["spend"] / ad["clicks"]) if ad["clicks"] else 0.0, 2)
        ad["cpa"] = round((ad["spend"] / ad["conversions"]) if ad["conversions"] else 999.0, 2)
        ad["roas"] = round((ad["revenue"] / ad["spend"]) if ad["spend"] else 0.0, 2)
        ad["frequency"] = round(1.0 + state["day"] * (0.35 + idx * 0.15), 2)
        ad["day_spend"] = spend
        ad["day_conversions"] = conversions

    state["ads"] = ads
    return state


def evaluate_rules(state: dict) -> dict:
    """Apply enabled rules; mutate budgets/statuses; append action log."""
    state = copy.deepcopy(state)
    targets = state.get("targets") or default_targets()
    rules = state.get("rules") or DEFAULT_RULES
    ads = state.get("ads") or []
    log = list(state.get("actions_log") or [])
    total_budget = float(state.get("ad_set_daily_budget") or sum(float(a.get("daily_budget") or 0) for a in ads))

    for rule in rules:
        if not rule.get("enabled", True):
            continue
        metric = rule["metric"]
        op = rule["operator"]
        target = float(targets.get(rule["target_key"], 0))
        action = rule["action"]
        pct = float(rule.get("amount_pct") or 10)

        for ad in ads:
            if ad.get("status") != "active" and action not in ("rotate_creative",):
                continue

            value = None
            if metric == "cpa":
                if not ad.get("conversions"):
                    continue
                value = float(ad.get("cpa") or 0)
            elif metric == "roas":
                value = float(ad.get("roas") or 0)
            elif metric == "ctr":
                value = float(ad.get("ctr") or 0)
            elif metric == "cpc":
                if not ad.get("clicks"):
                    continue
                value = float(ad.get("cpc") or 0)
            elif metric == "spend_no_conversion":
                if int(ad.get("conversions") or 0) > 0:
                    continue
                value = float(ad.get("spend") or 0)
            elif metric == "frequency":
                value = float(ad.get("frequency") or 0)
            else:
                continue

            if value is None or not _compare(value, op, target):
                continue

            detail = ""
            if action == "reduce_budget":
                before = float(ad.get("daily_budget") or 0)
                ad["daily_budget"] = round(max(1.0, before * (1 - pct / 100)), 2)
                detail = f"{ad['name']}: budget ${before:.2f} → ${ad['daily_budget']:.2f} (CPA ${value:.2f})"
            elif action == "increase_budget":
                before = float(state.get("ad_set_daily_budget") or total_budget)
                state["ad_set_daily_budget"] = round(before * (1 + pct / 100), 2)
                # scale active ads
                active = [a for a in ads if a.get("status") == "active"]
                if active:
                    share = state["ad_set_daily_budget"] / len(active)
                    for a in active:
                        a["daily_budget"] = round(share, 2)
                detail = f"Ad set budget → ${state['ad_set_daily_budget']:.2f} (ROAS strong)"
            elif action == "increase_ad_budget":
                before = float(ad.get("daily_budget") or 0)
                ad["daily_budget"] = round(before * (1 + pct / 100), 2)
                detail = f"{ad['name']}: winner budget ${before:.2f} → ${ad['daily_budget']:.2f} (ROAS {value:.2f}x)"
            elif action == "pause_ad":
                ad["status"] = "paused"
                detail = f"Paused {ad['name']} ({rule['name']}; value={value})"
                # redistribute budget to winners
                active = [a for a in ads if a.get("status") == "active"]
                if active:
                    pool = float(state.get("ad_set_daily_budget") or total_budget)
                    share = pool / len(active)
                    for a in active:
                        a["daily_budget"] = round(share, 2)
            elif action == "flag_new_creative":
                state["needs_new_creative"] = True
                detail = f"Flagged new creative test — {ad['name']} CPC ${value:.2f}"
            elif action == "rotate_creative":
                ad["status"] = "paused"
                state["needs_new_creative"] = True
                detail = f"Rotated {ad['name']} — frequency {value:.1f} too high"
            else:
                continue

            log.append(
                {
                    "id": str(uuid.uuid4()),
                    "at": _now(),
                    "rule_id": rule["id"],
                    "action": action,
                    "ad_id": ad.get("ad_id"),
                    "detail": detail,
                }
            )
            # One action per rule per day for increase_budget at adset level
            if action == "increase_budget":
                break

    # Rebalance if all paused somehow
    if not any(a.get("status") == "active" for a in ads) and ads:
        ads[0]["status"] = "active"
        ads[0]["daily_budget"] = float(state.get("ad_set_daily_budget") or 20)
        log.append(
            {
                "id": str(uuid.uuid4()),
                "at": _now(),
                "action": "safeguard",
                "detail": "Re-activated best ad — all creatives were paused",
            }
        )

    state["ads"] = ads
    state["actions_log"] = log[-80:]
    return state


def run_optimization_tick(state: dict, scenario: str = "mixed") -> dict:
    state = simulate_performance_day(state, scenario=scenario)
    state = evaluate_rules(state)
    return state


def update_rules(state: dict, rules: list[dict] | None = None, targets: dict | None = None) -> dict:
    state = copy.deepcopy(state or {})
    if rules is not None:
        state["rules"] = rules
    if targets is not None:
        merged = dict(state.get("targets") or default_targets())
        merged.update(targets)
        state["targets"] = merged
    return state
