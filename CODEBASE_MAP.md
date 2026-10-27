# Codebase map

## Implemented foundation

| Area | Owner | Checks |
|---|---|---|
| Three scripted scenarios, fictional roster, alternative continuations | keepers_boots/scenario.py | tests/test_foundation.py, tests/test_agents.py, tests/test_catalog.py |
| Whitelisted decision data, validation, immutable serialized snapshot, hash | keepers_boots/snapshots.py | tests/test_foundation.py |
| Ground-pass timing, preparation, pressure, signed comparisons and uncertainty | keepers_boots/analysis.py | tests/test_foundation.py, tests/test_agents.py |
| JSON CLI and fixture generation | keepers_boots/__main__.py | CLI smoke command |
| Three generated scenarios | data/scenarios/ | regenerate equivalence tests |
| UTF-8 and local Markdown link checking | tools/check_docs.py | run the tool |
| Local HTTP API, bounded sessions, immutable evidence and reveal gating | keepers_boots/api.py | tests/test_api.py |
| SVG replay, accessible choices, fan/analyst evidence and sequence recap | web/index.html, web/app.js, web/styles.css | tests/test_frontend.py, tests/test_web.mjs; tools/browser_smoke.mjs for real layout |
| Wide uncertainty reveal, unchanged snapshot/capture binding and pre-reveal concealment | keepers_boots/scenario.py, keepers_boots/api.py | tests/test_reveals.py |
| Versioned API request/response and snapshot schema | docs/api.schema.json, docs/API.md | HTTP/schema and browser contract checks |
| Fan-understanding discovery procedure | tasks/02-fan-understanding.md | participant results pending |
| Five read-only structured MCP tools | keepers_boots/mcp_server.py | tests/test_agents.py, real stdio transport |
| Microsoft analyst/reviewer, one repair, local inference | keepers_boots/agents.py | tests/test_agents.py; live evidence in active task |
| Structured prose and reference/scope guards | keepers_boots/claims.py | tests/test_agents.py |
| Recorded agent output, evidence binding and capture export | keepers_boots/recordings.py, tools/export_agent_recordings.py, data/agent-recordings/ | tests/test_recordings.py, recorded-mode browser smoke |
| API schemas and cached inference | tests/test_catalog.py | full local suite |
| Real local-model/API smoke with saved statuses | tools/agent_smoke.py | --require-reviewed distinguishes acceptance from fallback |
| Raw SDK output for bounded local probes | tools/captured_agent_server.py | tests/test_probe_capture.py; ignored raw drafts/reviews |
| Laptop resource gate | tools/check_resources.ps1 | PowerShell syntax/runtime checked; defer on memory/thermal/disk pressure |
| Single-workload Windows supervision | tools/run_supervised.py | tests/test_supervisor.py; machine mutex, committed-memory cap, resource refusal, deadline and owned-tree cleanup |
| Capture archives and known calibration misses | tools/agent_smoke.py, tools/export_calibration_evidence.py, data/evaluation/calibration/ | tests/test_capture_audit.py |
| Held-out paired reviewer comparison | tasks/04-reviewer-comparison.md | Implementation and results pending |
| SDK pins and container definition | requirements.in, requirements.txt, Dockerfile | pip check; container build pending |
| Public-repository continuous checks | .github/workflows/checks.yml | Fresh Windows GitHub Actions passed 75 tests, dependencies, notices, docs, CLI and whitespace |
| Dependency notices and hashed source preview | tools/export_dependency_notices.py, tools/build_preview.py | tests/test_dependency_notices.py, tests/test_preview.py |
| Adult pilot sheet and video preparation | data/pilot/adult-results-template.csv, data/demo/ | Actual 115-second Chrome footage and playback verified; allowed-host upload and participant sessions pending |

## Planned owning paths

These paths do not exist yet. Create only for the applicable task.

| Milestone | Proposed owner |
|---|---|
| Authorised cloud deployment | infra/main.bicep; deferred under A$0 budget |

Start with [the active task](tasks/01-keeper-loop.md), then its linked specifications.

Teen audience concept: [tasks/05-teen-fan-concept.md](tasks/05-teen-fan-concept.md), deferred beyond this submission; no implementation or participant evidence.
