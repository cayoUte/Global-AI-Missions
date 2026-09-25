"""Races and the seeded veteran on the REAL repositories and PostgreSQL (qa-engineer).

Row locks, the unique (attempt, question) answer and ON CONFLICT on coach_feedback only exist in
PostgreSQL, so the concurrency guarantees of api-contract §8 are checked here, not on the fakes.
Reuses the pg_client fixture (gam_test on 127.0.0.1:5433, migrated and seeded; skipped when
PostgreSQL is unreachable).
"""

import threading
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.models.attempts import AttemptAnswer
from app.models.coach import CoachFeedback, CoachMemory
from app.repositories import users as users_repo
from app.repositories.db import get_sessionmaker
from tests.api import helpers
from tests.api.test_postgres_flow import pg_client  # noqa: F401  (pytest fixture)
from tests.fakes import PASSWORD
from tests.leak import ANSWER_KEY_FIELDS, forbidden_keys


def _twin(client: TestClient) -> TestClient:
    """A second client on the same app with the same session cookie (a second tab)."""
    twin = TestClient(client.app)
    twin.cookies.set("gam_session", client.cookies.get("gam_session"))
    return twin


def _together(*calls):
    """Run the calls at the same moment (a barrier), return their responses in order."""
    barrier = threading.Barrier(len(calls))
    results: list = [None] * len(calls)

    def worker(i, call):
        barrier.wait()
        results[i] = call()

    threads = [threading.Thread(target=worker, args=(i, c)) for i, c in enumerate(calls)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    return results


def _count(model, **where) -> int:
    with get_sessionmaker()() as session:
        query = select(func.count()).select_from(model)
        for column, value in where.items():
            query = query.where(getattr(model, column) == value)
        return session.scalar(query)


def _sessions_count(email: str) -> int:
    with get_sessionmaker()() as session:
        user = users_repo.get_user_by_email(session, email)
        memory = session.get(CoachMemory, user.id)
        return memory.sessions_count if memory else 0


def test_two_concurrent_answers_lock_the_checkpoint_once(pg_client):  # noqa: F811
    state = pg_client.post("/api/missions/the-last-train/attempts").json()
    base = f"/api/attempts/{state['attempt_id']}"
    while state["node"]["kind"] != "checkpoint":
        state = pg_client.post(f"{base}/advance", json={"node_id": state["node"]["id"]}).json()
    attempt = uuid.UUID(state["attempt_id"])
    before = _count(AttemptAnswer, attempt_id=attempt)  # a resumed run may have answers already
    twin = _twin(pg_client)
    right, wrong = helpers.answer_body(state, True), helpers.answer_body(state, False)
    a, b = _together(
        lambda: pg_client.post(f"{base}/answer", json=right),
        lambda: twin.post(f"{base}/answer", json=wrong),
    )
    assert sorted([a.status_code, b.status_code]) == [200, 409], (a.text, b.text)
    loser = a if a.status_code == 409 else b
    assert loser.json()["error"]["code"] == "CHECKPOINT_LOCKED"
    assert _count(AttemptAnswer, attempt_id=attempt) == before + 1  # one answer, not two
    winner = a if a.status_code == 200 else b
    assert pg_client.get(base).json() == winner.json()["state"]  # the server state is the winner's
    # BUG-002 regression: the loser's 409 carries the state the winner committed, not the
    # checkpoint it read before the race (services.attempts.conflict re-reads the attempt).
    assert loser.json()["error"]["details"]["state"] == winner.json()["state"]


def test_two_concurrent_submits_make_one_report_and_one_memory_update(pg_client):  # noqa: F811
    ending = helpers.play(pg_client, wrong=frozenset({"q02", "q05"}))
    attempt_id = ending["attempt_id"]
    before = _sessions_count("new@globalai.test")
    twin = _twin(pg_client)
    url = f"/api/attempts/{attempt_id}/submit"
    a, b = _together(lambda: pg_client.post(url), lambda: twin.post(url))
    assert (a.status_code, b.status_code) == (200, 200), (a.text, b.text)
    assert a.json() == b.json()  # the same report: graded once
    assert a.json()["result"]["correct"] + a.json()["result"]["incorrect"] == 10
    assert _count(CoachFeedback, attempt_id=uuid.UUID(attempt_id)) == 1
    assert _sessions_count("new@globalai.test") == before + 1  # exactly once
    again = pg_client.post(url)  # and a later retry is still the same report
    assert again.status_code == 200 and again.json() == a.json()
    assert _sessions_count("new@globalai.test") == before + 1


def test_the_seeded_veteran_progress_over_http(pg_client):  # noqa: F811
    leo = TestClient(pg_client.app)
    r = leo.post("/api/auth/login", json={"email": "veteran@globalai.test", "password": PASSWORD})
    assert r.status_code == 200
    progress = leo.get("/api/me/progress").json()
    assert forbidden_keys(progress, ANSWER_KEY_FIELDS) == []
    history = progress["history"]
    assert len(history) == 4
    assert [h["attempt_number"] for h in history] == [4, 3, 2, 1]  # newest first
    assert all(h["correct"] + h["incorrect"] == 10 for h in history)
    assert progress["profile"]["based_on_attempts"] == 3
    assert [s["skill"] for s in progress["profile"]["skills"]] == [
        "grammar",
        "listening",
        "reading",
        "vocabulary",
    ]
    assert len(progress["level_history"]) == 4
    dates = [p["submitted_at"] for p in progress["level_history"]]
    assert dates == sorted(dates)  # oldest first, for the trend
    notes = progress["notes"]
    assert 1 <= len(notes) <= 5
    created = [n["created_at"] for n in notes]
    assert created == sorted(created, reverse=True)  # newest first
    world = leo.get("/api/world").json()
    assert world["greeting"]["source"] == "memory"
    assert sum(c["is_maya_pick"] for c in world["cards"]) == 1
