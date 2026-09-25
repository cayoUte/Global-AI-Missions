"""Submit phase 2 and the report's interpretation: Maya's feedback for a SUBMITTED attempt.

The coach never influences score, level or unlocks (SHARED_CONTEXT §9.6): everything it receives
was computed and committed by phase 1, and strength / challenge / next mission are checked
against the deterministic values before anything is stored.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.repositories import attempts as attempts_repo
from app.repositories import coach as coach_repo
from app.repositories import missions as missions_repo
from app.services import coach, content, grading
from app.services.content import LoadedMission

MAX_NOTES = 5
_PROVIDER_LABELS = {"anthropic": "Claude", "mock": coach.FALLBACK_LABEL}


@dataclass(frozen=True)
class FeedbackView:
    content: dict[str, Any]
    status: str  # ready | fallback
    provider_label: str


def stored_skill_results(session: Session, attempt_id: uuid.UUID) -> list[grading.SkillResult]:
    """The per-skill result written by phase 1, in the fixed display order."""
    rows = {row.skill: row for row in attempts_repo.get_skill_scores(session, attempt_id)}
    return [
        grading.SkillResult(skill, rows[skill].correct, rows[skill].total, rows[skill].pct)
        for skill in grading.SCORED_SKILLS
        if skill in rows
    ]


def candidate_missions(session: Session) -> list[Any]:
    """PD-010: the next-mission candidates are the non-playable catalog missions."""
    return [m for m in missions_repo.list_missions(session) if not m.playable]


def build_coach_request(
    session: Session, user: Any, attempt: Any, loaded: LoadedMission
) -> coach.CoachRequest:
    skills = stored_skill_results(session, attempt.id)
    strength, challenge = grading.strength_and_challenge(skills)
    answers = attempts_repo.list_attempt_answers(session, attempt.id)
    memory = coach_repo.get_coach_memory(session, user.id)
    candidates = [m.id for m in candidate_missions(session)]
    ending = loaded.graph.node(attempt.ending_node_id).get("ending", {})
    return coach.CoachRequest(
        first_name=str(user.display_name).split(" ")[0],
        suggested_cefr=attempt.suggested_cefr,
        score_pct=attempt.score_pct,
        skills=[vars(s) for s in skills],
        strength=strength,
        challenge=challenge,
        missed=[
            {
                "skill": a.skill,
                "cefr": a.cefr,
                "prompt": loaded.graph.items[a.item_id]["prompt"],
                "explanation": loaded.graph.items[a.item_id]["explanation"],
            }
            for a in answers
            if not a.is_correct
        ],
        ending_key=ending.get("key", ""),
        rescue_used=bool((attempt.state or {}).get("rescued", False)),
        hints_received=sum(1 for a in answers if a.hint_shown),
        sessions_count=memory.sessions_count if memory else 0,
        last_notes=[_note_text(n) for n in (memory.notes if memory else [])][:MAX_NOTES],
        candidate_mission_ids=candidates,
        default_next_mission_id=coach.default_next_mission(challenge, candidates),
    )


def ensure_feedback(session: Session, user: Any, attempt_id: uuid.UUID) -> None:
    """Submit phase 2. Runs after the grading commit. Stores the feedback at most once and grows
    coach memory exactly once per attempt (only when this call wrote the feedback row)."""
    if coach_repo.get_coach_feedback(session, attempt_id) is not None:
        session.commit()
        return
    attempt = attempts_repo.get_owned_attempt(session, attempt_id, user.id)
    loaded = content.get_loaded_mission(session, attempt.mission_version_id)
    request = build_coach_request(session, user, attempt, loaded)
    session.commit()  # end the read transaction: nothing is held while the coach runs
    result = coach.run_coach(request)
    wrote = coach_repo.save_coach_feedback(
        session,
        attempt_id=attempt_id,
        provider=result.provider,
        model=result.model,
        prompt_version=result.prompt_version,
        status=result.status,
        content=result.content,
        latency_ms=result.latency_ms,
    )
    if wrote:
        memory = coach_repo.get_coach_memory(session, user.id)
        note = {"text": result.content["memory_note"], "created_at": iso(datetime.now(UTC))}
        coach_repo.save_coach_memory(
            session,
            user.id,
            sessions_count=(memory.sessions_count if memory else 0) + 1,
            notes=[note, *(memory.notes if memory else [])][:MAX_NOTES],
            next_greeting=result.content["next_greeting"],
        )
    session.commit()


def feedback_for_report(
    session: Session, user: Any, attempt: Any, loaded: LoadedMission
) -> FeedbackView:
    """The stored feedback, or the deterministic mock when no row exists yet (status fallback)."""
    row = coach_repo.get_coach_feedback(session, attempt.id)
    if row is None:
        request = build_coach_request(session, user, attempt, loaded)
        return FeedbackView(coach.deterministic_feedback(request), "fallback", coach.FALLBACK_LABEL)
    label = row.content.get("provider_label") or _PROVIDER_LABELS.get(row.provider, row.provider)
    return FeedbackView(dict(row.content), row.status, str(label))


def iso(moment: datetime | None) -> str | None:
    """ISO 8601 in UTC with Z (api-contract §1)."""
    if moment is None:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _note_text(note: Any) -> str:
    return str(note.get("text", "")) if isinstance(note, dict) else str(note)
