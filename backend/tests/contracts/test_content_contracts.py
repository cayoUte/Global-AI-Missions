"""The frozen content contracts (docs/contracts/*.schema.json) accept what we mean and reject
what we don't. Owner: tech-lead. The engine validator covers the graph and content integrity."""

import copy
import importlib.util
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[3]
_spec = importlib.util.spec_from_file_location(
    "validate_content", REPO_ROOT / "backend" / "scripts" / "validate_content.py"
)
assert _spec and _spec.loader
validate_content = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validate_content)

VALIDATORS = validate_content.load_validators()

ITEMS = {
    "mission_id": "the-last-train",
    "items": [
        {
            "id": "q02",
            "type": "multiple_choice",
            "skill": "listening",
            "cefr": "A1",
            "prompt": "Which platform does the announcer say?",
            "stimulus": {
                "kind": "audio",
                "speaker": "Station announcer",
                "audio_script": "The last train to Brighton leaves from platform six.",
                "rate": 0.85,
                "text": None,
            },
            "options": [
                {"id": "a", "text": "Platform two"},
                {"id": "b", "text": "Platform six"},
                {"id": "c", "text": "Platform sixteen"},
            ],
            "answer_key": {"correct_option_id": "b"},
            "explanation": "The announcer says 'six'.",
            "hint": "Listen for the number, not the name.",
        },
        {
            "id": "q05",
            "type": "fill_blank",
            "skill": "grammar",
            "cefr": "A2",
            "prompt": "Could I ___ a single ticket, please?",
            "stimulus": {"kind": "dialogue", "speaker": "You", "text": "At the ticket office."},
            "options": None,
            "answer_key": {"accepted": ["have", "get", "buy"]},
            "explanation": "After 'could I' we use the base form of the verb.",
            "hint": "Think of a polite request.",
        },
        {
            "id": "q07",
            "type": "comprehension",
            "skill": "reading",
            "cefr": "B1",
            "prompt": "What does the notice tell you?",
            "stimulus": {
                "kind": "notice",
                "speaker": "Station notice",
                "text": "Line one.\nLine two.",
            },
            "options": [
                {"id": "a", "text": "A"},
                {"id": "b", "text": "B"},
                {"id": "c", "text": "C"},
                {"id": "d", "text": "D"},
            ],
            "answer_key": {"correct_option_id": "d"},
            "explanation": "Because.",
            "hint": "Read the last line.",
        },
    ],
}


def _scene(lines: int = 1) -> dict:
    return {
        "location": "Station concourse",
        "backdrop": "concourse_night",
        "lines": [{"speaker": "narrator", "text": "Text."}] * lines,
    }


MISSION = {
    "mission_id": "the-last-train",
    "version": 1,
    "title": "The Last Train",
    "setting": {"city": "London", "start_clock": "21:47", "minutes_available": 18},
    "companion": {
        "id": "maya",
        "name": "Maya",
        "mood_lines": {m: ["Line."] for m in ("curious", "encouraging", "worried", "proud")},
    },
    "flags": [{"id": "lost_ticket", "description": "The student dropped the ticket."}],
    "start_node": "intro",
    "nodes": [
        {"id": "intro", "kind": "narrative", "scene": _scene(), "diary": "We arrived."},
        {
            "id": "c02",
            "kind": "checkpoint",
            "item_id": "q02",
            "scene": _scene(0),
            "maya": {"intro": "Listen.", "reaction_ok": "Yes.", "reaction_fail": "Hmm."},
        },
        {
            "id": "c02_fail",
            "kind": "consequence",
            "scene": {
                **_scene(),
                "variants": [
                    {
                        "when_flag": "train_departed",
                        "lines": [{"speaker": "maya", "text": "Plan B."}],
                        "backdrop": "night_bus_stop",
                        "maya_line": "The bus it is.",
                    }
                ],
            },
        },
        {"id": "c02_ok", "kind": "consequence", "scene": _scene(), "maya": {"line": "Nice."}},
        {
            "id": "end_made_it",
            "kind": "ending",
            "scene": _scene(),
            "maya": {"line": "We made it."},
            "ending": {
                "key": "made_it",
                "title": "Made It",
                "priority": 1,
                "condition": {"min_minutes_left": 0, "rescued": False},
            },
        },
    ],
    "edges": [
        {"from": "intro", "to": "c02", "on": "always", "minutes": 0},
        {"from": "c02", "to": "c02_ok", "on": "correct", "minutes": 1},
        {
            "from": "c02",
            "to": "c02_fail",
            "on": "incorrect",
            "minutes": 3,
            "effects": {"set_flags": ["lost_ticket"]},
        },
        {"from": "c02", "to": "c02_fail", "on": "incorrect", "minutes": 1, "rescue": True},
        {"from": "c02_ok", "to": "end_made_it", "on": "ending", "minutes": 0},
        {"from": "c02_fail", "to": "end_made_it", "on": "ending", "minutes": 0},
    ],
}


