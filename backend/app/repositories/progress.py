"""Read models for the English World, Progress and the teacher view.

Everything comes back as raw facts and sums; percentages, labels and rules (rounding, CEFR
display labels, unlocks) are the services' job.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Attempt,
    AttemptSkillScore,
    ClassMember,
    CoachMemory,
    Mission,
    SchoolClass,
    User,
)
from app.repositories.attempts import list_open_attempts


@dataclass(frozen=True)
class SkillSums:
    skill: str
    correct: int
    total: int


@dataclass(frozen=True)
class ProfileSums:
    """PD-009 / F-05: pooled sums per skill over the last N submitted attempts (all missions)."""

    based_on_attempts: int
    skills: list[SkillSums]  # ordered by skill code (grammar, listening, reading, …)


@dataclass(frozen=True)
class HistoryRow:
    attempt_id: uuid.UUID
    attempt_number: int  # 1-based among the student's attempts of that mission, by started_at
    mission_id: str
    mission_title: str
    mission_version_id: int  # resolve ending_node_id -> EndingRef through the version's graph
    started_at: datetime
    submitted_at: datetime
    ending_node_id: str
    suggested_cefr: str
    score_pct: int
    correct: int
    incorrect: int
    skills: list[SkillSums]


@dataclass(frozen=True)
class LevelPoint:
    attempt_id: uuid.UUID
    submitted_at: datetime
    suggested_cefr: str


@dataclass(frozen=True)
class ProgressData:
    profile: ProfileSums | None
    history: list[HistoryRow]  # newest first
    level_history: list[LevelPoint]  # oldest first
    notes: list[dict[str, Any]]  # coach_memory.notes: ≤ 5 {text, created_at}, newest first
    open_attempt: Attempt | None  # the most recently active open attempt


@dataclass(frozen=True)
class ClassSummary:
    class_id: uuid.UUID
    name: str
    teacher_name: str
    student_count: int


@dataclass(frozen=True)
class StudentProgress:
    display_name: str
    missions_played: int  # submitted attempts, all missions
    latest: HistoryRow | None  # most recent submitted attempt
    profile: ProfileSums | None
    last_activity_at: datetime | None


@dataclass(frozen=True)
class ClassProgress:
    class_id: uuid.UUID
    name: str
    students: list[StudentProgress]  # by display_name


# --- Profile and history ---------------------------------------------------------------------


def get_profile(session: Session, user_id: uuid.UUID, last_n: int = 3) -> ProfileSums | None:
    """One query: Σcorrect and Σtotal per skill over the student's last N submitted attempts."""
    last = (
        select(Attempt.id)
        .where(Attempt.user_id == user_id, Attempt.status == "submitted")
        .order_by(Attempt.submitted_at.desc())
        .limit(last_n)
        .cte("last_submitted")
    )
    rows = session.execute(
        select(
            AttemptSkillScore.skill,
            func.sum(AttemptSkillScore.correct),
            func.sum(AttemptSkillScore.total),
            select(func.count()).select_from(last).scalar_subquery(),
        )
        .join(last, last.c.id == AttemptSkillScore.attempt_id)
        .group_by(AttemptSkillScore.skill)
        .order_by(AttemptSkillScore.skill)
    ).all()
    if not rows:
        return None
    return ProfileSums(
        based_on_attempts=int(rows[0][3]),
        skills=[SkillSums(skill, int(correct), int(total)) for skill, correct, total, _ in rows],
    )


