"""Domain errors shared by every layer (pure Python: no FastAPI import).

Services raise DomainError; app/api/error_handlers.py turns it into the HTTP envelope
{"error": {"code", "message", "details"}} defined in docs/contracts/api-contract.md §2.
"""

from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    FORBIDDEN_ROLE = "FORBIDDEN_ROLE"
    NOT_FOUND = "NOT_FOUND"
    ATTEMPT_NOT_IN_PROGRESS = "ATTEMPT_NOT_IN_PROGRESS"
    NODE_OUT_OF_SEQUENCE = "NODE_OUT_OF_SEQUENCE"
    CHECKPOINT_LOCKED = "CHECKPOINT_LOCKED"
    MISSION_NOT_FINISHED = "MISSION_NOT_FINISHED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


HTTP_STATUS: dict[ErrorCode, int] = {
    ErrorCode.INVALID_CREDENTIALS: 401,
    ErrorCode.UNAUTHENTICATED: 401,
    ErrorCode.FORBIDDEN_ROLE: 403,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.ATTEMPT_NOT_IN_PROGRESS: 409,
    ErrorCode.NODE_OUT_OF_SEQUENCE: 409,
    ErrorCode.CHECKPOINT_LOCKED: 409,
    ErrorCode.MISSION_NOT_FINISHED: 409,
    ErrorCode.VALIDATION_ERROR: 422,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.INTERNAL_ERROR: 500,
}


class DomainError(Exception):
    """An expected failure with a stable code. The message is for developers, not end users."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details
        self.headers = headers

    @property
    def status_code(self) -> int:
        return HTTP_STATUS[self.code]


def error_body(code: ErrorCode, message: str, details: dict[str, Any] | None = None) -> dict:
    """The one and only error envelope."""
    return {"error": {"code": code.value, "message": message, "details": details}}
