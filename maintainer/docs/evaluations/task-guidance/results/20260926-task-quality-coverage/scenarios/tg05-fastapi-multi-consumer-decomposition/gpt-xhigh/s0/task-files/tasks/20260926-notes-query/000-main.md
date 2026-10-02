# Notes-query capability across API, client, and CLI

Plan and coordinate one supported notes-query capability across the FastAPI
service, reusable Python client, and CLI without changing existing
unparameterized behavior.

## Requirements checklist

- [ ] Define and review one stable public query contract covering bounded
  pagination, deterministic sorting, optional text filtering, valid ranges,
  defaults, and invalid-input behavior.
- [ ] Extend the public notes collection API with that contract while keeping
  an unparameterized `GET /notes/` compatible with its current bare-list,
  all-notes behavior.
- [ ] Extend `NotesClient.list_notes()` with the same capability while keeping
  a no-argument call compatible with its current list return value and request.
- [ ] Extend `notes list` with the same capability while keeping the existing
  no-option command behavior and output compatible.
- [ ] Do not begin consumer implementation against an unstable contract; the
  API contract must be reviewed and documented before the client and CLI
  depend on it.
- [ ] Prove the complete CLI-to-production-client-to-service path for a
  parameterized query without injecting the CLI's test fake client.

## Scope and workstreams

The parent task coordinates three independently acceptable boundaries:

1. The HTTP contract and service/storage query implementation.
2. The reusable Python client interface and request mapping.
3. The CLI interface and the live client-to-service proof.

Documentation and focused verification stay with the workstream that owns the
public behavior. No application, package, or documentation implementation is
authorized by this draft.

## Requirement questions and scope decisions

These are material public-contract questions and must be answered or explicitly
accepted before the plan becomes `Approved`:

- Should query parameters be added to the existing `GET /notes/` route
  (recommended for path compatibility), or should a separate route be
  introduced?
- Should parameterized responses remain bare JSON arrays (recommended because
  both the existing client and CLI consume lists), or should pagination add
  metadata and therefore introduce a new response shape?
- What are the canonical names and semantics for pagination, sorting, and
  filtering? A concrete recommendation to review is `limit` plus `offset`,
  an allow-listed sort field plus direction, and a text query applied as a
  case-insensitive substring over title and description.
- What maximum page size, default values, allowed sort fields/directions, and
  invalid-input responses are part of the contract?
- What deterministic tie-breaker is required for equal sort values? The
  current schema has no timestamp, so `id` is the available stable secondary
  key and is the recommended tie-breaker.
- Should CLI flags mirror the HTTP/client names exactly, and should
  parameterized output remain one `id: title` line per note?

The recommendations above are planning proposals, not completed requirements.
No consumer-specific interpretation should be added until they are settled.

## Research and supporting facts

- `src/app/api/notes.py` exposes `GET /notes/` and currently returns
  `crud.get_all()` directly.
- `src/app/api/crud.py` currently selects every row without filtering,
  ordering, or bounds. The table contains only `id`, `title`, and
  `description`.
- `packages/notes_client/notes_client/client.py` currently calls
  `transport.get("/notes/").json()` with no parameters, and its test asserts a
  list result.
- `apps/notes_cli/cli.py` currently iterates `list_notes()` and prints
  `id: title`. Its existing test supplies an injected fake client; it does not
  exercise `NotesClient.from_environment()` or an HTTP service.
- `docs/development/index.md` records that no notes-query specification
  exists. The root README and both package READMEs describe the current
  unparameterized behavior.

## Subtasks

- [ ] `tasks/20260926-notes-query/010-public-api-contract-and-service.md`
- [ ] `tasks/20260926-notes-query/020-reusable-client.md`
- [ ] `tasks/20260926-notes-query/030-cli-and-production-path.md`

## Execution plan

Status: Draft

The API workstream owns the canonical contract. It must settle the route,
parameter, response, validation, ordering, and filter semantics, publish the
reviewable contract, and verify the service behavior before the client task
starts. The client then maps that contract without changing the result shape.
The CLI follows the same contract and must exercise a real
`NotesClient.from_environment()` against a running service, rather than
proving only an injected fake-client seam.

Compatibility is handled at the no-argument boundary: no query options mean
the existing API list response, client list return, and CLI output remain in
force. Parameterized calls add bounded selection, deterministic order, and
filtering under the one agreed contract. The exact parameter names and
semantics remain open until the contract questions above are resolved.

Ordered execution:

1. Resolve the public-contract questions and record the accepted contract in
   the API workstream. Keep the plan in `Draft` until that review is complete.
2. Execute the API workstream, including service/storage behavior, API
   compatibility coverage, and maintained contract documentation.
3. After the API contract and its decisive integration evidence are accepted,
   execute the reusable-client workstream and verify exact request mapping and
   no-argument compatibility.
4. Execute the CLI workstream against the agreed client interface, preserve
   existing output for an unparameterized command, and run the live
   client-to-service check.
5. Update all affected maintained READMEs and development documentation,
   execute the focused tests plus the cross-boundary check, and record any
   deferred scope without silently changing the contract.

### Implementation decisions and open questions

- Contract ownership is assigned to the public API workstream.
- The existing `/notes/` collection path is the recommended compatibility
  boundary; the route choice and response shape still require approval.
- `id` is the recommended deterministic secondary ordering key because the
  current data model has no creation timestamp.
- The client and CLI are explicitly dependent on the reviewed API contract.
- The exact query vocabulary, bounds, filter semantics, and CLI mapping remain
  unresolved as listed above.

### Documentation

- The service workstream should add or update the maintained notes-query
  contract under `docs/development/` and link it from the development index,
  plus update the root service README where public API behavior is described.
- The client workstream should update `packages/notes_client/README.md` with
  the supported method arguments and no-argument compatibility.
- The CLI workstream should update `apps/notes_cli/README.md` with its flags,
  output behavior, and an example of the supported query.
- No current-behavior documentation is changed during this planning-only
  step; target-only material must remain visibly non-current until implemented.

### Task checklist

- [ ] Resolve the contract questions and obtain approval to execute.
- [ ] Complete `010-public-api-contract-and-service.md`.
- [ ] Complete `020-reusable-client.md` after the API contract gate.
- [ ] Complete `030-cli-and-production-path.md` after the client contract gate.
- [ ] Run the named API, client, and CLI evidence and update requirement
  status from that evidence.
- [ ] Record completion notes only after all approved requirements are met.

### Requirement verification

- Canonical contract, bounded service query, stable ordering, text filtering,
  and unparameterized API compatibility: owned by
  `010-public-api-contract-and-service.md`; decisive evidence is an API
  integration test through `TestClient` and the real database adapter with
  records spanning page boundaries, sort ties, filter matches, and invalid
  bounds.
- Reusable-client capability and no-argument compatibility: owned by
  `020-reusable-client.md`; evidence must verify the public method's exact
  request mapping and list return, with at least one check against the
  agreed service contract rather than only a response-shaped mock.
- CLI capability and preserved output: owned by
  `030-cli-and-production-path.md`; evidence must invoke the CLI without an
  injected client, use `NotesClient.from_environment()` over HTTP to a
  running notes service, and assert the parameterized result.
- Contract stability before consumer reliance: requires human review of the
  accepted contract and the API workstream's documented/integration-tested
  result before the client or CLI workstreams are marked executable.

### Additional implementation verification

- Run the focused tests for each subsystem and the full cross-boundary CLI
  check after implementation. No repository tests are run by this planning
  task.
