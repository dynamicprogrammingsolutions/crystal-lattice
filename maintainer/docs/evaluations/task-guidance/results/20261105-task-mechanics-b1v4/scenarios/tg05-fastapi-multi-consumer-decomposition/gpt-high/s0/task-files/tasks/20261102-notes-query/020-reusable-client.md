# Reusable Notes Client Query Support

Expose the finalized notes query options through the independently maintained Python client.

Parent Task: `tasks/20261102-notes-query/000-main.md`
Depends On: `tasks/20261102-notes-query/010-api-contract-and-service.md`

## Requirements checklist

- [ ] `NotesClient` exposes the finalized API pagination, sorting, and text-filtering options and forwards them consistently.
- [ ] Calling `list_notes()` without options preserves the current request and decoded list behavior.
- [ ] Client documentation describes supported options according to the finalized API contract.

## Questions and decisions

- **Design decision:** Client method names, argument names, types, and option forwarding follow the reviewed HTTP contract from the API prerequisite; this task does not independently redefine query semantics.

## Supporting details

- `packages/notes_client/notes_client/client.py` implements `list_notes()` as a no-argument GET to `/notes/`.
- The package is independently maintained and has its own README and tests.
- Current client tests use a stub transport and do not exercise the service.

## Implementation plan

Status: Draft

After the API prerequisite has finalized the public HTTP semantics, add matching optional parameters to the reusable client method and forward them through the existing transport. Leave the no-argument call behavior intact. Update package documentation and tests to show supported invocation and preserved behavior.

The API task blocks this task because implementing against provisional names or response behavior creates avoidable compatibility churn. After focused client checks pass, this task can stop safely while the CLI proceeds. The primary risk is client/API drift; use the service's approved contract as the test and documentation source. Roll back the new optional method surface if it cannot match the stable service contract without altering no-argument behavior.

### Implementation decisions and open questions

The client mirrors—not interprets—the approved API contract. No unresolved client-specific material choice is identified; any mismatch discovered against the finalized service contract must be raised rather than papered over with client-only behavior.

### Documentation

Update `packages/notes_client/README.md` with the approved option names and types, pagination bounds, sorting/filter behavior, and no-argument compatibility. Keep documentation aligned with the public method signature and actual forwarding.

### Task checklist

- [ ] Add optional query arguments after API contract approval.
- [ ] Verify option forwarding and no-argument compatibility.
- [ ] Document the client invocation and supported behavior.

### Requirement verification

Client tests verify that each supported option is forwarded to the HTTP transport as the finalized query contract specifies and that the decoded response is returned as before. The tests do not prove service query execution; the API task owns that evidence.

No-argument compatibility is verified by a client test asserting the existing unparameterized request and list result.

### Additional implementation verification

Run the focused client package tests.