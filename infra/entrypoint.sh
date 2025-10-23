#!/usr/bin/env bash
set -euo pipefail

# Choose data dir: use /data if it exists (paid disk), else /tmp (free-tier)
DATA_DIR="${DATA_DIR:-/data}"
if [[ ! -d "$DATA_DIR" ]]; then
  DATA_DIR="/tmp"
fi

# If DB missing, seed from repo copy
if [[ ! -f "${DATA_DIR}/recipes.db" ]]; then
  echo "[entrypoint] Seeding DB to ${DATA_DIR}/recipes.db"
  mkdir -p "${DATA_DIR}"
  if [[ -f "/app/data/recipes.db" ]]; then
    cp /app/data/recipes.db "${DATA_DIR}/recipes.db"
  else
    # last resort: try to generate it
    python /app/app/db/ingest.py || true
    if [[ -f "/app/data/recipes.db" ]]; then
      cp /app/data/recipes.db "${DATA_DIR}/recipes.db"
    fi
  fi
fi

# If DB_URL not provided, default to the chosen DATA_DIR
export DB_URL="${DB_URL:-sqlite:////${DATA_DIR}/recipes.db}"

exec "$@"
