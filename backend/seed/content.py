"""Reference data, catalog and mission content: files in content/ -> validated rows.

Content is validated before anything is written: JSON Schema (docs/contracts) and then the
engine validator (graph invariants + content integrity). Any error aborts the whole seed.
A mission version is immutable: when the content hash changes, a new version is created and
existing attempts keep pointing to theirs.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.config import REPO_ROOT
from app.engine import normalize_answer, validate_documents
from app.models import (
    AcceptedAnswer,
    CefrLevel,
    Mission,
    MissionVersion,
    Question,
    QuestionOption,
    Skill,
)
from app.repositories import missions as missions_repo

CONTENT_DIR = REPO_ROOT / "content"
CONTRACTS_DIR = REPO_ROOT / "docs" / "contracts"
FIXTURE_FOLDER = "_fixture"

CEFR_LEVELS = (
    ("PRE_A1", 0, "Pre-A1"),
    ("A1", 1, "A1"),
    ("A2", 2, "A2"),
    ("B1", 3, "B1"),
    ("B2", 4, "B2"),
    ("C1", 5, "C1"),
)
SKILLS = (
    ("grammar", "Grammar"),
    ("vocabulary", "Vocabulary"),
    ("reading", "Reading"),
    ("listening", "Listening"),
    ("speaking", "Speaking"),
)


class SeedError(Exception):
    """Invalid content or an inconsistent database: the seed aborts and rolls back."""


@dataclass(frozen=True)
class ContentSource:
    mission_id: str  # the catalog mission it is seeded under
    folder: Path
    is_fixture: bool


@dataclass(frozen=True)
class VersionResult:
    version: MissionVersion
    created: bool
    source: ContentSource


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _schema_errors(schema_name: str, document: Any) -> list[str]:
    validator = Draft202012Validator(load_json(CONTRACTS_DIR / schema_name))
    return [
        f"{schema_name}: {'/'.join(str(p) for p in e.absolute_path) or '(root)'}: {e.message}"
        for e in sorted(validator.iter_errors(document), key=lambda e: list(e.absolute_path))
    ]


def content_hash(items_doc: Any, mission_doc: Any) -> str:
    canonical = json.dumps(
        {"items": items_doc, "mission": mission_doc},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# --- Reference data --------------------------------------------------------------------------


def seed_reference(session: Session) -> None:
    for code, rank, label in CEFR_LEVELS:
        session.execute(
            insert(CefrLevel)
            .values(code=code, rank=rank, label=label)
            .on_conflict_do_update(index_elements=[CefrLevel.code], set_={"label": label})
        )
    for code, label in SKILLS:
        session.execute(
            insert(Skill)
            .values(code=code, label=label)
            .on_conflict_do_update(index_elements=[Skill.code], set_={"label": label})
        )


# --- Catalog ---------------------------------------------------------------------------------


def seed_catalog(session: Session, content_dir: Path = CONTENT_DIR) -> list[dict[str, Any]]:
    """Upsert every catalog mission by id. Returns the catalog entries."""
    catalog = load_json(content_dir / "catalog.json")
    errors = _schema_errors("catalog.schema.json", catalog)
    if errors:
        raise SeedError("content/catalog.json is invalid:\n  " + "\n  ".join(errors))
    for entry in catalog["missions"]:
        values = {
            "title": entry["title"],
            "world_zone": entry["world_zone"],
            "skill_focus": entry["skill_focus"],
            "cefr_min": entry["cefr_range"]["min"],
            "cefr_max": entry["cefr_range"]["max"],
            "playable": entry["playable"],
            "unlock_rule": entry["unlock_rule"],
            "teaser": entry["teaser"],
            "sort_order": entry["sort_order"],
        }
        session.execute(
            insert(Mission)
            .values(id=entry["id"], **values)
            .on_conflict_do_update(index_elements=[Mission.id], set_=values)
        )
    return catalog["missions"]


# --- Mission content -------------------------------------------------------------------------


def resolve_source(
    mission_id: str, content_dir: Path = CONTENT_DIR, force_fixture: bool = False
) -> ContentSource:
    """content/missions/<id>/ when both files exist; otherwise the walking-skeleton fixture."""
    folder = content_dir / "missions" / mission_id
    complete = (folder / "items.json").exists() and (folder / "mission.json").exists()
    if complete and not force_fixture:
        return ContentSource(mission_id, folder, is_fixture=False)
    fixture = content_dir / "missions" / FIXTURE_FOLDER
    if not (fixture / "items.json").exists():
        raise SeedError(f"no content for playable mission '{mission_id}' and no fixture")
    return ContentSource(mission_id, fixture, is_fixture=True)


def load_and_validate(source: ContentSource) -> tuple[dict[str, Any], dict[str, Any]]:
    items_doc = load_json(source.folder / "items.json")
    mission_doc = load_json(source.folder / "mission.json")
    errors = _schema_errors("items.schema.json", items_doc)
    errors += _schema_errors("mission.schema.json", mission_doc)
    if not source.is_fixture and mission_doc.get("mission_id") != source.mission_id:
        errors.append(f"mission.json mission_id is not '{source.mission_id}'")
    if not errors:
        report = validate_documents(items_doc, mission_doc)
        errors = list(report.errors)
    if errors:
        raise SeedError(
            f"content in {source.folder} failed validation:\n  " + "\n  ".join(errors)
        )
    return items_doc, mission_doc


def seed_mission_version(
    session: Session, source: ContentSource, now: datetime | None = None
) -> VersionResult:
    """Create a new version when the content hash is new; otherwise reuse (and re-activate) it."""
    now = now or datetime.now(UTC)
    items_doc, mission_doc = load_and_validate(source)
    digest = content_hash(items_doc, mission_doc)
    existing = session.scalar(
        select(MissionVersion).where(
            MissionVersion.mission_id == source.mission_id, MissionVersion.content_hash == digest
        )
    )
    if existing is not None:
        active = missions_repo.get_active_mission_version(session, source.mission_id)
        if active is not None and active.id != existing.id:
            existing.published_at = now  # the files went back to an older version: republish it
            session.flush()
        return VersionResult(existing, created=False, source=source)

    last = session.scalar(
        select(func.max(MissionVersion.version)).where(
            MissionVersion.mission_id == source.mission_id
        )
    )
    version = MissionVersion(
        mission_id=source.mission_id,
        version=(last or 0) + 1,
        content_hash=digest,
        content=mission_doc,
        published_at=now,
    )
    session.add(version)
    session.flush()
    _insert_items(session, version.id, items_doc["items"])
    return VersionResult(version, created=True, source=source)


def _insert_items(session: Session, version_id: int, items: list[dict[str, Any]]) -> None:
    for position, item in enumerate(items, start=1):
        question = Question(
            mission_version_id=version_id,
            external_id=item["id"],
            type=item["type"],
            skill=item["skill"],
            cefr=item["cefr"],
            prompt=item["prompt"],
            stimulus=item["stimulus"],
            explanation=item["explanation"],
            hint=item["hint"],
            position=position,
        )
        session.add(question)
        session.flush()
        key = item["answer_key"]
        if item["type"] == "fill_blank":
            # Normalized and de-duplicated, authored order kept; the first one is the primary.
            accepted = list(dict.fromkeys(normalize_answer(a) for a in key["accepted"]))
            session.add_all(
                AcceptedAnswer(question_id=question.id, answer_normalized=a, is_primary=i == 0)
                for i, a in enumerate(accepted)
            )
        else:
            session.add_all(
                QuestionOption(
                    question_id=question.id,
                    option_key=option["id"],
                    text=option["text"],
                    position=i,
                    is_correct=option["id"] == key["correct_option_id"],
                )
                for i, option in enumerate(item["options"], start=1)
            )
    session.flush()
