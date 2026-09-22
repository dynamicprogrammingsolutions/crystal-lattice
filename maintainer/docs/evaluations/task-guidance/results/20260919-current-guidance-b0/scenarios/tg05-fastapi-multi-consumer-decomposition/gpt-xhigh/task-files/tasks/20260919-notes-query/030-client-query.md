# Expose notes querying in the reusable Python client

Parent Task: tasks/20260919-notes-query/000-main.md

Depends On: tasks/20260919-notes-query/010-query-contract.md, tasks/20260919-notes-query/020-api-query.md

Map the approved HTTP query capability into the independently maintained `notes-client` package without breaking existing no-argument callers.

## Requirements checklist

- [ ] `NotesClient.list_notes()` accepts the approved optional query arguments using stable Python names and types.
- [ ] The client serializes only the approved values and maps them to the approved HTTP parameter names and representation.
- [ ] `list_notes()` with no arguments preserves the current `GET /notes/` request and decoded list return behavior.
- [ ] Parameterized responses and service validation errors are handled according to the approved contract without introducing an undocumented second API.
- [ ] Client tests cover request construction, response representation, no-argument compatibility, and at least one real service interaction.

## Unresolved requirement questions and material decisions

This subtask inherits all public choices from `tasks/20260919-notes-query/010-query-contract.md`. In particular, the method signature and return type cannot be finalized until the response shape and parameter names are stable.

## Research and supporting facts

- `packages/notes_client/notes_client/client.py` currently constructs an `httpx.Client` from `NOTES_API_URL` and calls `self.transport.get("/notes/").json()`.
- The package test transport accepts `**kwargs` but does not currently assert them.
- `packages/notes_client/README.md` says `list_notes()` returns the unparameterized collection.
- The package has no existing parameter object, page type, or query helper.

## Execution plan

Status: Draft

Extend the existing public method in the smallest compatible way, using optional keyword arguments or the contract-approved query object. Build the HTTP `params` mapping at the client boundary with correct omission/default rules and leave transport/error behavior consistent with the service contract. Keep the no-argument invocation on the current path so existing callers receive a list and do not need to understand query metadata.

Add focused transport tests that capture the exact path and params for each option, assert that no-argument calls do not send accidental defaults, and verify the approved response shape. Add an integration test using the actual service endpoint for a representative filtered or paginated query so request serialization and response decoding are proven together.

### Implementation decisions and open questions

The contract subtask owns the public signature, parameter names, and result model. A local implementation may use a small query dataclass or keyword-only arguments only if it does not create a second public contract. Avoid silently clamping values in the client unless the approved contract explicitly requires client-side normalization; invalid values should reach the defined validation behavior.

### Documentation

Update `packages/notes_client/README.md` with the stable method signature, supported options, no-argument compatibility note, and a concise example. Keep it aligned with the service contract and only publish behavior verified by package and integration tests.

### Task checklist

- [ ] Implement the approved client method/query mapping.
- [ ] Add exact request-construction and no-argument compatibility tests.
- [ ] Add a service-backed client integration test.
- [ ] Update the package README after verification.

### Requirement verification

| Requirement | Planned evidence |
| --- | --- |
| Client query API | Package tests call the public method with every approved option |
| Correct HTTP mapping | Capturing transport assertions inspect path and exact params |
| No-argument compatibility | Test proves no params are added and the result remains a list |
| Response/error behavior | Tests exercise the approved success representation and service validation response |
| Real service mapping | Integration test uses the production client implementation against the API |

### Additional implementation verification

- Check that the client’s type/signature documentation and package README do not imply support for unapproved server options.
- Run package tests from the package boundary so import and dependency behavior are exercised as consumers use it.
