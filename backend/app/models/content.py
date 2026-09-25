"""Content as data: the catalog, versioned mission content and the assessment items.

The story graph (nodes, edges, scenes, Maya's lines) is versioned content: it is validated by the
engine at seed time and stored whole in mission_versions.content (JSONB). Everything that is
queried or constrained (items, options, answer keys) is relational.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

ITEM_TYPES = ("multiple_choice", "fill_blank", "comprehension", "vocabulary")


class Mission(Base):
    """One catalog entry (content/catalog.json). Upserted by id at seed time."""

    __tablename__ = "missions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # slug: the-last-train
    title: Mapped[str] = mapped_column(String(80))
    world_zone: Mapped[str] = mapped_column(String(64))
    skill_focus: Mapped[list[str]] = mapped_column(ARRAY(String(16)))  # skills.code values
    cefr_min: Mapped[str] = mapped_column(ForeignKey("cefr_levels.code"))
    cefr_max: Mapped[str] = mapped_column(ForeignKey("cefr_levels.code"))
    playable: Mapped[bool] = mapped_column(Boolean)
    unlock_rule: Mapped[dict[str, Any]]  # {kind, mission_id?, min_level?, hint} (PD-008)
    teaser: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(SmallInteger)


class MissionVersion(Base):
    """An immutable, validated snapshot of a mission's content. Attempts point to one version,
    so changing content never rewrites history: the seed creates a new version instead."""

    __tablename__ = "mission_versions"
    __table_args__ = (
        UniqueConstraint("mission_id", "version"),
        UniqueConstraint("mission_id", "content_hash"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    mission_id: Mapped[str] = mapped_column(ForeignKey("missions.id", ondelete="RESTRICT"))
    version: Mapped[int] = mapped_column(SmallInteger)  # 1, 2, … per mission
    content_hash: Mapped[str] = mapped_column(String(64))  # sha256 of items.json + mission.json
    content: Mapped[dict[str, Any]]  # the mission.json story graph, exactly as validated
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )  # the active version is the most recently published one


class Question(Base):
    """One assessment item of a mission version (items.json). Never sent with its key."""

    __tablename__ = "questions"
    __table_args__ = (
        UniqueConstraint("mission_version_id", "external_id"),
        # Also the index for "the items of a version in mission order".
        UniqueConstraint("mission_version_id", "position"),
        CheckConstraint(
            "type IN ('multiple_choice', 'fill_blank', 'comprehension', 'vocabulary')",
            name="type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    mission_version_id: Mapped[int] = mapped_column(
        ForeignKey("mission_versions.id", ondelete="CASCADE")
    )
    external_id: Mapped[str] = mapped_column(String(32))  # q01 … (the item id in content)
    type: Mapped[str] = mapped_column(String(20))
    skill: Mapped[str] = mapped_column(ForeignKey("skills.code"))
    cefr: Mapped[str] = mapped_column(ForeignKey("cefr_levels.code"))
    prompt: Mapped[str] = mapped_column(Text)
    stimulus: Mapped[dict[str, Any] | None]  # presentation content (items.schema.json)
    explanation: Mapped[str] = mapped_column(Text)
    hint: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(SmallInteger)  # 1-based order in items.json


class QuestionOption(Base):
    """An option of a choice item. is_correct is part of the answer key: selected only by
    repositories.missions.get_answer_key and load_mission_content (server side)."""

    __tablename__ = "question_options"
    __table_args__ = (
        UniqueConstraint("question_id", "option_key"),
        # At most one correct option per question (exactly one: the validator, before seeding).
        Index(
            "uq_question_options_one_correct",
            "question_id",
            unique=True,
            postgresql_where=text("is_correct"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"))
    option_key: Mapped[str] = mapped_column(String(8))  # a, b, c, d (the content's option id)
    text: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(SmallInteger)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)


class AcceptedAnswer(Base):
    """A fill_blank answer key entry, stored normalized and de-duplicated. is_primary marks the
    one the report displays (the first authored answer)."""

    __tablename__ = "accepted_answers"
    __table_args__ = (
        UniqueConstraint("question_id", "answer_normalized"),
        Index(
            "uq_accepted_answers_one_primary",
            "question_id",
            unique=True,
            postgresql_where=text("is_primary"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"))
    answer_normalized: Mapped[str] = mapped_column(String(80))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
