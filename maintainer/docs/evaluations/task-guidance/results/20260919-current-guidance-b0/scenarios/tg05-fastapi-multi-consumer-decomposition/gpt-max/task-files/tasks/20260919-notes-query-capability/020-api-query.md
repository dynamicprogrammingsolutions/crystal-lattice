# Implement notes queries at the public API

Parent Task: `tasks/20260919-notes-query-capability/000-main.md`

Depends On: `tasks/20260919-notes-query-capability/010-public-contract.md`

Implement the approved notes-query contract in the FastAPI route and database
access layer. The service remains the source of filtering, pagination, and
ordering behavior for all consumers.

## Requirements checklist

- [ ] `GET /notes/` accepts the approved bounded pagination, stable sorting,
  and optional text-filter parameters.
- [ ] The service applies filtering and pagination before returning results and
  uses a deterministic ordering, including the approved tie-breaker.
- [ ] Invalid or out-of-bound query values produce the contractually approved
  public errors.
- [ ] `GET /notes/` without query parameters preserves the current list-shaped
  behavior and does not silently impose a new default page limit.
- [ ] API tests cover the feature and compatibility at the public HTTP
  boundary.

## Unresolved requirement questions

Implementation is blocked on the contract decisions in
`tasks/20260919-notes-query-capability/010-public-contract.md`, especially
pagination/response shape, sort vocabulary, filter matching, and errors.

## Research and supporting facts

- `src/app/api/notes.py` currently delegates the collection route to
  `crud.get_all()` with no query model.
- `src/app/api/crud.py` currently issues an unrestricted `notes.select()` with
  no explicit ordering.
- `src/app/db.py` exposes only `id`, `title`, and `description`, which bounds
  the fields available to the public contract.
- `src/tests/test_notes.py` currently has no seeded multi-row query scenarios
  and the global database needs deliberate test isolation.

## Execution plan

Status: Draft

After the contract is approved, add route validation using the framework's
public request boundary and pass normalized query values into a database-level
query. Keep the no-argument route behavior explicit. Add integration tests
that create controlled notes through the service boundary, exercise each
query feature and invalid case, and verify the response shape and ordering.

### Implementation decisions and open questions

- The API layer owns public validation and the CRUD/data layer owns query
  construction; both must consume the same normalized contract values.
- Sorting must use an explicit secondary key so equal primary values have a
  repeatable order across pages.
- Filtering and pagination should be performed by the database query rather
  than by slicing an unrestricted result in Python.
- The final response representation and parameter names remain those approved
  by the contract subtask.

### Documentation

- Update the root API guidance and the shared notes-query contract only after
  the implementation and integration tests pass.
- Do not replace the existing unparameterized collection claim with a
  parameterized-only description; document both paths.

### Task checklist

- [ ] Add public query parameter validation from the approved contract.
- [ ] Extend the data query with text filtering, bounded pagination, and
  deterministic ordering.
- [ ] Preserve the no-argument route and response shape.
- [ ] Add public API integration coverage for normal, boundary, tie, and
  invalid-input cases.
- [ ] Record the service evidence in the parent task before handing off to
  the client subtask.

### Requirement verification

- [ ] A public HTTP integration test proves bounded pagination returns the
  approved slice and rejects values outside the approved bounds.
- [ ] A public HTTP integration test proves sorting is deterministic for equal
  primary values and remains consistent across pages.
- [ ] A public HTTP integration test proves the approved text filter matches
  exactly the contract's fields and matching rules.
- [ ] A no-parameter HTTP test proves the existing all-notes list behavior is
  preserved.

### Additional implementation verification

- [ ] Verify the generated OpenAPI schema exposes the approved query
  parameters, bounds, and response shape.
- [ ] Verify tests do not rely on database insertion order or data left by a
  previous test.