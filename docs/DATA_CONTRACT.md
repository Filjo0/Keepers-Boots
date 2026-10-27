# Data contract v0.1

## Units and identifiers
- Coordinates: metres, x along the 105 m pitch and y across its 68 m width.
- Time: integer milliseconds from scenario start; match clock is separate.
- Angles, when introduced, must declare radians/degrees and reference direction.
- Speeds: metres per second. Durations in model parameters: seconds.
- Stable fictional player, team, event, option and scenario IDs.
- Reject booleans masquerading as numbers, NaN/infinity, duplicate IDs and invalid ranges.

## Scenario package
The owning generator creates:
- schema_version, scenario_id, generator_version, seed (null when no randomness is used);
- teams and 22-player roster;
- timestamped world frames and events;
- decision: the explicitly available observations, context, options and model parameters;
- continuation events and outcome labels.

World frames and outcome labels are not pre-decision evidence. A fixture is a replay package, not an agent prompt.

## Decision snapshot
Current allowlist:
- scenario_id;
- decision fields: t_ms, pitch, attacking_team, attack_direction, keeper_id, match_context;
- observations: player_id, team, position_m, observed_at_ms;
- ball: position_m, controller_id, observed_at_ms; v0.1 requires keeper control at the keeper position;
- options: option_id, kind, target_player_id, target_m, ball_speed_mps where relevant; optional nonnegative preparation_delay_s requires point-arrival-v0.2;
- model: model_version, release_delay_s, defender_speed_mps, reaction_delay_s, lane_samples.

Positions are immutable observation values. For scenario 1 every rostered player's observation is current at t_ms. No goalkeeper field of view is claimed.

## Observation rules
- An observation after t_ms is invalid.
- An observation before t_ms remains old; do not replace it with the world's actual current position.
- The initial assessor declines geometry ranking when observations are stale. This is a conservative scaffold, not a calibrated freshness policy.
- Unknown opponents must not disappear from the analysis. Incomplete rosters are rejected.
- The optional midfielder extension introduces explicit refresh actions and versioned uncertainty propagation.

## Output evidence
Every assessment carries:
- snapshot_id, scenario_id, model_version, status and limitations;
- per-option evidence_id, pass kind, route length;
- modelled time ranges and sampled interception margins for ground passes;
- unsupported-model or insufficient-evidence reasons;
- code-computed comparison facts with evidence IDs, matching/extrema basis and explicit signed-margin ordering;
- no universal ranking and no inferred completion probability.

The implemented [claim contract](AGENTS_AND_MCP.md) references immutable evidence IDs. Numeric values, units, assumptions and observation times are rendered from code. Pressure and stale-observation uncertainty are separate explicit evidence fields.

## Input validation versus full schema
The current Python validator protects the implemented subset and its cross-field constraints. The [published JSON Schema](api.schema.json) covers the frozen snapshot and local API request/response envelopes; [API operations](API.md) document gating and lifetime rules. The implemented MCP server publishes input and structured object output schemas with additional identifier/domain checks.
Future contract versions must preserve explicit unknowns and retain old fixtures for replay tests.
