from __future__ import annotations

import logging

from app.config import settings

logger = logging.getLogger(__name__)


async def _enqueue(job_name: str, *args) -> bool:
    if not settings.redis_url:
        return False
    try:
        from arq import create_pool
        from arq.connections import RedisSettings

        redis = RedisSettings.from_dsn(settings.redis_url)
        pool = await create_pool(redis)
        await pool.enqueue_job(job_name, *args)
        await pool.close()
        return True
    except Exception as exc:
        logger.warning("Failed to enqueue %s: %s", job_name, exc)
        return False


async def enqueue_campaign_pipeline(campaign_id: str) -> bool:
    """Queue agent pipeline on Redis when ARQ is available."""
    return await _enqueue("run_campaign_pipeline", campaign_id)


async def enqueue_metrics_sync(campaign_id: str) -> bool:
    return await _enqueue("sync_campaign_metrics_job", campaign_id)
