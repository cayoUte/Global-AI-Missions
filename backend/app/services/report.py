"""The Mission Report (api-contract §7). Built only for a SUBMITTED attempt: that is the one
moment item tags, outcomes, correct answers and explanations may leave the server (PD-029).

Score, counts, per-skill results and the suggested level are read back from what phase 1 stored;
they are never recomputed here. The level's evidence and reason sentence are re-derived from the
stored per-item outcomes (a pure function of them) so the explanation matches the stored level.
"""

import logging
from typing import Any

from sqlalchemy.orm import Session

from app import engine
from app.core.errors import ErrorCode
from app.engine import StepRecord
from app.repositories import attempts as attempts_repo
from app.repositories import missions as missions_repo
from app.schemas.common import SkillScore
from app.schemas.report import (
    AttemptRecord,
    DiaryCheckpoint,
    DiaryEntryView,
    FeedbackSource,
    Interpretation,
    LevelEvidence,
    MissedCheckpoint,
    NextMission,
    Report,
    ResultBlock,
    SuggestedLevel,
)
from app.services import attempts, coach, content, feedback, grading, leveling
from app.services.content import LoadedMission
from app.services.state_view import ending_ref, stimulus_view

logger = logging.getLogger(__name__)


def get_report(session: Session, user: Any, attempt_id: str) -> Report:
    attempt = attempts.get_owned_attempt(session, user, attempt_id)
    if attempt.status != "submitted":
        raise attempts.conflict(
            session, ErrorCode.MISSION_NOT_FINISHED, "Report exists after submit.", attempt
        )
    return build_report(session, user, attempt)


def submit_and_report(session: Session, user: Any, attempt_id: str) -> Report:
    attempts.submit(session, user, attempt_id)
    return get_report(session, user, attempt_id)


def build_report(session: Session, user: Any, attempt: Any) -> Report:
    loaded = content.get_loaded_mission(session, attempt.mission_version_id)
    graph = loaded.graph
    mission = missions_repo.get_mission(session, attempt.mission_id)
    title = mission.title if mission else graph.title
    answers = attempts_repo.list_attempt_answers(session, attempt.id)
    skills = feedback.stored_skill_results(session, attempt.id)
    strength, challenge = grading.strength_and_challenge(skills)
    fb = feedback.feedback_for_report(session, user, attempt, loaded)
    return Report(
        attempt_id=str(attempt.id),
        mission_id=attempt.mission_id,
        mission_title=title,
        label=leveling.report_label(attempt.suggested_cefr, title, attempt.score_pct),
        result=_result_block(session, attempt, loaded, skills),
        attempt_record=AttemptRecord(
            attempt_number=attempts_repo.get_attempt_number(session, attempt),
            started_at=feedback.iso(attempt.started_at) or "",
            submitted_at=feedback.iso(attempt.submitted_at) or "",
            ending=ending_ref(graph, attempt.ending_node_id),
            story_minutes_used=graph.minutes_available
            - attempts.engine_state(attempt).minutes_left,
            rescue_used=attempts.engine_state(attempt).rescued,
            hints_received=sum(1 for a in answers if a.hint_shown),
        ),
        interpretation=Interpretation(
            summary=fb.content.get("summary", ""),
            strength=strength,  # always the deterministic values (SHARED_CONTEXT §6)
            challenge=challenge,
            recommendation=fb.content.get("recommendation", ""),
        ),
        feedback_source=FeedbackSource(status=fb.status, provider_label=fb.provider_label),
        next_mission=_next_mission(session, user, fb.content.get("next_mission_id"), challenge),
        diary=_diary(session, attempt, loaded),
        missed=_missed(session, answers, loaded),
    )


