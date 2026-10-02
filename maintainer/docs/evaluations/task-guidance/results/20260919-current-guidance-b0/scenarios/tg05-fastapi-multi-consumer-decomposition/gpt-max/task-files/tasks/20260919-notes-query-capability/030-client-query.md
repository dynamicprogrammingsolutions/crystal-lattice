# Expose notes queries through the reusable Python client

Parent Task: `tasks/20260919-notes-query-capability/000-main.md`

Depends On:
`tasks/20260919-notes-query-capability/010-public-contract.md`,
`tasks/20260919-notes-query-capability/020-api-query.md`

Map the approved notes-query contract into the independently maintained
`NotesClient` package without breaking existing callers of `list_notes()`.

## Requirements checklist

- [ ] `NotesClient.list_notes()` exposes the approved pagination, sorting, and
  text-filter controls using the public client surface.
- [ ] The client serializes only the approved query values and preserves the
  service's response shape.
- [ ] Existing `list_notes()` calls with no arguments remain valid and retain
  their current list-shaped behavior and request compatibility.
- [ ] Client tests cover argument mapping, omitted parameters, and the real
  service contract where integration coverage is needed.

## Unresolved requirement questions

The client method names, optional argument names, return shape, and invalid
input behavior remain blocked on the approved contract in
`tasks/20260919-notes-query-capability/010-public-contract.md`.

## Research and supporting facts

- `packages/notes_client/notes_client/client.py` currently accepts a transport
  and calls `get("/notes/")` without query parameters.
- The transport test fixture only returns an empty list and does not currently
  assert the requested path or query mapping.
- `packages/notes_client/README.md` documents only the no-argument method.

## Execution plan

Status: Draft

After the API contract and service behavior are available, extend
`list_notes()` with optional arguments that map one-to-one to the approved
public query controls. Preserve the no-argument call path, then add focused
transport tests for serialization and an integration check against the service
for response handling.

### Implementation decisions and open questions

- The client should not reimplement filtering, sorting, or pagination; it
  should send the approved query to the service.
- Omitted optional arguments must remain omitted from the request so an old
  no-argument caller does not receive an implicit client-side page.
- Whether the client validates locally or relies on API validation must follow
  the approved error contract; avoid silently accepting values the API rejects.
- Keep the existing injected transport seam for unit tests, while adding a
  real service-backed check for the public mapping.

### Documentation

- Update `packages/notes_client/README.md` with the approved method signature,
  query examples, response behavior, and no-argument compatibility.
- Link to the shared notes-query contract if it is created.
- Do not document unimplemented arguments while the plan remains a draft.

### Task checklist

- [ ] Add the approved optional query arguments to `list_notes()`.
- [ ] Serialize omitted and supplied values according to the contract.
- [ ] Preserve the existing no-argument request and return behavior.
- [ ] Add transport-level tests that assert exact query mapping.
- [ ] Add service-backed client coverage for the approved response and errors.
- [ ] Update package documentation after behavior is verified.

### Requirement verification

- [ ] A client test proves each pagination, sort, and filter control reaches
  the service using the contract's parameter names and values.
- [ ] A client compatibility test calls `list_notes()` with no arguments and
  proves the existing list-shaped result remains available.
- [ ] A client/service integration test proves the client can consume the
  API's approved response and validation behavior without a test-only response
  adapter.

### Additional implementation verification

- [ ] Verify the package's public import surface and dependency metadata still
  support the CLI's production import path.
- [ ] Verify URL/query encoding for text filters and omitted values.