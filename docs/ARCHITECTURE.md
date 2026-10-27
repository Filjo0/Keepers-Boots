# Architecture

## Status
The three-scenario generator, frozen geometry, [browser/API loop](API.md), structured MCP server and Microsoft analyst/reviewer workflow are implemented locally. Cloud deployment remains deferred under the A$0 budget. Runtime evidence and remaining limits live in the [active task](../tasks/01-keeper-loop.md).

## Chosen approach
- Python 3.12 for synthetic data, analysis, API, MCP and agent workflow.
- A small browser application with SVG or canvas pitch graphics. Start with plain HTML/CSS/JavaScript; no 3D or VR dependency.
- One local Python web/API process; a portable container definition is prepared, not built.
- Microsoft Agent Framework coordinates analyst/reviewer calls against an existing anonymous local model endpoint; Foundry hosting is deferred.
- MCP exposes bounded, read-only geometry/evidence tools.
- Static scenario fixtures first; a database, Fabric, Event Hubs, AKS and vector search are not needed for the initial demo.
- Record SDK/model choices and pin dependencies when those integrations are implemented.

[Agent Framework documentation](https://learn.microsoft.com/en-us/agent-framework/overview/) describes workflows linking functions and agents and supports MCP tools. [Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/overview) can host containerised HTTP applications. Agent Framework is implemented locally; Container Apps is a future hosting option, not deployed evidence.

## Information flow

~~~mermaid
flowchart LR
    G[Scripted synthetic generator] --> R[Replay frames and events]
    G --> O[Available observations]
    O --> S[Frozen decision snapshot]
    S --> D[Deterministic geometry]
    D --> M[Read-only MCP tools]
    M --> A[Analyst]
    A --> V[Reviewer and fact checks]
    V --> U[Fan or analyst view]
    R --> P[Pitch replay]
    P --> C[Fan choice]
    C --> X[Reveal gate]
    X --> F[Continuation and recap]
~~~

## Hard boundaries
1. World truth includes positions and future events; it is for replay/generation.
2. Available observations are a separate record. A position can be unknown or stale.
3. A decision snapshot includes only selected observation fields and permitted context.
4. All pre-decision tools and agents receive the snapshot/evidence, never the full fixture.
5. The recorded continuation is unlocked only after choice/reveal.
6. Outcome commentary must distinguish pre-decision assessment from later facts.

The browser must not preload the continuation or original decision before the choice if the product claims concealed outcomes. Server endpoints enforce reveal state; hiding an HTML element is insufficient.

## Immutable first assessment
The current foundation stores canonical JSON in a frozen object and verifies its SHA-256 digest before analysis. Reading returns a new object. The digest covers permitted input only, so changing future events does not change it.
The local API retains the first snapshot and serialized assessment across retries, view changes and reveal within each bounded session. Hosted persistence remains a later concern.

## Two agents with a reason to collaborate
The analyst proposes an interpretation. The reviewer independently challenges scope, assumptions and evidence, returning structured feedback. Code validates numbers and references. At most one repair is proposed initially; failure produces an evidence-only explanation. Measure the reviewer against a single-agent baseline before claiming a demonstrated quality benefit.

## Public access
The first hosted demo serves synthetic fixtures. Model calls have bounded input, call count, time and cost. Do not expose cloud administration, file-system tools, arbitrary URLs or executable code through the public MCP/API surface.
