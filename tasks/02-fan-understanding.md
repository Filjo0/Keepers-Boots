# Scenario 1 fan-understanding pilot

## Goal
Determine whether a small sample of fans can use and enjoy the keeper loop while distinguishing frozen model evidence from the later recording. Separately track scenario credibility and eventual reviewer-agent value. No participant results have been collected.

## Branch or worktree
Standalone local Keepers-Boots repository, main. Implementation status is in [the keeper-loop task](01-keeper-loop.md).

## Verified findings
- Existing geometry compares sampled ground-route timings under declared assumptions; it does not supply universally correct choices or pass probabilities.
- The default recording completes a short pass; the alternative intercepts it without changing frozen evidence.
- The project's [evaluation protocol](../docs/EVALUATION.md) already separates scenario validity, software checks and agent comparisons. This discovery task does not rewrite those frozen definitions.

## Plan

### Fan appeal and comprehension
Recruit a small convenience sample of approximately five adult football viewers with varied familiarity, reporting the actual count. Do not describe them as representative of all fans. The repository does not recruit or contact anyone automatically.

Give each participant one independent attempt without explaining the intended lesson. Observe navigation, skips, choice, evidence inspection, view selection, replay and completion time. Before opening the optional comprehension form, ask:

1. What did you notice about the two ground routes? Explain in your own words.
2. The recorded short pass completed. What, if anything, does that change about the earlier evidence?
3. What does the model leave unknown? Would you describe the wide pass as guaranteed to succeed?
4. If you chose a different action, did the recording show what your choice would have caused?
5. Would you use this during a halftime/on-demand replay? What would make you skip or return?
6. Would you want a friend to try this same moment?

Record the unaided answer first, then use the form for explanatory feedback. Do not count a response repeated after feedback as unaided understanding. Ask interest in an optional avatar/celebration separately after the core questions; interest does not justify building it or demonstrate understanding.

Record the friend-interest answer and volunteered reason separately from comprehension. Implement pass-the-phone turn-taking only if adult pilot responses support it; no accounts or backend extension is proposed. Any later reason input must use a fixed list, not free text. No friend mechanic is implemented in this round.

Use anonymous participant IDs and volunteered football familiarity, without names, faces or contact details. Keep only consented notes; do not publish identifiable quotes. The browser form itself stores and sends nothing.

Use [the empty results-sheet template](../data/pilot/adult-results-template.csv) for session notes. Copy it into ignored local-artifacts for actual consented responses; never overwrite the header-only tracked template or commit identifiable participant material. It contains no collected observations.

Use [the facilitator script](../data/pilot/facilitator-script.txt) for consistent consent, a neutral unaided attempt and the same six questions before feedback. Record display_mode as recorded/Fan or recorded/Analyst, including any switches, to distinguish these sessions from experimental live inference. Start with a fresh scenario 1 attempt and keep later exploratory answers separate.

### Record outcomes without grading choices
For each participant record: observed completion/skip, help needed, elapsed interaction time, selected mode, paraphrased trade-off, outcome/evidence distinction, recognition of model limits and recording/alternative distinction, plus stated interest and confusion. Mark each comprehension observation as demonstrated, unclear or contradicted and retain the supporting answer. This is coding an explanation response, not assigning a correct football action.

Report counts with denominators, conflicting observations and sample limitations. No numerical improvement or learning-effectiveness claim follows from a small one-session pilot. If most participants cannot distinguish model findings from guaranteed outcomes, fix the wording/interaction before adding rewards, and record any revised questions before the next round.

### Scenario realism, separately
Ask an independent, explicitly identified football reviewer to inspect the authored positions, press movement, option plausibility and assumptions, including cases not used to tune the generator. Record their role, exact scope, disagreements and date only with permission. Tests passing or participants liking the game cannot substitute for this review. Until it happens, principles and scenarios remain drafts rather than coach-validated content.

### Reviewer-agent value, later
Before claiming reviewer benefit, compare analyst-only against analyst-plus-reviewer on the same held-out cases from the existing protocol. Include semantically misleading claims with correct numbers, unsupported causal interpretations and uncertainty failures. Report useful corrections, false rejections, factual errors, latency and cost. Do not claim reviewer benefit from agent count, a staged single typo or deterministic checks that already reject the claim.

## Changes made
Pilot procedure and questions prepared. The optional in-page form supports two scope distinctions with explanatory feedback and no decision score. It is a usability aid, not a measurement dashboard.

## Validation
Browser automation can verify controls, wording and feedback paths. It cannot establish fan appeal, scenario realism or agent benefit. Actual participant and reviewer results are pending.

## Results record
No observations yet. Add a dated round with anonymous sample description, conditions, counts/denominators, dissenting answers, observed friction, unmeasured items and the next decision. Do not invent placeholder results.

## Remaining work and next action
Run the actual participant sessions with the functioning local loop. Complete independent scenario review separately. Keep celebrations deferred until the core interaction is understood and there is observed interest. Agent comparison requires the separate held-out experiment; the workflow is already implemented.

## Current three-scenario follow-up

The local Microsoft/MCP integration and three browser moments are now runtime verified; [the active task](01-keeper-loop.md) records exact evidence. Keep scenario 1 as the primary unaided attempt above. After collecting its answers, optionally show pressure and uncertainty moments and record these exploratory questions separately:

- What does the extra touch change under the declared timing model?
- Why does the system decline the current route comparison when V03's observation is old? What new information would help?
- Does the reviewer-checked label mean a coach approved the explanation, or only that a model reviewed it?
- Was the waiting state tolerable when numeric evidence was already available?

Do not merge these later, potentially primed answers into the primary unaided results. Reviewer benefit still requires the separate frozen comparison protocol; software tests and accepted model output are not participant evidence.
