# Global AI Missions — developer commands (delivery-engineer).
# Recipes are POSIX sh: on Windows run `make` from Git Bash (GNU make is not bundled with
# Git for Windows; install it with `winget install ezwinports.make`).
# Backend commands run with uv from backend/ (F-13); frontend commands with npm from frontend/.

.DEFAULT_GOAL := help
.PHONY: help env install app up down reset migrate seed dev-backend dev-frontend test test-backend \
        test-frontend e2e lint lint-backend lint-frontend gen-api validate-content

COMPOSE := docker compose
BACKEND := cd backend &&
FRONTEND := cd frontend &&
OPENAPI_JSON := ../docs/contracts/openapi.json

help: ## List the targets
	@grep -E '^[a-z0-9-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-18s %s\n", $$1, $$2}'

env: ## Create .env from .env.example if it does not exist
	@if [ -f .env ]; then echo ".env already exists (not overwritten)"; \
	else cp .env.example .env && echo "created .env from .env.example"; fi

install: ## Install backend (uv sync) and frontend (npm ci) dependencies
	$(BACKEND) uv sync
	$(FRONTEND) npm ci

app: env ## Build and start the whole app in Docker (PostgreSQL + API + SPA) on http://localhost:8000
	$(COMPOSE) up -d --build

up: env ## Start PostgreSQL 16 and wait until it is healthy
	$(COMPOSE) up -d --wait db

down: ## Stop the stack (keeps the database volume)
	$(COMPOSE) down

reset: env ## Wipe the database volume, start fresh, migrate and seed
	$(COMPOSE) down -v
	$(COMPOSE) up -d --wait db
	@$(MAKE) --no-print-directory migrate
	@$(MAKE) --no-print-directory seed

migrate: env ## Apply Alembic migrations (alembic upgrade head)
	@if [ -f backend/alembic.ini ]; then $(BACKEND) uv run alembic upgrade head; \
	else echo "migrate: not implemented yet (backend/alembic.ini missing; data-engineer)"; fi

seed: env ## Load reference data, missions and demo users (idempotent)
	@if [ -f backend/seed/__main__.py ]; then $(BACKEND) uv run python -m seed; \
	else echo "seed: not implemented yet (backend/seed/__main__.py missing; data-engineer)"; fi

dev-backend: env ## FastAPI with auto-reload on http://127.0.0.1:8000 (after make up migrate seed)
	$(BACKEND) uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

dev-frontend: ## Vite dev server on http://localhost:5173 (proxies /api to 127.0.0.1:8000)
	$(FRONTEND) npm run dev

test: test-backend test-frontend ## Run backend and frontend tests (E2E too with `make test E2E=1`)
	@if [ "$(E2E)" = "1" ]; then $(MAKE) --no-print-directory e2e; fi

test-backend: ## pytest (backend)
	$(BACKEND) uv run pytest

test-frontend: ## Vitest (frontend)
	$(FRONTEND) npm test

e2e: ## Playwright E2E: builds the SPA, serves it from FastAPI over a fresh gam_e2e database (needs `make up`)
	$(FRONTEND) npm run test:e2e

lint: lint-backend lint-frontend ## Lint, format check and typecheck both apps

lint-backend: ## ruff check + ruff format --check
	$(BACKEND) uv run ruff check .
	$(BACKEND) uv run ruff format --check .

lint-frontend: ## ESLint + tsc + Prettier check
	$(FRONTEND) npm run lint
	$(FRONTEND) npm run typecheck
	$(FRONTEND) npm run format:check

gen-api: env ## Export OpenAPI to docs/contracts/openapi.json and regenerate frontend types
	$(BACKEND) uv run python -c 'import json, pathlib; from app.main import app; pathlib.Path("$(OPENAPI_JSON)").write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8")'
	$(FRONTEND) npm run gen:api

validate-content: ## Validate content/ against the JSON Schemas (F-14)
	$(BACKEND) uv run python scripts/validate_content.py
