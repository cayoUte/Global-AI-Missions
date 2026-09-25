"""QA gap tests (qa-engineer): what the owners' suites did not pin down yet.

- every protected endpoint answers 401 UNAUTHENTICATED without a cookie (not just a status);
- the 409 bodies (details.state) of an open attempt carry no forbidden field either;
- a new client session (same cookie, or a fresh check-in) resumes the same node and state;
- a broken AI provider (timeout, invalid key, malformed JSON, unknown mission) never breaks
  submit and never changes score, level or record (SHARED_CONTEXT §6, §9.6; R-32, R-34).
"""

import uuid

import anthropic
import httpx
import pytest
from fastapi.testclient import TestClient

from app.ai.anthropic_provider import AnthropicCoachProvider
from app.ai.factory import SubmitSeamAdapter
from app.ai.mock_provider import MockCoachProvider
from tests.ai.helpers import as_json, fake_client
from tests.api.conftest import make_client
from tests.api.helpers import answer_body, assert_no_leaks, play
from tests.fakes import PASSWORD

WRONG = frozenset({"q07", "q08", "q09"})  # 70% → base B1, capped to A2 (ASSESSMENT_SPEC ex. 3)


def test_every_protected_endpoint_is_401_unauthenticated_without_a_cookie(client):
    some = uuid.uuid4()
    calls = [
        ("get", "/api/world"),
        ("get", "/api/me/progress"),
        ("post", "/api/missions/the-last-train/attempts"),
        ("get", f"/api/attempts/{some}"),
        ("post", f"/api/attempts/{some}/advance"),
        ("post", f"/api/attempts/{some}/answer"),
        ("post", f"/api/attempts/{some}/submit"),
        ("get", f"/api/attempts/{some}/report"),
        ("get", "/api/teacher/classes"),
        ("get", f"/api/teacher/classes/{some}/progress"),
    ]
    for method, path in calls:
        r = getattr(client, method)(path)
        assert r.status_code == 401, (path, r.status_code)
        assert r.json() == {
            "error": {
                "code": "UNAUTHENTICATED",
                "message": r.json()["error"]["message"],
                "details": None,
            }
        }, path


def test_conflict_bodies_of_an_open_attempt_leak_nothing(ana):
    """Every 409 carries details.state (a StateView): scan those too, not only the 200s."""
    start = ana.post("/api/missions/the-last-train/attempts").json()
    base = f"/api/attempts/{start['attempt_id']}"
    conflicts = [
        ana.post(f"{base}/submit"),  # MISSION_NOT_FINISHED
        ana.get(f"{base}/report"),  # MISSION_NOT_FINISHED
        ana.post(f"{base}/advance", json={"node_id": "c05"}),  # NODE_OUT_OF_SEQUENCE
        ana.post(f"{base}/answer", json={"node_id": "c10", "option_id": "a"}),  # out of sequence
    ]
    state = start
    while state["node"]["kind"] != "checkpoint":
        state = ana.post(f"{base}/advance", json={"node_id": state["node"]["id"]}).json()
    ana.post(f"{base}/answer", json=answer_body(state, False))
    conflicts.append(ana.post(f"{base}/answer", json=answer_body(state, True)))  # LOCKED
    assert [c.status_code for c in conflicts] == [409] * 5
    assert {c.json()["error"]["code"] for c in conflicts} == {
        "MISSION_NOT_FINISHED",
        "NODE_OUT_OF_SEQUENCE",
        "CHECKPOINT_LOCKED",
    }
    assert_no_leaks([c.json() for c in conflicts])


def test_a_new_client_session_resumes_the_same_node_and_state(app, ana):
    """Lost connection / new tab / new device: the server holds the run (R-60)."""
    state = ana.post("/api/missions/the-last-train/attempts").json()
    base = f"/api/attempts/{state['attempt_id']}"
    for _ in range(4):  # a few steps in, including a checkpoint answer
        if state["node"]["kind"] == "checkpoint":
            state = ana.post(f"{base}/answer", json=answer_body(state, False)).json()["state"]
        else:
            state = ana.post(f"{base}/advance", json={"node_id": state["node"]["id"]}).json()

    same_cookie = TestClient(app)
    same_cookie.cookies.set("gam_session", ana.cookies.get("gam_session"))
    assert same_cookie.get(base).json() == state
    other_device = make_client(app, "new@globalai.test")  # a fresh check-in, a new cookie
    assert other_device.get(base).json() == state
    again = other_device.post("/api/missions/the-last-train/attempts")
    assert again.status_code == 200 and again.json() == state  # start returns the open run


