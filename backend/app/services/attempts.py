"""The attempt lifecycle: start / resume, advance, answer and the two-phase submit.

The server is authoritative for everything: node, clock, flags, correctness, score and level.
The client only ever says "continue from node X" or "my answer at node X is Y".

Transactions (conventions §1: services own them):
- start, advance and answer each run in one short transaction; advance and answer take the
  attempt row lock (SELECT ... FOR UPDATE) and re-check before writing.
- submit runs in two phases: (1) grade + level under the row lock, commit; (2) with no lock and
  no transaction held, call the coach, store its feedback once, update coach memory once.

Synchronous on purpose: sync SQLAlchemy in FastAPI's thread pool is simple to read and debug.
At scale the coach call (the only slow step) moves to a queue; the rest is short DB work.
"""

import logging
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app import engine
from app.core.errors import DomainError, ErrorCode
from app.engine import CHECKPOINT, CONTINUE, CORRECT, HINT, RESCUE, Action, State
from app.repositories import attempts as attempts_repo
from app.repositories import missions as missions_repo
from app.schemas.attempts import AnswerRequest, AnswerResponse
from app.schemas.state import StateView
from app.services import content, feedback, grading, leveling
from app.services.content import LoadedMission
from app.services.state_view import to_state_view

logger = logging.getLogger(__name__)

FILL_BLANK_MAX = 80


# --- shared helpers (also used by report, world and progress) ---------------------------------


def parse_attempt_id(attempt_id: str) -> uuid.UUID:
    """A malformed UUID is indistinguishable from an unknown one: 404, never 422 (F-03)."""
    try:
        return uuid.UUID(attempt_id)
    except (ValueError, TypeError) as exc:
        raise DomainError(ErrorCode.NOT_FOUND, "Attempt not found.") from exc


def get_owned_attempt(session: Session, user: Any, attempt_id: str) -> Any:
    """The student's own attempt, or 404 (another user's attempt is 'not found', not 403)."""
    attempt = attempts_repo.get_owned_attempt(session, parse_attempt_id(attempt_id), user.id)
    if attempt is None:
        raise DomainError(ErrorCode.NOT_FOUND, "Attempt not found.")
    return attempt


def engine_state(attempt: Any) -> State:
    """attempts.state JSON + current_node_id -> the engine State (data-engineer's JSON shape)."""
    data: Mapping[str, Any] = attempt.state or {}
    return State(
        node_id=attempt.current_node_id,
        minutes_left=int(data.get("minutes_left", 0)),
        flags=frozenset(data.get("flags", ())),
        rescued=bool(data.get("rescued", False)),
        maya_mood=str(data.get("maya_mood", "curious")),
    )


def state_json(state: State) -> dict[str, Any]:
    return {
        "minutes_left": state.minutes_left,
        "flags": sorted(state.flags),
        "rescued": state.rescued,
        "maya_mood": state.maya_mood,
    }


def current_decision(session: Session, attempt: Any, loaded: LoadedMission) -> str:
    """Maya's decision on arrival at the current node, as persisted on the latest step."""
    last = attempts_repo.get_last_step(session, attempt.id)
    if last is not None and last.to_node_id == attempt.current_node_id:
        return str(last.maya_decision)
    return engine.arrival_decision(loaded.graph, loaded.h, engine_state(attempt))


def build_state_view(
    session: Session, attempt: Any, loaded: LoadedMission | None = None, decision: str | None = None
) -> StateView:
    loaded = loaded or content.get_loaded_mission(session, attempt.mission_version_id)
    mission = missions_repo.get_mission(session, attempt.mission_id)
    return to_state_view(
        attempt_id=str(attempt.id),
        mission_id=attempt.mission_id,
        mission_title=mission.title if mission else loaded.graph.title,
        status=attempt.status,
        graph=loaded.graph,
        state=engine_state(attempt),
        decision=decision or current_decision(session, attempt, loaded),
    )


def conflict(session: Session, code: ErrorCode, message: str, attempt: Any) -> DomainError:
    """Every 409 on an attempt endpoint carries the server's truth in details.state (F-02).
    The attempt is re-read first: a concurrent request may have just committed a move (BUG-002)."""
    session.refresh(attempt)
    view = build_state_view(session, attempt)
    return DomainError(code, message, {"state": view.model_dump(mode="json")})


# --- start / resume ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StartResult:
    view: StateView
    created: bool


