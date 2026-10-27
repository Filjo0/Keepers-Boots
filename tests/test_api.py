from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stderr
from copy import deepcopy
from email.message import Message
from http.client import HTTPConnection
import io
import json
import sys
from threading import Thread
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from keepers_boots.analysis import analyse_snapshot
from keepers_boots.api import APIError, KeeperHandler, KeeperLoop, KeeperServer, main, private_lan_ipv4
from keepers_boots.scenario import build_scenario


class LoopTests(unittest.TestCase):
    def setUp(self):
        self.loop = KeeperLoop()
        self.started = self.loop.start()
        self.session_id = self.started["session_id"]

    def test_predecision_has_no_continuation_events_or_velocity(self):
        self.assertEqual(self.started["frames"][-1]["t_ms"], 2000)
        for frame in self.started["frames"]:
            self.assertLessEqual(frame["t_ms"], 2000)
        for forbidden in ("continuation", "events", "outcome", "scripted_option_id", "velocity_mps"):
            self.assertNotIn(f'"{forbidden}"', json.dumps(self.started))
            self.assertNotIn(f'"{forbidden}"', json.dumps(self.loop.decision(self.session_id)))
        for operation in (self.loop.evidence, self.loop.reveal):
            with self.assertRaises(APIError) as caught:
                operation(self.session_id)
            self.assertEqual(caught.exception.status, 409)

    def test_alternative_outcomes_have_identical_prelude_and_evidence(self):
        alternate = KeeperLoop(build_scenario("intercepted"))
        started = alternate.start()
        original = dict(self.started)
        original.pop("session_id")
        started_id = started.pop("session_id")
        self.assertEqual(original, started)
        first = self.loop.choose(self.session_id, "short-right")
        second = alternate.choose(started_id, "short-right")
        self.assertEqual(first, second)
        self.assertNotEqual(self.loop.reveal(self.session_id)["continuation"], alternate.reveal(started_id)["continuation"])
        self.assertEqual(first, self.loop.evidence(self.session_id))
        self.assertEqual(second, alternate.evidence(started_id))

    def test_decision_display_uses_observations_and_drops_future_velocity(self):
        scenario = build_scenario()
        altered = deepcopy(scenario)
        decision_frame = next(frame for frame in altered["world_frames"] if frame["t_ms"] == 2000)
        decision_frame["players"][0]["position_m"] = [99, 66]
        decision_frame["players"][0]["velocity_mps"] = [123456, 654321]
        decision_frame["ball"]["position_m"] = [99, 66]
        altered["decision"]["hidden_policy"] = "future outcome"
        alternate = KeeperLoop(altered)
        started = alternate.start()
        self.assertEqual(self.started["frames"], started["frames"])
        self.assertEqual(self.loop.decision(self.session_id), alternate.decision(started["session_id"]))

    def test_assessment_is_computed_once_even_across_concurrent_retries(self):
        with patch("keepers_boots.api.analyse_snapshot", wraps=analyse_snapshot) as analyse:
            with ThreadPoolExecutor(max_workers=4) as executor:
                responses = list(executor.map(lambda _: self.loop.choose(self.session_id, "short-right"), range(4)))
            self.assertEqual(analyse.call_count, 1)
        for response in responses:
            self.assertEqual(response, responses[0])
        self.loop.reveal(self.session_id)
        self.assertEqual(responses[0], self.loop.evidence(self.session_id))
        with self.assertRaises(APIError) as caught:
            self.loop.choose(self.session_id, "switch-left")
        self.assertEqual(caught.exception.status, 409)

    def test_source_and_response_mutation_cannot_change_session(self):
        scenario = build_scenario()
        loop = KeeperLoop(scenario)
        scenario["continuation"]["outcome"] = "intercepted"
        started = loop.start()
        started["frames"][-1]["players"][0]["position_m"][0] = 99
        chosen = loop.choose(started["session_id"], "clear-long")
        original = deepcopy(chosen)
        chosen["assessment"]["options"][0]["route_length_m"] = 999
        revealed = loop.reveal(started["session_id"])
        self.assertEqual(revealed["continuation"]["outcome"], "completed")
        self.assertIn("does not simulate your choice", revealed["recap"]["choice_context"])
        self.assertEqual(original, loop.evidence(started["session_id"]))
        revealed["events"].clear()
        self.assertTrue(loop.reveal(started["session_id"])["events"])
        self.assertEqual(loop.decision(started["session_id"])["decision"]["ball"]["position_m"], [8, 34])

    def test_each_option_can_be_selected_without_an_overall_ranking(self):
        for option in ("short-right", "switch-left", "clear-long"):
            with self.subTest(option=option):
                session_id = self.loop.start()["session_id"]
                chosen = self.loop.choose(session_id, option)
                self.assertIsNone(chosen["assessment"]["ranking"])
                self.assertEqual(chosen["choice"], option)
                self.assertEqual(chosen["explanation"]["source"], "deterministic")
                self.assertEqual(self.loop.reveal(session_id), self.loop.reveal(session_id))

    def test_stale_information_abstains_and_does_not_get_world_replacement(self):
        scenario = build_scenario()
        scenario["decision"]["observations"][0]["observed_at_ms"] = 1000
        loop = KeeperLoop(scenario)
        session_id = loop.start()["session_id"]
        evidence = loop.choose(session_id, "switch-left")
        self.assertEqual(evidence["assessment"]["status"], "insufficient_evidence")
        self.assertEqual(evidence["explanation"]["options"], [])
        self.assertIn("old", evidence["explanation"]["summary"])
        self.assertEqual(loop.decision(session_id)["decision"]["observations"][0]["observed_at_ms"], 1000)

    def test_unknown_identifiers_capacity_and_expiry(self):
        for option in (None, True, [], "unknown"):
            with self.assertRaises(APIError) as caught:
                self.loop.choose(self.session_id, option)
            self.assertEqual(caught.exception.status, 400)
        with self.assertRaises(APIError):
            self.loop.start("unknown")
        with self.assertRaises(APIError):
            self.loop.decision("unknown")
        now = [0]
        bounded = KeeperLoop(max_sessions=1, session_ttl_s=10, clock=lambda: now[0])
        old = bounded.start()["session_id"]
        with self.assertRaises(APIError) as caught:
            bounded.start()
        self.assertEqual(caught.exception.status, 503)
        now[0] = 10
        bounded.start()
        with self.assertRaises(APIError) as caught:
            bounded.reveal(old)
        self.assertEqual(caught.exception.status, 404)


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = KeeperServer(("127.0.0.1", 0))
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def request(self, method, path, body=None, headers=None):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        actual_headers = {"Content-Type": "application/json", **(headers or {})}
        payload = None if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode())
        try:
            connection.request(method, path, payload, actual_headers)
            response = connection.getresponse()
            content = response.read()
            return response.status, dict(response.getheaders()), content
        finally:
            connection.close()

    def test_http_loop_gating_and_static_allowlist(self):
        status, headers, content = self.request("POST", "/api/start", {})
        self.assertEqual(status, 201)
        self.assertEqual(headers["Cache-Control"], "no-store")
        started = json.loads(content)
        base = f'/api/sessions/{started["session_id"]}'
        self.assertEqual(self.request("POST", base + "/reveal", {})[0], 409)
        self.assertEqual(self.request("GET", base + "/evidence")[0], 409)
        self.assertEqual(self.request("GET", base + "/decision")[0], 200)
        choice = self.request("POST", base + "/choice", {"option_id": "switch-left"})
        self.assertEqual(choice[0], 200)
        revealed = self.request("POST", base + "/reveal", {})
        self.assertEqual(revealed[0], 200)
        self.assertEqual(json.loads(choice[2])["assessment"], json.loads(revealed[2])["assessment"])
        self.assertEqual(self.request("GET", base + "/reveal")[0], 405)
        for path, mime in (("/", "text/html"), ("/app.js", "text/javascript"), ("/styles.css", "text/css"), ("/api/schema", "application/schema+json")):
            with self.subTest(path=path):
                status, headers, content = self.request("GET", path)
                self.assertEqual(status, 200)
                self.assertTrue(headers["Content-Type"].startswith(mime))
                self.assertTrue(content)
        for path in ("/data/scenarios/01-tempting-short-pass.json", "/../README.md", "/keepers_boots/api.py", "/api/sessions/invalid/decision"):
            self.assertEqual(self.request("GET", path)[0], 404)

    def test_http_rejects_unbounded_invalid_and_cross_origin_requests(self):
        cases = [(b"{bad", {}, 400), ([], {}, 400), ({"extra": 1}, {}, 400),
                 (b" " * 1025, {}, 413), ({}, {"Content-Type": "text/plain"}, 415),
                 ({}, {"Origin": "https://other.example"}, 403),
                 ({}, {"Host": "other.example"}, 403), ({}, {"Sec-Fetch-Site": "cross-site"}, 403),
                 ({}, {"Transfer-Encoding": "chunked"}, 400)]
        for body, headers, expected in cases:
            with self.subTest(headers=headers, expected=expected):
                self.assertEqual(self.request("POST", "/api/start", body, headers)[0], expected)
        self.assertEqual(self.request("POST", "/api/start", {"scenario_id": "unknown"})[0], 404)
        missing = "/api/sessions/" + "0" * 32 + "/decision"
        self.assertEqual(self.request("GET", missing)[0], 404)


