"""Capture selection and calibration failures remain inspectable and separate."""
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from keepers_boots.claims import validate_draft
from keepers_boots.scenario import build_scenario
from keepers_boots.snapshots import freeze_snapshot
from tools.agent_smoke import save_observation


ROOT = Path(__file__).resolve().parents[1]


class CaptureAuditTests(unittest.TestCase):
    def test_each_observation_is_preserved_with_cache_status_and_content_hash(self):
        evidence = {"assessment": {"snapshot_id": "a" * 64},
                    "interpretation": {"source": "deterministic", "status": "fallback"}}
        with tempfile.TemporaryDirectory() as directory:
            first = save_observation(Path(directory), "tempting-short-pass", evidence, True)
            first_bytes = first.read_bytes()
            second = save_observation(Path(directory), "tempting-short-pass", evidence, False)
            self.assertNotEqual(first, second)
            self.assertEqual(first.read_bytes(), first_bytes)
            for path, fresh in ((first, True), (second, False)):
                metadata = json.loads(path.with_suffix(".meta.json").read_text(encoding="utf-8"))
                self.assertEqual(metadata["fresh_job_observed"], fresh)
                self.assertEqual(metadata["capture_sha256"], sha256(path.read_bytes()).hexdigest())
                self.assertEqual(json.loads(path.read_text(encoding="utf-8")), evidence)

    def test_calibration_misses_preserve_approved_text_and_current_guard_failures(self):
        snapshot = freeze_snapshot(build_scenario())
        cases = list((ROOT / "data/evaluation/calibration").glob("*.json"))
        self.assertEqual(len(cases), 2)
        for path in cases:
            case = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(case["classification"], "calibration_failure")
            self.assertEqual(case["decision"], snapshot.read())
            interpretation = case["interpretation"]
            self.assertEqual(interpretation["trace"][-1]["status"], "accept")
            draft = {"snapshot_id": snapshot.snapshot_id, "ranking": None,
                     **{name: interpretation[name] for name in ("claims", "fan", "analyst", "missing_information")}}
            errors = validate_draft(draft, snapshot, case["assessment"])[1]
            self.assertEqual(errors, case["audit"]["current_guard_errors"])
            self.assertTrue(errors)
            self.assertFalse(case["audit"]["paired_analyst_only_result_available"])
            raw = json.dumps(case)
            for hidden in ("continuation", "world_frames", "events", "velocity_mps", "outcome", "choice"):
                self.assertNotIn('"' + hidden + '"', raw)


if __name__ == "__main__":
    unittest.main()
