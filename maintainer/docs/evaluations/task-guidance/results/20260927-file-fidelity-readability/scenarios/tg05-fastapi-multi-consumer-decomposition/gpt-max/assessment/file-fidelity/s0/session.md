# Session — tg05-fastapi-multi-consumer-decomposition · file-fidelity-assessment-gpt-max-s0 · glm max

- Run: `20260928T194526.268724Z-task-guidance-file-fidelity-tg05-fastapi-multi-consumer-decomposition-gpt-max-s0-6cad7346`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `116cf16e420d3cd4…`)
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
Created a Draft task hierarchy without implementing source changes:

- [Main task](</Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T221004.845192Z-task-guidance-tg05-fastapi-multi-consumer-decomposition-max-88684cd7/workspace/tasks/20260926-notes-query/000-main.md>)
- [Contract gate](</Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T221004.845192Z-task-guidance-tg05-fastapi-multi-consumer-decomposition-max-88684cd7/workspace/tasks/20260926-notes-query/010-contract.md>)
- [FastAPI service](</Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T221004.845192Z-task-guidance-tg05-fastapi-multi-consumer-decomposition-max-88684cd7/workspace/tasks/20260926-notes-query/020-api.md>)
- [Reusable Python client](</Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T221004.845192Z-task-guidance-tg05-fastapi-multi-consumer-decomposition-max-88684cd7/workspace/tasks/20260926-notes-query/030-python-client.md>)
- [CLI and production-path verification](</Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T221004.845192Z-task-guidance-tg05-fastapi-multi-consumer-decomposition-max-88684cd7/workspace/tasks/20260926-notes-query/040-cli.md>)

The plan sequences work as contract → API → client → CLI. It preserves the current unparameterized array behavior, assigns each public boundary its own acceptance evidence, and requires the CLI integration test to run through the production client against an actual HTTP-served FastAPI service.

The contract remains intentionally unresolved on pagination model/bounds, sort fields and tie-breaking, filter semantics, response shape, invalid-input behavior, and CLI option names. No tests were run because this was planning-only; the only worktree changes are the new task files.
````

The produced task files:

### tasks/20260926-notes-query/000-main.md

````markdown
# Add a stable notes-query capability across service, client, and CLI

Plan and coordinate one supported notes-query capability across the public
FastAPI service, reusable `notes_client` package, and `notes` CLI while
preserving the existing unparameterized collection behavior.

## Requirements checklist

- [ ] R1. The public query contract defines bounded pagination, stable sorting,
  optional text filtering, response shape, validation, and compatibility
  behavior before the client or CLI implementation relies on it.
- [ ] R2. The public notes collection API supports the approved query contract,
  including bounded pagination, deterministic sorting, and optional text
  filtering.
- [ ] R3. A request to the existing collection route without query parameters
  continues to return the current JSON-array behavior, and existing CRUD
  routes remain compatible.
- [ ] R4. `NotesClient` exposes the approved query capability while
  `list_notes()` with no arguments preserves its current request and return
  behavior.
- [ ] R5. `notes list` exposes the approved query capability through the
  reusable client and preserves the existing no-option command behavior.
- [ ] R6. Verification crosses the relevant public boundaries: the API is
  tested through the service route, the client is tested for contract mapping,
  and the CLI has a decisive test through the production client to a real
  service endpoint.
- [ ] R7. Maintained documentation describes the approved contract and the
  shipped service, client, and CLI behavior without presenting unimplemented
  behavior as current guidance.

## Scope

In scope:

- The collection query on `GET /notes/`.
- The corresponding `NotesClient.list_notes(...)` public method.
- Query options on the existing `notes list` command.
- Contract, compatibility, regression, integration, and documentation work
  owned by those three boundaries.

Out of scope unless the approved contract explicitly requires it:

- Changes to note creation, reading by ID, updating, or deletion.
- New persistence models, authentication, authorization, or unrelated API
  versioning.
- A separate search resource or a second client/CLI abstraction.

## Unresolved requirement questions

These questions change the public contract and must be answered before this
Draft plan becomes Approved or downstream consumer work begins.

- Q1 — Pagination: should the wire contract use `offset`/`limit`,
  page-number/page-size, or another model? What are the minimum, default, and
  maximum bounds, and does an absent pagination argument retain the current
  unbounded array behavior?
- Q2 — Sorting: which sortable fields and directions are public, what is the
  default order, and what unique tie-breaker guarantees deterministic results
  when the selected field has equal values?
- Q3 — Text filtering: which note fields are searched, is matching substring
  and case-insensitive, and what query parameter name and empty-value behavior
  are public?
- Q4 — Response shape: should queried responses remain JSON arrays, or should
  they add pagination metadata in an envelope? The same choice determines the
  client return type and CLI rendering.
