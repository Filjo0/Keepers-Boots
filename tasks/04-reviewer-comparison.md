# Held-out reviewer comparison

## Goal

Measure whether an analyst plus reviewer reduces errors relative to the same analyst with the same code guards. Report false rejections, failed repairs, abstention and latency as well as corrections. Do not infer benefit from the three showcase scenarios or the selected demo output.

## Branch or worktree

Local main branch. This is a scoped evaluation task; no evaluation has run. Keep docs/EVALUATION.md v0.1 unchanged. Known failures live separately in data/evaluation/calibration/.

## Verified findings

- Two of the first three documented scenario 1 selection captures contained reviewer-approved errors. Prompt and guard changes followed observation, so these are calibration cases.
- Historical captures contain final drafts and approval traces, not full reviewer objects or paired baseline drafts. They cannot reconstruct the proposed comparison.
- The frozen protocol already requires identical held-out variants. New variants must not be the three scenarios used to tune prompts/regex guards, nor simple copies of those cases.
- Current facts are limited to frozen available observations. Football plausibility and human comprehension are separate assessments.

## Plan

1. tools/build_evaluation_variants.py: add a documented evaluation-only generator using existing build_scenario/build_press_scenario/build_uncertain_scenario and freeze_snapshot. Vary visible opponent/receiver positions, route targets, release/preparation delays, observation ages and model parameter ranges. Include overlapping and changing-sign ranges, conflicting timing metrics, unsupported aerial actions and stale information. Keep three product scenarios unchanged. Generator output belongs in data/evaluation/held-out/, never hand-edit scenario JSON. Confirm cutoff, outcome independence and mirror invariants using tests/test_evaluation_variants.py.
2. Before model calls, commit the variant manifest, its generator seed/parameters and hashes, sampling plan and scoring rubric. Separate development and held-out variants. Freeze agents.py, claims.py, model/runtime settings and SDK pins; record hashes. Exclude showcase-selection runs and all data used for tuning. New variants alone do not make a test held-out if they are then used to adjust prompts.
3. tools/evaluate_reviewers.py: retain the first analyst Draft and raw Review objects from the real SDK/MCP path in ignored evaluation artifacts. Do not create a second independently generated draft for the baseline. Evaluate that same first draft plus code guards for analyst-only; evaluate its review/one repair plus the identical guards for the paired branch. Preserve code rejection and reviewer rejection as distinct events. Use fresh contexts and randomized ordering to reduce runtime/order bias. Never pass outcomes or hidden movement to either branch.
4. Label factual support, scope, completeness, clarity and tactical plausibility separately. Use an assessor blinded to branch/reviewer decision where practical; code can score deterministic facts. Human clarity/scenario review remains separate. Add a separately labelled corrupted-draft challenge set, including negations and misleading but numerically correct prose; do not blend it into natural-draft results. Define sample size and rubric before running, without choosing thresholds after seeing results.
5. Run the frozen set once and retain every attempt, timeout and fallback. Report paired counts/denominators for factual errors, unsupported claims, correct/incorrect reviewer interventions, accepted bad drafts, repairs, false rejections and abstentions. Report actual timing/call/token observations. If prompts or guards change after inspection, retire that set to calibration and use a new frozen held-out set.
6. Write the dated outcome in docs/audits/reviewer-comparison-YYYY-MM-DD.md and this task. Update README/pitch only if the results support the specific benefit claim. A negative or inconclusive result is a valid outcome; retain the layered-checks description.

## Changes made

Recorded the paired comparison design and preserved two calibration failures separately. The owning variant generator, evaluator and held-out set do not exist yet.

## Validation

Validate calibration assets and capture archives with tests/test_capture_audit.py. For implementation, run narrow evaluation tests, then the complete project suite, docs checker and real CLI. Confirm the live evaluator records real MCP/model calls and does not substitute injected runners or recorded output for execution proof.

## Remaining work

Variant generator and preregistration; evaluator/raw draft-review capture; independent rubric/assessor; real paired run and report. No reviewer-benefit result is claimed.

## Next action

Freeze prompts/guards before creating and scoring new variants. Stop and review the design if either branch sees different input/drafts, if hidden truth becomes an input, or if a changed prompt is evaluated on already inspected data.
