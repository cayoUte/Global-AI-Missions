"""Engine CLI (the only engine module that does I/O). Run from backend/:

uv run python -m app.engine.cli validate [--mission the-last-train]
uv run python -m app.engine.cli calibrate --profile A2 [--runs 1000]
uv run python -m app.engine.cli simulate --profile B1 --seed 7
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from app.engine import (
    PROFILES,
    SimulatedStudent,
    build_graph,
    calibrate,
    clock_time,
    compute_h,
    run,
    validate_documents,
)

MISSIONS_DIR = Path(__file__).resolve().parents[3] / "content" / "missions"


def load(folder: Path) -> tuple[Any, Any]:
    read = lambda name: json.loads((folder / name).read_text(encoding="utf-8"))  # noqa: E731
    return read("items.json"), read("mission.json")


def default_mission(missions_dir: Path) -> str:
    real = missions_dir / "the-last-train"
    return real.name if (real / "mission.json").exists() else "_fixture"


def cmd_validate(missions_dir: Path, mission: str | None) -> int:
    folders = (
        [missions_dir / mission]
        if mission
        else sorted(p for p in missions_dir.iterdir() if (p / "mission.json").exists())
    )
    failed = 0
    for folder in folders:
        report = validate_documents(*load(folder))
        print(f"{folder.name}: {'ok' if report.ok else 'FAIL'}")
        if report.path_count:
            endings = ", ".join(f"{k}={v}" for k, v in report.endings.items())
            print(
                f"  paths: {report.path_count} | story-minutes: {report.min_minutes}"
                f"-{report.max_minutes} | endings by path: {endings}"
            )
            print(f"  nodes reachable with train_departed: {len(report.departed_nodes)}")
        for line in report.errors:
            print(f"  error: {line}")
        for line in report.warnings:
            print(f"  warning: {line}")
        failed += not report.ok
    return 1 if failed else 0


def cmd_calibrate(missions_dir: Path, mission: str, profile: str, runs: int) -> int:
    graph = build_graph(*load(missions_dir / mission))
    for name in PROFILES if profile == "all" else [profile]:
        counts = calibrate(graph, name, runs)
        made = sum(v for k, v in counts.items() if k != "night_bus")
        shares = " | ".join(f"{k} {100 * v / runs:.1f}%" for k, v in counts.items())
        print(f"{mission} {name:<18} {shares} | made the train {100 * made / runs:.1f}%")
    return 0


def cmd_simulate(missions_dir: Path, mission: str, profile: str, seed: int) -> int:
    graph = build_graph(*load(missions_dir / mission))
    trace = run(graph, compute_h(graph), SimulatedStudent(profile), seed)
    for st in trace.steps:
        print(
            f"{clock_time(graph, st.minutes_left)}  {st.node_id:<24} {st.kind:<12} "
            f"{st.outcome or '-':<10} {st.maya_decision:<7} {st.maya_mood}"
        )
    print(
        f"ending={trace.ending_key} minutes_used={trace.minutes_used} correct={trace.correct} "
        f"hints={trace.hints} rescued={trace.rescued}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.engine.cli")
    parser.add_argument("--missions-dir", type=Path, default=MISSIONS_DIR)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate").add_argument("--mission")
    cal = sub.add_parser("calibrate")
    cal.add_argument("--profile", choices=[*PROFILES, "all"], default="all")
    cal.add_argument("--runs", type=int, default=1000)
    sim = sub.add_parser("simulate")
    sim.add_argument("--profile", choices=list(PROFILES), default="B1")
    sim.add_argument("--seed", type=int, default=7)
    for p in (cal, sim):
        p.add_argument("--mission")
    args = parser.parse_args(argv)
    missions_dir = args.missions_dir.resolve()
    if args.command == "validate":
        return cmd_validate(missions_dir, args.mission)
    mission = args.mission or default_mission(missions_dir)
    if args.command == "calibrate":
        return cmd_calibrate(missions_dir, mission, args.profile, args.runs)
    return cmd_simulate(missions_dir, mission, args.profile, args.seed)


if __name__ == "__main__":
    sys.exit(main())
