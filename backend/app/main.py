"""FastAPI application factory. Run locally with: uv run uvicorn app.main:app --reload"""

from fastapi import FastAPI

from app.api.error_handlers import register_error_handlers
from app.api.middleware import register_middleware
from app.api.routers import attempts, auth, health, world
from app.api.spa import mount_spa
from app.core.config import get_settings
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()  # fail fast on missing or invalid configuration
    configure_logging()

    app = FastAPI(
        title="Global AI Missions API",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    register_error_handlers(app)
    register_middleware(app)
    for module in (health, auth, world, attempts):
        app.include_router(module.router)
    spa_dir = settings.resolved_spa_dir()
    if spa_dir is not None:  # production mode: one origin serves the API and the SPA
        mount_spa(app, spa_dir)
    return app


app = create_app()
