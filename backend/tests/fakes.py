"""An in-memory stand-in for app.repositories, used when PostgreSQL is not reachable.

It implements the published repository signatures (app/repositories/__init__.py) over plain
objects, returning the repositories' own dataclasses where they define one. install() patches
the functions onto the real repository modules, so services and routers run unchanged.
It is a test double, not a second implementation: SQL-level behaviour (row locks, partial unique
indexes, ON CONFLICT) is simulated only as far as the services depend on it.
"""

import copy
import itertools
import json
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace as NS

from app.core.security import hash_password
from app.repositories import attempts as attempts_repo
from app.repositories import coach as coach_repo
from app.repositories import missions as missions_repo
from app.repositories import progress as progress_repo
from app.repositories import users as users_repo
from app.repositories.attempts import AnswerRow
from app.repositories.missions import AnswerKey, MissionContent
from app.repositories.progress import (
    ClassProgress,
    ClassSummary,
    HistoryRow,
    LevelPoint,
    ProfileSums,
    ProgressData,
    SkillSums,
    StudentProgress,
)

CONTENT = Path(__file__).resolve().parents[2] / "content"
PASSWORD = "LastTrain2026!"
_PASSWORD_HASH = hash_password(PASSWORD)  # argon2 is slow on purpose: hash once


def load_docs(folder: str = "_fixture") -> tuple[dict, dict]:
    base = CONTENT / "missions" / folder
    return (
        json.loads((base / "items.json").read_text(encoding="utf-8")),
        json.loads((base / "mission.json").read_text(encoding="utf-8")),
    )


class FakeSession:
    """Services call commit/rollback/close; the fake store is already 'committed'."""

    def __init__(self) -> None:
        self.commits = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        pass

    def refresh(self, instance: object) -> None:
        pass  # the fake store is shared in memory, so objects are always current

    def close(self) -> None:
        pass


