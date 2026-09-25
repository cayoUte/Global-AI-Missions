#!/bin/sh
# Container start (delivery-engineer): fix the DB URL scheme, migrate, seed, then serve.
# Used by the Dockerfile (compose `api` service and Render). Every step is idempotent, so a
# restart or a redeploy is always safe.
set -eu

: "${DATABASE_URL:?DATABASE_URL is required (postgresql+psycopg://user:password@host:5432/db)}"

# Hosted providers (Render, Heroku-style) hand out postgres:// or postgresql:// URLs; the app
# needs the psycopg 3 driver in the SQLAlchemy URL (CHANGE_REQUESTS F-07).
case "$DATABASE_URL" in
  postgres://*) DATABASE_URL="postgresql+psycopg://${DATABASE_URL#postgres://}" ;;
  postgresql://*) DATABASE_URL="postgresql+psycopg://${DATABASE_URL#postgresql://}" ;;
esac
export DATABASE_URL

cd /app/backend

# A freshly created managed database can take a few seconds to accept connections.
tries=0
until alembic upgrade head; do
  tries=$((tries + 1))
  if [ "$tries" -ge 5 ]; then
    echo "entrypoint: migrations failed after $tries attempts" >&2
    exit 1
  fi
  echo "entrypoint: database not ready, retrying in 3 s ($tries/5)" >&2
  sleep 3
done

# Reference data, missions and demo users (idempotent; aborts on invalid content).
python -m seed

# --proxy-headers: X-Forwarded-For/-Proto are honoured only from the addresses in
# FORWARDED_ALLOW_IPS (uvicorn's default: loopback only). See README "Deploy en Render".
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers
