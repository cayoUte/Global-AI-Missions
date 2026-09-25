"""Authentication use cases: login (with the rate limit), the session user, the public config."""

import uuid

from sqlalchemy.orm import Session

from app.core import demo
from app.core.config import get_settings
from app.core.errors import DomainError, ErrorCode
from app.core.rate_limit import login_limiter
from app.core.security import create_session_token, decode_session_token, verify_password
from app.repositories import users as users_repo
from app.schemas.auth import ConfigResponse, DemoAccount
from app.schemas.common import UserView


def user_view(user: object) -> UserView:
    return UserView(
        id=str(user.id),  # type: ignore[attr-defined]
        email=user.email,  # type: ignore[attr-defined]
        display_name=user.display_name,  # type: ignore[attr-defined]
        role=user.role,  # type: ignore[attr-defined]
    )


def login(session: Session, email: str, password: str, client_ip: str) -> tuple[UserView, str]:
    """(UserView, session token). Same error for an unknown email and a wrong password; argon2
    runs in both cases so their timing is similar."""
    login_limiter.hit(f"{client_ip}|{email}")
    user = users_repo.get_user_by_email(session, email)
    if not verify_password(user.password_hash if user else None, password) or user is None:
        raise DomainError(ErrorCode.INVALID_CREDENTIALS, "Invalid email or password.")
    return user_view(user), create_session_token(str(user.id), user.role)


def session_user(session: Session, token: str | None) -> object:
    """The user behind a session cookie, loaded fresh on every request (role changes and deleted
    users take effect immediately). Missing, bad or expired cookie -> UNAUTHENTICATED."""
    if not token:
        raise DomainError(ErrorCode.UNAUTHENTICATED, "Not signed in.")
    claims = decode_session_token(token)
    try:
        user_id = uuid.UUID(str(claims["sub"]))
    except ValueError as exc:
        raise DomainError(ErrorCode.UNAUTHENTICATED, "Invalid session.") from exc
    user = users_repo.get_user_by_id(session, user_id)
    if user is None:
        raise DomainError(ErrorCode.UNAUTHENTICATED, "Invalid session.")
    return user


def public_config() -> ConfigResponse:
    """Demo accounts and the shared demo password only when DEMO_MODE=true (PD-018)."""
    if not get_settings().demo_mode:
        return ConfigResponse(demo_mode=False, demo_accounts=None, demo_password=None)
    return ConfigResponse(
        demo_mode=True,
        demo_accounts=[
            DemoAccount(
                email=a.email, display_name=a.display_name, role=a.role, purpose=a.purpose
            )
            for a in demo.DEMO_ACCOUNTS
        ],
        demo_password=demo.DEMO_PASSWORD,
    )
