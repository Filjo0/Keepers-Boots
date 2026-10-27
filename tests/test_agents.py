import asyncio
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

from keepers_boots.agents import AgentWorkflow
from keepers_boots.analysis import analyse_pressure, analyse_snapshot
from keepers_boots.api import KeeperLoop
from keepers_boots.claims import draft_schema, validate_draft
from keepers_boots.mcp_server import EvidenceTools, TOOLS
from keepers_boots.scenario import build_catalog, build_press_scenario, build_scenario
from keepers_boots.snapshots import freeze_snapshot


def draft_for(snapshot, text="A sampled timing opportunity is not the same as a realised outcome."):
    return {"snapshot_id": snapshot.snapshot_id, "ranking": None,
            "claims": [{"claim_id": "c1", "evidence_ids": ["short-right:geometry"], "principle_ids": ["K04"], "text": text}],
            "fan": "Compare the routes under the model assumptions; an aerial clearance remains unranked.",
            "analyst": "The sampled ground-route comparison leaves aerial possession and real execution unresolved.", "missing_information": []}


class ScenarioTests(unittest.TestCase):
    def test_signed_comparison_is_computed_for_matching_parameter_cases(self):
        report = analyse_snapshot(freeze_snapshot(build_press_scenario()))
        comparison = report["comparisons"][0]
        self.assertEqual(comparison["larger_margin_option_id"], "release-short")
        self.assertEqual(comparison["smaller_margin_option_id"], "take-touch")
        self.assertEqual(comparison["basis"], "matched_parameter_cases")
        self.assertAlmostEqual(comparison["margin_difference_s"], 0.65)
        first = analyse_snapshot(freeze_snapshot(build_scenario()))["comparisons"][0]
        self.assertEqual(first["larger_margin_option_id"], "switch-left")
        self.assertEqual(first["basis"], "parameter_range_extrema")
        stale = analyse_snapshot(freeze_snapshot(build_catalog()["uncertain-outlet"]))
        self.assertEqual(stale["comparisons"], [])

    def test_three_scenarios_no_hindsight_and_no_unseen_replay_movement(self):
        completed, intercepted = build_catalog(), build_catalog("intercepted")
        self.assertEqual(len(completed), 3)
        for name, scenario in completed.items():
            with self.subTest(scenario=name):
                first, second = freeze_snapshot(scenario), freeze_snapshot(intercepted[name])
                self.assertEqual(first, second)
                self.assertEqual(analyse_snapshot(first), analyse_snapshot(second))
                a, b = KeeperLoop(scenario), KeeperLoop(intercepted[name])
                self.assertEqual(a.start(name)["frames"], b.start(name)["frames"])
        uncertain = analyse_snapshot(freeze_snapshot(completed["uncertain-outlet"]))
        self.assertEqual(uncertain["status"], "insufficient_evidence")
        self.assertEqual(uncertain["uncertainty_regions"][0]["radius_m"], 6.5)
        self.assertIsNone(uncertain["ranking"])

    def test_extra_preparation_cannot_improve_timing(self):
        scenario = build_press_scenario()
        baseline = analyse_pressure(freeze_snapshot(scenario))
        arrival = baseline["arrival_after_decision_s"]
        self.assertLess(arrival[0], 0.95)
        self.assertGreater(arrival[0], 0.3)
        scenario["decision"]["options"][0]["preparation_delay_s"] += 0.2
        changed = analyse_pressure(freeze_snapshot(scenario))
        for original, later in zip(baseline["options"][0]["release_before_pressure_margin_s"], changed["options"][0]["release_before_pressure_margin_s"]):
            self.assertLess(later, original)
        report = analyse_snapshot(freeze_snapshot(scenario))
        touch, release = report["options"][:2]
        for delayed, immediate in zip(touch["minimum_interception_margin_s"], release["minimum_interception_margin_s"]):
            self.assertLess(delayed, immediate)


