# Backward-Compatible Notes Query

Establish one supported notes-query capability across the public HTTP API, reusable Python client, and CLI, while preserving existing unparameterized behavior.

## Requirements checklist

- [ ] The public collection API supports bounded pagination, stable sorting, and optional text filtering under an agreed, documented contract.
- [ ] A request without query parameters preserves the current full-collection JSON-array response, and `NotesClient.list_notes()` without arguments preserves its current full-list behavior.
- [ ] The reusable Python client exposes the supported query capability, and the CLI exposes it through the client.
- [ ] The CLI is verified through the production client-to-service path, not only through a fake client or mocked transport.
- [ ] The public API query contract is settled and verified before client or CLI behavior relies on it.

## Subtasks

- [ ] [tasks/20261029-notes-query/010-api-query-contract.md](tasks/20261029-notes-query/010-api-query-contract.md)
- [ ] [tasks/20261029-notes-query/020-python-client.md](tasks/20261029-notes-query/020-python-client.md)
- [ ] [tasks/20261029-notes-query/030-cli.md](tasks/20261029-notes-query/030-cli.md)

## Unresolved questions

- What pagination parameters and bounds define the stable HTTP contract, and should pagination be opt-in so an unparameterized request continues returning every note?
- Which note fields are sortable, what ordering is the default, and what tie-breaker makes paged sorting deterministic?
- Which text fields does filtering search, and should matching be substring-based and case-insensitive?
- What CLI option names should expose the query, and what validation/error behavior should invalid query values produce?

## Supporting details

- `GET /notes/` currently returns the full collection as a JSON array. `NotesClient.list_notes()` currently sends no query parameters and returns that JSON value.
- The CLI currently has a single `list` command. Its tests supply a fake client, so they do not traverse the HTTP client or service.
- The CLI imports `notes_client`, but `apps/notes_cli/pyproject.toml` currently does not declare it as a runtime dependency. Ensure the normal CLI installation path resolves the reusable package.
- The service, client, and CLI each have maintained user-facing READMEs. `docs/development/documentation.md` advises updating those sources rather than creating placeholder documentation.
- The existing API tests use FastAPI `TestClient`; client tests use a fake transport; CLI tests use a fake client. None currently prove a CLI request through the real HTTP client to a running service.

## Execution plan

Status: Draft

Keep the HTTP collection endpoint as the source of query semantics. First agree and document its parameter names, validation, defaults, bounds, sorting behavior, and filter behavior; only then implement consumers. Preserve the existing no-argument client call and no-parameter API response. Because the existing route returns every note, the bounded-page defaults must be explicitly reconciled with that legacy behavior before implementation.

Split work by independently maintained compatibility surface: the API contract, the reusable client package, and the CLI application. The API task establishes the contract and owns route/database evidence. The client task depends on that contract and owns the package interface. The CLI task depends on the client and owns command-line behavior plus the decisive integration check: invoke the actual CLI against a running notes service, allowing the normal `NotesClient` environment configuration and HTTP transport to reach the service.

### Implementation decisions and open questions

- No query parameter names, defaults, bounds, sortable fields, filter semantics, CLI syntax, or invalid-input behavior are decided in this Draft.
- Resolve the questions above before implementation. The client and CLI subtasks depend on the settled and tested API contract, not on a guessed convention.
- Preserve the existing unparameterized response as an array of all notes; determine whether pagination is opt-in or whether the legacy behavior needs a different explicit compatibility treatment.
- The CLI packaging change should declare or otherwise reliably resolve `notes-client` in the normal installation path; validate this as part of the CLI task.

### Documentation

- Update the root README with the current HTTP query contract and no-parameter compatibility behavior.
- Update `packages/notes_client/README.md` with the client query interface and preserved no-argument behavior.
- Update `apps/notes_cli/README.md` with CLI query options and usage.
- Keep documentation in those maintained sources; do not add a placeholder specification or docs page.

### Task checklist

- [ ] Complete `tasks/20261029-notes-query/010-api-query-contract.md` before consumer work.
- [ ] Complete `tasks/20261029-notes-query/020-python-client.md` after the API contract is settled.
- [ ] Complete `tasks/20261029-notes-query/030-cli.md` after the client interface is available.

### Requirement verification

- API contract and legacy behavior: route/database integration tests exercise pagination bounds, stable ordering, filtering, invalid inputs once agreed, and the unparameterized full-array response.
- Python client behavior: package tests verify query forwarding and that `list_notes()` with no arguments keeps its existing behavior; the CLI integration check also traverses the real client to validate its connection to the service.
- CLI behavior and production path: CLI unit tests verify parsing/output, and an integration test invokes the real CLI against a running service with query options and verifies the resulting output. No fake client or mocked HTTP transport may supply the claimed query result in this decisive check.
- Contract-before-consumers constraint: the API task must record the agreed contract and its route-level verification before the dependent client and CLI tasks begin.

### Additional implementation verification

- Run the API, client, and CLI test suites after the focused checks.
- Verify the CLI's declared runtime dependency and normal entrypoint/install path as part of the real-service integration test.
