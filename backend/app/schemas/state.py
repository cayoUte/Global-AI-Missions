"""StateView: the only shape the client sees during a mission (api-contract §6).

It never contains skill, cefr, hint, explanation, answer keys, edges, variants or flags (§9.A).
Built only by app.services.state_view.to_state_view().
"""

from typing import Literal

from pydantic import BaseModel

from app.schemas.common import (
    AttemptStatus,
    Clock,
    EndingRef,
    ItemType,
    MayaDecision,
    MayaMood,
    NodeKind,
)


class SceneLine(BaseModel):
    speaker: str
    text: str


class SceneView(BaseModel):
    location: str
    backdrop: str
    lines: list[SceneLine]


class AudioStimulus(BaseModel):
    kind: Literal["audio"]
    speaker: str | None
    audio_script: str
    rate: float
    text: None = None


class TextStimulus(BaseModel):
    kind: Literal["dialogue", "sign", "message", "notice", "timetable"]
    speaker: str | None
    text: str


Stimulus = AudioStimulus | TextStimulus


class OptionView(BaseModel):
    id: str
    text: str


class CheckpointView(BaseModel):
    item_id: str
    type: ItemType
    prompt: str
    stimulus: Stimulus | None
    options: list[OptionView] | None


class NodeView(BaseModel):
    id: str
    kind: NodeKind
    scene: SceneView
    checkpoint: CheckpointView | None
    ending: EndingRef | None


class MayaView(BaseModel):
    mood: MayaMood
    decision: MayaDecision
    line: str | None


class StateView(BaseModel):
    attempt_id: str
    mission_id: str
    mission_title: str
    status: AttemptStatus
    clock: Clock
    node: NodeView
    maya: MayaView