- Q5 — Invalid input: what status and error shape should out-of-range,
  unsupported, or conflicting query values produce?
- Q6 — CLI surface: which option names map to the HTTP parameters, and should
  the existing one-line-per-note output remain unchanged when query options
  are supplied?

## Planning decisions

- Use one parent task with separate children for the contract gate, service,
  reusable package, and CLI. Each is an independently maintained public
  boundary with its own acceptance evidence.
- Sequence the work as contract → service → client → CLI. The contract child
  is a gate; it does not authorize consumer implementation while its public
  choices remain unresolved.
- Keep this handoff in `Draft` status. Creating these task files does not
  authorize implementation.

## Supporting facts

- `src/app/api/notes.py` currently exposes `GET /notes/` as an unparameterized
  collection route and returns `await crud.get_all()` directly.
- `src/app/api/crud.py` currently performs an unrestricted `notes.select()`;
  there is no explicit ordering, filtering, or pagination abstraction.
- `packages/notes_client/notes_client/client.py` currently implements
  `list_notes()` as `transport.get("/notes/").json()` with no arguments.
- `apps/notes_cli/cli.py` currently prints every result from
  `client.list_notes()` and already has a `client=None` test seam. Existing
  CLI tests use a fake client, so they do not prove the production
  client-to-service path.
- Existing tests cover only collection existence/array shape, a minimal client
  return type, and CLI output. They do not establish query semantics or
  cross-package integration.
- `docs/development/index.md` explicitly records that no notes-query
  specification exists. The service, package, and CLI READMEs currently
  describe only unparameterized behavior.

## Subtasks

- [ ] `tasks/20260926-notes-query/010-contract.md` — resolve and freeze the
  public notes-query contract before consumer implementation.
- [ ] `tasks/20260926-notes-query/020-api.md` — implement and verify the
  service-side query behavior against the approved contract.
- [ ] `tasks/20260926-notes-query/030-python-client.md` — expose the contract
  through the reusable Python client while preserving its no-argument API.
- [ ] `tasks/20260926-notes-query/040-cli.md` — expose the query through the
  CLI and prove the production client-to-service path.

## Execution plan

Status: Draft

The contract is the compatibility boundary for all three consumers. The first
child will record the parameter names, types, bounds, sorting and filtering
semantics, response shape, invalid-input behavior, and a compatibility matrix
for requests with and without query parameters. A reviewed contract document
must be accepted before service consumers are implemented; if a public choice
changes later, this plan returns to Draft and the dependent work is
reassessed.

After the contract gate, the service child will own the HTTP parameter
validation and database query behavior. The route and CRUD layer should keep
query construction inside the service, apply a unique tie-breaker for stable
ordering, enforce the approved pagination bounds, and retain the existing
no-parameter response behavior. Its decisive evidence is an integration test
through the FastAPI route and real SQLite-backed CRUD path.

The client child will map only the approved options to query parameters.
Omitting all options must continue to call `/notes/` without a query string
and return the existing list-compatible result. Its focused tests can use a
recording transport for serialization and regression behavior; the full
client-to-service connection is deliberately verified by the CLI child.

The CLI child will add the approved command options and keep HTTP ownership in
`NotesClient`. Existing rendering tests may retain a fake client for local
formatting, but the decisive query test must invoke the CLI without injecting a
fake client, configure the production client to an actual HTTP listener, and
assert the result returned by the running FastAPI service. If the repository
needs a test-only server launcher, that dependency and its lifecycle belong
to the CLI integration setup and must not replace the production request path.

Once all children are complete, run the repository's service, client, and CLI
tests together and inspect the maintained documentation for consistency. The
parent remains incomplete until the contract approval and real-path evidence
are recorded.

### Implementation decisions and open questions

The boundary split and execution order are decided for planning purposes. The
following public choices remain open because they affect all consumers:

- Pagination parameter model, bounds, defaults, and the no-parameter case
  (Q1).
- Sortable fields, direction syntax, default order, and deterministic
  tie-breaking (Q2).
- Filter scope and matching semantics (Q3).
- Array versus metadata envelope and corresponding client/CLI behavior (Q4).
- Invalid-input contract (Q5).
- CLI option names and output compatibility (Q6).

As a low-risk compatibility recommendation, evaluate keeping every response as
an array, applying pagination only when explicitly requested, using a bounded
`limit` plus an `offset`, searching title and description with a
case-insensitive substring, and always adding `id` as the final sort
tie-breaker. These are recommendations for review, not requirements or
decisions in this Draft.

### Documentation

