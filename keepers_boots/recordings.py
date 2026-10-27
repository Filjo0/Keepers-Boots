"""Load captured agent interpretations, bound to current code-computed evidence."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError

from .claims import validate_draft
from .scenario import SCENARIOS


ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "data/agent-recordings"


def evidence_digest(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256(payload.encode("utf-8")).hexdigest()


def validate_recording(recording, snapshot, assessment, pressure):
    """Check identity, evidence, prose guards and accepted trace before reuse."""
    if set(recording) != {"schema_version", "scenario_id", "interpretation", "recording"}:
        raise ValueError("Unexpected recording fields")
    metadata = recording["recording"]
    state = snapshot.read()
    if (recording["schema_version"] != "1" or recording["scenario_id"] != state["scenario_id"]
            or metadata["snapshot_id"] != snapshot.snapshot_id
            or metadata["assessment_sha256"] != evidence_digest(assessment)
            or metadata["pressure_sha256"] != evidence_digest(pressure)):
        raise ValueError("Recording does not match current frozen evidence")
    captured = recording["interpretation"]
    if captured["source"] != "local_agents" or captured["status"] not in ("reviewed", "insufficient_evidence"):
        raise ValueError("Recording is not an accepted local-agent result")
    if captured["status"] == "insufficient_evidence" and assessment["status"] != "insufficient_evidence":
        raise ValueError("Recording abstention does not match assessment")
    result = {**deepcopy(captured), "source": "recorded_agents", "recording": deepcopy(metadata)}
    schema = json.loads((ROOT / "docs/api.schema.json").read_text(encoding="utf-8"))
    try:
        Draft202012Validator({"$ref": "#/$defs/interpretation", "$defs": schema["$defs"]}).validate(result)
    except ValidationError as error:
        raise ValueError("Invalid recording contract") from error
    saved = datetime.fromisoformat(metadata["saved_at_utc"].replace("Z", "+00:00"))
    if saved.tzinfo is None or saved.utcoffset().total_seconds() != 0:
        raise ValueError("Capture timestamp must be UTC")
    _, errors = validate_draft({"snapshot_id": snapshot.snapshot_id, "claims": captured["claims"],
                               "fan": captured["fan"], "analyst": captured["analyst"],
                               "missing_information": captured["missing_information"], "ranking": None},
                              snapshot, assessment)
    if errors:
        raise ValueError("Captured draft fails current guards")
    trace = captured["trace"]
    if (not trace or (trace[0]["stage"], trace[0]["status"]) != ("mcp", "read")
            or (trace[-1]["stage"], trace[-1]["status"]) not in (("reviewer", "accept"), ("reviewer", "insufficient_evidence"))
            or not any(step["stage"] == "validator" and step["status"] == "accept" for step in trace)
            or any("test-only" in step["detail"].lower() for step in trace)
            or sum(step["stage"] == "repair" for step in trace) > 1):
        raise ValueError("Recording lacks the accepted live-workflow trace")
    return result


def export_recording(source, snapshot, assessment, pressure, notes=()):
    """Select only reviewed prose/trace and provenance from a real HTTP capture."""
    raw = source.read_bytes()
    evidence = json.loads(raw)
    if set(evidence) != {"assessment", "choice", "explanation", "interpretation", "pressure"}:
        raise ValueError("Unexpected HTTP capture fields")
    if evidence["assessment"] != assessment or evidence["pressure"] != pressure:
        raise ValueError("Captured numeric evidence differs from current code")
    saved = datetime.fromtimestamp(source.stat().st_mtime, timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    recording = {"schema_version": "1", "scenario_id": snapshot.read()["scenario_id"],
                 "interpretation": deepcopy(evidence["interpretation"]),
                 "recording": {"snapshot_id": snapshot.snapshot_id,
                               "assessment_sha256": evidence_digest(assessment),
                               "pressure_sha256": evidence_digest(pressure),
                               "source_sha256": sha256(raw).hexdigest(), "saved_at_utc": saved,
                               "timestamp_basis": "source_file_modified_time",
                               "capture_method": "tools/agent_smoke.py HTTP evidence capture",
                               "notes": list(notes)}}
    validate_recording(recording, snapshot, assessment, pressure)
    return recording


def load_recording(snapshot, assessment, pressure):
    try:
        scenario_id = snapshot.read()["scenario_id"]
        if scenario_id not in SCENARIOS:
            raise ValueError("Unknown recording scenario")
        path = DIRECTORY / (scenario_id + ".json")
        if path.stat().st_size > 65536:
            raise ValueError("Recording exceeds size bound")
        recording = json.loads(path.read_text(encoding="utf-8"))
        return validate_recording(recording, snapshot, assessment, pressure)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        # No unchecked prose or filesystem/provider details in the fallback.
        return {"status": "fallback", "source": "deterministic", "reason": "recording_unavailable",
                "trace": [{"stage": "recording", "status": "unavailable",
                           "detail": "Saved agent output unavailable or incompatible with current frozen evidence."}]}
