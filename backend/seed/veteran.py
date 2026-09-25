"""The veteran's history: 4 submitted attempts generated with the engine simulator.

The simulator's Trace is answer-free (outcomes only). Here, on the server and with the answer
keys (repositories.missions.get_answer_key), each outcome becomes a concrete answer:
    correct   -> the correct option, or the primary accepted text (fill_blank)
    incorrect -> the first wrong option, or a fixed wrong text (fill_blank)
and that answer is replayed through the engine's real RESULT(s, a), which must reproduce the
trace's outcome. Steps, answers, skill scores, coach feedback and coach memory are then written
with the same repository functions the API uses.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core import demo
from app.engine import (
    CONTINUE,
    HINT,
    RESCUE,
    Action,
    MissionGraph,
    SimulatedStudent,
    State,
    Trace,
    arrival_decision,
    build_graph,
    compute_h,
    initial_state,
    is_goal,
    normalize_answer,
    result,
    run,
)
from app.models import Attempt, CoachMemory, User
from app.repositories import attempts as attempts_repo
from app.repositories import coach as coach_repo
from app.repositories import missions as missions_repo
from seed.scoring import GradedItem, grade, mock_feedback

# Wrong texts for fill_blank items: the first one that is not an accepted answer is used.
WRONG_TEXT_CANDIDATES = ("goes", "went", "to", "is", "the")
STEP_SECONDS = 25  # story steps are spread over the evening for realistic timestamps
SEED_PROMPT_VERSION = "seed-v1"


@dataclass(frozen=True)
class SeededAttempt:
    attempt_id: Any
    seed: int
    trace: Trace
    answers: list[tuple[str, bool, int | None, str | None]]  # item, outcome, option_id, text


def state_json(s: State) -> dict[str, Any]:
    """The persisted engine state (attempts.state / attempt_steps.state_after)."""
    return {
        "minutes_left": s.minutes_left,
        "flags": sorted(s.flags),
        "rescued": s.rescued,
        "maya_mood": s.maya_mood,
    }


def _concrete_answer(
    session: Session, version_id: int, item: Any, correct: bool
) -> tuple[int, Action, int | None, str | None]:
    """(question_id, engine action, selected_option_id, text_answer) for a trace outcome."""
    question_id = missions_repo.get_question_id(session, version_id, item["id"])
    if question_id is None:
        raise LookupError(f"item {item['id']} is not seeded in version {version_id}")
    key = missions_repo.get_answer_key(session, question_id)
    if item["type"] == "fill_blank":
        if correct:
            text = key.accepted[0]
        else:
            text = next(w for w in WRONG_TEXT_CANDIDATES if normalize_answer(w) not in key.accepted)
        return question_id, Action("type", text), None, text
    if correct:
        option_key = key.correct_option_key
    else:
        option_key = next(o["id"] for o in item["options"] if o["id"] != key.correct_option_key)
    assert option_key is not None
    option_id = missions_repo.get_option_id(session, question_id, option_key)
    return question_id, Action("choose", option_key), option_id, None


def _evening(now: datetime, days_ago: int) -> datetime:
    day = (now - timedelta(days=days_ago)).date()
    return datetime.combine(day, time(20, 30), tzinfo=UTC)


def replay_trace(
    session: Session,
    *,
    user: User,
    mission_id: str,
    version_id: int,
    graph: MissionGraph,
    h: dict[str, int],
    trace: Trace,
    started_at: datetime,
) -> SeededAttempt:
    clock = started_at
    s = initial_state(graph)
    decision = arrival_decision(graph, h, s)
    attempt = attempts_repo.create_attempt(
        session,
        user_id=user.id,
        mission_id=mission_id,
        mission_version_id=version_id,
        start_node_id=s.node_id,
        state=state_json(s),
        maya_decision=decision,
        now=clock,
    )
    if attempt is None:
        raise RuntimeError("the veteran already has an open attempt on this mission")
    graded: list[GradedItem] = []
    answers = []
    for trace_step in trace.steps[:-1]:  # the last trace step is the ending (no action)
        if trace_step.node_id != s.node_id:
            raise RuntimeError(f"replay diverged at {s.node_id} (trace: {trace_step.node_id})")
        clock += timedelta(seconds=STEP_SECONDS)
        item = graph.item_at(s.node_id)
        if item is None:
            t = result(graph, s, CONTINUE, h)
            action: dict[str, Any] = {"kind": "continue"}
        else:
            wants_correct = trace_step.outcome == "correct"
            question_id, engine_action, option_id, text = _concrete_answer(
                session, version_id, item, wants_correct
            )
            t = result(graph, s, engine_action, h)
            if t.outcome != trace_step.outcome:
                raise RuntimeError(f"{item['id']}: replayed outcome != trace outcome")
            attempts_repo.save_answer(
                session,
                attempt_id=attempt.id,
                question_id=question_id,
                selected_option_id=option_id,
                text_answer=text,
                is_correct=wants_correct,
                hint_shown=decision == HINT,
                now=clock,
            )
            graded.append(GradedItem(item["skill"], item["cefr"], wants_correct))
            answers.append((item["id"], wants_correct, option_id, text))
            action = {"kind": "answer", "item_id": item["id"]}
        decision = arrival_decision(graph, h, t.next_state, via_rescue=t.maya_decision == RESCUE)
        attempts_repo.append_step(
            session,
            attempt,
            from_node_id=s.node_id,
            to_node_id=t.next_state.node_id,
            on_event=t.edge.on,
            action=action,
            minutes_cost=t.minutes_cost,
            minutes_left_after=t.next_state.minutes_left,
            maya_decision=decision,
            state_after=state_json(t.next_state),
            now=clock,
        )
        s = t.next_state
    if not is_goal(graph, s):
        raise RuntimeError("the replay did not reach an ending")

    attempts_repo.mark_attempt_completed(session, attempt, ending_node_id=s.node_id, now=clock)
    outcome = grade(graded)
    attempts_repo.save_skill_scores(
        session,
        attempt.id,
        [
            attempts_repo.SkillScoreIn(skill, right, total, value)
            for skill, (right, total, value) in outcome.skills.items()
        ],
    )
    submitted_at = clock + timedelta(seconds=40)
    attempts_repo.finish_attempt(
        session,
        attempt,
        score_pct=outcome.score_pct,
        correct_count=outcome.correct,
        incorrect_count=outcome.incorrect,
        suggested_cefr=outcome.suggested_cefr,
        now=submitted_at,
    )
    coach_repo.save_coach_feedback(
        session,
        attempt_id=attempt.id,
        provider="mock",
        model=None,
        prompt_version=SEED_PROMPT_VERSION,
        status="fallback",
        content=mock_feedback(outcome, user.display_name),
        latency_ms=0,
    )
    return SeededAttempt(attempt.id, trace.seed, trace, answers)


def seed_veteran_history(
    session: Session, user: User, mission_id: str, now: datetime | None = None
) -> list[SeededAttempt]:
    """Idempotent: does nothing if the veteran already has submitted attempts on the active
    version. Seeded history on an older version (e.g. the fixture) is demo data owned by the
    seed: it is deleted and regenerated so the veteran's reports show the current content."""
    now = now or datetime.now(UTC)
    version = missions_repo.get_active_mission_version(session, mission_id)
    if version is None:
        raise RuntimeError(f"mission '{mission_id}' has no version to seed history on")

    stale = session.scalar(
        select(Attempt.id)
        .where(Attempt.user_id == user.id, Attempt.mission_version_id != version.id)
        .limit(1)
    )
    if stale is not None:
        session.execute(delete(Attempt).where(Attempt.user_id == user.id))
        session.execute(delete(CoachMemory).where(CoachMemory.user_id == user.id))
        session.expire_all()
    already = session.scalar(
        select(Attempt.id).where(Attempt.user_id == user.id, Attempt.status == "submitted").limit(1)
    )
    if already is not None:
        return []

    content = missions_repo.load_mission_content(session, version.id)
    graph = build_graph(content.items_doc, content.mission_doc)
    h = compute_h(graph)
    student = SimulatedStudent(demo.VETERAN_PROFILE)
    traces = [run(graph, h, student, seed) for seed in demo.VETERAN_SEEDS]
    # Oldest attempt = lowest score, so the Progress page shows a trend (stable, deterministic).
    traces.sort(key=lambda t: t.correct)

    seeded = [
        replay_trace(
            session,
            user=user,
            mission_id=mission_id,
            version_id=version.id,
            graph=graph,
            h=h,
            trace=trace,
            started_at=_evening(now, days_ago),
        )
        for trace, days_ago in zip(traces, demo.VETERAN_DAYS_AGO, strict=True)
    ]

    notes = []
    last_feedback = None
    for item in reversed(seeded):  # newest first
        feedback = coach_repo.get_coach_feedback(session, item.attempt_id)
        assert feedback is not None
        last_feedback = last_feedback or feedback
        notes.append(
            {"text": feedback.content["memory_note"], "created_at": feedback_time(session, item)}
        )
    coach_repo.save_coach_memory(
        session,
        user.id,
        sessions_count=len(seeded),
        notes=notes[:5],
        next_greeting=last_feedback.content["next_greeting"] if last_feedback else None,
        now=now,
    )
    return seeded


def feedback_time(session: Session, item: SeededAttempt) -> str:
    attempt = session.get(Attempt, item.attempt_id)
    assert attempt is not None and attempt.submitted_at is not None
    return attempt.submitted_at.isoformat().replace("+00:00", "Z")
