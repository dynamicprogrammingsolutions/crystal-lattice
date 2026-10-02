# Add notes-query support to the reusable Python client

Map the finalized service query contract into `NotesClient.list_notes()` while
preserving the existing no-argument call and decoded list behavior.

Parent Task: tasks/20260919-notes-query/000-main.md
Depends On: tasks/20260919-notes-query/010-service-contract-and-api.md

## Requirements checklist

- [ ] Expose the approved pagination, filtering, and sorting controls through
      `NotesClient.list_notes()` using stable, documented Python arguments.
- [ ] Encode only supplied options in the HTTP request according to the
      finalized service contract.
- [ ] Preserve the existing no-argument request to `/notes/` and its returned
      JSON list behavior.
- [ ] Add focused tests for request encoding, omitted/default options, and
      response pass-through without replacing the service-boundary evidence.
- [ ] Update the package README with supported usage and compatibility notes.

## Open requirement questions and material design decisions

The client subtask depends on the parent-approved HTTP names, bounds,
defaults, filter/sort semantics, and no-argument compatibility rule. The
remaining public decision is whether invalid client values are rejected
locally or delegated to the service; the executor must align this with the
approved cross-boundary error contract rather than inventing a second one.

## Supporting facts

`NotesClient.list_notes()` currently accepts no arguments and calls
`transport.get("/notes/")`; the package test transport accepts arbitrary
keyword arguments but does not inspect them. The package has no models or
pagination wrapper, so introducing a response envelope would be a new public
surface and is not required by the current request.

## Execution plan

Status: Draft

After subtask 010 finalizes the HTTP contract, choose Python signatures that
make the supported options discoverable and preserve `list_notes()` with no
arguments. Build query parameters without sending absent options, delegate
validation consistently with the service contract, and return the decoded
list unchanged. Extend the transport fixture to capture path and parameters,
then use a real client-to-service test where needed to prove the mapping is
usable beyond a mocked transport.

### Implementation decisions and open questions

- The client must follow the service contract from
  `tasks/20260919-notes-query/010-service-contract-and-api.md`; it must not
  reinterpret filter, sort, or pagination semantics.
- Invalid-value handling depends on the approved public error contract.
  Preserve one predictable behavior and document it.
- The no-argument method call is a compatibility requirement, including its
  existing list return type.

### Documentation

Update `packages/notes_client/README.md` with the finalized method signature,
query examples, supported bounds/options, and an explicit note that the
no-argument method retains its existing behavior. Keep examples synchronized
with the service README.

### Task checklist

- [ ] Copy the approved service contract into the client API design.
- [ ] Extend `NotesClient.list_notes()` and encode supplied query options.
- [ ] Preserve and test the no-argument transport call and list return shape.
- [ ] Test each supported option and combinations at the client transport
      boundary, including validation behavior.
- [ ] Add or run a real service-backed client check for the finalized mapping.
- [ ] Update package documentation.
- [ ] Hand the stable client surface to
      `tasks/20260919-notes-query/030-cli-production-path.md`.

### Requirement verification

- [ ] Client capability: tests capture the actual transport call and prove
      each approved option is encoded with the service's names and values.
- [ ] Compatibility: `list_notes()` without arguments calls `/notes/` without
      query parameters and returns the decoded list as before.
- [ ] Cross-boundary mapping: a real client request against the FastAPI
      service produces the documented filtered/paginated/sorted results.