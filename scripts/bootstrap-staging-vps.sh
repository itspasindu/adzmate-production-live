#!/usr/bin/env bash
# One-time VPS bootstrap for AdzMate staging.
# Run as the deploy user on the VPS (user must be in the docker group).
set -euo pipefail

DEPLOY_DIR="${DEPLOY_DIR:-$HOME/adzmate}"

echo "==> Creating ${DEPLOY_DIR}"
mkdir -p "${DEPLOY_DIR}/scripts"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: Docker is not installed. Install Docker Engine + Compose plugin first."
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "ERROR: Docker Compose plugin missing (docker compose)."
  exit 1
fi

if [[ ! -f "${DEPLOY_DIR}/docker-compose.staging.yml" ]]; then
  echo "Copy docker-compose.staging.yml from the repo into ${DEPLOY_DIR}/"
  exit 1
fi

if [[ ! -f "${DEPLOY_DIR}/.env.staging" ]]; then
  if [[ -f "${DEPLOY_DIR}/.env.staging.example" ]]; then
    cp "${DEPLOY_DIR}/.env.staging.example" "${DEPLOY_DIR}/.env.staging"
    echo "Created .env.staging from example — EDIT SECRETS before first deploy."
  else
    echo "ERROR: Missing .env.staging (and no .env.staging.example)."
    exit 1
  fi
fi

chmod 600 "${DEPLOY_DIR}/.env.staging" || true
echo "==> Bootstrap OK. Push to the staging branch (or run Deploy Staging workflow) to ship."
