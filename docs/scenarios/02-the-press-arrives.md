# Scenario 2 - The press arrives

Implemented locally. Runtime and review evidence is recorded in [the active task](../../tasks/01-keeper-loop.md); independent coaching review remains pending.

## Intent
Compare time available to act with time needed to execute a pass or another touch.

## Required data
Timestamped keeper/ball state, approaching opponents, short outlet, declared action preparation duration and observation ages. Clearance has a nominal target, not a validated landing-region or aerial-contest model.
All player identifiers and observations follow the [data contract](../DATA_CONTRACT.md).

## Choices
- Take another touch.
- Release a short pass.
- Clear long.

## Evidence
Compute arrival-time ranges from declared assumptions.
Compare each action's release time with earliest point-arrival estimates at the keeper. The extra touch adds a declared preparation delay to the same ground pass.
Explain retaining possession versus immediate turnover exposure without estimating goal probability.
Aerial possession remains unavailable until an aerial model is separately implemented and checked.

## Generator task
Choose coordinates and movement rules before evaluating the continuation.
Use sensitivity ranges broad enough to expose assumptions.
Create at least two continuations with the same observations.
Have an independent coaching review challenge the scenario before calling it realistic.

## Acceptance
- A longer preparation time cannot silently improve time available under otherwise identical assumptions.
- Missing/stale pressure observations produce a limitation or abstention.
- A clearance may reduce immediate pressure while leaving subsequent possession unresolved.
- Future events do not determine the ranking or explanation.

Implemented in keepers_boots/scenario.py (build_press_scenario) and analysis.py (analyse_pressure); generated fixture data/scenarios/02-the-press-arrives.json. No-hindsight and monotonic preparation checks pass; realistic scenario interpretation remains unreviewed.
