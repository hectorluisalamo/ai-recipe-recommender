#!/usr/bin/env bash
set -euo pipefail

# Prefer /data if present (paid disk), else /tmp on free tier
DATA_DIR='${DATA_DIR:-/data}'
if [[ ! -d '$DATA_DIR' ]]; then
  DATA_DIR='/tmp'
fi

# Seed DB on first boot
if [[ ! -f '${DATA_DIR}/recipes.db' ]]; then
  echo '[entrypoint] Seeding DB to ${DATA_DIR}/recipes.db'
  mkdir -p '${DATA_DIR}'
  if [[ -f '/app/data/recipes.db' ]]; then
    cp /app/data/recipes.db '${DATA_DIR}/recipes.db'
  else
    # Try to generate from CSV if present
    python /app/app/db/ingest.py || true
    if [[ -f '/app/data/recipes.db' ]]; then
      cp /app/data/recipes.db '${DATA_DIR}/recipes.db'
    fi
  fi
fi

# Default DB_URL if not provided
export DB_URL='${DB_URL:-sqlite:////${DATA_DIR}/recipes.db}'

exec '$@'
