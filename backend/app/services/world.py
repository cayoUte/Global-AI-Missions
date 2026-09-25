"""The English World (api-contract §5.6), progress (§5.13) and the teacher views (§5.14-§5.15).

Card states and unlocks are deterministic rules over the student's submitted attempts (PD-008);
the LLM never influences them. Responses carry aggregates only, never item content (§9.B).
"""

import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy.orm import Session

from app import engine
from app.core.errors import DomainError, ErrorCode
from app.repositories import attempts as attempts_repo
from app.repositories import coach as coach_repo
from app.repositories import missions as missions_repo
from app.repositories import progress as progress_repo
from app.schemas.common import Profile, SkillPct, SkillScore
from app.schemas.world import (
    CefrRange,
    ClassesResponse,
    ClassProgressResponse,
    ClassStudent,
    ClassSummary,
    Greeting,
    HistoryRow,
    LatestResult,
    LevelPoint,
    MissionCard,
    Note,
    OpenAttemptCard,
    ProgressOpenAttempt,
    ProgressResponse,
    Snapshot,
    StudentName,
    WorldResponse,
)
from app.services import coach, content, grading, leveling
from app.services.attempts import engine_state
from app.services.feedback import candidate_missions, iso
from app.services.state_view import clock_view, ending_ref

# PD-022: the canonical first-meeting greeting (no coach memory yet).
FIRST_MEETING_GREETING = (
    "Hi, I'm Maya. Tonight we have one job: get you on the last train home. Ready when you are."
)


# --- Rules ------------------------------------------------------------------------------------


def unlock_rule_met(rule: dict[str, Any], history: Sequence[Any]) -> bool:
    """PD-008: always | mission_submitted {mission_id} | level_reached {min_level}."""
    kind = rule.get("kind")
    if kind == "always":
        return True
    if kind == "mission_submitted":
        return any(h.mission_id == rule.get("mission_id") for h in history)
    if kind == "level_reached":
        needed = leveling.CEFR_RANK.get(rule.get("min_level", ""), 99)
        return any(leveling.CEFR_RANK.get(h.suggested_cefr, -1) >= needed for h in history)
    return False


def unlock_met(session: Session, user: Any, mission: Any) -> bool:
    if mission.unlock_rule.get("kind") == "always":
        return True
    return unlock_rule_met(
        mission.unlock_rule, progress_repo.list_submitted_attempts(session, user.id)
    )


def card_state(mission: Any, open_attempt: Any | None, history: Sequence[Any]) -> str:
    """Exactly one state per card, rules evaluated in the contract's order (F-04)."""
    unlocked = unlock_rule_met(mission.unlock_rule, history)
    if not mission.playable:
        return "in_preparation" if unlocked else "locked"
    if open_attempt is not None:
        return "in_progress" if open_attempt.status == "in_progress" else "waiting_to_submit"
    if any(h.mission_id == mission.id for h in history):
        return "completed"
    return "available" if unlocked else "locked"


def card_state_for(session: Session, user: Any, mission: Any) -> str:
    history = progress_repo.list_submitted_attempts(session, user.id)
    open_attempt = attempts_repo.get_open_attempt(session, user.id, mission.id)
    return card_state(mission, open_attempt, history)


def profile_view(sums: Any | None) -> Profile | None:
    """PD-009 / F-05: pooled Σcorrect / Σtotal per scored skill, fixed order, rounded half up."""
    if sums is None:
        return None
    by_skill = {s.skill: s for s in sums.skills}
    skills = [
        SkillPct(skill=skill, pct=grading.percent(by_skill[skill].correct, by_skill[skill].total))
        for skill in grading.SCORED_SKILLS
        if skill in by_skill and by_skill[skill].total > 0
    ]
    return Profile(based_on_attempts=sums.based_on_attempts, skills=skills) if skills else None


def history_label(row: Any) -> str:
    return leveling.report_label(row.suggested_cefr, row.mission_title, row.score_pct)


def skill_scores(rows: Sequence[Any]) -> list[SkillScore]:
    by_skill = {r.skill: r for r in rows}
    return [
        SkillScore(
            skill=skill,
            correct=by_skill[skill].correct,
            total=by_skill[skill].total,
            pct=grading.percent(by_skill[skill].correct, by_skill[skill].total),
        )
        for skill in grading.SCORED_SKILLS
        if skill in by_skill and by_skill[skill].total > 0
    ]


# --- English World ----------------------------------------------------------------------------


def get_world(session: Session, user: Any) -> WorldResponse:
    history = progress_repo.list_submitted_attempts(session, user.id)  # newest first
    open_by_mission = {a.mission_id: a for a in attempts_repo.list_open_attempts(session, user.id)}
    pick = _maya_pick(session, user, history)
    cards = []
    for mission in missions_repo.list_missions(session):
        open_attempt = open_by_mission.get(mission.id)
        latest = next((h for h in history if h.mission_id == mission.id), None)
        cards.append(
            MissionCard(
                mission_id=mission.id,
                title=mission.title,
                world_zone=mission.world_zone,
                teaser=mission.teaser,
                sort_order=mission.sort_order,
                skill_focus=list(mission.skill_focus),
                cefr_range=CefrRange(min=mission.cefr_min, max=mission.cefr_max),
                playable=mission.playable,
                state=card_state(mission, open_attempt, history),
                is_maya_pick=mission.id == pick,
                unlock_hint=mission.unlock_rule.get("hint", ""),
                open_attempt=_open_card(session, open_attempt) if open_attempt else None,
                latest_result=LatestResult(
                    attempt_id=str(latest.attempt_id),
                    label=history_label(latest),
                    submitted_at=iso(latest.submitted_at) or "",
                )
                if latest
                else None,
                attempts_submitted=sum(1 for h in history if h.mission_id == mission.id),
            )
        )
    return WorldResponse(
        student=StudentName(display_name=user.display_name),
        greeting=_greeting(session, user),
        cards=cards,
        snapshot=Snapshot(
            missions_played=len(history),
            latest_label=history_label(history[0]) if history else None,
            profile=profile_view(progress_repo.get_profile(session, user.id)),
        ),
    )


