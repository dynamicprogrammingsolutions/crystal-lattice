# Define and implement the notes query HTTP contract

Own the public query contract and FastAPI/database behavior for bounded
pagination, stable sorting, and optional text filtering. Preserve the current
unparameterized collection response and publish the contract before consumer
work depends on it.

## Requirements checklist

- [ ] The approved HTTP contract defines query names, defaults, bounds,
  ordering guarantees, filtering semantics, response shape, and invalid-input
  behavior.
- [ ] `GET /notes/` implements the approved contract at the route and
  database boundaries.
- [ ] No-argument `GET /notes/` remains compatible with the existing JSON
  array behavior.
- [ ] API tests cover the query capability, edge/invalid values, stable
  ordering, and the no-argument regression through the real route.
- [ ] The maintained service-owned contract documentation is current.

Parent Task: tasks/20260925-notes-query-capability/000-main.md

## Research and supporting facts

- `src/app/api/notes.py` exposes `GET /notes/` with no declared query
  parameters.
- `src/app/api/crud.py` uses `notes.select()` without explicit ordering or
  slicing.
- `src/app/db.py` has `id`, `title`, and `description` only.
- `src/tests/test_notes.py` currently verifies only that the collection route
  returns a list and that a create route exists.

## Execution plan

Status: Draft

Resolve the HTTP contract first, then implement validation and query
composition at the service boundary. Use an explicit deterministic order
before applying pagination so adjacent pages cannot depend on database
incidental order. Keep the no-argument request compatible and test all
behavior through the FastAPI route with real database access.

### Implementation decisions and open questions

The pagination model, sort vocabulary, filter scope/matching rules, bounds,
error responses, and parameterized response shape are inherited from the
parent task's unresolved contract questions. Do not choose them implicitly
during implementation. If the approved sort needs a new persisted field,
stop and return the scope decision to the parent task.

### Documentation

Create or update the service-owned notes-query contract under
`docs/development/`, link it from `docs/development/index.md`, and keep the
root README's API description accurate. If the contract is documented before
implementation, mark it `Not implemented` until the route is complete.

### Task checklist

- [ ] Obtain approval for the HTTP query vocabulary and compatibility shape.
- [ ] Document the approved contract before consumer implementation begins.
- [ ] Implement validated filtering, stable ordering, and bounded pagination.
- [ ] Preserve and test the no-argument collection behavior.
- [ ] Test boundary and invalid inputs through `TestClient`.
- [ ] Update the parent task with contract decisions and evidence.

### Requirement verification

- HTTP contract: review the maintained service contract against the approved
  decision record before marking the requirement complete.
- Query behavior: route-level tests seed representative notes, call
  `GET /notes/` with each approved option, and assert the complete filtered,
  ordered, bounded result at the service boundary.
- Compatibility: a no-argument `GET /notes/` test asserts status 200 and the
  existing JSON array result, alongside the existing CRUD coverage.

### Additional implementation verification

- Verify tied primary sort values use the documented deterministic
  tie-breaker.
- Verify database filtering and slicing happen before the response is
  returned, rather than silently applying pagination only in Python.