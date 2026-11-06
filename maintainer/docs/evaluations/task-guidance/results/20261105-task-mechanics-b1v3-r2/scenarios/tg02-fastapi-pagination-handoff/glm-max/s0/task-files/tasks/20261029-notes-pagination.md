# Optional limit/offset pagination for `GET /notes/`

Add optional `limit`/`offset` query pagination to the notes collection route.
Paginated requests return an ascending-ID slice as a JSON array plus a
response header carrying the total note count. Requests without pagination
keep the current full-list array behavior. Invalid values fall out of normal
FastAPI query validation. No other CRUD route changes. Planning only — not
yet implemented.

## Requirements checklist

- [ ] `GET /notes/` accepts optional `limit` and `offset` integer query parameters. When pagination parameters are supplied, the response body is the requested slice of notes ordered by ascending `id` (`offset` rows skipped first, at most `limit` rows returned), still as a plain JSON array.
- [ ] Paginated responses include a response header carrying the total number of notes in the collection; the total is not reduced by `limit`/`offset`. (Exact header name: see plan decision D2, pending ratification.)
- [ ] Requests without pagination parameters keep the current behavior exactly: every note returned as a JSON array, no new header, no added ordering or envelope.
- [ ] Invalid pagination values (e.g. non-integer input, or values outside the agreed constraints) are rejected by FastAPI's standard query validation (HTTP 422); no hand-rolled validation or alternate error shape.
- [ ] The other CRUD routes (`POST /notes/`, `GET /notes/{id}/`, `PUT /notes/{id}/`, `DELETE /notes/{id}/`) keep their current behavior and contracts.
- [ ] `README.md` describes the new pagination behavior in the same change that introduces it (approved policy: new public claims ship with the code that makes them true).

## Requirement questions

- None. The request fixes the required outcomes; constraint specifics and the
  header name are contract details tracked as plan decisions (D1–D5), not
  requirement questions.

## Supporting details

Facts verified by reading the repository:

- `src/app/api/notes.py` — `read_all_notes()` currently returns
  `await crud.get_all()` with no parameters; router is mounted at `/notes` in
  `src/app/main.py`.
- `src/app/api/crud.py` — `get_all()` runs `notes.select()` with no `ORDER BY`;
  the other CRUD helpers (`get`, `post`, `put`, `delete`) are independent of it.
- `src/app/db.py` — sqlite via `databases` + SQLAlchemy Core; `notes` table has
  integer primary key `id`, plus `title` and `description`.
- `src/tests/test_notes.py` + `src/tests/conftest.py` — two `TestClient` tests
  (`test_read_all_notes` asserts a JSON list; `test_crud_routes_exist` asserts
  POST returns 201). `pytest` is imported but is not declared in
  `pyproject.toml`; the environment is expected to provide it.
- The DB is the file `./notes.db`, created at import time; tests currently do
  not reset it, so new pagination tests need deterministic table state.
- `README.md` states: "The collection route currently returns every note as a
  JSON array." — this sentence must be updated when pagination lands.
- `docs/development/index.md` notes no notes-query specification exists; no new
  spec page is warranted for this change (smallest structure that helps the
  reader: README only).

## Execution plan

Status: Draft

### Design

Contract (decisions D1–D5 below, pending ratification with plan approval):

- Query parameters on `GET /notes/`: `limit` (int, optional) and `offset`
  (int, optional). Either one alone activates pagination; `offset` defaults to
  0, an absent `limit` means "all remaining rows after the offset".
- Paginated body: bare JSON array of note objects (no envelope), ordered
  `ORDER BY id ASC`, `LIMIT limit OFFSET offset`.
- Paginated header: `X-Total-Count: <total notes in table>`; the count ignores
  `limit`/`offset`. No header is added on the unpaginated path.
- Validation: plain `int` typing plus `Query` numeric constraints, so bad input
  produces FastAPI's default 422 with no custom handling.

Component responsibilities:

- `src/app/api/crud.py` gains two helpers and keeps `get_all` untouched:
  - `get_page(offset, limit)` — `notes.select().order_by(notes.c.id.asc()).limit(limit).offset(offset)`; omitted `limit` is expressed by not chaining `.limit()`.
  - `count_notes()` — `SELECT count(*)` over `notes` (e.g. via
    `sqlalchemy.func.count()` fetched with `database.fetch_val`).
