# Known calibration failures

These two real captures preserve reviewer-approved errors from the scenario 1 showcase-selection sequence. They are excluded from the showcase and all held-out scores. Their source files remain in ignored local-artifacts/recording-archive. Re-export with tools/export_calibration_evidence.py; original model text and approval traces are never edited.

An additional calibration concern was identified in the selected third attempt on 15 October: its analyst text concludes that preparation delay does not alter the margin's width, although scenario 1 does not compare different preparation delays. Equal pressure margins for the current options do not establish that inference. This is an unsupported generalisation from the capture, not proof of a false number or a new run. The [unchanged selected interpretation](../../agent-recordings/tempting-short-pass.json) remains disclosed in recorded mode with a source-hash-bound scope note. Its reviewer accepted the draft and current code guards pass it. No new sentence-specific regex or model call was added; do not score this seen case as held-out evidence.

| Case | Captured issue | Historical reviewer decision |
|---|---|---|
| s1-pressure-subject.json | Fan text says the keeper arrives instead of the pressing opponent | Accept, after a code-triggered citation repair |
| s1-polarity-and-completeness.json | Both routes described as positive despite the short route's negative range; incomplete analyst sentence | Accept |

The frozen available decision, numeric evidence and accepted final draft are included. The audit labels describe a later project review against that evidence, not a coach or blinded assessment. Current guard errors were computed at export and reflect rules added after seeing these failures. They do not establish that the original guard detected the error.

Only the saved approval trace is available: full reviewer objects, initial drafts before any repair and paired analyst-only results were not captured. These cases demonstrate two reviewer misses, not an estimate of incremental reviewer benefit. The showcase-selection sequence used changing prompts/guards and selected a preferred output; its counts are not a held-out error rate or a latency benchmark.

Use these cases for regression/debugging. Follow [the held-out comparison task](../../../tasks/04-reviewer-comparison.md) on new variants before making a benefit claim. [Evaluation v0.1](../../../docs/EVALUATION.md) remains unchanged. Model text/provenance is covered by the [rights inventory](../../../docs/RIGHTS_AND_SOURCES.md); public release is pending.
