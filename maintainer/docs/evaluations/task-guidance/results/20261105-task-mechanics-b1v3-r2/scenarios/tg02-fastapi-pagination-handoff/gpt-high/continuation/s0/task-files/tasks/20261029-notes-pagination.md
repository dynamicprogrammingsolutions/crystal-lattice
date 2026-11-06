# Optional Notes List Pagination

Add optional pagination to `GET /notes/` while preserving its existing unpaginated response and leaving the other CRUD routes unchanged.

## Requirements checklist

- [ ] Accept optional `limit` and `offset` query parameters on `GET /notes/`.
- [ ] Return a bounded slice ordered by ascending note ID when pagination is requested.
- [ ] Include the total number of notes in a response header on paginated requests.
- [ ] Preserve the current full-list JSON array response when pagination is omitted.
- [ ] Let FastAPI return its normal validation response for invalid pagination values.
- [ ] Keep all other CRUD route behavior unchanged.

## Unresolved questions

- What exact header name should carry the total count? Recommendation: `X-Total-Count`.
- What values are valid for `limit` and `offset` (for example, positive `limit` and non-negative `offset`), and should an offset-only request be supported?

## Supporting details

- `src/app/api/notes.py` currently implements `GET /` by calling `crud.get_all()` and returning its result directly.
- `src/app/api/crud.py` currently selects all notes without explicit ordering or pagination.
- `src/tests/test_notes.py` only checks that the collection endpoint returns a JSON list; `src/tests/conftest.py` provides a `TestClient`.
- The root `README.md` describes the current full-array behavior and is the maintained user-facing documentation location. There is no `docs/index.md` or notes-query specification.
- Pagination is a collection-route concern; do not alter the other CRUD endpoints.

## Execution plan

Status: Draft

Keep the change within the notes collection API and the data-access path it calls. Add optional query parameters to the collection route, validate their accepted values using FastAPI parameter constraints, and pass them into a bounded query that orders by note ID ascending. Obtain the total note count independently of the slice so it represents all notes, including when the selected page is empty. Return the existing array response with the total in a response header on paginated requests; preserve the unpaginated array behavior. Do not alter per-note CRUD behavior or introduce a new response envelope.

The API contract still needs decisions on the total-count header name and accepted pagination values, including the behavior of offset without limit. The executor must obtain approval for those contract details before implementation. Once resolved, keep query validation in FastAPI so invalid inputs use its standard validation response.

### Implementation decisions and open questions

- Recommendation: use `X-Total-Count` for the count header.
- Confirm whether `limit` must be positive, whether `offset` may be zero, and whether `offset` without `limit` returns all remaining notes.
- Preserve the existing JSON array shape for both paginated and unpaginated requests; only the requested slice differs.
- Leave all routes other than `GET /notes/` untouched.

### Documentation

- Update the root `README.md` with the supported pagination parameters, ascending-ID ordering, total-count header, validation behavior, and unchanged unpaginated response after the API contract is confirmed.

### Task checklist

- [ ] Resolve and approve the pagination header and value semantics.
- [ ] Implement and test collection query validation, ordering, slicing, and total count.
- [ ] Verify omitted parameters retain the full-list array behavior.
- [ ] Verify the other CRUD routes remain unchanged.
- [ ] Update the root `README.md` to describe the implemented behavior.

### Requirement verification

- Pagination, ordering, and total count: add a test through `GET /notes/` that creates notes, requests a page, and asserts the ascending-ID slice and total-count header.
- Unpaginated behavior: retain or extend the collection route test to assert that omitting both parameters returns the full JSON array.
- Invalid values: send invalid query values through the FastAPI test client and assert FastAPI's standard validation status and response.
- Other CRUD routes: run the existing CRUD route coverage and add no route changes outside the collection handler.

### Additional implementation verification

- Run the focused notes API tests, then the full test suite if available.