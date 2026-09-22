# Implement notes querying in the public API

Parent Task: tasks/20260919-notes-query/000-main.md

Depends On: tasks/20260919-notes-query/010-query-contract.md

Implement the approved notes-query contract at the FastAPI route and database access boundary while preserving the existing unparameterized collection behavior.

## Requirements checklist

- [ ] `GET /notes/` accepts the approved optional pagination, sorting, and text-filter query parameters.
- [ ] Pagination is bounded and invalid or out-of-range inputs receive the contract-defined validation response.
- [ ] Sorting is explicit and deterministic, including the contract-defined tie-breaker.
- [ ] Text filtering applies exactly to the contract-defined fields and matching semantics.
- [ ] A request with no query parameters remains a `200` raw JSON list with the current all-notes behavior.
- [ ] API integration tests cover the approved combinations and compatibility path against the real database-backed service.

## Unresolved requirement questions and material decisions

This subtask inherits the public decisions from `tasks/20260919-notes-query/010-query-contract.md`. It must not independently choose parameter names, response shape, default ordering, bounds, or filter semantics.

## Research and supporting facts

- `src/app/api/notes.py` currently has `read_all_notes()` with no query model.
- `src/app/api/crud.py` currently calls `database.fetch_all(notes.select())`; no order, filter, limit, or offset is expressed.
- `src/app/db.py` defines the SQLite-backed `notes` table with `id`, `title`, and `description`.
- `src/tests/test_notes.py` only checks that the current collection response is a list and that a create route exists.

## Execution plan

Status: Draft

Add the approved query parameters at the route boundary with validation that is visible in the API schema. Pass a normalized query object into the data-access layer rather than duplicating query logic in the route. Build the SQL expression in a deterministic order: apply the approved text predicate, apply explicit sort columns plus the unique tie-breaker, then apply the approved pagination bounds. Preserve the existing no-query path’s raw-list response and all-row semantics exactly as required by the contract.

Use deterministic fixtures that include duplicate sort values, mixed-case text, enough rows to cross a page boundary, and records that should not match the filter. Assert the HTTP status, JSON shape, order, page boundaries, filtering, invalid input response, and no-query compatibility through the FastAPI test client.

### Implementation decisions and open questions

The contract subtask owns material API decisions. Local implementation choices may include a typed query model, SQLAlchemy expressions, and a shared normalization helper, provided they do not alter the approved public behavior.

Potential risk to revisit during execution: the current SQLite/database fixture is shared and the existing tests do not cleanly establish data isolation. The implementation should use an isolated or explicitly cleaned test dataset for query assertions rather than relying on insertion order or leftover records.

### Documentation

Update the service-owned contract or development guidance with the verified query examples, bounds, ordering, filtering, and compatibility behavior. Update `README.md` if its statement that the collection returns every note becomes incomplete. Do not claim support until the endpoint tests pass.

### Task checklist

- [ ] Add route-level query validation from the approved contract.
- [ ] Add deterministic filtering, ordering, and pagination in the data-access path.
- [ ] Preserve and test the no-query raw-list behavior.
- [ ] Add endpoint tests for valid, boundary, invalid, and tie-breaking cases.
- [ ] Update service-owned documentation after verification.

### Requirement verification

| Requirement | Planned evidence |
| --- | --- |
| Accepted query capability | HTTP integration tests issue real `GET /notes/` requests with each approved dimension |
| Bounded pagination | Boundary tests demonstrate maximum enforcement and page slicing |
| Stable sorting | Repeated/duplicate-key fixture assertions demonstrate deterministic order with the tie-breaker |
| Text filtering | HTTP assertions cover every contract-defined field and matching rule |
| No-query compatibility | Existing route path plus explicit all-notes raw-list assertion |
| Validation | HTTP assertions cover invalid and out-of-range values at the public API boundary |

### Additional implementation verification

- Inspect the generated OpenAPI schema for parameter names, defaults, bounds, and descriptions.
- Confirm the SQL query does not depend on database default row order.
