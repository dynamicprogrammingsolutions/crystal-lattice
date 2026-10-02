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