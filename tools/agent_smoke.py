"""Exercise an existing local API/model loop; save observed results, never stage claims."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from uuid import uuid4

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]


def save_observation(artifacts, scenario_id, evidence, fresh_job_observed):
    """Preserve every completed observation; distinguish cached responses from jobs."""
    saved = datetime.now(timezone.utc)
    archive = artifacts / "agent-captures"
    archive.mkdir(exist_ok=True)
    name = saved.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:12] + "-" + scenario_id
    path = archive / (name + ".json")
    raw = (json.dumps(evidence, indent=2, allow_nan=False) + "\n").encode("utf-8")
    with path.open("xb") as output:
        output.write(raw)
    metadata = {"scenario_id": scenario_id, "snapshot_id": evidence["assessment"]["snapshot_id"],
                "saved_at_utc": saved.isoformat(timespec="seconds").replace("+00:00", "Z"),
                "capture_sha256": sha256(raw).hexdigest(), "fresh_job_observed": fresh_job_observed,
                "source": evidence["interpretation"]["source"], "status": evidence["interpretation"]["status"],
                "working_tree_workflow_sha256": sha256((ROOT / "keepers_boots/agents.py").read_bytes()).hexdigest(),
                "working_tree_guards_sha256": sha256((ROOT / "keepers_boots/claims.py").read_bytes()).hexdigest()}
    with (archive / (name + ".meta.json")).open("x", encoding="utf-8") as output:
        output.write(json.dumps(metadata, indent=2) + "\n")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--require-reviewed", action="store_true")
    parser.add_argument("--require-fresh", action="store_true",
                        help="Reject an already cached response; use a fresh local-agent API process")
    parser.add_argument("--scenario-id", choices=("tempting-short-pass", "press-arrives", "uncertain-outlet"),
                        help="Capture one fresh scenario without overwriting the other observed runs")
    args = parser.parse_args()
    parsed = urlsplit(args.base_url)
    if (parsed.scheme != "http" or parsed.hostname not in ("localhost", "127.0.0.1")
            or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ("", "/")):
        parser.error("Use an anonymous loopback HTTP API")
    base = args.base_url.rstrip("/")
    schema = json.loads((ROOT / "docs/api.schema.json").read_text(encoding="utf-8"))
    artifacts = ROOT / "local-artifacts"
    artifacts.mkdir(exist_ok=True)

    def request(path, body=None):
        payload = None if body is None else json.dumps(body).encode("utf-8")
        req = Request(base + path, data=payload, headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=6) as response:
            return json.load(response)

    results = []
    for scenario_id, option_id in [("tempting-short-pass", "switch-left"),
                                    ("press-arrives", "release-short"), ("uncertain-outlet", "switch-left")]:
        if args.scenario_id is not None and scenario_id != args.scenario_id:
            continue
        started = request("/api/start", {"scenario_id": scenario_id})
        path = "/api/sessions/" + started["session_id"]
        decision = request(path + "/decision")
        for envelope in (started, decision):
            serialized = json.dumps(envelope)
            for hidden in ("continuation", "outcome", "events", "scripted_option_id", "velocity_mps"):
                assert '"' + hidden + '"' not in serialized
        first = request(path + "/choice", {"option_id": option_id})
        fresh_job_observed = first["interpretation"]["status"] == "running"
        if args.require_fresh and not fresh_job_observed:
            raise SystemExit("No running job observed: this may be cached, recorded or agents-off. Start a fresh live API.")
        print("START " + scenario_id, flush=True)
        deadline = time.monotonic() + 210
        while True:
            evidence = request(path + "/evidence")
            assert evidence["assessment"] == first["assessment"], "Assessment changed while polling"
            if evidence["interpretation"]["status"] != "running":
                break
            if time.monotonic() > deadline:
                raise TimeoutError("Local interpretation remained queued/running")
            time.sleep(2)
        contract = {"$ref": "#/$defs/evidenceResponse", "$defs": schema["$defs"]}
        Draft202012Validator(contract).validate(evidence)
        revealed = request(path + "/reveal", {})
        assert revealed["assessment"] == first["assessment"], "Reveal changed frozen assessment"
        interpretation = evidence["interpretation"]
        saved = save_observation(artifacts, scenario_id, evidence, fresh_job_observed)
        (artifacts / ("runtime-" + scenario_id + ".json")).write_text(
            json.dumps(evidence, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        results.append(interpretation)
        print(json.dumps({"scenario": scenario_id, "status": interpretation["status"],
                          "source": interpretation["source"], "elapsed_s": interpretation.get("elapsed_s"),
                          "fresh_job_observed": fresh_job_observed, "archive": saved.relative_to(ROOT).as_posix(),
                          "trace": [(item["stage"], item["status"]) for item in interpretation["trace"]]}), flush=True)
    if args.require_reviewed and not all(item["source"] == "local_agents" for item in results):
        raise SystemExit("Live reviewed output was not accepted for every scenario; observed fallback evidence saved.")
    print(f"PASS: {len(results)} real HTTP loops, schemas and assessment immutability; observed results saved.")


if __name__ == "__main__":
    main()
