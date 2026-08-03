# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1001 adzmate \
    && useradd --system --uid 1001 --gid adzmate adzmate

WORKDIR /app

# Repo layout expected by app.config (ROOT = /app)
COPY apps/api/requirements.txt /app/apps/api/requirements.txt
RUN pip install --no-cache-dir -r /app/apps/api/requirements.txt

COPY apps/api /app/apps/api
COPY fixtures /app/fixtures
COPY apps/api/docker-entrypoint.sh /entrypoint.sh

RUN mkdir -p /app/apps/api/uploads /app/apps/api/generated /app/apps/api/previews /app/apps/api/data \
    && chown -R adzmate:adzmate /app \
    && chmod +x /entrypoint.sh

WORKDIR /app/apps/api

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/api/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
