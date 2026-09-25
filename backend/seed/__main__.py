"""python -m seed  (from backend/, after `alembic upgrade head`). Idempotent: run it any time.

Loads reference data, content/catalog.json, each playable mission's validated content (the
walking-skeleton fixture until content/missions/<id>/ has both items.json and mission.json),
the demo users and class, and the veteran's simulated history. One transaction: any error
(e.g. invalid content) rolls everything back and exits with code 1.
"""

import argparse
import sys
from pathlib import Path

from app.repositories.db import get_sessionmaker
from seed.content import CONTENT_DIR, SeedError
from seed.run import run_seed


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m seed", description=__doc__.splitlines()[0])
    parser.add_argument("--content-dir", type=Path, default=CONTENT_DIR)
    parser.add_argument(
        "--fixture", action="store_true", help="seed content/missions/_fixture even if real "
        "content exists (walking skeleton)"
    )
    parser.add_argument("--no-veteran", action="store_true", help="skip the veteran history")
    args = parser.parse_args()

    with get_sessionmaker()() as session:
        try:
            summary = run_seed(
                session,
                content_dir=args.content_dir.resolve(),
                force_fixture=args.fixture,
                with_veteran=not args.no_veteran,
            )
            session.commit()
        except SeedError as exc:
            session.rollback()
            print(f"seed aborted, nothing written: {exc}", file=sys.stderr)
            return 1
    for line in summary.lines():
        print(line)
    print("seed complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