class ToolTests(unittest.TestCase):
    def test_direction_guard_rejects_a_reversed_signed_comparison(self):
        snapshot = freeze_snapshot(build_press_scenario())
        assessment = analyse_snapshot(snapshot)
        draft = draft_for(snapshot, "The release-short option has a smaller minimum interception margin than take-touch.")
        draft["claims"][0]["evidence_ids"] = ["comparison:take-touch:release-short"]
        self.assertIn("comparison_direction_mismatch:c1", validate_draft(draft, snapshot, assessment)[1])
        for text in ["The release-short option has a larger minimum interception margin than take-touch.",
                     "The release-short option does not have a smaller minimum interception margin than take-touch."]:
            draft["claims"][0]["text"] = text
            self.assertEqual(validate_draft(draft, snapshot, assessment)[1], [])
        tools = EvidenceTools([snapshot])
        self.assertEqual(tools.compare_options(snapshot.snapshot_id, ["release-short"])["comparisons"], [])

    def setUp(self):
        self.snapshot = freeze_snapshot(build_scenario())
        self.tools = EvidenceTools([self.snapshot])

    def test_tool_boundary_and_validation(self):
        state = self.tools.get_decision_state(self.snapshot.snapshot_id)
        self.assertNotIn("world_frames", json.dumps(state))
        self.assertNotIn("continuation", json.dumps(state))
        state["decision"]["ball"]["position_m"][0] = 99
        self.assertEqual(self.tools.get_decision_state(self.snapshot.snapshot_id)["decision"]["ball"]["position_m"], [8, 34])
        self.assertEqual(self.tools.analyse_pass_option(self.snapshot.snapshot_id, "clear-long")["option"]["status"], "not_modelled")
        self.assertEqual(self.tools.get_principle("K04")["review_status"], "draft")
        with self.assertRaises(ValueError):
            self.tools.get_decision_state("unknown")
        for ids in (["bad"], ["short-right", "short-right"], [], [True]):
            with self.assertRaises(ValueError):
                self.tools.compare_options(self.snapshot.snapshot_id, ids)
        with self.assertRaises(ValueError):
            self.tools.get_principle("private-kb")
        with self.assertRaises(TypeError):
            EvidenceTools([build_scenario()])

    def test_numeric_ids_time_and_outcome_guards(self):
        assessment = analyse_snapshot(self.snapshot)
        for change, expected in (({"snapshot_id": "bad"}, "snapshot_id_mismatch"),
                                 ({"fan": "The pass was completed."}, "future_or_outcome_claim"),
                                 ({"fan": "Margin is 999 seconds."}, "unrendered_number"),
                                 ({"fan": "The best action is guaranteed."}, "unsupported_scope")):
            draft = draft_for(self.snapshot)
            draft.update(change)
            self.assertIn(expected, validate_draft(draft, self.snapshot, assessment)[1])
        draft = draft_for(self.snapshot)
        draft["claims"][0]["evidence_ids"] = ["future:outcome"]
        self.assertIn("unknown_evidence_id:c1", validate_draft(draft, self.snapshot, assessment)[1])
        self.assertEqual(validate_draft(draft_for(self.snapshot), self.snapshot, assessment)[1], [])
        draft = draft_for(self.snapshot)
        draft["fan"] = "No overall best action is established; this is not a completion probability."
        self.assertEqual(validate_draft(draft, self.snapshot, assessment)[1], [])
        draft["analyst"] = "There is no guarantee, but the best action is the wider pass."
        self.assertIn("unsupported_scope", validate_draft(draft, self.snapshot, assessment)[1])
        draft = draft_for(self.snapshot)
        draft["analyst"] = "The model does not measure pass completion probability or subsequent possession."
        self.assertEqual(validate_draft(draft, self.snapshot, assessment)[1], [])
        draft["analyst"] += " The completion probability is certain."
        self.assertIn("unsupported_scope", validate_draft(draft, self.snapshot, assessment)[1])
        draft = draft_for(self.snapshot)
        draft["analyst"] = "K04 is an original draft principle about ground routes; H02 is an observed outlet."
        self.assertEqual(validate_draft(draft, self.snapshot, assessment)[1], [])
        draft["analyst"] = "K99 endorses H99 with a margin of 999 seconds."
        errors = validate_draft(draft, self.snapshot, assessment)[1]
        for expected in ("unknown_principle_id_in_prose", "unknown_player_id", "unrendered_number"):
            self.assertIn(expected, errors)

    def test_pressure_arrival_subject_guard_rejects_the_observed_keeper_wording(self):
        assessment = analyse_snapshot(self.snapshot)
        for field in ("fan", "analyst", "claim", "missing_information"):
            draft = draft_for(self.snapshot)
            wrong = "Both routes require similar preparation time before the keeper arrives."
            if field == "claim":
                draft["claims"][0]["text"] = wrong
            elif field == "missing_information":
                draft[field] = [wrong]
            else:
                draft[field] = wrong
            with self.subTest(field=field):
                self.assertIn("pressure_arrival_subject_mismatch", validate_draft(draft, self.snapshot, assessment)[1])
        draft = draft_for(self.snapshot)
        draft["fan"] = "The model compares release timing with the pressing opponent reaching the keeper."
        self.assertEqual(validate_draft(draft, self.snapshot, assessment)[1], [])

    def test_observed_false_joint_margin_polarity_is_rejected(self):
        assessment = analyse_snapshot(self.snapshot)
        draft = draft_for(self.snapshot)
        for sign, option_id in (("positive", "short-right"), ("negative", "switch-left")):
            draft["claims"][0]["text"] = "Both ground options show " + sign + " margins, but the comparison only covers sampled timing."
            draft["claims"][0]["evidence_ids"] = ["short-right:geometry", "switch-left:geometry"]
            self.assertIn("ground_margin_polarity_mismatch:" + sign + ":" + option_id,
                          validate_draft(draft, self.snapshot, assessment)[1])
        draft["claims"][0]["text"] = "The ground routes have different sampled timing findings."
        self.assertEqual(validate_draft(draft, self.snapshot, assessment)[1], [])

    def test_observed_mid_sentence_prose_is_rejected(self):
        assessment = analyse_snapshot(self.snapshot)
        draft = draft_for(self.snapshot)
        draft["analyst"] = "Therefore, the trade-off is between the larger, *"
        self.assertIn("incomplete_prose:analyst", validate_draft(draft, self.snapshot, assessment)[1])
        draft["analyst"] = "The sampled timing comparison leaves real execution unresolved."
        self.assertEqual(validate_draft(draft, self.snapshot, assessment)[1], [])

    def test_generation_schema_binds_snapshot_and_citations(self):
        from pydantic import ValidationError
        assessment = analyse_snapshot(self.snapshot)
        schema = draft_schema(self.snapshot, assessment)
        schema.model_validate(draft_for(self.snapshot))
        for text in ("The margin is 999 seconds.", "The model version is v0.2."):
            draft = draft_for(self.snapshot)
            draft["analyst"] = text
            with self.assertRaises(ValidationError):
                schema.model_validate(draft)
        allowed = draft_for(self.snapshot)
        allowed["fan"] = "K04 prompts consideration of the route to H02."
        schema.model_validate(allowed)
        for text in ['A "quoted" claim.', "A backslash \\", "A control\ncharacter.", "A" * 221]:
            draft = draft_for(self.snapshot)
            draft["claims"][0]["text"] = text
            with self.assertRaises(ValidationError):
                schema.model_validate(draft)
        for mutation in ("unknown_reference", "unknown_snapshot"):
            draft = draft_for(self.snapshot)
            if mutation == "unknown_reference":
                draft["claims"][0]["evidence_ids"] = ["invented:geometry"]
            else:
                draft["snapshot_id"] = "0" * 64
            with self.assertRaises(ValidationError):
                schema.model_validate(draft)
        stale = freeze_snapshot(build_catalog()["uncertain-outlet"])
        abstention = draft_for(stale)
        abstention["claims"][0]["evidence_ids"] = ["observations:age"]
        abstention["missing_information"] = ["A current opponent observation."]
        draft_schema(stale, analyse_snapshot(stale)).model_validate(abstention)
        abstention["claims"].append({**abstention["claims"][0], "claim_id": "c2"})
        with self.assertRaises(ValidationError):
            draft_schema(stale, analyse_snapshot(stale)).model_validate(abstention)

    def test_pressure_claim_needs_the_pressure_evidence_reference(self):
        draft = draft_for(self.snapshot, "Both ground options have the same release-before-pressure margin.")
        assessment = analyse_snapshot(self.snapshot)
        self.assertIn("pressure_evidence_required:c1:pressure:arrival", validate_draft(draft, self.snapshot, assessment)[1])
        draft["claims"][0]["evidence_ids"].append("pressure:arrival")
        self.assertEqual(validate_draft(draft, self.snapshot, assessment)[1], [])


