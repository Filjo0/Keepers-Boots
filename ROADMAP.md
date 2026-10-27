# Delivery roadmap

Planning date: 2026-10-09; budget and delivery order revised 2026-10-12. Operational progress is in [the active task](tasks/01-keeper-loop.md); this file defines milestones.

## M0 - foundation
- Create the separate project, linked documentation, scenario 1 generator and deterministic CLI.
- Prove future-event independence, hidden-information isolation and snapshot integrity.
- No cloud/model requests needed.

## M1 - first complete loop, target 12 October
- Implement a small HTTP API and browser pitch renderer for scenario 1.
- Play, pause at the decision, choose, inspect evidence, reveal and recap.
- Provide a deterministic explanation fallback and accessible controls.
- Prepare a portable container and verify local integration early. Azure deployment is deferred under the A$0 budget.

## M2 - keeper MVP, target 18-19 October (about day 10)
- All three scenarios work.
- Geometry tools are exposed through MCP.
- Analyst and reviewer run via Microsoft Agent Framework with available local inference; no paid model calls.
- The uncertain scenario declines unsupported ranking.
- Numerical/evidence validation, bounded repair and fallback paths work.
- Verify the real local loop, including reviewer rejection, repair and fallback; measure latency and failed-claim rates.
- Then run the small fan pilot and independent scenario review; no claim of reviewer benefit without a baseline comparison.

## M3 - conditional extension
Only if M2 is complete and tested by 19 October:
- Add one midfielder receiving step to the same sequence.
- A scripted observation refresh updates known positions and their age.
- Do not claim head tracking, gaze, attention or a physiological model.
- If M2 slips, omit this extension.

## M4 - polish and submission, target 20-26 October
- Finish fan/analyst modes, recap, evidence drill-down and error handling.
- Add a second language only after the evidence-preservation checks work.
- Fresh-environment install and local browser/model smoke; verify a public route separately if one is authorised at A$0.
- Record a video under two minutes; prepare pitch and public repository.
- Verify rights, current rules and public demo availability before publishing.
- Aim to submit by 26 October; retain the final day as contingency.

## External deadlines
See [Hackathon](docs/HACKATHON.md). Registration was completed by the user. Submission remains a user-account action and is pending.

## Stop conditions
- Never relax evidence boundaries to obtain a more decisive explanation.
- Never add optional features while the end-to-end keeper loop is broken.
- Pause cloud actions when access, cost limit or deployment authorization is absent.
- A change to claims or evaluation rules requires a versioned rationale before inspecting new outcomes.
