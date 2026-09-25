"""Database fixtures (data-engineer). Real PostgreSQL: gam_test from docker compose (port 5433).

The whole module is skipped when the database is unreachable, so `pytest` stays green without
Docker; the skip reason says so. Once per session: downgrade to base, upgrade to head (the real
migration) and run the seed, committed. Each test then runs in a transaction that is rolled back.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import get_settings
from app.services import content as content_service
from seed.run import SeedSummary, run_seed

BACKEND_DIR = Path(__file__).resolve().parents[2]


def alembic_config(url: str) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", url)
    return config


@pytest.fixture(scope="session")
def db_url() -> str:
    # 127.0.0.1, not localhost: on Windows + Docker Desktop, "localhost" may try IPv6 ::1 first
    # and stall (CR-00X). The test database is always local.
    url = get_settings().database_url.replace("@localhost:", "@127.0.0.1:")
    if not url.rsplit("/", 1)[-1].endswith("_test"):
        pytest.skip(f"refusing to run DB tests against a non-test database ({url})")
    return url


@pytest.fixture(scope="session")
def engine(db_url: str) -> Iterator[Engine]:
    eng = create_engine(db_url, connect_args={"connect_timeout": 3})
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError as exc:
        pytest.skip(f"PostgreSQL not reachable at {db_url} (docker compose up -d db): {exc}")
    config = alembic_config(db_url)
    command.downgrade(config, "base")  # a clean slate every session
    command.upgrade(config, "head")
    yield eng
    eng.dispose()


@pytest.fixture(scope="session")
def alembic_cfg(db_url: str) -> Config:
    return alembic_config(db_url)


@pytest.fixture(scope="session")
def seed_summary(engine: Engine) -> SeedSummary:
    content_service.clear_cache()
    with Session(engine) as session:
        summary = run_seed(session)
        session.commit()
    return summary


@pytest.fixture
def session(engine: Engine, seed_summary: SeedSummary) -> Iterator[Session]:
    """A session inside an outer transaction that is always rolled back."""
    with engine.connect() as connection:
        transaction = connection.begin()
        db = Session(bind=connection, join_transaction_mode="create_savepoint")
        try:
            yield db
        finally:
            db.close()
            transaction.rollback()
    content_service.clear_cache()
