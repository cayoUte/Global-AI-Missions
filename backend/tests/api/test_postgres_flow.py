"""The same HTTP flow against the REAL repositories and PostgreSQL (no fakes).

Uses the gam_test database from docker compose (DATABASE_URL, port 5433): migrates it to head
and runs the idempotent seed first. Skipped, with the reason printed, when it is unreachable.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.core.config import get_settings
from app.core.rate_limit import login_limiter
from app.repositories import missions as missions_repo
from app.repositories.db import get_sessionmaker
from app.services import content
from tests.api import helpers
from tests.fakes import PASSWORD
from tests.leak import ANSWER_KEY_FIELDS, forbidden_keys


@pytest.fixture
def pg_client(monkeypatch):
    """Point the app at the test database (127.0.0.1: on Windows "localhost" may stall on IPv6),
    migrate to head and run the idempotent seed, or skip when PostgreSQL is unreachable."""
    from alembic import command
    from app.main import create_app
    from app.repositories import db
    from seed.run import run_seed
    from tests.data.conftest import alembic_config

    settings = get_settings()
    url = settings.database_url.replace("@localhost:", "@127.0.0.1:")
    if not url.rsplit("/", 1)[-1].endswith("_test"):
        pytest.skip(f"refusing to run against a non-test database ({url})")
    probe = create_engine(url, connect_args={"connect_timeout": 3})
    try:
        with probe.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError as exc:
        pytest.skip(f"PostgreSQL not reachable at {url}: {type(exc).__name__}")
    finally:
        probe.dispose()
    monkeypatch.setattr(settings, "database_url", url)
    db.get_engine.cache_clear()
    db.get_sessionmaker.cache_clear()
    command.upgrade(alembic_config(url), "head")
    with get_sessionmaker()() as session:
        run_seed(session)
        session.commit()
    content.clear_cache()
    login_limiter.reset()
    with get_sessionmaker()() as session:
        version = missions_repo.get_active_mission_version(session, "the-last-train")
        docs = missions_repo.load_mission_content(session, version.id)
    monkeypatch.setattr(helpers, "ITEMS", {i["id"]: i for i in docs.items_doc["items"]})
    client = TestClient(create_app())
    r = client.post("/api/auth/login", json={"email": "new@globalai.test", "password": PASSWORD})
    assert r.status_code == 200
    yield client
    db.get_engine().dispose()
    db.get_engine.cache_clear()
    db.get_sessionmaker.cache_clear()


def test_walking_skeleton_on_postgres(pg_client):
    responses: list = []
    ending = helpers.play(pg_client, wrong=frozenset({"q07"}), responses=responses)
    helpers.assert_no_leaks(responses)
    first = pg_client.post(f"/api/attempts/{ending['attempt_id']}/submit")
    assert first.status_code == 200, first.text
    again = pg_client.post(f"/api/attempts/{ending['attempt_id']}/submit")
    assert again.json() == first.json()
    assert first.json()["result"]["correct"] == 9
    progress = pg_client.get("/api/me/progress").json()
    assert progress["history"][0]["attempt_id"] == ending["attempt_id"]
    assert forbidden_keys(progress, ANSWER_KEY_FIELDS) == []
    assert pg_client.get("/api/world").status_code == 200
