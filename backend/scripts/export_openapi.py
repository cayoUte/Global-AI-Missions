"""Export the OpenAPI document for the frontend's generated types.

    cd backend && uv run python scripts/export_openapi.py

Writes docs/contracts/openapi.json (the frontend runs `npm run gen:api` on it). No database is
needed: the app is only built, never served.
"""

import json
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
# Placeholder values so the export runs without a .env (nothing connects to them).
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://export:export@localhost:5432/export")
os.environ.setdefault("JWT_SECRET", "export-only-placeholder-secret-0123456789abcdef")

from app.main import create_app  # noqa: E402

OUT = BACKEND.parent / "docs" / "contracts" / "openapi.json"


def main() -> None:
    schema = create_app().openapi()
    OUT.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(BACKEND.parent)} ({len(schema['paths'])} paths)")


if __name__ == "__main__":
    main()
