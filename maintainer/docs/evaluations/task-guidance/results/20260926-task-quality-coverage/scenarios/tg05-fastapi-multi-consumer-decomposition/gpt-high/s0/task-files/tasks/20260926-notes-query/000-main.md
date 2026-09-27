# Notes query capability across API, client, and CLI

Plan and coordinate one supported notes-query capability across the public
FastAPI service, reusable Python client, and notes CLI, without implementing
the capability in this planning task.

## Requirements checklist

- [ ] The public notes API supports bounded pagination, stable sorting, and
      optional text filtering through one documented query contract.
- [ ] The existing unparameterized `GET /notes/` behavior remains compatible:
      it continues to return the current collection representation, and its
      default ordering is explicitly defined and stable.
- [ ] The reusable `notes-client` package exposes the same query capability
      while preserving the current no-argument `NotesClient.list_notes()`
      behavior and return contract.
- [ ] The `notes list` CLI exposes the supported query capability while
      preserving the current no-option command behavior.
- [ ] The public API contract is settled and documented, with API-level
      regression evidence, before client or CLI consumers are implemented
      against it.
- [ ] The CLI is verified through its production client-to-service path:
      the CLI entry point uses the real `NotesClient`, which makes a real
      request to the running notes service; a fake/injected client is not the
      decisive integration evidence.
- [ ] Maintained documentation for the service, client, and CLI describes the
      resulting supported behavior in the same reviewed change as its
      implementation.

## Open requirement questions

These choices change the public contract and must be answered before the
execution plan is approved:

1. What are the pagination parameter names and semantics? A concrete
   recommendation is `limit` plus `offset`, with a positive bounded `limit`,
   `offset >= 0`, and a documented maximum; the required default limit and
   maximum still need approval.
2. Which sort fields and direction syntax are public? A concrete
   recommendation is an allowlisted note field (at least `id` and `title`),
   ascending/descending direction, and `id` as the deterministic secondary
   key for every sort. The exact parameter names and allowlist need approval.
3. What text does the filter search—title only, description only, or both—and
   what matching rules (case sensitivity and substring/token behavior) are
   required?
4. Should parameterized responses remain JSON arrays, preserving the current
   client return type, or should pagination metadata be added in an envelope?
   Keeping arrays for all modes is the compatibility-preserving
   recommendation, but it does not expose a total count or continuation
   marker.
5. What CLI option names and invalid-input behavior should be public? The
   corresponding recommendation is long options mirroring the approved API
   names, with argparse validation and a nonzero command failure for invalid
   values.

Until these are answered, the requirements above intentionally do not assert
specific parameter names, limits, sort fields, matching rules, or response
metadata.

## Scope and exclusions

In scope are the existing notes collection route, the existing
`NotesClient.list_notes()` surface, the existing `notes list` command, their
focused tests, and the maintained documentation that describes them. This
plan does not add a new notes resource, cursor protocol, authentication
scheme, bulk operation, or unrelated package restructuring. It also does not
authorize implementation until the draft contract questions are resolved and
the plan is approved.

## Supporting facts

- The service currently exposes `GET /notes/` at `src/app/api/notes.py` and
  returns `crud.get_all()` as a bare JSON collection.
- `src/app/api/crud.py` currently performs an unbounded database select with no
  explicit ordering or filtering.
- `packages/notes_client/notes_client/client.py` currently sends
  `GET /notes/` with no parameters and returns the decoded JSON unchanged.
- `apps/notes_cli/cli.py` currently accepts only `notes list`, calls
  `NotesClient.from_environment()` when no client is injected, and prints each
  note's id and title.
- Existing tests separately cover the route shape, client list return type, and
  CLI rendering. They do not cross the service, reusable client, and CLI
  production path.
- `docs/development/index.md` records that no notes-query specification exists.
  The repository has package-local READMEs but no existing public query
  contract to preserve.

## Execution plan

Status: Draft

The service owns query semantics and the compatibility contract. The client
owns the Python representation of that contract and must pass only approved
query values to the service. The CLI owns command-line mapping and user-facing
validation, while delegating retrieval to the production client. The
dependency order is therefore API contract and route evidence, then client
support, then CLI support and a real HTTP end-to-end check.

