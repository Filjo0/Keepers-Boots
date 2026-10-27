# Teen fan concept: Read the Play

Status, 13 October 2026: deferred beyond this submission. No teen recruitment, pilot or feature implementation is planned for this hackathon. The general-fan pitch and adult pilot remain the submission scope. The ideas below are retained as future hypotheses; their plan is inactive.

## Goal

Explore a mobile football challenge that makes evidence worth discussing with friends. This is a product hypothesis, not an implemented extension or evidence that teenagers want it. Preserve the three-scenario keeper MVP, A$0 and the existing outcome/evidence boundaries.

## Branch or worktree

Local main. No recruitment, publication, accounts or additional model calls authorised by this concept note.

## Verified findings

[Ofcom's May 2026 research](https://www.ofcom.org.uk/online-safety/protecting-children/younger-phone-owners-the-rise-of-ai-and-consumption-over-creation-our-latest-look-at-uk-childrens-media-lives) describes phone-based media, short videos and gaming as a social activity among UK children. It also reports that more children consume than create social content. That supports exploring quick participation and friend comparison; it does not prove demand for football quizzes, sharing or celebrations among Australian teenagers. Treat football fans, casual viewers and gamers as different audiences.

The [official challenge](https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md) asks for synthetic events transformed into explainable match intelligence. A short choice/evidence/reveal experience can support that purpose. Entertainment alone does not establish category fit or judging acceptance.

## Plan

Test a proposed 30-60-second round: replay freezes, viewer picks short/wide/long, optionally names a reason, sees one route overlay and one plain-language explanation, then reveals the authored continuation. Another viewer can try the same frozen moment before seeing the first viewer's choice. This is comparing reads, not deciding who is the better footballer.

The recorded continuation is what happened in the synthetic replay; it is not what the viewer's chosen action would have caused. Choosing a different pass must not change that story or award a correct-choice point.

| Option | Possible appeal to test | Weakness / decision |
|---|---|---|
| Read the Play with a friend | Agency, football debate, shared moment | First candidate; choices alone cannot support a winner or leaderboard |
| Explain your take | Short personalised evidence responding to a selected reason | Strong brief fit if it addresses evidence; free-text interpretation needs new guards and validation |
| Choose an original avatar/celebration | Self-expression and a playful recap | Optional later test; original gestures on fictional players, independent of the actual replay outcome |
| Make a short recap card | Show a choice, evidence and what happened | Test whether sharing is wanted; include synthetic/recorded labels and uncertainty so context survives export |
| Realistic face swap / motion capture | Immersion hypothesis | Higher implementation burden with uncertain demand; keep deferred pending interest and rights review |

Personalisation should change useful explanation emphasis, for example responding to a selected concern about pressure, while keeping the facts identical. It must not grade tactical choices or pretend a model-generated explanation is a coach's approval.

Before coding, compare concept storyboards and the existing loop with a small, appropriately consented teen football-fan sample. Keep the adult pilot in tasks/02-fan-understanding.md separate. Record actual ages in broad groups, recruitment limitations and dissent; do not treat convenience participants as representative. No participant contact or data collection occurs through this repository.

Ask which concept they would actually try, why they might skip, whether they voluntarily request a second moment, whether friend comparison matters, and whether they can explain the evidence/recording distinction unaided. Ask about celebration interest after the core task. No invented learning, retention or share-rate results.

If a prototype is warranted, owning files are web/index.html, web/app.js and web/styles.css, with tools/browser_smoke.mjs for desktop/mobile verification. Start with local turn-taking and selected reasons; network multiplayer, accounts and automatic social posting need a separate task. Keep existing explanation and immutable-evidence contracts. If the presentation still encourages correct-pass scores or counterfactual outcome beliefs, revise it before rewards.

## Changes made

Concept and critical comparison documented only. Existing app behaviour is unchanged.

## Validation

Sources checked 12 October 2026. No teen pilot or feature/runtime evidence exists. Run tools/check_docs.py for local document links.

## Remaining work / next action

Defer this concept until after the current submission. The only immediate follow-up is the friend-interest question in the existing adult pilot, tasks/02-fan-understanding.md. Build turn-taking only if those responses support it. Any later reason input uses a fixed list. Future research involving minors needs an appropriate parent/guardian consent and participant-data plan before recruitment.