- Add the reviewed contract at `docs/development/notes-query.md` and link it
  from `docs/development/index.md`; keep it visibly marked `Not implemented`
  if it is drafted before the feature ships.
- Update `README.md` with the current public API behavior after the service
  implementation is verified.
- Update `packages/notes_client/README.md` with the supported method
  arguments and no-argument compatibility behavior after the client ships.
- Update `apps/notes_cli/README.md` with the supported list options and
  production usage after the CLI ships.
- Do not make current user documentation claim query support before the
  corresponding implementation and verification are complete.

### Task checklist

- [ ] Resolve Q1–Q6 and approve the contract direction.
- [ ] Complete `010-contract.md` and obtain human contract approval.
- [ ] Complete `020-api.md`, including route-level query and regression
  evidence.
- [ ] Complete `030-python-client.md`, including no-argument compatibility
  evidence.
- [ ] Complete `040-cli.md`, including the real CLI → client → service
  integration check.
- [ ] Run the combined verification and update maintained documentation.
- [ ] Append completion evidence only after all requirements are verified.

### Requirement verification

- R1: Human approval of `docs/development/notes-query.md`, followed by API
  contract tests that exercise every approved query condition at
  `GET /notes/`.
- R2: Service integration tests through FastAPI with seeded notes covering
  bounds, filtering, sort ties, and the approved pagination response.
- R3: A regression request to `GET /notes/` with no query parameters asserting
  the existing JSON-array behavior, plus the existing CRUD route checks.
- R4: Client tests asserting exact no-argument request compatibility and
  contract-compliant serialization for each supplied option.
- R5–R6: The CLI child’s named end-to-end test, invoked without a fake client,
  must traverse the CLI parser, production `NotesClient`, an actual HTTP
  service endpoint, and the returned query result.
- R7: Review the contract and each owning README after implementation; any
  target-only documentation remains marked until its behavior is shipped.

### Additional implementation verification

- Run the focused suites at their owners and then the combined command
  `pytest -q src/tests packages/notes_client/tests apps/notes_cli/tests` from
  the repository root, with any package path setup required by the existing
  project harness.
- Include regression cases for equal sort keys, empty result pages, boundary
  values, and invalid query input once Q1–Q5 are resolved.
````

### tasks/20260926-notes-query/010-contract.md

````markdown
# Freeze the notes-query public contract

Define and obtain approval for the stable notes-query contract that the
FastAPI service, reusable Python client, and CLI will all consume.

## Requirements checklist

- [ ] C1. The contract specifies query parameter names, types, bounds,
  defaults, and invalid-input behavior for bounded pagination.
- [ ] C2. The contract specifies sortable fields, direction syntax, default
  ordering, and a deterministic tie-breaker.
- [ ] C3. The contract specifies text-filter scope, matching and
  case-sensitivity rules, empty values, and the public parameter name.
- [ ] C4. The contract specifies the response shape and compatibility behavior
  for both unparameterized and parameterized requests.
- [ ] C5. The contract maps the HTTP options to the client method and CLI
  surface and is human-approved before dependent implementation begins.

Parent Task: `tasks/20260926-notes-query/000-main.md`

Depends On: None

## Scope

This task owns the public decision boundary and its documentation. It does
not implement the route, client, or CLI. It may draft a target contract, but
the document must not be presented as current supported behavior until the
dependent implementation is shipped.

## Supporting facts

- No notes-query specification currently exists.
- The current service route returns a JSON array for `GET /notes/` without
  parameters.
- The current client method has no arguments and returns the decoded JSON
  directly.
- The current CLI has one `list` command and prints one line per note.

## Execution plan

Status: Draft

Resolve the open public choices from the parent task, then write a compact
contract at `docs/development/notes-query.md`. It should include concrete
request examples, response examples, validation/error examples, a
compatibility matrix, and the client/CLI naming map. Keep the contract
independent of internal module names so it remains useful to HTTP consumers.

Review the document as a public API proposal. Once approved, treat parameter
names, response shape, and compatibility rules as frozen for the dependent
service, client, and CLI tasks. If a later implementation discovery requires a
public change, stop dependent work and return this task and the parent to
Draft before changing the document.

### Implementation decisions and open questions

The document must explicitly resolve pagination model and bounds, sorting and
tie-breaking, text matching, response envelope versus array, invalid-input
behavior, and CLI option names. Do not choose a value merely because it is
convenient for the current SQLite implementation; each choice is part of the
consumer-facing contract.

The compatibility recommendation in the parent—array responses, explicit
pagination, bounded `limit`/`offset`, case-insensitive title/description
substring matching, and an `id` tie-breaker—can be used as a review starting
point but requires approval before it becomes binding.

### Documentation

