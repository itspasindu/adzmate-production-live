#!/usr/bin/env bash
# Post-deploy smoke checks against staging URLs.
set -euo pipefail

WEB_URL="${STAGING_WEB_URL:?STAGING_WEB_URL required}"
API_URL="${STAGING_API_URL:?STAGING_API_URL required}"

WEB_URL="${WEB_URL%/}"
API_URL="${API_URL%/}"

echo "Smoke: API health → ${API_URL}/api/health"
curl -fsS --retry 5 --retry-delay 3 --retry-all-errors "${API_URL}/api/health" | tee /tmp/adzmate-health.json
grep -qi . /tmp/adzmate-health.json

echo "Smoke: API root → ${API_URL}/"
curl -fsS --retry 3 --retry-delay 2 "${API_URL}/" >/dev/null

echo "Smoke: Web → ${WEB_URL}/"
code=$(curl -sS -o /tmp/adzmate-web.html -w "%{http_code}" --retry 5 --retry-delay 3 --retry-all-errors "${WEB_URL}/")
if [[ "${code}" != "200" && "${code}" != "307" && "${code}" != "308" ]]; then
  echo "ERROR: web returned HTTP ${code}"
  exit 1
fi

echo "All smoke checks passed."
