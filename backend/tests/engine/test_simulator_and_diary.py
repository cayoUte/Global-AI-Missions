import dataclasses
import random

import pytest

from app.engine import (
    CORRECT,
    PROFILES,
    RESCUE,
    TRAIN_DEPARTED,
    SimulatedStudent,
    StepRecord,
    TraceStep,
    build_diary,
    calibrate,
    clock,
    run,
)


def test_run_is_deterministic_per_seed(graph, h):
    student = SimulatedStudent("A2_weak_listening")
    assert run(graph, h, student, 7) == run(graph, h, student, 7)
    assert len({run(graph, h, student, seed) for seed in range(20)}) > 1


def test_trace_shape_and_no_answer_content(graph, h):
    trace = run(graph, h, SimulatedStudent("B1"), 3)
    assert [f.name for f in dataclasses.fields(TraceStep)] == [
        "node_id",
        "kind",
        "item_id",
        "outcome",
        "minutes_left",
        "maya_decision",
        "maya_mood",
    ]
    checkpoints = [st for st in trace.steps if st.kind == "checkpoint"]
    assert len(checkpoints) == 10 and all(st.outcome for st in checkpoints)
    assert trace.steps[-1].kind == "ending"
    assert trace.minutes_used == graph.minutes_available - trace.steps[-1].minutes_left
    assert trace.correct == sum(st.outcome == CORRECT for st in checkpoints)
    text = repr(dataclasses.asdict(trace))
    assert "answer_key" not in text and "options" not in text


def test_profiles_order_the_probabilities(graph):
    listening = graph.items["q06"]  # B1 listening
    p = {name: SimulatedStudent(name).p_correct(listening) for name in PROFILES}
    assert p["A2_weak_listening"] < p["A2"] < p["B1"] < p["B2"]
    assert p["A1"] < p["A2"]
    assert SimulatedStudent("A2_weak_listening").p_correct(graph.items["q07"]) == p["A2"]


def test_calibrate_counts_every_run_and_is_deterministic(graph):
    counts = calibrate(graph, "A2", runs=200)
    assert sum(counts.values()) == 200
    assert counts == calibrate(graph, "A2", runs=200)
    b1, a1 = calibrate(graph, "B1", runs=200), calibrate(graph, "A1", runs=200)
    assert b1["night_bus"] < a1["night_bus"]


def _records_from_trace(graph, h, trace):
    """What the backend would persist: one step per node, each pointing to its parent."""
    records, flags, parent = [], frozenset(), None
    for i, st in enumerate(trace.steps):
        if st.minutes_left < 0:
            flags = flags | {TRAIN_DEPARTED}
        records.append(
            StepRecord(
                f"s{i}", parent, st.node_id, st.minutes_left, flags, st.outcome, st.maya_decision
            )
        )
        parent = f"s{i}"
    return records


def test_diary_rebuilds_the_path_from_parent_pointers(graph, h):
    trace = next(
        t
        for t in (run(graph, h, SimulatedStudent("A1"), s) for s in range(50))
        if t.ending_key == "night_bus"
    )
    records = _records_from_trace(graph, h, trace)
    shuffled = records[:]
    random.Random(1).shuffle(shuffled)
    diary = build_diary(graph, shuffled)
    assert [e.node_id for e in diary] == [st.node_id for st in trace.steps]
    assert [e.seq for e in diary] == list(range(1, len(diary) + 1))
    assert diary[0].clock == "21:47" and diary[0].text == graph.node("intro")["diary"]
    outcomes = {e.checkpoint["outcome"] for e in diary if e.checkpoint}
    assert outcomes <= {"understood", "missed"}
    departed = [e for e in diary if e.clock > "22:05" and e.kind != "ending"]
    assert departed and all(e.text.startswith("Plan B") for e in departed)


def test_diary_marks_the_rescue_and_rejects_two_leaves(graph, h):
    trace = next(
        t for t in (run(graph, h, SimulatedStudent("A2"), s) for s in range(200)) if t.rescued
    )
    diary = build_diary(graph, _records_from_trace(graph, h, trace))
    assert any(e.maya_decision == RESCUE and e.node_id.endswith("_rescue") for e in diary)
    with pytest.raises(ValueError):
        build_diary(
            graph,
            [
                StepRecord("a", None, "intro", 18, frozenset(), None, "quiet"),
                StepRecord("b", None, "c01", 18, frozenset(), None, "quiet"),
            ],
        )


@pytest.mark.parametrize(
    ("minutes_left", "label"),
    [
        (12, "21:53 · 12 min to departure"),
        (0, "22:05 · Departing now"),
        (-2, "22:07 · Train departed — Plan B"),
    ],
)
def test_clock_labels(graph, minutes_left, label):
    assert clock(graph, minutes_left)["label"] == label
    assert clock(graph, minutes_left)["train_departed"] is (minutes_left < 0)
