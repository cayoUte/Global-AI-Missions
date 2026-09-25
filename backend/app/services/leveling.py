"""Suggested level: deterministic and explainable (SHARED_CONTEXT §4, PD-015).

1. Base level from the global %: 0-29 Pre-A1 · 30-49 A1 · 50-69 A2 · 70-84 B1 · 85-100 B2.
2. Evidence cap: level L in {A1, A2, B1, B2} needs at least ceil(n_L / 2) correct answers among
   the n_L items tagged L; otherwise step down one level and check again. Pre-A1 needs none.
3. This mission can suggest at most B2 (C1 needs another mission).

Implements docs/assessment/ASSESSMENT_SPEC.md §5 exactly; tests/services/test_grading_leveling.py
replays its nine worked examples. Pure functions, no I/O.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

CEFR_ORDER: tuple[str, ...] = ("PRE_A1", "A1", "A2", "B1", "B2", "C1")
CEFR_RANK: dict[str, int] = {code: rank for rank, code in enumerate(CEFR_ORDER)}
# (minimum global %, level), checked top-down. B2 is this mission's ceiling.
BANDS: tuple[tuple[int, str], ...] = ((85, "B2"), (70, "B1"), (50, "A2"), (30, "A1"), (0, "PRE_A1"))


@dataclass(frozen=True)
class Evidence:
    cefr: str
    correct: int
    total: int
    required: int
    met: bool


@dataclass(frozen=True)
class LevelResult:
    cefr: str
    base_cefr: str
    evidence: tuple[Evidence, ...]  # every level checked, top-down
    reason: str


def cefr_label(code: str) -> str:
    return "Pre-A1" if code == "PRE_A1" else code


def base_level(score_pct: int) -> str:
    return next(level for minimum, level in BANDS if score_pct >= minimum)


def suggest_level(score_pct: int, by_cefr: Mapping[str, tuple[int, int]]) -> LevelResult:
    """ASSESSMENT_SPEC §5.1. `by_cefr`: level -> (correct, total) over this attempt's items."""
    base = base_level(score_pct)
    level, evidence = base, []
    while level != "PRE_A1":
        correct, total = by_cefr.get(level, (0, 0))
        required = (total + 1) // 2  # ceil(total / 2) in integers
        met = total > 0 and correct >= required  # a level with no items is never met
        evidence.append(Evidence(level, correct, total, required, met))
        if met:
            break
        level = CEFR_ORDER[CEFR_RANK[level] - 1]
    return LevelResult(level, base, tuple(evidence), level_reason(score_pct, base, level, evidence))


def _word(n: int) -> str:
    return "checkpoint" if n == 1 else "checkpoints"


def _clause(e: Evidence) -> str:
    label = cefr_label(e.cefr)
    need = f"{label} needs {e.required} of {e.total} {label} {_word(e.total)}"
    return f"{need} — you had {e.correct} —"


def level_reason(score_pct: int, base: str, level: str, evidence: Sequence[Evidence]) -> str:
    """ASSESSMENT_SPEC §5.2: exactly one of three sentence shapes (PD-015)."""
    opening = f"{score_pct}% points to {cefr_label(base)}"
    if base == "PRE_A1":
        return f"{opening}, so your suggested level is Pre-A1."
    failed = [e for e in evidence if not e.met]
    narrated = failed or [evidence[0]]  # base met: narrate the base check itself
    clauses = " and ".join(_clause(e) for e in narrated)
    return f"{opening}. {clauses} so your suggested level is {cefr_label(level)}."


def report_label(cefr: str, mission_title: str, score_pct: int) -> str:
    """`A2 · The Last Train — 70%` (middle dot U+00B7, em dash U+2014)."""
    return f"{cefr_label(cefr)} · {mission_title} — {score_pct}%"
