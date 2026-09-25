"""The coach service: build the context, generate feedback with a budget, update memory.

Runs after the grading commit, never inside a transaction (SHARED_CONTEXT §6): these functions
do no I/O except the provider call, and they never raise to the caller. The worst case is the
deterministic mock, reported as status "fallback".

The backend's submit phase 2 (app.services.coach.run_coach) reaches the same providers through
factory.get_coach_provider(); context_from_request() is the bridge from its CoachRequest.
"""

import logging
import time
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

from app.ai.mock_provider import MOCK_LABEL, MockCoachProvider
from app.ai.ports import (
    MAX_NOTES,
    CoachContext,
    CoachFeedback,
    CoachProvider,
    MissedItem,
    SkillScore,
)
from app.ai.templates import MISSION_FOR_SKILL

logger = logging.getLogger(__name__)

BUDGET_SECONDS = 8.0
Status = Literal["ready", "fallback"]


# --- context ------------------------------------------------------------------------------------


@dataclass(frozen=True)
class MemoryState:
    """Coach memory as the service sees it. notes = newest first, each {text, created_at}."""

    sessions_count: int = 0
    notes: tuple[Mapping[str, Any], ...] = ()
    next_greeting: str | None = None

    def note_texts(self) -> list[str]:
        return [str(n.get("text", "")) if isinstance(n, Mapping) else str(n) for n in self.notes]


def default_next_mission(challenge: str, candidates: Sequence[str]) -> str:
    """PD-010: the mission that trains the challenge skill, if it is a candidate."""
    preferred = MISSION_FOR_SKILL.get(challenge)
    if preferred in candidates:
        return str(preferred)
    return candidates[0] if candidates else ""


def build_context(
    *,
    first_name: str,
    suggested_cefr: str,
    score_pct: int,
    skills: Sequence[Mapping[str, Any]],
    strength: str,
    challenge: str,
    missed: Sequence[Mapping[str, Any]],
    ending_key: str,
    rescue_used: bool,
    hints_received: int,
    memory: MemoryState | None,
    candidate_mission_ids: Sequence[str],
) -> CoachContext:
    """From the graded attempt (already committed), the coach memory and the catalog. The
    strength / challenge are the deterministic values of ASSESSMENT_SPEC §7.1."""
    memory = memory or MemoryState()
    return CoachContext(
        first_name=first_name,
        suggested_cefr=suggested_cefr,  # type: ignore[arg-type]  # validated by pydantic
        score_pct=score_pct,
        skills=tuple(SkillScore.model_validate(dict(s)) for s in skills),
        strength=strength,  # type: ignore[arg-type]
        challenge=challenge,  # type: ignore[arg-type]
        missed=tuple(
            MissedItem.model_validate({k: m[k] for k in m if k in MissedItem.model_fields})
            for m in missed
        ),
        ending_key=ending_key,
        rescue_used=rescue_used,
        hints_received=hints_received,
        sessions_count=memory.sessions_count + 1,  # this mission is the next session
        last_notes=tuple(memory.note_texts()[:MAX_NOTES]),
        candidate_mission_ids=tuple(candidate_mission_ids),
        default_next_mission_id=default_next_mission(challenge, candidate_mission_ids),
    )


def context_from_request(request: Any) -> CoachContext:
    """Bridge from app.services.coach.CoachRequest (duck-typed: no import of services here)."""
    return build_context(
        first_name=request.first_name,
        suggested_cefr=request.suggested_cefr,
        score_pct=request.score_pct,
        skills=request.skills,
        strength=request.strength,
        challenge=request.challenge,
        missed=request.missed,
        ending_key=request.ending_key,
        rescue_used=request.rescue_used,
        hints_received=request.hints_received,
        memory=MemoryState(
            sessions_count=request.sessions_count,
            notes=tuple({"text": t} for t in request.last_notes),
        ),
        candidate_mission_ids=request.candidate_mission_ids,
    )


# --- generation ---------------------------------------------------------------------------------


@dataclass(frozen=True)
class FeedbackMeta:
    provider: str
    provider_label: str
    model: str | None
    prompt_version: str
    status: Status
    latency_ms: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    fallback_reason: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


_MOCK = MockCoachProvider()


def _fallback(
    context: CoachContext, started: float, reason: str | None
) -> tuple[CoachFeedback, FeedbackMeta]:
    feedback = _MOCK.generate(context)
    return feedback, FeedbackMeta(
        provider=_MOCK.provider,
        provider_label=MOCK_LABEL,
        model=None,
        prompt_version=_MOCK.prompt_version,
        status="fallback",
        latency_ms=int((time.monotonic() - started) * 1000),
        fallback_reason=reason,
    )


def generate_feedback(
    context: CoachContext,
    provider: CoachProvider | None = None,
    budget_seconds: float = BUDGET_SECONDS,
) -> tuple[CoachFeedback, FeedbackMeta]:
    """Never raises. Timeout, API error, malformed JSON or invalid output -> the mock, status
    fallback. The mock itself is also reported as fallback (it is not an LLM)."""
    started = time.monotonic()
    if provider is None or provider.provider == _MOCK.provider:
        return _fallback(context, started, None)
    pool = ThreadPoolExecutor(max_workers=1)
    try:
        output: Any = pool.submit(provider.generate, context).result(timeout=budget_seconds)
        # Re-validate whatever came back (a CoachFeedback or a raw mapping): never trusted.
        data = output.model_dump() if isinstance(output, CoachFeedback) else output
        feedback = CoachFeedback.validated(data, context)
        usage = getattr(output, "usage", None)
        if usage is not None:
            feedback.with_usage(usage)
    except FutureTimeout:
        logger.warning("coach %s timed out after %.1fs", provider.provider, budget_seconds)
        return _fallback(context, started, "timeout")
    except Exception as exc:  # provider errors, malformed JSON, validation failures
        logger.warning("coach %s failed (%s); using the fallback", provider.provider, exc)
        return _fallback(context, started, type(exc).__name__)
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
    return feedback, FeedbackMeta(
        provider=provider.provider,
        provider_label=provider.label,
        model=provider.model,
        prompt_version=provider.prompt_version,
        status="ready",
        latency_ms=int((time.monotonic() - started) * 1000),
        input_tokens=usage.input_tokens if usage else None,
        output_tokens=usage.output_tokens if usage else None,
    )


def deterministic_content(request: Any) -> dict[str, str]:
    """The mock's feedback for a backend CoachRequest, in the stored content shape (used by
    app.services.coach.deterministic_feedback for the demo default and every fallback)."""
    feedback = _MOCK.generate(context_from_request(request))
    return {**feedback.model_dump(), "provider_label": MOCK_LABEL}


# --- memory -------------------------------------------------------------------------------------


def update_memory(
    memory: MemoryState | None, feedback: CoachFeedback, now: datetime | None = None
) -> MemoryState:
    """One more session, the new note first and only the last 5 kept, the next greeting stored.
    Pure: the caller persists it once per attempt (only when its feedback row was written)."""
    memory = memory or MemoryState()
    note = {
        "text": feedback.memory_note,
        "created_at": (now or datetime.now(UTC)).isoformat(timespec="seconds"),
    }
    return MemoryState(
        sessions_count=memory.sessions_count + 1,
        notes=(note, *memory.notes)[:MAX_NOTES],
        next_greeting=feedback.next_greeting,
    )
