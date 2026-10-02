# Add a stable notes-query capability across consumers

Plan-only handoff for adding one notes-query capability to the FastAPI service,
the reusable Python client, and the CLI. The capability must support bounded
pagination, deterministic sorting, and optional text filtering without changing
the existing no-argument API or client behavior.

## Requirements checklist

- [ ] The public notes-query capability supports bounded pagination, stable
  sorting, and optional text filtering through the service, reusable client,
  and CLI.
- [ ] The unparameterized `GET /notes/` API remains a JSON list containing the
  current unparameterized collection behavior.
- [ ] The unparameterized `NotesClient.list_notes()` call remains valid and
  returns the same list-shaped result without requiring callers to change.
- [ ] A single public contract defines the HTTP parameters, response shape,
  validation and error behavior, sort stability, filtering semantics, client
  method surface, and CLI controls before consumer implementations depend on
  it.
- [ ] The CLI has evidence for the production client-to-service path: its
  query operation reaches the real reusable client and the real notes service,
  rather than only a fake client or an isolated formatter.

## Scope and workstreams

The work is deliberately split at the public compatibility boundaries:

1. Establish and review the shared contract.
2. Implement and test the service query behavior.
3. Expose the same contract through `NotesClient`.
4. Expose the same controls through the CLI and verify the end-to-end path.

The feature implementation, maintained user documentation, and test changes
are execution work. This handoff creates no implementation and does not
authorize execution while the plan is still `Draft`.

## Subtasks

- [ ] `tasks/20260919-notes-query-capability/010-public-contract.md`
- [ ] `tasks/20260919-notes-query-capability/020-api-query.md`
- [ ] `tasks/20260919-notes-query-capability/030-client-query.md`
- [ ] `tasks/20260919-notes-query-capability/040-cli-integration.md`

## Unresolved requirement questions

These questions affect public behavior and must be answered before the contract
subtask is approved:

- Should pagination use `limit` plus `offset`, `page` plus `page_size`, or
  another model? What are the default, minimum, and maximum bounds, and should
  a parameterized response remain a raw list or include metadata such as a
  total/count or continuation information?
- Which note fields may be sorted, how is direction expressed, what is the
  default order, and which deterministic tie-breaker is required when sort
  values are equal?
- Does text filtering search title, description, or both? Is matching
  substring-based, case-sensitive, and how should an empty filter be treated?
- What validation and error contract applies to invalid bounds, sort fields or
  directions, and filter values?
- Which names and output behavior should the CLI use for the query controls?
  Should it expose every HTTP/client control, and if a response envelope is
  chosen, how should pagination metadata be presented without changing the
  current no-flag output?

### Recommendation for contract review

Use one bounded `limit`/`offset` model, whitelist a small set of sort fields
with an explicit direction and an `id` tie-breaker, and use one optional
case-insensitive text query over the user-facing note text. Keep the response
list-shaped unless consumers need pagination metadata; if metadata is needed,
decide whether it is added only for parameterized requests or introduced
through an explicit compatibility-safe envelope. These are recommendations,
not approved requirements.

## Research and supporting facts

- `src/app/api/notes.py` currently exposes `GET /notes/` without query
  parameters and delegates to `crud.get_all()`.
- `src/app/api/crud.py` selects every row without filtering, pagination, or an
  explicit ordering clause. The current database order is therefore not a
  documented stable sort.
- `packages/notes_client/notes_client/client.py` currently defines
  `list_notes(self)` with no arguments and returns the response JSON unchanged.
- `apps/notes_cli/cli.py` currently supports only `notes list`, iterates over
  `client.list_notes()`, and its test fixture supplies a fake client.
- Existing tests are smoke tests: the service checks that the collection is a
  list, the client checks the return type, and the CLI checks that output is
  non-empty. There is no cross-boundary query coverage.
- `docs/development/index.md` states that no notes-query specification exists.
  The root and package READMEs describe the current unparameterized behavior.
