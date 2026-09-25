"""The walking skeleton end to end over HTTP: world -> start -> 10 checkpoints -> submit ->
report numbers -> progress row, with the forbidden-field scan over every in-progress response."""

from tests.api.helpers import assert_no_leaks, play
from tests.leak import ANSWER_KEY_FIELDS, forbidden_keys

WRONG = frozenset({"q07", "q08", "q09"})


def _card(world: dict, mission_id: str = "the-last-train") -> dict:
    return next(c for c in world["cards"] if c["mission_id"] == mission_id)


def test_full_run_leaks_nothing_and_the_report_has_the_numbers(ana, store):
    world = ana.get("/api/world").json()
    assert _card(world)["state"] == "available"
    assert world["greeting"]["source"] == "first_meeting"
    assert world["snapshot"] == {"missions_played": 0, "latest_label": None, "profile": None}
    assert [c["mission_id"] for c in world["cards"]][0] == "the-last-train"

    responses: list = []
    ending = play(ana, wrong=WRONG, responses=responses)
    assert len(responses) > 40
    assert_no_leaks(responses)
    assert ending["status"] == "completed" and ending["node"]["kind"] == "ending"
    assert ending["node"]["ending"]["key"] in {"made_it", "made_it_with_maya", "night_bus"}

    card = _card(ana.get("/api/world").json())
    assert card["state"] == "waiting_to_submit"
    assert card["open_attempt"]["ending"] == ending["node"]["ending"]
    again = ana.post("/api/missions/the-last-train/attempts")  # PD-028: the same finished run
    assert again.status_code == 200 and again.json()["attempt_id"] == ending["attempt_id"]
    early = ana.get(f"/api/attempts/{ending['attempt_id']}/report")
    assert early.status_code == 409 and early.json()["error"]["code"] == "MISSION_NOT_FINISHED"
    assert early.json()["error"]["details"]["state"]["status"] == "completed"

    r = ana.post(f"/api/attempts/{ending['attempt_id']}/submit")
    assert r.status_code == 200, r.text
    body = r.json()
    result = body["result"]
    assert (result["correct"], result["incorrect"], result["total"]) == (7, 3, 10)
    assert result["score_pct"] == 70
    assert [s["skill"] for s in result["skills"]] == [
        "grammar",
        "listening",
        "reading",
        "vocabulary",
    ]
    assert sum(s["total"] for s in result["skills"]) == 10
    assert result["unmeasured_skills"] == ["speaking"]
    level = result["suggested_level"]
    label = "Pre-A1" if level["cefr"] == "PRE_A1" else level["cefr"]
    assert body["label"] == f"{label} · The Last Train — 70%"
    assert level["base_cefr"] == "B1" and level["reason"].startswith("70% points to B1.")
    assert body["feedback_source"]["status"] == "fallback"
    assert body["interpretation"]["strength"] != body["interpretation"]["challenge"]
    assert {m["item_id"] for m in body["missed"]} == WRONG
    for m in body["missed"]:
        assert m["correct_answer"] and m["explanation"] and m["your_answer"]
    assert body["diary"][0]["seq"] == 1 and body["diary"][-1]["kind"] == "ending"
    checkpoints = [d for d in body["diary"] if d["checkpoint"]]
    assert len(checkpoints) == 10
    missed = {
        d["checkpoint"]["item_id"] for d in checkpoints if d["checkpoint"]["outcome"] == "missed"
    }
    assert missed == WRONG
    record = body["attempt_record"]
    assert record["attempt_number"] == 1 and record["ending"] == ending["node"]["ending"]
    assert record["story_minutes_used"] == 18 - ending["clock"]["minutes_left"]
    assert body["next_mission"]["state"] in {"locked", "in_preparation"}

    # Idempotent: same report, graded once, feedback stored once, memory grown once.
    assert ana.post(f"/api/attempts/{ending['attempt_id']}/submit").json() == body
    assert ana.get(f"/api/attempts/{ending['attempt_id']}/report").json() == body
    assert store.memory[store.ana.id].sessions_count == 1
    assert len(store.scores) == 4 and len(store.feedback) == 1

    progress = ana.get("/api/me/progress").json()
    assert forbidden_keys(progress, ANSWER_KEY_FIELDS) == []
    row = progress["history"][0]
    assert row["label"] == body["label"] and (row["correct"], row["incorrect"]) == (7, 3)
    assert row["ending"] == record["ending"] and row["skills"] == result["skills"]
    assert progress["level_history"][0]["suggested_cefr"] == level["cefr"]
    assert progress["profile"]["based_on_attempts"] == 1
    assert progress["notes"][0]["text"] and progress["open_attempt"] is None

    world = ana.get("/api/world").json()
    assert forbidden_keys(world, ANSWER_KEY_FIELDS) == []
    card = _card(world)
    assert card["state"] == "completed" and card["latest_result"]["label"] == body["label"]
    assert card["attempts_submitted"] == 1
    assert world["greeting"]["source"] == "memory"
    assert world["snapshot"]["missions_played"] == 1
    assert world["snapshot"]["latest_label"] == body["label"]
    picks = [c["mission_id"] for c in world["cards"] if c["is_maya_pick"]]
    assert picks == [body["next_mission"]["mission_id"]]
    assert _card(world, "night-radio")["state"] == "in_preparation"  # unlocked by the report


