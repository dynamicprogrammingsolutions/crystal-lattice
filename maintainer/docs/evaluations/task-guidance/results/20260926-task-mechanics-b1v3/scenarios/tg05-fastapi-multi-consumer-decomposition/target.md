# Reviewed target — tg05-fastapi-multi-consumer-decomposition

**FastAPI multi-consumer query decomposition** — Recognize valid service, SDK, and application boundaries without fragmenting each component into phases.

Category: decomposition · Project: `FastAPI notes multi-consumer fixture` · Acceptable partition sizes: 3, 4, 5

**Approved outcomes**

- QUERY-1: One approved public query contract covers filtering, sorting, pagination, validation, and compatibility.
- QUERY-2: The FastAPI service implements the contract through production HTTP and real storage behavior.
- QUERY-3: The reusable Python client exposes the capability while preserving current calls.
- QUERY-4: The CLI exposes the capability and proves the CLI-to-client-to-service path.
- QUERY-5: Each independently delivered public surface has accurate current documentation.

**Coherent deliverables**

- **QUERY-D1** — Approve the shared query contract
  A stable public contract independently unblocks multiple owners and consumers.
  - Outcomes: QUERY-1
- **QUERY-D2** — Deliver the FastAPI service capability (depends on QUERY-D1)
  The public API is independently usable by external and first-party consumers.
  - Outcomes: QUERY-2, QUERY-5
- **QUERY-D3** — Deliver the reusable Python client capability (depends on QUERY-D1)
  The client is an independently published reusable package with its own compatibility boundary.
  - Outcomes: QUERY-3, QUERY-5
- **QUERY-D4** — Deliver the CLI workflow and production integration (depends on QUERY-D2, QUERY-D3)
  The CLI is a separately accepted application and owns the complete first-party integration path.
  - Outcomes: QUERY-4, QUERY-5

**Important crossings**

- HTTP route to real storage.
- Python client transport to production API.
- CLI through the actual client package and HTTP service.

**Acceptable alternatives**

- Keep the short contract in the parent when one clear maintained owner remains.
- Combine service and client only when release, ownership, and compatibility are not independent.
- Use a separate integration child only when production integration is itself independently maintained.

**Fragmentation examples**

- Service model, query, route, tests, and docs as separate tasks.
- Client transport, models, errors, tests, and docs as separate tasks.
- CLI parsing, output, tests, and documentation as separate tasks.
- A generic final review or integration-test phase.

**Overpacking examples**

- One child for service, reusable client, and CLI hides independent package ownership and compatibility.

**Open questions**

- Exact filter grammar and sort fields require public-contract approval.

**Handoff expectations**

- fresh agent plan: A fresh agent recognizes valid component boundaries while keeping each component's work, tests, and docs together.
- omit plan: Preserve package facts, public questions, ownership boundaries, and crossings without the four-component task partition.
- retain plan: Preserve contract, ownership, compatibility, parallelism, and final integration dependencies.