def _greeting(session: Session, user: Any) -> Greeting:
    memory = coach_repo.get_coach_memory(session, user.id)
    if memory is None or not memory.next_greeting:
        return Greeting(text=FIRST_MEETING_GREETING, source="first_meeting", mood="curious")
    return Greeting(text=memory.next_greeting, source="memory", mood="encouraging")


def _maya_pick(session: Session, user: Any, history: Sequence[Any]) -> str | None:
    """next_mission_id of the most recent submitted attempt's feedback, or the deterministic
    fallback when that attempt has no feedback row. None without submitted attempts."""
    if not history:
        return None
    row = coach_repo.get_latest_submitted_feedback(session, user.id)
    candidates = [m.id for m in candidate_missions(session)]
    if row is not None and row.content.get("next_mission_id") in candidates:
        return str(row.content["next_mission_id"])
    results = [grading.SkillResult(s.skill, s.correct, s.total,
                                   grading.percent(s.correct, s.total)) for s in history[0].skills]
    _, challenge = grading.strength_and_challenge(results)
    return coach.default_next_mission(challenge, candidates)


def _open_card(session: Session, attempt: Any) -> OpenAttemptCard:
    graph = content.get_loaded_mission(session, attempt.mission_version_id).graph
    state = engine_state(attempt)
    return OpenAttemptCard(
        attempt_id=str(attempt.id),
        status=attempt.status,
        clock=clock_view(graph, state.minutes_left),
        location=engine.resolve_scene(graph, state.node_id, state.flags).location,
        ending=ending_ref(graph, state.node_id) if attempt.status == "completed" else None,
    )


# --- Progress ---------------------------------------------------------------------------------


def get_progress(session: Session, user: Any) -> ProgressResponse:
    data = progress_repo.get_progress(session, user.id)
    open_attempt = None
    if data.open_attempt is not None:
        a = data.open_attempt
        graph = content.get_loaded_mission(session, a.mission_version_id).graph
        mission = missions_repo.get_mission(session, a.mission_id)
        open_attempt = ProgressOpenAttempt(
            attempt_id=str(a.id),
            mission_id=a.mission_id,
            mission_title=mission.title if mission else graph.title,
            status=a.status,
            clock=clock_view(graph, engine_state(a).minutes_left),
        )
    return ProgressResponse(
        profile=profile_view(data.profile),
        history=[_history_row(session, h) for h in data.history],
        level_history=[
            LevelPoint(
                attempt_id=str(p.attempt_id),
                submitted_at=iso(p.submitted_at) or "",
                suggested_cefr=p.suggested_cefr,
            )
            for p in data.level_history
        ],
        notes=[_note(n) for n in data.notes[:5]],
        open_attempt=open_attempt,
    )


def _history_row(session: Session, h: Any) -> HistoryRow:
    graph = content.get_loaded_mission(session, h.mission_version_id).graph
    return HistoryRow(
        attempt_id=str(h.attempt_id),
        attempt_number=h.attempt_number,
        mission_id=h.mission_id,
        mission_title=h.mission_title,
        submitted_at=iso(h.submitted_at) or "",
        ending=ending_ref(graph, h.ending_node_id),
        label=history_label(h),
        suggested_cefr=h.suggested_cefr,
        score_pct=h.score_pct,
        correct=h.correct,
        incorrect=h.incorrect,
        skills=skill_scores(h.skills),
    )


def _note(note: Any) -> Note:
    if isinstance(note, dict):
        return Note(text=str(note.get("text", "")), created_at=str(note.get("created_at", "")))
    return Note(text=str(note), created_at="")


# --- Teacher (RBAC demo) ----------------------------------------------------------------------


def _teacher_scope(user: Any) -> uuid.UUID | None:
    """None = every class (admin); otherwise only the classes this teacher teaches."""
    return None if user.role == "admin" else user.id


def list_classes(session: Session, user: Any) -> ClassesResponse:
    return ClassesResponse(
        classes=[
            ClassSummary(
                class_id=str(c.class_id),
                name=c.name,
                teacher_name=c.teacher_name,
                student_count=c.student_count,
            )
            for c in progress_repo.list_teacher_classes(session, _teacher_scope(user))
        ]
    )


def class_progress(session: Session, user: Any, class_id: str) -> ClassProgressResponse:
    """Another teacher's class is 'not found' (404), like an unknown or malformed id."""
    try:
        parsed = uuid.UUID(class_id)
    except ValueError as exc:
        raise DomainError(ErrorCode.NOT_FOUND, "Class not found.") from exc
    data = progress_repo.list_class_progress(session, parsed, _teacher_scope(user))
    if data is None:
        raise DomainError(ErrorCode.NOT_FOUND, "Class not found.")
    return ClassProgressResponse(
        class_id=str(data.class_id),
        name=data.name,
        students=[
            ClassStudent(
                display_name=s.display_name,
                missions_played=s.missions_played,
                latest_label=history_label(s.latest) if s.latest else None,
                profile=profile_view(s.profile),
                last_activity_at=iso(s.last_activity_at),
            )
            for s in data.students
        ],
    )