The contract gate should settle the unresolved questions above, document the
approved wire behavior in the service-owned documentation, and add route-level
tests before client or CLI implementation begins. The route should make
ordering explicit even for an unparameterized request so pagination windows do
not drift between calls; the chosen primary sort must always have a
deterministic tie-breaker. Client and CLI documentation should then mirror the
same approved names and defaults rather than defining parallel behavior.

Ordered execution:

1. Resolve the public contract questions and record the approved parameter,
   validation, response, ordering, filtering, and CLI mapping decisions in the
   API subtask.
2. Implement and test the service query path, including unparameterized
   compatibility, bounded pagination validation, stable ordering, filtering,
   and documented error responses. Complete the API task's decisive
   `TestClient`/route checks before proceeding.
3. Implement the reusable client's query arguments and request encoding,
   retaining the no-argument list behavior. Verify both request construction
   and a client-to-service integration case against the approved route.
4. Implement CLI options by forwarding approved values through
   `NotesClient.list_notes()`, retain `notes list` behavior, and add user-facing
   validation/output coverage.
5. Run the CLI through the installed/production entry point against a running
   notes service, with no injected fake client, and verify that a query option
   changes the service-backed result. Update all affected maintained READMEs
   and run the focused checks plus the repository's relevant test commands.

### Implementation decisions and open questions

- Decision: use one parent task with three subtasks because the HTTP API,
  independently packaged client, and CLI have distinct compatibility and
  acceptance boundaries.
- Decision: order dependencies as API -> client -> CLI; no consumer may
  implement against an unsettled wire contract.
- Decision: make the CLI/service integration check cross the real HTTP
  boundary and use the production client construction path.
- Open: pagination names, defaults, maximum, response metadata, sort syntax
  and allowlist, filter semantics, CLI names, and invalid-input behavior are
  listed in `## Open requirement questions` and require direction before
  approval.

### Documentation

- API subtask: document the approved query contract with the service-owned
  documentation and update the root API description; do not publish target
  behavior as current guidance before implementation is complete.
- Client subtask: update `packages/notes_client/README.md` with the supported
  method arguments, defaults, return shape, and compatibility behavior.
- CLI subtask: update `apps/notes_cli/README.md` with the supported options,
  examples, and failure behavior.
- Keep any new public claims in the same implementation change as the code
  and contract tests. Do not create unrelated placeholder documentation.

### Task checklist

- [ ] Resolve and approve the public query contract.
- [ ] Complete `tasks/20260926-notes-query/010-api-contract-and-service.md`.
- [ ] Complete `tasks/20260926-notes-query/020-python-client.md`.
- [ ] Complete `tasks/20260926-notes-query/030-cli-production-path.md`.
- [ ] Run the decisive checks named by each subtask and record their evidence.
- [ ] Update parent requirement status and append completion notes only after
      all approved outcomes are evidenced.

### Requirement verification

- API pagination, sorting, filtering, validation, and default compatibility:
  the route-level integration test in
  `tasks/20260926-notes-query/010-api-contract-and-service.md` must seed
  notes and exercise the public `GET /notes/` request against the real
  application/database boundary.
- Client capability and no-argument compatibility: the client subtask's
  decisive integration test must invoke `NotesClient.list_notes()` against
  the approved service route and assert both encoded query behavior and the
  unchanged no-argument list result.
- CLI capability and production path: the CLI subtask must run the actual
  `notes` entry point against a running service with the real
  `NotesClient.from_environment()` path and assert the filtered/sorted/page
  output; injected test doubles may cover formatting but cannot satisfy this
  requirement.
- Documentation and contract stability: inspect the final service, client, and
  CLI maintained documentation alongside the contract tests before marking
  the corresponding requirements complete.

### Additional implementation verification

- Verify that stable ordering is explicit in the generated SQL/query rather
  than relying on database insertion order.
- Verify limit bounds and invalid sort/filter inputs at the public boundary,
  including a result set large enough to cross a page boundary.
- Verify the CLI's no-option behavior still reaches the same client method and
  output shape as before.