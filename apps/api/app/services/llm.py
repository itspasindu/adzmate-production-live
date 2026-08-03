"""LLM client for AdzMate agents (OpenAI-compatible HTTP API).

Supported providers:
- Google Gemini (recommended): GEMINI_API_KEY → OpenAI-compat endpoint
- OpenAI: OPENAI_API_KEY
- Groq / OpenRouter / Ollama / Azure: set LLM_BASE_URL + LLM_API_KEY

Falls back gracefully when LLM is off or the key is missing.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GEMINI_OPENAI_BASE = "https://generativelanguage.googleapis.com/v1beta/openai/"


def llm_enabled() -> bool:
    return bool(settings.use_llm and settings.llm_api_key)


def llm_provider() -> str:
    return settings.llm_provider or "custom"


async def chat_completion(
    system: str,
    user: str,
    *,
    temperature: float = 0.4,
    max_tokens: int = 800,
    json_mode: bool = False,
) -> str | None:
    """Return assistant text, or None if LLM is disabled / fails."""
    if not llm_enabled():
        return None

    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    body: dict[str, Any] = {
        "model": settings.llm_model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    # Gemini's OpenAI-compat layer is happiest without response_format for some models
    if json_mode and settings.llm_provider != "gemini":
        body["response_format"] = {"type": "json_object"}

    base = settings.llm_base_url.rstrip("/")
    url = f"{base}/chat/completions"
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(url, headers=headers, json=body)
            if res.status_code >= 400:
                logger.warning(
                    "LLM HTTP %s (%s): %s",
                    res.status_code,
                    settings.llm_provider,
                    res.text[:400],
                )
                res.raise_for_status()
            data = res.json()
            content = data["choices"][0]["message"]["content"]
            return (content or "").strip() or None
    except Exception as exc:
        logger.warning("LLM call failed (%s): %s", settings.llm_provider, exc)
        return None


async def chat_json(
    system: str,
    user: str,
    *,
    temperature: float = 0.3,
    max_tokens: int = 1000,
) -> dict | list | None:
    """Ask the model for JSON and parse it. Returns None on failure."""
    # Prefer explicit JSON instruction for Gemini; optional response_format for OpenAI
    json_system = system + "\nRespond with valid JSON only, no markdown fences."
    raw = await chat_completion(
        json_system,
        user,
        temperature=temperature,
        max_tokens=max_tokens,
        json_mode=settings.llm_provider != "gemini",
    )
    if not raw:
        raw = await chat_completion(
            json_system,
            user,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=False,
        )
    if not raw:
        return None
    return _parse_json(raw)


def _parse_json(raw: str) -> dict | list | None:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None
