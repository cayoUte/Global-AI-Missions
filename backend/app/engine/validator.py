"""Structural and content validator. Graph search proves the SHARED_CONTEXT §4-§5 invariants.

1. Content integrity of every item (answer keys are checked here, never exposed).
2. BFS with an explored set: every node reachable; no dead ends; checkpoint edges well formed.
3. Kahn's topological sort: no cycles.
4. DFS over every outcome path (tree search, no explored set on purpose: we need each path):
   10 checkpoints in the same order, 4/2/2/2 types, skills and the rising CEFR spread; every node
   reached with train_departed has a Plan-B variant; path count and min/max story-minutes.
"""

from collections import Counter, deque
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from app.engine.graph import (
    ALWAYS,
    CHECKPOINT,
    CORRECT,
    ENDING,
    ENDING_EDGE,
    INCORRECT,
    TRAIN_DEPARTED,
    MissionGraph,
    build_graph,
)
from app.engine.heuristic import compute_h
from app.engine.state import initial_state
from app.engine.transition import advance, is_goal, normalize_answer

BLUEPRINT = Counter(
    {
        ("multiple_choice", "grammar"): 2,
        ("multiple_choice", "listening"): 2,
        ("fill_blank", "grammar"): 2,
        ("comprehension", "reading"): 2,
        ("vocabulary", "vocabulary"): 2,
    }
)
CEFR_SEQUENCE = ("A1", "A1", "A2", "A2", "A2", "B1", "B1", "B1", "B2", "B2")
MAX_PATHS = 1 << 16


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    path_count: int = 0
    min_minutes: int | None = None
    max_minutes: int | None = None
    endings: dict[str, int] = field(default_factory=dict)  # ending key -> number of paths
    departed_nodes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_documents(
    items_doc: Mapping[str, Any], mission_doc: Mapping[str, Any]
) -> ValidationReport:
    try:
        graph = build_graph(items_doc, mission_doc)
    except (ValueError, KeyError) as exc:
        return ValidationReport(errors=[f"cannot build the graph: {exc}"])
    return validate(graph)


def validate(graph: MissionGraph) -> ValidationReport:
    report = ValidationReport()
    _check_items(graph, report)
    _check_structure(graph, report)
    if report.ok:
        _check_paths(graph, report)
    return report


def _check_items(graph: MissionGraph, report: ValidationReport) -> None:
    used = Counter(n["item_id"] for n in graph.nodes.values() if n["kind"] == CHECKPOINT)
    for item_id, item in graph.items.items():
        err = report.errors.append
        if used[item_id] != 1:
            err(f"item {item_id}: used by {used[item_id]} checkpoints (expected 1)")
        key, options = item["answer_key"], item["options"]
        if item["type"] == "fill_blank":
            accepted = [normalize_answer(a) for a in key.get("accepted", [])]
            if options is not None:
                err(f"item {item_id}: fill_blank must have options null")
            if not accepted or not all(accepted):
                err(f"item {item_id}: fill_blank needs at least one non-empty accepted answer")
            if len(set(accepted)) != len(accepted):
                report.warnings.append(
                    f"item {item_id}: duplicate accepted answers after "
                    "normalization (de-duplicated at seed time)"
                )
            if item["prompt"].count("___") != 1:
                err(f"item {item_id}: fill_blank prompt needs exactly one ___ gap")
            continue
        ids = [o["id"] for o in options or []]
        if not 3 <= len(ids) <= 4:
            err(f"item {item_id}: needs 3-4 options, has {len(ids)}")
        if len(set(ids)) != len(ids):
            err(f"item {item_id}: option ids are not unique")
        if key.get("correct_option_id") not in ids:
            err(f"item {item_id}: correct_option_id is not one of the options")


