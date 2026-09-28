# Session — tg05-fastapi-multi-consumer-decomposition · file-fidelity-assessment-glm-max-s0 · glm max

- Run: `20260928T194521.467902Z-task-guidance-file-fidelity-tg05-fastapi-multi-consumer-decomposition-glm-max-s0-e8f3256e`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-7f182e48e360.md) — captured (original SHA-256 `934e88a61ea34e7f…`)
- Config: [glm-assessor-max](../../../../../../shared/configs/glm-assessor-max.json)
- Activity: 3 messages · 0 tool calls · 0 tool results
- Usage: unknown — saved session contains no provider usage metadata

## Transcript

**User**

Assess the task files one agent produced for a fixed scenario, together
with that agent's final conversation response. Judge whether the files
carry what a continuing agent and a human reviewer need: the decided
design, the conversation's durable context, content in the right
sections, a plan justified by planning that actually happened, and
acceptance evidence that fits the work's kind.

Grade these dimensions:

- `plan_design_completeness`: a reader of the implementation plan alone
  can reconstruct the decided design — component responsibilities,
  interfaces or data flow, compatibility and dependency states, material
  decisions, and how the requirements are verified. An ordered list of
  work steps without the design behind it is `poor`; covering some
  design elements is `partial`.
- `durable_context_preservation`: every approved outcome, material
  decision, verified fact with its source, and verification approach the
  conversation established appears in the task files — compressed, not
  dropped. Use `not checked here` only when the conversation established
  nothing durable.
- `section_appropriateness`: content sits where a continuing agent looks
  for it — outcomes and constraints in requirements, rationale and
  learned facts in supporting details, direction in the implementation
  plan, unresolved items in questions and decisions.
- `plan_justification`: the implementation plan reflects planning that
  actually happened. `justified` when the plan restates or organizes the
  conversation's planning; `not_applicable` when no plan section exists;
  `fabricated` when the plan asserts design detail the conversation
  never established.
- `task_kind_fit`: the file uses the sections the work needs and states
  acceptance evidence appropriate to the work's kind — tests for code,
  review acceptance for documentation, rollback and verification for
  operations, brief or style acceptance for content, recorded decisions
  for tracking work. `forced` when inapplicable sections are filled
  mechanically; `missing` when the work's own acceptance evidence is
  absent.

Every grade carries findings: concrete `{where, quote, why}` items
backing it. A non-top grade with empty findings is invalid. Then hunt
for mistakes explicitly — dropped facts, invented decisions or scope,
content a continuing agent would look for in the wrong place, missing
acceptance evidence — and list each as `{where, quote, why}` in
`mistakes`. Grades stay completeness judgments; the mistake hunt is
your search strategy, not a grade.

Do not reward verbosity or formatting of its own. Do not penalize
brevity that loses nothing. The target excerpt and the natural user
request define what is material.

Return JSON only:

{
  "schema_version": 1,
  "scenario_id": "tg05-fastapi-multi-consumer-decomposition",
  "assessment": {
    "dimensions": {
      "plan_design_completeness": {
        "grade": "complete|partial|poor",
        "findings": [{"where": "...", "quote": "...", "why": "..."}]
      },
      "durable_context_preservation": {"grade": "...", "findings": []},
      "section_appropriateness": {"grade": "...", "findings": []},
      "plan_justification": {
        "grade": "justified|not_applicable|fabricated",
        "findings": []
      },
      "task_kind_fit": {"grade": "fits|forced|missing", "findings": []}
    },
    "mistakes": [{"where": "...", "quote": "...", "why": "..."}],
    "summary": "concise evidence-based interpretation"
  }
}

Reviewed target excerpt:

# FastAPI multi-consumer query decomposition

Recognize valid service, SDK, and application boundaries without fragmenting each component into phases.

Category: decomposition

Approved outcomes:

- QUERY-1: One approved public query contract covers filtering, sorting, pagination, validation, and compatibility.
- QUERY-2: The FastAPI service implements the contract through production HTTP and real storage behavior.
- QUERY-3: The reusable Python client exposes the capability while preserving current calls.
- QUERY-4: The CLI exposes the capability and proves the CLI-to-client-to-service path.
- QUERY-5: Each independently delivered public surface has accurate current documentation.

Open questions:

- Exact filter grammar and sort fields require public-contract approval.

Acceptable alternatives:

- Keep the short contract in the parent when one clear maintained owner remains.
- Combine service and client only when release, ownership, and compatibility are not independent.
- Use a separate integration child only when production integration is itself independently maintained.

Natural user request:

Add one supported notes-query capability across the public API, reusable Python client, and CLI. It must support bounded pagination, stable sorting, and optional text filtering while preserving current unparameterized API and client behavior. The public contract must be stable before consumers rely on it, and the CLI must prove the production client-to-service path. Plan the work and create the appropriate task structure without implementing it.

The producer's final conversation response (the durable-context source
the files must preserve):

````markdown
Task structure created — planning only, nothing implemented. Four files under `tasks/20260926-notes-query-capability/`, all plans in `Draft`:

```
000-main.md                                  overall requirements + coordination plan
010-api-collection-query.md                  public HTTP contract (first)
020-client-query-parameters.md               depends on 010
030-cli-query-flags-and-production-path.md   depends on 010 + 020
```

## Why main + 3 subtasks

The three boundaries are independently maintained deliverables (service in `src/app`, package `notes-client`, app `notes-cli`), each with its own README, tests, and compatibility state — exactly what `AGENTS.md` says may justify separate deliverables. The contract-first requirement makes the order structural: the client and CLI children declare `Depends On: 010`, so no execution order is unsafe. Tests and docs stay with the child that owns each outcome.

## Proposed v1 contract (needs your approval — D1–D9 in the main plan)

