# Freeze and implement the notes-query HTTP contract

Define the canonical public query contract and implement it at the FastAPI
collection boundary. This subtask owns service semantics and API
compatibility; it does not implement the Python client or CLI.

Parent Task: `tasks/20260925-notes-query/000-main.md`

Depends On: none

## Requirements checklist

- [ ] Establish the approved parameter names, types, defaults, limits,
      response shape, and validation/error behavior before consumer work
      starts.
- [ ] Support bounded pagination on `GET /notes/`.
- [ ] Support deterministic stable sorting, including a documented
      tie-breaker for equal primary values.
- [ ] Support the approved optional text-filter semantics.
- [ ] Preserve the successful no-parameter route as the current JSON array
      behavior.
- [ ] Expose the finalized contract through the maintained API/OpenAPI
      surface and cover it with service-boundary tests.

## Supporting facts

The current route has no query parameters and returns the result of an
unqualified notes table select. The existing table contains only `id`,
`title`, and `description`, so filtering and sorting choices must be made from
those fields unless the approved contract expands the schema, which is out of
scope for this plan.

## Execution plan

Status: Draft

First record the approved query contract in the route signature and its
generated API metadata, including bounds and invalid-input responses. Keep
the no-query path compatible with the current array result. Implement the
parameterized query as one database-side composition of text predicates,
explicit ordering, offset, and limit; never depend on incidental database
row order when stable sorting is requested. Apply the tie-breaker
consistently, including when the primary sort values are equal.

Seed integration fixtures with duplicate titles/descriptions and enough rows
to cross page boundaries. Verify valid combinations and invalid values
through `TestClient` at `/notes/`; inspect the response shape and status at
the HTTP boundary rather than testing only a CRUD helper.

### Implementation decisions and open questions

- Do not choose parameter names or semantics until the parent contract
  questions are approved.
- Decide whether no-parameter ordering is preserved exactly or explicitly
  documented as the new default while keeping response shape and content
  compatibility.
- Keep pagination bounds explicit and reject invalid values through the
  public validation contract rather than silently coercing them.

### Documentation

- Add parameter descriptions, defaults, bounds, and response/error examples to
  the maintained API/OpenAPI source.
- Update the root service README only with behavior that the implementation
  and tests verify.
- If a standalone developer contract is approved, place it under the
  existing `docs/development/` area; do not create it as a placeholder.

### Task checklist

- [ ] Resolve the parent contract questions relevant to HTTP behavior.
- [ ] Add the approved query parameters and API metadata.
- [ ] Implement database-side filter, sort, and bounded pagination behavior.
- [ ] Preserve and test the no-parameter array response.
- [ ] Add valid, boundary, invalid-input, tie-break, and filter integration
      coverage.
- [ ] Update API-owned documentation.
- [ ] Record evidence and any deviations in completion notes after execution.

### Requirement verification

- The decisive check for pagination, filtering, stable sorting, validation,
  and no-parameter compatibility is the API integration suite calling
  `GET /notes/` through `TestClient` with real database operations.
- OpenAPI inspection or a generated-schema assertion verifies that the
  approved public parameters and response/error contract are exposed before
  consumers are updated.