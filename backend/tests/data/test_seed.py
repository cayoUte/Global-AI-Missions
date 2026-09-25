"""The seed: idempotent, versioned content, and a veteran history that matches the simulator."""

from sqlalchemy import func, select

from app.core import demo
from app.engine import SimulatedStudent, build_graph, compute_h, normalize_answer, run
from app.models import (
    AcceptedAnswer,
    Attempt,
    AttemptAnswer,
    AttemptStep,
    MissionVersion,
    Question,
    QuestionOption,
    User,
)
from app.repositories import attempts as attempts_repo
from app.repositories import missions as missions_repo
from app.repositories import users as users_repo
from app.services import report as report_service
from seed.run import run_seed

COUNTED = (
    User,
    MissionVersion,
    Question,
    QuestionOption,
    AcceptedAnswer,
    Attempt,
    AttemptStep,
    AttemptAnswer,
)


def _counts(session):
    return {m.__tablename__: session.scalar(select(func.count()).select_from(m)) for m in COUNTED}


def _veteran_attempts(session):
    leo = users_repo.get_user_by_email(session, demo.VETERAN.email)
    query = select(Attempt).where(Attempt.user_id == leo.id).order_by(Attempt.started_at)
    return leo, list(session.scalars(query))


def test_seed_is_idempotent(session, seed_summary):
    assert seed_summary.versions[0].source.is_fixture is False  # real content is present
    before = _counts(session)
    summary = run_seed(session)
    assert _counts(session) == before
    assert [v.created for v in summary.versions] == [False]
    assert summary.veteran_attempts == []


def test_veteran_answers_match_the_trace_and_the_check(session):
    leo, attempts = _veteran_attempts(session)
    assert [a.status for a in attempts] == ["submitted"] * 4
    version = missions_repo.get_active_mission_version(session, "the-last-train")
    docs = missions_repo.load_mission_content(session, version.id)
    graph = build_graph(docs.items_doc, docs.mission_doc)
    h = compute_h(graph)
    traces = sorted(
        (run(graph, h, SimulatedStudent(demo.VETERAN_PROFILE), s) for s in demo.VETERAN_SEEDS),
        key=lambda t: t.correct,
    )
    for attempt, trace in zip(attempts, traces, strict=True):
        answers = attempts_repo.list_attempt_answers(session, attempt.id)
        assert len(answers) == 10
        expected = {st.item_id: st.outcome == "correct" for st in trace.steps if st.item_id}
        assert {a.item_id: a.is_correct for a in answers} == expected
        assert attempt.correct_count == trace.correct
        assert attempt.ending_node_id == trace.steps[-1].node_id
        for row in answers:
            # The CHECK holds (exactly one of option / text) and is_correct agrees with the key.
            assert (row.selected_option_key is None) != (row.text_answer is None)
            key = missions_repo.get_answer_key(session, row.question_id)
            if row.text_answer is not None:
                assert (normalize_answer(row.text_answer) in key.accepted) == row.is_correct
            else:
                assert (row.selected_option_key == key.correct_option_key) == row.is_correct
        steps = attempts_repo.list_steps(session, attempt.id)
        assert steps[0].on_event == "start" and steps[-1].to_node_id == attempt.ending_node_id
        assert all(s.parent_step_id == p.id for p, s in zip(steps, steps[1:], strict=False))


def test_each_seeded_attempt_produces_a_report(session):
    leo, attempts = _veteran_attempts(session)
    for attempt in attempts:
        report = report_service.build_report(session, leo, attempt)
        assert report.result.correct + report.result.incorrect == 10
        assert report.result.score_pct == attempt.score_pct
        assert report.feedback_source.status == "fallback"
        assert report.diary[0].node_id == graph_start(session, attempt)
        assert len(report.missed) == report.result.incorrect
    submitted = [a.submitted_at for a in attempts]
    assert submitted == sorted(submitted)
    assert (attempts[-1].submitted_at - attempts[0].submitted_at).days <= 14


def graph_start(session, attempt):
    return missions_repo.get_mission_version(session, attempt.mission_version_id).content[
        "start_node"
    ]


def test_new_content_creates_a_new_version_and_old_attempts_keep_theirs(session):
    ana = users_repo.get_user_by_email(session, demo.NEW_STUDENT.email)
    old = missions_repo.get_active_mission_version(session, "the-last-train")
    attempt = attempts_repo.create_attempt(
        session,
        user_id=ana.id,
        mission_id="the-last-train",
        mission_version_id=old.id,
        start_node_id=old.content["start_node"],
        state={"minutes_left": 18, "flags": [], "rescued": False, "maya_mood": "curious"},
        maya_decision="quiet",
    )
    summary = run_seed(session, force_fixture=True)  # different content -> different hash
    new = missions_repo.get_active_mission_version(session, "the-last-train")
    assert summary.versions[0].created and new.version == old.version + 1
    assert session.get(Attempt, attempt.id).mission_version_id == old.id
    # The seed-owned veteran history moved to the active version.
    _, veteran = _veteran_attempts(session)
    assert {a.mission_version_id for a in veteran} == {new.id}
