# Implement notes-query behavior in the FastAPI service

Implement the approved notes-query contract at the public HTTP and database
boundaries.

Parent Task: tasks/20260919-notes-query/000-main.md
Depends On: tasks/20260919-notes-query/010-contract-and-specification.md

## Requirements checklist

- [ ] Add bounded pagination using the approved query parameters and limits.
- [ ] Add the approved stable ordering and deterministic tie-breaker.
- [ ] Add optional text filtering with the approved field and matching
      semantics.
- [ ] Preserve the current unparameterized `GET /notes/` behavior.
- [ ] Return the approved response shape and validation errors.
- [ ] Add service-level evidence for all query and compatibility behavior.

## Supporting facts

`src/app/api/notes.py` currently has no query parameters and delegates to
`crud.get_all()`. `src/app/api/crud.py` uses an unordered SQLAlchemy select.
The existing route test only checks that an unparameterized response is a
list, so it does not prove stable ordering or query semantics.

## Execution plan

Status: Draft

1. Translate the approved contract into typed route parameters or request
   models at the HTTP boundary.
2. Extend the database query path so filtering, ordering, and bounds are
   applied before results are returned, with an explicit deterministic order.
3. Keep the no-parameter execution and response compatibility covered by a
   regression test.
4. Add tests with controlled notes that distinguish ordering, filtering,
   page boundaries, maximum bounds, empty results, and invalid values.
5. Update API-facing documentation only with behavior demonstrated by the
   tests.

### Implementation decisions and open questions

- Decision: query behavior must be tested through the FastAPI route and real
  database adapter, not only by testing a helper in isolation.
- Open: exact parameter names, response shape, and validation follow the
  approved contract task.

### Documentation

Update the API/developer documentation owned by the service with the verified
  query parameters, examples, ordering/filtering semantics, and compatibility
  behavior. Keep storage implementation details out of the public contract.

### Task checklist

- [ ] Implement approved route/query behavior.
- [ ] Implement explicit stable database ordering.
- [ ] Add API regression and feature tests.
- [ ] Verify the API documentation against test evidence.

### Requirement verification

- Bounded pagination, stable sorting, and filtering are proven by requests to
  `GET /notes/` using the public HTTP boundary and persisted test data.
- Unparameterized compatibility is proven by the existing collection shape and
  behavior under a request with no query parameters.
- Validation and empty-result behavior are proven at the HTTP boundary.

### Additional implementation verification

- Verify that SQL ordering is explicit and does not depend on SQLite’s
  incidental row order.
- Verify that filtering is applied before pagination and that page boundaries
  do not produce duplicate or skipped records under the documented ordering.