#!/bin/sh
# Backend container entrypoint: migrate -> seed identity -> exec the CMD.
#
# `alembic upgrade head` runs as the admin role (env.py default, or
# ALEMBIC_DATABASE_URL). The seed loader runs as the app role (DATABASE_URL,
# set by compose.yaml) and is idempotent -- guarded by the seed_marker row
# from migration 0003, so a second `docker compose up` re-runs both steps
# harmlessly. The committed identity dataset is bind-mounted at /seed/data.
set -e

echo "[entrypoint] alembic upgrade head"
uv run alembic upgrade head

echo "[entrypoint] seed loader (identity only; clinical is Phase 2)"
uv run python -m app.db.seed_loader

echo "[entrypoint] exec: $*"
exec "$@"