def _check_structure(graph: MissionGraph, report: ValidationReport) -> None:
    err = report.errors.append
    explored, frontier = {graph.start_node}, deque([graph.start_node])  # BFS
    while frontier:
        for edge in graph.out_edges(frontier.popleft()):
            if edge.target not in explored:
                explored.add(edge.target)
                frontier.append(edge.target)
    for node_id in graph.nodes:
        if node_id not in explored:
            err(f"node {node_id}: unreachable from {graph.start_node}")
    for node_id, node in graph.nodes.items():
        on = Counter((e.on, e.rescue) for e in graph.out_edges(node_id))
        if node["kind"] == ENDING:
            if on:
                err(f"node {node_id}: an ending cannot have outgoing edges")
        elif node["kind"] == CHECKPOINT:
            if (
                on[(CORRECT, False)] != 1
                or on[(INCORRECT, False)] != 1
                or on[(INCORRECT, True)] > 1
            ):
                err(f"node {node_id}: needs one correct, one incorrect and at most one rescue edge")
        elif not (on == Counter({(ALWAYS, False): 1}) or set(on) == {(ENDING_EDGE, False)}):
            err(f"node {node_id}: needs one 'always' edge or only 'ending' edges (dead end?)")
        for edge in graph.out_edges(node_id):
            if (edge.on == ENDING_EDGE) != (graph.kind(edge.target) == ENDING):
                err(f"edge {node_id} -> {edge.target}: 'ending' edges must target endings")
            for flag in edge.set_flags:
                if flag not in graph.declared_flags:
                    err(f"edge {node_id} -> {edge.target}: flag '{flag}' is not declared")
        for variant in node["scene"].get("variants", ()):
            if variant["when_flag"] not in graph.declared_flags | {TRAIN_DEPARTED}:
                err(f"node {node_id}: variant flag '{variant['when_flag']}' is not declared")
    indegree = Counter(e.target for e in graph.edges)  # Kahn: a cycle leaves nodes unsorted
    queue, sorted_count = deque(n for n in graph.nodes if indegree[n] == 0), 0
    while queue:
        sorted_count += 1
        for edge in graph.out_edges(queue.popleft()):
            indegree[edge.target] -= 1
            if indegree[edge.target] == 0:
                queue.append(edge.target)
    if sorted_count < len(graph.nodes):
        err("the graph has a cycle")
    h = compute_h(graph)
    for node_id in explored - set(h):
        err(f"node {node_id}: cannot reach an ending")


def _check_paths(graph: MissionGraph, report: ValidationReport) -> None:
    h, departed, sequences = compute_h(graph), set(), set()
    endings = {n["ending"]["key"]: 0 for n in graph.nodes.values() if n["kind"] == ENDING}
    stack: list[tuple[Any, tuple[str, ...]]] = [(initial_state(graph), ())]
    while stack and report.path_count < MAX_PATHS:
        s, checkpoints = stack.pop()
        if s.train_departed and not is_goal(graph, s):
            departed.add(s.node_id)
        if is_goal(graph, s):
            used = graph.minutes_available - s.minutes_left
            report.path_count += 1
            report.min_minutes = min(
                used, used if report.min_minutes is None else report.min_minutes
            )
            report.max_minutes = max(
                used, used if report.max_minutes is None else report.max_minutes
            )
            endings[graph.node(s.node_id)["ending"]["key"]] += 1
            sequences.add(checkpoints)
            continue
        is_checkpoint = graph.kind(s.node_id) == CHECKPOINT
        for outcome in (CORRECT, INCORRECT) if is_checkpoint else (None,):
            try:
                step = advance(graph, s, outcome, h)
            except ValueError as exc:
                report.errors.append(str(exc))
                return
            stack.append((step.next_state, checkpoints + ((s.node_id,) if is_checkpoint else ())))
    if stack:
        report.errors.append(f"more than {MAX_PATHS} paths: is the graph braided?")
    report.endings, report.departed_nodes = endings, sorted(departed)
    if len(sequences) != 1:
        report.errors.append(f"paths visit {len(sequences)} different checkpoint sequences")
    for sequence in sequences:
        items = [graph.item_at(node_id) or {} for node_id in sequence]
        if Counter((i["type"], i["skill"]) for i in items) != BLUEPRINT:
            report.errors.append(f"checkpoint sequence {sequence} breaks the 4/2/2/2 blueprint")
        if tuple(i["cefr"] for i in items) != CEFR_SEQUENCE:
            report.errors.append(f"CEFR order {[i['cefr'] for i in items]} != {CEFR_SEQUENCE}")
    for node_id in sorted(departed):
        flags = [v["when_flag"] for v in graph.node(node_id)["scene"].get("variants", ())]
        if TRAIN_DEPARTED not in flags:
            report.errors.append(f"node {node_id}: reachable after departure, no Plan-B variant")
        elif flags[0] != TRAIN_DEPARTED:
            report.warnings.append(f"node {node_id}: put the train_departed variant first")
    for key, count in endings.items():
        if count == 0:
            report.warnings.append(f"ending {key} is unreachable")
