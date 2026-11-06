# Python Client Notes Query

Expose the approved notes-query contract through the reusable Python client.

Parent Task: `tasks/20261102-notes-query/000-main.md`
Depends On: `tasks/20261102-notes-query/010-public-api.md`

## Requirements checklist
- [ ] The reusable client exposes the query options supported by the stable public API.
- [ ] Calling `list_notes()` without arguments preserves its existing unparameterized request and decoded result behavior.

## Supporting details
- `NotesClient.list_notes()` currently sends `GET /notes/` and returns the decoded JSON body.
- The client is independently packaged and currently has a focused test for the no-argument method.

## Implementation plan
Status: Draft

After the API contract is settled and available, add a client interface that maps its supported query options onto the exact public HTTP parameters and preserves the no-argument call. Keep HTTP parameter mapping in the client rather than requiring each caller to construct requests. Client tests should verify the mapping and preserved no-argument behavior against the approved contract.

This work depends on the API contract; it must not invent defaults or semantics. The compatibility risk is changing the existing method's no-argument behavior or return shape, so retain a focused regression check. Rollback is limited to the additive client query interface.

### Implementation decisions and open questions
- API parameter and response details are governed by `tasks/20261102-notes-query/010-public-api.md`; no independent contract is approved here.

### Documentation
- Update `packages/notes_client/README.md` to describe the supported client query interface after implementation.

### Task checklist
- [ ] Map the approved query options through `NotesClient`.
- [ ] Test parameter mapping and no-argument compatibility.
- [ ] Update the client package README.

### Requirement verification
- Exercise the client against the approved HTTP contract and assert the emitted request parameters and returned result; also verify the no-argument request remains unchanged. This does not prove the CLI production path.

### Additional implementation verification
- Run the focused client test suite.