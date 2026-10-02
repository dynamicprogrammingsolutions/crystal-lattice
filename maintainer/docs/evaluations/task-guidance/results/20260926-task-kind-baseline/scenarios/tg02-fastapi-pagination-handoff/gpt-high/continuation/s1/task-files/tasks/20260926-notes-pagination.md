# Add optional pagination to the notes collection

Plan the addition of optional `limit`/`offset` pagination to `GET /notes/`
while preserving its current JSON-array response when pagination is not
requested. This task is planning-only; implementation is not authorized by
this handoff.

## Requirements checklist

- [ ] `GET /notes/` accepts optional `limit` and `offset` query parameters.
- [ ] A paginated request returns a bounded JSON-array slice in ascending
  note-ID order, with `offset` applied before `limit`.
- [ ] A paginated response exposes the total number of notes in a response
  header.
- [ ] A request with neither pagination parameter retains the current
  full-list JSON-array behavior.
- [ ] Invalid pagination values are rejected through normal FastAPI request
  validation.
- [ ] The other note CRUD routes retain their current behavior.
- [ ] Public API documentation describes the supported pagination behavior
  after the contract is finalized and implemented.

## Unresolved requirement questions

- What exact response-header name should carry the total count? The
  implementation plan recommends `X-Total-Count`, but this is a public API
  contract and needs confirmation.
- Should the total-count header be emitted only when `limit` or `offset` is
  supplied, or on the unpaginated full-list response as well? The current
  reading is paginated responses only.
- What numeric bounds are required? The recommended baseline is
  `offset >= 0` and `limit >= 1` when supplied, using FastAPI's declared
  parameter constraints so malformed and out-of-range values produce the
  framework's ordinary `422` validation response. A maximum page size has not
  been requested.

## Research and supporting facts

- `src/app/api/notes.py` currently exposes `GET /` under the `/notes` router
  and returns `await crud.get_all()` directly.
- `src/app/api/crud.py` currently has only an unbounded `get_all()` query.
- `src/app/db.py` stores notes in a table with an integer primary-key `id`.
- `src/tests/test_notes.py` has a basic collection-response check and only a
  minimal CRUD-route smoke check; it has no pagination, ordering, validation,
  header, or non-regression coverage.
- `README.md` currently states that the collection route returns every note as
  a JSON array. No notes-query specification exists under `docs/`.

## Execution plan

Status: Draft

The collection endpoint should remain an array-returning route. The route
should declare optional integer query parameters through FastAPI, allowing
FastAPI to own parsing and constraint errors. It should distinguish the
no-parameter path from the paginated path so existing full-list behavior stays
compatible.

For the paginated path, the data-access layer should query notes ordered by
ascending primary-key ID, apply the offset, and then apply the limit when
present. It should obtain the total count from the notes table independently
of the page slice. The route should attach that count to the response using
the confirmed header name. Existing read-one, create, update, and delete
handlers and their data-access operations should remain unchanged.

Verification should cross the public HTTP boundary using the real FastAPI
route, database, and test application. Seed a known set of notes through the
public API, then verify:

- an ordinary `GET /notes/` remains a JSON array containing the full set;
- a request with both parameters returns the expected ascending-ID slice and
  total-count header;
- requests with only `limit` or only `offset` have the defined semantics;
- an empty or beyond-end slice still reports the full total;
- malformed and out-of-range values receive FastAPI's normal `422`
  validation response;
- the existing detail, create, update, and delete paths still work through
  their public endpoints.

The maintained `README.md` should be updated in the same implementation
change with the final parameter bounds, slice semantics, and header name. No
new documentation directory or placeholder specification is needed.

### Implementation decisions and open questions

- Keep the response shape as a JSON array; do not introduce a pagination
  envelope.
- Make ascending `id` ordering explicit for paginated queries so page
  membership is deterministic.
- Preserve the existing unpaginated code path as far as practical, rather
  than changing the behavior of unrelated CRUD operations.
- Resolve the header name, header emission scope, and exact parameter bounds
  before changing the status from Draft to Approved.

### Documentation

- Update `README.md` after the public contract is resolved and implemented.
- Document that omitting both parameters preserves the full-list array.
- Document the query parameters, ascending-ID ordering, total-count header,
  and validation behavior.
- Do not present the target behavior as current documentation while this task
  remains unimplemented.

### Task checklist

- [ ] Confirm the unresolved public-contract questions.
- [ ] Change the task status to `Approved` after the contract is confirmed.
- [ ] Add optional FastAPI-validated pagination parameters to the collection
  route.
- [ ] Add ordered, offset/limit page retrieval and total-count retrieval.
- [ ] Attach the confirmed total-count header on the defined responses.
- [ ] Add public integration coverage for paginated and unpaginated behavior,
  validation, ordering, empty pages, and header contents.
- [ ] Add public non-regression coverage for the other CRUD routes as needed.
- [ ] Update `README.md` with the implemented contract.
- [ ] Run the focused test suite and record the result.

### Requirement verification

- Optional parameters and normal invalid-input handling: public
  `GET /notes/` requests with omitted, malformed, and out-of-range query
  values; verify the successful array response and FastAPI `422` boundary.
- Bounded ascending-ID slices and total count: public seeded requests with
  both parameters, single parameters, and an empty/beyond-end page; verify
  item IDs, page length, and the confirmed response header against the seeded
  total.
- Full-list compatibility: public request without either parameter; verify
  the response remains a JSON array containing all seeded notes.
- CRUD compatibility: public create, detail, update, and delete requests
  using the existing API paths; verify their current status and payload
  behavior.
- Documentation: inspect the final README claims against the implemented
  route contract after tests pass.

### Additional implementation verification

- Run the existing test suite to catch regressions outside the new focused
  cases.
- Inspect the generated FastAPI route schema after implementation to ensure
  the optional parameters and validation constraints are exposed as intended.