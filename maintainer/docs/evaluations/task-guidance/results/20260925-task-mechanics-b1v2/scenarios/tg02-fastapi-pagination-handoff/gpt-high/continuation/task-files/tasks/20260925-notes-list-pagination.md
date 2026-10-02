# Add optional pagination to the notes collection

Add optional `limit`/`offset` pagination to `GET /notes/` while preserving
the existing unpaginated JSON-array response and all other CRUD routes.

## Requirements checklist

- [ ] `GET /notes/` accepts optional `limit` and `offset` query parameters.
- [ ] A paginated request returns a JSON array containing the requested
      bounded slice in ascending note-ID order.
- [ ] A paginated response exposes the total number of notes in a response
      header.
- [ ] A request without pagination retains the current full-list JSON-array
      behavior.
- [ ] Invalid pagination values are rejected through normal FastAPI parameter
      validation.
- [ ] The read-one, create, update, and delete routes retain their current
      public behavior.

## Unresolved requirement questions

These are public-contract choices that need confirmation before execution:

1. Should the total-count header be named `X-Total-Count`? This is the
   recommended conventional name.
2. Should the total-count header be emitted only when `limit` or `offset` is
   supplied, or on every `GET /notes/` response? The recommended behavior is
   to emit it only for paginated requests so the unpaginated path remains
   behaviorally unchanged apart from the explicitly requested feature.
3. What numeric constraints should apply? The recommended validation is
   integer `offset >= 0` and integer `limit >= 1`, with omitted parameters
   meaning no bound for that dimension. In particular, confirm whether
   `limit=0` should be rejected or represent an empty page.
4. If only one parameter is supplied, should it independently take effect?
   The recommended behavior is yes: an omitted offset starts at zero, and an
   omitted limit leaves the slice unbounded after the offset.

## Research and supporting facts

- The collection route is `src/app/api/notes.py::read_all_notes`; it
  currently has no query parameters and returns `crud.get_all()` directly.
- `src/app/api/crud.py::get_all` currently selects every row without an
  explicit ordering, limit, or offset.
- Notes use an integer primary key in `src/app/db.py`, so the paginated query
  can order by `notes.c.id.asc()` and apply SQL limit/offset operations.
- The current public test only checks that an unparameterized collection
  response is a list; the route is exercised through `TestClient`.
- The root `README.md` is the only user-facing API summary. There is no
  existing notes-query specification or API reference page.

## Execution plan

Status: Draft

The route will keep the response body as a bare list for both paths. FastAPI
will own query-parameter parsing and validation through typed optional query
parameters and declared range constraints. The route will pass the validated
values to the CRUD layer and use the response object only to add the agreed
total-count header for the paginated path.

The CRUD layer will retain a distinct no-pagination path for the existing
full-list behavior. For a paginated request it will count all notes
independently of the slice, select notes ordered by ascending ID, and apply
the requested offset and limit. No response envelope or changes to the
single-note and mutation handlers will be introduced.

Focused tests will cross the real FastAPI route, CRUD functions, and SQLite
database through `TestClient`. They will cover the unpaginated list shape, a
multi-row ascending-ID slice with the total header, each supported
single-parameter form, FastAPI validation failures, and smoke coverage for
the other CRUD routes. The README will be updated with the final query
parameters, validation rules, ordering, and header contract in the same
implementation change.

### Implementation decisions and open questions

- Recommended header: `X-Total-Count`, containing the decimal total number of
  notes before pagination.
- Recommended range: `offset` is a non-negative integer and `limit` is a
  positive integer. FastAPI should generate the validation response for
  malformed or out-of-range values.
- Recommended partial-parameter semantics: either parameter may be supplied
  alone; omitted values use offset zero or no limit respectively.
- The open questions above are requirement questions, not implementation
  details. Execution should not begin until the public choices are confirmed.

### Documentation

- Update the root `README.md`, which owns the current user-facing API
  summary, with the final `GET /notes/` pagination syntax and response
  header.
- Do not create a new documentation page or placeholder specification for
  this small API addition.

### Task checklist

- [ ] Confirm the header name and presence rule.
- [ ] Confirm numeric constraints and single-parameter semantics.
- [ ] Mark this plan Approved before implementation begins.
- [ ] Add FastAPI query validation and route response-header handling.
- [ ] Add ordered count-and-slice support in the CRUD layer.
- [ ] Add integration-level regression coverage for pagination,
      validation, unpaginated compatibility, and unchanged CRUD routes.
- [ ] Update the root README with the implemented public contract.
- [ ] Run the focused tests and the full available test suite.

### Requirement verification

- `GET /notes/?limit=...&offset=...`: a `TestClient` integration test creates
  known notes, verifies the response is a list of the expected IDs in
  ascending order, verifies the slice is bounded, and verifies the agreed
  total-count header equals the pre-pagination total.
- `GET /notes/` without query parameters: the existing collection test plus a
  regression assertion verify a bare full-list array remains the response
  shape.
- Invalid values: route-level requests with malformed and out-of-range
  values verify FastAPI returns its standard validation response rather than
  a custom error.
- Other CRUD routes: the real HTTP create/read/update/delete paths remain
  covered by smoke/regression assertions and are checked for unchanged
  status/body behavior.
- Documentation: review the README examples against the finalized route
  contract after implementation.