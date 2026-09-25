"""Validate the content files against the frozen JSON Schemas in docs/contracts/.

Usage (from backend/):  uv run python scripts/validate_content.py [--content-dir PATH]

Checks, for content/catalog.json and every content/missions/<folder>/{items,mission}.json:
  1. JSON Schema (Draft 2020-12) validity.
  2. Cheap cross-file references: unique catalog ids, unlock rules pointing to catalog missions,
     mission_id equal to the folder name (a leading "_" is ignored, so _fixture -> fixture),
     items.json and mission.json agreeing on mission_id, and every checkpoint item_id existing.

It does NOT check the graph (reachability, cycles, 10 checkpoints per path, 4/2/2/2) or content
integrity (unique option ids, correct_option_id among the options): that is the engine
validator's job (python -m app.engine.cli validate). Exit code 0 = valid, 1 = errors.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_DIR = REPO_ROOT / "docs" / "contracts"
SCHEMAS = {
    "catalog": "catalog.schema.json",
    "items": "items.schema.json",
    "mission": "mission.schema.json",
}


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def load_validators() -> dict[str, Draft202012Validator]:
    validators = {}
    for name, filename in SCHEMAS.items():
        schema = load_json(CONTRACTS_DIR / filename)
        Draft202012Validator.check_schema(schema)
        validators[name] = Draft202012Validator(schema)
    return validators


def schema_errors(validator: Draft202012Validator, document: Any) -> list[str]:
    errors = sorted(validator.iter_errors(document), key=lambda e: list(e.absolute_path))
    return [f"{'/'.join(str(p) for p in e.absolute_path) or '(root)'}: {e.message}" for e in errors]


def check_catalog(document: dict[str, Any]) -> list[str]:
    ids = [m["id"] for m in document["missions"]]
    errors = [f"duplicate mission id '{i}'" for i in sorted({i for i in ids if ids.count(i) > 1})]
    for mission in document["missions"]:
        target = mission["unlock_rule"].get("mission_id")
        if target is not None and target not in ids:
            errors.append(
                f"{mission['id']}: unlock_rule.mission_id '{target}' is not in the catalog"
            )
    return errors


def check_mission_folder(folder: Path, items: Any, mission: Any) -> list[str]:
    expected_id = folder.name.lstrip("_")
    errors = []
    for label, doc in (("items.json", items), ("mission.json", mission)):
        if doc is not None and doc["mission_id"] != expected_id:
            errors.append(f"{label}: mission_id '{doc['mission_id']}' != folder '{expected_id}'")
    if items is not None and mission is not None:
        item_ids = {item["id"] for item in items["items"]}
        for node in mission["nodes"]:
            if node["kind"] == "checkpoint" and node["item_id"] not in item_ids:
                errors.append(f"mission.json: node '{node['id']}' references unknown item")
    return errors


def validate(content_dir: Path) -> int:
    validators = load_validators()
    failures = 0

    def report(path: Path, errors: list[str]) -> None:
        nonlocal failures
        rel = (
            path.relative_to(content_dir.parent)
            if path.is_relative_to(content_dir.parent)
            else path
        )
        if errors:
            failures += len(errors)
            print(f"FAIL {rel}")
            for error in errors:
                print(f"     - {error}")
        else:
            print(f"ok   {rel}")

    catalog_path = content_dir / "catalog.json"
    catalog = load_json(catalog_path)
    errors = schema_errors(validators["catalog"], catalog)
    report(catalog_path, errors or check_catalog(catalog))

    missions_dir = content_dir / "missions"
    folders = (
        sorted(p for p in missions_dir.iterdir() if p.is_dir()) if missions_dir.exists() else []
    )
    for folder in folders:
        docs: dict[str, Any] = {}
        for name in ("items", "mission"):
            path = folder / f"{name}.json"
            if not path.exists():
                print(f"skip {path.relative_to(content_dir.parent)} (not written yet)")
                docs[name] = None
                continue
            docs[name] = load_json(path)
            errors = schema_errors(validators[name], docs[name])
            report(path, errors)
            if errors:
                docs[name] = None  # do not cross-check a structurally invalid document
        report(folder, check_mission_folder(folder, docs["items"], docs["mission"]))

    print("content is valid" if failures == 0 else f"{failures} error(s)")
    return 0 if failures == 0 else 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--content-dir", type=Path, default=REPO_ROOT / "content")
    args = parser.parse_args()
    sys.exit(validate(args.content_dir.resolve()))


if __name__ == "__main__":
    main()
