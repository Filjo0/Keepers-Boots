"""Preserve the two known reviewer misses as calibration data, never held-out scores."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from keepers_boots.analysis import analyse_pressure, analyse_snapshot
from keepers_boots.claims import validate_draft
from keepers_boots.scenario import build_scenario
from keepers_boots.snapshots import freeze_snapshot


CASES = {
    "s1-pressure-subject": ("4082286", ["The fan text makes the keeper arrive; pressure arrival refers to an opponent reaching the keeper."]),
    "s1-polarity-and-completeness": ("rejected-refresh-54s", [
        "The draft says both ground options have positive margins, although the short route's entire reported range is negative.",
        "The analyst paragraph stops mid-sentence."]),
}


def main():
    snapshot = freeze_snapshot(build_scenario())
    assessment, pressure = analyse_snapshot(snapshot), analyse_pressure(snapshot)
    directory = ROOT / "data/evaluation/calibration"
    directory.mkdir(parents=True, exist_ok=True)
    for case_id, (archive_name, issues) in CASES.items():
        source = ROOT / "local-artifacts/recording-archive" / archive_name / "runtime-tempting-short-pass.json"
        raw = source.read_bytes()
        capture = json.loads(raw)
        if capture["assessment"] != assessment or capture["pressure"] != pressure:
            raise ValueError("Historical evidence does not match the frozen calibration scenario")
        interpretation = capture["interpretation"]
        if interpretation["source"] != "local_agents" or interpretation["trace"][-1]["status"] != "accept":
            raise ValueError("Historical reviewer-acceptance trace is missing")
        _, errors = validate_draft({"snapshot_id": snapshot.snapshot_id, "ranking": None,
                                   **{name: interpretation[name] for name in ("claims", "fan", "analyst", "missing_information")}},
                                  snapshot, assessment)
        if not errors:
            raise ValueError("Known calibration error is no longer detected; review the export")
        data = {"schema_version": "1", "case_id": case_id, "classification": "calibration_failure",
                "snapshot_id": snapshot.snapshot_id, "decision": snapshot.read(),
                "assessment": assessment, "pressure": pressure, "interpretation": deepcopy(interpretation),
                "audit": {"issues": issues, "reviewer_approved": True, "current_guard_errors": errors,
                          "initial_analyst_draft_available": False, "full_review_object_available": False,
                          "paired_analyst_only_result_available": False,
                          "exclusion": "Seen during prompt/guard tuning; never count as held-out evidence."},
                "provenance": {"source_sha256": sha256(raw).hexdigest(),
                               "source_saved_at_utc": datetime.fromtimestamp(source.stat().st_mtime, timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                               "guard_source_sha256_at_export": sha256((ROOT / "keepers_boots/claims.py").read_bytes()).hexdigest()}}
        (directory / (case_id + ".json")).write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print("Exported calibration failure: " + case_id)


if __name__ == "__main__":
    main()
