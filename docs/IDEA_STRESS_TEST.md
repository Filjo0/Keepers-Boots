# Product ideas: critical review

Reviewed 2026-10-09. This is a product reasoning record, not a competition score prediction, coaching endorsement or implementation report. Current progress remains in [the active task](../tasks/01-keeper-loop.md).

## What the challenge is trying to achieve

The [official rules](https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md), sections 4.1 and 6, ask for synthetic events to become explainable, personalised match experiences through ingest, interpret, explain, render and personalise. The five judging areas have equal weight: technical implementation, agentic design, impact, experience and category fit. Theme and relevant technology also face an initial viability screen; a good-looking experience alone does not settle it.

The wider partnership has a broader purpose. The [Premier League announcement](https://www.premierleague.com/en/news/4338015) describes fan engagement, match analysis, infrastructure and operations. [Microsoft's account](https://news.microsoft.com/source/emea/features/premier-league-microsoft-partnership/) describes reaching newcomers as well as established fans, and helping them build a connection with clubs. These sources support engagement and understanding together. They do not establish that entertainment is unwelcome.

Our interpretation: make the information behind a match accessible, personally relevant and enjoyable, with a credible route from data to the experience. For Microsoft, showing useful applications of its platform is consistent with the judging criteria. Calling the challenge merely a technology showcase, or claiming to know the organisers' deeper private motives, goes beyond the evidence.

## Corrections to the earlier discussion

| Earlier claim | More defensible version |
|---|---|
| The purpose is understanding, not entertainment | Entertainment can deliver understanding. The required event-to-insight connection must survive beneath the visual effect. |
| Face swapping would score poorly | A standalone swap leaves major brief gaps. Actual scoring depends on the complete entry and judges; we cannot predict a score. |
| Face swapping is not unique because EA FC and apps do it | No checked source here establishes that exact comparison. Existing avatar features would not prove this particular interaction lacks differentiation anyway. |
| Real-player swaps are automatically illegal or unacceptable | Rights, consent, source-media permissions and presentation depend on the implementation. The rules do not provide blanket permission or a blanket face-swap ban. |
| Personalisation should only be garnish | It can be central to the product. It still needs meaningful intelligence to personalise. |
| Keeper's Boots is the winning shape | It is the current scoped hypothesis. It has substantial modelling, user-value and delivery risks. |
| You read the press correctly in 2 of 3 situations | We lack a validated correct-action label. A model comparison, authored continuation or completed pass cannot justify that score. |

## How to compare ideas

Use six questions before discussing more features:

1. Who wants this, at what moment, and what do they gain?
2. What match information changes the experience beyond a generic goal trigger?
3. What can we truthfully explain from the available data?
4. What is the smallest convincing demonstration, including its failure path?
5. Which part requires AI judgement, and what does a second agent improve?
6. Which assumption could make the idea fail even if the software works?

The following assessments are engineering and product judgements, not measured demand, exhaustive competitor research or legal conclusions.

## Your face on a player

**Strongest case:** participation and identity. A fan can see themselves within a memorable football moment and share it. This is a different user benefit from studying tactics, and should be taken seriously on its own terms.

**Core weakness for this entry:** swapping appearance does not itself interpret the match. If any goal clip produces essentially the same result, the football information is only a trigger. Adding an LLM that announces the scorer does not solve that weakness.

**Important distinctions:** replacing a real player's face in a real recording, rendering your face on an original fictional avatar, and inserting an avatar beside a fictional team are three different projects. The first depends on the underlying footage and likeness permissions. Owning the inserted selfie does not clear the base recording. The fictional-avatar versions give us more control over content and presentation, but an uploaded face still requires a deliberate storage/deletion and sharing design. A face image is not automatically a face-recognition system; do not invent a biometric pipeline we do not need.

**Delivery stress:** convincing video compositing must handle movement, occlusion, lighting and temporal consistency. A stylised avatar avoids some of those demands but changes the promise. Neither quality nor latency has been measured here. A simple selectable avatar can test whether participation matters before taking on photo uploads or realistic rendering.

**Falsification question:** if viewers enjoy the image but cannot identify anything distinctive about the goal, has the feature advanced this challenge's core pipeline?

**Recommendation:** defer realistic face swapping. Treat an original avatar as a possible later engagement experiment, rather than a prerequisite for Keeper's Boots.

## Celebrate alongside the scoring team

**Strongest case:** belonging. Joining a team celebration may appeal to a casual fan who would never open a geometry table. It can make the recap feel personally meaningful without grading the fan's football knowledge.

**Core weakness:** a generic celebration after every goal has little explanatory content. Choosing the favourite team's colours improves relevance, but still does not explain how the moment developed.

**A stronger version:** first replay a short original synthetic attack, show the build-up contribution that the data supports, then let an original fan avatar join the fictional team's celebration. The user can choose whose contribution to follow. The explanation stands on its own; the celebration adds participation.

**Delivery stress:** a shared celebratory scene requires additional characters and animation. Real-time multiplayer is a separate feature and is not necessary to test the emotional idea. A rendered group scene is not evidence that actual players or other fans are participating live. The keeper MVP currently contains distribution scenarios, not a generated scoring attack; adding this version creates new scenario work as well as visual work.

**Falsification question:** does the celebration improve interest in the explanation or return visits, or do viewers skip everything before it?

**Recommendation:** retain as a plausible extension for an explanatory goal recap. Keep it outside the three-scenario keeper MVP. Do not award it only for a supposedly correct pass choice.

## Players perform your celebration

**Strongest case:** creative authorship. The fan influences what the team does, rather than only seeing their face inserted. A repeatable signature gesture may be a clearer interaction than realistic face swapping.

**Two scopes:** selecting one of a few original animations is manageable to prototype; recording an arbitrary personal movement and transferring it to a whole team is a motion-capture and animation project. These should not share one estimate or completion claim.

**Core weakness:** the gesture still needs an insight-producing event pipeline elsewhere. A motion-processing agent is not automatically a match-intelligence agent. A more elaborate animation cannot repair missing interpretation.

**Delivery stress:** arbitrary movement transfer introduces body tracking, rig compatibility, occlusion, animation retargeting, clipping and input handling. Those are engineering concerns to investigate, not features already available in this repository. Selected original gestures can be shown with stylised figures and no camera input. Custom uploads introduce additional content and data-handling decisions.

**Falsification question:** does authorship add enough value beyond selecting a simple celebration to justify the extra capture and rendering work?

**Recommendation:** if an engagement extension is later justified, test a small set of original selectable celebrations before custom motion capture. For the current MVP, defer both. No real-player endorsement or real-match recreation should be implied.

## Keeper's Boots, subjected to the same scrutiny

**Strongest case:** a clear interaction joins participation to explanation. The fan makes a choice before seeing the outcome, then can inspect why the supported ground routes differ. The completed short pass creates a useful tension between recorded success and modelled exposure.

**Risk 1: authored evidence can confirm the author's story.** We chose the positions, capacities and script. Reproducible tests establish internal consistency, not football realism or tactical wisdom. Untuned variations and independent scenario review are necessary before broader claims. Do not hide inconvenient cases or tune every fixture to make the same action look attractive.

**Risk 2: geometry answers a narrower question than the interface suggests.** Point-arrival margins describe sampled interception opportunities under declared assumptions. They do not include every tactical objective, acceleration, reach, execution error or aerial contest. Positive margin is not safety; an unmodelled clearance cannot be marked wrong. Keep the fan language as cautious as the analyst evidence.

**Risk 3: understanding may not be engaging.** Fans may prefer to watch rather than stop and choose, or may find fictional players emotionally thin. The decision interaction should be optional and short. A studio or halftime replay is a plausible initial setting; pausing a replay does not demonstrate synchronisation with a live broadcast. That distinction belongs in the pitch.

**Risk 4: three moments are not a whole match.** A recap of these decisions is a sequence recap. It must not masquerade as a comprehensive match summary. Event ingestion, timing, recap scope and eventual broadcast use need to be visible in the demo. The [project brief](PROJECT.md) maps the intended pipeline; the current CLI is only its calculation foundation.

**Risk 5: the AI may be unnecessary for the easiest case.** Code already produces the geometric finding, and a template can explain it. The analyst must add useful interpretation without inventing facts. The reviewer should catch semantic overreach, unsupported tactical inference and mishandled uncertainty that numerical validation alone misses. If those benefits cannot be demonstrated, claiming superior multi-agent intelligence is unjustified. Follow the existing [agent comparison](AGENTS_AND_MCP.md) and [evaluation protocol](EVALUATION.md).

**Risk 6: personalisation may only change paragraph length.** The casual fan needs a visible trade-off and a plain-language takeaway; the analyst needs observation times, assumptions, uncertainty and inspectable evidence. Distinct tasks and controls matter more than two differently worded paragraphs. Neither view may become more certain than the underlying evidence.

**Risk 7: the product needs an abstention that feels useful.** If stale observations cause a refusal, show what is missing and why the comparison cannot be made. A blank explanation or an apologetic wall of text undermines the uncertain scenario's value.

**Recommendation:** continue with the keeper concept as the smallest current route to an event-to-explanation experience. This is a scope and delivery judgement, not proof of demand, novelty, learning benefit or competition success. Keep the strongest visual interaction; earn the explanation and agent claims through testing.

## Comparison at a glance

| Idea | Primary fan value | Insight supplied by the idea itself | Smallest meaningful next test | Current recommendation |
|---|---|---|---|---|
| Face on a player | Identity and shareability | Appearance change only | Compare a simple original avatar with no avatar in an explanatory recap | Defer realistic swapping |
| Join the team celebration | Belonging | Participation after an event | Test whether an optional group scene increases interest in the preceding explanation | Later goal-recap candidate |
| Team uses your celebration | Creative authorship | Gesture choice only | Compare selectable original gestures before considering movement capture | Defer custom capture |
| Keeper's Boots | Agency and understanding | Choice tied to frozen model evidence | Complete one browser loop; observe whether users distinguish opportunity from outcome | Continue scoped core |

These are not mutually exclusive businesses or experiences. The decision here concerns what this project can credibly deliver first.

## Other ideas already recorded in the project

These are older documented proposals, included for completeness; the newest ideas above receive the deeper review. No additional feature is accepted by this table.

| Idea family | Strongest case | Assumption to challenge | Decision for this submission |
|---|---|---|---|
| Midfielder information refresh / scanning | Show why old information changes a receiving decision | A scripted refresh is not real gaze, attention or awareness | Preserve the existing post-MVP gate |
| Ideal criteria for every position | Make role-specific tactics accessible | There is no context-free ideal player or universal policy | Defer; narrow to an explicit phase and objective if revisited |
| Effort, fuel, calories, nutrition | Connect physical demands to play | Movement data does not establish an individual's fatigue, reserves or dietary needs | Outside MVP; existing research limits apply |
| Substitutions / Coach's Eye | Explain tactical changes a viewer notices | A plausible story does not establish the causal benefit of a substitution | Defer pending stronger assumptions and evaluation |
| Passing Story / Press Escape | Follow a whole attacking pattern | Chaining individual margins does not validate a possession-value or success model | Promising later reuse; finish one decision first |
| Tackles and their causes | Explain a disruptive moment | Sparse events cannot identify intention or technique | Defer; separate observable facts from interpretation |
| Free-kicks, penalties, sweeping | Familiar high-interest keeper moments | Current ground-pass geometry does not model flight, reach or shot stopping | Separate modelling and review required |
| Stars, strongest players, physical matchups | Give fans familiar comparison hooks | A label, body trait or scripted capacity is not measured player ability | Fictional explicit capacities only; no real-player ratings |
| H2H / Rematch / counterfactuals | Let fans compare competing choices | An alternative script is not a validated prediction of what would have happened | Explain authored alternatives; do not imply causal certainty |
| Fan debate, audio, multilingual modes | Participation and access for different audiences | Every rendition must preserve facts and uncertainty; accessibility needs testing | Candidate after the core loop; breadth has a verification cost |
| Large event platform / many agents | Scale and orchestration demonstration | More services and agents may add complexity without user value | Add only for a measured need |

Sources and modelling boundaries for these older proposals remain in [Research](RESEARCH.md), [Decisions](DECISIONS.md) and [Rights and sources](RIGHTS_AND_SOURCES.md). This review does not reclassify them as validated or implemented.

## What evidence should change our mind

These are proposed product-discovery questions, not changes to the frozen evaluation protocol:

- For the core loop, ask viewers to describe the trade-off in their own words and separate what the recording shows from what the model estimates. Record confusion, skipped steps and observed completion time as well as positive comments.
- If most sampled viewers only want to see the outcome, investigate an optional insight overlay or guided recap before adding a reward. A celebration might mask a weak interaction rather than fix it.
- If avatar/celebration interest is strong, compare the same explanatory recap with and without the optional feature. Observe comprehension, willingness to replay, waiting time and preference separately. A small convenience sample informs iteration; it does not establish general effectiveness.
- For agent value, use the already-defined analyst-only comparison and corruption cases. Report useful corrections, false rejections, latency and cost. More agent messages are not the outcome being measured.
- Revisit scope only with a recorded reason. The [roadmap](../ROADMAP.md) gates remain in place; any adopted evaluation change needs a versioned rationale before new results are inspected.

## Main idea to carry forward

Before the save: understand the keeper's choices. Build a replay companion that makes the fan's participation produce an inspectable explanation. Keep fun as a real product objective, retain uncertainty, and let the original outcome challenge the fan's first impression without rewriting the evidence.

The celebration proposals remain available as separate engagement hypotheses. They do not need to be dismissed as frivolous, and they do not need to be built into the first keeper loop.
