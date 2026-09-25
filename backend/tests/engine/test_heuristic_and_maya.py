import pytest

from app.engine import (
    CORRECT,
    HINT,
    INCORRECT,
    QUIET,
    RESCUE,
    TRAIN_DEPARTED,
    Action,
    State,
    decide,
    maya_line,
    next_mood,
    result,
)
from app.engine.maya import AFTER_INCORRECT, ON_ARRIVAL


def test_h_values_on_the_fixture(graph, h):
    assert h["end_made_it"] == h["end_night_bus"] == 0
    assert h["c10"] == 1
    assert h["intro"] == 10  # ten correct answers at 1 minute each
    assert set(h) == set(graph.nodes)


def test_h_is_admissible_on_every_enumerated_path(h, all_paths):
    assert len(all_paths) == 1024
    for path in all_paths:
        final_minutes = path[-1][0].minutes_left
        for s, _ in path:
            assert h[s.node_id] <= s.minutes_left - final_minutes  # true cost-to-go


def test_h_is_consistent_on_every_non_rescue_edge(graph, h):
    for edge in graph.edges:
        if not edge.rescue:
            assert h[edge.source] <= edge.minutes + h[edge.target]


@pytest.mark.parametrize(("minutes_left", "decision"), [(12, HINT), (13, QUIET), (-1, HINT)])
def test_hint_threshold_is_slack_below_3(graph, h, minutes_left, decision):
    assert h["c01"] == 10
    assert decide(graph, h, State("c01", minutes_left), ON_ARRIVAL) == decision


def test_non_checkpoints_are_always_quiet(graph, h):
    assert decide(graph, h, State("intro", 0), ON_ARRIVAL) == QUIET


@pytest.mark.parametrize(
    ("state", "decision"),
    [
        (State("c07", 5), RESCUE),  # detour slack -1, rescue slack 1
        (State("c07", 4), RESCUE),  # detour slack -2, rescue slack 0
        (State("c07", 6), QUIET),  # the detour still makes the train
        (State("c07", 3), QUIET),  # lost even with the rescue
        (State("c07", 5, rescued=True), QUIET),  # at most one rescue
        (State("c07", 5, frozenset({TRAIN_DEPARTED})), QUIET),
        (State("c05", 4), QUIET),  # no rescue edge here
    ],
)
def test_rescue_policy(graph, h, state, decision):
    assert decide(graph, h, state, AFTER_INCORRECT) == decision


def test_rescue_transition_and_single_rescue(graph, h, all_paths):
    t = result(graph, State("c07", 5), Action("choose", "c"), h)
    assert (t.maya_decision, t.next_state.node_id, t.next_state.rescued) == (
        RESCUE,
        "c07_rescue",
        True,
    )
    assert t.maya_line == graph.node("c07")["maya"]["reaction_rescue"]
    for path in all_paths:
        assert sum(1 for _, step in path if step and step.edge.rescue) <= 1


@pytest.mark.parametrize(
    ("mood", "outcome", "slack", "expected"),
    [
        ("curious", CORRECT, 5, "proud"),
        ("curious", CORRECT, 2, "encouraging"),
        ("worried", CORRECT, 8, "encouraging"),  # worry recovers gradually
        ("proud", INCORRECT, 5, "encouraging"),
        ("proud", INCORRECT, 2, "worried"),
        ("encouraging", None, 0, "encouraging"),
    ],
)
def test_mood_machine(mood, outcome, slack, expected):
    assert next_mood(mood, outcome, slack) == expected


def test_line_selection(graph):
    assert maya_line(graph, State("c01", 12), HINT) == graph.items["q01"]["hint"]
    assert maya_line(graph, State("c01", 18), QUIET) == graph.node("c01")["maya"]["intro"]
    variant = graph.node("c04")["scene"]["variants"][0]["maya_line"]
    assert maya_line(graph, State("c04", 12, frozenset({"lost_ticket"})), QUIET) == variant
    fallback = maya_line(graph, State("c01_ok", 17, maya_mood="proud"), QUIET)
    assert fallback in graph.mood_lines["proud"]