def _errors(name: str, doc: dict) -> list[str]:
    return validate_content.schema_errors(VALIDATORS[name], doc)


def test_schemas_are_valid_draft_2020_12():
    for filename in validate_content.SCHEMAS.values():
        Draft202012Validator.check_schema(
            validate_content.load_json(REPO_ROOT / "docs/contracts" / filename)
        )


def test_repository_content_is_valid():
    assert validate_content.validate(REPO_ROOT / "content") == 0


def test_example_items_and_mission_are_valid():
    assert _errors("items", ITEMS) == []
    assert _errors("mission", MISSION) == []


def _mutated(doc: dict, mutate) -> dict:
    clone = copy.deepcopy(doc)
    mutate(clone)
    return clone


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(
            lambda d: d["items"][1].update(options=[{"id": "a", "text": "x"}] * 3),
            id="fill_blank_with_options",
        ),
        pytest.param(
            lambda d: d["items"][1].update(answer_key={"correct_option_id": "a"}),
            id="fill_blank_with_choice_key",
        ),
        pytest.param(
            lambda d: d["items"][1].update(prompt="No gap here."), id="fill_blank_without_gap"
        ),
        pytest.param(
            lambda d: d["items"][0].update(options=d["items"][0]["options"][:2]), id="two_options"
        ),
        pytest.param(lambda d: d["items"][0].update(options=None), id="choice_without_options"),
        pytest.param(lambda d: d["items"][0]["stimulus"].pop("rate"), id="audio_without_rate"),
        pytest.param(
            lambda d: d["items"][0]["stimulus"].update(rate=1.4), id="audio_rate_out_of_range"
        ),
        pytest.param(lambda d: d["items"][0].update(skill="pronunciation"), id="unknown_skill"),
        pytest.param(lambda d: d["items"][0].update(cefr="C2"), id="unknown_cefr"),
        pytest.param(lambda d: d["items"][0].update(is_correct=True), id="extra_field"),
        pytest.param(lambda d: d["items"][0].pop("hint"), id="missing_hint"),
    ],
)
def test_invalid_items_are_rejected(mutate):
    assert _errors("items", _mutated(ITEMS, mutate)) != []


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(lambda d: d["nodes"][1].pop("item_id"), id="checkpoint_without_item"),
        pytest.param(lambda d: d["nodes"][1]["maya"].pop("intro"), id="checkpoint_without_intro"),
        pytest.param(lambda d: d["nodes"][0].update(item_id="q01"), id="item_on_narrative"),
        pytest.param(lambda d: d["nodes"][4].pop("ending"), id="ending_without_ending"),
        pytest.param(lambda d: d["nodes"][4].pop("maya"), id="ending_without_closing_line"),
        pytest.param(lambda d: d["nodes"][0].update(kind="cutscene"), id="unknown_kind"),
        pytest.param(lambda d: d["edges"][1].update(rescue=True), id="rescue_on_correct_edge"),
        pytest.param(lambda d: d["edges"][0].update(on="maybe"), id="unknown_edge_event"),
        pytest.param(
            lambda d: d["flags"].append({"id": "train_departed", "description": "x"}),
            id="declares_automatic_flag",
        ),
        pytest.param(lambda d: d["setting"].update(start_clock="9:47"), id="bad_clock"),
    ],
)
def test_invalid_missions_are_rejected(mutate):
    assert _errors("mission", _mutated(MISSION, mutate)) != []


@pytest.mark.parametrize(
    "rule",
    [
        {"kind": "always", "mission_id": "the-last-train", "hint": "x"},
        {"kind": "mission_submitted", "hint": "x"},
        {"kind": "level_reached", "min_level": "A2", "mission_id": "x", "hint": "x"},
        {"kind": "level_reached", "min_level": "A3", "hint": "x"},
        {"kind": "always"},
    ],
)
def test_invalid_unlock_rules_are_rejected(rule):
    catalog = validate_content.load_json(REPO_ROOT / "content" / "catalog.json")
    catalog["missions"][0]["unlock_rule"] = rule
    assert _errors("catalog", catalog) != []


def test_catalog_cross_references():
    catalog = validate_content.load_json(REPO_ROOT / "content" / "catalog.json")
    catalog["missions"][1]["unlock_rule"]["mission_id"] = "no-such-mission"
    assert validate_content.check_catalog(catalog) != []
