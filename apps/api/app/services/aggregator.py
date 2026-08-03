from __future__ import annotations

from app.config import settings
from app.services.llm import chat_completion, llm_enabled


def aggregate_signals(
    creative: dict | None,
    sentiment: dict | None,
    strategy: dict | None,
    warnings: list[str],
) -> dict:
    """Deterministic decision gates (authoritative)."""
    creative_ready = float((creative or {}).get("creative_ready", 0.0))
    brand_sentiment = float((sentiment or {}).get("brand_sentiment", 0.5))
    roas = float((strategy or {}).get("roas", 0.0))
    spend_burn = float((strategy or {}).get("spend_burn", 0.0))
    spend = float((strategy or {}).get("spend", 0.0))

    reasons: list[str] = []
    decision = "HOLD"
    confidence = 0.55

    halt_sentiment = brand_sentiment < settings.sentiment_threshold
    halt_roas = roas > 0 and roas < settings.roas_floor

    metrics_launch = (
        creative_ready >= settings.creative_ready_threshold
        and brand_sentiment >= settings.sentiment_threshold
        and roas >= settings.roas_floor
    )

    if halt_sentiment and halt_roas:
        decision = "HALT"
        confidence = 0.92
        reasons.append(
            f"Brand sentiment {brand_sentiment:.2f} below {settings.sentiment_threshold} "
            f"and ROAS {roas:.2f}x below {settings.roas_floor}x"
        )
    elif halt_roas:
        decision = "HALT"
        confidence = 0.88
        reasons.append(f"ROAS {roas:.2f}x is below floor {settings.roas_floor}x — pause spend")
    elif halt_sentiment and creative_ready < settings.creative_ready_threshold:
        decision = "HALT"
        confidence = 0.8
        reasons.append("Weak sentiment and creatives not ready")
    elif halt_sentiment:
        decision = "HOLD"
        confidence = 0.7
        reasons.append(
            f"Brand sentiment {brand_sentiment:.2f} is soft — manager review before launch"
        )
    elif metrics_launch:
        decision = "LAUNCH"
        confidence = 0.9 if not warnings else 0.78
        reasons.append(
            f"Creatives ready ({creative_ready:.0%}), sentiment {brand_sentiment:.2f}, "
            f"ROAS {roas:.2f}x — safe to launch"
        )
        if warnings:
            reasons.append("Proceeding with degraded agent(s): " + "; ".join(warnings))
    else:
        decision = "HOLD"
        confidence = 0.6
        if creative_ready < settings.creative_ready_threshold:
            reasons.append("Creatives not ready")
        if brand_sentiment < settings.sentiment_threshold:
            reasons.append(f"Sentiment {brand_sentiment:.2f} below threshold")
        if roas < settings.roas_floor:
            reasons.append(f"ROAS {roas:.2f}x below floor")
        if not reasons:
            reasons.append("Signals inconclusive — awaiting manager decision")

    return {
        "creative_ready": creative_ready,
        "brand_sentiment": brand_sentiment,
        "roas": roas,
        "spend_burn": spend_burn,
        "spend": spend,
        "decision": decision,
        "decision_reason": " · ".join(reasons),
        "decision_confidence": confidence,
    }


async def enrich_decision_reason(
    agg: dict,
    creative: dict | None,
    sentiment: dict | None,
    strategy: dict | None,
) -> dict:
    """Optionally rewrite decision_reason with an LLM manager brief; decision stays fixed."""
    if not llm_enabled():
        return agg

    system = (
        "You are the Signal Aggregator for a marketing auto-pilot. "
        "Write a crisp manager-facing rationale. Do NOT change the decision. "
        "One or two sentences max. Plain text only."
    )
    user = (
        f"Decision (fixed): {agg['decision']}\n"
        f"Confidence: {agg['decision_confidence']}\n"
        f"Rule reasons: {agg['decision_reason']}\n"
        f"Creative ready: {agg['creative_ready']:.2f} · engine={(creative or {}).get('engine')}\n"
        f"Sentiment: {agg['brand_sentiment']:.2f} · {(sentiment or {}).get('message')}\n"
        f"ROAS: {agg['roas']:.2f}x · spend ${agg['spend']:.0f} · {(strategy or {}).get('message')}\n"
    )
    text = await chat_completion(system, user, temperature=0.25, max_tokens=120)
    if text:
        agg = {**agg, "decision_reason": text.strip(), "reason_engine": f"llm:{settings.llm_model}"}
    return agg
