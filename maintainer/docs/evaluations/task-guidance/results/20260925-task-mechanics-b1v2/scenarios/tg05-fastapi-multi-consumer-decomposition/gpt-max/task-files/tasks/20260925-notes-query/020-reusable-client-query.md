# Expose the notes query through the reusable Python client

Add the approved notes-query controls to `NotesClient` while retaining the
current zero-argument method contract and list return shape.

Parent Task: tasks/20260925-notes-query/000-main.md

Depends On: tasks/20260925-notes-query/010-public-api-contract.md

## Requirements checklist

- [ ] Add optional `list_notes` inputs that map one-to-one to the approved
  HTTP contract and do not introduce client-only query semantics.
- [ ] Keep `list_notes()` with no arguments equivalent to the current
  `transport.get("/notes/").json()` call and list result.
- [ ] Forward only supplied, approved query parameters with the names and
  value types required by the service.
- [ ] Preserve service validation/error behavior rather than silently
  clamping or rewriting unsupported values in the client.

## Unresolved requirement questions

The method argument names, keyword-only/positional shape, and response type
are determined by the approved contract in
`tasks/20260925-notes-query/010-public-api-contract.md`. Do not finalize a
different Python vocabulary or add pagination metadata locally.

## Supporting facts

- `packages/notes_client/notes_client/client.py` currently accepts an
  injected transport and calls `get("/notes/")` without keyword arguments.
- `packages/notes_client/tests/conftest.py` supplies a transport stub whose
  `get` method accepts `**kwargs`, so it can be extended into a request
  recorder without bypassing the client method.
- The package README currently says `list_notes()` returns the unparameterized
  collection.

## Execution plan

Status: Draft

### Design and boundaries

Make `list_notes` a thin optional-parameter adapter. Construct no `params`
mapping for the zero-argument call, preserving the current request exactly.
For a parameterized call, include only non-`None` values using the approved
HTTP names and let the transport/client preserve service responses and
errors. Prefer keyword-only controls if that is consistent with the reviewed
public package contract, so future additions do not silently change
positional meaning.

Do not duplicate filtering, sorting, or pagination in Python. The service is
the source of truth; the reusable client only serializes the request and
decodes the agreed response.

### Dependencies and sequencing

Wait for the API contract and public route tests in subtask 010. Use the
contract specification as the source for the method signature and parameter
mapping. The full real client-to-service connection is verified by subtask
030; this subtask's transport tests are necessary request-construction
evidence but are not sufficient connection evidence on their own.

### Risks and mitigations

- Always sending default query parameters could alter the old zero-argument
  request; build the no-argument request separately.
- A client-side rename or coercion could make CLI and HTTP behavior diverge;
  use one explicit mapping table based on the approved contract.
- Returning a new envelope only for parameterized calls would break callers
  that expect `list_notes()` to yield notes; preserve the approved response
  contract consistently.

### Implementation decisions and open questions

The parent/API contract must settle public names and response shape first.
Internal serialization helpers, transport recording fixtures, and type
annotations are local implementation choices. No client-specific fallback
behavior should be added for invalid service values unless the approved
contract explicitly requires it.

### Documentation

Update `packages/notes_client/README.md` with the supported method arguments,
their bounds/semantics, an example, and the unchanged zero-argument behavior.
Do not publish the example while it is still only a target specification.

### Task checklist

- [ ] Consume the approved API contract from subtask 010.
- [ ] Implement optional query argument serialization.
- [ ] Preserve and test the exact no-argument request/result behavior.
- [ ] Add request-construction and compatibility tests.
- [ ] Update the client README and report evidence to the parent and CLI
  subtask.

### Requirement verification

- A recording transport test calls `list_notes()` with no arguments and
  asserts the exact existing path and no query parameters, plus a list result.
- Additional recording transport cases assert every approved query control is
  serialized with the service's names and omitted values are not sent.
- The CLI-to-service check owned by subtask 030 exercises this client against
  the real FastAPI route; it is the decisive evidence that serialization and
  service semantics connect.

### Additional implementation verification

- Run the package's tests with the package import/install path used by the
  CLI, not only from a source-tree shell.
- Verify the client still works with its existing injected transport contract
  and with `from_environment()` against the local service used by subtask
  030.