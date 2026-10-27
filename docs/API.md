# Local browser/API contract

The three-scenario loop uses the Python standard library and original browser graphics. Optional agents require the pinned dependencies. Run it with the project environment:

~~~powershell
.\.venv\Scripts\python.exe -m keepers_boots.api
~~~

Open http://127.0.0.1:8000. Use --port to choose another local port, or --outcome intercepted to exercise the alternative authored recording. By default the server binds to IPv4 loopback with agents off. Add --agents local, --model and --model-endpoint to use an existing anonymous loopback inference server through Microsoft Agent Framework. No cloud requests are permitted.
Use --agents recorded to inspect captured explanations and handoffs without a model server. It requires Pydantic and JSON Schema for current guards/contracts, but does not import Agent Framework or the model client. No live agent or MCP execution occurs in recorded mode.

For phone testing on the same Wi-Fi, add --lan-ip with the laptop's explicitly chosen RFC1918 IPv4 address (10/8, 172.16/12 or 192.168/16). LAN mode requires --agents recorded, binds only that address and accepts only its exact Host/port with a matching Origin when present. Duplicate Host/Origin headers and cross-site requests are rejected. The default loopback policy and the legacy --host 0.0.0.0 container behaviour remain unchanged; wildcard binding alone does not allow arbitrary LAN hosts. This is a temporary trusted-LAN demo, not internet hosting.

## Contract and operations

[JSON Schema](api.schema.json) defines requests, responses and the frozen decision payload. It is also available at GET /api/schema. Validate each endpoint using its named $defs entry; the root accepts response envelopes. The existing Python snapshot validator additionally checks cross-field constraints such as timestamps, roster completeness and keeper control that JSON Schema alone does not establish.

| Operation | Request | Response definition | State rule |
|---|---|---|---|
| POST /api/start | {} or scenario_id: tempting-short-pass, press-arrives, uncertain-outlet | startResponse | Create a new bounded session |
| GET /api/sessions/{session_id}/decision | No body | decisionResponse | Available observations and options only |
| POST /api/sessions/{session_id}/choice | An option_id from the frozen decision (scenario 2: take-touch, release-short, clear-long) | evidenceResponse | First choice freezes the assessment |
| GET /api/sessions/{session_id}/evidence | No body | evidenceResponse | Requires a choice; reuses first assessment |
| POST /api/sessions/{session_id}/reveal | {} | revealResponse | Requires a choice; explicit outcome request |

Start includes fictional identity metadata, pitch/context and frames up to the decision. It excludes events, continuation, outcome labels, the scripted option and velocities. The final pre-decision frame comes from the frozen available observations, not the current world frame. Earlier frames are synthetic replay visuals, not assessor inputs. Scenario 3 masks each player after its last permitted observation so the replay does not expose later hidden movement.

Decision includes the snapshot hash and allowlisted snapshot. Choice/evidence includes choice, frozen assessment, pressure, explanation and interpretation status/trace, without the recording. Reveal adds continuation, later frames/events and a sequence recap. The numeric assessment remains identical before/after reveal. The explanation may switch from deterministic to reviewed local prose when its background job finishes; both use the same frozen input.

The viewer can request the decision directly or skip the replay; this is an explanatory experience, not an enforced gameplay clock. The concealed content is the original action and continuation. All three options remain visible at the freeze.

## Retry, error and lifetime behaviour

- Repeating a choice or reveal reuses the same assessment and recording; interpretation status may progress independently. Choosing a different action within a session returns 409; start a new attempt instead.
- The process retains at most 128 sessions for one hour from creation. Capacity returns 503; expired/unknown sessions return 404. Restarting the server clears sessions.
- Invalid option/body fields or malformed JSON return 400; wrong media type returns 415; JSON bodies outside 1-1024 bytes return 413. Known endpoints with unsupported GET/POST operations return 405.
- Cross-origin requests and unexpected Host values return 403. The allowed addresses are localhost or 127.0.0.1 at the actual server port. Responses are not cached and no CORS access is enabled.
- Only the three web files and schema are served. Fixtures, source paths and arbitrary filesystem paths return 404. Connections have a five-second socket timeout.
- Errors use {"error":"message"}. The UI keeps visible controls to retry a failed operation or start a new attempt.

This is a local prototype: sessions are process-local, the HTTP server is not a deployment configuration, and no cloud or production verification is implied. [Architecture](ARCHITECTURE.md) describes the intended later integrations.

## What the interface communicates

