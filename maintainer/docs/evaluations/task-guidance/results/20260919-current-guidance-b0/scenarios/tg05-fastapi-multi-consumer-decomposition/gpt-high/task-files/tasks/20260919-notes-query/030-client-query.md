# Expose notes-query through the reusable Python client

Extend the independently maintained Python client to consume the approved
notes-query contract while preserving its existing no-argument behavior.

Parent Task: tasks/20260919-notes-query/000-main.md
Depends On: tasks/20260919-notes-query/010-contract-and-specification.md
Depends On: tasks/20260919-notes-query/020-api-query.md

## Requirements checklist

- [ ] Add client arguments matching the approved pagination, sorting, and
      filtering contract.
- [ ] Serialize supported values to the agreed HTTP query parameters without
      sending unsupported or unset values.
- [ ] Preserve `NotesClient.list_notes()` with no arguments, including its
      current return compatibility.
- [ ] Surface service validation/errors consistently with existing transport
      behavior or the approved client contract.
- [ ] Add client tests for request construction, result handling, and
      no-argument compatibility.

## Supporting facts

`NotesClient.list_notes()` currently calls `self.transport.get("/notes/")`
without parameters and returns `.json()` unchanged. Its tests use a fake
transport and currently assert only that the result is a list.

## Execution plan

Status: Draft

1. Map the approved HTTP contract to a small, explicit `list_notes()` client
   signature or query object.
2. Preserve the no-argument call path and avoid changing its return shape
   unless the approved compatibility contract requires a documented adapter.
3. Add focused fake-transport tests that assert exact URL parameters and
   verify omitted values are not serialized.
4. Add a client integration check against the real service if needed to
   validate response decoding beyond request construction.
5. Update the client README with supported arguments and examples after
   service behavior is verified.

### Implementation decisions and open questions

- Decision: the client is a consumer of the approved HTTP contract, not a
  second source of query semantics.
- Open: exact signature, return type for parameterized requests, and error
  handling depend on the contract task.

### Documentation

Update `packages/notes_client/README.md` to describe the supported
`list_notes()` query controls, no-argument compatibility, and any documented
response/exception behavior. Keep examples aligned with the API contract.

### Task checklist

- [ ] Implement approved client query mapping.
- [ ] Add request serialization and compatibility tests.
- [ ] Verify client behavior against the API contract.
- [ ] Update and review the client README.

### Requirement verification

- Parameter mapping is proven by a fake transport that records the actual
  request path and query values.
- No-argument compatibility is proven by the existing public call shape and
  result assertion.
- At least one supported query is proven through the real service/client
  boundary if response decoding or metadata makes mocks insufficient.

### Additional implementation verification

- Check default omission versus explicit default values according to the
  contract.
- Check client behavior for API validation errors and empty result pages.