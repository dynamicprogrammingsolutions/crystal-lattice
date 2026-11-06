# Add Optional Notes Pagination

Extend `GET /notes/` with optional limit/offset pagination while preserving the existing response for requests without pagination.

## Requirements checklist

- [ ] `GET /notes/` accepts optional limit and offset values and returns the requested note slice in ascending ID order.
- [ ] Paginated responses include the total number of notes in a response header.
- [ ] Requests without pagination continue returning the full note list as a JSON array.
- [ ] Invalid pagination values use normal FastAPI validation responses.
- [ ] Other CRUD routes retain their current behavior.

## Unresolved questions and decisions

- Which response header name should carry the total count? Recommendation: `X-Total-Count`.
- What behavior should apply when only one pagination parameter is supplied? Recommendation: treat omitted `offset` as zero and an omitted `limit` as unbounded.

## Supporting details

- `src/app/api/notes.py` currently implements `GET /` by returning `crud.get_all()`; the route has no query parameters or response header handling.
- `src/app/api/crud.py` currently issues an un-ordered `notes.select()` and has no count or pagination operation.
- Notes use an integer primary-key `id` in `src/app/db.py`.
- `src/tests/test_notes.py` currently checks that the unpaginated route returns a JSON list and that basic CRUD routes exist; it does not verify pagination, order, headers, validation, or CRUD state preservation.
- The package README is the only existing user-facing API description found; no `docs/index.md` exists. Keep any behavior documentation local to that README unless repository structure changes.

## Execution plan

Status: Draft

Keep pagination behavior scoped to the notes collection GET route and its data-access operations. The public response remains an array in both modes; when pagination is requested, data is ordered by ascending note ID before applying offset and limit. The count header reports all notes, not only the returned slice. FastAPI query parameter declarations should provide normal request validation rather than route-specific error handling. The route should obtain the full count independently of the page query. No other CRUD route or response contract should change.

The header name and one-parameter semantics are unresolved public API decisions listed above; do not begin execution until they are confirmed. The recommendations provide a conventional default if approved.

### Implementation decisions and open questions

- Confirm the total-count header name before implementation; recommended `X-Total-Count`.
- Confirm omitted-parameter behavior for a request containing only `limit` or only `offset`; recommended defaults are omitted offset = zero and omitted limit = unbounded.
- Keep invalid-value behavior to FastAPI's ordinary query validation; do not introduce custom error formats.

### Documentation

- Update the root `README.md` alongside the implementation to describe the optional query parameters, ordering, count header, and unchanged no-parameter response.
- Do not create new documentation pages for this focused API addition.

### Task checklist

- [ ] Resolve the public header-name and one-parameter behavior questions.
- [ ] Implement GET-only pagination and all-notes count header without altering other CRUD routes.
- [ ] Add focused integration coverage for unpaginated compatibility, ascending-ID slicing, total count, invalid query validation, and unaffected CRUD behavior.
- [ ] Update README API guidance to match implemented behavior.

### Requirement verification

- Requirements 1 and 2: exercise the public `/notes/` route with multiple persisted notes and verify the returned ascending-ID slice plus total-count header, including a slice smaller than the total.
- Requirement 3: call `/notes/` without pagination and verify it still returns the full JSON array.
- Requirement 4: send invalid query values through the real FastAPI test client and verify FastAPI's normal validation response.
- Requirement 5: exercise create, read, update, and delete through their public routes in a focused regression test to ensure their existing behavior remains intact.

### Additional implementation verification

- Run the focused notes API tests and the repository's configured test suite if available.