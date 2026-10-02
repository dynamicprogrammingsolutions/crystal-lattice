# Add optional pagination to the notes collection

Plan the addition of optional `limit`/`offset` pagination to `GET /notes/`,
while preserving the existing full-list response when neither parameter is
requested and leaving the item CRUD routes unchanged.

## Requirements checklist

- [ ] `GET /notes/` supports optional `limit` and `offset` query parameters.
- [ ] A paginated request returns a slice bounded by the requested pagination
      values, ordered by ascending note ID.
- [ ] A paginated response reports the total number of notes in a response
      header.
- [ ] A request without pagination parameters keeps the current JSON array
      response containing the full note list.
- [ ] Invalid pagination values are rejected through normal FastAPI request
      validation.
- [ ] The single-note read, create, update, and delete routes retain their
      current behavior.

## Unresolved requirement questions

- What exact response-header name should carry the total count? A conventional
  recommendation is `X-Total-Count`, but this is a public HTTP contract and
  needs confirmation.
- What numeric bounds should be accepted? The implementation needs an explicit
  decision on whether `limit` must be positive, whether `offset` may be zero
  only or any non-negative integer, and whether a zero limit should return an
  empty page or a validation error.
- What should happen when only one parameter is supplied? A conventional
  recommendation is to treat either parameter as pagination, defaulting an
  omitted offset to zero and allowing an omitted limit to mean “from this
  offset onward,” but that leaves the latter request unbounded.

## Research and supporting facts

- The collection route is `src/app/api/notes.py::read_all_notes`; it currently
  accepts no query parameters and returns `await crud.get_all()` directly.
- `src/app/api/crud.py::get_all` performs an unfiltered `notes.select()`.
  There is no count helper or explicit ordering helper.
- Note IDs are SQLite primary keys defined in `src/app/db.py`, so the
  paginated query can order by `notes.c.id.asc()`.
- `src/tests/test_notes.py` currently verifies that `GET /notes/` returns a
  list and that the create route remains available. The fixture uses the
  real FastAPI `TestClient` boundary.
- `README.md` currently documents that the collection route returns every note
  as a JSON array. It is the maintained public documentation location found
  for this behavior; no notes-query specification exists.
- No task files or package-specific client/CLI boundary are present in this
  repository.

## Execution plan

Status: Draft

Implement the change at the HTTP and database-query boundaries owned by the
notes API. Keep the no-parameter branch compatible with the current
full-array response. For pagination, add FastAPI query declarations with the
approved constraints, obtain the unfiltered total separately, and use an
explicit ascending-ID database query with the effective offset and limit.
Write the total to the approved response header only for paginated responses
unless the unresolved header contract is decided otherwise.

Use integration tests through `TestClient` and the real SQLite-backed
application lifecycle. Seed notes through the public create route so the
tests prove ordering, slicing, and total-count behavior without bypassing the
HTTP boundary. Cover the no-parameter legacy shape, representative bounded
pages, offset/limit edge cases after their bounds are approved, malformed and
out-of-range query values returning FastAPI’s normal 422 response, and the
existing item CRUD routes.

Update the maintained README in the same implementation change to describe
the supported query parameters, ordering, total-count header, validation
behavior, and the preserved no-parameter array response. Do not publish the
target behavior before the implementation and tests make it true.

### Implementation decisions and open questions

The public header name, numeric bounds, and partial-parameter behavior remain
open requirement questions above. Once answered, record the decision here,
update the requirement checklist if needed, and change the plan status to
`Approved` only when execution is authorized. The implementation should keep
pagination-specific query/count work isolated from the item CRUD helpers and
avoid changing their route signatures or response behavior.

### Documentation

Update `README.md` as the owning public documentation after implementation.
The update should state the exact query syntax, defaulting/partial-parameter
rules, ascending-ID ordering, total-count header name and scope, validation
failures, and that requests without pagination still return the full JSON
array. No new documentation directory or placeholder specification is
warranted by the current repository.

### Task checklist

- [ ] Resolve the public header, bounds, and partial-parameter questions.
- [ ] Approve this execution plan before implementation.
- [ ] Complete `tasks/20260919-notes-pagination/010-api-pagination.md`.
- [ ] Complete `tasks/20260919-notes-pagination/020-route-tests.md`.
- [ ] Complete `tasks/20260919-notes-pagination/030-documentation.md`.
- [ ] Verify the unchanged item CRUD routes.
- [ ] Update the maintained README after the behavior is implemented.

### Requirement verification

- Optional query support, bounded slicing, ascending-ID ordering, and the
  total-count header: public `GET /notes/` integration tests with multiple
  created notes and explicit query parameters, after the open contract
  decisions are resolved.
- Legacy full-list behavior: a public request with neither query parameter
  must return status 200 and the complete JSON array in the existing shape.
- FastAPI validation: public requests with malformed or out-of-range
  pagination values must return the framework’s normal 422 response and must
  not reach a successful list response.
- CRUD compatibility: public create, single-note read, update, and delete
  requests continue to pass their existing behavior checks.
- Documentation: inspect the final README against the implemented and tested
  contract; documentation is not evidence for runtime behavior.
