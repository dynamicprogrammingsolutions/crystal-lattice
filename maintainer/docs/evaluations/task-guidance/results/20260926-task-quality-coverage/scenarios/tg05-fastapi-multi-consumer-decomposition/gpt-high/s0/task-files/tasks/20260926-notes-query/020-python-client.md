# Expose the notes-query contract through the reusable Python client

Add the approved notes-query capability to the independently maintained
`notes-client` package while preserving its current no-argument behavior.

Parent Task: tasks/20260926-notes-query/000-main.md
Depends On: tasks/20260926-notes-query/010-api-contract-and-service.md

## Requirements checklist

- [ ] `NotesClient.list_notes()` exposes the approved pagination, sorting, and
      optional text-filter inputs.
- [ ] The client encodes only approved values and parameter names for the
      service contract.
- [ ] A no-argument `list_notes()` call continues to request the unparameterized
      collection and return the current decoded list behavior.
- [ ] Client documentation describes the supported arguments, defaults,
      response/return shape, and compatibility behavior.
- [ ] Tests cover request encoding, no-argument compatibility, and the client
      against the settled service contract.

## Open requirement questions

- Use the exact API parameter names, defaults, validation, and response shape
  approved by `010-api-contract-and-service.md`; do not resolve a second
  client-specific contract.
- Confirm whether invalid client arguments fail locally, are sent for server
  validation, or follow another approved policy.

## Supporting facts

- The client implementation is `packages/notes_client/notes_client/client.py`.
- It currently calls `self.transport.get("/notes/").json()` and returns the
  decoded value directly.
- Its current test transport records no requests and only proves that the
  result is a list, so it cannot establish query encoding or service
  compatibility by itself.
- The package has its own README and `pyproject.toml`, making its method
  signature and return behavior an independently maintained package boundary.

## Execution plan

Status: Draft

After the API task settles the wire contract, extend `list_notes()` with the
approved optional arguments and construct a query parameter mapping that
omits unset values. Preserve the existing no-argument request and decoded
return path. Apply the approved client-side validation policy without
duplicating server semantics that belong to the HTTP contract.

Retain a focused transport-level test for exact request encoding, then add a
client-to-service integration test that uses the production `NotesClient`
method against the real FastAPI route. The integration evidence must exercise
at least one combined pagination/sort/filter request and the no-argument
compatibility path.

### Implementation decisions and open questions

- The API subtask is the source of truth for query names and response shape.
- Optional values should not appear in the request when omitted, preserving
  the current unparameterized request exactly.
- Whether local argument validation is required remains subordinate to the
  approved contract and error policy.

### Documentation

- Update `packages/notes_client/README.md` with the final method signature or
  invocation examples, query semantics, defaults, return shape, and no-arg
  compatibility.
- Keep package documentation aligned with the service contract; do not
  introduce client-only aliases without an approved compatibility reason.

### Task checklist

- [ ] Consume the settled API contract.
- [ ] Extend `NotesClient.list_notes()` and query encoding.
- [ ] Update transport-level and service integration tests.
- [ ] Update the package README.
- [ ] Run the package tests and decisive client-to-service check.
- [ ] Hand the client invocation contract to the CLI subtask.

### Requirement verification

- Query encoding: a transport-level test must assert the exact path and
  parameter mapping for every approved option and omission of unset values.
- Client compatibility: a no-argument call must still issue the existing
  unparameterized request and return a list.
- Public connection: an integration test must call the real `NotesClient`
  implementation against the implemented FastAPI route and assert the
  filtered, sorted, bounded result; a mocked response alone is not decisive.

### Additional implementation verification

- Confirm the client does not accidentally send `None`, client-only names, or
  an incompatible envelope assumption.
- If the API response shape is an array, preserve the existing direct JSON
  return; if the approved contract uses metadata, document and test the
  resulting intentional compatibility change explicitly.