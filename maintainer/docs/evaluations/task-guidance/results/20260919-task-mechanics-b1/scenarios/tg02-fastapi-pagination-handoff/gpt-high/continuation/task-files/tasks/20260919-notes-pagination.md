# Optional note-list pagination

Add optional `limit`/`offset` pagination to `GET /notes/`, preserving the
existing full-list response when pagination is not requested and leaving all
other CRUD routes unchanged.

## Requirements checklist

- [ ] `GET /notes/` accepts optional `limit` and `offset` query parameters.
- [ ] When pagination is requested, the response contains a bounded slice of
      notes ordered by ascending numeric `id`.
- [ ] A response header reports the total number of notes independently of the
      requested slice.
- [ ] Requests without pagination retain the current JSON array response
      containing the full note list.
- [ ] Invalid pagination values are rejected through normal FastAPI parameter
      validation.
- [ ] The behavior of the create, read-one, update, and delete routes remains
      unchanged.

## Unresolved requirement questions

- What exact response-header name should carry the total count? Recommended:
  `X-Total-Count`.
- What bounds should validation enforce? Recommended: `limit` is an integer
  greater than or equal to 1 when supplied, and `offset` is an integer greater
  than or equal to 0 when supplied. Non-integer and out-of-range values should
  produce FastAPI's standard 422 validation response.
- Should the total-count header be present only when `limit` or `offset` is
  supplied, or on every successful `GET /notes/` response? Recommended:
  return it for both paginated and unpaginated collection responses so the
  header consistently describes the collection; confirm before execution.
- If only one parameter is supplied, should the other use its natural boundary
  (no upper bound when only `offset` is supplied, and zero when only `limit` is
  supplied)? Recommended: support the parameters independently, with omitted
  `offset` meaning zero and omitted `limit` meaning no slice-size cap.

## Supporting facts

- `src/app/api/notes.py` currently exposes `read_all_notes()` at
  `GET /notes/` and returns `await crud.get_all()` directly.
- `src/app/api/crud.py` currently selects all notes without an explicit
  ordering or count operation.
- `src/tests/test_notes.py` currently verifies only that the collection
  response is a list and that the create route exists.
- `docs/development/index.md` states that no notes-query specification exists.
- The maintained public behavior is currently documented in the root
  `README.md` as a collection route that returns every note as a JSON array.

## Execution plan

Status: Draft

Implement and verify the capability at the public HTTP boundary while keeping
the existing route structure and response model intact.

1. Confirm the open contract questions above, especially the header name,
   validation bounds, header presence, and one-parameter behavior.
2. Extend the collection query path with explicit ascending `id` ordering,
   total-count calculation, and optional SQL-level offset/limit application.
   Keep the unpaginated result as a JSON array and avoid changing the
   signatures or semantics of the item and mutation routes.
3. Expose the total count through the agreed response header without changing
   the collection body shape.
4. Add focused HTTP integration coverage using the real FastAPI route and
   database boundary:
   - unpaginated requests still return a full array;
   - paginated requests return the expected ascending-ID window;
   - offset-only, limit-only, and boundary/empty-page cases follow the
     confirmed contract;
   - the total header reports the full collection count;
   - malformed and out-of-range query values receive standard FastAPI 422
     responses;
   - existing CRUD-route coverage remains green.
5. Update the owning API documentation with the current query parameters,
   ordering, header, validation behavior, and compatibility behavior. If the
   root README remains the only user-facing API reference, update it there;
   otherwise place the guidance in the smallest existing notes API document.
6. Run the focused notes tests and the full available test suite, recording
   any environment or database-isolation limitation in the completion notes.

### Implementation decisions and open questions

- Keep pagination scoped to `GET /notes/`; do not alter item lookup or
  mutation handlers.
- Apply ordering before offset/limit so page boundaries are deterministic and
  ascending by note `id`.
- Obtain the total from the complete notes relation, not from the page result.
- Prefer FastAPI/Pydantic query declarations for type conversion and bounds so
  invalid requests use the framework's normal validation response.
- The header name, exact bounds, header presence on unpaginated responses, and
  omitted-parameter defaults remain unresolved until confirmed above.

### Documentation

- Update the maintained notes API guidance in the same implementation change
  as the route behavior.
- Document the request examples, ascending-ID ordering, total-count header,
  validation failures, and the preserved unpaginated array response.
- Do not create a new documentation hierarchy or mark target behavior as
  current before the implementation is complete.

### Task checklist

- [ ] Resolve the four contract questions in this task.
- [ ] Mark this plan `Approved` before implementation begins.
- [ ] Implement collection query and response-header behavior.
- [ ] Add or update public-boundary regression tests.
- [ ] Update maintained API documentation.
- [ ] Run focused and full verification.
- [ ] Record implementation and completion notes with requirement evidence.

### Requirement verification

- The optional query contract, standard validation behavior, and unchanged
  unpaginated array behavior will be verified through `GET /notes/` requests
  against the real FastAPI application.
- Ascending-ID ordering, offset/limit slicing, and empty/boundary pages will
  be verified with multiple persisted notes and assertions on response IDs.
- The total-count requirement will be verified by comparing the agreed header
  to the seeded collection size on both a truncated page and the selected
  unpaginated behavior.
- CRUD compatibility will be verified by the existing create/read/update/delete
  route tests or focused additions that exercise those public routes without
  pagination parameters.

### Additional implementation verification

- Inspect the generated OpenAPI schema or route metadata to confirm the query
  parameters expose the intended integer bounds and optionality.
- Run the complete available test suite to catch route matching or shared
  database lifecycle regressions.