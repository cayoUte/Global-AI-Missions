"""The search state s = (node_id, minutes_left, flags, rescued, maya_mood) and the story clock."""

from dataclasses import dataclass

from app.engine.graph import TRAIN_DEPARTED, MissionGraph

CURIOUS, ENCOURAGING, WORRIED, PROUD = "curious", "encouraging", "worried", "proud"


@dataclass(frozen=True)
class State:
    node_id: str
    minutes_left: int
    flags: frozenset[str] = frozenset()
    rescued: bool = False
    maya_mood: str = CURIOUS

    @property
    def train_departed(self) -> bool:
        return TRAIN_DEPARTED in self.flags


def initial_state(graph: MissionGraph) -> State:
    return State(node_id=graph.start_node, minutes_left=graph.minutes_available)


def clock_time(graph: MissionGraph, minutes_left: int) -> str:
    """Story clock "HH:MM" = start_clock + minutes used (it is not a real-time timer)."""
    hours, minutes = (int(part) for part in graph.start_clock.split(":"))
    total = hours * 60 + minutes + graph.minutes_available - minutes_left
    return f"{total // 60 % 24:02d}:{total % 60:02d}"


def clock(graph: MissionGraph, minutes_left: int) -> dict[str, object]:
    """The api-contract Clock: {time, minutes_left, train_departed, label}."""
    time = clock_time(graph, minutes_left)
    if minutes_left > 0:
        label = f"{time} · {minutes_left} min to departure"
    elif minutes_left == 0:
        label = f"{time} · Departing now"
    else:
        label = f"{time} · Train departed — Plan B"
    return {
        "time": time,
        "minutes_left": minutes_left,
        "train_departed": minutes_left < 0,
        "label": label,
    }
