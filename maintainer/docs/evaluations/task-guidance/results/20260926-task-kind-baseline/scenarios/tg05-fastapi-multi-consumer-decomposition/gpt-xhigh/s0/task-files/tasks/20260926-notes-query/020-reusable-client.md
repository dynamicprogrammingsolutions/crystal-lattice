# Reusable notes client query support

Expose the agreed notes-query capability through `NotesClient` while keeping
the existing no-argument method and list return behavior compatible.

Parent Task: `tasks/20260926-notes-query/000-main.md`

Depends On: `tasks/20260926-notes-query/010-public-api-contract-and-service.md`

## Requirements checklist

- [ ] Add client arguments that map one-to-one to the reviewed HTTP query
  contract for pagination, sorting, and optional text filtering.
- [ ] Omit unspecified query options so a no-argument call preserves the
  current request and list result.
- [ ] Preserve the existing reusable-client response behavior for both
  unparameterized and parameterized calls.
- [ ] Verify request serialization and response handling against the agreed
  service contract.
- [ ] Document the supported client interface.

## Requirement questions and scope decisions

- The API workstream must settle the exact argument names and response shape
  before this task starts.
- Confirm whether client-side validation should mirror the HTTP bounds or
  leave all validation to the service; the client must not silently create a
  second contract.
- Confirm whether the public method should use explicit keyword-only query
  arguments to avoid positional ambiguity.

## Research and supporting facts

- `NotesClient.list_notes()` currently takes no arguments and calls
  `transport.get("/notes/").json()`.
- The package test transport accepts `**kwargs` but does not currently record
  them, so serialization evidence must be added.
- The package README currently promises only the unparameterized collection.

## Execution plan

Status: Draft

After the API contract gate passes, extend `list_notes()` with the canonical
query options and serialize only values the caller supplied. Keep the
no-argument branch equivalent to the current `get("/notes/")` call so existing
transports and callers continue to work. Do not add client-specific defaults,
sort semantics, or filter interpretation that differ from the HTTP contract.

Use a recording transport test for exact URL/parameter mapping and omission of
unset options. Add a contract-level check using the real service boundary
where feasible, ensuring a parameterized call returns the same list-shaped
data the service documents. Preserve a no-argument regression test. Update the
package README after the API contract is current.

### Implementation decisions and open questions

- This task consumes, rather than defines, the HTTP query vocabulary.
- The method should retain a list return unless the approved API contract
  explicitly introduces metadata.
- Keyword-only arguments are recommended for a stable Python interface, but
  the public signature remains subject to contract review.
- Validation ownership must be aligned with the API; no independent client
  semantics should be introduced.

### Documentation

- Update `packages/notes_client/README.md` with the method signature,
  supported options, list return behavior, and a query example.
- Keep no-argument usage documented as the compatibility path.

### Task checklist

- [ ] Confirm the API contract gate is complete.
- [ ] Implement client argument and query serialization.
- [ ] Add request-mapping, response, and no-argument regression tests.
- [ ] Update the client README.
- [ ] Report evidence before the CLI task starts.

### Requirement verification

- Client capability: a public `NotesClient` test must call the method with
  each supported option and assert the exact request parameters sent to the
  transport.
- Client compatibility: a no-argument public method test must assert the
  existing path, no unexpected parameters, and list return.
- API alignment: at least one test must use the accepted service contract or
  the full CLI live-path check must include a parameterized call through this
  production client implementation.

### Additional implementation verification

- Run the package's focused test suite and verify that omitted options do not
  become accidental `null` or default query parameters.
