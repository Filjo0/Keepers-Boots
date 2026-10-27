# In the Keeper's Boots

**Before the save: understand the keeper's choices.**

A new fan experience for the Inside the Game hackathon: replay a synthetic football sequence, freeze before the goalkeeper acts, choose a pass, inspect the evidence, and then reveal the outcome.
Here, ingest means loading and replaying generated scenario data. Live event-feed ingestion is not implemented.

## Current state

Local project, created 2026-10-09. Three synthetic scenarios, frozen geometry, browser/API loop, five MCP tools and a Microsoft Agent Framework analyst/reviewer workflow are implemented. Cloud deployment, independent scenario review, fan pilot and submission remain pending. The budget is A$0.

The single operational status and next action live in [the active task](tasks/01-keeper-loop.md).

Verified locally on 2026-10-27: 75 tests passed under the normal Windows supervisor, including real MCP stdio and 14 browser-independent frontend checks. Dependency checks, all 42 package notices and the CLI passed. All three recorded HTTP loops passed, and the owner checked the three scenarios on a phone. The latest fan/analyst presentation change still needs a real browser check. Earlier evidence includes live agent/API loops and a clean same-machine recorded installation without agent/model/MCP packages. Numerical evidence stays frozen across polling and reveal. Fan appeal, independent scenario realism and reviewer benefit are unmeasured.

[GitHub Actions checks](.github/workflows/checks.yml) are prepared for the public repository: pinned dependencies, the complete suite, documentation, CLI and whitespace checks on a standard Windows runner. The workflow skips private repositories under A$0, uses a read-only token and makes no model calls. Its commands passed locally on 13 October; execution on GitHub awaits publication. This is engineering validation, not evidence of additional hero-technology use.

[MIT](LICENSE) applies to the project, with attribution to Keeper's Boots contributors. [Dependency notices](THIRD_PARTY_NOTICES.txt) preserve installed notices for all 42 pinned Python packages; their source hashes are in [the notice manifest](data/release/dependency-notices.json). These components retain their own licences. Public publishing and submission were authorised on 27 October; the repository and video have not yet been published. A local preview can be built with tools/build_preview.py after staging the complete source. It excludes private/local artifacts and weights and includes an explicit unpublished label plus file hashes.

The public repository will start from a reviewed source snapshot using a GitHub no-reply author identity. Historical commit IDs in audit notes refer to the original local development history. The published files retain the [calibration failures](data/evaluation/calibration/README.md), capture-selection inventory and known limitations; these do not depend on publishing personal author metadata.

## Run locally

Use Python 3.12 and this project's virtual environment. The deterministic CLI/browser needs no third-party packages. Install pinned dependencies for MCP, Microsoft agents and the complete test suite. No cloud account or API keys are required.

~~~powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m keepers_boots
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tools/check_docs.py
~~~

The CLI prints synthetic model evidence as JSON. It is not an AI explanation or a real football recommendation.

