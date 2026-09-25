# syntax=docker/dockerfile:1
# Global AI Missions — production image (delivery-engineer).
# One image, one origin: FastAPI serves the API under /api and the built React SPA at /.
#
#   docker build -t global-ai-missions .
#   docker compose up -d --build            # the same image, with PostgreSQL (docker-compose.yml)
#
# On start, docker/entrypoint.sh applies the migrations, runs the idempotent seed and starts
# uvicorn on $PORT (default 8000). Render builds this same file (render.yaml).
#
# Builds behind a TLS-intercepting proxy can pass its CA as an optional BuildKit secret:
#   docker build --secret id=extra_ca,src=/path/to/ca.crt .
# Without the secret (the normal case) nothing changes.

ARG NODE_VERSION=22
ARG PYTHON_VERSION=3.12
ARG UV_VERSION=0.8.17

# --- Stage 1: build the SPA (frontend/dist) ------------------------------------
FROM node:${NODE_VERSION}-bookworm-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN --mount=type=secret,id=extra_ca,required=false \
    --mount=type=cache,target=/root/.npm \
    if [ -f /run/secrets/extra_ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/extra_ca; fi; \
    npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# --- Stage 2: backend dependencies (locked, no dev group) into /opt/venv ----------
FROM python:${PYTHON_VERSION}-slim-bookworm AS backend-deps
ARG UV_VERSION
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN --mount=type=secret,id=extra_ca,required=false \
    --mount=type=cache,target=/root/.cache \
    if [ -f /run/secrets/extra_ca ]; then \
        export PIP_CERT=/run/secrets/extra_ca SSL_CERT_FILE=/run/secrets/extra_ca; \
    fi; \
    pip install --no-cache-dir --disable-pip-version-check --root-user-action=ignore "uv==${UV_VERSION}" \
    && uv sync --locked --no-dev --no-install-project

# --- Stage 3: runtime ------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH \
    PORT=8000

# Layout mirrors the repository, so app.core.config.REPO_ROOT (= /app) finds content/,
# docs/contracts/ (the seed validates content against the JSON Schemas) and frontend/dist/.
WORKDIR /app/backend
COPY --from=backend-deps /opt/venv /opt/venv
COPY backend/ ./
COPY content/ /app/content/
COPY docs/contracts/catalog.schema.json docs/contracts/items.schema.json \
     docs/contracts/mission.schema.json /app/docs/contracts/
COPY --from=frontend /app/frontend/dist /app/frontend/dist
COPY --chmod=755 docker/entrypoint.sh /usr/local/bin/entrypoint.sh

# Unprivileged user; the app never writes to its own files.
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin app
USER app

EXPOSE 8000
ENTRYPOINT ["entrypoint.sh"]
