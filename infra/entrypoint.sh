#!/usr/bin/env bash
set -euo pipefail

APP_USER=appuser
APP_CMD="uvicorn app.api.main:app --host 0.0.0.0 --port 8000"

# Ensure runtime user exists (matches your Dockerfile useradd)
id -u "${APP_USER}" >/dev/null 2>&1 || useradd -m -u 1001 "${APP_USER}"

# If a volume is mounted at /data, fix ownership (idempotent)
if [[ -d "/data" ]]; then
  echo "[entrypoint] Ensuring /data owned by ${APP_USER}"
  chown -R ${APP_USER}:${APP_USER} /data || true
fi

# Optional: seed DB on first boot (same logic you had)
if [[ -d "/data" && ! -f "/data/recipes.db" && -f "/app/data/recipes.db" ]]; then
  echo "[entrypoint] Seeding DB to /data/recipes.db"
  cp /app/data/recipes.db /data/recipes.db || true
fi

# Drop privileges and exec app as appuser
exec su -s /bin/sh -c "${APP_CMD}" "${APP_USER}"