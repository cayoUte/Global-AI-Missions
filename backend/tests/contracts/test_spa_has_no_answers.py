"""R-22: questions and answers are not hardcoded in the frontend (qa-engineer).

Scans the SPA source (always) and the production bundle (when `npm run build` has produced
frontend/dist) for the real mission's item content: prompts, explanations, hints, listening
scripts, long option texts and the accepted fill-blank answers, plus answer-key field names.
The dev-only mock adapter (src/api/mock, never in a production build) is excluded from the source
scan; the bundle scan proves it is not shipped.
"""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
FRONTEND = ROOT / "frontend"
ITEMS = json.loads(
    (ROOT / "content" / "missions" / "the-last-train" / "items.json").read_text(encoding="utf-8")
)["items"]
KEY_FIELDS = ("correct_option_id", "answer_key", "accepted_answers", "is_correct")


def _secrets() -> set[str]:
    found: set[str] = set()
    for item in ITEMS:
        found |= {item["prompt"], item["explanation"], item["hint"]}
        stimulus = item.get("stimulus") or {}
        if stimulus.get("audio_script"):
            found.add(stimulus["audio_script"])
        found |= {o["text"] for o in item.get("options") or [] if len(o["text"]) >= 16}
        found |= set(item["answer_key"].get("accepted") or [])
    return {s for s in found if len(s) >= 8}  # short words ("Is", "a single") are not evidence


def _leaks(files: list[Path]) -> list[str]:
    secrets, leaks = _secrets(), []
    for file in files:
        text = file.read_text(encoding="utf-8", errors="ignore")
        leaks += [f"{file.name}: {s[:40]!r}" for s in secrets if s in text]
        leaks += [f"{file.name}: key {k}" for k in KEY_FIELDS if k in text]
    return leaks


def test_the_spa_source_has_no_item_content_or_answer_keys():
    src = FRONTEND / "src"
    files = [
        f
        for f in src.rglob("*")
        if f.suffix in {".ts", ".tsx"}
        and "mock" not in f.relative_to(src).parts[:2]
        and f.name != "schema.d.ts"
    ]
    assert len(files) > 20
    assert _leaks(files) == []


def test_the_production_bundle_has_no_item_content_or_answer_keys():
    dist = FRONTEND / "dist"
    files = [f for f in dist.rglob("*") if f.suffix in {".js", ".html", ".css"}]
    if not files:
        pytest.skip("frontend/dist not built (npm run build); the E2E run builds it")
    assert _leaks(files) == []
