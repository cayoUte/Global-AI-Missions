#!/bin/sh
# Playwright's webServer: a fresh E2E database, then FastAPI serving the built SPA (one origin).
# Needs PostgreSQL from docker compose (make up) and a built SPA (npm run build).
set -eu
cd "$(dirname "$0")/../../backend"
uv run python ../frontend/e2e/reset_e2e_db.py
uv run alembic upgrade head
uv run python -m seed
exec uv run uvicorn app.main:app --host 127.0.0.1 --port "${E2E_PORT:-8765}"
