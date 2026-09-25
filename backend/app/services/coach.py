"""The coach seam used by submit phase 2 (SHARED_CONTEXT §6).

- Called only AFTER the grading transaction has committed, never under a lock or transaction.
- 8-second total budget. Any failure, timeout or invalid output -> the deterministic fallback
  (status "fallback"), so the report always renders.
- strength / challenge must echo the deterministic values; next_mission_id must be a candidate.

The ai-coach-engineer plugs the real provider in through app.ai: if `app.ai.get_coach_provider`
exists it is used, otherwise the deterministic feedback below is the whole coach. A provider is
any object with `provider`, `model`, `prompt_version`, `label` attributes and
`generate(request: CoachRequest) -> dict` (the strict JSON of SHARED_CONTEXT §6).
At scale this seam becomes a queue consumer; the report already renders without a feedback row.
"""

import logging
import time
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass, field
from typing import Any

from app.services.leveling import cefr_label

logger = logging.getLogger(__name__)

COACH_BUDGET_SECONDS = 8.0
FALLBACK_PROVIDER = "mock"
FALLBACK_LABEL = "Maya's notebook"
FALLBACK_PROMPT_VERSION = "deterministic-v1"

# PD-010: the challenge skill -> the catalog mission that trains it.
MISSION_FOR_SKILL: dict[str, str] = {
    "grammar": "the-interview",
    "vocabulary": "dinner-for-two",
    "reading": "campus-day",
    "listening": "night-radio",
}
# ASSESSMENT_SPEC §7.2-§7.4: the reference register for the deterministic feedback.
CAN_DO: dict[str, str] = {
    "PRE_A1": "You can understand some very common words and numbers when people speak slowly "
    "and clearly.",
    "A1": "You can understand simple signs, numbers and short questions, like asking the way in "
    "a station.",
    "A2": "You can read short notices and messages and do simple travel tasks, like buying the "
    "right ticket.",
    "B1": "You can follow clear announcements and explain what happened to you, even when plans "
    "change.",
    "B2": "You can understand what people mean even when they don't say it directly, and talk "
    "about what could have happened.",
}
SKILL_BANDS: dict[str, tuple[str, str, str]] = {  # strong >= 75 · developing 50-74 · focus < 50
    "grammar": (
        "You build clear sentences, even with tricky verb forms.",
        "Your sentences mostly work. Some verb forms still need care.",
        "Verb forms are slowing you down. Short, clear sentences come first.",
    ),
    "listening": (
        "You catch numbers and details in announcements.",
        "You get the main idea when people speak. Some details slip past.",
        "Conversations are moving faster than you are.",
    ),
    "reading": (
        "You read signs, notices and messages quickly and well.",
        'You understand most of what you read. Small details, like times and "if", can trip you '
        "up.",
        "Written notices are hard for now. Read slowly and look for the key words.",
    ),
    "vocabulary": (
        "You recognize common vocabulary quickly.",
        "You know many everyday words. Phrases with two meanings are still tricky.",
        "New words are your next step. Learn travel words in small groups.",
    ),
}
RECOMMENDATIONS: dict[str, str] = {
    "grammar": "Say one sentence about your day each evening, and check the verb.",
    "listening": "Listen for numbers first, then names. Play short announcements twice.",
    "reading": 'Read the whole notice once, then look for times and the word "if".',
    "vocabulary": 'Learn words in pairs that go together, like "single" and "return".',
}


def _band_line(skill: str, pct: int) -> str:
    strong, developing, focus = SKILL_BANDS[skill]
    return strong if pct >= 75 else developing if pct >= 50 else focus


@dataclass(frozen=True)
class CoachRequest:
    """Everything the coach may know. Built by the backend after grading; no answer keys of an
    open attempt (this attempt is already closed), no personal data beyond the first name."""

    first_name: str
    suggested_cefr: str
    score_pct: int
    skills: Sequence[Mapping[str, Any]]  # [{skill, correct, total, pct}]
    strength: str
    challenge: str
    missed: Sequence[Mapping[str, Any]]  # [{skill, cefr, prompt, explanation}]
    ending_key: str
    rescue_used: bool
    hints_received: int
    sessions_count: int
    last_notes: Sequence[str]
    candidate_mission_ids: Sequence[str]
    default_next_mission_id: str


@dataclass(frozen=True)
class CoachResult:
    content: dict[str, str]  # summary, strength, challenge, recommendation, next_mission_id,
    #                          memory_note, next_greeting, provider_label
    status: str  # ready | fallback
    provider: str
    model: str | None
    prompt_version: str
    latency_ms: int
    extra: dict[str, Any] = field(default_factory=dict)


