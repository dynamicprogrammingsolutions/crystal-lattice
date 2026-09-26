# Add supported notes-query across API, Python client, and CLI

Plan for one public notes-query capability spanning the FastAPI service,
reusable Python client, and CLI. The work is planned only; implementation
starts after the contract questions are resolved and this plan is approved.

## Requirements checklist

- [ ] Freeze one documented notes-query contract before client or CLI
      consumers depend on it, including query names and types, defaults,
      maximums, response shape, validation errors, filtering semantics, and
      sorting/tie-break rules.
- [ ] Extend the public notes collection API with bounded pagination, stable
      deterministic sorting, and optional text filtering.
- [ ] Preserve the current unparameterized API behavior: `GET /notes/`
      without query parameters remains a successful JSON array response
      containing the unparameterized collection.
- [ ] Extend the reusable Python client to expose the same query capability
      while preserving the current no-argument `list_notes()` call and its
      list result.
- [ ] Extend the CLI list operation with the supported query controls and
      retain its existing default listing behavior.
- [ ] Prove the production CLI-to-client-to-service path against a live
      service endpoint, with no injected fake client or mocked HTTP response in
      the decisive check.
- [ ] Update maintained API, client, and CLI documentation in the same
      implementation change so public guidance describes only supported
      behavior.

## Scope and workstreams

The API owns the canonical query semantics and compatibility boundary. The
Python client owns translating its public method arguments into the canonical
HTTP request. The CLI owns user-facing option parsing and presentation. The
work is ordered so the API contract is frozen before either consumer is
implemented.

## Requirement questions and scope decisions

These questions affect the public contract and must be answered before the
plan is approved for execution:

- What query parameter names and response shape should be public? In
  particular, should pagination use `limit`/`offset` or page-number
  terminology, and should parameterized responses remain arrays or include
  pagination metadata in an envelope?
- Which note fields are searchable, whether matching is substring or another
  mode, and whether matching is case-sensitive?
- Which sort keys and directions are supported? What deterministic secondary
  key should resolve equal primary values?
- What are the inclusive bounds and error responses for pagination and other
  invalid query values?
- Should the no-parameter request retain database/insertion ordering exactly,
  or should the new stable default ordering also apply when no query
  parameters are present? The response type and no-parameter compatibility
  requirement remain fixed either way.

Recommended direction for review, not yet a decision: keep the response as a
JSON array for the smallest compatibility surface; use offset plus bounded
limit; make text matching an explicitly documented case-insensitive
substring over title and description; and define an explicit primary sort
with `id` as the tie-breaker. The implementation must not rely on these
recommendations until they are approved.

## Supporting facts

- `src/app/api/notes.py` currently exposes `GET /notes/` as an unparameterized
  route returning `crud.get_all()`.
- `src/app/api/crud.py` currently delegates collection retrieval directly to
  `database.fetch_all(notes.select())`; the schema has only `id`, `title`, and
  `description`.
- `packages/notes_client/notes_client/client.py` currently calls
  `transport.get("/notes/").json()` and returns the decoded value.
- `apps/notes_cli/cli.py` currently has one `list` subcommand, prints each
  returned note, and constructs `NotesClient.from_environment()` when no
  client is injected.
- Existing API tests cover only successful collection shape and route
  existence. Client and CLI tests use test doubles. No notes-query
  specification or maintained query documentation exists.
- The current project manifest does not declare an ASGI server executable.
  The live-path test therefore needs an explicitly supported process/server
  harness or a narrowly scoped test dependency decision during execution.

## Subtasks

- [ ] `tasks/20260925-notes-query/010-api-contract-and-service.md`
- [ ] `tasks/20260925-notes-query/020-python-client.md`
- [ ] `tasks/20260925-notes-query/030-cli.md`

## Execution plan

Status: Draft

The service subtask first turns the approved query vocabulary and semantics
into the HTTP/OpenAPI contract, validates inputs at the public route boundary,
and implements filtering, bounded pagination, and deterministic ordering in
the database query. The no-query branch must retain its current response
shape and behavior. API integration tests will seed enough notes to expose
page boundaries, duplicate sort values, and filter combinations.

After the API contract is frozen, the client subtask adds optional,
contract-aligned arguments to `list_notes()` and serializes only the selected
query values. Its no-argument path must continue to issue the existing
collection request and return the existing list. It will include focused
serialization tests plus a real service/client integration check so the
transport and HTTP contract are exercised together.

The CLI subtask adds options only after the client/API vocabulary is settled,
preserves the current default output, and defines how filtered or paginated
results are rendered. Its decisive acceptance check starts a live notes
service, points `NOTES_API_URL` at it, invokes the production CLI path without
injecting a client, and verifies that the requested query reaches the service
and produces the expected output.

All three public READMEs and any maintained API/developer contract source will
be updated as part of the implementation change. No target-only user guidance
will be presented as current behavior before the feature exists.

### Implementation decisions and open questions

- Public parameter names, result shape, searchable fields, matching mode,
  sort keys/directions, tie-breaker, and bounds remain open until reviewed.
- The implementation should keep the no-argument route and client call
  compatible even if the parameterized contract adds metadata or stricter
  validation.
- A real localhost HTTP process is required for the decisive consumer-path
  evidence. The execution plan must identify the project-supported ASGI
  server and declare any test-only dependency needed to launch it.

### Documentation

- API ownership: document the finalized HTTP query contract in the maintained
  API source/OpenAPI metadata and update the root service README if it is the
  user-facing entry point.
- Client ownership: update `packages/notes_client/README.md` with method
  arguments, defaults, result shape, and compatibility behavior.
- CLI ownership: update `apps/notes_cli/README.md` with supported list
  options, examples, validation behavior, and default output.
- Do not create a speculative current-behavior page while the contract is
  unresolved; if a standalone developer contract is needed after approval,
  place it under the existing `docs/development/` structure and link it from
  the development index.

### Task checklist

- [ ] Resolve and record the public contract decisions.
- [ ] Approve this plan and mark the execution status `Approved`.
- [ ] Complete `010-api-contract-and-service.md` and its public API evidence.
- [ ] Complete `020-python-client.md` and its real API/client evidence.
- [ ] Complete `030-cli.md` and its live production-path evidence.
- [ ] Update maintained documentation only after behavior is implemented.
- [ ] Run the focused API, client, CLI, and live-path checks; record blocked
      gates explicitly.
- [ ] Append completion notes with requirement evidence and any deferred
      scope.

### Requirement verification

- API query behavior, bounds, filtering, sorting, and no-parameter
  compatibility: service integration tests through `GET /notes/`, owned by
  `010-api-contract-and-service.md`.
- Client query exposure and request serialization: package tests plus a
  real-service `NotesClient` integration check, owned by
  `020-python-client.md`.
- CLI option behavior and preserved default rendering: CLI tests, owned by
  `030-cli.md`.
- Production consumer connection: one live HTTP acceptance test that starts
  the service, uses environment-based `NotesClient.from_environment()`, and
  invokes the CLI without an injected client, owned by
  `030-cli.md`. This is the decisive API-to-client-to-CLI check; fake-client
  tests remain supplementary only.
- Public guidance matching the shipped contract: inspection of the updated
  maintained API, client, and CLI documentation after implementation.