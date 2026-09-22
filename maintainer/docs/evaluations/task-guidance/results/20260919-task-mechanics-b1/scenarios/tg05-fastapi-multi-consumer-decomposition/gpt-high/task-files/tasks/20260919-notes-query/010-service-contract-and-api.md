# Establish the notes-query contract and public API behavior

Define the stable HTTP contract first, then implement and verify bounded
pagination, deterministic sorting, and optional text filtering in the FastAPI
notes collection endpoint.

Parent Task: tasks/20260919-notes-query/000-main.md

## Requirements checklist

- [ ] Publish one explicit HTTP query contract before dependent client work
      begins, including parameter names, defaults, bounds, supported sort
      fields/orders, filter matching, response shape, and validation errors.
- [ ] Support bounded pagination on `GET /notes/` using the approved contract.
- [ ] Support optional text filtering using the approved matching semantics.
- [ ] Return notes in a deterministic order, including a deterministic
      tie-breaker when the selected sort values are equal.
- [ ] Preserve the current unparameterized request and JSON-array response.
- [ ] Add API-boundary tests that use the real FastAPI route and database
      behavior rather than bypassing the route with mocked CRUD results.
- [ ] Document the supported HTTP behavior in the service-owned documentation.

## Open requirement questions and material design decisions

The service subtask cannot finalize the public contract until the parent
questions about parameter names, page bounds/defaults, no-argument
compatibility, filter matching, and sortable fields/order are resolved. The
recommended choices are recorded in the parent task; this subtask owns
recording the approved answers in the HTTP documentation and route contract.

## Supporting facts

The route in `src/app/api/notes.py` currently has no query parameters and
delegates directly to `crud.get_all()`. The database table contains only
`id`, `title`, and `description`; there is no timestamp column to use as an
implicit sort key. Existing API tests only assert a 200 status and list type.

## Execution plan

Status: Draft

Resolve the contract questions in the parent task and record the final
decision in the service documentation before changing consumer code. Add
validated route parameters and a query path in the service/CRUD layer that
applies the approved filter, stable ordering with `id` tie-breaking, and
bounded slice. Keep the no-argument branch compatible with the current array
response. Seed several notes with duplicate sort values and varied title or
description text, then test the public route for every supported combination
and invalid input.

### Implementation decisions and open questions

- The service is the source of truth for the wire-level names and semantics;
  the client and CLI must not introduce aliases without approval.
- The material choices listed above are inherited from the parent and must be
  resolved before execution is approved.
- The recommended compatibility shape is a JSON array in both unparameterized
  and parameterized responses, avoiding an unrequested envelope or metadata
  change.

### Documentation

Update the root README with the endpoint query contract and examples, and
ensure `docs/development/index.md` no longer claims that no notes-query
specification exists once the contract is maintained. Document only behavior
covered by the API tests.

### Task checklist

- [ ] Resolve and record the approved HTTP contract.
- [ ] Implement route/CRUD query handling with validation and stable ordering.
- [ ] Add regression coverage for an unparameterized `GET /notes/`.
- [ ] Add API integration coverage for pagination boundaries, filtering,
      sorting/tie-breaking, and invalid query values.
- [ ] Update service documentation and link the decisive tests to the
      contract.
- [ ] Hand the finalized contract to
      `tasks/20260919-notes-query/020-reusable-client.md`.

### Requirement verification

- [ ] Contract stability: documentation and route declarations expose the
      exact same approved names, bounds, defaults, and error behavior before
      client implementation is accepted.
- [ ] Query capability: real requests through `GET /notes/` demonstrate
      bounded pages, approved text matches, and deterministic ordering across
      repeated requests and equal primary sort values.
- [ ] Compatibility: a request with no query parameters returns the existing
      list-shaped response and includes the existing records.