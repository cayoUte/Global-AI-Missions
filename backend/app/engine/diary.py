"""The Diary: the solution path rebuilt by following parent pointers back from the ending."""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from app.engine.graph import CORRECT, MissionGraph, resolve_scene
from app.engine.state import clock_time

OUTCOME_LABEL = {CORRECT: "understood", "incorrect": "missed"}  # neutral words for the Report


@dataclass(frozen=True)
class StepRecord:
    """One persisted step (a search node): the backend maps its rows to this shape."""

    step_id: str
    parent_id: str | None
    node_id: str
    minutes_left: int  # on arrival
    flags: frozenset[str]
    outcome: str | None  # correct | incorrect for checkpoints
    maya_decision: str


@dataclass(frozen=True)
class DiaryEntry:
    seq: int
    clock: str
    node_id: str
    kind: str
    location: str
    text: str
    checkpoint: dict[str, Any] | None  # item_id, type, skill, cefr, outcome (closed attempts only)
    maya_decision: str


def build_diary(graph: MissionGraph, steps: Iterable[StepRecord]) -> list[DiaryEntry]:
    by_id = {step.step_id: step for step in steps}
    parents = {step.parent_id for step in by_id.values()}
    leaves = [step for step in by_id.values() if step.step_id not in parents]
    if len(leaves) != 1:
        raise ValueError(f"expected one leaf step, found {len(leaves)}")
    path, step = [], leaves[0]
    while True:
        path.append(step)
        if len(path) > len(by_id):
            raise ValueError("the parent pointers form a cycle")
        if step.parent_id is None:
            break
        step = by_id[step.parent_id]
    entries = []
    for seq, step in enumerate(reversed(path), start=1):
        scene = resolve_scene(graph, step.node_id, step.flags)
        item = graph.item_at(step.node_id)
        checkpoint = None
        if item is not None:
            checkpoint = {
                "item_id": item["id"],
                "type": item["type"],
                "skill": item["skill"],
                "cefr": item["cefr"],
                "outcome": OUTCOME_LABEL.get(step.outcome or ""),
            }
        entries.append(
            DiaryEntry(
                seq,
                clock_time(graph, step.minutes_left),
                step.node_id,
                graph.kind(step.node_id),
                scene.location,
                scene.diary,
                checkpoint,
                step.maya_decision,
            )
        )
    return entries