Play/pause/skip controls work before assessment. Keys 1, 2 and 3 select the actions at the freeze; native buttons also support keyboard and touch. Teams have different shapes and labels, so colour is not the only distinction. The analyst view adds timing ranges, units, model parameters, observation timestamps, snapshot and evidence IDs. View switches reuse evidence.

With agents off, explanation is fixed wording labelled deterministic. With local agents enabled, it starts as deterministic evidence with a running label, then exposes reviewed fan/analyst text and workflow trace or explicitly labelled fallback. One interpretation is cached per scenario per process; polling or changing view never launches a new job. Aerial actions stay unmodelled. Old observations produce explicit insufficient evidence. Neither presentation supplies completion probabilities, a universal best action or a correct-choice score.

Recorded mode uses source=recorded_agents with status=reviewed or insufficient_evidence, and a required recording object containing the snapshot ID, assessment/pressure hashes, source capture hash, saved UTC timestamp, timestamp basis, capture method and notes. explanation.source has the same distinct value. Captured elapsed_s describes the original run, not replay latency. The original trace and accepted draft are retained; the UI labels the model/date and any known wording issue. Loading requires current snapshot, complete assessment and pressure hashes to match, accepted trace structure and current draft guards. Missing, malformed or mismatched captures produce deterministic fallback with reason=recording_unavailable and no captured prose. Captures remain choice-gated and outcome-independent. No raw fixture path is served.
Recordings are loaded and validated once when the server starts. Restart it after changing code or exporting new captures; there is no file watcher or hot reload. The browser smoke compares served recorded text/trace/provenance with the current on-disk fixture, so a stale process cache cannot count as refresh verification.

Reveal plays the recorded short pass regardless of the selected option. The recap states when it differs from the fan's choice. Revisiting the frozen decision retains the first assessment, and the recorded continuation can be replayed. New attempt resets the session and unsaved comprehension answers.

The optional comprehension form explains the difference between outcome and evidence and the limited meaning of a timing margin. It does not grade football choices, save responses, send analytics or establish human learning. The separate [pilot task](../tasks/02-fan-understanding.md) defines how to gather actual fan evidence.

## Reproducible checks

~~~powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_api.py -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
node --check web/app.js
node tools/browser_smoke.mjs
~~~

The browser check requires the API to be running, Node 22+ and an installed Chrome or Edge. It uses built-in browser debugging with an isolated temporary profile and writes screenshots to ignored local-artifacts. An alternate local URL and Chromium executable path can be passed as its first and second arguments. It checks the actual rendered desktop/mobile workflow and network responses; it does not simulate fan participants.

## Scenario and agent operations

GET /api/scenarios returns the three authored scenario IDs, labels and titles; GET /health reports local process health. These endpoints reveal no continuation. Scenario 2's preparation_delay_s requires point-arrival-v0.2. Scenario 3 supplies uncertainty_regions on an insufficient-evidence assessment; their radius is an illustrative maximum-speed region, not a probability or route ranking.

The shared local inference gate admits one generation job at a time. Sessions remain usable while queued. GET evidence polls only status and cached interpretation. The model sees neither the fan choice nor the revealed result. Provider/MCP/validation failures expose a sanitized reason class and retain the deterministic explanation. See [agents](AGENTS_AND_MCP.md) and [operations](OPERATIONS.md) for configuration and limits.

For real local-agent verification, start the model-enabled API and run:

~~~powershell
.\.venv\Scripts\python.exe tools/agent_smoke.py --base-url http://127.0.0.1:8000 --require-reviewed
~~~

It records the actual accepted/fallback outcomes and verifies schemas and assessment immutability across polling/reveal. The optional --require-reviewed fails if any scenario remains deterministic. It does not fabricate a successful agent run. Observed evidence is saved in ignored local-artifacts/runtime-*.json.
Use --scenario-id tempting-short-pass to capture just that scenario and --require-fresh with a new live API process to reject an already cached response. Each completed observed result, including fallback, is also preserved under local-artifacts/agent-captures with a unique name, content hash, observed running/cache status and current working-tree source hashes. These hashes document files at capture time, not attest which code a pre-existing server loaded. Restart after code changes. Cached probes are not fresh generation attempts; showcase selection counts must be disclosed separately.

The handoff disclosure shows accepted claim text and its evidence/principle identifiers only after review. A rejected draft is labelled draft not approved; a provider failure is labelled local agents unavailable. Neither path publishes the unchecked analyst narrative. Principle citations remain original drafts, not coach endorsement.
