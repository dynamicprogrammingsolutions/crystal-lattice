# Add optional pagination to the notes collection

Add optional `limit`/`offset` pagination to `GET /notes/` while preserving
the current unpaginated array response and leaving the item and mutation
routes unchanged.

## Requirements checklist

- [ ] `GET /notes/` accepts optional `limit` and `offset` query parameters.
- [ ] A paginated request returns a JSON array containing the requested
      bounded slice of notes, ordered by ascending note ID.
- [ ] The collection response exposes the total number of notes in a response
      header, counting notes before applying `limit` and `offset`.
- [ ] A request without pagination parameters keeps the current full-list JSON
      array behavior.
- [ ] Invalid pagination values are rejected through normal FastAPI request
      validation rather than custom response handling.
- [ ] The existing `GET /notes/{note_id}/`, `POST /notes/`, `PUT
      /notes/{note_id}/`, and `DELETE /notes/{note_id}/` behavior is unchanged.

## Unresolved requirement questions

- What exact response-header name should carry the total: recommend
  `X-Total-Count`, unless an existing API convention is intended.
- Should the total-count header be present only when `limit` or `offset` is
  supplied, or on every `GET /notes/` response? Recommending every collection
  response keeps the metadata contract consistent while preserving the
  unpaginated body.
- What bounds and defaults are part of the public parameter contract? The
  implementation should use typed FastAPI query parameters with explicit
  non-negative validation; confirm whether `limit=0` is valid, whether an
  omitted limit means “all remaining notes,” and whether an omitted offset
  means `0`.

## Research and supporting facts

- `src/app/api/notes.py` currently defines `read_all_notes()` without query
  parameters and returns `await crud.get_all()` directly, so the collection
  body is currently the database result list.
- `src/app/api/crud.py` currently selects all notes without an explicit order
  and has no count or pagination helper. Ascending-ID ordering must therefore
  be made explicit for the new collection behavior.
- `src/app/db.py` defines the SQLite `notes` table with integer primary-key
  `id`, making `id ASC` the natural stable ordering and count source.
- `src/tests/test_notes.py` only verifies that the unfiltered collection
  response is a list and that a create route exists. It has no deterministic
  coverage for ordering, slicing, totals, validation, or preservation of the
  other routes.
- `README.md` is the maintained user-facing API summary. There is no existing
  notes-query specification in `docs/development/index.md`; no new
  specification page is needed for this focused change.

## Execution plan

Status: Draft

The collection endpoint remains a JSON-array endpoint. FastAPI will parse the
optional query parameters and enforce their agreed bounds at the HTTP boundary.
The collection data access path will make the order explicit, obtain the
unpaginated count, and then apply the requested offset/limit to the note
selection. The route will attach the count as a response header while
returning the selected rows as the existing array shape. No item route or
mutation route will share this new pagination behavior.

The production-path tests should exercise `TestClient` against `/notes/`,
create a deterministic set of notes, and verify the body, ordering, slice
boundaries, total header, unpaginated compatibility, and FastAPI's 422
validation responses. They should also retain a focused smoke check for the
other CRUD routes so the route signatures and mutation behavior remain
covered. Test setup must isolate or clean its records so assertions do not
depend on the repository's SQLite file state.

Ordered work:

1. Resolve the header-presence, header-name, and parameter-bound/default
   questions above and record the approved contract in this task.
2. Update the collection data-access and route layers to implement the
   approved count, ascending-ID ordering, slicing, and response metadata,
   without changing the other route handlers.
3. Extend the public HTTP tests with deterministic pagination, validation,
   total-count, unpaginated-compatibility, and CRUD-regression cases.
4. Update the maintained README API summary with the verified query
   parameters, ordering, response header, and validation behavior.
5. Run the focused notes tests and the complete configured test suite, then
   record the evidence in this task.

### Implementation decisions and open questions

- The public response remains an array for both paginated and unpaginated
  requests; introducing an envelope is out of scope.
- Ordering is `id ASC`, and the total is computed before pagination.
- Query parsing and invalid-value responses belong to FastAPI's normal
  validation path.
- The exact header name, header presence policy, and limit/offset bounds and
  defaults remain open requirement questions. Execution should not begin until
  they are approved.

### Documentation

- Update `README.md` in the same change as the implementation because it is
  the maintained user-facing description of the notes API.
- Do not create a new development specification page for this small change;
  the task and updated README provide the needed planning and user guidance.

### Task checklist

- [ ] Resolve and record the open pagination contract questions.
- [ ] Implement collection-only pagination and total-count metadata.
- [ ] Add deterministic public-route regression coverage.
- [ ] Update the README with the verified behavior.
- [ ] Run focused and full test suites and record results.

### Requirement verification

- Optional parameters, bounded slicing, ascending-ID ordering, and the total
  header: an integration test through `TestClient` at `GET /notes/` with
  multiple created notes and a nonzero offset/limit.
- Unpaginated full-list array compatibility: an integration test through
  `GET /notes/` without query parameters, asserting the complete seeded set
  and array response shape.
- Invalid values: integration requests through `GET /notes/` with malformed
  and out-of-range values, asserting FastAPI's `422` response.
- Other CRUD routes unchanged: the existing public-route smoke coverage plus
  focused create/read/update/delete assertions using the same application
  and database path.

### Additional implementation verification

- Run the focused notes test module and the complete configured test suite.
- Inspect the final route and query diff to confirm pagination parameters and
  count logic are limited to the collection endpoint.