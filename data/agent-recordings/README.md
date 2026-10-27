# Captured agent demonstrations

These three JSON files preserve selected outputs from real Microsoft Agent Framework analyst/reviewer runs over this project's fictional scenarios, captured by tools/agent_smoke.py on 12 October 2026. The backend was the existing local Gemma model, identified as gemma4:e4b-llama.cpp. Run python -m keepers_boots.api --agents recorded to inspect them without model hardware; install the README's Pydantic and JSON Schema dependencies first.

## What is preserved

The fan and analyst text, accepted claims/citations, missing-information list, model identifier, status, elapsed time and original handoff trace are unchanged from local-artifacts/runtime-*.json. Only these fields and nonsecret provenance are exported. No fan choice, session, outcome, continuation, hidden motion, model endpoint, absolute local path, private corpus or weights are included.

On 15 October, a human scope note was added to scenario 1 without changing captured text: equal current release-pressure margins do not establish its analyst conclusion about varying preparation delay. Scenario 1 tests no such variation. The export annotation is bound to that capture's exact source hash; a future capture does not automatically inherit it. See [the additional calibration concern](../evaluation/calibration/README.md). The remaining dense fan wording and scenario 3's suggestion to wait for an update need audience testing; they are not corrected by reviewer acceptance.

On 22 October, that note was clarified to identify the known wording flaw in both the analyst text and a claim, and to state that this recording uses the prompt from before commit 7ee37ef. The later live-prompt fix did not regenerate the recording. All model output, trace and capture provenance remain unchanged. Re-capture scenario 1 only when a supervised model run is permitted, count the attempt, and validate the new output before replacing the showcase; no new wording-specific rejection guard was added.

| Capture | Original duration | Actual trace |
|---|---|---|
| tempting-short-pass.json | 86.031 s | Fresh MCP read, validator acceptance, reviewer acceptance |
| press-arrives.json | 26.219 s | MCP read, validator acceptance, reviewer acceptance |
| uncertain-outlet.json | 21.360 s | MCP read, validator acceptance, reviewer acceptance of an explanation of abstention |

These individual observations are not latency benchmarks or a held-out reviewer evaluation. Current captures contain no rejection or repair. The earlier scenario 1 capture had a code-validator rejection and repair; it remains in commit 4082286 and the ignored local audit archive. The analyst generation calls are represented by the resulting draft; the saved trace does not contain a separate analyst-start event.

## Provenance and reuse

### Scenario 1 selection disclosure

Selected 1 of 5 attempts in this documented showcase-selection sequence: attempt 3 remains the showcase. Earlier exploratory model calls are not fully inventoried, so five is not the lifetime call count. The [selection audit](scenario1-selection.json) preserves source hashes, durations, dispositions and actual traces. Raw observations remain in ignored local-artifacts; the two accepted errors are also preserved as [calibration evidence](../evaluation/calibration/README.md).

| Attempt | Duration | Disposition |
|---|---|---|
| 1 | 41.875 s | Reviewer accepted the wrong pressure-arrival subject; earlier code-triggered citation repair |
| 2 | 54.250 s | Reviewer accepted false joint positive margins and incomplete analyst prose |
| 3 | 86.031 s | Selected unchanged; checked facts, dense fan wording, no repair |
| 4 | 98.516 s | Client failure fallback; no approved explanation available |
| 5 | 99.204 s | Client failure fallback; no approved explanation available |

Attempts 4 and 5 used the same experimental two-short-sentence fan prompt. Both returned ChatClientException; neither demonstrates whether that wording instruction helps clarity. The experimental prompt is archived locally and the previous default restored. No new recording was exported and no further selection attempts were made in this round. The fan pilot still needs to test the selected wording.

The two reviewer misses among the first three reviewed outputs are calibration observations, not a reviewer error-rate estimate or evidence of benefit over analyst-only. Prompts and guards changed during that sequence. Current guards were added after the errors were observed. Follow the [paired held-out comparison plan](../../tasks/04-reviewer-comparison.md) before making benefit claims.

Each file records the frozen snapshot ID, canonical SHA-256 hashes of the original numeric assessment and pressure, SHA-256 of the raw source HTTP capture, and its file-modification timestamp in UTC. The timestamp is when the source file was saved, not an independently attested generation start. Hashes document provenance and detect incompatible evidence; they are not signatures or proof of execution.

At startup, recorded mode recomputes evidence, verifies these bindings and runs current draft/contract checks. Missing, malformed or incompatible captures fall back to deterministic text with a recording-unavailable label. Choice and outcome never determine the captured interpretation. No live agent, model or MCP calls occur during replay; elapsed_s remains the original run duration.

The source artifacts remain ignored local files. tools/export_agent_recordings.py can re-export them only if their assessment and pressure match current code and the accepted draft passes current guards. It does not fabricate outputs, alter explanations or automatically create replacement runs. After any new capture, inspect content and notes before committing an updated fixture.

## Known limitation and rights

Scenario 1's previous capture contained an erroneous keeper-arrival phrase that the reviewer accepted. It was replaced through fresh live generation, not text editing. The old capture remains in commit 4082286 and local audit records; current guards reject its wording. See the [active task](../../tasks/01-keeper-loop.md) for refresh failures and validation. The new explanation has no correction banner. Reviewer acceptance is still not proof of semantic correctness. The unclear wording in scenario 3 refers to the code's stale-observation policy; independent football/scenario review is still pending.

The [rights inventory](../../docs/RIGHTS_AND_SOURCES.md) includes these generated outputs. The project MIT licence is applied with attribution to Keeper's Boots contributors. Captures use only this project's original principles and fictional evidence; the selected text and provenance remain unchanged. Public release and the final release inventory review remain separate actions. No model weights are redistributed.
