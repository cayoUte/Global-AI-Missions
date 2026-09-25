"""Story graph engine: a mission as a state-space search problem. Standard library only.

Public API (services import from `app.engine` only, never from the submodules):

    graph = build_graph(items_doc, mission_doc)   # immutable MissionGraph (ValueError if broken)
    report = validate(graph)                       # ValidationReport(ok, errors, path_count, ...)
    h = compute_h(graph)                           # {node_id: min story-minutes to an ending}

    s = initial_state(graph)                       # State(node_id, minutes_left, flags, ...)
    actions(graph, s)                              # ACTIONS(s): CONTINUE | choose ids | TYPE
    t = result(graph, s, Action("choose", "b"), h) # RESULT(s, a) -> Transition (grades inside)
    t = result(graph, s, Action("type", "have"), h)
    t = result(graph, s, CONTINUE, h)
    t = advance(graph, s, "incorrect", h)       # RESULT given an outcome (no answer needed)
    t.next_state, t.outcome, t.maya_decision, t.maya_line   # outcome: correct | incorrect | None
    is_goal(graph, s)                              # s is at an ending

    decision = arrival_decision(graph, h, s, via_rescue=...)  # quiet | hint | rescue (StateView)
    maya_line(graph, s, decision)                  # hint, intro, node line or mood line
    resolve_scene(graph, node_id, s.flags)         # Scene with variants resolved
    clock(graph, s.minutes_left)                   # api-contract Clock dict with its label
    normalize_answer(text)                         # the fill-blank normalization (validation too)

    build_diary(graph, [StepRecord(...), ...])     # parent pointers -> [DiaryEntry]
    run(graph, h, SimulatedStudent("A2_weak_listening"), seed) -> Trace   # veteran seed
    calibrate(graph, "A2", runs=1000) -> {ending_key: count}

Answer keys are read only by grade() inside result(); Transition and Trace never carry them.
"""

from app.engine.diary import DiaryEntry, StepRecord, build_diary
from app.engine.graph import (
    CHECKPOINT,
    CORRECT,
    ENDING,
    INCORRECT,
    TRAIN_DEPARTED,
    Edge,
    MissionGraph,
    Scene,
    build_graph,
    resolve_scene,
)
from app.engine.heuristic import compute_h
from app.engine.maya import (
    HINT,
    QUIET,
    RESCUE,
    arrival_decision,
    decide,
    maya_line,
    next_mood,
    slack,
)
from app.engine.simulator import PROFILES, SimulatedStudent, Trace, TraceStep, calibrate, run
from app.engine.state import State, clock, clock_time, initial_state
from app.engine.transition import (
    CONTINUE,
    Action,
    Transition,
    actions,
    advance,
    grade,
    is_goal,
    normalize_answer,
    result,
)
from app.engine.validator import ValidationReport, validate, validate_documents

__all__ = [
    "CHECKPOINT",
    "CONTINUE",
    "CORRECT",
    "ENDING",
    "HINT",
    "INCORRECT",
    "PROFILES",
    "QUIET",
    "RESCUE",
    "TRAIN_DEPARTED",
    "Action",
    "DiaryEntry",
    "Edge",
    "MissionGraph",
    "Scene",
    "SimulatedStudent",
    "State",
    "StepRecord",
    "Trace",
    "TraceStep",
    "Transition",
    "ValidationReport",
    "actions",
    "advance",
    "arrival_decision",
    "build_diary",
    "build_graph",
    "calibrate",
    "clock",
    "clock_time",
    "compute_h",
    "decide",
    "grade",
    "initial_state",
    "is_goal",
    "maya_line",
    "next_mood",
    "normalize_answer",
    "resolve_scene",
    "result",
    "run",
    "slack",
    "validate",
    "validate_documents",
]
