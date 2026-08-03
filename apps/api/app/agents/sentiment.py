from __future__ import annotations

import asyncio
import json
import re

from app.config import settings
from app.services.llm import chat_json, llm_enabled

# Lexicon approximates DistilBERT SST-2 polarity for reliable offline demos.
POSITIVE = {
    "love", "best", "great", "amazing", "excellent", "impressed", "premium",
    "fast", "solid", "wow", "perfect", "recommend", "beautiful", "happy",
    "quality", "helpful", "worth", "fantastic", "awesome", "good",
}
NEGATIVE = {
    "hate", "worst", "terrible", "awful", "waste", "scam", "broken", "broke",
    "refund", "poor", "bad", "disappointed", "fake", "misleading", "ignored",
    "overpriced", "junk", "never", "return", "damaged", "slow", "meh",
}

_pipeline = None
_pipeline_checked = False


def _try_load_distilbert():
    global _pipeline, _pipeline_checked
    if _pipeline_checked:
        return _pipeline
    _pipeline_checked = True
    if not settings.use_distilbert:
        _pipeline = None
        return None
    try:
        from transformers import pipeline

        _pipeline = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
        )
    except Exception:
        _pipeline = None
    return _pipeline


def _lexicon_score(text: str) -> tuple[float, str]:
    tokens = set(re.findall(r"[a-zA-Z']+", text.lower()))
    pos = len(tokens & POSITIVE)
    neg = len(tokens & NEGATIVE)
    if pos == 0 and neg == 0:
        return 0.5, "NEUTRAL"
    if neg > pos:
        score = max(0.05, 0.45 - 0.12 * (neg - pos))
        label = "NEGATIVE"
    elif pos > neg:
        score = min(0.95, 0.55 + 0.12 * (pos - neg))
        label = "POSITIVE"
    else:
        score = 0.5
        label = "NEUTRAL"
    return score, label


def _score_comment(text: str) -> dict:
    pipe = _try_load_distilbert()
    if pipe is not None:
        result = pipe(text[:512])[0]
        label = result["label"]
        conf = float(result["score"])
        if label.upper().startswith("POS"):
            sentiment = 0.5 + conf / 2
        else:
            sentiment = 0.5 - conf / 2
        return {
            "text": text,
            "label": label,
            "score": round(sentiment, 3),
            "engine": "distilbert-sst2",
        }

    score, label = _lexicon_score(text)
    return {
        "text": text,
        "label": label,
        "score": round(score, 3),
        "engine": "distilbert-compatible-lexicon",
    }


def load_comments(scenario: str) -> list[dict]:
    path = settings.fixtures_dir / "comments" / f"{scenario}.json"
    if not path.exists():
        path = settings.fixtures_dir / "comments" / "healthy.json"
    return json.loads(path.read_text(encoding="utf-8"))


async def _llm_brand_insight(scored: list[dict], brand_score: float, trend: str) -> dict | None:
    samples = [
        {"text": s["text"][:160], "label": s["label"], "score": s["score"], "platform": s.get("platform")}
        for s in scored[:12]
    ]
    system = (
        "You are a brand reputation analyst for performance marketing. "
        "Summarize social sentiment for a campaign manager. Return JSON only."
    )
    user = (
        f"Aggregate brand sentiment score: {brand_score:.3f} (0-1)\n"
        f"Trend: {trend}\n"
        f"Comment sample:\n{json.dumps(samples, ensure_ascii=False)}\n\n"
        "Return JSON with keys:\n"
        "summary (1-2 sentences),\n"
        "risks (array of short strings),\n"
        "opportunities (array of short strings),\n"
        "recommended_action (one of: launch_ok, hold_review, pause_crisis)."
    )
    data = await chat_json(system, user, temperature=0.3, max_tokens=500)
    return data if isinstance(data, dict) else None


async def run_sentiment_agent(scenario: str, extra_comments: list[dict] | None = None) -> dict:
    await asyncio.sleep(0.3)

    if settings.force_fail_agent == "sentiment":
        raise RuntimeError("Sentiment agent forced failure (demo)")

    comments = load_comments(scenario)
    if extra_comments:
        comments = comments + extra_comments

    scored = [_score_comment(c["text"]) for c in comments]
    for i, c in enumerate(comments):
        scored[i]["platform"] = c.get("platform", "meta")
        scored[i]["author"] = c.get("author", "user")

    brand_score = sum(s["score"] for s in scored) / max(len(scored), 1)
    positives = sum(1 for s in scored if s["score"] >= 0.6)
    negatives = sum(1 for s in scored if s["score"] <= 0.4)

    if brand_score >= 0.65:
        trend = "rising"
    elif brand_score <= 0.45:
        trend = "falling"
    else:
        trend = "flat"

    quotes = sorted(scored, key=lambda s: s["score"])
    sample = quotes[:2] + quotes[-2:]

    engine = scored[0]["engine"] if scored else "none"
    insight = None
    if llm_enabled() and scored:
        insight = await _llm_brand_insight(scored, brand_score, trend)
        if insight:
            engine = f"{engine}+llm:{settings.llm_model}"

    message = f"Scored {len(scored)} comments via {engine}; brand score {brand_score:.2f} ({trend})"
    if insight and insight.get("summary"):
        message = str(insight["summary"])

    return {
        "brand_sentiment": round(brand_score, 3),
        "trend": trend,
        "positives": positives,
        "negatives": negatives,
        "total_comments": len(scored),
        "samples": sample,
        "insight": insight,
        "engine": engine,
        "message": message,
    }
