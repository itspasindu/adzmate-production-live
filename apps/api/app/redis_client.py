from __future__ import annotations

import json
import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

_redis = None
_redis_checked = False


async def get_redis():
    """Return async Redis client or None when unavailable."""
    global _redis, _redis_checked
    if _redis_checked:
        return _redis
    _redis_checked = True
    if not settings.redis_url:
        return None
    try:
        from redis.asyncio import Redis

        _redis = Redis.from_url(settings.redis_url, decode_responses=True)
        await _redis.ping()
        logger.info("Redis connected")
        return _redis
    except Exception as exc:
        logger.warning("Redis unavailable (%s) — using in-memory fallbacks", exc)
        _redis = None
        return None


async def redis_health() -> dict[str, Any]:
    client = await get_redis()
    if not client:
        return {"ok": False, "configured": bool(settings.redis_url), "detail": "not connected"}
    try:
        await client.ping()
        return {"ok": True, "configured": True}
    except Exception as exc:
        return {"ok": False, "configured": True, "detail": str(exc)}


async def redis_set_json(key: str, value: dict, ttl_seconds: int = 600) -> bool:
    client = await get_redis()
    if not client:
        return False
    await client.set(key, json.dumps(value), ex=ttl_seconds)
    return True


async def redis_get_json(key: str) -> dict | None:
    client = await get_redis()
    if not client:
        return None
    raw = await client.get(key)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


async def redis_delete(key: str) -> None:
    client = await get_redis()
    if client:
        await client.delete(key)


async def close_redis() -> None:
    global _redis, _redis_checked
    if _redis is not None:
        await _redis.close()
    _redis = None
    _redis_checked = False
