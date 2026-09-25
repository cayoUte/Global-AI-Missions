"""GET /api/missions/{mission_id}/simulate (api-contract §5.16, stretch, DEMO_MODE only).

Security invariant 7 (SHARED_CONTEXT §9): the replay carries outcomes, nodes, the clock and
Maya's decisions, never options, chosen answers, prompts or answer content.
"""

import typing

import pytest

from app.core.config import get_settings
from app.engine import PROFILES
from app.schemas.simulation import SimulationProfile
from tests.api.conftest import make_client
from tests.fakes import load_docs
from tests.leak import OPEN_ATTEMPT_FORBIDDEN, forbidden_keys

URL = "/api/missions/the-last-train/simulate"
ALL_PROFILES = sorted(PROFILES)
REAL_ITEMS, REAL_MISSION = load_docs("the-last-train")

# §9.A minus `outcome` (the contract names it: understood | missed), plus every key that could
# carry item content or the student's choice.
SIMULATE_FORBIDDEN = (OPEN_ATTEMPT_FORBIDDEN - {"outcome"}) | {
    "options",
    "option_id",
    "chosen_option_id",
    "answer",
    "answers",
    "text",
    "item_id",
    "prompt",
    "stimulus",
    "audio_script",
    "lines",
    "scene",
    "maya_line",
}


@pytest.fixture
def real_store(store):
    """Publish the real mission as the active version (the default store holds the fixture)."""
    store.add_version("the-last-train", *load_docs("the-last-train"))
    return store


def get(client, url=URL, **params):
    return client.get(url, params=params)


def strings(payload) -> list[str]:
    if isinstance(payload, dict):
        return [s for value in payload.values() for s in strings(value)] + list(payload)
    if isinstance(payload, list):
        return [s for value in payload for s in strings(value)]
    return [payload] if isinstance(payload, str) else []


def secret_strings(items_doc: dict) -> tuple[set[str], set[str]]:
    """(exact, substring): short content strings must not appear as a value; long ones must not
    appear anywhere inside any string of the response."""
    values: set[str] = set()
    for item in items_doc["items"]:
        values |= {item["id"], item["prompt"], item["explanation"], item["hint"]}
        for option in item["options"] or ():
            values |= {option["id"], option["text"]}
        key = item["answer_key"]
        values |= set(key.get("accepted", ())) | {key.get("correct_option_id") or ""}
        stimulus = item.get("stimulus") or {}
        values |= {stimulus.get("text") or "", stimulus.get("audio_script") or ""}
    values.discard("")
    return {v for v in values if len(v) < 12}, {v for v in values if len(v) >= 12}


# --- access ---------------------------------------------------------------------------------


@pytest.mark.parametrize("who", ["ana", "teacher", "admin"])
def test_any_authenticated_role_gets_a_replay_in_demo_mode(request, real_store, who):
    r = get(request.getfixturevalue(who), profile="A2", seed=7)
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"mission_id", "profile", "seed", "steps", "ending", "story_minutes_used"}
    assert (body["mission_id"], body["profile"], body["seed"]) == ("the-last-train", "A2", 7)
    assert set(body["steps"][0]) == {
        "seq",
        "node_id",
        "kind",
        "clock",
        "outcome",
        "maya_decision",
        "maya_mood",
    }


def test_demo_mode_off_is_a_404_like_an_unknown_route_for_everyone(app, monkeypatch):
    monkeypatch.setattr(get_settings(), "demo_mode", False)
    anonymous, student = make_client(app), make_client(app, "new@globalai.test")
    unknown = anonymous.get("/api/no-such-route")
    for client in (anonymous, student):
        r = get(client, profile="A2")
        assert r.status_code == 404
        assert r.json()["error"]["code"] == unknown.json()["error"]["code"] == "NOT_FOUND"
        assert r.json()["error"]["details"] is None
    # Before any validation too: a bad profile does not reveal that the route exists.
    assert get(student, profile="Z9").status_code == 404


