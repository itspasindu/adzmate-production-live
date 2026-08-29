"""ARQ worker — run from apps/api: arq app.jobs.worker.WorkerSettings"""

from __future__ import annotations

from arq.connections import RedisSettings
from arq.cron import cron

from app.config import settings
from app.jobs.tasks import run_campaign_pipeline, sync_all_live_metrics, sync_campaign_metrics_job


class WorkerSettings:
    functions = [run_campaign_pipeline, sync_campaign_metrics_job, sync_all_live_metrics]
    redis_settings = RedisSettings.from_dsn(settings.redis_url or "redis://localhost:6379")
    max_jobs = 10
    job_timeout = 600
    # Every 6 hours: sync Meta Insights for live campaigns
    cron_jobs = [
        cron(
            "sync_all_live_metrics",
            hour={0, 6, 12, 18},
            minute=0,
            run_at_startup=False,
        ),
    ]
