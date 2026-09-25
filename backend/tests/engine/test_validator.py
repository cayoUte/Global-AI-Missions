import json
import shutil

import pytest

from app.engine import validate_documents
from app.engine.cli import main as cli_main
from tests.engine.helpers import FIXTURE_DIR, REAL_DIR, load_docs


def _node(mission, node_id):
    return next(n for n in mission["nodes"] if n["id"] == node_id)


def _item(items, item_id):
    return next(i for i in items["items"] if i["id"] == item_id)


def test_fixture_is_valid(docs):
    report = validate_documents(*docs)
    assert report.ok, report.errors
    assert report.warnings == []
    assert report.path_count == 1024
    assert (report.min_minutes, report.max_minutes) == (10, 30)
    assert all(count > 0 for count in report.endings.values())
    assert sum(report.endings.values()) == 1024
    assert "c07_fail" in report.departed_nodes
    assert "c07" not in report.departed_nodes  # first departure only after checkpoint 7


@pytest.mark.skipif(not (REAL_DIR / "mission.json").exists(), reason="real mission not written")
def test_real_mission_is_valid():
    report = validate_documents(*load_docs(REAL_DIR))
    assert report.ok, report.errors
    assert report.path_count == 1024


def _break(docs, mutate):
    items, mission = docs
    mutate(items, mission)
    return validate_documents(items, mission)


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (
            lambda i, m: _item(i, "q01")["answer_key"].update(correct_option_id="z"),
            "correct_option_id",
        ),
        (
            lambda i, m: _item(i, "q01").update(options=_item(i, "q01")["options"][:2]),
            "3-4 options",
        ),
        (lambda i, m: _item(i, "q02")["options"][1].update(id="a"), "not unique"),
        (lambda i, m: _item(i, "q03").update(options=[{"id": "a", "text": "x"}]), "options null"),
        (lambda i, m: _item(i, "q03")["answer_key"].update(accepted=["?!"]), "accepted answer"),
        (lambda i, m: _item(i, "q03").update(prompt="No gap."), "___"),
        (lambda i, m: _item(i, "q04").update(skill="vocabulary"), "blueprint"),
        (lambda i, m: _item(i, "q01").update(cefr="B2"), "CEFR order"),
        (lambda i, m: _node(m, "c09")["scene"].pop("variants"), "Plan-B"),
        (
            lambda i, m: m["edges"].remove(next(e for e in m["edges"] if e["from"] == "c05_ok")),
            "dead end",
        ),
        (
            lambda i, m: next(e for e in m["edges"] if e["from"] == "c02_ok").update(to="c01"),
            "cycle",
        ),
        (
            lambda i, m: m["edges"].remove(
                next(e for e in m["edges"] if e["from"] == "c04" and e["on"] == "incorrect")
            ),
            "one correct, one incorrect",
        ),
        (lambda i, m: m["edges"][0].update(to="nowhere"), "cannot build"),
        (lambda i, m: _node(m, "c02").update(item_id="q01"), "used by 2"),
    ],
)
def test_validator_rejects_broken_content(docs, mutate, expected):
    report = _break(docs, mutate)
    assert not report.ok
    assert any(expected in error for error in report.errors), report.errors


def test_duplicate_accepted_answers_are_reported_as_warnings(docs):
    report = _break(docs, lambda i, m: _item(i, "q03")["answer_key"]["accepted"].append("Have."))
    assert report.ok
    assert any("duplicate accepted" in w for w in report.warnings)


def test_cli_validate_fails_on_a_broken_answer_key(tmp_path, capsys):
    folder = tmp_path / "_fixture"
    shutil.copytree(FIXTURE_DIR, folder)
    assert cli_main(["--missions-dir", str(tmp_path), "validate"]) == 0
    items = json.loads((folder / "items.json").read_text(encoding="utf-8"))
    items["items"][3]["answer_key"]["correct_option_id"] = "z"
    (folder / "items.json").write_text(json.dumps(items), encoding="utf-8")
    assert cli_main(["--missions-dir", str(tmp_path), "validate"]) == 1
    assert "correct_option_id" in capsys.readouterr().out