def start_attempt(session: Session, user: Any, mission_id: str) -> StartResult:
    """Return the OPEN attempt (in_progress, or completed and not submitted) or create one."""
    from app.services import world  # local import: world also uses this module's helpers

    mission = missions_repo.get_mission(session, mission_id)
    if mission is None or not mission.playable or not world.unlock_met(session, user, mission):
        raise DomainError(ErrorCode.NOT_FOUND, "Mission not found.")
    existing = attempts_repo.get_open_attempt(session, user.id, mission_id)
    if existing is not None:
        return StartResult(build_state_view(session, existing), created=False)
    version = missions_repo.get_active_mission_version(session, mission_id)
    if version is None:
        raise DomainError(ErrorCode.NOT_FOUND, "Mission not found.")
    loaded = content.get_loaded_mission(session, version.id)
    state = engine.initial_state(loaded.graph)
    decision = engine.arrival_decision(loaded.graph, loaded.h, state)
    attempt = attempts_repo.create_attempt(
        session,
        user_id=user.id,
        mission_id=mission_id,
        mission_version_id=version.id,
        start_node_id=state.node_id,
        state=state_json(state),
        maya_decision=decision,
    )
    if attempt is None:  # a concurrent start won the one-open-attempt index: return the winner
        winner = attempts_repo.get_open_attempt(session, user.id, mission_id)
        if winner is None:
            raise DomainError(ErrorCode.INTERNAL_ERROR, "Could not start the attempt.")
        return StartResult(build_state_view(session, winner), created=False)
    session.commit()
    return StartResult(build_state_view(session, attempt, loaded, decision), created=True)


def get_state(session: Session, user: Any, attempt_id: str) -> StateView:
    """Resume after a reload or a lost connection: the server's current truth."""
    return build_state_view(session, get_owned_attempt(session, user, attempt_id))


# --- advance (CONTINUE) -----------------------------------------------------------------------


def _check_advance(session: Session, attempt: Any, node_id: str, loaded: LoadedMission) -> None:
    if attempt.status != "in_progress":
        raise conflict(session, ErrorCode.ATTEMPT_NOT_IN_PROGRESS, "Attempt is closed.", attempt)
    kind = loaded.graph.kind(attempt.current_node_id)
    if node_id != attempt.current_node_id or kind in (CHECKPOINT, "ending"):
        raise conflict(session, ErrorCode.NODE_OUT_OF_SEQUENCE, "Not the current node.", attempt)


def advance(session: Session, user: Any, attempt_id: str, node_id: str) -> StateView:
    attempt = get_owned_attempt(session, user, attempt_id)
    loaded = content.get_loaded_mission(session, attempt.mission_version_id)
    _check_advance(session, attempt, node_id, loaded)
    attempt = _lock(session, user, attempt)
    _check_advance(session, attempt, node_id, loaded)  # a concurrent request may have moved on
    before = engine_state(attempt)
    step = engine.result(loaded.graph, before, CONTINUE, loaded.h)
    decision = engine.arrival_decision(loaded.graph, loaded.h, step.next_state)
    _persist_move(session, attempt, loaded, before, step, {"kind": "continue"}, decision)
    session.commit()
    return build_state_view(session, attempt, loaded, decision)


# --- answer -----------------------------------------------------------------------------------


def answer(session: Session, user: Any, attempt_id: str, req: AnswerRequest) -> AnswerResponse:
    """api-contract §5.10, in its fixed order: shape (Pydantic) -> 404 -> 409 locked -> 409 not
    in progress -> 409 out of sequence -> 422 item rules -> row lock + re-check -> grade, RESULT,
    persist, commit. Nothing is locked or written before the request is known to be valid.
    The LLM is never called here."""
    attempt = get_owned_attempt(session, user, attempt_id)  # 2. no row lock yet
    loaded = content.get_loaded_mission(session, attempt.mission_version_id)
    graph = loaded.graph
    item = graph.item_at(req.node_id) if req.node_id in graph.nodes else None
    question_id = (
        missions_repo.get_question_id(session, attempt.mission_version_id, item["id"])
        if item is not None
        else None
    )
    _check_answer(session, attempt, req.node_id, question_id, loaded)  # 3-5
    action = _answer_action(item, req)  # 6 (item is not None past step 5)
    attempt = _lock(session, user, attempt)  # 7
    _check_answer(session, attempt, req.node_id, question_id, loaded)
    assert item is not None and question_id is not None
    before = engine_state(attempt)
    hint_shown = current_decision(session, attempt, loaded) == HINT
    step = engine.result(graph, before, action, loaded.h)  # 8. grades on the server
    saved = attempts_repo.save_answer(
        session,
        attempt_id=attempt.id,
        question_id=question_id,
        selected_option_id=(
            missions_repo.get_option_id(session, question_id, req.option_id)
            if req.option_id is not None
            else None
        ),
        text_answer=req.text.strip() if req.text is not None else None,
        is_correct=step.outcome == CORRECT,
        hint_shown=hint_shown,
    )
    if saved is None:  # the unique (attempt, question) index caught a concurrent Confirm
        session.rollback()
        raise conflict(session, ErrorCode.CHECKPOINT_LOCKED, "Already answered.", attempt)
    decision = engine.arrival_decision(
        graph, loaded.h, step.next_state, via_rescue=step.maya_decision == RESCUE
    )
    action_json = {"kind": "answer", "item_id": item["id"]}
    _persist_move(session, attempt, loaded, before, step, action_json, decision)
    session.commit()
    view = build_state_view(session, attempt, loaded, decision)
    return AnswerResponse(maya_line=step.maya_line, state=view)


