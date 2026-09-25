"""to_state_view(): the ONE place that maps engine state + attempt data to what the client sees.

Every field is copied by name from a whitelist; no content dict is ever passed through whole.
That is what keeps answer keys, explanations, hints, skill/CEFR tags, edges, variants and flags
on the server (api-contract §6 and §9.A). Unit-tested in tests/services/test_state_view.py.
"""

from collections.abc import Mapping
from typing import Any

from app import engine
from app.engine import MissionGraph, State
from app.schemas.common import Clock, EndingRef
from app.schemas.state import (
    AudioStimulus,
    CheckpointView,
    MayaView,
    NodeView,
    OptionView,
    SceneLine,
    SceneView,
    StateView,
    Stimulus,
    TextStimulus,
)


def to_state_view(
    *,
    attempt_id: str,
    mission_id: str,
    mission_title: str,
    status: str,
    graph: MissionGraph,
    state: State,
    decision: str,
) -> StateView:
    """`decision` is Maya's arrival decision at the current node (quiet | hint | rescue)."""
    node = graph.node(state.node_id)
    scene = engine.resolve_scene(graph, state.node_id, state.flags)
    return StateView(
        attempt_id=attempt_id,
        mission_id=mission_id,
        mission_title=mission_title,
        status=status,
        clock=clock_view(graph, state.minutes_left),
        node=NodeView(
            id=state.node_id,
            kind=node["kind"],
            scene=SceneView(
                location=scene.location,
                backdrop=scene.backdrop,
                lines=[SceneLine(speaker=ln["speaker"], text=ln["text"]) for ln in scene.lines],
            ),
            checkpoint=_checkpoint_view(graph.item_at(state.node_id)),
            ending=ending_ref(graph, state.node_id),
        ),
        maya=MayaView(
            mood=state.maya_mood,
            decision=decision,
            line=engine.maya_line(graph, state, decision),
        ),
    )


def clock_view(graph: MissionGraph, minutes_left: int) -> Clock:
    return Clock(**engine.clock(graph, minutes_left))


def ending_ref(graph: MissionGraph, node_id: str) -> EndingRef | None:
    ending = graph.node(node_id).get("ending")
    return EndingRef(key=ending["key"], title=ending["title"]) if ending else None


def stimulus_view(stimulus: Mapping[str, Any] | None) -> Stimulus | None:
    if stimulus is None:
        return None
    if stimulus["kind"] == "audio":
        return AudioStimulus(
            kind="audio",
            speaker=stimulus.get("speaker"),
            audio_script=stimulus["audio_script"],
            rate=stimulus["rate"],
        )
    return TextStimulus(
        kind=stimulus["kind"], speaker=stimulus.get("speaker"), text=stimulus["text"]
    )


def _checkpoint_view(item: Mapping[str, Any] | None) -> CheckpointView | None:
    if item is None:
        return None
    options = item.get("options")
    return CheckpointView(
        item_id=item["id"],
        type=item["type"],
        prompt=item["prompt"],
        stimulus=stimulus_view(item.get("stimulus")),
        options=[OptionView(id=o["id"], text=o["text"]) for o in options] if options else None,
    )
