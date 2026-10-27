"""Public contracts, cached inference and local-only configuration boundaries."""
import json
from pathlib import Path
from threading import Event
import unittest

from jsonschema import Draft202012Validator

from keepers_boots.agents import AgentWorkflow
from keepers_boots.api import APIError, KeeperCatalog, KeeperLoop
from keepers_boots.scenario import build_catalog


ROOT = Path(__file__).resolve().parents[1]


class CatalogTests(unittest.TestCase):
    def test_every_scenario_envelope_matches_the_public_schema(self):
        schema = json.loads((ROOT / "docs/api.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        catalog = KeeperCatalog()
        for scenario_id in build_catalog():
            start = catalog.start(scenario_id)
            session_id = start["session_id"]
            decision = catalog.decision(session_id)
            for operation in (catalog.evidence, catalog.reveal):
                with self.assertRaises(APIError) as caught:
                    operation(session_id)
                self.assertEqual(caught.exception.status, 409)
            option_id = decision["decision"]["options"][0]["option_id"]
            chosen = catalog.choose(session_id, option_id)
            revealed = catalog.reveal(session_id)
            self.assertEqual(chosen["assessment"], revealed["assessment"])
            for name, envelope in [("startResponse", start), ("decisionResponse", decision),
                                   ("evidenceResponse", chosen), ("revealResponse", revealed)]:
                with self.subTest(scenario=scenario_id, response=name):
                    contract = {"$ref": "#/$defs/" + name, "$defs": schema["$defs"]}
                    Draft202012Validator(contract).validate(envelope)
        with self.assertRaises(APIError):
            catalog.start("unknown")

    def test_background_interpretation_runs_once_and_never_mutates_assessment(self):
        entered, release = Event(), Event()
        class Workflow:
            calls = 0
            async def generate(self, snapshot, assessment):
                self.calls += 1
                entered.set()
                release.wait(3)
                return {"status": "fallback", "source": "deterministic", "reason": "test", "trace": []}
        workflow = Workflow()
        loop = KeeperLoop(workflow=workflow)
        first = loop.start()["session_id"]
        chosen = loop.choose(first, "short-right")
        self.assertTrue(entered.wait(2))
        self.assertEqual(chosen["interpretation"]["status"], "running")
        second = loop.start()["session_id"]
        for _ in range(3):
            self.assertEqual(loop.evidence(first)["assessment"], chosen["assessment"])
            loop.choose(first, "short-right")
        loop.choose(second, "switch-left")
        loop.reveal(first)
        release.set()
        self.assertEqual(workflow.calls, 1)
        self.assertEqual(loop.reveal(first)["assessment"], chosen["assessment"])

    def test_generated_fixtures_reproduce_from_the_owning_generator(self):
        filenames = ["01-tempting-short-pass.json", "02-the-press-arrives.json", "03-uncertain-outlet.json"]
        for scenario, filename in zip(build_catalog().values(), filenames):
            saved = json.loads((ROOT / "data/scenarios" / filename).read_text(encoding="utf-8"))
            self.assertEqual(scenario, saved)

    def test_agent_configuration_cannot_route_to_cloud_or_credentials(self):
        for endpoint in ["https://example.com/v1", "http://example.com/v1", "http://user:secret@localhost:8088/v1",
                         "http://localhost:8088/v1?key=secret", "http://localhost:8088/v1#secret"]:
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                AgentWorkflow(base_url=endpoint)
        with self.assertRaises(ValueError):
            AgentWorkflow(model="example:cloud")
        self.assertEqual(AgentWorkflow().base_url, "http://127.0.0.1:8088/v1")


if __name__ == "__main__":
    unittest.main()
