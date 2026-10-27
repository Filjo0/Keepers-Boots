"""Local browser/API loop. Uses synthetic data and the Python standard library."""
import argparse
import asyncio
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from ipaddress import IPv4Address, IPv4Network
import json
from pathlib import Path
import re
from threading import RLock, Semaphore, Thread
from time import monotonic
from uuid import uuid4

from .analysis import analyse_pressure, analyse_snapshot
from .scenario import SCENARIOS, build_catalog, build_scenario
from .snapshots import freeze_snapshot


ROOT = Path(__file__).resolve().parent.parent
LAN_NETWORKS = tuple(IPv4Network(value) for value in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"))


def private_lan_ipv4(value):
    address = IPv4Address(value)
    if not any(address in network for network in LAN_NETWORKS):
        raise ValueError("Use the laptop's private Wi-Fi IPv4 address.")
    return str(address)


FINDINGS = {
    "interception_reachable_in_all_tested_parameter_combinations":
        "A defender can reach this route before the ball in every tested parameter combination.",
    "positive_margin_at_sampled_points_in_all_tested_parameter_combinations":
        "The ball arrives before defenders at the sampled points in every tested parameter combination.",
    "finding_changes_with_assumptions":
        "The timing finding changes with the model assumptions.",
}


class APIError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _frame(frame):
    # Decision-time velocities may encode unseen movement after the freeze.
    return {"t_ms": frame["t_ms"],
            "players": [{"player_id": item["player_id"], "position_m": list(item["position_m"])}
                        for item in frame["players"]],
            "ball": {"position_m": list(frame["ball"]["position_m"])}}


def explain(assessment):
    """Fixed wording from assessment fields only; never receives an outcome."""
    if assessment["status"] == "insufficient_evidence":
        return {"source": "deterministic", "summary":
                "Some observations are old. This model declines to compare the routes.", "options": []}
    summary = ("Compare release timing under the approaching pressure. Another touch adds preparation time; release before arrival does not establish pass success."
               if assessment["scenario_id"] == "press-arrives" else
               "Compare the two ground routes under the stated assumptions. The aerial clearance is unmodelled, so there is no overall best-action score.")
    return {"source": "deterministic", "summary": summary,
            "options": [{"option_id": item["option_id"], "evidence_id": item["evidence_id"],
                         "text": FINDINGS.get(item.get("finding"),
                                              "This action is outside the current geometry model.")}
                        for item in assessment["options"]]}


class KeeperLoop:
    """Bounded sessions retaining the first choice and serialized assessment."""
    def __init__(self, scenario=None, *, max_sessions=128, session_ttl_s=3600, clock=monotonic, workflow=None, agent_gate=None, recorded=False):
        if recorded and workflow is not None:
            raise ValueError("Choose recorded output or a live workflow")
        scenario = deepcopy(scenario if scenario is not None else build_scenario())
        self._snapshot = freeze_snapshot(scenario)
        state = self._snapshot.read()
        self._option_ids = {option["option_id"] for option in state["options"]}
        frames = [_frame(frame) for frame in scenario["world_frames"] if frame["t_ms"] < state["t_ms"]]
        observations = {item["player_id"]: item for item in state["observations"]}
        for frame in frames:
            for player in frame["players"]:
                known = observations[player["player_id"]]
                if known["observed_at_ms"] < frame["t_ms"]:
                    player["position_m"] = list(known["position_m"])
        # Display the available observations at the freeze, not the world frame.
        frames.append({"t_ms": state["t_ms"],
                       "players": [{"player_id": item["player_id"], "position_m": item["position_m"]}
                                   for item in state["observations"]],
                       "ball": {"position_m": state["ball"]["position_m"]}})
        self._start_json = _json({
            "schema_version": "0.1", "scenario_id": state["scenario_id"], "synthetic": True,
            "title": SCENARIOS[state["scenario_id"]]["title"], "labels": SCENARIOS[state["scenario_id"]]["labels"],
            "teams": scenario["teams"], "roster": scenario["roster"],
            "pitch": state["pitch"], "match_context": state["match_context"],
            "decision_t_ms": state["t_ms"], "frames": frames,
        })
        self._reveal_json = _json({
            "continuation": scenario["continuation"],
            "frames": [_frame(frame) for frame in scenario["world_frames"] if frame["t_ms"] > state["t_ms"]],
            "events": [event for event in scenario["events"] if event["t_ms"] > state["t_ms"]],
        })
        self._sessions = {}
        self._lock = RLock()
        self._max_sessions = max_sessions
        self._ttl = session_ttl_s
        self._clock = clock
        self._workflow = workflow
        self._agent_gate = agent_gate if agent_gate is not None else Semaphore(1)
        self._interpretation_json = None
        if recorded:
            from .recordings import load_recording
            self._interpretation_json = _json(load_recording(
                self._snapshot, analyse_snapshot(self._snapshot), analyse_pressure(self._snapshot)))

    def _interpret(self, assessment):
        try:
            with self._agent_gate:
                result = asyncio.run(self._workflow.generate(self._snapshot, assessment))
        except Exception:
            result = {"status": "fallback", "source": "deterministic", "reason": "workflow_unavailable", "trace": []}
        with self._lock:
            self._interpretation_json = _json(result)

    def _expire(self):
        now = self._clock()
        for session_id in list(self._sessions):
            if now - self._sessions[session_id]["created_at"] >= self._ttl:
                del self._sessions[session_id]

    def _session(self, session_id):
        self._expire()
        if session_id not in self._sessions:
            raise APIError(404, "Unknown or expired session. Start a new replay.")
        return self._sessions[session_id]

    def start(self, scenario_id="tempting-short-pass"):
        with self._lock:
            if scenario_id != self._snapshot.read()["scenario_id"]:
                raise APIError(404, "Unknown scenario.")
            self._expire()
            if len(self._sessions) >= self._max_sessions:
                raise APIError(503, "Local session limit reached. Try again after sessions expire.")
            session_id = uuid4().hex
            self._sessions[session_id] = {"created_at": self._clock(), "choice": None, "assessment_json": None}
            return {**json.loads(self._start_json), "session_id": session_id}

    def decision(self, session_id):
        with self._lock:
            self._session(session_id)
            return {"snapshot_id": self._snapshot.snapshot_id, "decision": self._snapshot.read()}

    def _evidence(self, session):
        if session["choice"] is None:
            raise APIError(409, "Choose an action before inspecting evidence or revealing the outcome.")
        assessment = json.loads(session["assessment_json"])
        interpretation = (json.loads(self._interpretation_json) if self._interpretation_json is not None
                          else {"status": "deterministic", "source": "deterministic", "trace": []})
        explanation = explain(assessment)
        if interpretation["status"] in ("reviewed", "insufficient_evidence") and interpretation["source"] in ("local_agents", "recorded_agents"):
            explanation.update(source=interpretation["source"], summary=interpretation["fan"], analyst_summary=interpretation["analyst"])
        return {"choice": session["choice"], "assessment": assessment, "explanation": explanation,
                "pressure": analyse_pressure(self._snapshot), "interpretation": interpretation}

    def choose(self, session_id, option_id):
        with self._lock:
            session = self._session(session_id)
            if not isinstance(option_id, str) or option_id not in self._option_ids:
                raise APIError(400, "Unknown option.")
            if session["choice"] is not None and session["choice"] != option_id:
                raise APIError(409, "The first choice is frozen. Start a new replay to choose again.")
            if session["assessment_json"] is None:
                session["assessment_json"] = _json(analyse_snapshot(self._snapshot))
                session["choice"] = option_id
                if self._workflow is not None and self._interpretation_json is None:
                    self._interpretation_json = _json({"status": "running", "source": "deterministic", "trace": []})
                    Thread(target=self._interpret, args=(json.loads(session["assessment_json"]),), daemon=True).start()
            return self._evidence(session)

    def evidence(self, session_id):
        with self._lock:
            return self._evidence(self._session(session_id))

    def reveal(self, session_id):
        with self._lock:
            session = self._session(session_id)
            evidence = self._evidence(session)
            reveal = json.loads(self._reveal_json)
            continuation = reveal["continuation"]
            action = SCENARIOS[self._snapshot.read()["scenario_id"]]["labels"][continuation["scripted_option_id"]]
            recorded = f"Recorded action: {action}. The pass was {continuation['outcome']}."
            context = ("The recording shows your chosen action." if session["choice"] == continuation["scripted_option_id"]
                       else "You chose a different action. This recording does not simulate your choice.")
            return {**evidence, **reveal, "recap": {
                "recorded_outcome": recorded, "choice_context": context,
                "assessment_context": (
                    "The frozen comparison remains unavailable. Seeing the continuation does not supply the observation that was missing at the decision."
                    if evidence["assessment"]["status"] == "insufficient_evidence" else
                    "The frozen assessment stays unchanged. A completed pass does not erase a modelled interception opportunity."),
            }}


class KeeperCatalog:
    """Three scenarios with a shared, serial local-inference gate and bounded sessions."""
    def __init__(self, outcome="completed", workflow=None, recorded=False):
        gate = Semaphore(1)
        self._loops = {key: KeeperLoop(scenario, workflow=workflow, agent_gate=gate, recorded=recorded)
                       for key, scenario in build_catalog(outcome).items()}
        self._lock = RLock()

    def start(self, scenario_id="tempting-short-pass"):
        if not isinstance(scenario_id, str) or scenario_id not in self._loops:
            raise APIError(404, "Unknown scenario.")
        with self._lock:
            for loop in self._loops.values():
                with loop._lock:
                    loop._expire()
            if sum(len(loop._sessions) for loop in self._loops.values()) >= 128:
                raise APIError(503, "Local session limit reached.")
            return self._loops[scenario_id].start(scenario_id)

    def _owning(self, session_id):
        for loop in self._loops.values():
            with loop._lock:
                loop._expire()
                if session_id in loop._sessions:
                    return loop
        raise APIError(404, "Unknown or expired session. Start a new replay.")

    def decision(self, session_id):
        return self._owning(session_id).decision(session_id)

    def choose(self, session_id, option_id):
        return self._owning(session_id).choose(session_id, option_id)

    def evidence(self, session_id):
        return self._owning(session_id).evidence(session_id)

    def reveal(self, session_id):
        return self._owning(session_id).reveal(session_id)


class KeeperServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, loop=None, *, lan_ip=None):
        self.lan_ip = private_lan_ipv4(lan_ip) if lan_ip is not None else None
        if self.lan_ip is not None and address[0] != self.lan_ip:
            raise ValueError("LAN address must match the explicit bind address.")
        self.loop = loop if loop is not None else KeeperLoop()
        super().__init__(address, KeeperHandler)

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(5)
        return connection, address


class KeeperHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send(self, status, data, content_type="application/json; charset=utf-8"):
        payload = data if isinstance(data, bytes) else _json(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(payload)

    def _local_request(self):
        port = self.server.server_port
        host = self.headers.get("Host", "")
        allowed = (f"{self.server.lan_ip}:{port}",) if self.server.lan_ip else (f"127.0.0.1:{port}", f"localhost:{port}")
        if len(self.headers.get_all("Host", [])) != 1 or host not in allowed:
            raise APIError(403, "Use the configured demo address.")
        origin = self.headers.get("Origin")
        if (len(self.headers.get_all("Origin", [])) > 1
                or (origin is not None and origin != f"http://{host}")
                or self.headers.get("Sec-Fetch-Site") == "cross-site"):
            raise APIError(403, "Cross-origin requests are unsupported.")

    def _body(self):
        if self.headers.get("Transfer-Encoding"):
            raise APIError(400, "Transfer encoding is unsupported.")
        if self.headers.get_content_type() != "application/json":
            raise APIError(415, "Use application/json.")
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise APIError(400, "Invalid body length.") from None
        if not 0 < size <= 1024:
            raise APIError(413, "JSON body must be between 1 and 1024 bytes.")
        try:
            body = json.loads(self.rfile.read(size))
        except (ValueError, UnicodeError):
            raise APIError(400, "Invalid JSON.") from None
        if not isinstance(body, dict):
            raise APIError(400, "JSON object required.")
        return body

    def _route(self, method):
        self._local_request()
        # Fixed allowlist; fixtures and arbitrary filesystem paths cannot be served.
        static = {"/": ("web/index.html", "text/html"), "/app.js": ("web/app.js", "text/javascript"),
                  "/styles.css": ("web/styles.css", "text/css"), "/api/schema": ("docs/api.schema.json", "application/schema+json")}
        if method == "GET" and self.path in static:
            name, mime = static[self.path]
            self._send(200, (ROOT / name).read_bytes(), mime + "; charset=utf-8")
            return
        if method == "GET" and self.path == "/api/scenarios":
            self._send(200, [{"scenario_id": key, **value} for key, value in SCENARIOS.items()])
            return
        if method == "GET" and self.path == "/health":
            self._send(200, {"status": "ok", "budget": "local-only"})
            return
        if self.path == "/api/start" and method == "POST":
            body = self._body()
            if set(body) - {"scenario_id"}:
                raise APIError(400, "Only scenario_id is accepted.")
            self._send(201, self.server.loop.start(body.get("scenario_id", "tempting-short-pass")))
            return
        match = re.fullmatch(r"/api/sessions/([a-f0-9]{32})/(decision|evidence|choice|reveal)", self.path)
        if match is None:
            raise APIError(404, "Unknown endpoint.")
        session_id, operation = match.groups()
        loop = self.server.loop
        if method == "GET" and operation in ("decision", "evidence"):
            self._send(200, getattr(loop, operation)(session_id))
        elif method == "POST" and operation in ("choice", "reveal"):
            body = self._body()
            if operation == "choice":
                if set(body) != {"option_id"}:
                    raise APIError(400, "Only option_id is required.")
                result = loop.choose(session_id, body["option_id"])
            else:
                if body:
                    raise APIError(400, "Reveal expects an empty object.")
                result = loop.reveal(session_id)
            self._send(200, result)
        else:
            raise APIError(405, "Unsupported method for this endpoint.")

    def _handle(self, method):
        try:
            self._route(method)
        except APIError as error:
            self._send(error.status, {"error": error.message})
        except TimeoutError:
            self._send(408, {"error": "Request timed out."})

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--outcome", choices=("completed", "intercepted"), default="completed")
    parser.add_argument("--agents", choices=("off", "local", "recorded"), default="off",
                        help="off: fixed text; local: live agents; recorded: captured agent output without model calls")
    parser.add_argument("--model", default="gemma4:e4b-llama.cpp")
    parser.add_argument("--model-endpoint", default="http://127.0.0.1:8088/v1",
                        help="Anonymous local OpenAI-compatible server; no cloud endpoints")
    bind = parser.add_mutually_exclusive_group()
    bind.add_argument("--host", choices=("127.0.0.1", "0.0.0.0"), default="127.0.0.1")
    bind.add_argument("--lan-ip", type=private_lan_ipv4, help="Opt-in recorded phone demo on this private IPv4 interface")
    args = parser.parse_args()
    if args.lan_ip and args.agents != "recorded":
        parser.error("Phone LAN mode requires --agents recorded.")
    workflow = None
    if args.agents == "local":
        from .agents import AgentWorkflow
        workflow = AgentWorkflow(model=args.model, base_url=args.model_endpoint)
    with KeeperServer((args.lan_ip or args.host, args.port), KeeperCatalog(args.outcome, workflow, recorded=args.agents == "recorded"), lan_ip=args.lan_ip) as server:
        print(f"Keeper's Boots local demo: http://{args.lan_ip or '127.0.0.1'}:{server.server_port}", flush=True)
        if args.lan_ip:
            print("Private LAN recorded demo: use this address from your phone on the same Wi-Fi.", flush=True)
        if args.agents == "recorded":
            print("Recorded agent output mode: captured explanations and traces; no live model or MCP calls.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
