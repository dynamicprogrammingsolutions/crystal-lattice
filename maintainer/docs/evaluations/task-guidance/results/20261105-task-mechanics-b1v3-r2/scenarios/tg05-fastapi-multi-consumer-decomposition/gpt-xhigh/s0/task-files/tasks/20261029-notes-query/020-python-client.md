# Python Client Notes Query

Expose the settled notes-query capability through the reusable Python client without changing its no-argument behavior.

## Requirements checklist

- [ ] `NotesClient` exposes the settled pagination, sorting, and text-filtering options.
- [ ] Calling `list_notes()` without arguments continues to perform the unparameterized request and return the existing list response.
- [ ] Client request behavior is covered and documented against the stable API contract.

Parent Task: tasks/20261029-notes-query/000-main.md

Depends On: tasks/20261029-notes-query/010-api-query-contract.md

## Unresolved questions

- The HTTP parameter names, accepted values, and behavior must be taken from the completed API contract in `tasks/20261029-notes-query/010-api-query-contract.md`; no independent client semantics are approved here.

## Supporting details

- `packages/notes_client/notes_client/client.py` currently implements `list_notes()` as a no-argument request to `/notes/`.
- The package test fixture supplies a fake transport, which can verify query forwarding but cannot prove service behavior. The real CLI-to-service integration is owned by `tasks/20261029-notes-query/030-cli.md`.

## Execution plan

Status: Draft

Wait for the API contract task to be completed. Add a backwards-compatible optional query interface to `NotesClient`, mapping its public arguments directly to the approved HTTP query parameters while keeping the no-argument request unchanged. Test request construction and return behavior at the package boundary, then update the package README with supported arguments and examples.

### Implementation decisions and open questions

- Do not choose parameter names or defaults independently from the HTTP API.
- Keep the existing list-returning no-argument behavior; query response shape follows the approved API contract.

### Documentation

- Update `packages/notes_client/README.md` to describe query arguments, bounds, sorting and filter semantics, and the no-argument behavior.

### Task checklist

- [ ] Wait for and review the completed API contract task.
- [ ] Implement optional client query arguments and forward them using the approved parameter names.
- [ ] Add package tests for query forwarding, supported values, and no-argument compatibility.
- [ ] Update and verify the client README.

### Requirement verification

- Use the package's client boundary to verify its query arguments become the approved HTTP request parameters and preserve the returned list.
- Verify an argument-free `list_notes()` continues to issue the legacy unparameterized request.
- Do not treat mocked client tests as proof of the API or full production path; that decisive evidence belongs to the CLI integration check.