- `apps/notes_cli/pyproject.toml` imports `notes_client` in application code
  but does not currently declare a runtime dependency on the client package;
  packaging/installability should be checked as part of the production-path
  verification.

## Execution plan

Status: Draft

The contract subtask gates all consumer work. After the public semantics are
approved, implement the service first, then the reusable client, and finally
the CLI integration. Each layer should be tested at the boundary it owns, with
the CLI receiving an additional end-to-end test that uses the production
`NotesClient` against the service application or a real local service endpoint.

The plan should be re-approved if the agreed response shape, public names,
compatibility behavior, or test/deployment boundary changes materially.

### Implementation decisions and open questions

- The public HTTP contract is the source of truth; the client and CLI should
  map to it rather than maintain independent query semantics.
- The API should perform filtering, bounds, and ordering in the database query
  so the behavior remains correct as the collection grows. The implementation
  must add a deterministic secondary ordering key, once the contract names it.
- The no-argument path must remain distinguishable from a parameterized query:
  no-argument callers retain the existing list result and do not silently
  acquire a default page limit.
- The unresolved questions above are contract decisions, not implementation
  details. They remain open until reviewed and recorded by
  `010-public-contract.md`.
- The preferred documentation shape is one focused development contract
  document, with current user guidance updated in the owning root, client, and
  CLI READMEs during implementation. Do not publish target-only behavior in
  current guidance while this plan is still a draft.

### Documentation

- `docs/development/notes-query.md` should become the maintained cross-consumer
  contract if the contract review confirms that a focused document is useful.
  It should define only approved, implemented behavior.
- `README.md` should retain the current API compatibility statement and gain
  concise query guidance once the API is implemented.
- `packages/notes_client/README.md` should document the optional client
  arguments and no-argument compatibility after the client is implemented.
- `apps/notes_cli/README.md` should document the query flags and examples after
  the CLI is implemented.
- `docs/development/index.md` should be updated through its maintained source
  boundary to link the new contract, replacing the current “no specification”
  statement only after the contract exists.

### Task checklist

- [ ] Resolve and record the public contract in
  `tasks/20260919-notes-query-capability/010-public-contract.md`.
- [ ] Implement and test the service behavior through
  `tasks/20260919-notes-query-capability/020-api-query.md`.
- [ ] Implement and test the reusable client mapping through
  `tasks/20260919-notes-query-capability/030-client-query.md`.
- [ ] Implement and test the CLI and production client-to-service path through
  `tasks/20260919-notes-query-capability/040-cli-integration.md`.
- [ ] Update maintained documentation only after the corresponding behavior
  and contract are verified.
- [ ] Run the required boundary tests and record evidence against every
  requirement before marking this task complete.

### Requirement verification

- [ ] Query capability: service integration tests exercise bounded pagination,
  stable sorting including ties, and text filtering; client and CLI tests
  prove those same controls cross their public boundaries.
- [ ] API compatibility: an integration test calls `GET /notes/` with no query
  parameters and verifies the existing list-shaped collection behavior.
- [ ] Client compatibility: a client test calls `list_notes()` with no
  arguments and verifies the existing list-shaped result and request shape.
- [ ] Contract stability: the approved contract document is reviewed before
  client or CLI implementation and matches the final public names, validation,
  response, and compatibility behavior.
- [ ] Production path: an end-to-end CLI test invokes the real CLI operation
  with a real `NotesClient` configured for the service and verifies filtered,
  paginated, sorted output from the service; a fake client remains suitable
  only for narrow formatting tests.

### Additional implementation verification

- [ ] Verify package installation/import metadata for the independently
  maintained client and CLI, including the CLI's runtime dependency on the
  client where required.
- [ ] Verify test data isolation so persisted notes from one query scenario do
  not affect another.
- [ ] Verify invalid query inputs at the public API boundary and confirm the
  client/CLI surface reports the agreed errors without inventing alternate
  semantics.