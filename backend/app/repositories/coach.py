"""Maya's coach layer: feedback per attempt and memory per student."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Attempt, CoachFeedback, CoachMemory


def get_coach_memory(session: Session, user_id: uuid.UUID) -> CoachMemory | None:
    return session.get(CoachMemory, user_id)


def save_coach_memory(
    session: Session,
    user_id: uuid.UUID,
    *,
    sessions_count: int,
    notes: list[dict[str, Any]],
    next_greeting: str | None,
    now: datetime | None = None,
) -> CoachMemory:
    """Upsert the memory row. The service decides the values (e.g. keeps the last 5 notes)."""
    values = {
        "sessions_count": sessions_count,
        "notes": notes,
        "next_greeting": next_greeting,
        "updated_at": now or datetime.now(UTC),
    }
    session.execute(
        insert(CoachMemory)
        .values(user_id=user_id, **values)
        .on_conflict_do_update(index_elements=[CoachMemory.user_id], set_=values)
    )
    memory = session.get(CoachMemory, user_id, populate_existing=True)  # refresh any stale copy
    assert memory is not None
    return memory


def get_coach_feedback(session: Session, attempt_id: uuid.UUID) -> CoachFeedback | None:
    return session.scalar(select(CoachFeedback).where(CoachFeedback.attempt_id == attempt_id))


def get_latest_submitted_feedback(session: Session, user_id: uuid.UUID) -> CoachFeedback | None:
    """Feedback of the student's most recent submitted attempt (None if it has no row)."""
    latest = (
        select(Attempt.id)
        .where(Attempt.user_id == user_id, Attempt.status == "submitted")
        .order_by(Attempt.submitted_at.desc())
        .limit(1)
        .scalar_subquery()
    )
    return session.scalar(select(CoachFeedback).where(CoachFeedback.attempt_id == latest))


def save_coach_feedback(
    session: Session,
    *,
    attempt_id: uuid.UUID,
    provider: str,
    model: str | None,
    prompt_version: str,
    status: str,
    content: dict[str, Any],
    latency_ms: int | None,
) -> bool:
    """INSERT ... ON CONFLICT (attempt_id) DO NOTHING. True only if this call wrote the row:
    the caller updates coach memory only then, so sessions_count grows once per attempt."""
    written = session.scalar(
        insert(CoachFeedback)
        .values(
            attempt_id=attempt_id,
            provider=provider,
            model=model,
            prompt_version=prompt_version,
            status=status,
            content=content,
            latency_ms=latency_ms,
        )
        .on_conflict_do_nothing(index_elements=[CoachFeedback.attempt_id])
        .returning(CoachFeedback.id)
    )
    return written is not None
