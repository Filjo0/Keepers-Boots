"""Offline JSON evidence CLI. No agents, network or cloud credentials."""
import argparse
import json
from pathlib import Path
from .analysis import analyse_snapshot
from .scenario import SCENARIOS, build_catalog
from .snapshots import freeze_snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", type=Path, help="Read a synthetic scenario JSON file")
    parser.add_argument("--scenario-id", choices=tuple(SCENARIOS), default="tempting-short-pass")
    parser.add_argument("--outcome", choices=("completed", "intercepted"), default="completed")
    parser.add_argument("--write-scenario", type=Path, help="Regenerate a scenario file and exit")
    args = parser.parse_args()
    scenario = (
        json.loads(args.scenario.read_text(encoding="utf-8"))
        if args.scenario else build_catalog(args.outcome)[args.scenario_id]
    )
    if args.write_scenario:
        args.write_scenario.parent.mkdir(parents=True, exist_ok=True)
        args.write_scenario.write_text(
            json.dumps(scenario, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n"
        )
        print(f"Wrote synthetic scenario: {args.write_scenario}")
        return
    report = analyse_snapshot(freeze_snapshot(scenario))
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
