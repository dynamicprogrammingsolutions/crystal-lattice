# Python Client Notes Queries

Expose the approved notes-query API contract through the reusable Python client without changing existing no-argument behavior.

Parent Task: tasks/20261029-notes-query-capability/000-main.md
Depends On: tasks/20261029-notes-query-capability/010-api-contract.md

## Requirements checklist
- [ ] Provide a client listing operation that supports the approved pagination, sorting, and optional text-filter query.
- [ ] Preserve `list_notes()` with no arguments, its request behavior, and its decoded response behavior.
- [ ] Document the supported client interface.

## Supporting Details
- **Fact:** `NotesClient.list_notes()` currently issues `GET /notes/` with no query arguments and returns decoded JSON.
- **Decision:** Keep this deliverable dependent on the settled API contract; do not define an independent client interpretation of the query semantics.

## Execution plan
Status: Draft

Add typed/clear client parameters consistent with the approved API contract and forward them through the existing HTTP transport. Preserve the existing no-argument call path, including its legacy response behavior. Add focused transport-level tests for request construction and compatibility, then document usage in the client README. Those focused tests do not replace the parent task's integrated CLI-to-service evidence.

### Implementation decisions and open questions
- Follow the API contract from `tasks/20261029-notes-query-capability/010-api-contract.md`; no additional HTTP semantics are owned here.

### Documentation
- Update `packages/notes_client/README.md` with the supported query operation and a no-argument compatibility example.

### Task checklist
- [ ] Add client query parameters matching the approved API names and supported values.
- [ ] Preserve and test the existing no-argument call and return behavior.
- [ ] Test that query arguments are transmitted to the approved route.
- [ ] Update client package documentation.

### Requirement verification
- Requirement 1: Client tests inspect the transport request and verify all approved query arguments are forwarded as expected; the parent integration test separately proves the real service accepts them.
- Requirement 2: A client test invokes `list_notes()` without arguments and proves the request remains the unparameterized collection request and returns decoded JSON.
- Requirement 3: Review client README examples against the implemented signature and approved API contract.

### Additional implementation verification
- Run the focused client package tests.