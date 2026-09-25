"""A simulated student agent: a stochastic policy P(correct | skill, cefr) per profile.

Seeded and deterministic (random.Random(seed)). It acts on outcomes, never on options, so a
Trace holds nodes, outcomes, minutes and Maya's decisions but no answer content.
"""

import random
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from app.engine.graph import CORRECT, INCORRECT, MissionGraph
from app.engine.heuristic import compute_h
from app.engine.maya import HINT, RESCUE, arrival_decision
from app.engine.state import initial_state
from app.engine.transition import advance, is_goal

CEFR_RANK = {"PRE_A1": 0, "A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5}
# P(correct) by gap = item level - student level, clamped to [-3, 3].
P_BY_GAP = {-3: 0.97, -2: 0.95, -1: 0.9, 0: 0.75, 1: 0.45, 2: 0.25, 3: 0.12}
# profile -> (CEFR level, per-skill adjustment)
PROFILES: dict[str, tuple[str, dict[str, float]]] = {
    "A1": ("A1", {}),
    "A2": ("A2", {}),
    "B1": ("B1", {}),
    "B2": ("B2", {}),
    "A2_weak_listening": ("A2", {"listening": -0.3}),
}


@dataclass(frozen=True)
class SimulatedStudent:
    profile: str

    def p_correct(self, item: Mapping[str, Any]) -> float:
        level, skill_shift = PROFILES[self.profile]
        gap = max(-3, min(3, CEFR_RANK[item["cefr"]] - CEFR_RANK[level]))
        return min(0.99, max(0.01, P_BY_GAP[gap] + skill_shift.get(item["skill"], 0.0)))


@dataclass(frozen=True)
class TraceStep:
    node_id: str
    kind: str
    item_id: str | None
    outcome: str | None  # correct | incorrect on checkpoints
    minutes_left: int  # on arrival at the node
    maya_decision: str  # quiet | hint | rescue (as the StateView would show it)
    maya_mood: str


@dataclass(frozen=True)
class Trace:
    profile: str
    seed: int
    steps: tuple[TraceStep, ...]
    ending_key: str
    minutes_used: int
    rescued: bool
    hints: int
    correct: int


def run(graph: MissionGraph, h: Mapping[str, int], student: SimulatedStudent, seed: int) -> Trace:
    rng = random.Random(seed)
    s = initial_state(graph)
    decision = arrival_decision(graph, h, s)
    steps = []
    while True:
        item = graph.item_at(s.node_id)
        outcome = None
        if item is not None:
            outcome = CORRECT if rng.random() < student.p_correct(item) else INCORRECT
        steps.append(
            TraceStep(
                s.node_id,
                graph.kind(s.node_id),
                item["id"] if item else None,
                outcome,
                s.minutes_left,
                decision,
                s.maya_mood,
            )
        )
        if is_goal(graph, s):
            break
        step = advance(graph, s, outcome, h)
        s = step.next_state
        decision = arrival_decision(graph, h, s, via_rescue=step.maya_decision == RESCUE)
    return Trace(
        profile=student.profile,
        seed=seed,
        steps=tuple(steps),
        ending_key=graph.node(s.node_id)["ending"]["key"],
        minutes_used=graph.minutes_available - s.minutes_left,
        rescued=s.rescued,
        hints=sum(1 for st in steps if st.maya_decision == HINT),
        correct=sum(1 for st in steps if st.outcome == CORRECT),
    )


def calibrate(graph: MissionGraph, profile: str, runs: int = 1000, seed: int = 0) -> dict[str, int]:
    """Endings distribution over `runs` seeded runs (informational, not a gate)."""
    h, student = compute_h(graph), SimulatedStudent(profile)
    counts = {n["ending"]["key"]: 0 for n in graph.nodes.values() if n["kind"] == "ending"}
    for i in range(runs):
        counts[run(graph, h, student, seed + i).ending_key] += 1
    return counts
