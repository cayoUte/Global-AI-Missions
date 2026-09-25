"""Write docs/ai/samples/{new_student,veteran}.json: the exact coach input and its output.

    cd backend && uv run python -m app.ai.samples

Always runs the mock. Also runs the configured LLM when COACH_PROVIDER names one and its
variables are set in the environment / .env (anthropic: ANTHROPIC_API_KEY; openai_compatible:
OPENAI_COMPAT_BASE_URL, _API_KEY, _MODEL). One call per scenario, about a cent in total with
Claude, free on Groq's free tier. For a quick live check use scripts/coach_smoke.py instead.
"""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from app.ai.factory import create_provider
from app.ai.mock_provider import MockCoachProvider
from app.ai.ports import CoachContext, CoachProvider
from app.ai.prompting import context_payload
from app.ai.service import MemoryState, build_context, generate_feedback

REPO_ROOT = Path(__file__).resolve().parents[3]
ITEMS = REPO_ROOT / "content" / "missions" / "the-last-train" / "items.json"
OUT_DIR = REPO_ROOT / "docs" / "ai" / "samples"
CANDIDATES = ("night-radio", "dinner-for-two", "the-interview", "campus-day")


def _missed(item_ids: tuple[str, ...]) -> list[dict[str, Any]]:
    items = {i["id"]: i for i in json.loads(ITEMS.read_text(encoding="utf-8"))["items"]}
    return [{k: items[i][k] for k in ("skill", "cefr", "prompt", "explanation")} for i in item_ids]


def _skills(grammar: int, listening: int, reading: int, vocabulary: int) -> list[dict[str, int]]:
    rows = []
    for skill, correct, total in (
        ("grammar", grammar, 4),
        ("listening", listening, 2),
        ("reading", reading, 2),
        ("vocabulary", vocabulary, 2),
    ):
        rows.append(
            {
                "skill": skill,
                "correct": correct,
                "total": total,
                "pct": (200 * correct + total) // (2 * total),
            }
        )
    return rows


def new_student() -> CoachContext:
    """Ana, first night with Maya. ASSESSMENT_SPEC example 3 (q07, q08, q09 missed)."""
    return build_context(
        first_name="Ana",
        suggested_cefr="A2",
        score_pct=70,
        skills=_skills(3, 1, 2, 1),
        strength="reading",
        challenge="listening",
        missed=_missed(("q07", "q08", "q09")),
        ending_key="made_it",
        rescue_used=False,
        hints_received=1,
        memory=None,
        candidate_mission_ids=CANDIDATES,
    )


def veteran() -> CoachContext:
    """Leo, fifth night (profile A2_weak_listening): q06, q07, q10 missed; four notes in memory."""
    notes = (
        "Strong in vocabulary; listening needs practice (A2, 60%). Took the night bus home "
        "with me.",
        "Strong in vocabulary; reading needs practice (A2, 60%). Caught the last train with my "
        "shortcut.",
        "Strong in grammar; listening needs practice (A1, 40%). Took the night bus home with me.",
        "Strong in vocabulary; listening needs practice (A1, 30%). Took the night bus home "
        "with me.",
    )
    return build_context(
        first_name="Leo",
        suggested_cefr="A2",
        score_pct=70,
        skills=_skills(3, 1, 1, 2),
        strength="vocabulary",
        challenge="listening",
        missed=_missed(("q06", "q07", "q10")),
        ending_key="made_it_with_maya",
        rescue_used=True,
        hints_received=2,
        memory=MemoryState(sessions_count=4, notes=tuple({"text": n} for n in notes)),
        candidate_mission_ids=CANDIDATES,
    )


def _run(ctx: CoachContext, provider: CoachProvider) -> dict[str, Any]:
    feedback, meta = generate_feedback(ctx, provider)
    return {"meta": asdict(meta), "feedback": feedback.model_dump()}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    configured = create_provider()
    providers: list[CoachProvider] = [MockCoachProvider()]
    if configured.provider != "mock":
        providers.append(configured)
    for name, ctx in (("new_student", new_student()), ("veteran", veteran())):
        doc = {
            "scenario": name,
            "coach_input": context_payload(ctx),
            "outputs": [_run(ctx, p) for p in providers],
        }
        path = OUT_DIR / f"{name}.json"
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(REPO_ROOT)} ({', '.join(p.provider for p in providers)})")


if __name__ == "__main__":
    main()
