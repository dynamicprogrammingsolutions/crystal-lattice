# Expose the notes query through the reusable Python client

Mirror the approved notes-query HTTP contract in `NotesClient` so Python
consumers can request bounded pages, stable sorting, and optional text
filtering without constructing query strings themselves.

## Requirements checklist

- [ ] `NotesClient.list_notes()` exposes the approved optional query
  arguments and encodes them using the service contract.
- [ ] `NotesClient.list_notes()` with no arguments preserves the current
  request path and returned JSON array behavior.
- [ ] Client tests cover request encoding, omitted options, and compatibility.
- [ ] Client documentation describes the supported query arguments and
  examples.

Parent Task: tasks/20260925-notes-query-capability/000-main.md

Depends On: tasks/20260925-notes-query-capability/010-api-contract-service.md

## Research and supporting facts

- `packages/notes_client/notes_client/client.py` currently defines only
  `list_notes(self)` and calls `transport.get("/notes/").json()`.
- The package README says the method currently returns the unparameterized
  collection.
- `packages/notes_client/tests/test_client.py` uses a small transport double
  and currently checks only that the result is a list.

## Execution plan

Status: Draft

After the service contract is approved, add optional typed or clearly
documented method arguments matching its names and semantics. Build the
request through the existing transport interface, omitting unspecified
parameters so the no-argument request remains unchanged. Test the method's
request mapping with a capture transport; rely on the CLI integration
subtask for the decisive real client-to-service path.

### Implementation decisions and open questions

The client signature, parameter names, and whether pagination metadata is
returned are determined by the service contract. Do not add client-only
defaults or silently clamp values differently from the service.

### Documentation

Update `packages/notes_client/README.md` with the approved method signature,
query semantics, no-argument compatibility, and a concise usage example.

### Task checklist

- [ ] Confirm the approved service contract from the API subtask.
- [ ] Add optional query arguments and approved request encoding.
- [ ] Preserve the no-argument request and result behavior.
- [ ] Test all supported argument combinations and omitted options.
- [ ] Update the client README.
- [ ] Update the parent task with package evidence and any compatibility
  findings.

### Requirement verification

- Client contract: an argument-capture test asserts that each public client
  option maps to the exact approved HTTP parameter and that unsupported
  values are handled at the documented boundary.
- Compatibility: a no-argument test asserts the transport receives
  `"/notes/"` without query parameters and returns the existing list result.
- Public usage: package tests collect and exit cleanly with the maintained
  client package configuration.

### Additional implementation verification

- Verify omitted optional values are not serialized as misleading empty
  strings or zeroes.
- Verify the client does not duplicate filtering, sorting, or pagination
  locally and therefore remains a reusable HTTP consumer.