class LANPolicyTests(unittest.TestCase):
    def test_only_explicit_rfc1918_ipv4_addresses_are_accepted(self):
        for address in ("10.2.3.4", "172.16.0.2", "172.31.255.254", "192.168.50.10"):
            self.assertEqual(private_lan_ipv4(address), address)
        for address in ("0.0.0.0", "127.0.0.1", "8.8.8.8", "169.254.1.2", "172.32.0.1", "192.0.2.1", "localhost", "::1"):
            with self.subTest(address=address), self.assertRaises(ValueError):
                private_lan_ipv4(address)
        with self.assertRaisesRegex(ValueError, "bind address"):
            KeeperServer(("127.0.0.1", 0), lan_ip="192.168.50.10")

    def policy(self, pairs, lan_ip="192.168.50.10"):
        handler = KeeperHandler.__new__(KeeperHandler)
        handler.server = SimpleNamespace(server_port=8000, lan_ip=lan_ip)
        handler.headers = Message()
        for key, value in pairs:
            handler.headers[key] = value
        return handler._local_request()

    def test_lan_host_and_origin_must_match_exactly(self):
        host = "192.168.50.10:8000"
        self.policy([("Host", host)])
        self.policy([("Host", host), ("Origin", "http://" + host)])
        cases = [[], [("Host", "127.0.0.1:8000")], [("Host", "192.168.1.249:8000")],
                 [("Host", "192.168.50.10:8001")], [("Host", "evil.example:8000")],
                 [("Host", host), ("Host", host)],
                 [("Host", host), ("Origin", "https://" + host)],
                 [("Host", host), ("Origin", "null")],
                 [("Host", host), ("Origin", "http://evil.example")],
                 [("Host", host), ("Origin", "http://" + host), ("Origin", "http://" + host)],
                 [("Host", host), ("Sec-Fetch-Site", "cross-site")]]
        for pairs in cases:
            with self.subTest(pairs=pairs), self.assertRaises(APIError) as caught:
                self.policy(pairs)
            self.assertEqual(caught.exception.status, 403)

    def test_loopback_default_still_rejects_lan_host(self):
        self.policy([("Host", "localhost:8000")], lan_ip=None)
        self.policy([("Host", "127.0.0.1:8000")], lan_ip=None)
        with self.assertRaises(APIError):
            self.policy([("Host", "192.168.50.10:8000")], lan_ip=None)

    def test_lan_cli_refuses_live_or_default_modes_before_starting_any_server(self):
        for mode in ("off", "local"):
            with self.subTest(mode=mode), patch.object(sys, "argv", ["api", "--agents", mode, "--lan-ip", "192.168.50.10"]):
                with patch("keepers_boots.api.KeeperServer") as server, redirect_stderr(io.StringIO()) as output:
                    with self.assertRaises(SystemExit) as caught:
                        main()
                    self.assertEqual(caught.exception.code, 2)
                    self.assertIn("requires --agents recorded", output.getvalue())
                    server.assert_not_called()


if __name__ == "__main__":
    unittest.main()
