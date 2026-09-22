# Add optional pagination to the notes collection

Plan the `GET /notes/` enhancement so clients can request a bounded,
ascending-ID slice while preserving the existing collection response for
requests that do not use pagination. This task covers the HTTP behavior,
regression evidence, and the maintained API documentation; it does not
authorize implementation yet.

## Requirements checklist

- [ ] `GET /notes/` accepts optional `limit` and `offset` query parameters.
- [ ] A request using pagination returns notes as a bounded slice ordered by
      ascending note ID.
- [ ] A paginated response exposes the total number of notes in a response
      header.
- [ ] A request without pagination parameters keeps the current full-list JSON
      array behavior.
- [ ] Invalid pagination values are rejected by FastAPI's normal query
      validation and produce its standard validation response.
- [ ] The create, read-one, update, and delete routes retain their current
      behavior.

## Scope

This is a single deliverable at the public HTTP boundary. It includes focused
route-level integration tests and an update to the existing README. It does not
introduce a new response envelope, client package, CLI behavior, or unrelated
CRUD changes.

## Unresolved requirement questions

These choices affect the public contract and should be confirmed before
execution:

1. What exact response-header name should carry the total? Recommendation:
   `X-Total-Count`, unless the project has an external naming convention.
2. What validation bounds are required? The usual contract is
   `limit >= 1` and `offset >= 0`; the request does not specify whether
   `limit=0` is valid or whether there is a maximum limit.
3. When only one parameter is supplied, should the route paginate using the
   other parameter's default (`offset` alone skips, `limit` alone takes the
   first page), and should the total header appear for those partial requests?
4. Should the total header be emitted only when at least one pagination
   parameter is present, or also on the legacy full-list response?

Until these questions are answered, the checklist intentionally does not
claim a particular header spelling, numeric bound, default, or header-presence
policy.

## Research and supporting facts

- The collection route is `src/app/api/notes.py::read_all_notes`, currently
  with no query parameters, and it delegates to `src/app/api/crud.py::get_all`.
- `get_all` currently selects the complete `notes` table without an explicit
  ordering, limit, offset, or count query.
- The notes table has an integer primary-key `id`; the requested paginated
  order can therefore be expressed at the database query boundary.
- `src/tests/test_notes.py` currently checks only that `GET /notes/` returns
  status 200 and a JSON list, plus that creation is available.
- `README.md` is the only maintained user-facing package documentation found;
  `docs/development/index.md` records that no notes-query specification exists.
- The working tree was clean before this task file was added.

## Execution plan

Status: Draft

Add typed optional query parameters at the collection route and use FastAPI's
query validation for parsing and bounds. Preserve the existing no-parameter
path as a full list, while the paginated path obtains the total count
independently, applies explicit ascending-ID ordering, and applies the
requested offset and limit before returning the JSON array plus the agreed
header. Keep the single-note and mutation routes untouched.

Extend the public `TestClient` coverage with independent seeded notes to
prove:

- the no-parameter response remains a JSON array containing the full
  collection;
- a paginated response is ordered by ascending ID, bounded by the requested
  offset and limit, and carries the total count;
- partial-parameter behavior, once confirmed, follows the documented
  defaults;
- malformed, negative, zero, or otherwise out-of-range values covered by the
  agreed contract return FastAPI's normal 422 validation response;
- the existing CRUD smoke coverage still passes.

Update `README.md` only after the contract choices above are confirmed and
implemented. Document the query parameters, their validation, ordering,
response-header semantics, and the preserved full-list behavior. Do not
describe target behavior as current before implementation is complete.

### Implementation decisions and open questions

The task is intentionally a single task file because the change has one
public owner and one acceptance boundary, even though its execution includes
code, tests, and documentation. The exact header name, numeric bounds,
partial-parameter defaults, and whether the header is present on the legacy
response remain requirement questions listed above; execution should return
the plan to Draft if any answer changes the checklist.

### Documentation

During execution, update `README.md` as the maintained user-facing guide for
the notes API. No new documentation directory or placeholder notes-query
page is warranted by the current repository structure.

### Task checklist

- [ ] Confirm the unresolved public-contract questions.
- [ ] Mark this plan `Approved` before implementation begins.
- [ ] Implement optional collection pagination at the HTTP/database boundary.
- [ ] Add or update public route-level regression tests.
- [ ] Update the README with verified pagination behavior.
- [ ] Run the focused tests and the complete available test suite.
- [ ] Record implementation and completion notes with evidence.

### Requirement verification

- Full-list compatibility: a `TestClient` request to `GET /notes/` with no
  query parameters returns status 200 and the complete collection as a JSON
  array.
- Paginated slice and ordering: a `TestClient` request with confirmed
  pagination parameters returns only the requested bounded records in
  ascending ID order.
- Total count: the same public response includes the agreed total-count
  header whose value equals the number of stored notes, independent of the
  requested slice.
- Validation: public requests containing each agreed invalid value receive
  FastAPI's standard 422 response; tests must exercise the actual route
  boundary rather than calling query or CRUD helpers directly.
- CRUD preservation: the existing create/read/update/delete route coverage,
  supplemented where necessary to cover the changed collection's interaction
  with stored notes, continues to pass.

### Additional implementation verification

- Verify that the count is taken from the full notes collection and is not
  accidentally limited or offset.
- Verify that the no-pagination branch does not change the response shape to
  an envelope or alter unrelated route behavior.
- Run the repository's available test command and report any environment
  limitation rather than treating an uncollected or interrupted run as
  passing.