- **Extend `GET /notes/` in place**, response stays a **bare JSON array** (no envelope, no total count — page end detected by a short page). Unparameterized calls return the full collection exactly as today.
- **Pagination**: `limit` (1..100, server-enforced cap; absent = full collection) + `offset`; violations → 422.
- **Sorting**: one `sort` param (`id|title|description`, `-` prefix for descending); `id` ascending always appended as tie-break; default `id` ascending — making today's incidental order contractual.
- **Filtering**: one `q` param, case-insensitive literal substring on `title` (narrower v1 semantics; widening later would change results for existing consumers).
- **Client**: optional keyword-only params on the existing `list_notes()`; no-arg call byte-identical.
- **CLI**: `--limit`, `--offset`, `--sort`, `--filter` on `notes list`; output format unchanged.

## Acceptance evidence

- 010: HTTP-boundary integration tests (real app + SQLite): windows, bounds, sort tie stability, literal `%`/`_` matching, 422s, unparameterized regression; existing tests pass unmodified; OpenAPI cross-check.
- 020: captured-request component tests for serialization + unchanged no-arg request.
- 030: **the named decisive check** — real uvicorn server, notes seeded via public POST, real `NotesClient.from_environment()` via `NOTES_API_URL`, real `main([...])`, asserting parameterized stdout and the unparameterized full listing. Per-side mocked tests are supporting evidence only.

## Notable risks/decisions to confirm

- **D7**: the decisive check adds `uvicorn` as a test dependency (real socket = production path); ASGI-transport fallback exists but simulates the socket.
- **D8**: a short spec under `docs/development/` (the index currently notes its absence) as the reviewable contract artifact.
- **Environment**: no virtualenv or test deps exist yet; execution starts by establishing one. Also flagged: `notes.db` cwd side effect, an unverified lifespan assumption in the existing `TestClient` fixture, and the undeclared `notes-cli` → `notes-client` dependency (D9).
- **Exclusions**: no cursor pagination, no envelope/total, no new endpoints, no schema changes, no client auto-pagination iterator, no required version bumps.

Approval of the plan freezes D1–D9 as the v1 public contract (afterward, changes become breaking). **Execution waits for your approval** — tell me if you want any contract value changed (e.g., page cap, filter scope, flag names, spec page), or approve as-is.
````

The produced task files:

### tasks/20260926-notes-query-capability/000-main.md

````markdown
# Notes query capability across the public API, Python client, and CLI

Add one supported notes-collection query capability end to end: the public
HTTP API gains bounded pagination, stable sorting, and optional text filtering
on the notes collection; the reusable `notes_client` package and the `notes`
CLI expose the same capability, each preserving its current unparameterized
behavior. The public contract is defined and frozen before the client and CLI
rely on it, and one named end-to-end check proves the real CLI → real client →
real running service path.

## Requirements checklist

- [ ] R1 — The notes collection HTTP operation (`GET /notes/`) supports
      bounded pagination (server-enforced maximum page size), stable sorting
      (deterministic total order), and optional text filtering, per an
      approved written contract.
- [ ] R2 — Unparameterized API behavior is preserved: `GET /notes/` with no
      query parameters returns the full collection as a bare JSON array
      exactly as today, and existing service tests keep passing unmodified.
- [ ] R3 — `notes_client.NotesClient.list_notes()` accepts the query
      parameters and forwards them to the service; the no-argument call sends
      the same request as today and returns the same parsed JSON list.
- [ ] R4 — `notes list` exposes the capability through CLI flags and forwards
      them through the client; the no-flag invocation and its `{id}: {title}`
      output format are unchanged.
- [ ] R5 — The public query contract (parameters, defaults, bounds, ordering,
      response shape, error semantics) is recorded and frozen before the
      client and CLI are implemented against it; task order enforces
      API-contract work first.
- [ ] R6 — One named decisive check exercises the production client-to-service
      path end to end: real CLI invocation, real `NotesClient`, real HTTP
      server running the real app. Per-side mocked tests alone do not satisfy
      this.
- [ ] R7 — Maintained documentation is updated in the same reviewed changes as
      the behavior it describes: service-facing docs (root `README.md`, and
      the notes-query specification if approved),
      `packages/notes_client/README.md`, and `apps/notes_cli/README.md`.

## Subtasks

- [ ] tasks/20260926-notes-query-capability/010-api-collection-query.md
- [ ] tasks/20260926-notes-query-capability/020-client-query-parameters.md
- [ ] tasks/20260926-notes-query-capability/030-cli-query-flags-and-production-path.md

## Decisions pending plan approval

Contract-level choices below are presented with tradeoffs in
`## Execution plan` → `### Implementation decisions and open questions`.
Approving the plan freezes them as the v1 public contract; later changes
become breaking for consumers.

- D1 — Extend `GET /notes/` in place; keep the bare JSON array response shape.
- D2 — `limit`/`offset` pagination with a server-enforced maximum page size;
      absent `limit` means full collection (required for R2).
- D3 — Single `sort` parameter (`field` or `-field`); `id` ascending always
      appended as tie-break; default order `id` ascending.
- D4 — Single `q` text filter; case-insensitive literal substring match on
      `title` only.
- D5 — Extend the existing `list_notes()` with optional keyword-only
      parameters instead of adding a new client method.
