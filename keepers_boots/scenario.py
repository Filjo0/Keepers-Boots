"""Owning generator for scenario 1. All identities and events are fictional."""
from copy import deepcopy
from math import ceil, dist

VERSION = "scripted-scenario-1-v0.1"
DECISION_MS = 2000
PITCH = {"length_m": 105, "width_m": 68}
HOME = {
    "H01": [8, 34], "H02": [19, 46], "H03": [24, 12], "H04": [43, 40],
    "H05": [62, 5], "H06": [66, 17], "H07": [70, 29], "H08": [73, 43],
    "H09": [76, 57], "H10": [80, 8], "H11": [84, 62],
}
AWAY = {
    "V01": [16, 37], "V02": [21, 45], "V03": [37, 22], "V04": [44, 39],
    "V05": [60, 8], "V06": [64, 21], "V07": [67, 35], "V08": [70, 50],
    "V09": [79, 60], "V10": [87, 25], "V11": [100, 34],
}


def _lerp(start, end, fraction):
    fraction = min(1, max(0, fraction))
    return [round(a + fraction * (b - a), 6) for a, b in zip(start, end)]


def build_scenario(outcome="completed"):
    if outcome not in ("completed", "intercepted"):
        raise ValueError("unknown scripted outcome")
    positions = {**HOME, **AWAY}
    release_ms = 2300
    flight_ms = 1000 * dist(HOME["H01"], HOME["H02"]) / 13
    receipt_ms = ceil(release_ms + flight_ms)
    interception_ms = 3200
    intercept_point = _lerp(
        HOME["H01"], HOME["H02"], (interception_ms - release_ms) / flight_ms
    )

    def player_position(player_id, t_ms):
        if player_id == "V01":
            if t_ms <= DECISION_MS:
                return _lerp([23, 40], AWAY[player_id], t_ms / DECISION_MS)
            return _lerp(AWAY[player_id], HOME["H01"], (t_ms - DECISION_MS) / 1500)
        if player_id == "V02":
            if t_ms <= DECISION_MS:
                return _lerp([23, 43], AWAY[player_id], t_ms / DECISION_MS)
            if outcome == "intercepted":
                return _lerp(AWAY[player_id], intercept_point, (t_ms - 2150) / 1050)
        return list(positions[player_id])

    def ball_position(t_ms):
        if outcome == "intercepted" and t_ms >= interception_ms:
            return intercept_point
        return _lerp(HOME["H01"], HOME["H02"], (t_ms - release_ms) / flight_ms)

    roster = [
        {"player_id": player_id, "team": "H" if player_id.startswith("H") else "V",
         "label": ("Lantern " if player_id.startswith("H") else "Comet ") + player_id[1:]}
        for player_id in positions
    ]
    frames = []
    # Include the event time as well as the regular 100 ms samples.
    times = sorted(set(range(0, 5001, 100)) | {receipt_ms, interception_ms, release_ms})
    for t_ms in times:
        players = []
        for player in roster:
            pos = player_position(player["player_id"], t_ms)
            next_pos = player_position(player["player_id"], t_ms + 1)
            players.append({
                "player_id": player["player_id"], "position_m": pos,
                "velocity_mps": [round((b - a) * 1000, 6) for a, b in zip(pos, next_pos)],
            })
        ball = ball_position(t_ms)
        next_ball = ball_position(t_ms + 1)
        frames.append({
            "t_ms": t_ms, "players": players,
            "ball": {"position_m": ball,
                     "velocity_mps": [round((b - a) * 1000, 6) for a, b in zip(ball, next_ball)]},
        })
    observations = [
        {"player_id": player["player_id"], "team": player["team"],
         "position_m": player_position(player["player_id"], DECISION_MS),
         "observed_at_ms": DECISION_MS}
        for player in roster
    ]
    event_ms = receipt_ms if outcome == "completed" else interception_ms
    return {
        "schema_version": "0.1",
        "scenario_id": "tempting-short-pass",
        "generator_version": VERSION,
        "seed": None,
        "synthetic": True,
        "teams": {"H": "Harbour Lanterns", "V": "Vale Comets"},
        "roster": roster,
        "world_frames": frames,
        "decision": {
            "t_ms": DECISION_MS, "pitch": deepcopy(PITCH),
            "attacking_team": "H", "attack_direction": 1, "keeper_id": "H01",
            "match_context": {"home_goals": 1, "away_goals": 1, "match_clock_s": 4320},
            "observations": observations,
            "ball": {"position_m": list(HOME["H01"]), "controller_id": "H01",
                     "observed_at_ms": DECISION_MS},
            "options": [
                {"option_id": "short-right", "kind": "ground", "target_player_id": "H02",
                 "target_m": list(HOME["H02"]), "ball_speed_mps": [12, 16]},
                {"option_id": "switch-left", "kind": "ground", "target_player_id": "H03",
                 "target_m": list(HOME["H03"]), "ball_speed_mps": [16, 20]},
                {"option_id": "clear-long", "kind": "aerial", "target_player_id": "H04",
                 "target_m": list(HOME["H04"])},
            ],
            "model": {"model_version": "point-arrival-v0.1", "release_delay_s": 0.3,
                      "defender_speed_mps": [4.5, 6.5], "reaction_delay_s": [0.15, 0.35],
                      "lane_samples": 1001},
        },
        "events": [
            {"event_id": "pass-release", "t_ms": release_ms, "kind": "pass",
             "player_id": "H01", "target_player_id": "H02"},
            {"event_id": "pass-outcome", "t_ms": event_ms, "kind": outcome,
             "player_id": "H02" if outcome == "completed" else "V02"},
        ],
        "continuation": {"scripted_option_id": "short-right", "outcome": outcome,
                         "note": "Scripted continuation, not an optimal policy or a fan-choice simulation."},
    }