- `src/app/api/notes.py` — `read_all_notes` takes `limit` and `offset` as
  `Query` parameters and a `Response` parameter (FastAPI merges headers set on
  it into the returned object's response). If neither parameter was supplied,
  it keeps the existing `crud.get_all()` call verbatim; otherwise it calls the
  new helpers, sets `X-Total-Count`, and returns the slice list. Other route
  functions are not edited.
- Tests: `src/tests/test_notes.py` gains a deterministic-state fixture (clear
  the `notes` table via SQLAlchemy Core through the real engine, then seed via
  the public `POST /notes/` route) plus pagination tests; existing tests stay
  as-is.

Verification strategy: component/integration tests through `TestClient` over
the real FastAPI app and the real sqlite adapter — no mocks of the transport
or DB, since the claim is about the HTTP contract and actual slicing/counting.
The existing suite run doubles as regression evidence that unpaginated
behavior and the other CRUD routes are unchanged.

### Steps

1. Add `get_page(offset, limit)` and `count_notes()` to `src/app/api/crud.py`.
2. Extend the `GET /notes/` handler in `src/app/api/notes.py` with optional
   `Query` parameters, the header, and the unchanged no-pagination path.
3. Add the deterministic fixture and pagination tests to `src/tests/`:
   bounded ascending slice, offset skipping, total-count header (including a
   case where the count exceeds the page size), unpaginated full-list
   regression with seeded rows, and 422 cases for invalid values.
4. Update the collection-route sentence in `README.md`.
5. Run the full test suite; confirm the new tests and the two existing tests
   pass cleanly.

### Implementation decisions and open questions

- D1 (parameter constraints): `limit` integer `>= 1`, `offset` integer
  `>= 0`. Recommended: no upper bound on `limit` (fixture has no scale
  concern); `limit=0` returns 422 as "invalid". Ratified by plan approval.
- D2 (header name): `X-Total-Count`. Recommended as the common convention;
  ratify at approval.
- D3 (activation rule): pagination activates when either parameter is
  present; each defaults independently. Alternative rejected: requiring both
  together (stricter but less useful, and the request says clients "request a
  bounded slice" via optional params without tying them together).
- D4 (body shape): paginated body remains a bare JSON array. Alternative
  rejected: `{items, total}` envelope — the request places the total in a
  header precisely so the array shape is preserved.
- D5 (unpaginated path): no `ORDER BY`, no header, no envelope; `get_all()` is
  not modified, so current behavior is preserved by construction.
- Open question: none blocking. If a different header name or constraint set
  is preferred, say so at approval and the plan will be adjusted before
  execution.

### Documentation

- Audience: API clients (README.md is the only maintained user-facing doc).
- Change: rewrite the sentence stating the collection route "returns every
  note as a JSON array" to state the default full-array behavior plus the
  optional `limit`/`offset` slice and `X-Total-Count` header, in the same
  change as the code (approved docs policy).
- No new pages or directories; no spec file created (`docs/development/index.md`
  stays accurate).

### Task checklist

- [ ] Add paginated fetch and total-count helpers to `src/app/api/crud.py`
      without touching `get_all()`.
- [ ] Extend `GET /notes/` in `src/app/api/notes.py` with optional `limit`/
      `offset` query params, `X-Total-Count` on paginated responses, and the
      unchanged no-pagination path.
- [ ] Add deterministic DB-state fixture and pagination regression tests in
      `src/tests/` (slice + ordering, offset, header total, unpaginated
      regression, 422 invalid values).
- [ ] Update `README.md` collection-route description in the same change.
- [ ] Run the full test suite; new and existing tests pass cleanly.

### Requirement verification

- Pagination slice + ordering + header (reqs 1–2): new `TestClient` tests
  against the real app and sqlite DB, seeding via `POST /notes/`; assert body
  ids/order, slice bounds, and header value with a dataset larger than one
  page.
- Unpaginated behavior unchanged (req 3): new seeded regression test asserting
  the full array with no extra header, plus the existing
  `test_read_all_notes` still passing.
- Normal FastAPI validation (req 4): new tests asserting HTTP 422 for
  non-integer input and constraint violations, with FastAPI's default error
  body.
- Other CRUD routes unchanged (req 5): existing tests
  (`test_crud_routes_exist`) run unmodified and pass; code inspection confirms
  only the list route and new crud helpers are touched.
- Documentation (req 6): README diff reviewed in the same change; claim
  matches the tested behavior.

### Additional implementation verification

- Deterministic tests despite the persistent `./notes.db`: the fixture clears
  the table through the real engine before pagination tests (test-infra
  change; its value is proven by the new tests as real consumers). Risk if
  skipped: slice/count assertions flake on stale rows from prior runs.
- `pytest` is not declared in `pyproject.toml`; if the environment lacks it,
  report the suite as not run rather than bypassing.
