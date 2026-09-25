"""Scoring: deterministic, server-side only (SHARED_CONTEXT §4, api-contract §7).

global % = correct / total · per-skill % = correct / items of that skill · correct + incorrect =
total (every checkpoint needs an answer; there is no skip). Hints never change the score.
Percentages are integers rounded half up.

Implements docs/assessment/ASSESSMENT_SPEC.md §3-§4 and §7.1. Pure functions, no I/O: the
attempts service feeds them the outcomes stored when each answer was locked (never re-decided).
"""

from collections.abc import Iterable
from dataclasses import dataclass

SCORED_SKILLS: tuple[str, ...] = ("grammar", "listening", "reading", "vocabulary")  # display order
UNMEASURED_SKILLS: tuple[str, ...] = ("speaking",)


@dataclass(frozen=True)
class GradedItem:
    """One checkpoint of the attempt: the item's tags and whether the stored answer was correct."""

    item_id: str
    skill: str
    cefr: str
    is_correct: bool


@dataclass(frozen=True)
class SkillResult:
    skill: str
    correct: int
    total: int
    pct: int


@dataclass(frozen=True)
class GradeResult:
    correct: int
    incorrect: int
    total: int
    score_pct: int
    skills: tuple[SkillResult, ...]  # scored skills that have items, fixed display order
    by_cefr: dict[str, tuple[int, int]]  # cefr -> (correct, total), used by leveling


def percent(correct: int, total: int) -> int:
    """100 × correct / total rounded half up, with integer arithmetic (no float surprises)."""
    if total <= 0:
        return 0
    return (200 * correct + total) // (2 * total)


def grade_attempt(items: Iterable[GradedItem]) -> GradeResult:
    items = list(items)
    correct = sum(1 for item in items if item.is_correct)
    total = len(items)
    skills = []
    for skill in SCORED_SKILLS:
        tagged = [item for item in items if item.skill == skill]
        if tagged:
            ok = sum(1 for item in tagged if item.is_correct)
            skills.append(SkillResult(skill, ok, len(tagged), percent(ok, len(tagged))))
    by_cefr: dict[str, tuple[int, int]] = {}
    for item in items:
        ok, n = by_cefr.get(item.cefr, (0, 0))
        by_cefr[item.cefr] = (ok + int(item.is_correct), n + 1)
    return GradeResult(
        correct=correct,
        incorrect=total - correct,
        total=total,
        score_pct=percent(correct, total),
        skills=tuple(skills),
        by_cefr=by_cefr,
    )


def strength_and_challenge(skills: Iterable[SkillResult]) -> tuple[str, str]:
    """ASSESSMENT_SPEC §7.1. The LLM must echo these two values (SHARED_CONTEXT §6).

    strength  = highest pct; ties -> more correct, then display order.
    challenge = lowest pct among the OTHER skills; ties -> more incorrect, then display order.
    """
    ordered = sorted(skills, key=lambda s: SCORED_SKILLS.index(s.skill))
    if len(ordered) < 2:
        return SCORED_SKILLS[0], SCORED_SKILLS[1]
    order = {s.skill: i for i, s in enumerate(ordered)}
    strength = min(ordered, key=lambda s: (-s.pct, -s.correct, order[s.skill]))
    others = [s for s in ordered if s.skill != strength.skill]
    challenge = min(others, key=lambda s: (s.pct, -(s.total - s.correct), order[s.skill]))
    return strength.skill, challenge.skill