- Create `docs/development/notes-query.md` as the maintained contract source.
- Update `docs/development/index.md` to link to the specification only after
  the contract has been reviewed; while the feature is not shipped, label the
  target behavior `Not implemented`.
- Do not update package or CLI user guidance in this task; those owners will
  document shipped behavior after implementation.

### Task checklist

- [ ] Resolve the public questions recorded in the parent task.
- [ ] Draft the contract with examples and compatibility matrix.
- [ ] Review and approve the contract.
- [ ] Record approval and unlock `020-api.md`, `030-python-client.md`, and
  `040-cli.md`.

### Requirement verification

- C1–C4: Inspect the reviewed contract for complete request, response,
  validation, and compatibility examples; unresolved public choices leave the
  requirements incomplete.
- C5: Human approval is the decisive gate. The dependent task files must not
  move to execution until the approved contract is available.
````

### tasks/20260926-notes-query/020-api.md

````markdown
# Implement notes-query behavior in the public FastAPI service

Implement the approved notes-query contract at the existing collection route,
including real service/database verification and preservation of the
unparameterized API.

## Requirements checklist

- [ ] A1. `GET /notes/` accepts the approved pagination, sorting, and text
  filtering parameters and enforces their approved validation and bounds.
- [ ] A2. Query results have the approved deterministic ordering, including the
  required unique tie-breaker.
- [ ] A3. `GET /notes/` without query parameters preserves the existing
  JSON-array behavior and does not regress the CRUD routes.
- [ ] A4. Service tests exercise the behavior through FastAPI and the
  SQLite-backed CRUD path, including boundary, tie, filter, empty-result, and
  invalid-input cases required by the contract.
- [ ] A5. Service-facing documentation reflects only verified, shipped
  behavior.

Parent Task: `tasks/20260926-notes-query/000-main.md`

Depends On: `tasks/20260926-notes-query/010-contract.md`

## Scope

This task owns the HTTP route, service query construction, and service-level
tests. It does not change client serialization or CLI parsing. The route
shape and all public validation behavior come from the approved contract.

## Supporting facts

- `src/app/api/notes.py` currently delegates the collection route to
  `crud.get_all()` without query parameters.
- `src/app/api/crud.py` currently issues an unrestricted SQLAlchemy select.
- `src/tests/test_notes.py` uses `fastapi.testclient.TestClient` and currently
  verifies only that the collection response is a list.
- The notes table has `id`, `title`, and `description`; no pagination metadata
  or query-specific persistence is currently present.

## Execution plan

Status: Draft

After `010-contract.md` is approved, introduce a service-side query
representation at the route boundary and pass it to CRUD/query construction.
Keep parameter validation at the public HTTP boundary and make the SQL query
apply filtering, ordering, and pagination in a deterministic order. The
ordering implementation must include the contract’s unique tie-breaker even
when multiple notes share the requested sort value.

Preserve the existing no-parameter path deliberately: a request with no query
parameters must retain its current response shape and compatibility semantics.
Do not make consumer behavior depend on undocumented database insertion order;
where the approved contract requires stable ordering, express it in the
query.

Add route-level tests using the actual FastAPI app and SQLite-backed CRUD
operations. Seed notes with duplicate sort values and matching/non-matching
text, then assert the complete approved contract through HTTP responses rather
than calling CRUD functions directly.

### Implementation decisions and open questions

The public decisions are owned by `010-contract.md`; this task must not
silently reinterpret them. Internal choices—such as whether to use a small
validated query model or explicit FastAPI parameters—may be resolved locally
provided they preserve the approved wire contract.

If the existing test database lifecycle makes isolation unreliable, improve
the test fixture within this task without changing production persistence or
adding a test-only route.

### Documentation

- Update the root service README with the verified collection-query usage.
- Keep `docs/development/notes-query.md` as the contract source and update
  its implementation status only after the route tests pass.
- Do not document client or CLI behavior here; those claims belong to their
  owning tasks.

### Task checklist

- [ ] Confirm the approved contract from
  `tasks/20260926-notes-query/010-contract.md`.
- [ ] Implement route validation and service/CRUD query behavior.
- [ ] Add route-level regression and query integration tests.
- [ ] Run the service-focused suite and record evidence.
- [ ] Update service-facing documentation with verified behavior.

### Requirement verification

- A1–A2: HTTP integration tests through `TestClient` with real CRUD/database
  execution cover each approved query feature and deterministic ordering.
- A3: A no-query request asserts the existing JSON-array shape and the CRUD
  route regression tests remain green.
- A4: The decisive evidence is the service suite crossing the route, FastAPI
  validation, CRUD, SQL query, and response serialization boundaries.
- A5: Review the root README and contract status after the implementation
  tests succeed.
````

