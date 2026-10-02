# Expose notes-query through the reusable Python client

Add the approved notes-query capability to `NotesClient` while preserving its
existing no-argument behavior. This subtask owns package API design,
serialization, and client documentation.

Parent Task: `tasks/20260925-notes-query/000-main.md`

Depends On: `tasks/20260925-notes-query/010-api-contract-and-service.md`

## Requirements checklist

- [ ] Expose client arguments that map directly to the approved HTTP query
      contract.
- [ ] Preserve `NotesClient.list_notes()` with no arguments, including its
      existing request path and list result behavior.
- [ ] Serialize optional query values with the approved omission, encoding,
      and validation rules.
- [ ] Verify the client against the real service contract, not only a mocked
      response.
- [ ] Document the method signature, query behavior, result shape, and
      backward-compatible default.

## Supporting facts

The client currently accepts an injected transport or constructs a synchronous
`httpx.Client` from `NOTES_API_URL`. `list_notes()` always calls
`transport.get("/notes/")` without keyword arguments. The existing package
test transport records no request details, so new tests need to distinguish
the unchanged no-argument call from parameterized calls.

## Execution plan

Status: Draft

Once the API contract is frozen, add optional, typed method arguments using
the same names and meanings as the HTTP contract. Build the query mapping
without adding absent values to the no-argument request, and preserve the
decoded response behavior selected by the API contract. Client-side
validation should only duplicate contract validation where it is part of the
approved package behavior; otherwise allow the service response to remain the
source of truth.

Use a recording transport for focused request-construction tests, including
the exact unchanged no-argument call. Then add a real-service integration
check that constructs the production client transport, sends a filtered,
sorted, bounded request, and asserts the service response. The integration
check must cross HTTP and the service rather than substituting a response
object.

### Implementation decisions and open questions

- Method argument names, optional-value omission, and return typing depend on
  the API contract in `010-api-contract-and-service.md`.
- Decide whether invalid values fail locally or are returned as service
  validation errors only if the approved package contract requires that
  distinction.
- Keep `from_environment()` as the production construction path and do not
  add a test-only transport shortcut to the public behavior.

### Documentation

- Update `packages/notes_client/README.md` with the finalized method
  signature, examples, defaults, result shape, and service error behavior.
- Keep package documentation aligned with the API contract; do not document
  target behavior before the service supports it.

### Task checklist

- [ ] Consume the frozen API contract without redefining it.
- [ ] Add optional query arguments and request serialization.
- [ ] Add no-argument compatibility and focused transport tests.
- [ ] Add the real service/client integration check.
- [ ] Update the package README.
- [ ] Record evidence and any deviations in completion notes after execution.

### Requirement verification

- No-argument compatibility and exact query serialization are verified by
  package tests using a recording transport.
- The client’s actual supported capability is decisively verified by a test
  that uses `NotesClient.from_environment()` or an equivalent production
  transport against a live notes service and asserts the returned filtered,
  sorted, bounded data.