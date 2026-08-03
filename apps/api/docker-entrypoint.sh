#!/bin/sh
# Ensure volume-mounted dirs are writable by the app user.
set -eu
mkdir -p /app/apps/api/data /app/apps/api/uploads /app/apps/api/generated /app/apps/api/previews
chown -R adzmate:adzmate /app/apps/api/data /app/apps/api/uploads /app/apps/api/generated /app/apps/api/previews
exec runuser -u adzmate -- "$@"