### tasks/20260926-notes-query/030-python-client.md

````markdown
# Expose notes-query through the reusable Python client

Map the approved notes-query contract onto `NotesClient` while keeping the
existing no-argument `list_notes()` call compatible.

## Requirements checklist

- [ ] P1. `NotesClient.list_notes(...)` accepts the approved query options and
  serializes them to the documented HTTP request.
- [ ] P2. `list_notes()` with no arguments continues to request `/notes/`
  without query parameters and returns the current list-compatible result.
- [ ] P3. Client tests cover option mapping, omission of unset values, response
  decoding, and no-argument regression behavior.
- [ ] P4. The package README documents the verified query interface and
  compatibility behavior.

Parent Task: `tasks/20260926-notes-query/000-main.md`

Depends On:

- `tasks/20260926-notes-query/010-contract.md`
- `tasks/20260926-notes-query/020-api.md`

## Scope

This task owns the reusable package API and HTTP request serialization. It
does not own FastAPI query semantics or CLI option parsing. It must consume
the frozen contract rather than expose package-specific names that diverge
from the public HTTP interface without a documented reason.

## Supporting facts

- `NotesClient` accepts an injected transport and has a
  `from_environment()` constructor that creates an `httpx.Client`.
- The current implementation calls `transport.get("/notes/").json()` with no
  arguments.
- The existing client test uses a minimal recording-compatible transport but
  does not assert the requested path or query parameters.

## Execution plan

Status: Draft

After the contract and service are stable, extend `list_notes` with the
approved, clearly named options. Build request parameters from values actually
supplied by the caller so the zero-argument call remains an unparameterized
request. Preserve the client’s direct JSON decoding unless the approved
response contract requires a deliberately documented result model or
envelope.

Expand the client tests with a recording transport that captures path and
keyword arguments. Assert exact serialization and URL-safe handling for each
query option, omission of unset values, decoding of the approved response,
and the unchanged no-argument behavior. Keep one focused client test per
mapping concern; the full service connection is verified by the CLI
integration task.

### Implementation decisions and open questions

The method signature and return type are public package behavior. They remain
blocked on the approved response and option contract. Do not add a second
method or silently change the no-argument return type to make pagination
metadata convenient.

The transport abstraction should remain usable for existing callers. Any
change needed to support a real-path integration test must preserve the
constructor and environment behavior unless the contract explicitly approves
an additive compatibility change.

### Documentation

- Update `packages/notes_client/README.md` with the verified method signature,
  option semantics, response handling, and no-argument compatibility.
- Link to the maintained query contract where appropriate.
- Do not state support until the client tests and dependent service behavior
  are verified.

### Task checklist

- [ ] Confirm the approved HTTP contract and service behavior.
- [ ] Extend `NotesClient.list_notes(...)` with the approved options.
- [ ] Add serialization and no-argument regression tests.
- [ ] Run the package-focused suite and record evidence.
- [ ] Update the package README with current behavior.

### Requirement verification

- P1: Client tests with a recording transport assert the exact path and query
  mapping for every approved option.
- P2: A no-argument test asserts the path `/notes/`, absence of query
  parameters, and the existing list-compatible decoded result.
- P3: The package test suite must collect and pass with the real client class,
  not only a fake client.
- P4: Review the package README against the approved contract and passing
  tests.
````

### tasks/20260926-notes-query/040-cli.md

````markdown
# Expose notes-query through the CLI and prove the production path

Add the approved query options to `notes list`, preserve existing output for
the no-option command, and verify the real CLI → `NotesClient` → FastAPI
service path.

## Requirements checklist

- [ ] L1. `notes list` exposes the approved query options with documented
  names, validation, and forwarding behavior.
- [ ] L2. `notes list` with no query options preserves the current command
  behavior and output contract.
- [ ] L3. The CLI delegates all service access to the production
  `NotesClient`; it does not implement a second HTTP/query protocol.
- [ ] L4. A decisive integration test invokes the CLI without a fake client,
  reaches an actual HTTP-served FastAPI application through the production
  client, and proves the approved pagination, sorting, and filtering result.
- [ ] L5. CLI documentation and tests describe only the verified behavior.

Parent Task: `tasks/20260926-notes-query/000-main.md`

Depends On:

- `tasks/20260926-notes-query/010-contract.md`
- `tasks/20260926-notes-query/020-api.md`
- `tasks/20260926-notes-query/030-python-client.md`

## Scope

This task owns CLI parsing, forwarding, rendering, and the end-to-end
consumer-path evidence. It does not change HTTP semantics or duplicate client
serialization.

## Supporting facts

- `apps/notes_cli/cli.py` currently defines only `notes list`, prints
  `id: title`, and uses `NotesClient.from_environment()` when no client is
  injected.
