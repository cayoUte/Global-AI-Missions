"""Scoring for SEEDED history only (the veteran's past attempts).

This mirrors the SHARED_CONTEXT §4 rules so the seed can write complete submitted attempts
without the API. The authoritative implementation for real attempts is the backend's
app/services/grading.py + leveling.py (backend-api-engineer). When those exist, the seed should
call them instead and this module should be deleted, so the rule lives in one place.
"""

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

SCORED_SKILLS = ("grammar", "listening", "reading", "vocabulary")  # fixed display order
EVIDENCE_LEVELS = ("A1", "A2", "B1", "B2")
LEVEL_ORDER = ("PRE_A1", "A1", "A2", "B1", "B2")  # this mission suggests at most B2
BANDS = ((85, "B2"), (70, "B1"), (50, "A2"), (30, "A1"), (0, "PRE_A1"))
NEXT_MISSION_BY_CHALLENGE = {  # PD-010
    "grammar": "the-interview",
    "vocabulary": "dinner-for-two",
    "reading": "campus-day",
    "listening": "night-radio",
}


def pct(correct: int, total: int) -> int:
    """100 * correct / total, rounded half up, as an integer (api-contract §1)."""
    return (200 * correct + total) // (2 * total)


@dataclass(frozen=True)
class GradedItem:
    skill: str
    cefr: str
    correct: bool


@dataclass(frozen=True)
class Result:
    correct: int
    incorrect: int
    score_pct: int
    skills: dict[str, tuple[int, int, int]]  # skill -> (correct, total, pct)
    suggested_cefr: str
    strength: str
    challenge: str


def grade(items: Iterable[GradedItem]) -> Result:
    items = list(items)
    correct = sum(i.correct for i in items)
    score = pct(correct, len(items))
    skills = {}
    for skill in SCORED_SKILLS:
        of_skill = [i for i in items if i.skill == skill]
        if of_skill:
            right = sum(i.correct for i in of_skill)
            skills[skill] = (right, len(of_skill), pct(right, len(of_skill)))
    ranked = sorted(skills, key=lambda s: (-skills[s][2], SCORED_SKILLS.index(s)))
    return Result(
        correct=correct,
        incorrect=len(items) - correct,
        score_pct=score,
        skills=skills,
        suggested_cefr=suggest_level(score, items),
        strength=ranked[0],
        challenge=sorted(skills, key=lambda s: (skills[s][2], SCORED_SKILLS.index(s)))[0],
    )


def suggest_level(score_pct: int, items: list[GradedItem]) -> str:
    """Base band from the global %, then the evidence cap steps down one level at a time."""
    level = next(code for floor, code in BANDS if score_pct >= floor)
    total_by_level = Counter(i.cefr for i in items)
    right_by_level = Counter(i.cefr for i in items if i.correct)
    while level in EVIDENCE_LEVELS:
        required = (total_by_level[level] + 1) // 2  # ceil(n / 2)
        if right_by_level[level] >= required:
            break
        level = LEVEL_ORDER[LEVEL_ORDER.index(level) - 1]
    return level


def mock_feedback(result: Result, first_name: str) -> dict[str, Any]:
    """Deterministic coach output in the SHARED_CONTEXT §6 shape (seeded history only)."""
    lines: Mapping[str, tuple[str, str, str, str]] = {
        # skill: (strength sentence, challenge sentence, memory note, greeting tip)
        "grammar": (
            "Your sentences hold together well.",
            "Some sentence patterns still slow you down.",
            "Builds clear sentences; still unsure with some verb forms.",
            "Tonight, take a breath and check the verb.",
        ),
        "listening": (
            "You catch what people say, even in a noisy station.",
            "Fast speech was tricky tonight.",
            "Hesitates when people speak quickly; strong with signs and menus.",
            "Tonight, listen for the numbers.",
        ),
        "reading": (
            "You understand signs and messages very well.",
            "Longer notices took more time.",
            "Reads short texts well; longer notices take time.",
            "Tonight, read the first line twice.",
        ),
        "vocabulary": (
            "You know the words a traveller needs.",
            "A few travel words were new.",
            "Good everyday words; some travel words are still new.",
            "Tonight, look for words you already know.",
        ),
    }
    strength, challenge = lines[result.strength], lines[result.challenge]
    return {
        "summary": f"You got {result.correct} of 10 decisions right. {strength[0]} {challenge[1]}",
        "strength": result.strength,
        "challenge": result.challenge,
        "recommendation": f"Practise {result.challenge} a little every day. {challenge[3]}",
        "next_mission_id": NEXT_MISSION_BY_CHALLENGE[result.challenge],
        "memory_note": challenge[2],
        "next_greeting": f"Welcome back, {first_name}. {challenge[1]} {challenge[3]}",
    }
