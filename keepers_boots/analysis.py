"""Simplified synthetic geometry. No LLM, outcomes or whole-scenario input."""
from itertools import combinations, product
from math import dist
from .snapshots import DecisionSnapshot


LIMITATIONS = [
    "Synthetic constant-speed point-player model; no real-player calibration.",
    "Spatial sampling is approximate; no reach radius, acceleration or execution error.",
    "Aerial contests are not modelled; no universal option ranking.",
    "Timing margins are not pass-completion probabilities.",
]


def _comparison_facts(state, report):
    """Signed timing relations are code facts, not an LLM arithmetic task."""
    evidence = {item["option_id"]: item for item in report["options"]}
    ground = [item for item in state["options"] if evidence[item["option_id"]]["status"] == "model_evidence"]
    facts = []
    for left, right in combinations(ground, 2):
        a, b = left["option_id"], right["option_id"]
        fact = {"evidence_id": f"comparison:{a}:{b}", "option_ids": [a, b],
                "metric": "sampled_interception_margin", "relation": "overlapping_ranges",
                "larger_margin_option_id": None, "smaller_margin_option_id": None,
                "basis": "parameter_range_extrema", "text": "The sampled margin ranges overlap; their extrema alone do not establish an ordering."}
        if left["target_m"] == right["target_m"] and left["ball_speed_mps"] == right["ball_speed_mps"]:
            # Identical route/speed grids: preparation subtracts a constant from
            # every sampled margin. Compare matched cases, not overlapping extrema.
            shift = right.get("preparation_delay_s", 0) - left.get("preparation_delay_s", 0)
            fact.update(basis="matched_parameter_cases", margin_difference_s=round(abs(shift), 6))
            if shift == 0:
                fact.update(relation="equal", text="These ground actions have identical sampled timing margins under matched assumptions.")
            else:
                fact.update(relation="ordered", larger_margin_option_id=a if shift > 0 else b,
                            smaller_margin_option_id=b if shift > 0 else a)
        else:
            first = evidence[a]["minimum_interception_margin_s"]
            second = evidence[b]["minimum_interception_margin_s"]
            if first[0] > second[1] or second[0] > first[1]:
                fact.update(relation="ordered", larger_margin_option_id=a if first[0] > second[1] else b,
                            smaller_margin_option_id=b if first[0] > second[1] else a)
        if fact["relation"] == "ordered":
            scope = ("with the same route, ball-speed range and defender assumptions"
                     if fact["basis"] == "matched_parameter_cases" else "throughout the tested parameter ranges")
            fact["text"] = (f"{fact['larger_margin_option_id']} has larger signed sampled interception margins than "
                            f"{fact['smaller_margin_option_id']} {scope}. "
                            "This does not establish lower interception probability or an overall best action.")
        facts.append(fact)
    return facts


