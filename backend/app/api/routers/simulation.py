"""Simulated replay (api-contract §5.16): stretch, any authenticated role, DEMO_MODE only."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DemoMode, SessionDep
from app.schemas.simulation import SimulationProfile, SimulationResponse
from app.services import simulation as simulation_service
from app.services.simulation import SEED_MAX, SEED_MIN

router = APIRouter(prefix="/api", tags=["demo"])


@router.get("/missions/{mission_id}/simulate")
def simulate(
    mission_id: str,
    _demo: DemoMode,  # first: with DEMO_MODE off the route is a 404, before authentication
    user: CurrentUser,
    session: SessionDep,
    profile: SimulationProfile,
    seed: Annotated[int, Query(ge=SEED_MIN, le=SEED_MAX)] = 1,
) -> SimulationResponse:
    """One seeded run of the simulated student: outcomes, nodes, clock and Maya's decisions,
    never options or answer content. Deterministic; nothing is persisted."""
    return simulation_service.simulate(session, mission_id, profile, seed)
