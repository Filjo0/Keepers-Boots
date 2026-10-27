"""Local experiment server preserving SDK draft/review output before validation."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from keepers_boots import agents
from keepers_boots.api import KeeperCatalog, KeeperServer


def save_response(directory, role, response, sequence=1):
    """Capture model text/value, not transport metadata, errors or credentials."""
    value = response.value
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    payload = {"role": role, "sequence": sequence, "text": response.text, "value": value}
    path = directory / (f"{sequence:02d}-" + role + "-" + uuid4().hex + ".json")
    with path.open("x", encoding="utf-8", newline="\n") as output:
        output.write(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    return path


class CapturedWorkflow(agents.AgentWorkflow):
    """Use the real workflow; mirror its SDK call solely to preserve raw output."""
    def __init__(self, *, capture_directory, **kwargs):
        super().__init__(**kwargs)
        self.capture_directory = capture_directory
        self.response_count = 0

    async def _run(self, role, prompt, schema, tools):
        from agent_framework import Agent
        client, transport = agents.local_client(self.model, self.base_url)
        try:
            agent = Agent(client=client, name=role,
                          instructions=agents.ANALYST if role == "analyst" else agents.REVIEWER)
            response = await agent.run(prompt, options={"response_format": schema, "temperature": 0,
                                                       "max_tokens": 800 if role == "analyst" else 350})
            self.response_count += 1
            save_response(self.capture_directory, role, response, self.response_count)
            if response.value is not None:
                return schema.model_validate(response.value)
            return schema.model_validate_json(response.text)
        finally:
            await transport.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8007)
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-endpoint", required=True)
    parser.add_argument("--capture-name", required=True)
    args = parser.parse_args()
    if not args.capture_name or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in args.capture_name):
        parser.error("Use a simple lowercase capture name")
    directory = ROOT / "local-artifacts/phi-trial" / args.capture_name
    directory.mkdir(parents=True, exist_ok=False)
    metadata = {"saved_at_utc": datetime.now(timezone.utc).isoformat(), "model": args.model,
                "workflow_sha256": sha256((ROOT / "keepers_boots/agents.py").read_bytes()).hexdigest(),
                "guards_sha256": sha256((ROOT / "keepers_boots/claims.py").read_bytes()).hexdigest(),
                "probe_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
                "purpose": "Calibration probe; raw SDK output before current code checks, not held-out evidence."}
    (directory / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    workflow = CapturedWorkflow(capture_directory=directory, model=args.model, base_url=args.model_endpoint)
    with KeeperServer(("127.0.0.1", args.port), KeeperCatalog("completed", workflow)) as server:
        print(f"Captured local agent server: http://127.0.0.1:{args.port}; {directory.relative_to(ROOT)}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
