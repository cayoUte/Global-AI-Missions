"""Simulated replay (api-contract §5.16, PRODUCT §5.8): one seeded run of the simulated student.

Read-only and deterministic: the engine's SimulatedStudent (P(correct | skill, cefr) per profile,
random.Random(seed)) plays the ACTIVE version of the mission, loaded through the same in-memory
cache the attempt services use. Nothing is persisted and the coach is never called.

The response is copied field by field from the engine Trace: node id, kind, clock, outcome
(understood | missed), Maya's decision and mood, the ending and the story minutes used. The
trace's item_id, and anything from the items (options, prompts, answer keys, hints,
explanations), never leave the server (SHARED_CONTEXT §9.7).
"""

from sqlalchemy.orm import Session

from app import engine
from app.core.config import get_settings
from app.core.errors import DomainError, ErrorCode
from app.engine import CORRECT, INCORRECT
from app.repositories import missions as missions_repo
from app.schemas.simulation import SimulationProfile, SimulationResponse, SimulationStep
from app.services import content
from app.services.state_view import clock_view, ending_ref

SEED_MIN, SEED_MAX = 0, 1_000_000  # a sane, documented range (422 outside it)
OUTCOME_LABEL = {CORRECT: "understood", INCORRECT: "missed"}


def ensure_demo_mode() -> None:
    """Outside demo mode the endpoint does not exist: 404 NOT_FOUND, like an unknown route."""
    if not get_settings().demo_mode:
        raise DomainError(ErrorCode.NOT_FOUND, "Not found.")


def simulate(
    session: Session, mission_id: str, profile: SimulationProfile, seed: int
) -> SimulationResponse:
    ensure_demo_mode()  # also enforced by the router dependency, before authentication
    mission = missions_repo.get_mission(session, mission_id)
    version = (
        missions_repo.get_active_mission_version(session, mission_id)
        if mission is not None and mission.playable
        else None
    )
    if version is None:
        raise DomainError(ErrorCode.NOT_FOUND, "Mission not found.")
    loaded = content.get_loaded_mission(session, version.id)
    graph = loaded.graph
    trace = engine.run(graph, loaded.h, engine.SimulatedStudent(profile), seed)
    ending = ending_ref(graph, trace.steps[-1].node_id)
    assert ending is not None  # engine.run stops only at an ending node
    return SimulationResponse(
        mission_id=mission_id,
        profile=profile,
        seed=seed,
        steps=[
            SimulationStep(
                seq=seq,
                node_id=step.node_id,
                kind=step.kind,
                clock=clock_view(graph, step.minutes_left),
                outcome=OUTCOME_LABEL[step.outcome] if step.outcome else None,
                maya_decision=step.maya_decision,
                maya_mood=step.maya_mood,
            )
            for seq, step in enumerate(trace.steps, start=1)
        ],
        ending=ending,
        story_minutes_used=trace.minutes_used,
    )
