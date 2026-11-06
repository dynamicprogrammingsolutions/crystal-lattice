# Python Client Notes Queries

Expose the approved notes collection query capability through the reusable Python client.

Parent Task: `tasks/20261029-notes-query/000-main.md`
Depends On: `tasks/20261029-notes-query/010-public-api.md`

## Requirements checklist

- [ ] `NotesClient` exposes the approved pagination, sorting, and optional text-filter inputs.
- [ ] A no-argument `list_notes()` call preserves current behavior.
- [ ] The client documents its supported arguments and compatibility behavior.

## Supporting details

- **Fact:** `packages/notes_client/notes_client/client.py` implements `list_notes()` as a parameterless GET to `/notes/`.
- **Fact:** `packages/notes_client/tests/test_client.py` currently checks only that the result is a list.
- **Dependency:** Client query names and encoding must follow the approved API contract in `tasks/20261029-notes-query/010-public-api.md`.

## Execution plan
Status: Draft

After the API contract is fixed, extend the client list method to encode optional supported query arguments into the `/notes/` request. Calls without arguments must continue to request the collection without query parameters and return the decoded response as before. Keep the reusable package's documentation and focused tests in this package.

### Implementation decisions and open questions

- Method argument names and validation follow the approved API contract; do not invent a parallel client contract.

### Documentation

- Update `packages/notes_client/README.md` with method usage, supported arguments, and no-argument compatibility.

### Task checklist

- [ ] Add approved optional query arguments and request encoding.
- [ ] Test query encoding and no-argument behavior.
- [ ] Document the reusable client interface.

### Requirement verification

- Test the client HTTP request against the API's agreed parameter names and values, then verify the decoded result.
- Test `list_notes()` without arguments and assert the request remains unparameterized.

### Additional implementation verification

- Run the focused client package tests.