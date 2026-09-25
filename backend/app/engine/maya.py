"""Maya the planner: policy (quiet | hint | rescue), mood machine and line selection.

slack(s) = minutes_left - h(node): the story-minutes to spare if every remaining answer is right.
"""

from collections.abc import Mapping

from app.engine.graph import CHECKPOINT, CORRECT, INCORRECT, Edge, MissionGraph, resolve_scene
from app.engine.state import ENCOURAGING, PROUD, WORRIED, State

QUIET, HINT, RESCUE = "quiet", "hint", "rescue"
ON_ARRIVAL, AFTER_INCORRECT = "on_arrival", "after_incorrect"  # the two decision phases
HINT_BELOW_SLACK = 3  # SHARED_CONTEXT §5: slack < 3 -> hint


def slack(h: Mapping[str, int], s: State) -> int:
    return s.minutes_left - h[s.node_id]


def decide(graph: MissionGraph, h: Mapping[str, int], s: State, phase: str) -> str:
    """The policy. On arrival at a checkpoint: HINT when slack < 3, else QUIET.

    After an incorrect answer: RESCUE (at most once, before departure) when the normal detour
    would lose the train even with perfect play from there, and the rescue edge keeps it catchable.
    """
    if graph.kind(s.node_id) != CHECKPOINT:
        return QUIET
    if phase == ON_ARRIVAL:
        return HINT if slack(h, s) < HINT_BELOW_SLACK else QUIET
    if s.rescued or s.train_departed:
        return QUIET
    detour, rescue = incorrect_edges(graph, s.node_id)
    if detour is None or rescue is None:
        return QUIET

    def slack_via(edge: Edge) -> int:
        return s.minutes_left - edge.minutes - h[edge.target]

    return RESCUE if slack_via(detour) < 0 <= slack_via(rescue) else QUIET


def arrival_decision(
    graph: MissionGraph, h: Mapping[str, int], s: State, via_rescue: bool = False
) -> str:
    """The StateView decision: rescue on the node a rescue edge led to, else the arrival policy."""
    return RESCUE if via_rescue else decide(graph, h, s, ON_ARRIVAL)


def incorrect_edges(graph: MissionGraph, node_id: str) -> tuple[Edge | None, Edge | None]:
    edges = [e for e in graph.out_edges(node_id) if e.on == INCORRECT]
    detour = next((e for e in edges if not e.rescue), None)
    return detour, next((e for e in edges if e.rescue), None)


def next_mood(mood: str, outcome: str | None, slack_after: int) -> str:
    """Mood FSM, driven by the outcome and the slack after the move. Worry recovers gradually."""
    if outcome is None:
        return mood
    if outcome == INCORRECT:
        return WORRIED if slack_after < HINT_BELOW_SLACK else ENCOURAGING
    if slack_after < HINT_BELOW_SLACK or mood == WORRIED:
        return ENCOURAGING
    return PROUD


def mood_line(graph: MissionGraph, s: State) -> str | None:
    lines = graph.mood_lines.get(s.maya_mood, ())
    return lines[list(graph.nodes).index(s.node_id) % len(lines)] if lines else None


def reaction_line(graph: MissionGraph, s: State, outcome: str, decision: str) -> str | None:
    """Maya's reaction to an answer at checkpoint s: item-specific first, mood line fallback."""
    maya = graph.node(s.node_id).get("maya", {})
    if decision == RESCUE and maya.get("reaction_rescue"):
        return maya["reaction_rescue"]
    key = "reaction_ok" if outcome == CORRECT else "reaction_fail"
    return maya.get(key) or mood_line(graph, s)


def maya_line(graph: MissionGraph, s: State, decision: str) -> str | None:
    """The StateView line: the item's hint on HINT, else the scene's Maya line, else a mood line."""
    if decision == HINT:
        item = graph.item_at(s.node_id)
        if item is not None:
            return item["hint"]
    return resolve_scene(graph, s.node_id, s.flags).maya_line or mood_line(graph, s)
