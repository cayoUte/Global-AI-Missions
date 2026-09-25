"""Attempt lifecycle: the attempt head, its steps (search nodes), answers and skill scores.

Repositories flush and never commit. Conflicts on the two race-prone unique indexes (one open
attempt, one answer per checkpoint) are caught inside a SAVEPOINT and reported as None, so the
caller's transaction stays usable and the service decides what the conflict means.
"""

import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    OPEN_STATUSES,
    Attempt,
    AttemptAnswer,
    AttemptSkillScore,
    AttemptStep,
    Question,
    QuestionOption,
)


@dataclass(frozen=True)
class AnswerRow:
    """One locked answer joined with its item. SERVER ONLY (carries is_correct): for grading at
    submit and for the report of a submitted attempt."""

    question_id: int
    item_id: str
    item_type: str
    skill: str
    cefr: str
    position: int
    is_correct: bool
    hint_shown: bool
    selected_option_key: str | None
    selected_option_text: str | None
    text_answer: str | None
    answered_at: datetime

    @property
    def your_answer(self) -> str:
        return self.selected_option_text or self.text_answer or ""


@dataclass(frozen=True)
class SkillScoreIn:
    skill: str
    correct: int
    total: int
    pct: int


def _now(now: datetime | None) -> datetime:
    return now or datetime.now(UTC)


# --- The attempt head ------------------------------------------------------------------------


def create_attempt(
    session: Session,
    *,
    user_id: uuid.UUID,
    mission_id: str,
    mission_version_id: int,
    start_node_id: str,
    state: dict[str, Any],
    maya_decision: str,
    now: datetime | None = None,
) -> Attempt | None:
    """Insert an in_progress attempt and its root step (seq 1, on_event "start").

    Returns None if the one-open-attempt index rejected it (a concurrent start won); the caller
    then loads the winner with get_open_attempt.
    """
    now = _now(now)
    attempt = Attempt(
        id=uuid.uuid4(),
        user_id=user_id,
        mission_id=mission_id,
        mission_version_id=mission_version_id,
        status="in_progress",
        current_node_id=start_node_id,
        state=state,
        started_at=now,
        last_activity_at=now,
    )
    root = AttemptStep(
        attempt_id=attempt.id,
        seq=1,
        parent_step_id=None,
        from_node_id=None,
        to_node_id=start_node_id,
        on_event="start",
        action=None,
        minutes_cost=0,
        path_cost=0,
        minutes_left_after=state["minutes_left"],
        maya_decision=maya_decision,
        state_after=state,
        created_at=now,
    )
    try:
        with session.begin_nested():
            session.add(attempt)
            session.flush()
            session.add(root)
            session.flush()
    except IntegrityError:
        return None
    return attempt


def get_open_attempt(session: Session, user_id: uuid.UUID, mission_id: str) -> Attempt | None:
    return session.scalar(
        select(Attempt).where(
            Attempt.user_id == user_id,
            Attempt.mission_id == mission_id,
            Attempt.status.in_(OPEN_STATUSES),
        )
    )


def list_open_attempts(session: Session, user_id: uuid.UUID) -> list[Attempt]:
    return list(
        session.scalars(
            select(Attempt)
            .where(Attempt.user_id == user_id, Attempt.status.in_(OPEN_STATUSES))
            .order_by(Attempt.last_activity_at.desc())
        )
    )


def get_owned_attempt(
    session: Session, attempt_id: uuid.UUID, user_id: uuid.UUID
) -> Attempt | None:
    """None when the attempt does not exist or belongs to someone else (both -> 404)."""
    return session.scalar(
        select(Attempt).where(Attempt.id == attempt_id, Attempt.user_id == user_id)
    )


