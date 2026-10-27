# Scenario 3 - The uncertain outlet

Implemented locally with a conservative stale-observation abstention. Independent scenario review is pending.

## Intent
Show a useful abstention. Two outlets are available, but an old opponent observation prevents comparison. The prototype does not prove that a plausible movement reverses route ordering.

## Required data
Two candidate ground routes, one explicitly stale or incomplete opponent observation, and a documented movement uncertainty set. Keep true world movement out of the analysis input.

## Experience
The fan chooses an outlet.
The system identifies known facts, shows where information is old, and explains what additional observation could distinguish the options.
It does not pick an option just to finish the story.

## Initial implementation
V03 is observed before the freeze; later hidden movement varies between continuations. The browser masks movement after that observation before reveal. Geometry abstains and displays an illustrative radius equal to observation age times maximum declared defender speed. It does not use the region to rank routes, claim calibrated confidence or infer a freshness threshold.

The authored continuation plays switch-left toward H03 and reveals V03 moving near that outlet. Completed and intercepted generator variants share the same frozen assessment; neither outcome resolves what was observable earlier. The earlier short-pass continuation was replaced without changing the decision snapshot or its recorded-agent evidence hashes. Fan labels, a last-seen marker and the uncertainty explanation are implemented; browser verification of the latest presentation remains pending.

## Counterfactual checks
- Multiple hidden continuations with identical observations yield identical assessments.
- A new permitted observation may legitimately change the assessment.
- Increasing uncertainty must not produce a more confident ranking without justification.
- Unknown data remains unavailable rather than becoming zero or an absent opponent.

## Optional midfielder connection
Only after the keeper MVP is complete: the next recipient gets a scripted refresh control.
A refresh records what the simulator makes available and when. It does not claim to model eyes, head turns, attention or memory.
Unobserved movement is revealed afterward, never supplied as pre-choice knowledge.

Implemented in keepers_boots/scenario.py (build_uncertain_scenario), analysis.py and the browser; generated fixture data/scenarios/03-uncertain-outlet.json. See [roadmap](../../ROADMAP.md).
