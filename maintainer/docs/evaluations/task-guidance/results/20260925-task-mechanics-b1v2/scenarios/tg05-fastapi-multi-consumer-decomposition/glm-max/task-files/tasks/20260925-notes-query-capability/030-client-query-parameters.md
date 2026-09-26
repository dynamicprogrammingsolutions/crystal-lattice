# Add query parameters to the reusable Python client

Mirror the approved notes-query contract as optional keyword arguments on
`NotesClient.list_notes()`, sending only provided values, and keep the
no-argument call identical to today's request.

Parent Task: tasks/20260925-notes-query-capability/000-main.md
Depends On: tasks/20260925-notes-query-capability/010-public-query-contract.md

## Requirements checklist

- [ ] `list_notes()` accepts optional keyword-only `limit`, `offset`,
  `sort`, `order`, and `text`, mirroring the contract.
- [ ] Only provided values are sent; omitted values produce no query
  parameter.
- [ ] The no-argument call issues `GET /notes/` with no query string —
  identical to the current behavior.
- [ ] Component tests with a recording fake transport assert the exact
  request for: each parameter individually, a combined call, and the
  no-argument call.
- [ ] `packages/notes_client/README.md` documents the parameters, and the
  package version is bumped to 0.2.0 (recommended step), in the same
  change.

## Supporting facts

- Current method: packages/notes_client/notes_client/client.py:20 —
  `self.transport.get("/notes/")`.
- The test fake's `get(self, path, **kwargs)`
  (packages/notes_client/tests/conftest.py) already tolerates a `params`
  keyword, so a recording harness can be introduced without breaking the
  existing test.
- The client is independently maintained
  (`packages/notes_client/pyproject.toml`); its compatibility boundary is
  the method signature and the wire request, not the service
  implementation.
- The full production connection (client → service) is proven once in
  subtask 040 and is intentionally not duplicated here.

## Execution plan

Status: Draft

Add the optional keyword-only parameters; build the query-parameter
mapping from provided values only and pass it as `params` to the transport.
Extend the existing fake transport to record `(path, params)` and assert
the request matrix above. Update the README and package version.

### Implementation decisions and open questions

None material. Argument names mirror the approved HTTP contract by design;
the internal mapping construction is a local, reversible choice.

### Documentation

`packages/notes_client/README.md` (client consumers), same change as the
code.

### Task checklist

- [ ] Add keyword-only parameters + params mapping
- [ ] Recording-transport component tests (per-param, combined, no-arg)
- [ ] README + version bump

### Requirement verification

- Decisive at this boundary: recording-fake-transport tests asserting the
  exact request (path and query parameters) for each case, including the
  no-argument regression.
- Regression: existing `test_list_notes` passes unchanged.
- Run: the `packages/notes_client` test suite collects and exits cleanly.

### Additional implementation verification

None planned. URL encoding of `text` values with spaces is exercised on
the production path by the end-to-end test in subtask 040, whose seed data
includes a spaced title.