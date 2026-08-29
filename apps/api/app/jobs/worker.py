"""ARQ worker — run from apps/api: arq app.jobs.worker.WorkerSettings"""

from __future__ import annotations

from arq.connections import RedisSettings

from app.config import settings
from app.jobs.tasks import run_campaign_pipeline, sync_campaign_metrics_job


class WorkerSettings:
    functions = [run_campaign_pipeline, sync_campaign_metrics_job]
    redis_settings = RedisSettings.from_dsn(settings.redis_url or "redis://localhost:6379")
    max_jobs = 10
    job_timeout = 600
