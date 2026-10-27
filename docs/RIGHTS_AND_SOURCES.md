# Rights, sources and project separation

## Private Coach KB
The personal Coach KB is excluded from this project: corpus, books, source excerpts, embeddings, database, derived retrieval service and credentials.
Do not connect the public demo to it or upload it to Azure.
General lessons may inform independently written project material, but rewriting alone is not rights clearance.

## Project content
Use original scenario scripts, fictional teams/players and original graphics.
The principles in this repository are newly drafted text. Human coaching review is pending.
Do not call them approved, expert-reviewed or licensed from a federation.

## External material
A public web page can be cited without copying its graphics or long passages into the app.
Public accessibility does not itself authorize redistribution or broad reuse.
Check licenses/terms before incorporating text, media, datasets, code or models.
Maintain a source/asset inventory with URL, owner, license/permission, use and attribution.

## Predictor
Reuse general engineering ideas such as timestamps, immutable observations and forward-only evaluation.
No betting models, private code, provider payloads, databases, credentials or production services have been copied.
This is a newly created project, with its own future release lifecycle.

## Hackathon/publication
Review current [official rules](https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md), including third-party rights and the organizers' submission-use license, before publication.
The owner agreed to MIT and delegated the attribution choice on 15 October 2026. The root [LICENSE](../LICENSE) now uses Copyright (c) 2026 Keeper's Boots contributors. It applies to project material to the extent rights are held; third-party components retain their own terms. No account-derived personal name was used. Public repository creation, publishing and submission remain separate actions.
No Premier League logos, real kits, player likenesses or match footage are included.
Section 7 of the rules grants the organizers broad, perpetual reuse rights in a submitted entry. Public submission therefore needs deliberate ownership/rights review, not just a clean repository scan.

## Inventory at bootstrap
| Asset | Origin | Status |
|---|---|---|
| Source code and tests | Written for this project | MIT; reviewed source snapshot published 27 October |
| Synthetic fixture | Project's own generator | Fictional, reproducible |
| Keeper principles | Original draft text | Human review pending |
| Recorded agent text and handoff traces | Three local Gemma/Microsoft workflow captures, 12 October 2026 | Original outputs preserved; hashes bound; selected generic football text inspected against original synthetic inputs; project MIT applies to held rights; source snapshot published 27 October |
| Calibration failures and selection audit | Two original reviewer-approved errors and five-attempt showcase-selection metadata | Frozen visible evidence and unedited interpretations only; excluded from held-out scoring; project MIT applies to held rights; source snapshot published 27 October |
| Research links | Public primary sources and product pages | Linked references only |

## Dependency and model boundaries

The runtime now uses pinned Agent Framework, MCP, OpenAI protocol client, Pydantic and JSON Schema packages. Their installed license metadata and notices must accompany any redistribution; requirements.txt records versions. No third-party football assets or private KB packages are incorporated.

Collected 15 October: [THIRD_PARTY_NOTICES.txt](../THIRD_PARTY_NOTICES.txt) includes the original installed notice texts for all 42 pinned Python packages, with canonical aggregate line endings. [The manifest](../data/release/dependency-notices.json) binds exact versions, environment markers and original notice-file byte hashes. Reproduce with tools/export_dependency_notices.py in this project's Windows environment; --check detects stale output. It fails on missing notices or mismatched versions. The notice set includes Windows-marked pywin32 and preserves separate licences including certifi's MPL-2.0. This source preview does not vendor wheels or native libraries; notice collection is not a completed native-binary redistribution audit or permission to relicense those dependencies as MIT. The Docker definition copies the notice file; container build and native-component redistribution checks remain pending.

Local model weights remain in the existing user's cache and are not bundled, copied into the container or uploaded. Gemma and Qwen have model-specific terms; using an existing endpoint does not select a publication license for those weights. Review the chosen model's upstream terms before changing distribution. Inspecting nonsecret provider/model wiring in the separate project is not permission to import its corpus, prompts or services.
Checked 2026-10-12: Google's [Gemma 4 model card](https://ai.google.dev/gemma/docs/core/model_card_4) identifies Apache 2.0, and the [model licence](https://ai.google.dev/gemma/apache_2) supplies its terms. Google's older [Gemma terms](https://ai.google.dev/gemma/terms) explicitly direct Gemma 4 users to that separate licence; do not apply the older custom terms to this E4B model. This confirms the upstream model licence, not a completed audit of all generated text, quantization notices or project dependencies. No weights are redistributed here.
Recorded mode bundles only selected explanations, citations, traces and nonsecret provenance from this project's synthetic runs. It excludes the original fan choice, sessions, model endpoint, local paths, weights and private knowledge. These new files are release assets and need the generated-output and licence review before publication; local export is not public release or rights clearance.

On 13 October, a single local Phi trial used [Microsoft Phi-4-mini-instruct](https://huggingface.co/microsoft/Phi-4-mini-instruct), declared MIT, through the [Unsloth Q4_K_M conversion](https://huggingface.co/unsloth/Phi-4-mini-instruct-GGUF/blob/78eb92a46fc37e6b524df991ed9aca9bc6aa7b80/README.md), also declared MIT. The 2,491,874,272-byte GGUF was downloaded only into ignored local-artifacts/phi-trial and verified against the published LFS SHA-256 88c00229914083cd112853aab84ed51b87bdf6b9ce42f532d8c85c7c63b1730a. The trial did not pass workflow acceptance; neither weights nor output replace the Gemma defaults or release recordings. No weights or new third-party code are bundled for publication. Model licensing does not select the copyright-holder name for this project's MIT licence.

Inspected installed notices on 2026-10-12:

| Package | Version | License |
|---|---|---|
| agent-framework-core | 1.21.0 | MIT, installed LICENSE |
| agent-framework-openai | 1.16.0 | MIT, installed LICENSE |
| mcp | 1.30.0 | MIT |
| openai | 3.28.0 | Apache-2.0 |
| pydantic | 2.14.0 | MIT |
| jsonschema | 4.26.0 | MIT |

This is a dependency inventory, not a completed native-component redistribution audit. The project's MIT licence does not replace third-party terms. The selected source preview and tracked history passed forbidden-path and redacted credential-pattern checks on 15 October; no weights, private corpus or raw local captures are included. Such checks do not establish rights in arbitrary future generated text. The owner authorised public materials and submission on 27 October. The reviewed source is now public at https://github.com/Filjo0/Keepers-Boots; an anonymous download was verified against all 92 committed source files. The original local Git history was not uploaded, preserving its author email metadata. No public demo video or submitted entry exists yet.
