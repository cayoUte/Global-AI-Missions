"""Application settings, read once from environment variables (and the repo-root .env).

Every variable is documented in .env.example (delivery-engineer) and SHARED_CONTEXT §10.
Nothing else in the codebase reads os.environ directly: import get_settings() instead.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Persistence. SQLAlchemy URL with the psycopg 3 driver:
    # postgresql+psycopg://user:password@host:5432/dbname
    database_url: str

    # Auth. HS256 needs a long random secret; the app refuses to boot with a short one.
    jwt_secret: SecretStr = Field(min_length=32)
    jwt_ttl_minutes: int = 60
    # Secure flag on the session cookie. False for local http; true on any https deploy.
    cookie_secure: bool = False

    # AI coach (see docs/contracts/api-contract.md, feedback_source).
    coach_provider: Literal["mock", "anthropic"] = "mock"
    anthropic_api_key: SecretStr | None = None
    anthropic_model: str | None = None

    # Production mode: FastAPI serves the built SPA (single origin, no CORS). Defaults to
    # frontend/dist when that folder exists; development uses the Vite dev server instead.
    spa_dist_dir: Path | None = None

    # Demo mode: exposes demo accounts on GET /api/config and enables /simulate (stretch).
    # Secure default is off; .env.example turns it on for local runs.
    demo_mode: bool = False


    def resolved_spa_dir(self) -> Path | None:
        candidate = self.spa_dist_dir or REPO_ROOT / "frontend" / "dist"
        return candidate if (candidate / "index.html").is_file() else None


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # values come from the environment
