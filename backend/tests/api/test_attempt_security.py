"""Security invariants of SHARED_CONTEXT §9 and the answer processing order (api-contract §5.10)."""

import uuid

import pytest

from tests.api.conftest import make_client
from tests.api.helpers import ITEMS, answer_body, play


def _to_checkpoint(client, item_type=None) -> dict:
    """Start and CONTINUE until the first checkpoint (of `item_type`, answering others right)."""
    state = client.post("/api/missions/the-last-train/attempts").json()
    while True:
        node = state["node"]
        if node["kind"] == "checkpoint":
            if item_type is None or ITEMS[node["checkpoint"]["item_id"]]["type"] == item_type:
                return state
            url = f"/api/attempts/{state['attempt_id']}/answer"
            state = client.post(url, json=answer_body(state, True)).json()["state"]
        else:
            url = f"/api/attempts/{state['attempt_id']}/advance"
            state = client.post(url, json={"node_id": node["id"]}).json()


def _answer(client, state, body):
    return client.post(f"/api/attempts/{state['attempt_id']}/answer", json=body)


@pytest.mark.parametrize(
    "body",
    [
        {"option_id": "b"},  # missing node_id
        {"node_id": "X", "option_id": "b", "text": "have"},  # both
        {"node_id": "X"},  # neither
        {"node_id": "X", "option_id": "b", "is_correct": True},  # extra field
        {"node_id": "X", "option_id": "B!"},  # option id shape
        {"node_id": "X", "text": "x" * 201},  # raw text too long
    ],
)
def test_answer_shape_errors_are_422_and_do_not_lock(ana, body):
    state = _to_checkpoint(ana)
    body = {k: (state["node"]["id"] if v == "X" else v) for k, v in body.items()}
    r = _answer(ana, state, body)
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"
    assert _answer(ana, state, answer_body(state, True)).status_code == 200  # still answerable


def test_item_rules_are_422_and_the_checkpoint_stays_answerable(ana):
    state = _to_checkpoint(ana, "multiple_choice")
    node = state["node"]["id"]
    for body in ({"node_id": node, "option_id": "zz"}, {"node_id": node, "text": "have"}):
        r = _answer(ana, state, body)
        assert r.status_code == 422, r.text
        assert r.json()["error"]["details"]["errors"][0]["field"] in {"option_id", "text"}
    assert _answer(ana, state, answer_body(state, False)).status_code == 200


def test_fill_blank_needs_1_to_80_characters_after_normalization(ana):
    state = _to_checkpoint(ana, "fill_blank")
    node = state["node"]["id"]
    for bad in ("...", "   ", "a" * 81, {"option_id": "a"}):
        body = {"node_id": node, **(bad if isinstance(bad, dict) else {"text": bad})}
        assert _answer(ana, state, body).status_code == 422
    ok = _answer(ana, state, {"node_id": node, "text": "  " + "a" * 80 + " !!"})
    assert ok.status_code == 200


def test_a_second_answer_is_409_checkpoint_locked_with_the_current_state(ana):
    state = _to_checkpoint(ana)
    first = _answer(ana, state, answer_body(state, False))
    assert first.status_code == 200 and set(first.json()) == {"maya_line", "state"}
    retry = _answer(ana, state, answer_body(state, True))
    assert retry.status_code == 409
    assert retry.json()["error"]["code"] == "CHECKPOINT_LOCKED"
    assert retry.json()["error"]["details"]["state"] == first.json()["state"]


def test_advance_is_optimistic_and_only_for_continue_nodes(ana):
    start = ana.post("/api/missions/the-last-train/attempts").json()
    url = f"/api/attempts/{start['attempt_id']}/advance"
    stale = ana.post(url, json={"node_id": "c05"})
    assert stale.status_code == 409 and stale.json()["error"]["code"] == "NODE_OUT_OF_SEQUENCE"
    assert stale.json()["error"]["details"]["state"] == start
    moved = ana.post(url, json={"node_id": start["node"]["id"]})
    assert moved.status_code == 200
    retried = ana.post(url, json={"node_id": start["node"]["id"]})  # a retried Continue
    assert retried.status_code == 409
    assert retried.json()["error"]["details"]["state"] == moved.json()
    if moved.json()["node"]["kind"] == "checkpoint":
        on_checkpoint = ana.post(url, json={"node_id": moved.json()["node"]["id"]})
        assert on_checkpoint.json()["error"]["code"] == "NODE_OUT_OF_SEQUENCE"
    assert ana.post(url, json={"node_id": "x", "minutes": 5}).status_code == 422


