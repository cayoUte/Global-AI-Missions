"""The mission run (api-contract §5.7-§5.12). Thin: parse, call one service, return a schema."""

from fastapi import APIRouter, Response, status

from app.api.deps import SessionDep, Student
from app.schemas.attempts import AdvanceRequest, AnswerRequest, AnswerResponse
from app.schemas.report import Report
from app.schemas.state import StateView
from app.services import attempts as attempts_service
from app.services import report as report_service

router = APIRouter(prefix="/api", tags=["attempts"])


@router.post(
    "/missions/{mission_id}/attempts",
    status_code=status.HTTP_201_CREATED,
    responses={200: {"model": StateView, "description": "The open attempt already existed."}},
)
def start_attempt(
    mission_id: str, response: Response, user: Student, session: SessionDep
) -> StateView:
    """Start the mission, or return the OPEN attempt (200) so a finished run can be submitted."""
    result = attempts_service.start_attempt(session, user, mission_id)
    if not result.created:
        response.status_code = status.HTTP_200_OK
    return result.view


@router.get("/attempts/{attempt_id}")
def get_attempt(attempt_id: str, user: Student, session: SessionDep) -> StateView:
    """The current StateView: how a student resumes after a reload or a lost connection."""
    return attempts_service.get_state(session, user, attempt_id)


@router.post("/attempts/{attempt_id}/advance")
def advance(attempt_id: str, body: AdvanceRequest, user: Student, session: SessionDep) -> StateView:
    """CONTINUE on a narrative or consequence node; node_id must be the current node."""
    return attempts_service.advance(session, user, attempt_id, body.node_id)


@router.post("/attempts/{attempt_id}/answer")
def answer(
    attempt_id: str, body: AnswerRequest, user: Student, session: SessionDep
) -> AnswerResponse:
    """Lock the checkpoint's answer; the server grades it. No outcome field (F-01)."""
    return attempts_service.answer(session, user, attempt_id, body)


@router.post("/attempts/{attempt_id}/submit")
def submit(attempt_id: str, user: Student, session: SessionDep) -> Report:
    """Two-phase and idempotent: grade once, then Maya's feedback. Returns the Report."""
    return report_service.submit_and_report(session, user, attempt_id)


@router.get("/attempts/{attempt_id}/report")
def get_report(attempt_id: str, user: Student, session: SessionDep) -> Report:
    return report_service.get_report(session, user, attempt_id)