def test_an_open_run_shows_in_progress_on_the_world_and_progress(ana):
    start = ana.post("/api/missions/the-last-train/attempts")
    assert start.status_code == 201
    state = start.json()
    assert state["clock"]["label"] == "21:47 · 18 min to departure"
    card = _card(ana.get("/api/world").json())
    assert card["state"] == "in_progress"
    assert card["open_attempt"]["attempt_id"] == state["attempt_id"]
    assert card["open_attempt"]["location"] == state["node"]["scene"]["location"]
    progress = ana.get("/api/me/progress").json()
    assert progress["open_attempt"]["attempt_id"] == state["attempt_id"]
    assert progress["open_attempt"]["status"] == "in_progress"
    # Starting again resumes the same run.
    again = ana.post("/api/missions/the-last-train/attempts")
    assert again.status_code == 200 and again.json() == state


def test_play_again_creates_a_new_numbered_attempt(ana):
    first = play(ana)
    report = ana.post(f"/api/attempts/{first['attempt_id']}/submit").json()
    assert report["result"]["score_pct"] == 100 and report["missed"] == []
    second = play(ana, wrong=frozenset({"q01"}))
    assert second["attempt_id"] != first["attempt_id"]
    report = ana.post(f"/api/attempts/{second['attempt_id']}/submit").json()
    assert report["attempt_record"]["attempt_number"] == 2
    progress = ana.get("/api/me/progress").json()
    assert [h["attempt_number"] for h in progress["history"]] == [2, 1]
    assert progress["profile"]["based_on_attempts"] == 2


def test_a_coach_failure_after_grading_still_returns_the_report(ana, monkeypatch):
    from app.services import feedback

    def boom(*args, **kwargs):
        raise RuntimeError("provider down")

    monkeypatch.setattr(feedback.coach, "run_coach", boom)
    ending = play(ana)
    r = ana.post(f"/api/attempts/{ending['attempt_id']}/submit")
    assert r.status_code == 200
    assert r.json()["feedback_source"]["status"] == "fallback"
    assert r.json()["result"]["score_pct"] == 100


def test_the_real_mission_runs_end_to_end_without_leaks(ana, store, monkeypatch):
    """The Last Train's real content (published as a newer version) over HTTP, with a rescue-prone
    pattern of misses, scanned for forbidden fields at every step."""
    from tests.api import helpers
    from tests.fakes import load_docs

    items_doc, mission_doc = load_docs("the-last-train")
    store.add_version("the-last-train", items_doc, mission_doc)
    monkeypatch.setattr(helpers, "ITEMS", {i["id"]: i for i in items_doc["items"]})
    for wrong in (frozenset(), frozenset({"q02", "q04", "q06", "q07", "q08", "q09", "q10"})):
        responses: list = []
        ending = play(ana, wrong=wrong, responses=responses)
        assert_no_leaks(responses)
        report = ana.post(f"/api/attempts/{ending['attempt_id']}/submit").json()
        assert report["result"]["correct"] == 10 - len(wrong)
        assert len([d for d in report["diary"] if d["checkpoint"]]) == 10
        assert report["attempt_record"]["ending"] == ending["node"]["ending"]
