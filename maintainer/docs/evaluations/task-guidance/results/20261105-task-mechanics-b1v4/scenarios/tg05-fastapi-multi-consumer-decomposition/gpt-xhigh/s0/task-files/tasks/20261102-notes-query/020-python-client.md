# Reusable Python Client Notes Query

Expose the finalized notes-query API through the independently reusable Python client while preserving its current no-argument behavior.

## Requirements checklist

- [ ] The reusable client exposes the approved pagination, sorting, and text-filtering options using the finalized API contract.
- [ ] Calling `NotesClient.list_notes()` without options continues to issue the existing unparameterized request and return decoded JSON.
- [ ] Client documentation describes supported query usage without claiming behavior beyond the public API contract.

Parent Task: tasks/20261102-notes-query/000-main.md
Depends On: tasks/20261102-notes-query/010-public-api.md

## Supporting details

- **Fact:** `packages/notes_client/notes_client/client.py` implements `list_notes()` as `GET /notes/` followed by `.json()`.
- **Fact:** The client package currently depends on `httpx`; its tests use a small transport double.
- **Constraint:** This deliverable depends on the API contract and behavior in `tasks/20261102-notes-query/010-public-api.md`. It must not define independent names or semantics.

## Implementation plan

Status: Draft

After the API task establishes the contract, extend the client's public `list_notes()` interface to accept the approved query options and forward them using the corresponding HTTP parameters. Preserve the existing no-argument call as a bare `GET /notes/` request so existing consumers retain the same route, response decoding, and full-collection behavior. Keep parameter translation in the client rather than duplicating server-side filtering or sorting.

This task follows the API milestone and blocks the CLI task. Focused client tests should verify correct parameter forwarding and that no arguments do not introduce a query payload. Those tests are local package evidence only; the CLI task owns the decisive integration check through a real HTTP service and the production client configuration.

The main risk is interface drift or changing the no-argument call while adding optional parameters. If the new method surface proves incompatible, retain the no-argument signature behavior and revise only the additive options to match the approved API contract.

### Implementation decisions and open questions

Use the approved parameter and matching semantics from `tasks/20261102-notes-query/010-public-api.md`. Any unresolved consumer naming question in the parent task must be answered before implementation.

### Documentation

Update `packages/notes_client/README.md` with the approved method arguments, an example of a filtered/paginated/sorted call, and a clear statement that the no-argument call preserves the existing full collection behavior.

### Task checklist

- [ ] Confirm the API milestone is complete and its contract is stable.
- [ ] Add the client query arguments and parameter forwarding.
- [ ] Test parameter forwarding and no-argument compatibility.
- [ ] Update the client README.
- [ ] Provide the completed client for CLI integration.

### Requirement verification

- **Client capability and compatibility:** Client tests use the package's transport boundary to verify the exact approved parameters are sent and that a no-argument call remains unparameterized. They deliberately do not claim to prove the live service or CLI path; that evidence is owned by `tasks/20261102-notes-query/030-cli.md`.

### Additional implementation verification

Check public method defaults and annotations against the approved API behavior so omitted arguments do not silently change the legacy request.