- D6 — CLI flags `--limit`, `--offset`, `--sort`, `--filter` on the `list`
      subparser (`--filter` carries the contract's `q` value).
- D7 — The end-to-end check runs a real uvicorn server on an ephemeral local
      port (adds `uvicorn` as a test dependency of the CLI app) rather than an
      in-process ASGI transport.
- D8 — Record the contract in a short specification under `docs/development/`
      and update `docs/development/index.md`, in addition to README updates.
- D9 — Record the implicit `notes-cli` → `notes-client` dependency in the CLI
      README (and optionally in `pyproject.toml`) instead of leaving it
      undocumented.

No unresolved requirement questions: the request fixes the capability, the
three compatibility-preserving boundaries, the contract-first ordering, and
the production-path proof. Everything above is a design decision awaiting
approval.

## Supporting facts

- Service: FastAPI app with router prefix `/notes` (`src/app/main.py`);
  storage is SQLite via `databases`/SQLAlchemy, table
  `notes {id, title, description}` (`src/app/db.py`, hardcoded
  `sqlite:///./notes.db`).
- Today the collection route returns `crud.get_all()` — a bare list of every
  note (`src/app/api/notes.py:8`, `src/app/api/crud.py:4`); there are no query
  parameters, no ordering contract, and no pagination.
- Client: `NotesClient(transport)` with `from_environment()` reading
  `NOTES_API_URL` (default `http://127.0.0.1:8000`); `list_notes()` does
  `GET /notes/` and returns `.json()`
  (`packages/notes_client/notes_client/client.py`).
- CLI: `notes list` prints `{id}: {title}` per note through the client
  (`apps/notes_cli/cli.py`); `apps/notes_cli/pyproject.toml` declares no
  dependency on `notes-client` despite importing it (D9).
- Current tests are per-boundary and shallow: service tests assert only list
  shape and one POST route; the client test uses a fake transport; the CLI
  test uses a fake client. No test today crosses CLI → client → service,
  which is why R6 requires a new named decisive check.
- `docs/development/index.md` states "No notes-query specification exists."
  Root `README.md` describes the collection route as returning every note as
  a JSON array. Both are maintained touchpoints for this change.
- No virtualenv or test dependencies exist in the workspace: runtime deps
  (`fastapi`, `databases`, `sqlalchemy`, `httpx`) are not installed, `pytest`
  is not declared in any pyproject, and `.gitignore` does not cover
  `notes.db`. Execution must first establish a test environment and
  invocation paths (service tests import `app` from `src/`; client/CLI tests
  import `notes_client`).
- Not yet verified (assumption to check during execution): whether the
  installed Starlette version runs the app lifespan for the existing
  `TestClient(app)` fixture pattern; if not, the fixture must enter the
  client as a context manager so `database.connect()` runs. The real-server
  end-to-end check runs lifespan regardless.

## Execution plan

Status: Draft

### Design

One supported query operation, extended in place at each of the three
boundaries. The service owns the contract; the client serializes it; the CLI
exposes it and owns the production-path proof.

Proposed v1 contract for `GET /notes/` (all parameters optional; violations
rejected with 422 by query validation):

| Parameter | Range / values | Default | Semantics |
| --------- | -------------- | ------- | --------- |
| `limit`   | integer 1..100 | absent  | Page size. Absent → full collection (preserves R2). Outside 1..100 → 422. This server-side cap is the pagination bound. |
| `offset`  | integer ≥ 0    | 0       | Rows skipped after filtering and sorting. |
| `sort`    | `id`, `title`, `description`, each optionally `-`-prefixed | `id` ascending | Primary sort field and direction; `id` ascending is always appended as final tie-break, so the total order is deterministic. Unknown value → 422. |
| `q`       | any string     | absent  | Case-insensitive literal substring match on `title`; `%` and `_` are matched literally. |

Response body is unchanged: a bare JSON array of `{id, title, description}`
objects. The unparameterized response is the full collection in `id` order —
in practice identical to today's SQLite insertion order, but now contractual
rather than incidental.

Component responsibilities and compatibility states:
- Service (010) owns the contract and its validation: FastAPI `Query`
  constraints on the collection handler; `crud.get_all` gains optional
  parameters building the SQLAlchemy select (escaped `ilike` filter,
  `order_by` with `id` tie-break, `offset`, `limit`). Absent parameters leave
  the query unchanged.
- Client (020) forwards optional keyword-only parameters as query-string
  parameters, omitting unset ones; no client-side validation; unchanged
  return type.
- CLI (030) parses flags and maps them 1:1 to client parameters, keeps the
  existing output format, and owns the decisive end-to-end check.
- Each boundary keeps its unparameterized behavior (same request, same
  response, same output); new behavior is reachable only through the newly
  added optional parameters/flags. Dependencies enforce 010 → 020 → 030.

Interpretation note: "stable sorting" means a deterministic total order
(field plus `id` tie-break), not snapshot stability of offset pagination
under concurrent writes; the latter is out of scope.

Verification strategy:
- 010: integration tests through the real FastAPI app and SQLite at the HTTP
  boundary (existing `src/tests` pattern) — pagination windows and bounds,
  sort directions and tie stability, filter matching incl. literal `%`/`_`,
  combined parameters, 422s, and an unparameterized regression.
- 020: component tests with a request-capturing fake transport — parameter
  serialization and an unparameterized call that sends no query string.
- 030: CLI unit test (flags → client arguments, output format) plus the named
  decisive check — a real uvicorn server serving `app.main`, notes seeded via
  the public POST route, `NOTES_API_URL` set, real
  `NotesClient.from_environment()`, real `main([...])` invocation, asserting
  a parameterized query's stdout and the unparameterized full listing through
  the same path.
- All three existing suites pass unmodified.

### Implementation decisions and open questions

- D1 (route and response shape) — extend `GET /notes/` in place and keep the
  bare array. Alternatives rejected: an envelope would break the current
  shape for unparameterized consumers or make the shape depend on which
  parameters are sent; a separate `/notes/query` route would fragment "one
  capability" into two collection operations. Consequence: no total-count
  field; consumers detect page end by receiving a short page.
- D2 (pagination) — `limit`/`offset` with a server-enforced cap of 100.
  Absent `limit` means the full collection; a default page size would change
  unparameterized behavior and violate R2. Out-of-range values → 422. The
  cap (100) is arbitrary but fixed in the contract; change it before
  approval, not after consumers rely on it.
- D3 (sorting) — one `sort` parameter, `field` or `-field`, over the three
  existing columns; `id` ascending always appended as tie-break; default `id`
  ascending. A separate `order` parameter was rejected: one parameter carries
  the same information.
- D4 (filtering) — one `q` parameter, case-insensitive literal substring
  match on `title` only. Matching `description` too would be more useful but
  widening the match later changes results for existing consumers, so the
  narrower, easier-to-document semantics are recommended for v1.
- D5 (client surface) — optional keyword-only parameters on the existing
  `list_notes()`. A separate `query_notes()` method was rejected: two methods
  for one collection operation invite divergence, and the no-arg call must
  stay unchanged.
- D6 (CLI surface) — flags `--limit`, `--offset`, `--sort`, `--filter` on the
  existing `list` subparser; `--filter` maps to the contract's `q`. Flag
  forwarding only; the CLI adds no semantics of its own.
- D7 (end-to-end harness) — real uvicorn server on an ephemeral `127.0.0.1`
  port in the decisive check, added as a test dependency of the CLI app; the
  socket-level server is what makes this the production path (lifespan, real
  HTTP round trips, `NOTES_API_URL` construction). An in-process
  `httpx.ASGITransport` fallback exists but simulates the socket; not
  recommended for R6.
- D8 (contract artifact) — a short specification under `docs/development/`
  (updating `index.md`'s "no notes-query specification exists" note) in
  addition to README updates. The spec is the reviewed artifact that makes
  the contract stable and inspectable before consumers depend on it; the
  generated OpenAPI schema remains the machine-readable contract, changed
  through its maintained source (the route definitions).
- D9 (CLI packaging gap) — record the `notes-cli` → `notes-client` dependency
  in the CLI README; optionally also declare it in `pyproject.toml`. Left as
  a decision because the workspace has no package index, so an added install
  requirement may not resolve; the README note is safe either way.
- Minor version bumps (`notes-client`, `notes-cli` 0.1.0 → 0.2.0) are
  optional since both changes are backward-compatible; not required by this
  task.

Open question: none at requirement level. Approval of this plan approves
D1–D9 as the frozen v1 contract.

### Documentation

- Root `README.md` (service audience): the collection route description
  gains the query parameters; owned by 010, same change as the API code.
- Notes-query specification under `docs/development/` plus `index.md` update
  (if D8 approved); owned by 010 — the service owns the contract.
- `packages/notes_client/README.md` (Python integrators): parameter
  documentation; owned by 020.
- `apps/notes_cli/README.md` (end users): flag documentation and the client
  dependency note (D9); owned by 030.
- No new documentation structure beyond the single spec page; no placeholder
  pages.

### Task checklist

- [ ] 010 — API collection query implemented, contract locked with tests and
      documentation
      (tasks/20260926-notes-query-capability/010-api-collection-query.md)
- [ ] 020 — Client query parameters implemented with regression tests and
      docs, after 010
      (tasks/20260926-notes-query-capability/020-client-query-parameters.md)
- [ ] 030 — CLI query flags plus the decisive production-path end-to-end
      check and docs, after 010 and 020
      (tasks/20260926-notes-query-capability/030-cli-query-flags-and-production-path.md)

### Requirement verification

- R1 → 010 integration tests at the HTTP boundary (real app + SQLite):
  windowing, bounds, ordering, filtering, 422s.
- R2 → existing `src/tests` pass unmodified plus a new unparameterized
  regression test asserting the bare-array full collection in `id` order.
- R3 → 020 captured-request component tests (forwarded parameters;
  no-arg call sends no query string) plus the 030 end-to-end check.
- R4 → 030 CLI unit test (flags → client arguments; unchanged output format)
  plus the end-to-end check.
- R5 → process constraint made structural: 020 and 030 declare
  `Depends On: 010`; the contract is written down (README/spec) in 010's
  reviewed change and frozen by plan approval before 020/030 execute.
- R6 → the named decisive check in 030: real uvicorn service + real
  `NotesClient` via `NOTES_API_URL` + real CLI `main()` invocation, asserting
  both a parameterized query and the unparameterized full listing through
  stdout. The client component test and the service route tests are
  supporting evidence only and do not substitute for this.
- R7 → documentation diffs reviewed with their owning code changes
  (010/020/030).

### Additional implementation verification

- 010 asserts the generated OpenAPI schema (read via the maintained route
  definitions) lists the new parameters — a cheap contract cross-check.
- Watch `notes.db` side effects: the service writes `./notes.db` relative to
  the working directory and it is not gitignored; run verification from an
  isolated working directory so execution leaves no stray database file in
  the repository.
- None beyond the above; the per-child plans carry the focused evidence.
````

### tasks/20260926-notes-query-capability/010-api-collection-query.md

````markdown
# Public API: bounded, sorted, filtered notes collection query

Implement and lock the approved query contract on the notes collection route
(`GET /notes/`): bounded pagination, stable sorting, and optional text
filtering, with unparameterized behavior preserved and the contract recorded
in the maintained service documentation.

Parent Task: tasks/20260926-notes-query-capability/000-main.md
Depends On: none — this is the first subtask; the contract it implements is
approved with the parent plan (decisions D1–D4, D8).

## Requirements checklist

- [ ] `GET /notes/` accepts optional query parameters per the approved
      contract: `limit` (integer 1..100), `offset` (integer ≥ 0), `sort`
      (`id|title|description`, optionally `-`-prefixed for descending), `q`
      (case-insensitive literal substring on `title`).
- [ ] Pagination is bounded by the server: `limit` outside 1..100 is rejected
      with 422; malformed `offset` or unknown `sort` values are rejected with
      422.
- [ ] Results are totally ordered: the requested `sort` field is primary and
      `id` ascending is always appended as tie-break; when `sort` is absent
      the order is `id` ascending.
- [ ] Unparameterized `GET /notes/` returns the full collection as a bare
      JSON array of `{id, title, description}` in `id` order, identical to
      current behavior; the existing service tests pass unmodified.
- [ ] The contract is recorded in the same change: root `README.md` updated
      and (per D8) a notes-query specification under `docs/development/` with
      `index.md` updated.
- [ ] The generated OpenAPI schema reflects the new parameters.

## Execution plan

Status: Draft

Approach:
- Add FastAPI `Query` parameters to `read_all_notes` (`src/app/api/notes.py`):
  `limit` with `ge=1, le=100`, `offset` with `ge=0`, `sort` validated against
  an allow-list of the six permitted values, `q` as a plain optional string.
  Validation failures become contractual 422 responses.
- Extend `crud.get_all` (`src/app/api/crud.py`) to accept the optional
  parameters and build the SQLAlchemy select: optional
  `where(notes.c.title.ilike(...))` with `%`, `_`, and the escape character
  escaped in the user value so matching stays literal; `order_by` on the
  requested column plus `notes.c.id.asc()` as tie-break; `offset`; `limit`.
  Absent parameters leave the query unchanged, preserving current behavior.
- Keep the response a bare list — no envelope, no shape change (D1).

Tests (additions in `src/tests/`, existing tests kept unmodified):
- Seed via the public POST route, then assert:
  - unparameterized: 200, bare array, full collection, `id` ascending;
  - `limit`/`offset` windowing, including limit-absent full result;
  - `limit=101` and `limit=0` → 422; `offset=-1` → 422;
  - `sort=title` and `sort=-title` with duplicate titles → ties broken by
    ascending `id` (stability proof);
  - unknown `sort` value → 422;
  - `q` matches case-insensitively, `%`/`_` match literally, no match → `[]`;
  - combined `q` + `sort` + `limit` + `offset`.
- Verify how the fixture's `TestClient(app)` invocation connects the database
  (lifespan); if the installed Starlette does not run lifespan outside a
  context manager, adjust the fixture to a context-manager client without
  weakening the boundary.
- Assert the generated OpenAPI schema exposes the new parameters.

Environment: execution must first establish a test environment (no
virtualenv or declared test dependencies exist) and run from an isolated
working directory, because the service writes `./notes.db` relative to the
working directory.

### Implementation decisions and open questions

- Contract values (bounds, sort fields, filter semantics, response shape)
  come from parent decisions D1–D4; this subtask implements them and locks
  them with tests. Open questions: none at this scope.
- Local choices resolved here: validation via FastAPI `Query` constraints
  (contractual 422s), literal-match escaping in the CRUD layer, `sort`
  validated as an explicit allow-list.

### Documentation

- Root `README.md`: update the "returns every note as a JSON array"
  description to the current collection behavior plus the query parameters,
  in the same change as the code.
- If D8 approved: add the notes-query specification under `docs/development/`
  describing the frozen contract and update `index.md`; otherwise leave
  `docs/development/` untouched.

### Task checklist

- [ ] Implement query parameters and CRUD selection with stable ordering
- [ ] Add HTTP-boundary integration tests (new behavior and unparameterized regression)
- [ ] Update root `README.md` (and the spec per D8) in the same change
- [ ] Run the service suite; confirm existing tests pass unmodified

### Requirement verification

- Parent R1 → the integration tests listed above (windowing, bounds, sort
  directions with tie stability, literal filter matching, 422s).
- Parent R2 → unmodified existing tests plus the unparameterized regression
  test asserting bare-array shape, full collection, `id` order.
- Parent R5 → the recorded contract (README/spec) reviewed in the same change
  as the implementation; generated OpenAPI asserted to match.
- Parent R7 (service part) → README/spec diff in this change.
````

### tasks/20260926-notes-query-capability/020-client-query-parameters.md

````markdown
# Python client: query parameters on list_notes

Expose the approved query contract on the reusable client so Python consumers
can paginate, sort, and filter the notes collection, while the no-argument
`list_notes()` call keeps its current request and return behavior.

Parent Task: tasks/20260926-notes-query-capability/000-main.md
Depends On: tasks/20260926-notes-query-capability/010-api-collection-query.md
(the contract is implemented and locked before the client relies on it)

## Requirements checklist

- [ ] `NotesClient.list_notes()` accepts optional keyword-only `limit`,
      `offset`, `sort`, and `q`, and forwards provided values as query
      parameters on `GET /notes/` exactly as the approved contract defines
      them — no client-side transformation, defaulting, or validation.
- [ ] The no-argument call issues the same request as today (no query
      parameters) and returns the parsed JSON list — unchanged return type.
- [ ] Component tests prove parameter serialization via a captured request
      and prove the unchanged unparameterized request.
- [ ] `packages/notes_client/README.md` documents the parameters in the same
      change.

## Execution plan

Status: Draft

Approach:
- Extend `list_notes` in
  `packages/notes_client/notes_client/client.py` to
  `list_notes(self, *, limit=None, offset=None, sort=None, q=None)`; build a
  params mapping from the set values and pass it to
  `self.transport.get("/notes/", params=...)` only when non-empty, so the
  unparameterized call stays byte-identical to today's request.
- No validation in the client: the service is the contract boundary; the
  client passes values through (parent decision D5).

Tests (component level, `packages/notes_client/tests/`):
- Fake transport capturing path and query parameters:
  - each parameter appears in the captured query string with the expected
    encoding;
  - unset parameters are omitted;
  - the no-argument call sends no query string (regression) and returns the
    parsed JSON list.
- The existing client test passes unmodified. The full client-to-service
  path is not proven here: it is owned by the named decisive check in 030.

### Implementation decisions and open questions

- D5 (extend `list_notes`; no new method) is approved at the parent level.
  Local choices resolved here: keyword-only parameters to keep the no-arg
  call unambiguous, omission (not empty strings) for unset values.
- Open questions: none.

### Documentation

- `packages/notes_client/README.md`: document the optional parameters and
  note that the no-argument call is unchanged (Python integrator audience).

### Task checklist

- [ ] Add keyword-only query parameters to `list_notes()`
- [ ] Add component tests for serialization and the unparameterized regression
- [ ] Update `packages/notes_client/README.md`
- [ ] Run the client suite

### Requirement verification

- Parent R3 → captured-request component tests prove the forwarded parameters
  and the unchanged no-arg request/return; the production path is proven
  once, end to end, by the decisive check in 030.
- Parent R7 (client part) → README diff in the same change.
````

### tasks/20260926-notes-query-capability/030-cli-query-flags-and-production-path.md

````markdown
# CLI: query flags and the production client-to-service path

Expose the query capability on `notes list` and prove — through the real
production path — that the CLI, the client, and the running service work
together: a real server, the real `NotesClient`, the real `main()`.

Parent Task: tasks/20260926-notes-query-capability/000-main.md
Depends On: tasks/20260926-notes-query-capability/010-api-collection-query.md
and tasks/20260926-notes-query-capability/020-client-query-parameters.md

## Requirements checklist

- [ ] `notes list` supports `--limit`, `--offset`, `--sort`, and `--filter`
      (parent decision D6), forwarding provided values to the client's
      parameters.
- [ ] The no-flag `notes list` invocation and its `{id}: {title}` output
      format are unchanged.
- [ ] A CLI unit test proves the flags map to client arguments and the output
      format is unchanged.
- [ ] The named decisive end-to-end check runs the production path: a real
      uvicorn server serving the real app, notes seeded through the public
      POST route, the real `NotesClient` via `NOTES_API_URL`, and a real
      `main([...])` invocation with no injected test double — asserting a
      parameterized query's stdout and the unparameterized full listing
      through the same path.
- [ ] `apps/notes_cli/README.md` documents the flags and the
      `notes-client` dependency (parent decision D9) in the same change.

## Execution plan

Status: Draft

Approach:
- `apps/notes_cli/cli.py`: add options to the `list` subparser
  (`--limit` int, `--offset` int, `--sort` str, `--filter` str, all defaulting
  to unset) and pass only provided values to `client.list_notes(...)`; keep
  the print loop and line format unchanged.
- Named decisive check (new test in `apps/notes_cli/tests/`):
  - start `uvicorn.Server` serving `app.main.app` on an ephemeral
    `127.0.0.1` port in a daemon thread and wait for startup (`uvicorn` is
    added as a test dependency of the CLI app — parent decision D7);
  - seed notes through the public HTTP POST route so the check uses only
    public behavior;
  - set `NOTES_API_URL` to the server address, build
    `NotesClient.from_environment()`, and call
    `main(["list", "--sort", "title", "--limit", "2", "--filter", ...])` with
    no injected client; assert the exact stdout lines (order, filtering,
    pagination);
  - run the unparameterized `main(["list"])` against the same server and
    assert the full seeded listing — compatibility verified through the
    production path as well.
  - This test traverses the real CLI parser → real client → real httpx →
    real TCP → real FastAPI app → SQLite. The per-side tests (020's
    captured-transport test, 010's route tests) remain supporting evidence
    only and do not substitute for this check.
- CLI unit test (existing pattern with a fake client): flags forwarded as the
  expected client keyword arguments; unchanged formatting.

Environment: execution must first establish a test environment — no
virtualenv or declared test dependencies exist yet, and the end-to-end test
needs `app` (from `src/`), `notes_client`, and `notes_cli` importable
alongside `uvicorn` and `pytest`. Run from an isolated working directory:
the service writes `./notes.db` relative to the working directory.

### Implementation decisions and open questions

- D6 (flag names), D7 (real uvicorn server), and D9 (dependency recording)
  are approved at the parent level. Local choices resolved here: ephemeral
  port with a daemon-thread server; seeding via the public POST route;
  the decisive check uses the `from_environment()` construction path.
- Open questions: none.

### Documentation

- `apps/notes_cli/README.md`: document the new flags and the dependency on
  `notes-client` (D9); end-user audience.

### Task checklist

- [ ] Add query flags to the `list` subparser
- [ ] Add CLI unit test for flag forwarding and output regression
- [ ] Add the named production-path end-to-end check (real server, real client, real CLI)
- [ ] Update `apps/notes_cli/README.md`
- [ ] Run the CLI suite and record the decisive check's run

### Requirement verification

- Parent R4 → CLI unit test (flags → client arguments; unchanged line format)
  plus the end-to-end check.
- Parent R6 → the named decisive check described above; count it successful
  only when the intended tests collect and exit cleanly with the real server
  running.
- Parent R2/R3 production-path cross-check → the unparameterized
  `main(["list"])` assertion through the same real server and client path.
- Parent R7 (CLI part) → README diff in the same change.
````


**Assistant** *(reasoning present)*

```json
{
  "schema_version": 1,
  "scenario_id": "tg05-fastapi-multi-consumer-decomposition",
  "assessment": {
    "dimensions": {
      "plan_design_completeness": {
        "grade": "complete",
        "findings": [
          {
            "where": "000-main.md → Execution plan → Design (parameter table)",
            "quote": "`limit` | integer 1..100 | absent | Page size. Absent → full collection (preserves R2). Outside 1..100 → 422. This server-side cap is the pagination bound.",
            "why": "The plan states the full interface — ranges, defaults, semantics, and error behavior for all four parameters plus the unchanged bare-array response — so the decided contract is reconstructible from the plan alone, not just an ordered list of work steps."
          },
          {
            "where": "000-main.md → Design (component responsibilities and compatibility states)",
            "quote": "Each boundary keeps its unparameterized behavior (same request, same response, same output); new behavior is reachable only through the newly added optional parameters/flags. Dependencies enforce 010 → 020 → 030.",
            "why": "Assigns per-component responsibility (service owns contract/validation via Query constraints and the SQLAlchemy select, client serializes without validation, CLI maps flags 1:1 and owns the production-path proof), plus compatibility and dependency states — the design elements a continuing agent needs."
          },
          {
            "where": "000-main.md → Implementation decisions and open questions (D1–D9)",
            "quote": "Alternatives rejected: an envelope would break the current shape for unparameterized consumers or make the shape depend on which parameters are sent; a separate `/notes/query` route would fragment \"one capability\" into two collection operations.",
            "why": "Material decisions are recorded with rejected alternatives and consequences (\"no total-count field; consumers detect page end by receiving a short page\"), showing the decided design rather than mechanically filled sections."
          },
          {
            "where": "000-main.md → Requirement verification",
            "quote": "R6 → the named decisive check in 030: real uvicorn service + real `NotesClient` via `NOTES_API_URL` + real CLI `main()` invocation, asserting both a parameterized query and the unparameterized full listing through stdout.",
            "why": "Every requirement R1–R7 is mapped to specific verification evidence, closing the loop from design to how each requirement will be proven."
          }
        ]
      },
      "durable_context_preservation": {
        "grade": "complete",
        "findings": [
          {
            "where": "000-main.md → Decisions pending plan approval",
            "quote": "Approving the plan freezes them as the v1 public contract; later changes become breaking for consumers.",
            "why": "The conversation's approval-freeze framing (\"Approval of the plan freezes D1–D9 as the v1 public contract (afterward, changes become breaking)\") is carried into the files, preserving the approval mechanics and the D1–D9 numbering the response used."
          },
          {
            "where": "000-main.md → Design table and D4",
            "quote": "Case-insensitive literal substring match on `title`; `%` and `_` are matched literally.",
            "why": "The conversation's contract values and rationales reappear compressed but intact: literal matching, the narrower-v1 argument (\"widening the match later changes results for existing consumers\"), the id tie-break/default order, and 020's \"byte-identical to today's request\"."
          },
          {
            "where": "030-cli-query-flags-and-production-path.md → Execution plan",
            "quote": "seed notes through the public HTTP POST route so the check uses only public behavior; set `NOTES_API_URL` to the server address, build `NotesClient.from_environment()`",
            "why": "Every element of the conversation's decisive-check evidence is preserved in the owning child: real uvicorn + D7 test dependency, public POST seeding, from_environment, real main(...), parameterized and unparameterized stdout assertions, and mocks demoted to supporting evidence."
          },
          {
            "where": "000-main.md → Supporting facts",
            "quote": "Not yet verified (assumption to check during execution): whether the installed Starlette version runs the app lifespan for the existing `TestClient(app)` fixture pattern",
            "why": "All conversation-established risks and verified facts with sources survive: the lifespan assumption, the notes.db cwd side effect, the undeclared notes-cli→notes-client dependency (D9), the docs-index \"no notes-query specification exists\" quote, and the absent virtualenv/test dependencies."
          }
        ]
      },
      "section_appropriateness": {
        "grade": "complete",
        "findings": [
          {
            "where": "000-main.md → Requirements checklist (R1–R7)",
            "quote": "R2 — Unparameterized API behavior is preserved: `GET /notes/` with no query parameters returns the full collection as a bare JSON array exactly as today",
            "why": "Outcomes and compatibility constraints sit in requirements where a continuing agent looks first, and each child restates its own share in its own checklist rather than forcing a reader back to the parent."
          },
          {
            "where": "000-main.md → Supporting facts",
            "quote": "`apps/notes_cli/pyproject.toml` declares no dependency on `notes-client` despite importing it (D9).",
            "why": "Learned facts carry their sources (file paths, the docs-index quote, test-shape observations) in supporting details, with the actionable follow-up cross-referenced into the owning child's plan."
          },
          {
            "where": "010-api-collection-query.md → Execution plan",
            "quote": "Add FastAPI `Query` parameters to `read_all_notes` (`src/app/api/notes.py`): `limit` with `ge=1, le=100`",
            "why": "Direction — files to touch, mechanism, a concrete named test list, and environment setup — lives in the execution plans instead of leaking into requirements sections."
          },
          {
            "where": "000-main.md → Implementation decisions and open questions",
            "quote": "Open question: none at requirement level. Approval of this plan approves D1–D9 as the frozen v1 contract.",
            "why": "Pending/unresolved items sit in the decisions-and-open-questions sections; children honestly report \"Open questions: none\" rather than manufacturing questions, and the excerpt's open question (filter grammar, sort fields) is resolved into D3/D4 awaiting approval — the mechanism the target excerpt itself specifies."
          }
        ]
      },
      "plan_justification": {
        "grade": "justified",
        "findings": [
          {
            "where": "000-main.md → Implementation decisions and open questions (D2)",
            "quote": "`limit`/`offset` with a server-enforced cap of 100. Absent `limit` means the full collection; a default page size would change unparameterized behavior and violate R2.",
            "why": "Restates the conversation's proposal (\"limit (1..100, server-enforced cap; absent = full collection)\") including its compatibility rationale — the plan organizes planning that actually happened, using the same D1–D9 structure the response presented for approval."
          },
          {
            "where": "020/030 Depends On headers vs. the response's file list",
            "quote": "Depends On: tasks/20260926-notes-query-capability/010-api-collection-query.md (the contract is implemented and locked before the client relies on it)",
            "why": "Matches the conversation's structure and ordering rationale (\"the contract-first requirement makes the order structural\"); 030 depends on 010 + 020 exactly as the response's listing states."
          },
          {
            "where": "030 → Execution plan (named decisive check)",
            "quote": "start `uvicorn.Server` serving `app.main.app` on an ephemeral `127.0.0.1` port in a daemon thread and wait for startup",
            "why": "The evidence plan mirrors the conversation's per-file acceptance list; the added harness detail (ephemeral port, daemon thread, offset ≥ 0 default) is mechanical elaboration of decisions the conversation already made (D6, D7), not invented design scope."
          }
        ]
      },
      "task_kind_fit": {
        "grade": "fits",
        "findings": [
          {
            "where": "010-api-collection-query.md → Tests",
            "quote": "`limit=101` and `limit=0` → 422; `offset=-1` → 422; `sort=title` and `sort=-title` with duplicate titles → ties broken by ascending `id` (stability proof);",
            "why": "For code work the acceptance evidence is concrete named tests — bounds, 422s, tie stability, literal %/_ matching, combined parameters, and an unparameterized regression — the kind's own evidence rather than generic completion boxes."
          },
          {
            "where": "030 → Requirements checklist",
            "quote": "The named decisive end-to-end check runs the production path: a real uvicorn server serving the real app, notes seeded through the public POST route, the real `NotesClient` via `NOTES_API_URL`, and a real `main([...])` invocation with no injected test double",
            "why": "Matches the natural request's own acceptance bar (\"the CLI must prove the production client-to-service path\") with a named decisive check and explicit demotion of per-side mocks to supporting evidence."
          },
          {
            "where": "000-main.md → R7 and child Documentation sections",
            "quote": "R7 — Maintained documentation is updated in the same reviewed changes as the behavior it describes",
            "why": "Documentation acceptance is review-with-owning-change per surface (README/spec in 010, client README in 020, CLI README in 030) instead of a placeholder docs section — review acceptance appropriate to the docs portion."
          },
          {
            "where": "000-main.md → Decisions pending plan approval",
            "quote": "Contract-level choices below are presented with tradeoffs in `## Execution plan` → `### Implementation decisions and open questions`.",
            "why": "For a planning/decomposition deliverable the recorded decisions with tradeoffs are the acceptance artifact, and plan approval is wired in as the freeze mechanism; no inapplicable sections (e.g., rollback/ops) are filled mechanically."
          }
        ]
      }
    },
    "mistakes": [
      {
        "where": "000-main.md → Implementation decisions and open questions (scope exclusions)",
        "quote": "D1 — Extend `GET /notes/` in place; keep the bare JSON array response shape.",
        "why": "The conversation's explicit exclusion list is only partially carried: envelope/total, new endpoints, and version bumps survive via D1, the rejected /notes/query route, and the version-bump note, but \"no cursor pagination\", \"no schema changes\", and \"no client auto-pagination iterator\" appear nowhere as statements — a continuing agent scanning the files for v1 scope limits finds them only by implication from the four-parameter table and 020's pass-through rule."
      },
      {
        "where": "000-main.md → Subtasks",
        "quote": "- [ ] tasks/20260926-notes-query-capability/010-api-collection-query.md\n- [ ] tasks/20260926-notes-query-capability/020-client-query-parameters.md\n- [ ] tasks/20260926-notes-query-capability/030-cli-query-flags-and-production-path.md",
        "why": "The conversation's decomposition rationale — three independently maintained deliverables (service in src/app, notes-client package, notes-cli app), each with its own README, tests, and compatibility state, \"exactly what AGENTS.md says may justify separate deliverables\" — is compressed to a bare file list; the release/ownership/compatibility reasoning and the AGENTS.md anchor survive only as dispersed supporting facts, so a reviewer of the structure must reconstruct why three children rather than one."
      }
    ],
    "summary": "The four files let a reader reconstruct the decided design without the conversation: the plan alone yields the full v1 contract (parameter table with ranges, defaults, and 422 semantics; unchanged bare-array response with page-end-by-short-page), per-component responsibilities with compatibility states, the 010→020→030 dependency structure, D1–D9 with rejected alternatives and consequences, and an R1–R7→evidence mapping. Durable context is preserved nearly fully and compressed rather than dropped — structure, freeze-on-approval mechanics, contract values and rationales, per-child acceptance evidence, and the environment risks (lifespan assumption, notes.db side effect, D9, missing test deps) all appear, with facts carrying their sources. Content sits where a continuing agent looks: outcomes/constraints in requirements checklists, facts in supporting details, direction in Draft execution plans, pending items in decisions-and-open-questions (children honestly report none). The plan restates the response's own planning — same D-numbering, structure, and evidence — with only mechanical elaboration beyond it, so it is justified rather than fabricated. Acceptance evidence fits the work's kind: named integration/component/unit tests with regressions for code, review-with-owning-change for docs, and the named real-server/real-client/real-CLI decisive check the request demanded. Two minor losses: the explicit exclusion list is carried only partially (cursor pagination, schema changes, and the no-auto-pagination-iterator boundary are implied, not stated), and the three-way decomposition rationale, including its AGENTS.md anchor, is dropped to a bare subtask list."
  }
}
```
