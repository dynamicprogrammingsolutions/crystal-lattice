# Notes query across API, client, and CLI

Plan and coordinate one supported notes-query capability across the public
FastAPI service, reusable Python client, and CLI without implementing it in
this planning task.

## Requirements checklist

- [ ] Define and record one stable public query contract before implementing
      consumer-facing API, client, or CLI changes.
- [ ] Support bounded pagination, stable sorting, and optional text filtering
      through the public notes API.
- [ ] Preserve the current unparameterized API behavior, including acceptance
      of an unparameterized collection request and its current response
      compatibility.
- [ ] Expose the same query capability through the reusable Python client
      while preserving the current no-argument `list_notes()` behavior.
- [ ] Expose the supported query controls through `notes list`.
- [ ] Prove the CLI-to-service path with the production client and a real HTTP
      service boundary, not only injected fakes or a test-only client shortcut.
- [ ] Add focused evidence for API compatibility, client compatibility, query
      semantics, and the CLI production path.
- [ ] Update maintained documentation at the owning API, client, and CLI
      boundaries once the behavior is implemented and verified.

## Open requirement questions

These questions affect the public contract and must be answered before the
contract subtask is approved for implementation:

1. Which pagination vocabulary and bounds are required: offset plus limit,
   page plus page size, or another model; what are the defaults, maximums, and
   invalid-value responses?
2. Which sort keys and directions are public, what is the default order, and
   what deterministic tie-breaker guarantees stable results when primary sort
   values match?
3. What text does the filter search (title, description, both, or another
   field set), and is matching case-sensitive, substring-based, or otherwise
   normalized?
4. Does a parameterized response remain a bare note array for compatibility,
   or does the contract introduce pagination metadata; if metadata is added,
   how is the unparameterized response kept compatible?
5. How should client method arguments map to the HTTP contract, and what CLI
   option names/output behavior are part of the supported interface?

## Supporting facts

- The collection route is `GET /notes/` in `src/app/api/notes.py` and
  currently returns `crud.get_all()` directly.
- `src/app/api/crud.py` currently issues an unordered `notes.select()` with no
  filtering or bounds.
- The current API test only asserts that an unparameterized collection request
  returns a list; it does not establish ordering or query semantics.
- `packages/notes_client/notes_client/client.py` has a synchronous
  `NotesClient.list_notes()` that performs `GET /notes/` and returns the JSON
  value unchanged.
- `packages/notes_client/tests/test_client.py` uses a fake transport and
  establishes only the current list return type.
- `apps/notes_cli/cli.py` exposes `notes list`, delegates to
  `NotesClient.list_notes()`, and currently accepts an injectable client;
  its test uses a fake client rather than the production HTTP transport.
- Maintained package READMEs currently describe only unparameterized
  collection behavior. `docs/development/index.md` says no notes-query
  specification exists.
- No `tasks/` structure existed before this handoff.

## Scope and sequencing

The work is decomposed by compatibility boundary. The contract subtask owns
the public vocabulary and response semantics first. The API subtask then
implements and tests the service behavior, followed by the reusable client and
CLI. The final subtask checks the cross-boundary path and updates owned
documentation. The CLI integration evidence must exercise the production
client against an actual HTTP service instance.

Out of scope unless the contract questions explicitly expand it: changing
create/read/update/delete behavior, introducing authentication, changing note
storage fields, or redesigning unrelated command output.

## Execution plan

Status: Draft

1. Resolve the open contract questions and write a maintained notes-query
   specification before consumer implementation. The specification must define
   parameter names, defaults and bounds, validation/error behavior, filtering
   semantics, ordering and tie-breaking, response shape, and compatibility
   rules.
2. Implement the API query behavior against the real database query boundary.
   Preserve the no-parameter path and add service-level tests for pagination,
   filtering, deterministic ordering, validation, and compatibility.
3. Update `NotesClient.list_notes()` to accept the agreed query controls,
   serialize only supported parameters, and preserve the existing no-argument
   return behavior. Test both request construction and the public result
   contract.
4. Add the agreed `notes list` options and output handling. Retain the
   injectable client seam for focused CLI tests, then add an integration test
   that invokes the CLI with the production `NotesClient` against a real
   service endpoint.
5. Run the relevant API, client, CLI, and cross-boundary test suites; update
   the API/developer documentation and both package READMEs only with verified
   supported behavior.

### Implementation decisions and open questions

- Decision: use a main task with ordered subtasks because the request spans
  three independently maintained public consumers plus a shared contract.
- Decision: keep this handoff in `Draft`; creating task files does not
  authorize implementation.
- Open: the five contract questions above must be resolved before marking the
  contract task complete or approving downstream implementation.
- Recommendation: make the stable sort explicit in the contract and test it
  through the service rather than relying on database default row order.

### Documentation

- Contract/specification ownership: repository development documentation,
  using the smallest maintained page that makes the public query semantics
  reviewable before implementation.
- API behavior: document the verified HTTP query parameters, response shape,
  compatibility behavior, and validation at the API-facing documentation
  boundary.
- Reusable client: update `packages/notes_client/README.md` with the accepted
  method arguments and no-argument compatibility.
- CLI: update `apps/notes_cli/README.md` with supported options and examples
  only after the production path is verified.
- Do not present target behavior as current guidance before implementation;
  the specification may describe the approved target while implementation is
  pending.

### Task checklist

- [ ] Complete `tasks/20260919-notes-query/010-contract-and-specification.md`.
- [ ] Complete `tasks/20260919-notes-query/020-api-query.md`.
- [ ] Complete `tasks/20260919-notes-query/030-client-query.md`.
- [ ] Complete `tasks/20260919-notes-query/040-cli-query.md`.
- [ ] Complete `tasks/20260919-notes-query/050-cross-boundary-verification-and-docs.md`.
- [ ] Reconcile requirement evidence and parent status after all subtasks.

### Requirement verification

- Contract stability: approved maintained specification reviewed before
  consumer implementation; cite the final specification and review decision.
- API capability and compatibility: integration tests against the FastAPI
  route and database prove bounded pagination, stable sorting, optional
  filtering, validation, and the unchanged unparameterized path.
- Client capability and compatibility: client tests prove the agreed
  parameter serialization and that `list_notes()` without arguments retains
  its current public result behavior.
- CLI capability and production path: an integration test invokes the CLI
  with the production client configured for a real HTTP service and verifies
  query options and output.
- Documentation: inspect the maintained API/developer and package docs for
  claims matching the verified contract.

### Additional implementation verification

- Run the repository’s relevant test commands with the service lifecycle
  enabled so the evidence crosses the actual transport boundary.
- Check invalid and boundary values at the public API/client/CLI interfaces
  consistently, especially maximum page size and empty result behavior.