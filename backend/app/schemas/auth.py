"""Auth and public config DTOs (api-contract §5.2–§5.5)."""

import re

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import RequestModel, Role

_EMAIL_SHAPE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class LoginRequest(RequestModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        """Trimmed and lowercased; only the shape is checked (the server is the authority)."""
        value = value.strip().lower()
        if not _EMAIL_SHAPE.match(value):
            raise ValueError("Enter a valid email address.")
        return value


class DemoAccount(BaseModel):
    email: str
    display_name: str
    role: Role
    purpose: str


class ConfigResponse(BaseModel):
    demo_mode: bool
    demo_accounts: list[DemoAccount] | None
    demo_password: str | None