class WorkflowTests(unittest.IsolatedAsyncioTestCase):
    async def test_review_status_and_rejected_claims_cannot_be_overridden_by_benign_reasons(self):
        snapshot = freeze_snapshot(build_scenario())
        for status, rejected in (("insufficient_evidence", []), ("accept", ["c1"])):
            with self.subTest(status=status):
                async def runner(role, prompt, schema):
                    if role == "analyst":
                        return draft_for(snapshot)
                    return {"status": status, "rejected_claim_ids": rejected,
                            "reasons": ["No unsupported statements."]}
                result = await AgentWorkflow(runner=runner).generate(snapshot, analyse_snapshot(snapshot))
                self.assertEqual(result["source"], "deterministic")
                self.assertEqual(result["reason"], "review_not_accepted")
                self.assertEqual(sum(step["stage"] == "repair" for step in result["trace"]), 1)
                self.assertEqual(sum(step["stage"] == "reviewer" for step in result["trace"]), 2)

    async def test_reviewer_repairs_semantic_overclaim_with_frozen_evidence(self):
        snapshot = freeze_snapshot(build_scenario())
        calls = []
        async def runner(role, prompt, schema):
            calls.append((role, prompt))
            self.assertNotIn('"continuation"', prompt)
            self.assertNotIn('"events"', prompt)
            if role == "analyst":
                return draft_for(snapshot, "The wider route creates better buildup." if len(calls) == 1 else "A sampled margin does not establish subsequent possession.")
            return {"status": "revise", "rejected_claim_ids": ["c1"], "reasons": ["Buildup value is not measured by point-arrival evidence."]} if len(calls) == 2 else {"status": "accept", "rejected_claim_ids": [], "reasons": ["The repaired scope is supported."]}
        result = await AgentWorkflow(runner=runner).generate(snapshot, analyse_snapshot(snapshot))
        self.assertEqual(result["status"], "reviewed")
        self.assertEqual([role for role, _ in calls], ["analyst", "reviewer", "analyst", "reviewer"])
        self.assertEqual([step["status"] for step in result["trace"] if step["stage"] == "reviewer"], ["revise", "accept"])

    async def test_invalid_draft_and_timeout_fall_back_with_no_unchecked_prose(self):
        snapshot = freeze_snapshot(build_scenario())
        calls = []
        async def bad(role, prompt, schema):
            calls.append(role)
            return draft_for(snapshot, "The pass was completed with a margin of 999 seconds.")
        result = await AgentWorkflow(runner=bad).generate(snapshot, analyse_snapshot(snapshot))
        self.assertEqual(result["status"], "fallback")
        self.assertEqual(calls, ["analyst", "analyst"])
        self.assertNotIn("fan", result)
        async def slow(*args):
            await asyncio.sleep(1)
        result = await AgentWorkflow(runner=slow, timeout_s=0.01).generate(snapshot, analyse_snapshot(snapshot))
        self.assertEqual(result["status"], "fallback")
        self.assertEqual(result["reason"], "TimeoutError")

    async def test_live_stdio_lists_exact_five_tools_and_rejects_unknown_ids(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        params = StdioServerParameters(command=sys.executable, args=["-m", "keepers_boots.mcp_server"], cwd=str(Path(__file__).resolve().parents[1]))
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                listed = await session.list_tools()
                self.assertEqual({tool.name for tool in listed.tools}, set(TOOLS))
                self.assertTrue(all(tool.outputSchema for tool in listed.tools))
                snapshot = freeze_snapshot(build_scenario())
                requests = {"get_decision_state": {"snapshot_id": snapshot.snapshot_id},
                            "analyse_pass_option": {"snapshot_id": snapshot.snapshot_id, "option_id": "short-right"},
                            "analyse_pressure": {"snapshot_id": snapshot.snapshot_id},
                            "compare_options": {"snapshot_id": snapshot.snapshot_id, "option_ids": ["short-right", "switch-left"]},
                            "get_principle": {"principle_id": "K04"}}
                for name, arguments in requests.items():
                    response = await session.call_tool(name, arguments)
                    self.assertFalse(response.isError, name)
                    self.assertIsNotNone(response.structuredContent, name)
                    self.assertNotIn('"continuation"', json.dumps(response.structuredContent))
                response = await session.call_tool("get_decision_state", {"snapshot_id": "unknown"})
                self.assertTrue(response.isError)


if __name__ == "__main__":
    unittest.main()