- Existing CLI tests inject a fake client and therefore prove formatting only.
- The client’s environment-based constructor targets `NOTES_API_URL`, so a
  production-path test must configure that variable and avoid the injected
  fake-client seam.

## Execution plan

Status: Draft

After the contract and client are approved, add the documented list options
to the argument parser and pass only supplied values to
`NotesClient.list_notes(...)`. Keep the existing rendering path for the
approved response shape; if metadata is introduced, define its presentation
in the contract before changing output.

Retain focused unit tests for parser and rendering behavior with a small fake
client where that is the narrowest useful evidence. Add a separate decisive
integration test that:

1. Starts the real FastAPI application behind an actual HTTP listener with
   isolated test data.
2. Seeds notes through a supported service path.
3. Sets `NOTES_API_URL` to that listener.
4. Invokes the CLI production entry point or `main(...)` with no injected
   client and the approved query options.
5. Asserts the command succeeds and prints exactly the notes selected and
   ordered by the running service.

The test must use the production `NotesClient.from_environment()` path and a
real service response. A fake client, mocked transport, direct CRUD call, or
direct invocation of the route is not decisive evidence for L4. Record the
exact focused invocation used by the test suite, for example
`pytest -q apps/notes_cli/tests/test_cli_integration.py`, after the fixture
and server dependency are settled.

### Implementation decisions and open questions

CLI option names and output behavior remain blocked on the approved contract.
The current `client=None` seam may remain for unit-level rendering tests, but
it must not be used by the decisive integration test. If an HTTP server
launcher or test dependency is needed, choose one that exercises the actual
ASGI application and record its lifecycle and dependency ownership; do not
replace the production request with a mocked response.

### Documentation

- Update `apps/notes_cli/README.md` with the verified options, examples, and
  no-option compatibility behavior.
- Link to the query contract without duplicating conflicting semantics.
- Document the real-path integration command in developer-facing test
  guidance only if it is stable and maintained.

### Task checklist

- [ ] Confirm the approved contract and completed client interface.
- [ ] Add parser options and forwarding through `NotesClient`.
- [ ] Preserve and test no-option rendering behavior.
- [ ] Add and pass the real CLI → client → HTTP service integration test.
- [ ] Run the CLI-focused suite and record the exact invocation.
- [ ] Update the CLI README with verified behavior.

### Requirement verification

- L1: Parser tests and a recording-client test assert option names, defaults,
  and forwarding without duplicating HTTP serialization.
- L2: The existing no-option command test remains green and asserts unchanged
  output semantics.
- L3: Code inspection plus tests confirm the CLI calls `NotesClient` rather
  than constructing service requests itself.
- L4: The decisive evidence is the integration test invocation
  `pytest -q apps/notes_cli/tests/test_cli_integration.py` (or its recorded
  maintained equivalent), run with no injected client and an actual
  HTTP-served FastAPI app.
