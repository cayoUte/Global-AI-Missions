"""Auth and public config (api-contract §5.2-§5.5)."""

from fastapi import APIRouter, Request, Response, status

from app.api.deps import OptionalUser, SessionDep
from app.core.config import get_settings
from app.core.security import SESSION_COOKIE
from app.schemas.auth import ConfigResponse, LoginRequest
from app.schemas.common import UserView
from app.services import auth as auth_service

router = APIRouter(prefix="/api", tags=["auth"])


@router.get("/config")
def get_config() -> ConfigResponse:
    """Public. Demo accounts and the demo password only when DEMO_MODE=true."""
    return auth_service.public_config()


@router.post("/auth/login")
def login(
    body: LoginRequest, request: Request, response: Response, session: SessionDep
) -> UserView:
    """Sets the httpOnly session cookie. Rate limited per (client IP, email)."""
    client_ip = request.client.host if request.client else "unknown"
    user, token = auth_service.login(session, body.email, body.password, client_ip)
    settings = get_settings()
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=settings.jwt_ttl_minutes * 60,
        path="/",
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
    )
    return user


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> Response:
    """Always 204; clears the cookie whether or not a session existed."""
    response.delete_cookie(
        SESSION_COOKIE, path="/", httponly=True, samesite="lax", secure=get_settings().cookie_secure
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/auth/me")
def me(user: OptionalUser) -> UserView | None:
    """200 UserView, or 200 null without a session cookie (CR-008: an anonymous probe is not an
    error, so the browser console stays clean). A bad or expired cookie is still 401."""
    return auth_service.user_view(user) if user is not None else None