def lock_attempt_for_update(
    session: Session, attempt_id: uuid.UUID, user_id: uuid.UUID
) -> Attempt | None:
    """SELECT ... FOR UPDATE on the owned attempt; refreshes any stale copy in the session."""
    return session.scalar(
        select(Attempt)
        .where(Attempt.id == attempt_id, Attempt.user_id == user_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )


def mark_attempt_completed(
    session: Session, attempt: Attempt, *, ending_node_id: str, now: datetime | None = None
) -> None:
    """An ending was reached: the run waits for Submit (still the open attempt, PD-028)."""
    attempt.status = "completed"
    attempt.ending_node_id = ending_node_id
    attempt.completed_at = _now(now)
    session.flush()


def finish_attempt(
    session: Session,
    attempt: Attempt,
    *,
    score_pct: int,
    correct_count: int,
    incorrect_count: int,
    suggested_cefr: str,
    now: datetime | None = None,
) -> None:
    """Write the graded totals and close the attempt (status submitted). Values come from the
    grading/leveling services; nothing is computed here."""
    attempt.status = "submitted"
    attempt.submitted_at = _now(now)
    attempt.score_pct = score_pct
    attempt.correct_count = correct_count
    attempt.incorrect_count = incorrect_count
    attempt.suggested_cefr = suggested_cefr
    session.flush()


def get_attempt_number(session: Session, attempt: Attempt) -> int:
    """1-based position among the student's attempts of that mission, by started_at."""
    earlier = session.scalar(
        select(func.count())
        .select_from(Attempt)
        .where(
            Attempt.user_id == attempt.user_id,
            Attempt.mission_id == attempt.mission_id,
            Attempt.started_at < attempt.started_at,
        )
    )
    return (earlier or 0) + 1


# --- Steps -----------------------------------------------------------------------------------


def get_last_step(session: Session, attempt_id: uuid.UUID) -> AttemptStep | None:
    return session.scalar(
        select(AttemptStep)
        .where(AttemptStep.attempt_id == attempt_id)
        .order_by(AttemptStep.seq.desc())
        .limit(1)
    )


def list_steps(session: Session, attempt_id: uuid.UUID) -> list[AttemptStep]:
    return list(
        session.scalars(
            select(AttemptStep)
            .where(AttemptStep.attempt_id == attempt_id)
            .order_by(AttemptStep.seq)
        )
    )


def append_step(
    session: Session,
    attempt: Attempt,
    *,
    from_node_id: str,
    to_node_id: str,
    on_event: str,
    action: dict[str, Any] | None,
    minutes_cost: int,
    minutes_left_after: int,
    maya_decision: str,
    state_after: dict[str, Any],
    now: datetime | None = None,
) -> AttemptStep:
    """Persist one transition as a child of the last step and move the attempt head to it.

    Call under lock_attempt_for_update: seq and parent come from the last step.
    """
    now = _now(now)
    parent = get_last_step(session, attempt.id)
    if parent is None:
        raise LookupError(f"attempt {attempt.id} has no root step")
    step = AttemptStep(
        attempt_id=attempt.id,
        seq=parent.seq + 1,
        parent_step_id=parent.id,
        from_node_id=from_node_id,
        to_node_id=to_node_id,
        on_event=on_event,
        action=action,
        minutes_cost=minutes_cost,
        path_cost=parent.path_cost + minutes_cost,
        minutes_left_after=minutes_left_after,
        maya_decision=maya_decision,
        state_after=state_after,
        created_at=now,
    )
    session.add(step)
    attempt.current_node_id = to_node_id
    attempt.state = state_after
    attempt.last_activity_at = now
    session.flush()
    return step


# --- Answers ---------------------------------------------------------------------------------


def answer_exists(session: Session, attempt_id: uuid.UUID, question_id: int) -> bool:
    return (
        session.scalar(
            select(AttemptAnswer.id).where(
                AttemptAnswer.attempt_id == attempt_id, AttemptAnswer.question_id == question_id
            )
        )
        is not None
    )


def save_answer(
    session: Session,
    *,
    attempt_id: uuid.UUID,
    question_id: int,
    selected_option_id: int | None = None,
    text_answer: str | None = None,
    is_correct: bool,
    hint_shown: bool,
    now: datetime | None = None,
) -> AttemptAnswer | None:
    """Lock the checkpoint's answer. None if an answer already exists (UNIQUE rejected it)."""
    answer = AttemptAnswer(
        attempt_id=attempt_id,
        question_id=question_id,
        selected_option_id=selected_option_id,
        text_answer=text_answer,
        is_correct=is_correct,
        hint_shown=hint_shown,
        answered_at=_now(now),
    )
    try:
        with session.begin_nested():
            session.add(answer)
            session.flush()
    except IntegrityError:
        return None
    return answer


def list_attempt_answers(session: Session, attempt_id: uuid.UUID) -> list[AnswerRow]:
    rows = session.execute(
        select(
            AttemptAnswer.question_id,
            Question.external_id,
            Question.type,
            Question.skill,
            Question.cefr,
            Question.position,
            AttemptAnswer.is_correct,
            AttemptAnswer.hint_shown,
            QuestionOption.option_key,
            QuestionOption.text,
            AttemptAnswer.text_answer,
            AttemptAnswer.answered_at,
        )
        .join(Question, Question.id == AttemptAnswer.question_id)
        .outerjoin(QuestionOption, QuestionOption.id == AttemptAnswer.selected_option_id)
        .where(AttemptAnswer.attempt_id == attempt_id)
        .order_by(Question.position)
    ).all()
    return [AnswerRow(*row) for row in rows]


# --- Skill scores ----------------------------------------------------------------------------


def save_skill_scores(
    session: Session, attempt_id: uuid.UUID, scores: Iterable[SkillScoreIn]
) -> None:
    session.add_all(
        AttemptSkillScore(
            attempt_id=attempt_id, skill=s.skill, correct=s.correct, total=s.total, pct=s.pct
        )
        for s in scores
    )
    session.flush()


def get_skill_scores(session: Session, attempt_id: uuid.UUID) -> list[AttemptSkillScore]:
    return list(
        session.scalars(
            select(AttemptSkillScore)
            .where(AttemptSkillScore.attempt_id == attempt_id)
            .order_by(AttemptSkillScore.skill)
        )
    )