For this Windows laptop, [the optional supervised launcher](docs/OPERATIONS.md#laptop-resource-limits) adds resource checks, a job committed-memory cap and cleanup of its own process tree. A shared machine mutex prevents overlapping supervised jobs across checkouts. The direct commands above remain the portable inspection path; ordinary supervised tests/recorded mode do not require NVIDIA hardware. This tool cannot cap all physical RAM/GPU usage or control unrelated applications.

### See the captured agents without model hardware

This is the recommended inspection path. Live inference below is experimental and has recent client failures; recorded mode replays captured executions and does not demonstrate fresh inference.

Use Python 3.12. Recorded mode needs only the existing Pydantic/JSON Schema dependencies; it does not require Microsoft Agent Framework, a GPU, weights, a model server or API keys:

~~~powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install pydantic==2.14.0 jsonschema==4.26.0
.\.venv\Scripts\python.exe -m keepers_boots.api --agents recorded
~~~

Open http://127.0.0.1:8000, choose a moment, skip to the freeze and choose an action. The evidence shows recorded Gemma explanations, citations and actual Microsoft analyst/reviewer traces captured on 12 October. The current captures were accepted without repair; do not narrate a rejection that their traces do not contain. The UI labels recorded output and states that no live agent/model/MCP calls occur. Both audience variants remain available. Current numeric evidence is recomputed and matched to the capture before the text is used; a missing or incompatible recording falls back explicitly.

Fan view turns the computed route findings into plain-language cards and explains the pressure diagram. Analyst view adds exact timing ranges, matched comparisons, assumptions, observation identity and the captured handoff. The plain-language cards are deterministic presentations of computed findings; the original captured AI summaries, claims and traces are not rewritten. Switching views keeps the same choice and frozen evidence.

The [recording inventory](data/agent-recordings/README.md) discloses selection of 1 of 5 scenario 1 attempts, provenance and the replacement of an earlier erroneous capture, which remains in Git history/local audit records. The refreshed explanation is an unedited new model output. Captures demonstrate observed runs, not fresh execution or measured reviewer benefit. Install all dependencies above and use local mode below to exercise the live workflow. Public release and the complete rights/licence review remain pending.

Run the three-scenario browser experience with deterministic explanations:

~~~powershell
.\.venv\Scripts\python.exe -m keepers_boots.api
~~~

Open http://127.0.0.1:8000. Select a scenario, play or skip to the freeze, choose with buttons or keys 1/2/3, inspect fan/analyst evidence, and explicitly reveal the recording. Scenario 2 adds pressure/preparation timing; scenario 3 shows an old observation and declines comparison. The optional comprehension check does not rate football choices or save responses. See the [API contract](docs/API.md) and [fan pilot](tasks/02-fan-understanding.md).

### Experimental live inference

For actual local AI execution, start an existing OpenAI-compatible model server first, then run:

~~~powershell
.\.venv\Scripts\python.exe -m keepers_boots.api --agents local --model gemma4:e4b-llama.cpp --model-endpoint http://127.0.0.1:8088/v1
~~~

These defaults match PythonProject2's current source configuration, not a verified record of its last-used model. Its alternative Ollama configuration names Qwen; a compatible local Qwen server can be selected with the same flags. Keeper's Boots reuses only the model endpoint, never that project's private knowledge. No runtime or weights are bundled or automatically downloaded.

Microsoft Agent Framework runs the analyst and independent reviewer over frozen MCP evidence. One repair is allowed; unavailable or rejected output leaves the deterministic explanation visible. The browser labels its source and shows the workflow trace. Numeric evidence stays unchanged. [Agent contracts](docs/AGENTS_AND_MCP.md) and [operations](docs/OPERATIONS.md) distinguish implementation from verification.
The design uses layered checks: code computes facts, code guards check specified claim rules, and a reviewer adds a judgment-based check in a fresh context using the same model. The reviewer approved wrong text in two known calibration runs; benefit over an analyst with the same guards is unproven. See the [calibration evidence](data/evaluation/calibration/README.md) and [held-out comparison task](tasks/04-reviewer-comparison.md).

Live mode can take minutes on the tested laptop. Of the last three documented scenario 1 jobs, one completed at 86.031 seconds and two returned ChatClientException fallbacks at 98.516 and 99.204 seconds. This is an observed count across changed prompts, not a general failure-rate estimate. Earlier successful cold runs took 21-86 seconds. Allow up to three minutes per admitted job, plus queue time; the workflow deadline is 180 seconds and provider requests time out after 90 seconds. Deterministic evidence stays usable while waiting and after failure. The underlying client-failure cause is unverified; recorded mode makes no inference calls.

Regenerate the checked-in scenario from its owning source:

~~~powershell
.\.venv\Scripts\python.exe -m keepers_boots --write-scenario data/scenarios/01-tempting-short-pass.json
.\.venv\Scripts\python.exe -m keepers_boots --scenario-id press-arrives --write-scenario data/scenarios/02-the-press-arrives.json
.\.venv\Scripts\python.exe -m keepers_boots --scenario-id uncertain-outlet --write-scenario data/scenarios/03-uncertain-outlet.json
~~~

## Read only what you need

| Need | Document |
|---|---|
| Product, audience, agreed scope | [Project brief](docs/PROJECT.md) |
| Dates, submission and judging | [Hackathon](docs/HACKATHON.md) |
| Current progress and next implementation step | [Active task](tasks/01-keeper-loop.md) |
| Milestones and optional extension gate | [Roadmap](ROADMAP.md) |
| Where the code lives | [Code map](CODEBASE_MAP.md) |
| Components and information boundaries | [Architecture](docs/ARCHITECTURE.md) |
| Data fields, snapshots and observations | [Data contract](docs/DATA_CONTRACT.md) |
| Geometry assumptions and limitations | [Analysis model](docs/ANALYSIS.md) |
| Two agents and bounded MCP tools | [Agents and MCP](docs/AGENTS_AND_MCP.md) |
| Scenario 1 | [The tempting short pass](docs/scenarios/01-tempting-short-pass.md) |
| Scenario 2 | [The press arrives](docs/scenarios/02-the-press-arrives.md) |
| Scenario 3 | [The uncertain outlet](docs/scenarios/03-uncertain-outlet.md) |
| Interface and two-minute demo | [Experience and demo](docs/EXPERIENCE_AND_DEMO.md) |
| Evaluation protocol and acceptance checks | [Evaluation](docs/EVALUATION.md) |
| Azure install, release and operations plan | [Operations](docs/OPERATIONS.md) |
| Draft original coaching principles | [Principles](docs/knowledge/keeper-principles.md) |
| Research, competitors and corrected claims | [Research](docs/RESEARCH.md) |
| Accepted choices and deferred ideas | [Decisions](docs/DECISIONS.md) |
| Challenge purpose and critical review of keeper, face/avatar and celebration ideas | [Idea stress test](docs/IDEA_STRESS_TEST.md) |
| Private KB boundary, attribution and publishing | [Rights and sources](docs/RIGHTS_AND_SOURCES.md) |

## Product boundary

All clubs, players, events and tracking are fictional. Geometry describes a documented simulation. It does not establish real player ability, coaching optimality, training effectiveness or betting value.

The existing predictor and private Coach KB are separate projects. This repository contains no copied predictor code, betting data, private coaching corpus, credentials or real match footage.
