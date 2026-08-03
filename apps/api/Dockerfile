# syntax=docker/dockerfile:1
# Build context = apps/api (NOT the monorepo root).
#
# Render Docker settings:
#   Root Directory  = apps/api
#   Dockerfile Path = Dockerfile
#   Docker Context  = .          ← blank or ".", never "apps/api"
#
# Local:
#   docker build -t adzmate-api -f apps/api/Dockerfile apps/api
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

# Keep monorepo paths so app.config ROOT (= parents[3]) resolves to /app
COPY requirements.txt /app/apps/api/requirements.txt
RUN pip install --no-cache-dir -r /app/apps/api/requirements.txt

COPY . /app/apps/api
COPY docker-entrypoint.sh /entrypoint.sh

# Expose fixtures at /app/fixtures for ROOT / "fixtures" lookups
RUN if [ -d /app/apps/api/fixtures ]; then \
      mkdir -p /app/fixtures \
      && cp -a /app/apps/api/fixtures/. /app/fixtures/; \
    fi \
    && mkdir -p /app/apps/api/uploads /app/apps/api/generated /app/apps/api/previews /app/apps/api/data \
    && chown -R adzmate:adzmate /app \
    && chmod +x /entrypoint.sh

WORKDIR /app/apps/api

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/api/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
# Render sets $PORT — set Docker Command to:
#   uvicorn app.main:app --host 0.0.0.0 --port $PORT
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
