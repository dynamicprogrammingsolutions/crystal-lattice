# Optional pagination for the notes collection

Add optional `limit`/`offset` pagination to `GET /notes/` while preserving the
existing full-list response when pagination is not requested. Paginated
responses must be ordered by ascending note ID, expose the total number of
notes in a response header, and leave every other CRUD route unchanged.

## Requirements checklist

- [ ] `GET /notes/` accepts optional `limit` and `offset` query parameters.
- [ ] A paginated request returns a bounded slice of notes ordered by ascending
      `id`, with `offset` applied before `limit`.
- [ ] A paginated response includes the total note count in the agreed response
      header; the count represents all notes, independent of the requested
      slice.
- [ ] A request without pagination parameters continues to return the current
      full-list JSON array behavior.
- [ ] Invalid pagination values are rejected through normal FastAPI request
      validation with no custom error contract.
- [ ] The existing single-note, create, update, and delete routes retain their
      current behavior.

## Open requirement questions

- What exact response-header name should carry the total count? `X-Total-Count`
  is the conventional recommendation, but it is not specified by the request.
- What numeric bounds should apply to the optional parameters? The recommended
  contract is `limit >= 1` and `offset >= 0`; this needs confirmation because
  the requested behavior does not state whether zero or negative values are
  valid.
- When only one of `limit` or `offset` is supplied, should the supplied value
  take effect while the other uses its unbounded/default behavior? The plan
  assumes yes, subject to confirmation.

## Research and supporting facts

- The public collection route is `src/app/api/notes.py::read_all_notes`, which
  currently returns `await crud.get_all()` directly.
- `src/app/api/crud.py::get_all` currently performs an unbounded
  `notes.select()` query. The notes table has an integer primary-key `id`.
- The API is mounted at `/notes`, and the existing test boundary is
  `src/tests/test_notes.py` through FastAPI's `TestClient`.
- The existing collection test only asserts a `200` response and JSON array
  shape. There is no maintained API reference page; the repository README
  currently describes the collection as returning every note.
- No working-tree changes were present when this task was drafted.

## Execution plan

Status: Draft

Implement the behavior at the public route and CRUD/query boundary:

1. Add typed optional query parameters to `GET /notes/`, using FastAPI's
   parameter validation constraints once the numeric bounds are confirmed.
2. Extend the notes data-access operation (or add a focused collection
   operation) to apply an explicit ascending `id` order and SQL `offset` and
   `limit` only for the paginated path.
3. Obtain the total count separately from the sliced query and attach it to
   the paginated response using the approved header name. Preserve the
   unpaginated route's JSON array shape and avoid changing the other route
   handlers.
4. Add route-level integration tests that create known notes through the real
   API, verify ascending-ID slicing, offset/limit interaction, total-count
   header behavior, and the unchanged unpaginated array response.
5. Add invalid-query tests for non-integers and each confirmed out-of-range
   value, asserting FastAPI's `422` validation response without introducing a
   custom error body.
6. Exercise the existing CRUD-route smoke coverage and update the README's
   current collection behavior only after the implementation is complete and
   the public contract is confirmed. Do not document the target behavior as
   current guidance during this planning-only handoff.

### Implementation decisions and open questions

The capability belongs in one task because its acceptance boundary is the
single public collection endpoint, with query construction, response headers,
regression tests, and the small README correction all serving that endpoint.
No separate task or subtask is justified by the current repository structure.

The following material API choices remain unresolved and must be settled before
execution is approved:

- the total-count header name;
- lower bounds for `limit` and `offset`;
- behavior when only one optional pagination parameter is provided.

The recommended choices are recorded above as recommendations, not completed
requirements. Once confirmed, they must be reflected consistently in the
requirements checklist, implementation, tests, and documentation.

### Documentation

After implementation, update `README.md` because it currently states that the
collection route returns every note. Describe the supported optional query
parameters, ascending-ID slice semantics, total-count response header, and
validation behavior. Keep the existing full-list behavior documented. No new
documentation directory or placeholder API page is needed.

### Task checklist

- [ ] Resolve the open public-contract questions and update this Draft plan.
- [ ] Change the collection route/data-access path only.
- [ ] Add public-route regression and validation tests.
- [ ] Verify the other CRUD routes remain compatible.
- [ ] Update the maintained README after behavior is implemented.
- [ ] Run the focused test suite and record the result.
- [ ] Append implementation and completion notes when execution is approved and
      finished.

### Requirement verification

- The optional-parameter and bounded-slice requirements will be verified by
  `TestClient` requests against `GET /notes/` after creating multiple notes
  through `POST /notes/`; assertions will cover ID order, offset, limit, and
  the returned array.
- The total-count requirement will be verified from the response header while
  requesting a slice smaller than the seeded collection, including a slice
  beyond the first page if the confirmed contract permits it.
- The unpaginated compatibility requirement will be verified by a request with
  no query parameters and an array-shape/content assertion over the complete
  seeded collection.
- FastAPI validation will be verified with malformed and confirmed
  out-of-range query values, asserting status `422` at the HTTP boundary.
- CRUD compatibility will be verified by the existing CRUD smoke test plus
  focused create/read/update/delete requests where needed to ensure the
  pagination changes do not alter those routes.
