"""The migration matches the models, and the constraints enforce the invariants."""

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from alembic import command
from app.core import demo
from app.models import Attempt, QuestionOption
from app.repositories import attempts as attempts_repo
from app.repositories import missions as missions_repo
from app.repositories import users as users_repo

STATE = {"minutes_left": 18, "flags": [], "rescued": False, "maya_mood": "curious"}


def test_migration_matches_models(engine, alembic_cfg):
    command.check(alembic_cfg)  # raises if autogenerate would emit any operation


def _start(session, email=demo.NEW_STUDENT.email):
    user = users_repo.get_user_by_email(session, email)
    version = missions_repo.get_active_mission_version(session, "the-last-train")
    return attempts_repo.create_attempt(
        session,
        user_id=user.id,
        mission_id="the-last-train",
        mission_version_id=version.id,
        start_node_id=version.content["start_node"],
        state=STATE,
        maya_decision="quiet",
    )


def test_at_most_one_correct_option_per_question(session):
    option = session.scalar(select(QuestionOption).where(~QuestionOption.is_correct).limit(1))
    option.is_correct = True
    with pytest.raises(IntegrityError, match="uq_question_options_one_correct"):
        session.flush()


def test_one_open_attempt_per_student_and_mission(session):
    first = _start(session)
    assert first is not None
    assert _start(session) is None  # the partial unique index rejects a second open attempt
    assert attempts_repo.get_open_attempt(session, first.user_id, "the-last-train") == first
    # A completed (not yet submitted) run is still the open attempt.
    attempts_repo.mark_attempt_completed(session, first, ending_node_id="end_x")
    assert _start(session) is None
    attempts_repo.finish_attempt(
        session, first, score_pct=50, correct_count=5, incorrect_count=5, suggested_cefr="A2"
    )
    assert _start(session) is not None  # submitted attempts do not block a new run


def test_one_answer_per_question_and_exactly_one_answer_field(session):
    attempt = _start(session)
    version_id = attempt.mission_version_id
    question_id = missions_repo.get_question_id(session, version_id, "q01")
    option_id = session.scalar(
        select(QuestionOption.id).where(QuestionOption.question_id == question_id).limit(1)
    )
    saved = attempts_repo.save_answer(
        session,
        attempt_id=attempt.id,
        question_id=question_id,
        selected_option_id=option_id,
        is_correct=False,
        hint_shown=False,
    )
    assert saved is not None
    assert attempts_repo.answer_exists(session, attempt.id, question_id)
    again = attempts_repo.save_answer(
        session,
        attempt_id=attempt.id,
        question_id=question_id,
        text_answer="x",
        is_correct=True,
        hint_shown=False,
    )
    assert again is None  # locked on first write
    other = missions_repo.get_question_id(session, version_id, "q02")
    for option, text_answer in ((None, None), (option_id, "both")):
        insert = text(
            "INSERT INTO attempt_answers (attempt_id, question_id, selected_option_id,"
            " text_answer, is_correct, hint_shown) VALUES (:a, :q, :o, :t, false, false)"
        )
        params = {"a": attempt.id, "q": other, "o": option, "t": text_answer}
        with (
            pytest.raises(IntegrityError, match="ck_attempt_answers_one_answer"),
            session.begin_nested(),
        ):
            session.execute(insert, params)


def test_submitted_attempt_requires_its_result(session):
    attempt = _start(session)
    attempt.status = "submitted"
    with pytest.raises(IntegrityError, match="ck_attempts_"):
        session.flush()


def test_email_is_stored_lowercase(session):
    assert users_repo.get_user_by_email(session, "  NEW@GlobalAI.test ").display_name == "Ana"
    with pytest.raises(IntegrityError, match="ck_users_email_lowercase"):
        session.execute(
            text("UPDATE users SET email = upper(email) WHERE email = :e"),
            {"e": demo.NEW_STUDENT.email},
        )


def test_attempt_ids_are_uuids(session):
    attempt = _start(session)
    assert session.get(Attempt, attempt.id).id.version == 4
