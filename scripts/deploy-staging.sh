#!/usr/bin/env bash
# Deploy AdzMate staging on a VPS via Docker Compose + GHCR images.
# Invoked over SSH by GitHub Actions (deploy-staging.yml).
set -euo pipefail

DEPLOY_DIR="${DEPLOY_DIR:-$HOME/adzmate}"
API_IMAGE="${API_IMAGE:?API_IMAGE required}"
WEB_IMAGE="${WEB_IMAGE:?WEB_IMAGE required}"
GHCR_TOKEN="${GHCR_TOKEN:?GHCR_TOKEN required}"
GHCR_USER="${GHCR_USER:?GHCR_USER required}"

mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

if [[ ! -f docker-compose.staging.yml ]]; then
  echo "ERROR: docker-compose.staging.yml missing in $DEPLOY_DIR"
  echo "Copy it from the repo once during VPS bootstrap."
  exit 1
fi

if [[ ! -f .env.staging ]]; then
  echo "ERROR: .env.staging missing in $DEPLOY_DIR"
  echo "Copy .env.staging.example and fill secrets on the VPS."
  exit 1
fi

# Persist image tags for compose variable substitution
{
  echo "API_IMAGE=${API_IMAGE}"
  echo "WEB_IMAGE=${WEB_IMAGE}"
} > .images.env

echo "${GHCR_TOKEN}" | docker login ghcr.io -u "${GHCR_USER}" --password-stdin

docker compose \
  --env-file .env.staging \
  --env-file .images.env \
  -f docker-compose.staging.yml \
  pull

docker compose \
  --env-file .env.staging \
  --env-file .images.env \
  -f docker-compose.staging.yml \
  up -d --remove-orphans

# Wait for health
echo "Waiting for containers to become healthy..."
for i in $(seq 1 30); do
  api_h=$(docker compose --env-file .env.staging --env-file .images.env -f docker-compose.staging.yml ps --format json 2>/dev/null \
    | grep -c '"Healthy"' || true)
  if [[ "${api_h}" -ge 1 ]]; then
    echo "At least one service healthy."
    break
  fi
  sleep 5
done

docker compose \
  --env-file .env.staging \
  --env-file .images.env \
  -f docker-compose.staging.yml \
  ps

docker image prune -f >/dev/null 2>&1 || true
echo "Deploy finished."
