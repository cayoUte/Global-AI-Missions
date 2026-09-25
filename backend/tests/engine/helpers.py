"""Shared helpers for the engine tests (imported by conftest.py and the test modules)."""

import json
from pathlib import Path

from app.engine import CORRECT, INCORRECT, advance, initial_state, is_goal

MISSIONS_DIR = Path(__file__).resolve().parents[3] / "content" / "missions"
FIXTURE_DIR = MISSIONS_DIR / "_fixture"
REAL_DIR = MISSIONS_DIR / "the-last-train"


def load_docs(folder: Path = FIXTURE_DIR) -> tuple[dict, dict]:
    read = lambda name: json.loads((folder / name).read_text(encoding="utf-8"))  # noqa: E731
    return read("items.json"), read("mission.json")


def enumerate_paths(graph, h):
    """Every outcome path as a list of (state, transition-or-None). Tree search, no explored set."""
    paths, stack = [], [(initial_state(graph), [])]
    while stack:
        s, path = stack.pop()
        if is_goal(graph, s):
            paths.append([*path, (s, None)])
            continue
        outcomes = (CORRECT, INCORRECT) if graph.kind(s.node_id) == "checkpoint" else (None,)
        for outcome in outcomes:
            t = advance(graph, s, outcome, h)
            stack.append((t.next_state, [*path, (s, t)]))
    return paths
