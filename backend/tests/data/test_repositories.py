"""Repository functions against the seeded database."""

import uuid

from app.core import demo
from app.engine import build_graph, validate
from app.repositories import attempts as attempts_repo
from app.repositories import coach as coach_repo
from app.repositories import missions as missions_repo
from app.repositories import progress as progress_repo
from app.repositories import users as users_repo

STATE = {"minutes_left": 18, "flags": [], "rescued": False, "maya_mood": "curious"}


def _user(session, account):
    return users_repo.get_user_by_email(session, account.email)


def test_catalog_and_reference_data(session):
    missions = missions_repo.list_missions(session)
    assert [m.id for m in missions][0] == "the-last-train"
    assert len(missions) == 5
    assert missions_repo.get_cefr_ranks(session) == {
        "PRE_A1": 0,
        "A1": 1,
        "A2": 2,
        "B1": 3,
        "B2": 4,
        "C1": 5,
    }


def test_load_mission_content_rebuilds_a_valid_graph(session):
    version = missions_repo.get_active_mission_version(session, "the-last-train")
    docs = missions_repo.load_mission_content(session, version.id)
    assert len(docs.items_doc["items"]) == 10
    assert validate(build_graph(docs.items_doc, docs.mission_doc)).ok


def test_answer_key_path(session):
    version = missions_repo.get_active_mission_version(session, "the-last-train")
    docs = missions_repo.load_mission_content(session, version.id)
    for item in docs.items_doc["items"]:
        question_id = missions_repo.get_question_id(session, version.id, item["id"])
        key = missions_repo.get_answer_key(session, question_id)
        if item["type"] == "fill_blank":
            assert key.correct_option_key is None
            assert key.accepted and key.display_answer == key.accepted[0]
            assert len(set(key.accepted)) == len(key.accepted)
        else:
            assert key.correct_option_key == item["answer_key"]["correct_option_id"]
            assert key.correct_option_id == missions_repo.get_option_id(
                session, question_id, key.correct_option_key
            )


def test_ownership_and_steps(session):
    ana, leo = _user(session, demo.NEW_STUDENT), _user(session, demo.VETERAN)
    version = missions_repo.get_active_mission_version(session, "the-last-train")
    attempt = attempts_repo.create_attempt(
        session,
        user_id=ana.id,
        mission_id="the-last-train",
        mission_version_id=version.id,
        start_node_id="intro",
        state=STATE,
        maya_decision="quiet",
    )
    assert attempts_repo.get_owned_attempt(session, attempt.id, ana.id) is attempt
    assert attempts_repo.get_owned_attempt(session, attempt.id, leo.id) is None
    assert attempts_repo.lock_attempt_for_update(session, attempt.id, leo.id) is None
    assert attempts_repo.lock_attempt_for_update(session, uuid.uuid4(), ana.id) is None

    after = {**STATE, "minutes_left": 17}
    step = attempts_repo.append_step(
        session,
        attempt,
        from_node_id="intro",
        to_node_id="n2",
        on_event="always",
        action={"kind": "continue"},
        minutes_cost=1,
        minutes_left_after=17,
        maya_decision="quiet",
        state_after=after,
    )
    root, second = attempts_repo.list_steps(session, attempt.id)
    assert (root.seq, root.on_event, root.parent_step_id) == (1, "start", None)
    assert (second.seq, second.parent_step_id, second.path_cost) == (2, root.id, 1)
    assert step is second
    assert (attempt.current_node_id, attempt.state) == ("n2", after)
    assert attempts_repo.get_attempt_number(session, attempt) == 1


def test_progress_of_the_veteran(session):
    leo = _user(session, demo.VETERAN)
    data = progress_repo.get_progress(session, leo.id)
    assert len(data.history) == 4
    assert [h.submitted_at for h in data.history] == sorted(
        (h.submitted_at for h in data.history), reverse=True
    )
    assert [p.attempt_id for p in data.level_history] == [
        h.attempt_id for h in reversed(data.history)
    ]
    assert sorted(h.attempt_number for h in data.history) == [1, 2, 3, 4]
    # PD-009 / F-05: pooled over the last 3 submitted attempts.
    assert data.profile.based_on_attempts == 3
    for sums in data.profile.skills:
        last3 = [s for h in data.history[:3] for s in h.skills if s.skill == sums.skill]
        assert sums.correct == sum(s.correct for s in last3)
        assert sums.total == sum(s.total for s in last3)
    assert len(data.notes) == 4 and data.open_attempt is None
    assert progress_repo.get_profile(session, _user(session, demo.NEW_STUDENT).id) is None


def test_teacher_scope(session):
    teacher = _user(session, demo.TEACHER)
    classes = progress_repo.list_teacher_classes(session, teacher.id)
    assert [(c.name, c.teacher_name, c.student_count) for c in classes] == [
        (demo.DEMO_CLASS_NAME, "Ms. Clarke", 2)
    ]
    class_id = classes[0].class_id
    view = progress_repo.list_class_progress(session, class_id, teacher.id)
    assert [s.display_name for s in view.students] == ["Ana", "Leo"]
    assert [s.missions_played for s in view.students] == [0, 4]
    assert progress_repo.list_class_progress(session, class_id, uuid.uuid4()) is None  # -> 404
    assert progress_repo.list_class_progress(session, class_id, None) is not None  # admin
    assert progress_repo.list_class_progress(session, uuid.uuid4(), None) is None


def test_coach_feedback_is_written_once(session):
    leo = _user(session, demo.VETERAN)
    latest = progress_repo.list_submitted_attempts(session, leo.id)[0]
    assert coach_repo.get_latest_submitted_feedback(session, leo.id).attempt_id == latest.attempt_id
    wrote = coach_repo.save_coach_feedback(
        session,
        attempt_id=latest.attempt_id,
        provider="mock",
        model=None,
        prompt_version="x",
        status="fallback",
        content={},
        latency_ms=0,
    )
    assert wrote is False  # the seed already stored it: ON CONFLICT DO NOTHING
    memory = coach_repo.save_coach_memory(
        session, leo.id, sessions_count=5, notes=[], next_greeting="Hi"
    )
    assert (memory.sessions_count, memory.next_greeting) == (5, "Hi")