SCENARIOS = {
    "tempting-short-pass": {"title": "The tempting short pass", "labels": {
        "short-right": "Short right", "switch-left": "Switch left", "clear-long": "Clear long"}},
    "press-arrives": {"title": "The press arrives", "labels": {
        "take-touch": "Touch, then pass", "release-short": "Release short", "clear-long": "Clear long"}},
    "uncertain-outlet": {"title": "The uncertain outlet", "labels": {
        "short-right": "Short right", "switch-left": "Switch left", "clear-long": "Clear long"}},
}


def build_press_scenario(outcome="completed"):
    """Extra touch changes preparation time only; no dribbling/ball-control model."""
    scenario = build_scenario(outcome)
    scenario.update(scenario_id="press-arrives", generator_version="scripted-press-v0.1")
    decision = scenario["decision"]
    decision["model"]["model_version"] = "point-arrival-v0.2"
    for item in decision["observations"]:
        if item["player_id"] == "V01":
            item["position_m"] = [11.6, 34]
    for frame in scenario["world_frames"]:
        for player in frame["players"]:
            if player["player_id"] == "V01":
                t = frame["t_ms"]
                player["position_m"] = (_lerp([20, 35], [11.6, 34], t / DECISION_MS) if t <= DECISION_MS
                                         else _lerp([11.6, 34], HOME["H01"], (t - DECISION_MS) / 704))
                # Replay velocities are excluded from assessment and the prelude.
                player["velocity_mps"] = [0, 0]
    short = deepcopy(decision["options"][0])
    touch = deepcopy(short)
    short["option_id"] = "release-short"
    touch.update(option_id="take-touch", preparation_delay_s=0.65)
    decision["options"] = [touch, short, decision["options"][2]]
    scenario["continuation"]["scripted_option_id"] = "release-short"
    return scenario


def build_uncertain_scenario(outcome="completed"):
    """Two unseen movements share the same last available observation."""
    scenario = build_scenario(outcome)
    scenario.update(scenario_id="uncertain-outlet", generator_version="scripted-uncertainty-v0.2")
    for item in scenario["decision"]["observations"]:
        if item["player_id"] == "V03":
            item.update(position_m=[31, 21], observed_at_ms=1000)
    destination = [37, 22] if outcome == "completed" else [25, 19]
    # Only the reveal changes: the available decision and last-seen observation
    # remain identical. Reveal the wide outlet that the old observation obscures.
    release_ms, interception_ms = 2300, 3200
    flight_ms = 1000 * dist(HOME["H01"], HOME["H03"]) / 18
    receipt_ms = ceil(release_ms + flight_ms)
    intercept_point = _lerp(HOME["H01"], HOME["H03"], (interception_ms - release_ms) / flight_ms)

    def ball_position(t_ms):
        if outcome == "intercepted" and t_ms >= interception_ms:
            return intercept_point
        return _lerp(HOME["H01"], HOME["H03"], (t_ms - release_ms) / flight_ms)

    def opponent_position(t_ms):
        if t_ms <= DECISION_MS:
            return _lerp([31, 21], destination, (t_ms - 1000) / 1000)
        endpoint = [29, 16] if outcome == "completed" else intercept_point
        duration = 1600 if outcome == "completed" else interception_ms - DECISION_MS
        return _lerp(destination, endpoint, (t_ms - DECISION_MS) / duration)

    receipt_frame = deepcopy(next(frame for frame in scenario["world_frames"] if frame["t_ms"] >= receipt_ms))
    receipt_frame["t_ms"] = receipt_ms
    scenario["world_frames"].append(receipt_frame)
    scenario["world_frames"].sort(key=lambda frame: frame["t_ms"])
    for frame in scenario["world_frames"]:
        t_ms = frame["t_ms"]
        for player in frame["players"]:
            if player["player_id"] == "V03":
                player["position_m"] = opponent_position(t_ms)
                player["velocity_mps"] = ([0, 0] if t_ms <= DECISION_MS else
                                          [round((b - a) * 1000, 6) for a, b in
                                           zip(opponent_position(t_ms), opponent_position(t_ms + 1))])
            elif player["player_id"] == "V02" and t_ms > DECISION_MS:
                player.update(position_m=list(AWAY["V02"]), velocity_mps=[0, 0])
        if t_ms > DECISION_MS:
            frame["ball"] = {"position_m": ball_position(t_ms),
                             "velocity_mps": [round((b - a) * 1000, 6) for a, b in
                                              zip(ball_position(t_ms), ball_position(t_ms + 1))]}
    scenario["events"] = [
        {"event_id": "pass-release", "t_ms": release_ms, "kind": "pass",
         "player_id": "H01", "target_player_id": "H03"},
        {"event_id": "pass-outcome", "t_ms": receipt_ms if outcome == "completed" else interception_ms,
         "kind": outcome, "player_id": "H03" if outcome == "completed" else "V03"},
    ]
    scenario["continuation"]["scripted_option_id"] = "switch-left"
    return scenario


def build_catalog(outcome="completed"):
    return {"tempting-short-pass": build_scenario(outcome),
            "press-arrives": build_press_scenario(outcome),
            "uncertain-outlet": build_uncertain_scenario(outcome)}