def list_submitted_attempts(session: Session, user_id: uuid.UUID) -> list[HistoryRow]:
    """The student's submitted attempts, newest first, each with its per-skill scores."""
    numbered = (
        select(
            Attempt.id,
            func.row_number()
            .over(partition_by=Attempt.mission_id, order_by=(Attempt.started_at, Attempt.id))
            .label("attempt_number"),
        )
        .where(Attempt.user_id == user_id)
        .subquery()
    )
    attempts = session.execute(
        select(Attempt, numbered.c.attempt_number, Mission.title)
        .join(numbered, numbered.c.id == Attempt.id)
        .join(Mission, Mission.id == Attempt.mission_id)
        .where(Attempt.user_id == user_id, Attempt.status == "submitted")
        .order_by(Attempt.submitted_at.desc())
    ).all()
    scores: dict[uuid.UUID, list[SkillSums]] = {a.id: [] for a, _, _ in attempts}
    if scores:
        for row in session.scalars(
            select(AttemptSkillScore)
            .where(AttemptSkillScore.attempt_id.in_(scores))
            .order_by(AttemptSkillScore.skill)
        ):
            scores[row.attempt_id].append(SkillSums(row.skill, row.correct, row.total))
    return [
        HistoryRow(
            attempt_id=a.id,
            attempt_number=int(number),
            mission_id=a.mission_id,
            mission_title=title,
            mission_version_id=a.mission_version_id,
            started_at=a.started_at,
            submitted_at=a.submitted_at,  # submitted -> never null
            ending_node_id=a.ending_node_id,
            suggested_cefr=a.suggested_cefr,
            score_pct=a.score_pct,
            correct=a.correct_count,
            incorrect=a.incorrect_count,
            skills=scores[a.id],
        )
        for a, number, title in attempts
    ]


def get_progress(session: Session, user_id: uuid.UUID) -> ProgressData:
    history = list_submitted_attempts(session, user_id)
    memory = session.get(CoachMemory, user_id)
    open_attempts = list_open_attempts(session, user_id)
    return ProgressData(
        profile=get_profile(session, user_id),
        history=history,
        level_history=[
            LevelPoint(h.attempt_id, h.submitted_at, h.suggested_cefr) for h in reversed(history)
        ],
        notes=list(memory.notes) if memory else [],
        open_attempt=open_attempts[0] if open_attempts else None,
    )


# --- Teacher view ----------------------------------------------------------------------------


def list_teacher_classes(session: Session, teacher_id: uuid.UUID | None) -> list[ClassSummary]:
    """Classes taught by teacher_id; every class when teacher_id is None (admin)."""
    count = (
        select(func.count())
        .select_from(ClassMember)
        .where(ClassMember.class_id == SchoolClass.id)
        .scalar_subquery()
    )
    query = (
        select(SchoolClass.id, SchoolClass.name, User.display_name, count)
        .join(User, User.id == SchoolClass.teacher_id)
        .order_by(SchoolClass.name, SchoolClass.id)
    )
    if teacher_id is not None:
        query = query.where(SchoolClass.teacher_id == teacher_id)
    return [ClassSummary(*row) for row in session.execute(query).all()]


def list_class_progress(
    session: Session, class_id: uuid.UUID, teacher_id: uuid.UUID | None
) -> ClassProgress | None:
    """A class's students with aggregates only. None if the class does not exist or is not
    taught by teacher_id (teacher_id None = admin: any class)."""
    school_class = session.get(SchoolClass, class_id)
    if school_class is None or (teacher_id is not None and school_class.teacher_id != teacher_id):
        return None
    members = session.execute(
        select(User.id, User.display_name)
        .join(ClassMember, ClassMember.user_id == User.id)
        .where(ClassMember.class_id == class_id)
        .order_by(User.display_name, User.id)
    ).all()
    students = []
    for user_id, display_name in members:
        history = list_submitted_attempts(session, user_id)
        last_activity = session.scalar(
            select(func.max(Attempt.last_activity_at)).where(Attempt.user_id == user_id)
        )
        students.append(
            StudentProgress(
                display_name=display_name,
                missions_played=len(history),
                latest=history[0] if history else None,
                profile=get_profile(session, user_id),
                last_activity_at=last_activity,
            )
        )
    return ClassProgress(class_id=school_class.id, name=school_class.name, students=students)
