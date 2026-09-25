"""The transition model: ACTIONS(s), RESULT(s, a), the goal test and grading.

grade() is the only function that reads answer keys. Transition objects carry the outcome
(correct | incorrect) and the edge taken, never the key or the accepted answers.
"""

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Any

from app.engine.graph import (
    ALWAYS,
    CHECKPOINT,
    CORRECT,
    ENDING,
    ENDING_EDGE,
    INCORRECT,
    TRAIN_DEPARTED,
    Edge,
    MissionGraph,
)
from app.engine.maya import AFTER_INCORRECT, QUIET, RESCUE, decide, next_mood, reaction_line
from app.engine.state import State

CONTINUE_KIND, CHOOSE_KIND, TYPE_KIND = "continue", "choose", "type"


@dataclass(frozen=True)
class Action:
    kind: str  # continue | choose (option_id in value) | type (free text in value)
    value: str | None = None


CONTINUE = Action(CONTINUE_KIND)


@dataclass(frozen=True)
class Transition:
    next_state: State
    outcome: str | None  # correct | incorrect on checkpoints, None elsewhere
    edge: Edge
    minutes_cost: int
    maya_decision: str  # quiet | rescue
    maya_line: str | None  # Maya's reaction after a checkpoint answer


_CURLY = str.maketrans({"‘": "'", "’": "'", "ʼ": "'"})


def normalize_answer(text: str) -> str:
    """Fill-blank normalization (ASSESSMENT_SPEC): straighten curly apostrophes, lowercase,
    trim, collapse inner whitespace, strip final punctuation. Shared by validation and grading."""
    text = " ".join(text.translate(_CURLY).lower().split())
    return text.rstrip(".,!?;:…").rstrip()


def grade(item: Mapping[str, Any], action: Action) -> bool:
    key = item["answer_key"]
    if item["type"] == "fill_blank":
        accepted = {normalize_answer(a) for a in key["accepted"]}
        return action.kind == TYPE_KIND and normalize_answer(action.value or "") in accepted
    return action.kind == CHOOSE_KIND and action.value == key["correct_option_id"]


def actions(graph: MissionGraph, s: State) -> tuple[Action, ...]:
    """ACTIONS(s). A fill_blank's action space is any text: one TYPE template stands for it."""
    kind = graph.kind(s.node_id)
    if kind == ENDING:
        return ()
    if kind != CHECKPOINT:
        return (CONTINUE,)
    item = graph.item_at(s.node_id)
    assert item is not None
    if item["options"] is None:
        return (Action(TYPE_KIND),)
    return tuple(Action(CHOOSE_KIND, option["id"]) for option in item["options"])


def is_goal(graph: MissionGraph, s: State) -> bool:
    return graph.kind(s.node_id) == ENDING


def result(graph: MissionGraph, s: State, action: Action, h: Mapping[str, int]) -> Transition:
    """RESULT(s, a): grade the action (checkpoints) and follow the matching edge."""
    allowed = actions(graph, s)
    if action.kind == TYPE_KIND and allowed == (Action(TYPE_KIND),):
        if not isinstance(action.value, str) or not normalize_answer(action.value):
            raise ValueError("a fill_blank answer needs non-empty text")
    elif action not in allowed:
        raise ValueError(f"action {action} is not available at node '{s.node_id}'")
    outcome = None
    item = graph.item_at(s.node_id)
    if item is not None:
        outcome = CORRECT if grade(item, action) else INCORRECT
    return advance(graph, s, outcome, h)


def advance(graph: MissionGraph, s: State, outcome: str | None, h: Mapping[str, int]) -> Transition:
    """The transition given an outcome. RESULT uses it after grading; the validator and the
    simulator use it directly, so they never need options or answers."""
    if is_goal(graph, s):
        raise ValueError(f"'{s.node_id}' is an ending: no actions")
    if graph.kind(s.node_id) != CHECKPOINT:
        edge = _continue_edge(graph, s)
        return Transition(_follow(s, edge), None, edge, edge.minutes, QUIET, None)
    if outcome not in (CORRECT, INCORRECT):
        raise ValueError("a checkpoint needs an outcome")
    decision = QUIET
    if outcome == INCORRECT and decide(graph, h, s, AFTER_INCORRECT) == RESCUE:
        decision = RESCUE
    edges = graph.out_edges(s.node_id)
    edge = next((e for e in edges if e.on == outcome and e.rescue == (decision == RESCUE)), None)
    if edge is None:
        raise ValueError(f"checkpoint '{s.node_id}' has no '{outcome}' edge")
    after = _follow(s, edge, rescued=s.rescued or decision == RESCUE)
    slack_after = after.minutes_left - h[after.node_id]
    after = replace(after, maya_mood=next_mood(s.maya_mood, outcome, slack_after))
    line = reaction_line(graph, s, outcome, decision)
    return Transition(after, outcome, edge, edge.minutes, decision, line)


def _follow(s: State, edge: Edge, rescued: bool | None = None) -> State:
    """Apply an edge: path cost, flag effects and the automatic train_departed flag."""
    minutes_left = s.minutes_left - edge.minutes
    flags = s.flags | set(edge.set_flags) | ({TRAIN_DEPARTED} if minutes_left < 0 else set())
    return replace(
        s,
        node_id=edge.target,
        minutes_left=minutes_left,
        flags=frozenset(flags),
        rescued=s.rescued if rescued is None else rescued,
    )


def _continue_edge(graph: MissionGraph, s: State) -> Edge:
    """CONTINUE: the single always edge, or the best-priority ending whose condition holds."""
    edges = graph.out_edges(s.node_id)
    always = [e for e in edges if e.on == ALWAYS]
    if always:
        return always[0]
    candidates = [e for e in edges if e.on == ENDING_EDGE]
    matching = [e for e in candidates if ending_matches(graph, e.target, _follow(s, e))]
    if not matching:
        raise ValueError(f"no ending condition matches at '{s.node_id}'")
    return min(matching, key=lambda e: graph.node(e.target)["ending"]["priority"])


def ending_matches(graph: MissionGraph, ending_id: str, s: State) -> bool:
    condition = graph.node(ending_id)["ending"]["condition"]
    checks = {
        "min_minutes_left": lambda v: s.minutes_left >= v,
        "max_minutes_left": lambda v: s.minutes_left <= v,
        "rescued": lambda v: s.rescued == v,
        "train_departed": lambda v: s.train_departed == v,
    }
    return all(checks[name](value) for name, value in condition.items())
