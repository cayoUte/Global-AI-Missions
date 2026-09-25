"""Simulated replay DTOs (api-contract §5.16, stretch, DEMO_MODE only).

Outcomes, nodes, the clock and Maya's decisions only: no item id, option, prompt, chosen answer
or answer content (SHARED_CONTEXT §9.7). Built field by field in services/simulation.py.
"""

from typing import Literal

from pydantic import BaseModel

from app.schemas.common import Clock, EndingRef, MayaDecision, MayaMood, NodeKind

SimulationProfile = Literal["A1", "A2", "B1", "B2", "A2_weak_listening"]
SimulationOutcome = Literal["understood", "missed"]


class SimulationStep(BaseModel):
    seq: int
    node_id: str
    kind: NodeKind
    clock: Clock  # on arrival at the node
    outcome: SimulationOutcome | None  # checkpoints only
    maya_decision: MayaDecision  # as the StateView would have shown it on arrival
    maya_mood: MayaMood


class SimulationResponse(BaseModel):
    mission_id: str
    profile: SimulationProfile
    seed: int
    steps: list[SimulationStep]
    ending: EndingRef
    story_minutes_used: int
