"""FastAPI dependencies: the per-request DB session, the current user and role checks."""

from collections.abc import Callable, Iterator
from typing import Annotated, Any

from fastapi import Cookie, Depends
from sqlalchemy.orm import Session

from app.core.errors import DomainError, ErrorCode
from app.core.security import SESSION_COOKIE
from app.repositories.db import get_sessionmaker
from app.services import auth as auth_service
from app.services import simulation as simulation_service


def get_session() -> Iterator[Session]:
    """One session per request. Services own commits; anything uncommitted is rolled back."""
    session = get_sessionmaker()()
    try:
        yield session
    finally:
        session.close()  # rolls back anything a service did not commit


SessionDep = Annotated[Session, Depends(get_session)]


def current_user(
    session: SessionDep,
    gam_session: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> Any:
    return auth_service.session_user(session, gam_session)


CurrentUser = Annotated[Any, Depends(current_user)]


def optional_user(
    session: SessionDep,
    gam_session: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> Any | None:
    """None when no cookie was sent (an anonymous visitor, CR-008). A cookie that is present but
    bad, tampered, expired or for a deleted user still raises UNAUTHENTICATED (401)."""
    if not gam_session:
        return None
    return auth_service.session_user(session, gam_session)


OptionalUser = Annotated[Any | None, Depends(optional_user)]


def require_role(*roles: str) -> Callable[..., Any]:
    """Dependency factory: 403 FORBIDDEN_ROLE unless the session user has one of `roles`."""

    def dependency(user: CurrentUser) -> Any:
        if user.role not in roles:
            raise DomainError(
                ErrorCode.FORBIDDEN_ROLE, "Role not allowed here.", {"required": list(roles)}
            )
        return user

    return dependency


Student = Annotated[Any, Depends(require_role("student"))]
TeacherOrAdmin = Annotated[Any, Depends(require_role("teacher", "admin"))]


def require_demo_mode() -> None:
    """Declared before the user dependency on demo-only routes, so with DEMO_MODE off the route
    is a 404 NOT_FOUND for everyone, authenticated or not (api-contract §5.16)."""
    simulation_service.ensure_demo_mode()


DemoMode = Annotated[None, Depends(require_demo_mode)]
