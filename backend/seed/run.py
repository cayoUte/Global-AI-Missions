"""The seed, step by step, inside the caller's transaction (idempotent)."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.core import demo
from seed.content import (
    CONTENT_DIR,
    VersionResult,
    resolve_source,
    seed_catalog,
    seed_mission_version,
    seed_reference,
)
from seed.users import seed_demo_users
from seed.veteran import SeededAttempt, seed_veteran_history


@dataclass
class SeedSummary:
    versions: list[VersionResult] = field(default_factory=list)
    users: list[str] = field(default_factory=list)
    veteran_attempts: list[SeededAttempt] = field(default_factory=list)
    veteran_skipped: str | None = None

    def lines(self) -> list[str]:
        out = []
        for v in self.versions:
            what = "created" if v.created else "unchanged"
            src = "FIXTURE " if v.source.is_fixture else ""
            out.append(
                f"mission {v.version.mission_id}: version {v.version.version} {what} "
                f"({src}{v.source.folder.name}, hash {v.version.content_hash[:12]})"
            )
        out.append(f"demo users: {', '.join(self.users)} (demo-only password)")
        if self.veteran_skipped:
            out.append(f"veteran history: skipped ({self.veteran_skipped})")
        elif self.veteran_attempts:
            scores = ", ".join(
                f"seed {a.seed}: {a.trace.correct}/10 -> {a.trace.ending_key}"
                for a in self.veteran_attempts
            )
            out.append(f"veteran history: {len(self.veteran_attempts)} attempts created ({scores})")
        else:
            out.append("veteran history: already present on the active version (unchanged)")
        return out


def run_seed(
    session: Session,
    content_dir: Path = CONTENT_DIR,
    force_fixture: bool = False,
    with_veteran: bool = True,
    now: datetime | None = None,
) -> SeedSummary:
    now = now or datetime.now(UTC)
    summary = SeedSummary()
    seed_reference(session)
    catalog = seed_catalog(session, content_dir)
    playable = [entry["id"] for entry in catalog if entry["playable"]]
    for mission_id in playable:
        source = resolve_source(mission_id, content_dir, force_fixture)
        summary.versions.append(seed_mission_version(session, source, now))

    users = seed_demo_users(session)
    summary.users = [u.email for u in users.values()]

    veteran_mission = "the-last-train" if "the-last-train" in playable else None
    if not with_veteran:
        summary.veteran_skipped = "--no-veteran"
    elif veteran_mission is None:
        summary.veteran_skipped = "no playable the-last-train mission in the catalog"
    else:
        summary.veteran_attempts = seed_veteran_history(
            session, users[demo.VETERAN.email], veteran_mission, now
        )
    session.flush()
    return summary
