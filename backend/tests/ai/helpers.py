"""Shared contexts and fakes for the coach tests. No database, no network."""

import json
from types import SimpleNamespace

from app.ai.ports import CoachContext
from app.ai.service import build_context

CANDIDATES = ("night-radio", "dinner-for-two", "the-interview", "campus-day")
SKILLS_A2 = [
    {"skill": "grammar", "correct": 3, "total": 4, "pct": 75},
    {"skill": "listening", "correct": 1, "total": 2, "pct": 50},
    {"skill": "reading", "correct": 2, "total": 2, "pct": 100},
    {"skill": "vocabulary", "correct": 1, "total": 2, "pct": 50},
]
SKILLS_LEO = [
    {"skill": "grammar", "correct": 3, "total": 4, "pct": 75},
    {"skill": "listening", "correct": 1, "total": 2, "pct": 50},
    {"skill": "reading", "correct": 1, "total": 2, "pct": 50},
    {"skill": "vocabulary", "correct": 2, "total": 2, "pct": 100},
]
LEO_NOTES = (
    "Strong in vocabulary; listening needs practice (A2, 60%).",
    "Strong in vocabulary; reading needs practice (A2, 60%).",
    "Strong in grammar; listening needs practice (A1, 40%).",
    "Strong in vocabulary; listening needs practice (A1, 30%).",
)


def make_context(**overrides) -> CoachContext:
    args = {
        "first_name": "Ana",
        "suggested_cefr": "A2",
        "score_pct": 70,
        "skills": SKILLS_A2,
        "strength": "reading",
        "challenge": "listening",
        "missed": [
            {
                "skill": "listening",
                "cefr": "B1",
                "prompt": "What did the announcement say?",
                "explanation": "The barriers were out of order.",
            }
        ],
        "ending_key": "made_it",
        "rescue_used": False,
        "hints_received": 0,
        "memory": None,
        "candidate_mission_ids": CANDIDATES,
    }
    args.update(overrides)
    return build_context(**args)


def good_output(ctx: CoachContext, **changes) -> dict:
    data = {
        "summary": "You can read short notices. Fast announcements were harder tonight.",
        "strength": ctx.strength,
        "challenge": ctx.challenge,
        "recommendation": "Listen for numbers first, then names.",
        "next_mission_id": ctx.default_next_mission_id,
        "memory_note": f"Strong in {ctx.strength}; {ctx.challenge} needs practice.",
        "next_greeting": f"Welcome back, {ctx.first_name}. Tonight, listen for the numbers.",
    }
    data.update(changes)
    return data


class FakeMessages:
    """Stands in for anthropic.Anthropic().messages; records every call."""

    def __init__(self, text=None, stop_reason="end_turn", error=None):
        self.text, self.stop_reason, self.error = text, stop_reason, error
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return SimpleNamespace(
            stop_reason=self.stop_reason,
            content=[SimpleNamespace(type="text", text=self.text)],
            usage=SimpleNamespace(input_tokens=1800, output_tokens=240),
        )


def fake_client(text=None, **kwargs) -> SimpleNamespace:
    return SimpleNamespace(messages=FakeMessages(text, **kwargs))


def as_json(data: dict) -> str:
    return json.dumps(data)