class FakeStore:
    def __init__(self, content_folder: str = "_fixture") -> None:
        self._clock = datetime(2026, 9, 24, 20, 0, tzinfo=UTC)
        self._ids = itertools.count(1)
        self.users: dict[uuid.UUID, NS] = {}
        self.missions: dict[str, NS] = {}
        self.versions: dict[int, NS] = {}
        self.questions: dict[int, NS] = {}
        self.options: dict[int, NS] = {}
        self.accepted: dict[int, list[str]] = {}
        self.attempts: dict[uuid.UUID, NS] = {}
        self.steps: list[NS] = []
        self.answers: list[NS] = []
        self.scores: list[NS] = []
        self.feedback: dict[uuid.UUID, NS] = {}
        self.memory: dict[uuid.UUID, NS] = {}
        self.classes: dict[uuid.UUID, NS] = {}
        self.members: list[tuple[uuid.UUID, uuid.UUID]] = []
        self.coach_calls = 0
        self._seed_catalog()
        self.version_id = self.add_version("the-last-train", *load_docs(content_folder))

    # --- setup helpers ---------------------------------------------------------------------

    def now(self) -> datetime:
        self._clock += timedelta(seconds=1)
        return self._clock

    def _seed_catalog(self) -> None:
        catalog = json.loads((CONTENT / "catalog.json").read_text(encoding="utf-8"))
        for m in catalog["missions"]:
            self.missions[m["id"]] = NS(
                id=m["id"],
                title=m["title"],
                world_zone=m["world_zone"],
                skill_focus=list(m["skill_focus"]),
                cefr_min=m["cefr_range"]["min"],
                cefr_max=m["cefr_range"]["max"],
                playable=m["playable"],
                unlock_rule=m["unlock_rule"],
                teaser=m["teaser"],
                sort_order=m["sort_order"],
            )

    def add_version(self, mission_id: str, items_doc: dict, mission_doc: dict) -> int:
        vid = len(self.versions) + 1
        self.versions[vid] = NS(
            id=vid,
            mission_id=mission_id,
            version=vid,
            content=copy.deepcopy(mission_doc),
            published_at=self.now(),
        )
        for pos, item in enumerate(items_doc["items"], start=1):
            qid = next(self._ids)
            self.questions[qid] = NS(id=qid, version_id=vid, position=pos, item=item)
            for opt_pos, opt in enumerate(item["options"] or ()):
                oid = next(self._ids)
                correct = opt["id"] == item["answer_key"].get("correct_option_id")
                self.options[oid] = NS(
                    id=oid,
                    question_id=qid,
                    option_key=opt["id"],
                    text=opt["text"],
                    position=opt_pos,
                    is_correct=correct,
                )
            if item["type"] == "fill_blank":
                self.accepted[qid] = list(item["answer_key"]["accepted"])
        return vid

    def add_user(self, email: str, name: str, role: str = "student") -> NS:
        user = NS(
            id=uuid.uuid4(),
            email=email,
            password_hash=_PASSWORD_HASH,
            display_name=name,
            role=role,
        )
        self.users[user.id] = user
        return user

    def add_class(self, name: str, teacher: NS, students: list[NS]) -> NS:
        klass = NS(id=uuid.uuid4(), name=name, teacher_id=teacher.id)
        self.classes[klass.id] = klass
        self.members += [(klass.id, s.id) for s in students]
        return klass

    # --- users -------------------------------------------------------------------------------

    def get_user_by_email(self, s, email):
        email = email.strip().lower()
        return next((u for u in self.users.values() if u.email == email), None)

    def get_user_by_id(self, s, user_id):
        return self.users.get(user_id)

    # --- missions ----------------------------------------------------------------------------

    def list_missions(self, s):
        return sorted(self.missions.values(), key=lambda m: (m.sort_order, m.id))

    def get_mission(self, s, mission_id):
        return self.missions.get(mission_id)

    def get_active_mission_version(self, s, mission_id):
        versions = [v for v in self.versions.values() if v.mission_id == mission_id]
        return max(versions, key=lambda v: v.published_at) if versions else None

    def load_mission_content(self, s, version_id):
        version = self.versions[version_id]
        items = [
            copy.deepcopy(q.item)
            for q in sorted(self.questions.values(), key=lambda q: q.position)
            if q.version_id == version_id
        ]
        doc = copy.deepcopy(version.content)
        return MissionContent({"mission_id": doc["mission_id"], "items": items}, doc)

    def get_question_id(self, s, version_id, item_id):
        return next(
            (
                q.id
                for q in self.questions.values()
                if q.version_id == version_id and q.item["id"] == item_id
            ),
            None,
        )

    def get_option_id(self, s, question_id, option_key):
        return next(
            (
                o.id
                for o in self.options.values()
                if o.question_id == question_id and o.option_key == option_key
            ),
            None,
        )

    def get_answer_key(self, s, question_id):
        q = self.questions[question_id]
        correct = next(
            (o for o in self.options.values() if o.question_id == question_id and o.is_correct),
            None,
        )
        return AnswerKey(
            question_id=question_id,
            item_type=q.item["type"],
            correct_option_id=correct.id if correct else None,
            correct_option_key=correct.option_key if correct else None,
            correct_option_text=correct.text if correct else None,
            accepted=tuple(self.accepted.get(question_id, ())),
        )

    # --- attempts ----------------------------------------------------------------------------

    def create_attempt(
        self,
        s,
        *,
        user_id,
        mission_id,
        mission_version_id,
        start_node_id,
        state,
        maya_decision,
        now=None,
    ):
        if self.get_open_attempt(s, user_id, mission_id) is not None:
            return None  # the one-open-attempt partial unique index
        now = now or self.now()
        attempt = NS(
            id=uuid.uuid4(),
            user_id=user_id,
            mission_id=mission_id,
            mission_version_id=mission_version_id,
            status="in_progress",
            current_node_id=start_node_id,
            state=copy.deepcopy(state),
            started_at=now,
            last_activity_at=now,
            completed_at=None,
            submitted_at=None,
            score_pct=None,
            correct_count=None,
            incorrect_count=None,
            suggested_cefr=None,
            ending_node_id=None,
        )
        self.attempts[attempt.id] = attempt
        self.steps.append(
            NS(
                id=next(self._ids),
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
                state_after=copy.deepcopy(state),
                created_at=now,
            )
        )
        return attempt

    def get_open_attempt(self, s, user_id, mission_id):
        return next(
            (
                a
                for a in self.attempts.values()
                if a.user_id == user_id
                and a.mission_id == mission_id
                and a.status in ("in_progress", "completed")
            ),
            None,
        )

    def list_open_attempts(self, s, user_id):
        return sorted(
            (
                a
                for a in self.attempts.values()
                if a.user_id == user_id and a.status in ("in_progress", "completed")
            ),
            key=lambda a: a.last_activity_at,
            reverse=True,
        )

    def get_owned_attempt(self, s, attempt_id, user_id):
        attempt = self.attempts.get(attempt_id)
        return attempt if attempt is not None and attempt.user_id == user_id else None

    def lock_attempt_for_update(self, s, attempt_id, user_id):
        return self.get_owned_attempt(s, attempt_id, user_id)

    def mark_attempt_completed(self, s, attempt, *, ending_node_id, now=None):
        attempt.status, attempt.ending_node_id = "completed", ending_node_id
        attempt.completed_at = now or self.now()

    def finish_attempt(
        self, s, attempt, *, score_pct, correct_count, incorrect_count, suggested_cefr, now=None
    ):
        attempt.status, attempt.submitted_at = "submitted", now or self.now()
        attempt.score_pct, attempt.correct_count = score_pct, correct_count
        attempt.incorrect_count, attempt.suggested_cefr = incorrect_count, suggested_cefr

    def get_attempt_number(self, s, attempt):
        return 1 + sum(
            1
            for a in self.attempts.values()
            if a.user_id == attempt.user_id
            and a.mission_id == attempt.mission_id
            and a.started_at < attempt.started_at
        )

    def get_last_step(self, s, attempt_id):
        steps = self.list_steps(s, attempt_id)
        return steps[-1] if steps else None

    def list_steps(self, s, attempt_id):
        return sorted((st for st in self.steps if st.attempt_id == attempt_id), key=lambda x: x.seq)

    def append_step(
        self,
        s,
        attempt,
        *,
        from_node_id,
        to_node_id,
        on_event,
        action,
        minutes_cost,
        minutes_left_after,
        maya_decision,
        state_after,
        now=None,
    ):
        now = now or self.now()
        parent = self.get_last_step(s, attempt.id)
        step = NS(
            id=next(self._ids),
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
            state_after=copy.deepcopy(state_after),
            created_at=now,
        )
        self.steps.append(step)
        attempt.current_node_id, attempt.state = to_node_id, copy.deepcopy(state_after)
        attempt.last_activity_at = now
        return step

    def answer_exists(self, s, attempt_id, question_id):
        return any(
            a.attempt_id == attempt_id and a.question_id == question_id for a in self.answers
        )

    def save_answer(
        self,
        s,
        *,
        attempt_id,
        question_id,
        selected_option_id=None,
        text_answer=None,
        is_correct,
        hint_shown,
        now=None,
    ):
        if self.answer_exists(s, attempt_id, question_id):
            return None
        assert (selected_option_id is None) != (text_answer is None)  # CHECK one_answer
        answer = NS(
            attempt_id=attempt_id,
            question_id=question_id,
            selected_option_id=selected_option_id,
            text_answer=text_answer,
            is_correct=is_correct,
            hint_shown=hint_shown,
            answered_at=now or self.now(),
        )
        self.answers.append(answer)
        return answer

    def list_attempt_answers(self, s, attempt_id):
        rows = []
        for a in self.answers:
            if a.attempt_id != attempt_id:
                continue
            q = self.questions[a.question_id]
            opt = self.options.get(a.selected_option_id) if a.selected_option_id else None
            rows.append(
                AnswerRow(
                    question_id=q.id,
                    item_id=q.item["id"],
                    item_type=q.item["type"],
                    skill=q.item["skill"],
                    cefr=q.item["cefr"],
                    position=q.position,
                    is_correct=a.is_correct,
                    hint_shown=a.hint_shown,
                    selected_option_key=opt.option_key if opt else None,
                    selected_option_text=opt.text if opt else None,
                    text_answer=a.text_answer,
                    answered_at=a.answered_at,
                )
            )
        return sorted(rows, key=lambda r: r.position)

    def save_skill_scores(self, s, attempt_id, scores):
        for sc in scores:
            assert sc.total > 0 and 0 <= sc.correct <= sc.total
            self.scores.append(
                NS(
                    attempt_id=attempt_id,
                    skill=sc.skill,
                    correct=sc.correct,
                    total=sc.total,
                    pct=sc.pct,
                )
            )

    def get_skill_scores(self, s, attempt_id):
        return sorted((x for x in self.scores if x.attempt_id == attempt_id), key=lambda x: x.skill)

    # --- coach -------------------------------------------------------------------------------

    def get_coach_memory(self, s, user_id):
        return self.memory.get(user_id)

    def save_coach_memory(self, s, user_id, *, sessions_count, notes, next_greeting, now=None):
        self.memory[user_id] = NS(
            user_id=user_id,
            sessions_count=sessions_count,
            notes=list(notes),
            next_greeting=next_greeting,
            updated_at=now or self.now(),
        )
        return self.memory[user_id]

    def get_coach_feedback(self, s, attempt_id):
        return self.feedback.get(attempt_id)

    def get_latest_submitted_feedback(self, s, user_id):
        submitted = [
            a for a in self.attempts.values() if a.user_id == user_id and a.status == "submitted"
        ]
        if not submitted:
            return None
        latest = max(submitted, key=lambda a: a.submitted_at)
        return self.feedback.get(latest.id)

    def save_coach_feedback(
        self, s, *, attempt_id, provider, model, prompt_version, status, content, latency_ms
    ):
        self.coach_calls += 1
        if attempt_id in self.feedback:
            return False  # ON CONFLICT (attempt_id) DO NOTHING
        self.feedback[attempt_id] = NS(
            attempt_id=attempt_id,
            provider=provider,
            model=model,
            prompt_version=prompt_version,
            status=status,
            content=copy.deepcopy(content),
            latency_ms=latency_ms,
            created_at=self.now(),
        )
        return True

    # --- progress ----------------------------------------------------------------------------

    def _submitted(self, user_id):
        return sorted(
            (a for a in self.attempts.values() if a.user_id == user_id and a.status == "submitted"),
            key=lambda a: a.submitted_at,
            reverse=True,
        )

    def get_profile(self, s, user_id, last_n=3):
        last = self._submitted(user_id)[:last_n]
        sums: dict[str, list[int]] = {}
        for a in last:
            for sc in self.get_skill_scores(s, a.id):
                pair = sums.setdefault(sc.skill, [0, 0])
                pair[0] += sc.correct
                pair[1] += sc.total
        if not sums:
            return None
        return ProfileSums(len(last), [SkillSums(k, c, t) for k, (c, t) in sorted(sums.items())])

    def list_submitted_attempts(self, s, user_id):
        return [
            HistoryRow(
                attempt_id=a.id,
                attempt_number=self.get_attempt_number(s, a),
                mission_id=a.mission_id,
                mission_title=self.missions[a.mission_id].title,
                mission_version_id=a.mission_version_id,
                started_at=a.started_at,
                submitted_at=a.submitted_at,
                ending_node_id=a.ending_node_id,
                suggested_cefr=a.suggested_cefr,
                score_pct=a.score_pct,
                correct=a.correct_count,
                incorrect=a.incorrect_count,
                skills=[
                    SkillSums(x.skill, x.correct, x.total) for x in self.get_skill_scores(s, a.id)
                ],
            )
            for a in self._submitted(user_id)
        ]

    def get_progress(self, s, user_id):
        history = self.list_submitted_attempts(s, user_id)
        memory = self.memory.get(user_id)
        opened = self.list_open_attempts(s, user_id)
        return ProgressData(
            profile=self.get_profile(s, user_id),
            history=history,
            level_history=[
                LevelPoint(h.attempt_id, h.submitted_at, h.suggested_cefr)
                for h in reversed(history)
            ],
            notes=list(memory.notes) if memory else [],
            open_attempt=opened[0] if opened else None,
        )

    def list_teacher_classes(self, s, teacher_id):
        return [
            ClassSummary(
                c.id,
                c.name,
                self.users[c.teacher_id].display_name,
                sum(1 for cid, _ in self.members if cid == c.id),
            )
            for c in self.classes.values()
            if teacher_id is None or c.teacher_id == teacher_id
        ]

    def list_class_progress(self, s, class_id, teacher_id):
        klass = self.classes.get(class_id)
        if klass is None or (teacher_id is not None and klass.teacher_id != teacher_id):
            return None
        students = []
        for cid, uid in self.members:
            if cid != class_id:
                continue
            history = self.list_submitted_attempts(s, uid)
            activity = [a.last_activity_at for a in self.attempts.values() if a.user_id == uid]
            students.append(
                StudentProgress(
                    display_name=self.users[uid].display_name,
                    missions_played=len(history),
                    latest=history[0] if history else None,
                    profile=self.get_profile(s, uid),
                    last_activity_at=max(activity) if activity else None,
                )
            )
        return ClassProgress(klass.id, klass.name, sorted(students, key=lambda x: x.display_name))

    # --- wiring ------------------------------------------------------------------------------

    MODULES = {
        users_repo: ("get_user_by_email", "get_user_by_id"),
        missions_repo: (
            "list_missions",
            "get_mission",
            "get_active_mission_version",
            "load_mission_content",
            "get_question_id",
            "get_option_id",
            "get_answer_key",
        ),
        attempts_repo: (
            "create_attempt",
            "get_open_attempt",
            "list_open_attempts",
            "get_owned_attempt",
            "lock_attempt_for_update",
            "mark_attempt_completed",
            "finish_attempt",
            "get_attempt_number",
            "get_last_step",
            "list_steps",
            "append_step",
            "answer_exists",
            "save_answer",
            "list_attempt_answers",
            "save_skill_scores",
            "get_skill_scores",
        ),
        coach_repo: (
            "get_coach_memory",
            "save_coach_memory",
            "get_coach_feedback",
            "get_latest_submitted_feedback",
            "save_coach_feedback",
        ),
        progress_repo: (
            "get_profile",
            "list_submitted_attempts",
            "get_progress",
            "list_teacher_classes",
            "list_class_progress",
        ),
    }

    def install(self, monkeypatch) -> None:
        for module, names in self.MODULES.items():
            for name in names:
                assert hasattr(module, name), f"{module.__name__}.{name} is not published"
                monkeypatch.setattr(module, name, getattr(self, name))
