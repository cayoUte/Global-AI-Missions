"""Catalog, mission versions, items and - on a separate, explicit path - answer keys."""

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AcceptedAnswer,
    CefrLevel,
    Mission,
    MissionVersion,
    Question,
    QuestionOption,
)


@dataclass(frozen=True)
class MissionContent:
    """The two documents engine.build_graph(items_doc, mission_doc) expects.

    SERVER ONLY: items_doc carries the answer keys (the engine grades inside RESULT). Never
    serialize it to a client; build StateView/Report DTOs field by field instead.
    """

    items_doc: dict[str, Any]
    mission_doc: dict[str, Any]


@dataclass(frozen=True)
class AnswerKey:
    """The answer key of one item. For choice items: the correct option; for fill_blank: the
    normalized accepted answers, primary first (the primary is what the report displays)."""

    question_id: int
    item_type: str
    correct_option_id: int | None
    correct_option_key: str | None
    correct_option_text: str | None
    accepted: tuple[str, ...]

    @property
    def display_answer(self) -> str | None:
        """What the report shows as the correct answer."""
        return (
            self.correct_option_text if self.correct_option_key else next(iter(self.accepted), None)
        )


# --- Catalog ---------------------------------------------------------------------------------


def list_missions(session: Session) -> list[Mission]:
    return list(session.scalars(select(Mission).order_by(Mission.sort_order, Mission.id)))


def get_mission(session: Session, mission_id: str) -> Mission | None:
    return session.get(Mission, mission_id)


def get_cefr_ranks(session: Session) -> dict[str, int]:
    return {code: rank for code, rank in session.execute(select(CefrLevel.code, CefrLevel.rank))}


# --- Versions and content --------------------------------------------------------------------


def get_active_mission_version(session: Session, mission_id: str) -> MissionVersion | None:
    """The most recently published version (new attempts start on it)."""
    return session.scalar(
        select(MissionVersion)
        .where(MissionVersion.mission_id == mission_id)
        .order_by(MissionVersion.published_at.desc(), MissionVersion.version.desc())
        .limit(1)
    )


def get_mission_version(session: Session, version_id: int) -> MissionVersion | None:
    return session.get(MissionVersion, version_id)


def load_mission_content(session: Session, version_id: int) -> MissionContent:
    """Rebuild items.json (with keys) from the relational rows + the stored mission.json."""
    version = session.get(MissionVersion, version_id)
    if version is None:
        raise LookupError(f"mission version {version_id} does not exist")
    questions = list(
        session.scalars(
            select(Question)
            .where(Question.mission_version_id == version_id)
            .order_by(Question.position)
        )
    )
    ids = [q.id for q in questions]
    options: dict[int, list[QuestionOption]] = defaultdict(list)
    for option in session.scalars(
        select(QuestionOption)
        .where(QuestionOption.question_id.in_(ids))
        .order_by(QuestionOption.question_id, QuestionOption.position)
    ):
        options[option.question_id].append(option)
    accepted: dict[int, list[AcceptedAnswer]] = defaultdict(list)
    for answer in session.scalars(
        select(AcceptedAnswer)
        .where(AcceptedAnswer.question_id.in_(ids))
        .order_by(AcceptedAnswer.question_id, AcceptedAnswer.is_primary.desc(), AcceptedAnswer.id)
    ):
        accepted[answer.question_id].append(answer)

    items = []
    for q in questions:
        if q.type == "fill_blank":
            item_options = None
            answer_key: dict[str, Any] = {"accepted": [a.answer_normalized for a in accepted[q.id]]}
        else:
            item_options = [{"id": o.option_key, "text": o.text} for o in options[q.id]]
            correct = next(o.option_key for o in options[q.id] if o.is_correct)
            answer_key = {"correct_option_id": correct}
        items.append(
            {
                "id": q.external_id,
                "type": q.type,
                "skill": q.skill,
                "cefr": q.cefr,
                "prompt": q.prompt,
                "stimulus": q.stimulus,
                "options": item_options,
                "answer_key": answer_key,
                "explanation": q.explanation,
                "hint": q.hint,
            }
        )
    mission_doc = version.content
    return MissionContent({"mission_id": mission_doc["mission_id"], "items": items}, mission_doc)


# --- Items (no answer keys) ------------------------------------------------------------------


def get_question_id(session: Session, version_id: int, item_id: str) -> int | None:
    return session.scalar(
        select(Question.id).where(
            Question.mission_version_id == version_id, Question.external_id == item_id
        )
    )


def get_option_id(session: Session, question_id: int, option_key: str) -> int | None:
    return session.scalar(
        select(QuestionOption.id).where(
            QuestionOption.question_id == question_id, QuestionOption.option_key == option_key
        )
    )


# --- Answer keys: the only reader of is_correct / accepted_answers besides the loader above ---


def get_answer_key(session: Session, question_id: int) -> AnswerKey:
    item_type = session.scalar(select(Question.type).where(Question.id == question_id))
    if item_type is None:
        raise LookupError(f"question {question_id} does not exist")
    correct = session.execute(
        select(QuestionOption.id, QuestionOption.option_key, QuestionOption.text).where(
            QuestionOption.question_id == question_id, QuestionOption.is_correct
        )
    ).first()
    accepted = session.scalars(
        select(AcceptedAnswer.answer_normalized)
        .where(AcceptedAnswer.question_id == question_id)
        .order_by(AcceptedAnswer.is_primary.desc(), AcceptedAnswer.id)
    ).all()
    return AnswerKey(
        question_id=question_id,
        item_type=item_type,
        correct_option_id=correct.id if correct else None,
        correct_option_key=correct.option_key if correct else None,
        correct_option_text=correct.text if correct else None,
        accepted=tuple(accepted),
    )