def default_next_mission(challenge: str, candidates: Sequence[str]) -> str:
    preferred = MISSION_FOR_SKILL.get(challenge)
    if preferred in candidates:
        return preferred
    return candidates[0] if candidates else preferred or ""


def deterministic_feedback(req: CoachRequest) -> dict[str, str]:
    """The mock / fallback, assembled from ASSESSMENT_SPEC §7 (can-do line, the strength's strong
    line, the challenge's line for its own band). Built only from the grading result."""
    pct = {row["skill"]: int(row["pct"]) for row in req.skills}
    level = cefr_label(req.suggested_cefr)
    summary = " ".join(
        part
        for part in (
            CAN_DO.get(req.suggested_cefr, ""),
            SKILL_BANDS[req.strength][0] if req.strength in SKILL_BANDS else "",
            _band_line(req.challenge, pct.get(req.challenge, 0))
            if req.challenge in SKILL_BANDS
            else "",
        )
        if part
    )
    greeting_middle = "Our first night went well. " if req.sessions_count == 0 else ""
    return {
        "summary": summary,
        "strength": req.strength,
        "challenge": req.challenge,
        "recommendation": RECOMMENDATIONS.get(req.challenge, "Practise a little every day."),
        "next_mission_id": req.default_next_mission_id,
        "memory_note": f"Strong in {req.strength}; {req.challenge} needs practice ({level}).",
        "next_greeting": (
            f"Welcome back, {req.first_name}. {greeting_middle}"
            f"Tonight, let's work on {req.challenge}."
        ),
        "provider_label": FALLBACK_LABEL,
    }


def fallback_result(req: CoachRequest, latency_ms: int = 0, reason: str = "") -> CoachResult:
    return CoachResult(
        content=deterministic_feedback(req),
        status="fallback",
        provider=FALLBACK_PROVIDER,
        model=None,
        prompt_version=FALLBACK_PROMPT_VERSION,
        latency_ms=latency_ms,
        extra={"reason": reason} if reason else {},
    )


_REQUIRED_TEXT = ("summary", "recommendation", "memory_note", "next_greeting")


def validate_output(req: CoachRequest, output: Any) -> dict[str, str] | None:
    """The provider's output if it respects the contract, else None (-> fallback)."""
    if not isinstance(output, Mapping):
        return None
    if output.get("strength") != req.strength or output.get("challenge") != req.challenge:
        return None
    if output.get("next_mission_id") not in req.candidate_mission_ids:
        return None
    for key in _REQUIRED_TEXT:
        value = output.get(key)
        if not isinstance(value, str) or not value.strip() or len(value) > 800:
            return None
    return {key: str(output[key]) for key in (*_REQUIRED_TEXT, "strength", "challenge",
                                             "next_mission_id")}


def _load_provider() -> Any | None:
    try:
        from app.ai import get_coach_provider  # type: ignore[attr-defined]
    except ImportError:
        return None
    return get_coach_provider()


def run_coach(
    req: CoachRequest,
    provider_loader: Callable[[], Any | None] = _load_provider,
    budget_seconds: float = COACH_BUDGET_SECONDS,
) -> CoachResult:
    """Never raises: the worst case is the deterministic fallback."""
    started = time.monotonic()
    elapsed_ms = lambda: int((time.monotonic() - started) * 1000)  # noqa: E731
    try:
        provider = provider_loader()
    except Exception:  # a misconfigured provider must not break submit
        logger.exception("Coach provider could not be created; using the fallback")
        return fallback_result(req, elapsed_ms(), "provider_error")
    if provider is None or getattr(provider, "provider", FALLBACK_PROVIDER) == FALLBACK_PROVIDER:
        return fallback_result(req, elapsed_ms())
    pool = ThreadPoolExecutor(max_workers=1)
    try:
        output = pool.submit(provider.generate, req).result(timeout=budget_seconds)
    except FutureTimeout:
        logger.warning("Coach timed out after %.1fs; using the fallback", budget_seconds)
        return fallback_result(req, elapsed_ms(), "timeout")
    except Exception:
        logger.exception("Coach failed; using the fallback")
        return fallback_result(req, elapsed_ms(), "error")
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
    content = validate_output(req, output)
    if content is None:
        logger.warning("Coach output failed validation; using the fallback")
        return fallback_result(req, elapsed_ms(), "invalid_output")
    content["provider_label"] = str(getattr(provider, "label", provider.provider))
    return CoachResult(
        content=content,
        status="ready",
        provider=str(provider.provider),
        model=getattr(provider, "model", None),
        prompt_version=str(getattr(provider, "prompt_version", "unknown")),
        latency_ms=elapsed_ms(),
    )