- L5: Review the CLI README against the approved contract and passing tests.
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
            "where": "tasks/20260926-notes-query/000-main.md — Planning decisions",
            "quote": "Use one parent task with separate children for the contract gate, service, reusable package, and CLI. Each is an independently maintained public boundary with its own acceptance evidence.",
            "why": "States the component decomposition and each boundary's responsibility, so the parent alone conveys the decided structure, not just an ordered step list."
          },
          {
            "where": "tasks/20260926-notes-query/000-main.md — Execution plan",
            "quote": "the route and CRUD layer should keep query construction inside the service, apply a unique tie-breaker for stable ordering, enforce the approved pagination bounds, and retain the existing no-parameter response behavior",
            "why": "Gives the service child's internal design and data flow (route validation -> CRUD query construction -> tie-breaker/bounds), which is design behind the sequence, not just steps."
          },
          {
            "where": "tasks/20260926-notes-query/000-main.md — Execution plan (client paragraph)",
            "quote": "Omitting all options must continue to call `/notes/` without a query string and return the existing list-compatible result",
            "why": "Defines the client's interface contract and compatibility state explicitly, mirrored in P2 and L2 for the other boundaries."
          },
          {
            "where": "tasks/20260926-notes-query/040-cli.md — Execution plan",
            "quote": "Starts the real FastAPI application behind an actual HTTP listener with isolated test data. Seeds notes through a supported service path. Sets `NOTES_API_URL` to that listener. Invokes the CLI production entry point or `main(...)` with no injected client and the approved query options.",
            "why": "The consumer-path design is concrete enough to reconstruct: real ASGI app, real listener, seeded data, environment-based production client, exact assertion target."
          },
          {
            "where": "tasks/20260926-notes-query/000-main.md — Requirement verification",
            "quote": "R3: A regression request to `GET /notes/` with no query parameters asserting the existing JSON-array behavior, plus the existing CRUD route checks.",
            "why": "Each requirement R1–R7 carries its verification method in the plan, so the plan alone shows how the requirements are verified."
          },
          {
            "where": "tasks/20260926-notes-query/000-main.md — Implementation decisions and open questions",
            "quote": "These are recommendations for review, not requirements or decisions in this Draft.",
            "why": "Separates decided design from open public choices (Q1–Q6), keeping the decided-vs-open boundary unambiguous for a reader of the plan alone."
          }
        ]
      },
      "durable_context_preservation": {
        "grade": "complete",
        "findings": [
          {
            "where": "tasks/20260926-notes-query/000-main.md — Planning decisions",
            "quote": "Sequence the work as contract → service → client → CLI. The contract child is a gate; it does not authorize consumer implementation while its public choices remain unresolved.",
            "why": "Preserves the response's stated sequencing and gate decision verbatim."
          },
          {
            "where": "tasks/20260926-notes-query/000-main.md — Requirements checklist R3",
            "quote": "A request to the existing collection route without query parameters continues to return the current JSON-array behavior, and existing CRUD routes remain compatible.",
            "why": "Preserves the response's unparameterized-array preservation outcome; the same constraint is restated in P2 and L2 for their boundaries."
          },
          {
            "where": "tasks/20260926-notes-query/040-cli.md — Requirements checklist L4",
            "quote": "A decisive integration test invokes the CLI without a fake client, reaches an actual HTTP-served FastAPI application through the production client, and proves the approved pagination, sorting, and filtering result.",
            "why": "Preserves the response's requirement that the CLI integration test run through the production client against an actual HTTP-served service."
          },
          {
            "where": "tasks/20260926-notes-query/000-main.md — Implementation decisions and open questions",
            "quote": "Pagination parameter model, bounds, defaults, and the no-parameter case (Q1). ... CLI option names and output compatibility (Q6).",
            "why": "The response's six intentionally unresolved contract areas map one-to-one onto Q1–Q6; compressed, not dropped, and echoed in 010's open-questions section."
          },
          {
            "where": "tasks/20260926-notes-query/000-main.md — Planning decisions",
            "quote": "Keep this handoff in `Draft` status. Creating these task files does not authorize implementation.",
            "why": "Preserves the planning-only outcome and non-authorization state established in the conversation."
          },
          {
            "where": "tasks/20260926-notes-query/000-main.md — Supporting facts",
            "quote": "packages/notes_client/notes_client/client.py currently implements `list_notes()` as `transport.get(\"/notes/\").json()` with no arguments",
            "why": "Verified current-behavior facts are preserved with their file sources, including the client test seam, the fake-client CLI tests, and docs/development/index.md recording that no notes-query specification exists."
          }
        ]
      },
      "section_appropriateness": {
        "grade": "complete",
        "findings": [
          {
            "where": "tasks/20260926-notes-query/000-main.md — Scope",
            "quote": "Out of scope unless the approved contract explicitly requires it: ... New persistence models, authentication, authorization, or unrelated API versioning.",
            "why": "Outcomes and constraints sit in the requirements checklist and scope sections where a continuing agent looks for them first."
          },
          {
            "where": "tasks/20260926-notes-query/000-main.md — Supporting facts",
            "quote": "Existing CLI tests inject a fake client and therefore prove formatting only.",
            "why": "Learned investigation facts are in supporting details, kept out of the plan narrative and requirement lists."
          },
          {
            "where": "tasks/20260926-notes-query/000-main.md — Execution plan",
            "quote": "A reviewed contract document must be accepted before service consumers are implemented; if a public choice changes later, this plan returns to Draft and the dependent work is reassessed.",
            "why": "Sequencing and gating direction live in the implementation-plan section, matching where a continuing agent reads for direction."
          },
          {
            "where": "tasks/20260926-notes-query/020-api.md — Implementation decisions and open questions",
            "quote": "The public decisions are owned by `010-contract.md`; this task must not silently reinterpret them.",
            "why": "Unresolved dependencies are recorded in the questions/decisions section of each dependent child, not buried in scope text."
          },
          {
            "where": "tasks/20260926-notes-query/010-contract.md — Implementation decisions and open questions",
            "quote": "The compatibility recommendation in the parent—array responses, explicit pagination, bounded `limit`/`offset`, case-insensitive title/description substring matching, and an `id` tie-breaker—can be used as a review starting point but requires approval before it becomes binding.",
            "why": "The pending proposal is placed with the open questions it belongs to, and its non-binding status is restated in the task that would act on it."
          }
        ]
      },
      "plan_justification": {
        "grade": "justified",
        "findings": [
          {
            "where": "Producer response vs tasks/20260926-notes-query/000-main.md — Unresolved requirement questions",
            "quote": "response: 'pagination model/bounds, sort fields and tie-breaking, filter semantics, response shape, invalid-input behavior, and CLI option names' → files: Q1, Q2, Q3, Q4, Q5, Q6",
            "why": "The six open contract areas in the files restate exactly the unresolved set the conversation established, with nothing extra declared decided."
          },
          {
            "where": "tasks/20260926-notes-query/000-main.md — Execution plan",
            "quote": "The contract is the compatibility boundary for all three consumers.",
            "why": "Organizes the conversation's planning (contract gate first, consumers after) rather than introducing new structure."
          },
          {
            "where": "tasks/20260926-notes-query/000-main.md — Implementation decisions and open questions",
            "quote": "These are recommendations for review, not requirements or decisions in this Draft.",
            "why": "The only design detail beyond the response's summary (array responses, limit/offset, substring matching, id tie-breaker) is explicitly non-binding, so no unestablished detail is asserted as decided."
          },
          {
            "where": "tasks/20260926-notes-query/040-cli.md — Execution plan",
            "quote": "Record the exact focused invocation used by the test suite, for example `pytest -q apps/notes_cli/tests/test_cli_integration.py`, after the fixture and server dependency are settled.",
            "why": "Forward-looking evidence naming is marked provisional, consistent with the conversation's planning-only state in which no tests were run."
          }
        ]
      },
      "task_kind_fit": {
        "grade": "fits",
        "findings": [
          {
            "where": "tasks/20260926-notes-query/010-contract.md — Requirement verification C5",
            "quote": "Human approval is the decisive gate. The dependent task files must not move to execution until the approved contract is available.",
            "why": "The contract is a document artifact, and its acceptance evidence is review approval plus the unlock condition — the right evidence kind for a contract-freeze task."
          },
          {
            "where": "tasks/20260926-notes-query/020-api.md — Requirement verification A4",
            "quote": "The decisive evidence is the service suite crossing the route, FastAPI validation, CRUD, SQL query, and response serialization boundaries.",
            "why": "Code boundaries get test-based acceptance evidence crossing real storage, matching the code kind of the child."
          },
          {
            "where": "tasks/20260926-notes-query/000-main.md — Requirement verification R7",
            "quote": "Review the contract and each owning README after implementation; any target-only documentation remains marked until its behavior is shipped.",
            "why": "The documentation outcome gets review acceptance with a not-implemented guard, fitting the documentation kind required by QUERY-5."
          },
          {
            "where": "tasks/20260926-notes-query/040-cli.md — Requirement verification L4",
            "quote": "The decisive evidence is the integration test invocation `pytest -q apps/notes_cli/tests/test_cli_integration.py` (or its recorded maintained equivalent), run with no injected client and an actual HTTP-served FastAPI app.",
            "why": "The integration child names its decisive command and explicitly rules out fake-client/mocked/CRUD-level evidence, so the production-path acceptance is executable and checkable."
          },
          {
            "where": "tasks/20260926-notes-query/000-main.md — Planning decisions",
            "quote": "Keep this handoff in `Draft` status. Creating these task files does not authorize implementation.",
            "why": "The tracking parent records its decisions and state; no test results or completion evidence are fabricated for planning-only work, and no inapplicable sections (e.g., rollback) are mechanically filled."
          }
        ]
      }
    },
    "mistakes": [],
    "summary": "The task hierarchy restates and organizes the conversation's planning without extending it into invented decisions. The four-boundary split, contract→API→client→CLI sequencing, gate semantics with a Draft/unlock rule, unparameterized JSON-array preservation, per-boundary decisive evidence, and the production CLI→client→HTTP-service integration requirement all match the final response, and the response's six unresolved contract areas map one-to-one onto Q1–Q6, so no durable outcome, decision, sourced fact, or verification approach was dropped. Content sits in conventional sections: requirements/scope carry outcomes and constraints, supporting facts carry sourced investigation findings, the execution plan carries direction, and open items plus the explicitly non-binding compatibility recommendation sit in the questions/decisions sections. Acceptance evidence fits each artifact kind: human approval for the contract document, boundary-crossing tests for code children, README review for documentation, and Draft status plus recorded decisions for the tracking parent — with no mechanically filled inapplicable sections and no invented test results. The mistake hunt surfaced no dropped facts, invented scope, misplaced content, or missing acceptance evidence; the only borderline item (the response's 'no tests were run / only task files changed' session note) is recoverable from the unchecked checklists and Draft statuses, so it is not a material drop."
  }
}
```
