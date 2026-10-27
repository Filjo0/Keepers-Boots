# Scenario 1 - The tempting short pass

Status: generator, prototype geometry, browser/API interaction and Microsoft agent integration implemented locally; live outcomes are recorded in the active task. Independent scenario review remains pending. See the [active task](../../tasks/01-keeper-loop.md) for validation evidence.

## Intent
A completed short pass can still expose the team to a modelled interception opportunity. Explain using the pre-decision information, then reveal the continuation.

## Context
Fictional clubs: Harbour Lanterns and Vale Comets.
Level score; keeper controls the ball at their feet. A presser approaches.
Pitch 105 x 68 m; attacking direction is +x. Decision at scenario time 2,000 ms.

## Key actors at decision
| ID | Role | Position (m) |
|---|---|---|
| H01 | Keeper | (8, 34) |
| H02 | Right centre-back | (19, 46) |
| H03 | Left outlet | (24, 12) |
| H04 | Forward | (43, 40) |
| V01 | Approaching presser | (16, 37) |
| V02 | Short-outlet defender | (21, 45) |
| V03 | Wide-outlet defender | (37, 22) |
| V04 | Forward marker | (44, 39) |

The generator includes the other 14 players; all opponents are evaluated. This table is an excerpt, not the complete world.

## Build-up
| t_ms | V01 | V02 |
|---|---|---|
| 0 | (23, 40) | (23, 43) |
| 1000 | (19.5, 38.5) | (22, 44) |
| 2000 | (16, 37) | (21, 45) |

The current generator emits frames every 100 ms by documented linear interpolation. That interval is an implementation choice, not a competition requirement or a validated measurement frequency.

## Options
- short-right: ground pass to H02, 12-16 m/s.
- switch-left: ground pass to H03, 16-20 m/s.
- clear-long: aerial clearance toward H04; aerial outcomes are not modelled.

Use [analysis assumptions](../ANALYSIS.md), not an invented completion probability.

## Expected evidence
The short ground route permits an interception in the simplified model across the tested parameter extremes. The wide route has positive sampled timing margins.
The clearance cannot be ranked by the current model.
Describe the result as a comparison of supported ground routes under stated assumptions.

## Continuation
The default scripted short pass succeeds: the defender does not exploit the opportunity.
An alternative generated continuation intercepts that same pass.
The pre-decision snapshot and assessment must be identical for both.

## Display
Before choice: pitch, current observations, action buttons and synthetic label.
After choice: frozen evidence, scope and assumptions. The local loop uses a labelled deterministic explanation; reviewer-approved interpretation remains an agent-integration target.
On reveal: recorded continuation, clearly separate outcome facts and recap.
The fan does not yet cause a branching counterfactual match simulation.

## Acceptance
- Future/outcome changes do not affect assessment.
- Hidden world changes do not alter the observation snapshot.
- Mirror geometry agrees.
- Snapshot mutation is rejected or cannot affect stored data.
- Every numerical statement traces to evidence.
- Successful outcome never upgrades the original action assessment.

Owner: keepers_boots/scenario.py.
Generated fixture: data/scenarios/01-tempting-short-pass.json.
