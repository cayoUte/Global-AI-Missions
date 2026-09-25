"""MissionGraph: an immutable, indexed view of one mission's items.json + mission.json."""

import copy
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

# Vocabulary of the content format (docs/contracts/mission.schema.json).
CHECKPOINT, ENDING = "checkpoint", "ending"
ALWAYS, CORRECT, INCORRECT, ENDING_EDGE = "always", "correct", "incorrect", "ending"
TRAIN_DEPARTED = "train_departed"  # automatic flag, set by the engine when minutes_left < 0


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    on: str  # always | correct | incorrect | ending
    minutes: int
    rescue: bool = False
    set_flags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Scene:
    """A node's scene with variants resolved (the first variant whose flag is set wins)."""

    location: str
    backdrop: str
    lines: tuple[Mapping[str, str], ...]
    maya_line: str | None  # variant maya_line, else the node's maya.line / maya.intro
    diary: str  # variant diary, else node diary, else the first scene line, else location


@dataclass(frozen=True)
class MissionGraph:
    mission_id: str
    version: int
    title: str
    start_node: str
    start_clock: str
    minutes_available: int
    declared_flags: frozenset[str]
    mood_lines: Mapping[str, tuple[str, ...]]
    nodes: Mapping[str, Mapping[str, Any]]  # read-only by convention
    items: Mapping[str, Mapping[str, Any]]  # the only place answer keys live
    edges: tuple[Edge, ...]
    outgoing: Mapping[str, tuple[Edge, ...]]

    def node(self, node_id: str) -> Mapping[str, Any]:
        return self.nodes[node_id]

    def kind(self, node_id: str) -> str:
        return self.nodes[node_id]["kind"]

    def out_edges(self, node_id: str) -> tuple[Edge, ...]:
        return self.outgoing.get(node_id, ())

    def item_at(self, node_id: str) -> Mapping[str, Any] | None:
        item_id = self.nodes[node_id].get("item_id")
        return self.items[item_id] if item_id else None


def build_graph(items_doc: Mapping[str, Any], mission_doc: Mapping[str, Any]) -> MissionGraph:
    """Index the two documents. Raises ValueError on duplicate ids or dangling references."""
    mission, items_list = copy.deepcopy(dict(mission_doc)), copy.deepcopy(items_doc["items"])
    nodes = {n["id"]: n for n in mission["nodes"]}
    items = {i["id"]: i for i in items_list}
    problems = []
    if len(nodes) != len(mission["nodes"]):
        problems.append("duplicate node ids")
    if len(items) != len(items_list):
        problems.append("duplicate item ids")
    if mission["start_node"] not in nodes:
        problems.append(f"start_node '{mission['start_node']}' does not exist")
    if items_doc["mission_id"] != mission["mission_id"]:
        problems.append("items.json and mission.json disagree on mission_id")
    edges = tuple(
        Edge(
            e["from"],
            e["to"],
            e["on"],
            e["minutes"],
            e.get("rescue", False),
            tuple(e.get("effects", {}).get("set_flags", ())),
        )
        for e in mission["edges"]
    )
    for e in edges:
        if e.source not in nodes or e.target not in nodes:
            problems.append(f"edge {e.source} -> {e.target} references an unknown node")
    for n in nodes.values():
        if n.get("item_id") and n["item_id"] not in items:
            problems.append(f"node '{n['id']}' references unknown item '{n['item_id']}'")
    if problems:
        raise ValueError("; ".join(problems))
    outgoing: dict[str, list[Edge]] = {}
    for e in edges:
        outgoing.setdefault(e.source, []).append(e)
    return MissionGraph(
        mission_id=mission["mission_id"],
        version=mission["version"],
        title=mission["title"],
        start_node=mission["start_node"],
        start_clock=mission["setting"]["start_clock"],
        minutes_available=mission["setting"]["minutes_available"],
        declared_flags=frozenset(f["id"] for f in mission["flags"]),
        mood_lines=MappingProxyType(
            {m: tuple(v) for m, v in mission["companion"]["mood_lines"].items()}
        ),
        nodes=MappingProxyType(nodes),
        items=MappingProxyType(items),
        edges=edges,
        outgoing=MappingProxyType({k: tuple(v) for k, v in outgoing.items()}),
    )


def resolve_scene(graph: MissionGraph, node_id: str, flags: frozenset[str]) -> Scene:
    node = graph.node(node_id)
    scene, maya = node["scene"], node.get("maya", {})
    variant = next((v for v in scene.get("variants", ()) if v["when_flag"] in flags), {})
    lines = tuple(variant.get("lines", scene["lines"]))
    first_line = lines[0]["text"] if lines else scene["location"]
    return Scene(
        location=variant.get("location", scene["location"]),
        backdrop=variant.get("backdrop", scene["backdrop"]),
        lines=lines,
        maya_line=variant.get("maya_line", maya.get("intro", maya.get("line"))),
        diary=variant.get("diary", node.get("diary", first_line)),
    )
