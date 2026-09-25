"""The deterministic coach: ASSESSMENT_SPEC §7 templates + what Maya's notebook remembers.

It is the demo default (no API key needed) and the fallback for every provider failure, so it
must be total: same context in, same feedback out, always valid. Its output is reported with
status "fallback" and the label "Maya's notebook" (PD-016).

Memory: the mock writes notes that start "Strong in X; Y needs practice", and reads them back
next time to say one concrete thing it remembers ("You usually do well with vocabulary."). It
never invents a memory: with no readable note it only welcomes the student back.
"""

import re

from app.ai.ports import CoachContext, CoachFeedback
from app.ai.templates import (
    CAN_DO,
    DOES_WELL_WITH,
    GREETING_TIPS,
    NUMBER_WORDS,
    RECOMMENDATIONS,
    SKILL_BANDS,
    STILL_HESITATES,
    band_line,
    cefr_label,
)

MOCK_PROVIDER = "mock"
MOCK_LABEL = "Maya's notebook"
MOCK_PROMPT_VERSION = "deterministic-v2"

_SKILL = r"(grammar|listening|reading|vocabulary)"
_STRONG = re.compile(rf"strong in {_SKILL}", re.IGNORECASE)
_NEEDS = re.compile(rf"{_SKILL} needs practice", re.IGNORECASE)
_ENDING_NOTES = {
    "made_it": "Caught the last train.",
    "made_it_with_maya": "Caught the last train with my shortcut.",
    "night_bus": "Took the night bus home with me.",
}


def _read_note(note: str) -> tuple[str | None, str | None]:
    strong, needs = _STRONG.search(note), _NEEDS.search(note)
    return (
        strong.group(1).lower() if strong else None,
        needs.group(1).lower() if needs else None,
    )


def memory_observations(ctx: CoachContext) -> list[str]:
    """At most two sentences, each grounded in a note Maya actually wrote (MAYA.md §8.6)."""
    if not ctx.is_returning:
        return []
    parsed = [_read_note(note) for note in ctx.last_notes]
    past_strengths = [s for s, _ in parsed if s]
    past_challenges = [c for _, c in parsed if c]
    sentences: list[str] = []

    times_strong = past_strengths.count(ctx.strength)
    if times_strong >= 2:
        sentences.append(f"You usually do well with {DOES_WELL_WITH[ctx.strength]}.")
    elif times_strong == 1:
        sentences.append(f"Once again, you did well with {DOES_WELL_WITH[ctx.strength]}.")

    last_challenge = parsed[0][1] if parsed else None
    if ctx.challenge in past_challenges:
        sentences.append(STILL_HESITATES[ctx.challenge])
    elif last_challenge and (ctx.pct(last_challenge) or 0) >= 75:
        sentences.append(
            f"Last time {last_challenge} was the hard part. Tonight it went much better."
        )
    return sentences[:2]


def _personal_line(ctx: CoachContext) -> str:
    if not ctx.is_returning:
        return f"Nice to meet you, {ctx.first_name}."
    observed = memory_observations(ctx)
    return " ".join(observed) if observed else f"Good to see you again, {ctx.first_name}."


def _next_greeting(ctx: CoachContext) -> str:
    hard, tip = GREETING_TIPS[ctx.challenge]
    if ctx.sessions_count >= 3:  # the next session is the 4th or later: familiar companion
        nights = NUMBER_WORDS.get(ctx.sessions_count, str(ctx.sessions_count))
        return (
            f"Welcome back, {ctx.first_name}. {nights} nights in London now. "
            f"Your {ctx.strength} is steady. Tonight, {tip}."
        )
    return f"Welcome back, {ctx.first_name}. Last time {hard}. Tonight, {tip}."


def compose_feedback(ctx: CoachContext) -> CoachFeedback:
    """ASSESSMENT_SPEC §7 assembly: can-do line, the strength's strong line, the challenge's line
    for its own band, then one personal line (first meeting or one memory)."""
    summary = " ".join(
        (
            CAN_DO[ctx.suggested_cefr] if ctx.suggested_cefr in CAN_DO else CAN_DO["B2"],
            SKILL_BANDS[ctx.strength][0],
            band_line(ctx.challenge, ctx.pct(ctx.challenge) or 0),
            _personal_line(ctx),
        )
    )
    memory_note = (
        f"Strong in {ctx.strength}; {ctx.challenge} needs practice "
        f"({cefr_label(ctx.suggested_cefr)}, {ctx.score_pct}%). "
        f"{_ENDING_NOTES.get(ctx.ending_key, '')}"
    ).strip()
    return CoachFeedback.validated(
        {
            "summary": summary,
            "strength": ctx.strength,
            "challenge": ctx.challenge,
            "recommendation": RECOMMENDATIONS[ctx.challenge],
            "next_mission_id": ctx.default_next_mission_id,
            "memory_note": memory_note,
            "next_greeting": _next_greeting(ctx),
        },
        ctx,
    )


class MockCoachProvider:
    """Deterministic, offline, free. Implements the CoachProvider port."""

    provider = MOCK_PROVIDER
    label = MOCK_LABEL
    model: str | None = None
    prompt_version = MOCK_PROMPT_VERSION

    def generate(self, context: CoachContext) -> CoachFeedback:
        return compose_feedback(context)