def test_unauthenticated_is_401(client):
    r = get(client, profile="A2")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.parametrize(
    "params",
    [
        {"profile": "C1"},
        {"profile": "a2"},
        {},  # profile is required
        {"profile": "A2", "seed": -1},
        {"profile": "A2", "seed": 1_000_001},
        {"profile": "A2", "seed": "seven"},
        {"profile": "A2", "seed": "1.5"},
    ],
)
def test_bad_profile_or_seed_is_422_validation_error(ana, params):
    r = get(ana, **params)
    assert r.status_code == 422, r.text
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"
    assert r.json()["error"]["details"]["errors"]


@pytest.mark.parametrize("mission_id", ["no-such-mission", "night-radio"])  # unknown, not playable
def test_unknown_or_non_playable_mission_is_404(ana, mission_id):
    r = get(ana, f"/api/missions/{mission_id}/simulate", profile="A2")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


def test_the_profile_enum_matches_the_engine_profiles():
    assert set(typing.get_args(SimulationProfile)) == set(PROFILES)


# --- behaviour ------------------------------------------------------------------------------


def test_same_profile_and_seed_is_identical_and_seeds_vary(ana, real_store):
    first = get(ana, profile="A2", seed=7).json()
    assert get(ana, profile="A2", seed=7).json() == first
    runs = {str(get(ana, profile="A2", seed=seed).json()["steps"]) for seed in range(1, 21)}
    assert len(runs) > 1


def test_seed_defaults_to_1(ana, real_store):
    default = get(ana, profile="B1").json()
    assert default["seed"] == 1
    assert default == get(ana, profile="B1", seed=1).json()


@pytest.mark.parametrize("profile", ALL_PROFILES)
def test_the_path_visits_10_checkpoints_and_ends_at_an_ending(ana, real_store, profile):
    body = get(ana, profile=profile, seed=3).json()
    steps = body["steps"]
    assert [s["seq"] for s in steps] == list(range(1, len(steps) + 1))
    checkpoints = [s for s in steps if s["kind"] == "checkpoint"]
    assert len(checkpoints) == 10
    assert all(s["outcome"] in ("understood", "missed") for s in checkpoints)
    assert all(s["outcome"] is None for s in steps if s["kind"] != "checkpoint")
    assert steps[-1]["kind"] == "ending"
    assert [s["kind"] for s in steps].count("ending") == 1
    ending_nodes = {n["id"]: n["ending"] for n in REAL_MISSION["nodes"] if n["kind"] == "ending"}
    ending = ending_nodes[steps[-1]["node_id"]]
    assert body["ending"] == {"key": ending["key"], "title": ending["title"]}
    minutes = REAL_MISSION["setting"]["minutes_available"]
    assert steps[0]["clock"]["minutes_left"] == minutes
    assert body["story_minutes_used"] == minutes - steps[-1]["clock"]["minutes_left"]


def test_nothing_is_persisted_and_the_coach_is_not_called(ana, real_store):
    before = (len(real_store.attempts), len(real_store.steps), len(real_store.answers))
    coach_calls, feedback = real_store.coach_calls, len(real_store.feedback)
    for profile in ALL_PROFILES:
        assert get(ana, profile=profile, seed=5).status_code == 200
    assert (len(real_store.attempts), len(real_store.steps), len(real_store.answers)) == before
    assert (real_store.coach_calls, len(real_store.feedback)) == (coach_calls, feedback)
    world = ana.get("/api/world").json()
    assert world["cards"][0]["open_attempt"] is None


# --- invariant 7: no option, choice or answer content ----------------------------------------


def test_no_forbidden_key_or_item_content_in_any_replay(ana, real_store):
    exact, substrings = secret_strings(REAL_ITEMS)
    for profile in ALL_PROFILES:
        for seed in (1, 7, 42):
            body = get(ana, profile=profile, seed=seed).json()
            assert forbidden_keys(body, SIMULATE_FORBIDDEN) == []
            found = strings(body)
            assert [s for s in found if s in exact] == []
            assert [(s, secret) for s in found for secret in substrings if secret in s] == []


def test_no_item_content_with_the_fixture_mission_either(ana):
    exact, substrings = secret_strings(load_docs()[0])
    body = get(ana, profile="A2_weak_listening", seed=9).json()
    assert forbidden_keys(body, SIMULATE_FORBIDDEN) == []
    found = strings(body)
    assert [s for s in found if s in exact] == []
    assert [(s, secret) for s in found for secret in substrings if secret in s] == []
