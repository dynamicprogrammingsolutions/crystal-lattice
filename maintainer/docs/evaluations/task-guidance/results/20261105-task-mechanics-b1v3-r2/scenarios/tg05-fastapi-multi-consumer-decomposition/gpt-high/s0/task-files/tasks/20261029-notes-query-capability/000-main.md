# Notes Query Capability

Plan one notes-query capability across the public HTTP API, reusable Python client, and CLI, with the API contract defined before consumer work.

## Requirements checklist
- [ ] Provide bounded pagination, stable sorting, and optional text filtering through the public notes API.
- [ ] Preserve the current no-parameter API response as the complete notes array and preserve the no-argument client and CLI behavior.
- [ ] Expose the supported query capability through the reusable Python client and CLI.
- [ ] Prove the CLI-to-production-client-to-service path through an actual service request, not mocked consumer behavior.
- [ ] Keep the API, client, and CLI documentation aligned with supported behavior.

## Subtasks
- [ ] [tasks/20261029-notes-query-capability/010-api-contract.md](tasks/20261029-notes-query-capability/010-api-contract.md)
- [ ] [tasks/20261029-notes-query-capability/020-python-client.md](tasks/20261029-notes-query-capability/020-python-client.md)
- [ ] [tasks/20261029-notes-query-capability/030-cli.md](tasks/20261029-notes-query-capability/030-cli.md)

## Unresolved Questions
- What pagination parameters, default page size, and maximum bound should the public contract use?
- Which note fields are sortable and searchable, what sort directions are supported, and how should equal sort keys be deterministically ordered?
- What response shape should parameterized queries return while the unparameterized route retains its existing JSON-array shape?
- What text-matching semantics should filtering use?

These are public-contract questions and must be resolved before client and CLI consumers implement the API.

## Supporting Details
- **Fact:** The existing collection endpoint is `GET /notes/` and returns all notes as a JSON array.
- **Fact:** `NotesClient.list_notes()` calls that endpoint without parameters and returns decoded JSON; `notes list` prints every note through the client.
- **Fact:** Existing package tests use fake transports/clients, and the service test fixture uses FastAPI `TestClient`. Those seams alone do not establish the required CLI-to-service path.
- **Decision:** Treat the API contract, client package, and CLI as separate deliverables because each is an independently maintained public compatibility boundary. Sequence the client after the API contract and the CLI after the client.

## Execution plan
Status: Draft

The API deliverable owns the HTTP contract, including the query parameters, their validation and bounds, stable ordering, filter semantics, response representation, and legacy no-parameter behavior. Resolve the public-contract questions before consumer implementation; use that approved contract as the shared source for the client method and CLI flags. The service should perform query work through the existing API/CRUD/database boundary. Do not let the implementation of a consumer silently decide HTTP semantics.

The reusable client owns a compatible parameterized listing operation while retaining the existing no-argument call and return behavior. The CLI owns user-facing query options and forwards them through the real client; its no-option invocation continues to list all notes. Keep focused unit/component checks within each deliverable, but make one integrated test traverse the CLI, production client, HTTP route, and service persistence path.

Order execution by dependency: settle and implement the API contract first, implement the client against it second, then expose the API-supported options in the CLI and verify the full path. Keep documentation with each owning audience: service API documentation at the service/root entry point, client usage in the client README, and command usage in the CLI README. No task file creation authorizes implementation; the plan remains Draft pending approval.

### Implementation decisions and open questions
- Keep all unresolved API contract questions above open. The API subtask must record their approved answers before dependent consumer work begins.
- **Decision:** Preserve no-argument behavior at all three surfaces, and require deterministic ordering when sort values tie.
- **Decision:** Use the CLI integration check as the decisive end-to-end evidence; mocked CLI and client tests are supplemental only.

### Documentation
- Update the root/service documentation with the stable HTTP query contract and the retained unparameterized behavior.
- Update `packages/notes_client/README.md` with parameterized usage and compatibility behavior.
- Update `apps/notes_cli/README.md` with query options and a usable invocation.
- Do not create a new docs index or placeholder documentation hierarchy.

### Task checklist
- [ ] Resolve the API contract questions and implement the documented public behavior.
- [ ] Add API verification for parameter validation/bounds, filtering, deterministic sorting, pagination, and no-parameter compatibility.
- [ ] Add client query support and tests proving parameters are sent and legacy calls remain unchanged.
- [ ] Add CLI query options and focused argument/forwarding checks.
- [ ] Add a decisive integrated test that invokes the CLI against the actual HTTP service through `NotesClient` and the service persistence layer.
- [ ] Update documentation at the API, client, and CLI ownership boundaries.

### Requirement verification
- Requirements 1–2: API tests call the public `/notes/` route with and without query options and prove bounded pagination, stable deterministic sorting, optional matching, and the unchanged unparameterized array. Do not treat isolated CRUD tests as proof.
- Requirement 3: Client and CLI focused tests verify supported parameter forwarding and unchanged no-argument behavior; their respective maintained READMEs document current behavior.
- Requirement 4: The decisive integration test invokes the CLI while using the production `NotesClient` against the actual notes HTTP service and persistence path, without replacing the client or service behavior with mocks.
- Requirement 5: Review each maintained README against the implemented contract and actual command interface.

### Additional implementation verification
- Run focused service, client, and CLI tests, then the integrated path test. Report test boundaries and any unavailable runtime setup explicitly.