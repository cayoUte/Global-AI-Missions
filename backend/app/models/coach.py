"""Maya's coach layer: the post-mission feedback (one per attempt) and her memory of a student."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAt


class CoachFeedback(Base):
    """The validated coach output for one submitted attempt (or its deterministic fallback)."""

    __tablename__ = "coach_feedback"
    __table_args__ = (CheckConstraint("status IN ('ready', 'fallback')", name="status"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("attempts.id", ondelete="CASCADE"), unique=True
    )
    provider: Mapped[str] = mapped_column(String(32))  # mock | anthropic | …
    model: Mapped[str | None] = mapped_column(String(64))
    prompt_version: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16))
    # {summary, strength, challenge, recommendation, next_mission_id, memory_note, next_greeting}
    content: Mapped[dict[str, Any]]
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[CreatedAt]


class CoachMemory(Base):
    """What Maya remembers between sessions. notes = the last 5 {text, created_at}, newest first."""

    __tablename__ = "coach_memory"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    sessions_count: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[list[Any]]
    next_greeting: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
