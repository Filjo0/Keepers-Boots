# Project brief

## Pitch
Before the save: understand the keeper's choices.

Fans watch a synthetic football sequence, choose the goalkeeper's action before the outcome, inspect the options and their evidence, and receive an explanation at their preferred depth.

## Audience and problem
Primary: curious fans who want to understand decisions under pressure.
Secondary: analysts and studio producers who need concise, inspectable explanations.
A narrow decision loop is the first product. It does not promise to train elite goalkeepers.

The first setting is a studio, halftime or on-demand replay companion: "What could the keeper see, and how did the available ground routes compare?" Live-feed synchronisation and whole-match coverage need separate evidence. Participation and entertainment are product goals alongside understanding; the explanation must still trace to match data.

## MVP
- Three scripted goalkeeper scenarios.
- Two-dimensional pitch replay with fictional clubs and players.
- Freeze, choose, inspect, reveal and recap.
- Deterministic geometry and versioned assumptions.
- Two substantive agents: analyst and reviewer/editor.
- Fan and analyst presentation from the same evidence.
- Explicit abstention when evidence cannot distinguish options.
- Reproducible local install; a public demo route is deferred until it can meet the A$0 budget.

## Five-stage pipeline
| Stage | Project implementation |
|---|---|
| Ingest | Stream/replay timestamped synthetic frames and events |
| Interpret | Detect the scripted decision and calculate option evidence |
| Explain | Analyst interprets; reviewer checks; deterministic validators enforce facts |
| Render | Pitch, option cards, evidence markers and timed insight cards |
| Personalise | Casual versus analyst wording and evidence depth; selected keeper perspective |

## Why this scope
The goalkeeper theme is not globally novel. The proposed contribution is an accessible fan experience for pre-action distribution decisions, with available-information boundaries and visible evidence. See [Research](RESEARCH.md).

This is a scoped product hypothesis, not a predicted competition winner. The [idea stress test](IDEA_STRESS_TEST.md) challenges its synthetic realism, fan appeal, recap coverage and actual need for two agents, alongside the proposed face/avatar and celebration experiences.

## Completion definition
A fresh install can run the three-scenario loop; with an available local model, reviewers can inspect reviewed claims, trigger abstention/fallback and see a recorded sequence recap. The video target remains under two minutes. Cloud deployment and public access require separate evidence.

The recap covers the demonstrated keeper sequences. Do not describe it as a comprehensive match recap or score the fan's choices as correct without a separately justified evaluation basis.

## Claims we can earn
- Deterministic calculations reproduce from a frozen snapshot.
- Future events do not change the assessment.
- Displayed numerical facts match evidence.
- Our sampled users can understand the demonstrated trade-offs, if measured.

Synthetic outcomes do not establish real-world decision optimality, player rankings, causal substitution effects, physiology or improved coaching performance.
