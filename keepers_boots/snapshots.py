"""The only permitted input boundary for pre-decision analysis."""
from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
import json
import math
import re


def _number(value, label, minimum=0):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    if not math.isfinite(value) or value < minimum:
        raise ValueError(f"{label} must be finite and >= {minimum}")
    return value


def _integer(value, label, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{label} must be an integer >= {minimum}")
    return value


def _identifier(value, label):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", value):
        raise ValueError(f"invalid {label}")
    return value


def _pair(value, label, positive=False):
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"{label} must have two values")
    result = [_number(item, label) for item in value]
    if positive and min(result) <= 0:
        raise ValueError(f"{label} must be positive")
    return result


def _range(value, label, positive=False):
    result = _pair(value, label, positive)
    if result[0] > result[1]:
        raise ValueError(f"{label} is reversed")
    return result


def _position(value, label, pitch):
    result = _pair(value, label)
    if result[0] > pitch["length_m"] or result[1] > pitch["width_m"]:
        raise ValueError(f"{label} lies outside pitch")
    return result


def _validate_payload(source):
    # Construct an allowlisted object: narrative, world truth and future metadata
    # are never copied even if present in the source package.
    pitch = {
        key: _number(source["pitch"][key], key, 1)
        for key in ("length_m", "width_m")
    }
    t_ms = _integer(source["t_ms"], "t_ms")
    direction = source["attack_direction"]
    if type(direction) is not int or direction not in (-1, 1):
        raise ValueError("attack_direction must be -1 or 1")
    context = {
        key: _integer(source["match_context"][key], key)
        for key in ("home_goals", "away_goals", "match_clock_s")
    }
    observations = []
    for item in source["observations"]:
        seen = _integer(item["observed_at_ms"], "observed_at_ms")
        if seen > t_ms:
            raise ValueError("observation after decision")
        observations.append({
            "player_id": _identifier(item["player_id"], "player_id"),
            "team": _identifier(item["team"], "team"),
            "position_m": _position(item["position_m"], "position_m", pitch),
            "observed_at_ms": seen,
        })
    ids = [item["player_id"] for item in observations]
    team_counts = Counter(item["team"] for item in observations)
    if len(ids) != 22 or len(set(ids)) != 22 or sorted(team_counts.values()) != [11, 11]:
        raise ValueError("complete distinct 11-v-11 observations required")
    attacking_team = _identifier(source["attacking_team"], "attacking_team")
    keeper_id = _identifier(source["keeper_id"], "keeper_id")
    by_id = {item["player_id"]: item for item in observations}
    if keeper_id not in by_id or by_id[keeper_id]["team"] != attacking_team:
        raise ValueError("keeper must belong to attacking team")
    raw_ball = source["ball"]
    ball = {
        "position_m": _position(raw_ball["position_m"], "ball.position_m", pitch),
        "controller_id": _identifier(raw_ball["controller_id"], "ball.controller_id"),
        "observed_at_ms": _integer(raw_ball["observed_at_ms"], "ball.observed_at_ms"),
    }
    if ball["observed_at_ms"] > t_ms:
        raise ValueError("ball observation after decision")
    if ball["controller_id"] != keeper_id or ball["position_m"] != by_id[keeper_id]["position_m"]:
        raise ValueError("v0.1 requires keeper-controlled ball at keeper position")
    options = []
    for option in source["options"]:
        kind = option["kind"]
        if kind not in ("ground", "aerial"):
            raise ValueError("unsupported option kind")
        target_id = _identifier(option["target_player_id"], "target_player_id")
        if target_id not in by_id or by_id[target_id]["team"] != attacking_team:
            raise ValueError("target must belong to attacking team")
        cleaned = {
            "option_id": _identifier(option["option_id"], "option_id"),
            "kind": kind,
            "target_player_id": target_id,
            "target_m": _position(option["target_m"], "target_m", pitch),
        }
        if kind == "ground":
            cleaned["ball_speed_mps"] = _range(
                option["ball_speed_mps"], "ball_speed_mps", positive=True
            )
        if "preparation_delay_s" in option:
            cleaned["preparation_delay_s"] = _number(option["preparation_delay_s"], "preparation_delay_s")
        options.append(cleaned)
    if len(options) != 3 or len({item["option_id"] for item in options}) != 3:
        raise ValueError("three distinct options required")
    raw_model = source["model"]
    samples = _integer(raw_model["lane_samples"], "lane_samples", 2)
    if samples > 10001:
        raise ValueError("lane_samples exceeds local calculation bound")
    model = {
        "model_version": _identifier(raw_model["model_version"], "model_version"),
        "release_delay_s": _number(raw_model["release_delay_s"], "release_delay_s"),
        "defender_speed_mps": _range(
            raw_model["defender_speed_mps"], "defender_speed_mps", positive=True
        ),
        "reaction_delay_s": _range(raw_model["reaction_delay_s"], "reaction_delay_s"),
        "lane_samples": samples,
    }
    if model["model_version"] not in ("point-arrival-v0.1", "point-arrival-v0.2"):
        raise ValueError("unsupported model version")
    if model["model_version"] == "point-arrival-v0.1" and any("preparation_delay_s" in option for option in options):
        raise ValueError("preparation delays require model v0.2")
    return {
        "schema_version": "0.1",
        "scenario_id": _identifier(source["scenario_id"], "scenario_id"),
        "t_ms": t_ms, "pitch": pitch, "attack_direction": direction,
        "attacking_team": attacking_team, "keeper_id": keeper_id,
        "match_context": context, "ball": ball,
        "observations": sorted(observations, key=lambda x: x["player_id"]),
        "options": options, "model": model,
    }


@dataclass(frozen=True)
class DecisionSnapshot:
    payload_json: str
    snapshot_id: str

    def read(self):
        actual = sha256(self.payload_json.encode("utf-8")).hexdigest()
        if actual != self.snapshot_id:
            raise ValueError("snapshot digest mismatch")
        # Revalidate at the analysis boundary and return a fresh independent object.
        return _validate_payload(json.loads(self.payload_json))


def freeze_snapshot(scenario):
    if scenario["schema_version"] != "0.1":
        raise ValueError("unsupported scenario schema")
    decision = dict(scenario["decision"])
    decision["scenario_id"] = scenario["scenario_id"]
    payload = _validate_payload(decision)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return DecisionSnapshot(encoded, sha256(encoded.encode("utf-8")).hexdigest())