def _claude(**kwargs) -> SubmitSeamAdapter:
    return SubmitSeamAdapter(AnthropicCoachProvider("sk-test-not-a-key", "claude-test", **kwargs))


_REQUEST = httpx.Request("POST", "https://api.anthropic.com/v1/messages")


def _unknown_mission(baseline: dict) -> SubmitSeamAdapter:
    """Everything valid except next_mission_id, which is not a catalog candidate."""
    output = {
        "summary": "You can read signs.",
        "strength": baseline["interpretation"]["strength"],
        "challenge": baseline["interpretation"]["challenge"],
        "recommendation": "Read menus.",
        "next_mission_id": "the-moon-landing",
        "memory_note": "x",
        "next_greeting": "Hi.",
    }
    return _claude(client=fake_client(as_json(output)))


BROKEN_PROVIDERS = {
    "timeout": lambda _: _claude(client=fake_client(error=anthropic.APITimeoutError(_REQUEST))),
    "invalid_key": lambda _: _claude(
        client=fake_client(
            error=anthropic.AuthenticationError(
                "invalid x-api-key", response=httpx.Response(401, request=_REQUEST), body=None
            )
        )
    ),
    "malformed_json": lambda _: _claude(client=fake_client('{"summary": "half an object"')),
    "unknown_mission": _unknown_mission,
}


def _submit_with(client, monkeypatch, provider) -> dict:
    monkeypatch.setattr("app.ai.get_coach_provider", lambda: provider)
    ending = play(client, wrong=WRONG)
    r = client.post(f"/api/attempts/{ending['attempt_id']}/submit")
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.parametrize("failure", sorted(BROKEN_PROVIDERS))
def test_a_broken_ai_provider_never_breaks_submit_or_changes_the_grade(
    app, store, monkeypatch, failure
):
    baseline = _submit_with(
        make_client(app, "veteran@globalai.test"),
        monkeypatch,
        SubmitSeamAdapter(MockCoachProvider()),
    )
    ana = TestClient(app)
    ana.post("/api/auth/login", json={"email": "new@globalai.test", "password": PASSWORD})
    report = _submit_with(ana, monkeypatch, BROKEN_PROVIDERS[failure](baseline))

    assert report["feedback_source"]["status"] == "fallback"
    assert report["result"] == baseline["result"]  # score, per-skill, counts, level + reason
    assert report["result"]["score_pct"] == 70
    assert report["result"]["suggested_level"]["cefr"] == "A2"
    assert report["interpretation"]["strength"] == baseline["interpretation"]["strength"]
    assert report["interpretation"]["challenge"] == baseline["interpretation"]["challenge"]
    assert report["next_mission"]["mission_id"] in {
        "the-interview",
        "dinner-for-two",
        "campus-day",
        "night-radio",
    }
    # Memory still grows exactly once, and the report reads back the same.
    assert store.memory[store.ana.id].sessions_count == 1
    assert ana.get(f"/api/attempts/{report['attempt_id']}/report").json() == report


def test_a_valid_ai_provider_is_ready_and_still_cannot_change_the_grade(app, monkeypatch):
    baseline = _submit_with(
        make_client(app, "veteran@globalai.test"),
        monkeypatch,
        SubmitSeamAdapter(MockCoachProvider()),
    )
    good = {
        "summary": "You can read signs and short messages well.",
        "strength": baseline["interpretation"]["strength"],  # must echo the deterministic values
        "challenge": baseline["interpretation"]["challenge"],
        "recommendation": "Listen for numbers first.",
        "next_mission_id": baseline["next_mission"]["mission_id"],
        "memory_note": "Strong with signs.",
        "next_greeting": "Welcome back, Ana.",
    }
    report = _submit_with(
        make_client(app, "new@globalai.test"),
        monkeypatch,
        _claude(client=fake_client(as_json(good))),
    )
    assert report["feedback_source"] == {"status": "ready", "provider_label": "Claude"}
    assert report["interpretation"]["summary"] == good["summary"]
    assert report["result"] == baseline["result"]
