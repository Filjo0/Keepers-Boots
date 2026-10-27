"""Fast continuation checks: no model, MCP runtime or route sampling."""
import json
from hashlib import sha256
from pathlib import Path
import unittest

from keepers_boots.analysis import analyse_pressure, analyse_snapshot
from keepers_boots.api import KeeperLoop
from keepers_boots.scenario import build_catalog, build_uncertain_scenario
from keepers_boots.snapshots import freeze_snapshot


ROOT = Path(__file__).resolve().parents[1]


class RevealTests(unittest.TestCase):
    def test_wide_reveal_does_not_rewrite_available_evidence(self):
        complete = build_uncertain_scenario("completed")
        intercepted = build_uncertain_scenario("intercepted")
        self.assertEqual(freeze_snapshot(complete), freeze_snapshot(intercepted))
        self.assertEqual(analyse_snapshot(freeze_snapshot(complete)), analyse_snapshot(freeze_snapshot(intercepted)))
        metadata = json.loads((ROOT / "data/agent-recordings/uncertain-outlet.json").read_text(encoding="utf-8"))["recording"]
        snapshot = freeze_snapshot(complete)
        self.assertEqual(snapshot.snapshot_id, metadata["snapshot_id"])
        for field, value in [("assessment_sha256", analyse_snapshot(snapshot)), ("pressure_sha256", analyse_pressure(snapshot))]:
            digest = sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()
            self.assertEqual(digest, metadata[field])
        self.assertEqual(complete["continuation"]["scripted_option_id"], "switch-left")
        self.assertEqual(complete["events"][0]["target_player_id"], "H03")
        for scenario, recipient in [(complete, "H03"), (intercepted, "V03")]:
            event = scenario["events"][1]
            frame = next(item for item in scenario["world_frames"] if item["t_ms"] == event["t_ms"])
            player = next(item for item in frame["players"] if item["player_id"] == recipient)
            self.assertEqual(frame["ball"]["position_m"], player["position_m"])
        self.assertEqual(complete["world_frames"][-1]["ball"]["position_m"], [24, 12])

    def test_api_reveals_the_wide_action_without_exposing_the_hidden_position_early(self):
        loop = KeeperLoop(build_uncertain_scenario())
        start = loop.start("uncertain-outlet")
        last_seen = next(item for item in start["frames"][-1]["players"] if item["player_id"] == "V03")
        self.assertEqual(last_seen["position_m"], [31, 21])
        chosen = loop.choose(start["session_id"], "switch-left")
        reveal = loop.reveal(start["session_id"])
        self.assertEqual(chosen["assessment"], reveal["assessment"])
        self.assertIn("Switch left", reveal["recap"]["recorded_outcome"])
        self.assertIn("missing", reveal["recap"]["assessment_context"])
        self.assertEqual(reveal["frames"][-1]["ball"]["position_m"], [24, 12])

    def test_each_fixture_reproduces_and_the_reveals_are_not_all_identical(self):
        catalog = build_catalog()
        names = ["01-tempting-short-pass.json", "02-the-press-arrives.json", "03-uncertain-outlet.json"]
        for scenario, filename in zip(catalog.values(), names):
            with self.subTest(filename=filename):
                self.assertEqual(scenario, json.loads((ROOT / "data/scenarios" / filename).read_text(encoding="utf-8")))
        self.assertNotEqual(catalog["tempting-short-pass"]["world_frames"], catalog["press-arrives"]["world_frames"])
        self.assertNotEqual(catalog["tempting-short-pass"]["events"], catalog["uncertain-outlet"]["events"])


if __name__ == "__main__":
    unittest.main()