def _check_answer(
    session: Session, attempt: Any, node_id: str, question_id: int | None, loaded: LoadedMission
) -> None:
    if question_id is not None and attempts_repo.answer_exists(session, attempt.id, question_id):
        raise conflict(session, ErrorCode.CHECKPOINT_LOCKED, "Already answered.", attempt)
    if attempt.status != "in_progress":
        raise conflict(session, ErrorCode.ATTEMPT_NOT_IN_PROGRESS, "Attempt is closed.", attempt)
    current = attempt.current_node_id
    if node_id != current or loaded.graph.kind(current) != CHECKPOINT:
        raise conflict(session, ErrorCode.NODE_OUT_OF_SEQUENCE, "Not the current node.", attempt)


def _answer_action(item: Mapping[str, Any] | None, req: AnswerRequest) -> Action:
    """Item rules (step 6). A rejection is a 422 and the checkpoint stays answerable."""
    if item is None:  # unreachable after _check_answer; kept for type narrowing
        raise _invalid("node_id", "Not a checkpoint.")
    if item["type"] == "fill_blank":
        if req.text is None:
            raise _invalid("text", "This checkpoint needs a typed answer.")
        if not 1 <= len(engine.normalize_answer(req.text)) <= FILL_BLANK_MAX:
            raise _invalid("text", f"Type between 1 and {FILL_BLANK_MAX} characters.")
        return Action("type", req.text)
    if req.option_id is None:
        raise _invalid("option_id", "This checkpoint needs one of its options.")
    if req.option_id not in {option["id"] for option in item["options"] or ()}:
        raise _invalid("option_id", "Not an option of this checkpoint.")
    return Action("choose", req.option_id)


def _invalid(field: str, message: str) -> DomainError:
    return DomainError(
        ErrorCode.VALIDATION_ERROR,
        "Invalid answer.",
        {"errors": [{"field": field, "message": message}]},
    )


# --- submit (two phases) ----------------------------------------------------------------------


def submit(session: Session, user: Any, attempt_id: str) -> None:
    """Grades exactly once; safe to retry and to race. The caller then renders the Report."""
    attempt = get_owned_attempt(session, user, attempt_id)
    if attempt.status == "in_progress":
        raise conflict(session, ErrorCode.MISSION_NOT_FINISHED, "Mission not finished.", attempt)
    # Phase 1: one short transaction under the row lock.
    attempt = _lock(session, user, attempt)
    if attempt.status == "completed":
        loaded = content.get_loaded_mission(session, attempt.mission_version_id)
        _grade_and_level(session, attempt, loaded)
    session.commit()  # also releases the lock when it was already submitted
    # Phase 2: after the commit, no lock and no open transaction while the coach runs.
    try:
        feedback.ensure_feedback(session, user, attempt.id)
    except Exception:  # the report renders the deterministic fallback without a row
        logger.exception("Coach phase failed after grading; the report uses the fallback")
        session.rollback()


def _grade_and_level(session: Session, attempt: Any, loaded: LoadedMission) -> None:
    graded = graded_items(session, attempt, loaded)
    result = grading.grade_attempt(graded)
    level = leveling.suggest_level(result.score_pct, result.by_cefr)
    attempts_repo.save_skill_scores(
        session,
        attempt.id,
        [
            attempts_repo.SkillScoreIn(skill=s.skill, correct=s.correct, total=s.total, pct=s.pct)
            for s in result.skills
        ],
    )
    attempts_repo.finish_attempt(
        session,
        attempt,
        score_pct=result.score_pct,
        correct_count=result.correct,
        incorrect_count=result.incorrect,
        suggested_cefr=level.cefr,
    )


def graded_items(session: Session, attempt: Any, loaded: LoadedMission) -> list[grading.GradedItem]:
    """Every item of the mission with the outcome stored when its answer was locked. The total
    is always the number of items (a missing answer, impossible by design, counts as incorrect)."""
    stored = {
        row.item_id: bool(row.is_correct)
        for row in attempts_repo.list_attempt_answers(session, attempt.id)
    }
    return [
        grading.GradedItem(item_id, item["skill"], item["cefr"], stored.get(item_id, False))
        for item_id, item in loaded.graph.items.items()
    ]


# --- internals --------------------------------------------------------------------------------


def _lock(session: Session, user: Any, attempt: Any) -> Any:
    locked = attempts_repo.lock_attempt_for_update(session, attempt.id, user.id)
    if locked is None:
        raise DomainError(ErrorCode.NOT_FOUND, "Attempt not found.")
    return locked


def _persist_move(
    session: Session,
    attempt: Any,
    loaded: LoadedMission,
    before: State,
    step: Any,
    action: dict[str, Any],
    decision: str,
) -> None:
    """Append the step (which also moves the attempt head) and close the story at an ending."""
    after: State = step.next_state
    attempts_repo.append_step(
        session,
        attempt,
        from_node_id=before.node_id,
        to_node_id=after.node_id,
        on_event=step.edge.on,
        action=action,
        minutes_cost=step.minutes_cost,
        minutes_left_after=after.minutes_left,
        maya_decision=decision,
        state_after=state_json(after),
    )
    if engine.is_goal(loaded.graph, after):
        attempts_repo.mark_attempt_completed(session, attempt, ending_node_id=after.node_id)
