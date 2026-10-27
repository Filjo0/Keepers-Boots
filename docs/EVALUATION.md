# Evaluation protocol v0.1

Defined before building the UI/agents. Keep operational results in the task card or dated audits. Version changes to this protocol with reasons; do not rewrite criteria after inspecting results.

## What this evaluates
Software correctness, evidence preservation, bounded agent behaviour and whether the demo communicates its stated model.
It does not validate professional football optimality or real player improvement.

## Required deterministic checks
1. Future events and alternative outcomes leave snapshot and assessment unchanged.
2. Unobserved world movements do not affect assessment until a permitted refresh.
3. Future-dated observations are rejected.
4. Snapshot reads cannot mutate stored data; digest tampering is rejected.
5. Mirror-image fixtures preserve geometric results within numerical tolerance.
6. Missing/stale information produces explicit unavailability.
7. Non-finite values, invalid bounds and duplicate/incomplete rosters are rejected.
8. Unsupported aerial actions remain unranked.
9. Generated fixtures reproduce exactly from the owning source.
10. Parameter/sampling sensitivity is reported before claiming robust geometric separation.

## Agent checks, when implemented
- Inject a wrong number, wrong player, unsupported evidence ID and future fact.
- Check both the deterministic validator and reviewer response.
- Test plausible prose that misinterprets a correct number.
- Test one bounded repair, reviewer/tool failure, timeout and fallback.
- Compare analyst-only and analyst-plus-reviewer on identical held-out variants.
- Separate factual accuracy from tactical plausibility and stylistic preference.
- Test each personalised/language output, not only the original explanation.

## Measures
Report counts and denominators for factual errors, unsupported interpretations, reviewer corrections, false rejections, abstentions and fallback use.
Measure latency distributions, model calls, tokens/cost per completed interaction and cache behaviour.
Publish measured values; do not invent targets retroactively.

## Scenario validity
Obtain explicit review of authored scenarios/principles before claiming coach validation.
Use variations not used to tune parameters. Simulator agreement establishes internal consistency only.
Do not score a user as wrong solely because their choice differs from the scripted continuation.

## Release acceptance
- All current regression checks pass.
- Fresh-clone install, browser loop and hosted smoke test work.
- No unchecked narrative is shown as verified.
- No private content or credentials are present.
- Every feature is labelled according to its actual implementation/deployment status.
