"""Password hashing (argon2) and the session token (JWT HS256). Pure: no FastAPI, no database.

api-contract §3: claims sub (user UUID), role, iat, exp (60 minutes by default).
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import get_settings
from app.core.errors import DomainError, ErrorCode

JWT_ALGORITHM = "HS256"
SESSION_COOKIE = "gam_session"

_hasher = PasswordHasher()
# Verified against unknown emails so both login failures take a similar time (no user probing).
_DUMMY_HASH = _hasher.hash("not-a-real-password-used-only-for-timing")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    """True when the password matches. With no hash (unknown email) it still runs argon2."""
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerificationError, InvalidHashError):
        return False


def create_session_token(user_id: str, role: str, now: datetime | None = None) -> str:
    settings = get_settings()
    issued = now or datetime.now(UTC)
    claims = {
        "sub": user_id,
        "role": role,
        "iat": int(issued.timestamp()),
        "exp": int((issued + timedelta(minutes=settings.jwt_ttl_minutes)).timestamp()),
    }
    return jwt.encode(claims, settings.jwt_secret.get_secret_value(), algorithm=JWT_ALGORITHM)


def decode_session_token(token: str) -> dict[str, Any]:
    """The verified claims, or UNAUTHENTICATED for a malformed, tampered or expired token."""
    try:
        claims = jwt.decode(
            token,
            get_settings().jwt_secret.get_secret_value(),
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "role", "iat", "exp"]},
        )
    except jwt.PyJWTError as exc:
        raise DomainError(ErrorCode.UNAUTHENTICATED, "Invalid or expired session.") from exc
    return claims