def analyse_snapshot(snapshot: DecisionSnapshot):
    state = snapshot.read()
    result = {
        "snapshot_id": snapshot.snapshot_id,
        "scenario_id": state["scenario_id"],
        "decision_t_ms": state["t_ms"],
        "model_version": state["model"]["model_version"],
        "status": "model_evidence",
        "ranking": None,
        "limitations": list(LIMITATIONS),
        "options": [],
        "comparisons": [],
    }
    stale = [
        item["player_id"] for item in state["observations"]
        if item["observed_at_ms"] < state["t_ms"]
    ]
    if state["ball"]["observed_at_ms"] < state["t_ms"]:
        stale.append("ball")
    if stale:
        result.update(status="insufficient_evidence", reason="stale_observations", stale_observation_ids=stale)
        result["uncertainty_regions"] = [
            {"player_id": item["player_id"], "observed_at_ms": item["observed_at_ms"],
             "position_m": item["position_m"], "age_ms": state["t_ms"] - item["observed_at_ms"],
             "radius_m": round((state["t_ms"] - item["observed_at_ms"]) / 1000 * state["model"]["defender_speed_mps"][1], 6),
             "assumption": "Maximum declared constant speed in any direction; not a probability region."}
            for item in state["observations"] if item["observed_at_ms"] < state["t_ms"]
        ]
        return result
    origin = state["ball"]["position_m"]
    defenders = [
        item for item in state["observations"]
        if item["team"] != state["attacking_team"]
    ]
    model = state["model"]
    for option in state["options"]:
        target = option["target_m"]
        length = dist(origin, target)
        evidence = {
            "option_id": option["option_id"],
            "evidence_id": option["option_id"] + ":geometry",
            "kind": option["kind"],
            "route_length_m": round(length, 6),
            "status": "not_modelled" if option["kind"] == "aerial" else "model_evidence",
        }
        if option["kind"] == "aerial":
            evidence["reason"] = "aerial_flight_and_contest_not_modelled"
            result["options"].append(evidence)
            continue
        if length == 0:
            evidence.update(status="not_modelled", reason="zero_length_pass")
            result["options"].append(evidence)
            continue
        margins = []
        for ball_speed, defender_speed, reaction in product(
            option["ball_speed_mps"], model["defender_speed_mps"], model["reaction_delay_s"]
        ):
            minimum = float("inf")
            for index in range(model["lane_samples"]):
                fraction = index / (model["lane_samples"] - 1)
                point = [
                    origin[axis] + fraction * (target[axis] - origin[axis])
                    for axis in (0, 1)
                ]
                ball_time = model["release_delay_s"] + option.get("preparation_delay_s", 0) + fraction * length / ball_speed
                for defender in defenders:
                    arrival = reaction + dist(defender["position_m"], point) / defender_speed
                    minimum = min(minimum, arrival - ball_time)
            margins.append(minimum)
        low, high = min(margins), max(margins)
        if high < 0:
            finding = "interception_reachable_in_all_tested_parameter_combinations"
        elif low > 0:
            finding = "positive_margin_at_sampled_points_in_all_tested_parameter_combinations"
        else:
            finding = "finding_changes_with_assumptions"
        times = [model["release_delay_s"] + option.get("preparation_delay_s", 0) + length / speed for speed in option["ball_speed_mps"]]
        evidence.update(
            receipt_after_decision_s=[round(min(times), 6), round(max(times), 6)],
            minimum_interception_margin_s=[round(low, 6), round(high, 6)],
            finding=finding,
            parameter_combinations=len(margins),
            lane_samples=model["lane_samples"],
        )
        result["options"].append(evidence)
    result["comparisons"] = _comparison_facts(state, result)
    return result


def analyse_pressure(snapshot: DecisionSnapshot):
    """Point-arrival pressure estimate from current observations only."""
    state = snapshot.read()
    result = {"snapshot_id": snapshot.snapshot_id, "evidence_id": "pressure:arrival",
              "model_version": state["model"]["model_version"], "status": "model_evidence",
              "limitations": ["Constant-speed point-player arrival at keeper position; no reach, acceleration or ball control.",
                              "Release before arrival does not establish pass success or subsequent possession.",
                              "An extra touch is represented only by a declared preparation delay."], "options": []}
    stale = [item["player_id"] for item in state["observations"] if item["observed_at_ms"] < state["t_ms"]]
    if state["ball"]["observed_at_ms"] < state["t_ms"]:
        stale.append("ball")
    if stale:
        result.update(status="insufficient_evidence", stale_observation_ids=stale)
        return result
    defenders = [item for item in state["observations"] if item["team"] != state["attacking_team"]]
    model = state["model"]
    arrivals = [min(reaction + dist(item["position_m"], state["ball"]["position_m"]) / speed
                    for item in defenders)
                for speed, reaction in product(model["defender_speed_mps"], model["reaction_delay_s"])]
    result["arrival_after_decision_s"] = [round(min(arrivals), 6), round(max(arrivals), 6)]
    for option in state["options"]:
        release = model["release_delay_s"] + option.get("preparation_delay_s", 0)
        result["options"].append({"option_id": option["option_id"], "release_after_decision_s": round(release, 6),
                                  "release_before_pressure_margin_s": [round(min(arrivals) - release, 6), round(max(arrivals) - release, 6)]})
    return result
