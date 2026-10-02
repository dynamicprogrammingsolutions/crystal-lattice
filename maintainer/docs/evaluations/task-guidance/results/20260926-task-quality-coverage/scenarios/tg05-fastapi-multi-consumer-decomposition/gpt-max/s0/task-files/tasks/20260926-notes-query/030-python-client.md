# Expose notes-query through the reusable Python client

Map the approved notes-query contract onto `NotesClient` while keeping the
existing no-argument `list_notes()` call compatible.

## Requirements checklist

- [ ] P1. `NotesClient.list_notes(...)` accepts the approved query options and
  serializes them to the documented HTTP request.
- [ ] P2. `list_notes()` with no arguments continues to request `/notes/`
  without query parameters and returns the current list-compatible result.
- [ ] P3. Client tests cover option mapping, omission of unset values, response
  decoding, and no-argument regression behavior.
- [ ] P4. The package README documents the verified query interface and
  compatibility behavior.

Parent Task: `tasks/20260926-notes-query/000-main.md`

Depends On:

- `tasks/20260926-notes-query/010-contract.md`
- `tasks/20260926-notes-query/020-api.md`

## Scope

This task owns the reusable package API and HTTP request serialization. It
does not own FastAPI query semantics or CLI option parsing. It must consume
the frozen contract rather than expose package-specific names that diverge
from the public HTTP interface without a documented reason.

## Supporting facts

- `NotesClient` accepts an injected transport and has a
  `from_environment()` constructor that creates an `httpx.Client`.
- The current implementation calls `transport.get("/notes/").json()` with no
  arguments.
- The existing client test uses a minimal recording-compatible transport but
  does not assert the requested path or query parameters.

## Execution plan

Status: Draft

After the contract and service are stable, extend `list_notes` with the
approved, clearly named options. Build request parameters from values actually
supplied by the caller so the zero-argument call remains an unparameterized
request. Preserve the client’s direct JSON decoding unless the approved
response contract requires a deliberately documented result model or
envelope.

Expand the client tests with a recording transport that captures path and
keyword arguments. Assert exact serialization and URL-safe handling for each
query option, omission of unset values, decoding of the approved response,
and the unchanged no-argument behavior. Keep one focused client test per
mapping concern; the full service connection is verified by the CLI
integration task.

### Implementation decisions and open questions

The method signature and return type are public package behavior. They remain
blocked on the approved response and option contract. Do not add a second
method or silently change the no-argument return type to make pagination
metadata convenient.

The transport abstraction should remain usable for existing callers. Any
change needed to support a real-path integration test must preserve the
constructor and environment behavior unless the contract explicitly approves
an additive compatibility change.

### Documentation

- Update `packages/notes_client/README.md` with the verified method signature,
  option semantics, response handling, and no-argument compatibility.
- Link to the maintained query contract where appropriate.
- Do not state support until the client tests and dependent service behavior
  are verified.

### Task checklist

- [ ] Confirm the approved HTTP contract and service behavior.
- [ ] Extend `NotesClient.list_notes(...)` with the approved options.
- [ ] Add serialization and no-argument regression tests.
- [ ] Run the package-focused suite and record evidence.
- [ ] Update the package README with current behavior.

### Requirement verification

- P1: Client tests with a recording transport assert the exact path and query
  mapping for every approved option.
- P2: A no-argument test asserts the path `/notes/`, absence of query
  parameters, and the existing list-compatible decoded result.
- P3: The package test suite must collect and pass with the real client class,
  not only a fake client.
- P4: Review the package README against the approved contract and passing
  tests.