from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import unittest

from keepers_boots.analysis import analyse_snapshot
from keepers_boots.scenario import build_scenario
from keepers_boots.snapshots import freeze_snapshot


def by_option(report):
    return {item["option_id"]: item for item in report["options"]}


class FoundationTests(unittest.TestCase):
    def test_future_outcomes_cannot_change_assessment(self):
        complete = build_scenario("completed")
        intercepted = build_scenario("intercepted")
        self.assertNotEqual(complete["continuation"], intercepted["continuation"])
        self.assertNotEqual(complete["world_frames"], intercepted["world_frames"])
        first, second = freeze_snapshot(complete), freeze_snapshot(intercepted)
        self.assertEqual(first, second)
        self.assertEqual(analyse_snapshot(first), analyse_snapshot(second))

    def test_unobserved_world_movement_cannot_change_assessment(self):
        scenario = build_scenario()
        observation = scenario["decision"]["observations"][12]
        observation["observed_at_ms"] = 1000
        altered = deepcopy(scenario)
        for frame in altered["world_frames"]:
            if frame["t_ms"] > 1000:
                frame["players"][12]["position_m"] = [30, 30]
        first, second = freeze_snapshot(scenario), freeze_snapshot(altered)
        self.assertEqual(first, second)
        self.assertEqual(analyse_snapshot(first), analyse_snapshot(second))
        self.assertEqual(analyse_snapshot(first)["status"], "insufficient_evidence")

    def test_refresh_can_change_available_evidence(self):
        scenario = build_scenario()
        observation = scenario["decision"]["observations"][12]
        observation["observed_at_ms"] = 1000
        stale = freeze_snapshot(scenario)
        observation["observed_at_ms"] = 2000
        fresh = freeze_snapshot(scenario)
        self.assertNotEqual(stale.snapshot_id, fresh.snapshot_id)
        self.assertEqual(analyse_snapshot(stale)["status"], "insufficient_evidence")
        self.assertEqual(analyse_snapshot(fresh)["status"], "model_evidence")

    def test_future_observation_rejected(self):
        scenario = build_scenario()
        scenario["decision"]["observations"][0]["observed_at_ms"] = 2001
        with self.assertRaisesRegex(ValueError, "after decision"):
            freeze_snapshot(scenario)

    def test_snapshot_is_independent_of_source_and_read_copies(self):
        scenario = build_scenario()
        snapshot = freeze_snapshot(scenario)
        original = snapshot.read()
        copy = snapshot.read()
        copy["observations"][0]["position_m"][0] = 90
        scenario["decision"]["observations"][0]["position_m"][0] = 91
        self.assertEqual(snapshot.read(), original)

    def test_tampered_snapshot_rejected(self):
        snapshot = freeze_snapshot(build_scenario())
        damaged = replace(snapshot, payload_json=snapshot.payload_json + " ")
        with self.assertRaisesRegex(ValueError, "digest"):
            analyse_snapshot(damaged)

    def test_unapproved_metadata_is_not_snapshotted(self):
        scenario = build_scenario()
        expected = freeze_snapshot(scenario)
        scenario["decision"]["future_outcome"] = "secret success"
        scenario["decision"]["observations"][0]["hidden_policy"] = "next action"
        scenario["decision"]["match_context"]["coach_intention"] = "unknown"
        self.assertEqual(freeze_snapshot(scenario), expected)

    def test_mirror_preserves_geometry(self):
        scenario = build_scenario()
        original = by_option(analyse_snapshot(freeze_snapshot(scenario)))
        mirrored = deepcopy(scenario)
        mirrored["decision"]["attack_direction"] = -1
        for observation in mirrored["decision"]["observations"]:
            observation["position_m"][0] = 105 - observation["position_m"][0]
        for option in mirrored["decision"]["options"]:
            option["target_m"][0] = 105 - option["target_m"][0]
        mirrored["decision"]["ball"]["position_m"][0] = 105 - mirrored["decision"]["ball"]["position_m"][0]
        reflected = by_option(analyse_snapshot(freeze_snapshot(mirrored)))
        for key in original:
            self.assertAlmostEqual(original[key]["route_length_m"], reflected[key]["route_length_m"], places=5)
            if original[key]["kind"] == "ground":
                for left, right in zip(original[key]["minimum_interception_margin_s"],
                                       reflected[key]["minimum_interception_margin_s"]):
                    self.assertAlmostEqual(left, right, places=5)
                self.assertEqual(original[key]["finding"], reflected[key]["finding"])

    def test_scenario_geometry_and_unsupported_option(self):
        report = analyse_snapshot(freeze_snapshot(build_scenario()))
        options = by_option(report)
        self.assertLess(options["short-right"]["minimum_interception_margin_s"][1], 0)
        self.assertGreater(options["switch-left"]["minimum_interception_margin_s"][0], 0)
        self.assertEqual(options["clear-long"]["status"], "not_modelled")
        self.assertNotIn("minimum_interception_margin_s", options["clear-long"])
        self.assertIsNone(report["ranking"])

    def test_all_opponents_are_included(self):
        scenario = build_scenario()
        last = next(item for item in scenario["decision"]["observations"] if item["player_id"] == "V11")
        last["position_m"] = [24, 12]
        options = by_option(analyse_snapshot(freeze_snapshot(scenario)))
        self.assertLess(options["switch-left"]["minimum_interception_margin_s"][1], 0)

    def test_faster_defenders_do_not_improve_margin(self):
        scenario = build_scenario()
        baseline = by_option(analyse_snapshot(freeze_snapshot(scenario)))
        scenario["decision"]["model"]["defender_speed_mps"] = [9, 12]
        changed = by_option(analyse_snapshot(freeze_snapshot(scenario)))
        for key in ("short-right", "switch-left"):
            self.assertLessEqual(changed[key]["minimum_interception_margin_s"][0],
                                 baseline[key]["minimum_interception_margin_s"][0])

    def test_invalid_numbers_rejected(self):
        for value in (float("nan"), float("inf"), -float("inf"), -1, True):
            with self.subTest(value=value):
                scenario = build_scenario()
                scenario["decision"]["observations"][0]["position_m"][0] = value
                with self.assertRaises(ValueError):
                    freeze_snapshot(scenario)
        scenario = build_scenario()
        scenario["decision"]["model"]["defender_speed_mps"] = [7, 4]
        with self.assertRaisesRegex(ValueError, "reversed"):
            freeze_snapshot(scenario)

    def test_missing_or_duplicate_opponent_rejected(self):
        for mode in ("missing", "duplicate"):
            with self.subTest(mode=mode):
                scenario = build_scenario()
                if mode == "missing":
                    scenario["decision"]["observations"].pop()
                else:
                    scenario["decision"]["observations"][-1] = deepcopy(scenario["decision"]["observations"][-2])
                with self.assertRaisesRegex(ValueError, "complete distinct"):
                    freeze_snapshot(scenario)

    def test_stale_or_uncontrolled_ball_is_not_assessed(self):
        scenario = build_scenario()
        scenario["decision"]["ball"]["observed_at_ms"] = 1000
        report = analyse_snapshot(freeze_snapshot(scenario))
        self.assertEqual(report["status"], "insufficient_evidence")
        self.assertIn("ball", report["stale_observation_ids"])
        scenario["decision"]["ball"]["controller_id"] = "V01"
        with self.assertRaisesRegex(ValueError, "keeper-controlled"):
            freeze_snapshot(scenario)

    def test_generation_is_reproducible_and_fixture_matches(self):
        generated = build_scenario()
        self.assertEqual(generated, build_scenario())
        fixture_path = Path(__file__).resolve().parents[1] / "data/scenarios/01-tempting-short-pass.json"
        self.assertEqual(json.loads(fixture_path.read_text(encoding="utf-8")), generated)
        for frame in generated["world_frames"]:
            self.assertEqual(len(frame["players"]), 22)
            for player in frame["players"]:
                x, y = player["position_m"]
                self.assertTrue(0 <= x <= 105 and 0 <= y <= 68)


if __name__ == "__main__":
    unittest.main()