def _result_block(
    session: Session, attempt: Any, loaded: LoadedMission, skills: list[grading.SkillResult]
) -> ResultBlock:
    graded = attempts.graded_items(session, attempt, loaded)
    by_cefr = grading.grade_attempt(graded).by_cefr
    level = leveling.suggest_level(attempt.score_pct, by_cefr)
    if level.cefr != attempt.suggested_cefr:  # stored value wins; flag the drift loudly
        logger.warning(
            "Stored level %s differs from re-derived %s for attempt %s",
            attempt.suggested_cefr,
            level.cefr,
            attempt.id,
        )
    return ResultBlock(
        score_pct=attempt.score_pct,
        correct=attempt.correct_count,
        incorrect=attempt.incorrect_count,
        total=attempt.correct_count + attempt.incorrect_count,
        skills=[
            SkillScore(skill=s.skill, correct=s.correct, total=s.total, pct=s.pct) for s in skills
        ],
        unmeasured_skills=list(grading.UNMEASURED_SKILLS),
        suggested_level=SuggestedLevel(
            cefr=attempt.suggested_cefr,
            base_cefr=level.base_cefr,
            reason=level.reason,
            evidence=[LevelEvidence(**vars(e)) for e in level.evidence],
        ),
    )


def _next_mission(
    session: Session, user: Any, next_mission_id: str | None, challenge: str
) -> NextMission | None:
    from app.services import world

    candidates = {m.id: m for m in feedback.candidate_missions(session)}
    if next_mission_id not in candidates:
        next_mission_id = coach.default_next_mission(challenge, list(candidates))
    mission = candidates.get(next_mission_id or "")
    if mission is None:
        return None
    skill = mission.skill_focus[0] if mission.skill_focus else challenge
    reason = (
        f"It trains {skill}, the skill that was hardest tonight."
        if skill == challenge
        else f"It trains {skill}, and Maya thinks it is your next good step."
    )
    return NextMission(
        mission_id=mission.id,
        title=mission.title,
        skill_focus=list(mission.skill_focus),
        reason=reason,
        state=world.card_state_for(session, user, mission),
        unlock_hint=mission.unlock_rule.get("hint", ""),
    )


def _diary(session: Session, attempt: Any, loaded: LoadedMission) -> list[DiaryEntryView]:
    """Rebuilt from the persisted steps by following parent pointers (engine.build_diary).
    Each entry's outcome is the event of the step that LEFT that node."""
    steps = attempts_repo.list_steps(session, attempt.id)
    left_by = {step.parent_step_id: step.on_event for step in steps if step.parent_step_id}
    records = [
        StepRecord(
            step_id=str(step.id),
            parent_id=str(step.parent_step_id) if step.parent_step_id else None,
            node_id=step.to_node_id,
            minutes_left=step.minutes_left_after,
            flags=frozenset((step.state_after or {}).get("flags", ())),
            outcome=_outcome(left_by.get(step.id)),
            maya_decision=step.maya_decision,
        )
        for step in steps
    ]
    return [
        DiaryEntryView(
            seq=e.seq,
            clock=e.clock,
            node_id=e.node_id,
            kind=e.kind,
            location=e.location,
            text=e.text,
            checkpoint=DiaryCheckpoint(**e.checkpoint) if e.checkpoint else None,
            maya_decision=e.maya_decision,
        )
        for e in engine.build_diary(loaded.graph, records)
    ]


def _outcome(event: str | None) -> str | None:
    return event if event in (engine.CORRECT, engine.INCORRECT) else None


def _missed(session: Session, answers: list[Any], loaded: LoadedMission) -> list[MissedCheckpoint]:
    missed = []
    for answer in answers:  # already in mission order (item position)
        if answer.is_correct:
            continue
        item = loaded.graph.items[answer.item_id]
        key = missions_repo.get_answer_key(session, answer.question_id)
        missed.append(
            MissedCheckpoint(
                item_id=answer.item_id,
                type=answer.item_type,
                skill=answer.skill,
                cefr=answer.cefr,
                prompt=item["prompt"],
                stimulus=stimulus_view(item.get("stimulus")),
                your_answer=answer.your_answer,
                correct_answer=key.display_answer or "",
                explanation=item["explanation"],
                maya_tip=item["hint"],
            )
        )
    return missed
