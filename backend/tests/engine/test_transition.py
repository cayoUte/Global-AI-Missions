import dataclasses

import pytest

from app.engine import (
    CONTINUE,
    CORRECT,
    INCORRECT,
    TRAIN_DEPARTED,
    Action,
    State,
    actions,
    grade,
    initial_state,
    is_goal,
    normalize_answer,
    result,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("have", "have"),
        ("  Have. ", "have"),
        ("HAVE!", "have"),
        ("a   single\tticket ?", "a single ticket"),
        ("I’m here...", "i'm here"),
        ("can‘t", "can't"),
        ("?!.", ""),
    ],
)
def test_normalize_answer(raw, expected):
    assert normalize_answer(raw) == expected


def test_grade_choice_and_fill_blank(graph):
    choice, blank = graph.items["q01"], graph.items["q03"]
    assert grade(choice, Action("choose", "b"))
    assert not grade(choice, Action("choose", "a"))
    assert not grade(choice, Action("type", "b"))
    assert grade(blank, Action("type", "  Get. "))
    assert grade(blank, Action("type", "BUY"))
    assert not grade(blank, Action("type", "take"))
    assert not grade(blank, Action("choose", "have"))


def test_actions_per_node_kind(graph):
    assert actions(graph, initial_state(graph)) == (CONTINUE,)
    assert actions(graph, State("c01", 18)) == tuple(Action("choose", i) for i in "abc")
    assert actions(graph, State("c03", 16)) == (Action("type"),)
    assert actions(graph, State("end_made_it", 5)) == ()


@pytest.mark.parametrize(
    ("node", "right", "wrong"),
    [
        ("c01", Action("choose", "b"), Action("choose", "c")),  # multiple_choice (listening)
        ("c02", Action("choose", "a"), Action("choose", "b")),  # vocabulary
        ("c03", Action("type", "Have."), Action("type", "take")),  # fill_blank
        ("c05", Action("choose", "b"), Action("choose", "a")),  # comprehension
    ],
)
def test_result_for_each_item_type(graph, h, node, right, wrong):
    s = State(node, 15)
    ok, fail = result(graph, s, right, h), result(graph, s, wrong, h)
    assert (ok.outcome, ok.next_state.node_id, ok.next_state.minutes_left) == (
        CORRECT,
        f"{node}_ok",
        14,
    )
    assert (fail.outcome, fail.next_state.node_id, fail.next_state.minutes_left) == (
        INCORRECT,
        f"{node}_fail",
        12,
    )
    assert ok.maya_line == graph.node(node)["maya"]["reaction_ok"]
    assert fail.maya_line == graph.node(node)["maya"]["reaction_fail"]


def test_result_rejects_actions_outside_actions_s(graph, h):
    with pytest.raises(ValueError):
        result(graph, State("c01", 18), Action("choose", "z"), h)
    with pytest.raises(ValueError):
        result(graph, State("c03", 16), Action("type", " ?! "), h)
    with pytest.raises(ValueError):
        result(graph, State("c01", 18), CONTINUE, h)
    with pytest.raises(ValueError):
        result(graph, State("end_night_bus", -3), CONTINUE, h)


def test_continue_and_edge_effects(graph, h):
    t = result(graph, initial_state(graph), CONTINUE, h)
    assert (t.next_state.node_id, t.outcome, t.minutes_cost) == ("c01", None, 0)
    t = result(graph, State("c03", 16), Action("type", "take"), h)
    assert "lost_ticket" in t.next_state.flags


def test_train_departed_is_set_automatically(graph, h):
    late = result(graph, State("c08", 2, rescued=True), Action("type", "never"), h)
    assert late.next_state.minutes_left == -1
    assert TRAIN_DEPARTED in late.next_state.flags
    on_time = result(graph, State("c08", 5, rescued=True), Action("type", "never"), h)
    assert TRAIN_DEPARTED not in on_time.next_state.flags


@pytest.mark.parametrize(
    ("state", "ending"),
    [
        (State("c10_ok", 0), "end_made_it"),
        (State("c10_ok", 4), "end_made_it"),
        (State("c10_rescue", 0, rescued=True), "end_made_it_with_maya"),
        (State("c10_fail", -1, frozenset({TRAIN_DEPARTED})), "end_night_bus"),
        (State("c10_fail", -2, frozenset({TRAIN_DEPARTED}), rescued=True), "end_night_bus"),
    ],
)
def test_ending_resolution_by_priority_and_condition(graph, h, state, ending):
    t = result(graph, state, CONTINUE, h)
    assert t.next_state.node_id == ending
    assert is_goal(graph, t.next_state)


def test_transition_never_carries_answer_content(graph, h):
    for s, a in [
        (State("c01", 18), Action("choose", "b")),
        (State("c03", 16), Action("type", "x")),
    ]:
        text = repr(dataclasses.asdict(result(graph, s, a, h)))
        for secret in ("answer_key", "correct_option_id", "accepted", "explanation", "'have'"):
            assert secret not in text
