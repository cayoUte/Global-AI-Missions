"""The coach seam (8-second budget, validation, fallback) and the login rate limiter."""

import time
from types import SimpleNamespace

import pytest

from app.core.errors import DomainError
from app.core.rate_limit import SlidingWindowLimiter
from app.services import coach

REQUEST = coach.CoachRequest(
    first_name="Ana",
    suggested_cefr="A2",
    score_pct=70,
    skills=[
        {"skill": "grammar", "correct": 3, "total": 4, "pct": 75},
        {"skill": "listening", "correct": 1, "total": 2, "pct": 50},
        {"skill": "reading", "correct": 2, "total": 2, "pct": 100},
        {"skill": "vocabulary", "correct": 1, "total": 2, "pct": 50},
    ],
    strength="reading",
    challenge="listening",
    missed=[],
    ending_key="made_it",
    rescue_used=False,
    hints_received=0,
    sessions_count=0,
    last_notes=[],
    candidate_mission_ids=["night-radio", "dinner-for-two", "the-interview", "campus-day"],
    default_next_mission_id="night-radio",
)
GOOD = {
    "summary": "You can read short notices.",
    "strength": "reading",
    "challenge": "listening",
    "recommendation": "Listen for numbers first.",
    "next_mission_id": "night-radio",
    "memory_note": "Strong with signs.",
    "next_greeting": "Welcome back, Ana.",
}


def provider(generate, name="anthropic"):
    return lambda: SimpleNamespace(
        provider=name, model="m", prompt_version="v1", label="Claude", generate=generate
    )


def test_valid_provider_output_is_ready_with_the_adapters_label():
    result = coach.run_coach(REQUEST, provider(lambda req: dict(GOOD)))
    assert result.status == "ready" and result.content["provider_label"] == "Claude"
    assert result.provider == "anthropic" and result.prompt_version == "v1"


@pytest.mark.parametrize(
    "change",
    [
        {"strength": "grammar"},  # must echo the deterministic strength
        {"challenge": "reading"},
        {"next_mission_id": "the-last-train"},  # not a candidate
        {"summary": ""},
    ],
)
def test_invalid_output_falls_back(change):
    result = coach.run_coach(REQUEST, provider(lambda req: {**GOOD, **change}))
    assert result.status == "fallback" and result.provider == "mock"
    assert result.content["strength"] == "reading" and result.content["challenge"] == "listening"


def test_errors_and_timeouts_fall_back_within_the_budget():
    def slow(req):
        time.sleep(2)
        return GOOD

    def broken(req):
        raise RuntimeError("down")

    started = time.monotonic()
    assert coach.run_coach(REQUEST, provider(slow), budget_seconds=0.2).status == "fallback"
    assert time.monotonic() - started < 1.5
    assert coach.run_coach(REQUEST, provider(broken)).status == "fallback"
    assert coach.run_coach(REQUEST, lambda: None).status == "fallback"


def test_deterministic_feedback_follows_the_spec_templates():
    content = coach.deterministic_feedback(REQUEST)
    assert content["summary"].startswith("You can read short notices and messages")
    assert "You read signs, notices and messages quickly and well." in content["summary"]
    assert content["recommendation"].startswith("Listen for numbers first")
    assert content["next_mission_id"] == "night-radio"
    assert coach.default_next_mission("grammar", REQUEST.candidate_mission_ids) == "the-interview"


def test_rate_limiter_window():
    now = [0.0]
    limiter = SlidingWindowLimiter(5, 60, clock=lambda: now[0])
    for _ in range(5):
        limiter.hit("ip|a@b.c")
    with pytest.raises(DomainError) as exc:
        limiter.hit("ip|a@b.c")
    assert exc.value.details == {"retry_after_seconds": 60}
    limiter.hit("ip|other@b.c")  # separate bucket
    now[0] = 60.0
    limiter.hit("ip|a@b.c")  # the window slid
