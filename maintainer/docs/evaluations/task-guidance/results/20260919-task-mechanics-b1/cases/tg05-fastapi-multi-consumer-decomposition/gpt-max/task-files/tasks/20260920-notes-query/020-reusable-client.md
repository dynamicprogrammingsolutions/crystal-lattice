# Reusable client notes query

Expose the approved notes-query controls through `notes-client` while
preserving the current no-argument `list_notes()` behavior. This task depends
on the reviewed and implemented API contract and is a Draft planning handoff.

## Requirements checklist

- [ ] `NotesClient` exposes the approved pagination, sorting, and optional
  text-filter controls with names and values matching the public API contract.
- [ ] A no-argument `list_notes()` call still requests the unparameterized
  collection and returns its decoded list without an envelope or other
  compatibility change.
- [ ] Client evidence proves the approved query arguments work against the
  real notes service, not only against a mocked response.

Parent Task: `tasks/20260920-notes-query/000-main.md`

Depends On: `tasks/20260920-notes-query/010-public-api-contract.md`

## Scope and workstreams

- Own the reusable Python method signature/argument validation, HTTP query
  encoding, client tests, and package documentation.
- Follow the API contract exactly; do not create a client-only query dialect
  or silently translate ambiguous values.
- Keep the existing transport injection seam usable for focused request
  construction tests, while adding a real service-facing check.

## Unresolved requirement questions

The API/contract task must resolve these before this task starts:

- Final parameter names, allowed values, bounds, defaults, and error
  behavior.
- Whether the client accepts omitted values as `None`, uses a request/options
  object, or exposes another approved signature.
- Whether parameterized calls return the same list type or a documented
  metadata-bearing result.

## Research and supporting facts

- `packages/notes_client/notes_client/client.py::NotesClient.list_notes`
  currently has no arguments and returns `transport.get("/notes/").json()`.
- The injected transport’s `get` method accepts `**kwargs`, so query encoding
  can be tested without changing the existing no-argument fixture.
- `packages/notes_client/tests/test_client.py` currently only asserts that
  the decoded no-argument result is a list.
- The package README currently describes only the unparameterized operation.

## Execution plan

Status: Draft

1. Wait for the API contract task to record the approved public vocabulary
   and response shape.
2. Extend the existing list operation, or add the explicitly approved client
   entry point, so optional values are encoded as the service expects and
   omitted values do not produce unintended query parameters.
3. Add focused transport tests for query construction, allowed values, and
   no-argument compatibility. Add an integration test that instantiates the
   production `NotesClient` and sends a real request through the FastAPI
   service.
4. Update the package README with current usage examples only after the
   service-facing evidence passes.

Execution waits for completion and approval of
`010-public-api-contract.md`.

### Implementation decisions and open questions

- The client must not settle unresolved API semantics. Its public method
  shape is a consumer-facing compatibility decision and follows the
  approved contract.
- Keep the no-argument call distinguishable from an explicitly supplied
  default if the HTTP contract gives those requests different semantics.
- Request-shape unit tests are supporting evidence; the decisive
  compatibility check crosses the actual client-to-service boundary.

### Documentation

- Update `packages/notes_client/README.md` with the approved method
  signature, query examples, bounds, and compatibility note after
  implementation.
- Avoid documenting target-only behavior as current before the API contract
  and client integration are verified.

### Task checklist

- [ ] Confirm the API contract task is complete and approved.
- [ ] Implement the approved client query surface and encoding.
- [ ] Add request-construction and no-argument compatibility tests.
- [ ] Add and run a real client-to-service query test.
- [ ] Update package documentation and report the client boundary complete.

### Requirement verification

- **Client controls:** focused tests assert each approved argument becomes
  the correct HTTP query value and invalid client inputs follow the contract.
- **Unparameterized compatibility:** the existing no-argument method test
  asserts `"/notes/"` is requested without query parameters and the result
  remains a list.
- **Service compatibility:** an integration test uses `NotesClient` with a
  real HTTP transport to the FastAPI application and verifies service
  filtering, pagination, and sorting are reflected in the returned data.