def test_answer_on_a_non_checkpoint_or_a_future_checkpoint_is_409(ana):
    start = ana.post("/api/missions/the-last-train/attempts").json()
    r = _answer(ana, start, {"node_id": start["node"]["id"], "option_id": "a"})
    assert r.status_code == 409 and r.json()["error"]["code"] == "NODE_OUT_OF_SEQUENCE"
    r = _answer(ana, start, {"node_id": "c10", "option_id": "a"})  # skipping ahead
    assert r.status_code == 409 and r.json()["error"]["code"] == "NODE_OUT_OF_SEQUENCE"


def test_a_closed_attempt_rejects_advance_and_answer(ana):
    ending = play(ana)
    url = f"/api/attempts/{ending['attempt_id']}"
    r = ana.post(f"{url}/advance", json={"node_id": ending["node"]["id"]})
    assert r.status_code == 409 and r.json()["error"]["code"] == "ATTEMPT_NOT_IN_PROGRESS"
    r = ana.post(f"{url}/answer", json={"node_id": ending["node"]["id"], "option_id": "a"})
    assert r.json()["error"]["code"] == "ATTEMPT_NOT_IN_PROGRESS"


def test_submit_before_the_ending_is_409_mission_not_finished(ana):
    start = ana.post("/api/missions/the-last-train/attempts").json()
    r = ana.post(f"/api/attempts/{start['attempt_id']}/submit")
    assert r.status_code == 409 and r.json()["error"]["code"] == "MISSION_NOT_FINISHED"
    assert r.json()["error"]["details"]["state"] == start


def test_another_students_attempt_is_404_everywhere(ana, app):
    state = ana.post("/api/missions/the-last-train/attempts").json()
    leo = make_client(app, "veteran@globalai.test")
    base = f"/api/attempts/{state['attempt_id']}"
    calls = [
        leo.get(base),
        leo.get(f"{base}/report"),
        leo.post(f"{base}/submit"),
        leo.post(f"{base}/advance", json={"node_id": state["node"]["id"]}),
        leo.post(f"{base}/answer", json={"node_id": state["node"]["id"], "option_id": "a"}),
    ]
    assert [c.status_code for c in calls] == [404] * 5
    assert {c.json()["error"]["code"] for c in calls} == {"NOT_FOUND"}


def test_malformed_and_unknown_ids_are_404_not_422(ana):
    assert ana.get("/api/attempts/not-a-uuid").status_code == 404
    assert ana.get(f"/api/attempts/{uuid.uuid4()}").status_code == 404
    assert ana.post("/api/attempts/123/submit").status_code == 404


def test_locked_non_playable_and_unknown_missions_cannot_be_started(ana):
    for mission_id in ("night-radio", "the-interview", "nope"):
        r = ana.post(f"/api/missions/{mission_id}/attempts")
        assert r.status_code == 404 and r.json()["error"]["code"] == "NOT_FOUND"


def test_student_endpoints_need_a_session_and_the_student_role(client, teacher):
    for path in ("/api/world", "/api/me/progress"):
        assert client.get(path).status_code == 401
        r = teacher.get(path)
        assert r.status_code == 403 and r.json()["error"]["code"] == "FORBIDDEN_ROLE"
    assert client.post("/api/missions/the-last-train/attempts").status_code == 401
    assert teacher.post("/api/missions/the-last-train/attempts").status_code == 403


def test_teacher_rbac(ana, teacher, admin, store):
    assert ana.get("/api/teacher/classes").status_code == 403
    mine = teacher.get("/api/teacher/classes").json()["classes"]
    assert [c["name"] for c in mine] == ["Evening B1"] and mine[0]["student_count"] == 2
    own = teacher.get(f"/api/teacher/classes/{store.klass.id}/progress")
    assert own.status_code == 200
    assert [s["display_name"] for s in own.json()["students"]] == ["Ana", "Leo"]
    assert set(own.json()["students"][0]) == {  # aggregates only: no user ids, no drill-in
        "display_name",
        "missions_played",
        "latest_label",
        "profile",
        "last_activity_at",
    }
    other = teacher.get(f"/api/teacher/classes/{store.other_class.id}/progress")
    assert other.status_code == 404
    assert teacher.get("/api/teacher/classes/not-a-uuid/progress").status_code == 404
    assert len(admin.get("/api/teacher/classes").json()["classes"]) == 2
    assert admin.get(f"/api/teacher/classes/{store.other_class.id}/progress").status_code == 200
    assert ana.get(f"/api/teacher/classes/{store.klass.id}/progress").status_code == 403


def test_the_client_can_never_send_a_score(ana):
    ending = play(ana, wrong=frozenset({"q01"}))
    r = ana.post(f"/api/attempts/{ending['attempt_id']}/submit", json={"score_pct": 100})
    assert r.status_code == 200  # submit takes no body: anything sent is never read
    assert r.json()["result"]["score_pct"] == 90  # the server's grading, not the client's


def test_unknown_api_route_uses_the_envelope(client):
    r = client.get("/api/nope")
    assert r.status_code == 404 and set(r.json()["error"]) == {"code", "message", "details"}
