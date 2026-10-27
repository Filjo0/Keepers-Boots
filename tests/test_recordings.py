"""Captured agent demonstrations stay labelled, gated and bound to frozen evidence."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator

from keepers_boots.analysis import analyse_pressure, analyse_snapshot
from keepers_boots.api import APIError, KeeperCatalog, KeeperLoop
from keepers_boots.recordings import DIRECTORY, export_recording, load_recording, validate_recording
from keepers_boots.scenario import build_catalog
from keepers_boots.snapshots import freeze_snapshot


ROOT = Path(__file__).resolve().parents[1]


class RecordingTests(unittest.TestCase):
    def test_recorded_catalog_needs_no_agent_runtime_and_matches_the_api_contract(self):
        schema = json.loads((ROOT / "docs/api.schema.json").read_text(encoding="utf-8"))
        # If the replay accidentally imports either live runtime, fail immediately.
        with patch.dict("sys.modules", {"agent_framework": None, "agent_framework.openai": None, "openai": None}):
            catalog = KeeperCatalog(recorded=True)
            for scenario_id in build_catalog():
                started = catalog.start(scenario_id)
                session_id = started["session_id"]
                with self.assertRaises(APIError) as caught:
                    catalog.evidence(session_id)
                self.assertEqual(caught.exception.status, 409)
                decision = catalog.decision(session_id)
                option_id = decision["decision"]["options"][0]["option_id"]
                chosen = catalog.choose(session_id, option_id)
                interpretation = chosen["interpretation"]
                self.assertEqual(interpretation["source"], "recorded_agents")
                self.assertIn(interpretation["status"], ("reviewed", "insufficient_evidence"))
                self.assertEqual(interpretation["recording"]["snapshot_id"], decision["snapshot_id"])
                self.assertEqual(chosen["explanation"]["source"], "recorded_agents")
                self.assertEqual(chosen["explanation"]["summary"], interpretation["fan"])
                self.assertEqual(chosen, catalog.evidence(session_id))
                revealed = catalog.reveal(session_id)
                self.assertEqual(revealed["assessment"], chosen["assessment"])
                self.assertEqual(revealed["interpretation"], interpretation)
                for name, envelope in [("startResponse", started), ("decisionResponse", decision),
                                       ("evidenceResponse", chosen), ("revealResponse", revealed)]:
                    with self.subTest(scenario=scenario_id, envelope=name):
                        Draft202012Validator({"$ref": "#/$defs/" + name, "$defs": schema["$defs"]}).validate(envelope)
                raw = json.dumps(chosen)
                for hidden in ("continuation", "world_frames", "events", "scripted_option_id", "outcome"):
                    self.assertNotIn('"' + hidden + '"', raw)

    def test_recordings_do_not_depend_on_fan_choice_or_outcome(self):
        baseline = KeeperCatalog(recorded=True)
        alternate = KeeperCatalog("intercepted", recorded=True)
        for scenario_id in build_catalog():
            for option in build_catalog()[scenario_id]["decision"]["options"]:
                records = []
                for catalog in (baseline, alternate):
                    session_id = catalog.start(scenario_id)["session_id"]
                    records.append(catalog.choose(session_id, option["option_id"]))
                self.assertEqual(records[0], records[1])
                self.assertEqual(records[0]["interpretation"]["source"], "recorded_agents")

    def test_actual_capture_text_and_trace_are_preserved_without_the_old_wording_error(self):
        recording = json.loads((DIRECTORY / "tempting-short-pass.json").read_text(encoding="utf-8"))
        snapshot = freeze_snapshot(build_catalog()["tempting-short-pass"])
        result = validate_recording(recording, snapshot, analyse_snapshot(snapshot), analyse_pressure(snapshot))
        self.assertNotIn("before the keeper arrives", result["fan"])
        self.assertEqual(result["recording"]["notes"], [
            "Known wording flaw in the analyst text and a claim: scenario 1 tests no variation in preparation delay, so it does not establish that delay leaves the margin's width unchanged. This recording uses the prompt from before commit 7ee37ef; the later prompt fix did not regenerate it. Reviewer approval does not establish that inference."
        ])
        for field, value in recording["interpretation"].items():
            if field != "source":
                self.assertEqual(result[field], value, field + " was changed during replay")

    def test_stale_or_unchecked_recordings_are_not_displayed(self):
        snapshot = freeze_snapshot(build_catalog()["tempting-short-pass"])
        assessment, pressure = analyse_snapshot(snapshot), analyse_pressure(snapshot)
        original = json.loads((DIRECTORY / "tempting-short-pass.json").read_text(encoding="utf-8"))

        def change(path, value):
            recording = deepcopy(original)
            target = recording
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            return recording

        cases = [change(["recording", "snapshot_id"], "0" * 64),
                 change(["recording", "assessment_sha256"], "0" * 64),
                 change(["recording", "pressure_sha256"], "0" * 64),
                 change(["interpretation", "source"], "deterministic"),
                 change(["interpretation", "claims", 0, "evidence_ids"], ["unknown:geometry"]),
                 change(["interpretation", "fan"], "The recorded pass was completed."),
                 change(["interpretation", "fan"], "Both routes require similar preparation time before the keeper arrives."),
                 change(["interpretation", "trace", -1, "status"], "revise"),
                 change(["interpretation", "trace", 0, "detail"], "Test-only injected evidence"),
                 {**deepcopy(original), "continuation": {"outcome": "completed"}}]
        with tempfile.TemporaryDirectory() as directory, patch("keepers_boots.recordings.DIRECTORY", Path(directory)):
            path = Path(directory) / "tempting-short-pass.json"
            for index, recording in enumerate(cases):
                with self.subTest(case=index):
                    path.write_text(json.dumps(recording), encoding="utf-8")
                    result = load_recording(snapshot, assessment, pressure)
                    self.assertEqual(result["reason"], "recording_unavailable")
                    self.assertEqual(result["source"], "deterministic")
                    self.assertNotIn("fan", result)
                    self.assertNotIn("claims", result)

    def test_missing_recording_and_ambiguous_execution_mode_fail_safely(self):
        with tempfile.TemporaryDirectory() as directory, patch("keepers_boots.recordings.DIRECTORY", Path(directory)):
            loop = KeeperLoop(recorded=True)
            session_id = loop.start()["session_id"]
            result = loop.choose(session_id, "switch-left")
            self.assertEqual(result["interpretation"]["reason"], "recording_unavailable")
            self.assertEqual(result["explanation"]["source"], "deterministic")
        with self.assertRaises(ValueError):
            KeeperLoop(recorded=True, workflow=object())

    def test_export_preserves_the_capture_and_excludes_choice_and_other_payloads(self):
        snapshot = freeze_snapshot(build_catalog()["tempting-short-pass"])
        assessment, pressure = analyse_snapshot(snapshot), analyse_pressure(snapshot)
        recorded = json.loads((DIRECTORY / "tempting-short-pass.json").read_text(encoding="utf-8"))
        evidence = {"assessment": deepcopy(assessment), "pressure": deepcopy(pressure), "choice": "switch-left",
                    "explanation": {}, "interpretation": recorded["interpretation"]}
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "capture.json"
            source.write_text(json.dumps(evidence), encoding="utf-8")
            exported = export_recording(source, snapshot, assessment, pressure)
            self.assertEqual(exported["interpretation"], evidence["interpretation"])
            self.assertEqual(exported["recording"]["source_sha256"], sha256(source.read_bytes()).hexdigest())
            self.assertNotIn("choice", exported)
            self.assertNotIn("explanation", exported)
            evidence["assessment"]["snapshot_id"] = "0" * 64
            source.write_text(json.dumps(evidence), encoding="utf-8")
            with self.assertRaises(ValueError):
                export_recording(source, snapshot, assessment, pressure)


if __name__ == "__main__":
    unittest.main()
