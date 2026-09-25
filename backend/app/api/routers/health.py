from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["health"])


class HealthResponse(BaseModel):
    status: str


@router.get("/health")
def health() -> HealthResponse:
    """Liveness probe. Public, no database access."""
    return HealthResponse(status="ok")
