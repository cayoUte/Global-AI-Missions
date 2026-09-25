"""Attempts: one run of a mission, its steps (the persisted search nodes), answers and scores."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAt

ATTEMPT_STATUSES = ("in_progress", "completed", "submitted")
OPEN_STATUSES = ("in_progress", "completed")
STEP_EVENTS = ("start", "always", "correct", "incorrect", "ending")
MAYA_DECISIONS = ("quiet", "hint", "rescue")


class Attempt(Base):
    """The head of an attempt: where the student is now and, once submitted, the result.

    current_node_id + state = the engine State (state holds minutes_left, flags, rescued,
    maya_mood). Totals and suggested_cefr are written once, by the grading transaction.
    """

    __tablename__ = "attempts"
    __table_args__ = (
        CheckConstraint("status IN ('in_progress', 'completed', 'submitted')", name="status"),
        CheckConstraint(
            "status = 'in_progress' OR (completed_at IS NOT NULL AND ending_node_id IS NOT NULL)",
            name="finished_has_ending",
        ),
        CheckConstraint(
            "status <> 'submitted' OR (submitted_at IS NOT NULL AND score_pct IS NOT NULL"
            " AND correct_count IS NOT NULL AND incorrect_count IS NOT NULL"
            " AND suggested_cefr IS NOT NULL)",
            name="submitted_has_result",
        ),
        CheckConstraint("score_pct BETWEEN 0 AND 100", name="score_pct_range"),
        # One open attempt (in_progress or completed-not-submitted) per student and mission.
        Index(
            "uq_attempts_one_open",
            "user_id",
            "mission_id",
            unique=True,
            postgresql_where=text("status IN ('in_progress', 'completed')"),
        ),
        # History, profile (last 3 submitted) and the World: newest submitted first.
        Index("ix_attempts_user_id_submitted_at", "user_id", text("submitted_at DESC")),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    mission_id: Mapped[str] = mapped_column(ForeignKey("missions.id", ondelete="RESTRICT"))
    mission_version_id: Mapped[int] = mapped_column(
        ForeignKey("mission_versions.id", ondelete="RESTRICT")
    )
    status: Mapped[str] = mapped_column(String(16), default="in_progress")
    current_node_id: Mapped[str] = mapped_column(String(64))  # the graph's external node id
    state: Mapped[dict[str, Any]]  # {minutes_left, flags, rescued, maya_mood}
    started_at: Mapped[CreatedAt]
    last_activity_at: Mapped[CreatedAt]
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    score_pct: Mapped[int | None] = mapped_column(SmallInteger)
    correct_count: Mapped[int | None] = mapped_column(SmallInteger)
    incorrect_count: Mapped[int | None] = mapped_column(SmallInteger)
    suggested_cefr: Mapped[str | None] = mapped_column(ForeignKey("cefr_levels.code"))
    ending_node_id: Mapped[str | None] = mapped_column(String(64))


class AttemptStep(Base):
    """One persisted transition = one search Node: (state, parent, action, path_cost).

    seq 1 is the root (on_event "start", no parent, no from_node). Following parent_step_id back
    from the ending rebuilds the solution path: that is the Diary. maya_decision is Maya's
    decision on arrival at to_node_id, as the StateView showed it.
    """

    __tablename__ = "attempt_steps"
    __table_args__ = (
        UniqueConstraint("attempt_id", "seq"),  # also the (attempt_id, seq) index
        CheckConstraint(
            "on_event IN ('start', 'always', 'correct', 'incorrect', 'ending')", name="on_event"
        ),
        CheckConstraint("maya_decision IN ('quiet', 'hint', 'rescue')", name="maya_decision"),
        CheckConstraint(
            "(seq = 1 AND on_event = 'start' AND parent_step_id IS NULL AND from_node_id IS NULL)"
            " OR (seq > 1 AND on_event <> 'start' AND parent_step_id IS NOT NULL"
            " AND from_node_id IS NOT NULL)",
            name="root_or_child",
        ),
        CheckConstraint("minutes_cost >= 0", name="minutes_cost_positive"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    attempt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("attempts.id", ondelete="CASCADE"))
    seq: Mapped[int] = mapped_column(SmallInteger)
    parent_step_id: Mapped[int | None] = mapped_column(
        ForeignKey("attempt_steps.id", ondelete="CASCADE")
    )
    from_node_id: Mapped[str | None] = mapped_column(String(64))
    to_node_id: Mapped[str] = mapped_column(String(64))
    on_event: Mapped[str] = mapped_column(String(16))
    action: Mapped[dict[str, Any] | None]  # null | {"kind": "continue"} | {"kind": "answer", ...}
    minutes_cost: Mapped[int] = mapped_column(SmallInteger)  # this edge's story-minutes
    path_cost: Mapped[int] = mapped_column(SmallInteger)  # story-minutes used since the start
    minutes_left_after: Mapped[int] = mapped_column(SmallInteger)
    maya_decision: Mapped[str] = mapped_column(String(8))
    state_after: Mapped[dict[str, Any]]  # engine state on arrival (shape of attempts.state)
    created_at: Mapped[CreatedAt]


class AttemptAnswer(Base):
    """The answer locked at a checkpoint. Exactly one of selected_option_id / text_answer."""

    __tablename__ = "attempt_answers"
    __table_args__ = (
        # One answer per checkpoint; also serves the attempt_answers(attempt_id) lookups.
        UniqueConstraint("attempt_id", "question_id"),
        CheckConstraint("num_nonnulls(selected_option_id, text_answer) = 1", name="one_answer"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    attempt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("attempts.id", ondelete="CASCADE"))
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="RESTRICT"))
    selected_option_id: Mapped[int | None] = mapped_column(
        ForeignKey("question_options.id", ondelete="RESTRICT")
    )
    text_answer: Mapped[str | None] = mapped_column(String(200))  # raw trimmed text (report)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    hint_shown: Mapped[bool] = mapped_column(Boolean, default=False)
    answered_at: Mapped[CreatedAt]


class AttemptSkillScore(Base):
    """Per-skill result of a submitted attempt, written by the grading transaction."""

    __tablename__ = "attempt_skill_scores"
    __table_args__ = (
        CheckConstraint("total > 0 AND correct BETWEEN 0 AND total", name="counts"),
        CheckConstraint("pct BETWEEN 0 AND 100", name="pct_range"),
    )

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("attempts.id", ondelete="CASCADE"), primary_key=True
    )
    skill: Mapped[str] = mapped_column(ForeignKey("skills.code"), primary_key=True)
    correct: Mapped[int] = mapped_column(SmallInteger)
    total: Mapped[int] = mapped_column(SmallInteger)
    pct: Mapped[int] = mapped_column(SmallInteger)
