# Agent workflow and MCP

Implemented locally in keepers_boots/mcp_server.py, agents.py and claims.py. The [active task](../tasks/01-keeper-loop.md) records runtime evidence and limits. Nothing is deployed to Azure.

## Responsibilities and handoff

The host reads frozen state, comparison, pressure and selected original principles through MCP. The analyst writes evidence-linked interpretations, fan/analyst variants, missing information and a null ranking. Numeric facts stay in code-rendered evidence. The generation schema binds snapshot_id and citation choices to the frozen packet; unknown IDs are still checked after generation.

Code checks snapshot identity, references, numeric rendering and explicit scope rules. A separate reviewer receives a fresh MCP packet and proposed draft, without the analyst conversation. Its prompt asks it to check semantic implications such as equating positive sampled margins with safe possession or excluding aerial clearance because its contest is unmodelled. It returns accept, revise or insufficient_evidence and claim-level reasons. This is a judgment-based layer using the same model, not demonstrated error correction; known misses are preserved in the calibration data.

One analyst repair and second review are permitted. Failure retains deterministic text and evidence. Interpretation is cached once per scenario per process. Audience switches and new attempts reuse it; the fan's selected action does not enter its prompt. Choice highlighting and recorded recap are deterministic.

MCP calls are chosen by the host workflow, rather than an autonomous model tool planner. Models interpret/review; code controls observation access. Reviewer acceptance is not proof of truth, and text matching cannot establish semantic correctness.

## Five read-only tools

| Tool | Input | Bound |
|---|---|---|
| get_decision_state | snapshot_id | Allowlisted frozen snapshot |
| analyse_pass_option | snapshot_id, option_id | Fixed option evidence or unsupported/stale status |
| analyse_pressure | snapshot_id | Point-arrival/release timing; abstains on stale information |
| compare_options | snapshot_id, option_ids | Ground-route evidence and code-computed signed timing relations; no overall ranking |
| get_principle | principle_id | Original draft text and review status; no private KB retrieval |

The stdio FastMCP server publishes input and structured object output schemas. Domain checks reject unknown identifiers and duplicate option requests. Its backend accepts only DecisionSnapshot objects, with no world, continuation, arbitrary file, URL or execution tools. Run `python -m keepers_boots.mcp_server` in the project environment; stdout is reserved for protocol messages.

## Claim and failure contracts

Pydantic Draft contains snapshot_id, one to five claims (claim_id, evidence_ids, principle_ids, text), fan, analyst, missing_information and ranking=null. Review contains status, rejected_claim_ids and reasons. Unknown fields are forbidden. The generation schema permits at most two claims (one on stale evidence), binds hash/citations, and restricts prose to bounded JSON-safe text without numeric measurements. Validated player/principle identifiers are permitted. See keepers_boots/claims.py for exact limits.

On stale observations, a draft must identify missing information. Neither agent receives outcomes or hidden movement. Rejected, malformed, unavailable or timed-out output is never displayed as reviewed. No completion probabilities, ideal-player scores or correct-choice ratings are supported. The recorded recap cannot rewrite the numeric assessment.

## Dependency choices

Pinned on 2026-10-10: agent-framework-core 1.21.0, agent-framework-openai 1.16.0, mcp 1.30.0. requirements.txt pins transitive packages; pywin32 is Windows-only. MCP v1 is used because this Agent Framework release requires mcp below v2. Calls were checked against [Agent Framework structured outputs](https://learn.microsoft.com/en-us/agent-framework/agents/structured-outputs) and the [official MCP v1 SDK](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x).

The Microsoft OpenAI adapter connects to an explicitly supplied anonymous loopback endpoint. Its protocol name does not imply a cloud call. Defaults mirror PythonProject2's source configuration: Gemma via llama.cpp at port 8088. A local Qwen server can be selected explicitly. Cloud URLs, URL credentials, queries and cloud model tags are rejected; this connector loads no environment file or private project configuration.

Agent Framework is the Microsoft component in the A$0 route. Foundry inference, Azure hosting and Copilot are not implemented. Do not claim Foundry-category eligibility or guaranteed judging credit.

## Evaluation remaining

Injected tests demonstrate semantic rejection and repair without changing evidence: orchestration proof, not live quality. Real stdio tests exercise all five tools. Record actual model results separately, including fallback. Compare the same first analyst draft plus identical guards against its reviewer/repair branch on new, preregistered held-out variants and separately labelled corrupted claims. Freeze prompts/guards before testing; the three product scenarios and known failure examples are calibration and cannot establish benefit. Follow [the comparison task](../tasks/04-reviewer-comparison.md). Fan appeal and realism need the separate [pilot](../tasks/02-fan-understanding.md) and independent scenario review.

## Local inference observations

The existing Gemma server was tested with one slot, an 8192-token context, RAM prompt caching/checkpoints disabled and a 128-token reasoning budget. These are local test settings, not a hardware-independent recommendation. The original project's launcher is unchanged.

Decoder constraints need JSON-safe, bounded prose patterns. The installed llama.cpp converter handles a pattern before separate string-length keywords; patterns therefore carry their own repetition bounds. The exact public [b9037 converter source](https://github.com/ggml-org/llama.cpp/blob/b9037/common/json-schema-to-grammar.cpp) and [server documentation](https://github.com/ggml-org/llama.cpp/blob/b9037/tools/server/README.md) were inspected during diagnosis. Application validation remains authoritative if a backend ignores constraints.

Early live runs exposed timeouts, truncated output and false reviewer rejections. A deliberately scripted diagnostic then checked supported timing, unsupported buildup and useful abstention. Those checks guided prompt calibration and are not a held-out evaluation; initial calibration also falsely accepted the buildup claim before correction. Preserve these limits when reporting reviewer value. The active task records the final natural-draft runtime outcomes.

The host provides deterministic comparison facts as additional citation targets. An observed agent reversal of a signed margin motivated this boundary: facts include ordering, not just individual numbers. The UI renders these comparisons directly from code. Reviewer approval alone remains insufficient to establish factual correctness.

A further guard requires explicit release-before-pressure claims to cite pressure:arrival. The observed missing-citation draft was repaired once in the final live run. Numeric facts and signed comparison direction remain code-owned; other qualitative interpretation still needs held-out evaluation.

## Recorded demonstration

--agents recorded loads the three [captured results](../data/agent-recordings/README.md), rechecks frozen evidence identity and current guards, and displays source=recorded_agents. It calls neither the agents nor MCP. Fan/analyst text, accepted claims and the original trace remain unchanged. Scenario 1 was refreshed after a known wording error; the current capture contains validator and reviewer acceptance without repair. Its prior rejection/repair came from code, not the reviewer, and remains in Git history/local audit records. Trace/provenance checks prevent accidental incompatible reuse, not establish cryptographic proof that a model ran. Missing or changed evidence fails to an explicitly labelled deterministic fallback. Live --agents local remains the execution route.

The refreshed first draft also exposed a false joint-positive-margin claim and incomplete prose despite reviewer acceptance. Those failures were not exported. Focused guards now reject the observed keeper-arrival phrase, joint margin polarity contradicted by an option's entire range, and unfinished fan/analyst/claim sentences. These are narrow regression boundaries, not general semantic validation or held-out evidence of reviewer benefit.
