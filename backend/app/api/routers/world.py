"""English World, Progress and the read-only teacher views (api-contract §5.6, §5.13-§5.15)."""

from fastapi import APIRouter

from app.api.deps import SessionDep, Student, TeacherOrAdmin
from app.schemas.world import (
    ClassesResponse,
    ClassProgressResponse,
    ProgressResponse,
    WorldResponse,
)
from app.services import world as world_service

router = APIRouter(prefix="/api", tags=["world"])


@router.get("/world")
def get_world(user: Student, session: SessionDep) -> WorldResponse:
    return world_service.get_world(session, user)


@router.get("/me/progress")
def get_progress(user: Student, session: SessionDep) -> ProgressResponse:
    return world_service.get_progress(session, user)


@router.get("/teacher/classes", tags=["teacher"])
def list_classes(user: TeacherOrAdmin, session: SessionDep) -> ClassesResponse:
    return world_service.list_classes(session, user)


@router.get("/teacher/classes/{class_id}/progress", tags=["teacher"])
def class_progress(class_id: str, user: TeacherOrAdmin, session: SessionDep) -> ClassProgressResponse:
    """That class's teacher or an admin; another teacher's class is 404 (not 403)."""
    return world_service.class_progress(session, user, class_id)
