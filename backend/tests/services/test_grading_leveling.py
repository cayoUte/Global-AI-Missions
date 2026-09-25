"""grading.py and leveling.py against ASSESSMENT_SPEC.md §4-§5 and §7.1 (its 9 worked examples)."""

import pytest

from app.services.grading import GradedItem, grade_attempt, percent, strength_and_challenge
from app.services.leveling import report_label, suggest_level
from tests.fakes import load_docs

ITEMS = load_docs("the-last-train")[0]["items"]

# (incorrect items, score, base, suggested, per-skill pct G/L/R/V, strength, challenge, reason)
EXAMPLES = [
    (
        set(),
        100,
        "B2",
        "B2",
        (100, 100, 100, 100),
        "grammar",
        "listening",
        "100% points to B2. B2 needs 1 of 2 B2 checkpoints — you had 2 — "
        "so your suggested level is B2.",
    ),
    (
        {"q02"},
        90,
        "B2",
        "B2",
        (100, 50, 100, 100),
        "grammar",
        "listening",
        "90% points to B2. B2 needs 1 of 2 B2 checkpoints — you had 2 — "
        "so your suggested level is B2.",
    ),
    (
        {"q07", "q08", "q09"},
        70,
        "B1",
        "A2",
        (75, 50, 100, 50),
        "reading",
        "listening",
        "70% points to B1. B1 needs 2 of 3 B1 checkpoints — you had 1 — "
        "so your suggested level is A2.",
    ),
    (
        {"q06", "q07", "q09"},
        70,
        "B1",
        "A2",
        (50, 50, 100, 100),
        "reading",
        "grammar",
        "70% points to B1. B1 needs 2 of 3 B1 checkpoints — you had 1 — "
        "so your suggested level is A2.",
    ),
    (
        {"q07", "q09"},
        80,
        "B1",
        "B1",
        (75, 50, 100, 100),
        "reading",
        "listening",
        "80% points to B1. B1 needs 2 of 3 B1 checkpoints — you had 2 — "
        "so your suggested level is B1.",
    ),
    (
        {"q01", "q02", "q04", "q05"},
        60,
        "A2",
        "PRE_A1",
        (50, 50, 100, 50),
        "reading",
        "grammar",
        "60% points to A2. A2 needs 2 of 3 A2 checkpoints — you had 1 — and A1 needs 1 of 2 A1 "
        "checkpoints — you had 0 — "
        "so your suggested level is Pre-A1.",
    ),
    (
        {"q01", "q05", "q07", "q08", "q09", "q10"},
        40,
        "A1",
        "A1",
        (25, 50, 50, 50),
        "listening",
        "grammar",
        "40% points to A1. A1 needs 1 of 2 A1 checkpoints — you had 1 — "
        "so your suggested level is A1.",
    ),
    (
        {"q02", "q03", "q05", "q06", "q07", "q08", "q09", "q10"},
        20,
        "PRE_A1",
        "PRE_A1",
        (25, 0, 0, 50),
        "vocabulary",
        "listening",
        "20% points to Pre-A1, so your suggested level is Pre-A1.",
    ),
    (
        {"q01", "q02", "q05", "q07", "q08", "q09", "q10"},
        30,
        "A1",
        "PRE_A1",
        (25, 0, 50, 50),
        "reading",
        "listening",
        "30% points to A1. A1 needs 1 of 2 A1 checkpoints — you had 0 — "
        "so your suggested level is "
        "Pre-A1.",
    ),
]


@pytest.mark.parametrize("example", EXAMPLES, ids=[f"example{i}" for i in range(1, 10)])
def test_worked_examples(example):
    wrong, score, base, suggested, pcts, strength, challenge, reason = example
    graded = [GradedItem(i["id"], i["skill"], i["cefr"], i["id"] not in wrong) for i in ITEMS]
    result = grade_attempt(graded)
    assert (result.correct, result.incorrect, result.total) == (10 - len(wrong), len(wrong), 10)
    assert result.score_pct == score
    assert [s.skill for s in result.skills] == ["grammar", "listening", "reading", "vocabulary"]
    assert tuple(s.pct for s in result.skills) == pcts
    level = suggest_level(result.score_pct, result.by_cefr)
    assert (level.base_cefr, level.cefr, level.reason) == (base, suggested, reason)
    assert strength_and_challenge(result.skills) == (strength, challenge)
    if base == "PRE_A1":
        assert level.evidence == ()
    if suggested == "PRE_A1" and base != "PRE_A1":
        assert all(not e.met for e in level.evidence)


def test_example_3_evidence_matches_the_contract():
    graded = [
        GradedItem(i["id"], i["skill"], i["cefr"], i["id"] not in {"q07", "q08", "q09"})
        for i in ITEMS
    ]
    result = grade_attempt(graded)
    evidence = suggest_level(70, result.by_cefr).evidence
    assert [(e.cefr, e.correct, e.total, e.required, e.met) for e in evidence] == [
        ("B1", 1, 3, 2, False),
        ("A2", 3, 3, 2, True),
    ]


def test_percent_rounds_half_up_with_integers():
    assert [percent(1, 3), percent(2, 3), percent(1, 8), percent(7, 10), percent(3, 4)] == [
        33,
        67,
        13,
        70,
        75,
    ]
    assert percent(1, 2) == 50 and percent(0, 0) == 0


def test_a_level_with_no_items_is_never_met():
    level = suggest_level(90, {"B1": (3, 3)})
    assert level.evidence[0].cefr == "B2" and not level.evidence[0].met
    assert level.evidence[0].total == 0 and level.evidence[0].required == 0
    assert level.cefr == "B1"


def test_hints_never_change_the_score():
    # Scoring only sees outcomes; there is no hint input at all. Same outcomes -> same result.
    graded = [GradedItem(i["id"], i["skill"], i["cefr"], True) for i in ITEMS]
    assert grade_attempt(graded) == grade_attempt(list(graded))


def test_report_label_format():
    assert report_label("A2", "The Last Train", 70) == "A2 · The Last Train — 70%"
    assert report_label("PRE_A1", "The Last Train", 20) == "Pre-A1 · The Last Train — 20%"
