# Experience and demo

## One interaction
1. Play a short synthetic sequence.
2. Freeze at the decision.
3. Choose short, wide or long using mouse, touch or keyboard.
4. Inspect frozen evidence and its assumptions.
5. Reveal the recorded continuation.
6. Read a short recap separating decision quality from outcome.

## Screen
One pitch with a compact score/clock strip, option panel and expandable evidence drawer.
Use fictional club names and original graphics.
Clearly label synthetic tracking and modelled evidence.
Do not rely on colour alone. Supply text equivalents for routes and keyboard-accessible controls.
Pause/skip controls must work without a model response.

## Audience modes
- Fan: one short explanation and one key trade-off.
- Analyst: timings, units, ranges, observations and limitations.
Both use the same immutable evidence.
An optional second language must preserve numbers, identities, negations and uncertainty.

Fan mode should help the viewer identify one visible trade-off; analyst mode should let them audit the observations and assumptions behind it. Distinct controls and tasks should support those needs, beyond changing the explanation's length.

The recap describes the viewer's choices, supported model findings and recorded outcomes separately. Do not display a "correct choices" score or imply that agreement with the recorded action validates the choice. Optional original avatars or celebrations are deferred engagement experiments; see [the idea review](IDEA_STRESS_TEST.md).

## Display states
playing, awaiting_choice, assessing, evidence_ready, insufficient_evidence, revealed, recap.
A model failure transitions to evidence-only fallback, not a blank screen.
Reveal is explicit. Replaying the decision retains the original snapshot and assessment.

## Proposed under-two-minute video
| Time | Demonstration |
|---|---|
| 0-10 s | Problem and pitch; visibly synthetic match |
| 10-30 s | Replay, freeze and fan choice |
| 30-55 s | Two ground routes and inspectable evidence |
| 55-75 s | Successful short-pass outcome; assessment stays unchanged |
| 75-95 s | Uncertain scenario declines to rank |
| 95-110 s | Fan/analyst switch, recap and real workflow trace |
| 110-115 s | Public repository, free test-build instructions and one-sentence takeaway |

Target 115 seconds to leave a buffer. Record functioning software, not a mock screen presented as live.
The [caption/narration draft](../data/demo/narration.srt), [timed shot list](../data/demo/shot-list.csv) and [submission-description draft](../data/demo/submission-description.txt) are prepared. They are production inputs, not a recorded video. Add actual verified public links to the end card only after publication; retain the recorded/synthetic disclosures.
Describe the system as layered checks: code computes facts, code guards check specified claim rules, and a reviewer adds a judgment-based check. Do not say the reviewer catches errors or outperforms one analyst without the held-out result. Ingest is replay of generated scenario data, not a live sports/event feed.
Use a deterministic fallback if the model service fails, and label it.
Record actual reviewer decisions and repairs. If explanations are cached, disclose that the replay reuses a reviewed explanation; do not present cached responsiveness as live generation speed. Individual uncached local calls took 21-86 seconds, so the current product is an on-demand replay prototype rather than verified live-match narration. Keep the fan-facing explanation concise, with detailed model assumptions available in the evidence drawer.
For the hardware-free demonstration use --agents recorded. Its model/date label, no-live-calls disclosure and original elapsed time must remain visible when showing the capture. Current captures contain no repair; do not invent a rejection for the video. The previous scenario 1 capture's missing-citation rejection came from code and remains in audit history. This mode is a recorded execution demonstration, while --agents local exercises the current live pipeline.
If showing the old rejection/repair trace, use footage from the archived capture or its immutable record, labelled "Earlier calibration run; code-triggered repair; reviewer later accepted flawed text". Keep it separate from the current showcase; do not present that repair as a reviewer success or try to force one live. Disclose the showcase selection count from data/agent-recordings/README.md.

## Validation
Test a small number of fans on identifying the trade-off and distinguishing estimated evidence from observed outcome.
Record the sample and questions; do not claim general learning effectiveness from a tiny convenience sample.
