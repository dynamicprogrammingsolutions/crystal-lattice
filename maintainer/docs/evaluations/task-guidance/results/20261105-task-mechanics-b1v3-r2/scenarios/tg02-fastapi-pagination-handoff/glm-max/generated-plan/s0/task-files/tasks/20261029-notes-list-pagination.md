# Notes list pagination (limit/offset + total-count header)

Add optional `limit`/`offset` query pagination to `GET /notes/` so clients can
request a bounded ascending-ID slice and receive the total note count in a
response header. Planning only: this task records the decided approach and
open questions; implementation has not been approved or started.

## Requirements checklist

- [ ] `GET /notes/` accepts optional integer query parameters `limit` and
  `offset` and, when pagination is requested, returns a JSON array slice of
  notes ordered by ascending `id`, bounded by `offset` (skip) and `limit`
  (max rows).
- [ ] Paginated list responses carry the total number of notes in the
  database in a response header (header name proposed `X-Total-Count`,
  pending the open question below).
- [ ] A `GET /notes/` request without `limit` and `offset` keeps the current
  behavior exactly: full list as a JSON array, no changes to status, body, or
  headers.
- [ ] Invalid parameter values (non-integers, values below the accepted
  minimums) produce normal FastAPI validation errors (`422`), with no custom
  error handling added.
- [ ] The other CRUD routes (`POST /notes/`, `GET /notes/{id}/`,
  `PUT /notes/{id}/`, `DELETE /notes/{id}/`) are unchanged in behavior,
  status codes, and payloads.
- [ ] Maintained documentation that describes the collection route is updated
  in the same change as the code (README.md currently states the collection
  route returns every note as a JSON array).

## Open questions

Requirement questions (answers change required outcomes; ask before resolving):

1. **Total-count header scope** — Should the total-count header appear only
   on paginated responses, or on every `GET /notes/` response including
   unpaginated full-list responses? The requirement "keep the current
   full-list array behavior" is read strictly here as "unpaginated responses
   are unchanged", but adding an informational header to all responses would
   not break the array body. *Recommendation: paginated responses only.*
2. **Validation bounds** — Proposed: `limit >= 1`, `offset >= 0`
   (`ge=1` / `ge=0`), leaving `limit=0` a validation error. Alternative is to
   allow `limit >= 0` (empty slice) or leave bounds unvalidated beyond
   integer type. *Recommendation: `limit >= 1`, `offset >= 0`.*

Material decisions needing confirmation (user-visible API surface):

3. **Header name** — Proposed `X-Total-Count` (common convention for
   collection totals).
4. **Documentation scope** — `docs/development/index.md` records that no
   notes-query specification exists. Decide whether this change only updates
   `README.md` (smallest structure that serves API consumers) or also authors
   a notes-query specification under `docs/development/`. *Recommendation:
   README update required; spec only if the maintainer wants query semantics
   specified.*

## Supporting facts

- Current route: `src/app/api/notes.py` `read_all_notes` returns
  `crud.get_all()` directly; `crud.get_all` (`src/app/api/crud.py`) runs
  `notes.select()` with no `ORDER BY`, so an ascending slice needs an explicit
  `order_by(notes.c.id.asc())` in the paginated query only.
- Storage: SQLite file `./notes.db` through `databases` + SQLAlchemy
  (`src/app/db.py`); `notes` columns are `id` (integer PK), `title`,
  `description`. The file persists across processes and test runs, so tests
  cannot assume an empty database.
- Tests: `src/tests/test_notes.py` uses `fastapi.testclient.TestClient` with
  the lifespan-managed DB connection from `src/tests/conftest.py`. The HTTP
  boundary through the real app and real SQLite is the right evidence level
  for these requirements; no mocks needed.
- `pyproject.toml` pins no `requires-python`; use `Optional[int]` typing for
  the query parameters rather than `int | None` to avoid assuming 3.10+.
- FastAPI serializes the current raw `databases` Row objects fine (existing
  behavior), so returning the slice the same way introduces no new
  serialization path.
- Documentation to keep true: `README.md` ("The collection route currently
  returns every note as a JSON array") must change with the code.
  `docs/development/index.md` states "No notes-query specification exists."

## Execution plan

Status: Draft

### Approach

Single deliverable, one code path addition plus its evidence. The route owns
the HTTP contract (query params, header, unchanged unpaginated behavior);
`crud` owns the new SQL; README owns the public claim.

Route (`src/app/api/notes.py`): `read_all_notes` gains `response: Response`,
`limit: Optional[int] = Query(None, ge=1)` and
`offset: Optional[int] = Query(None, ge=0)` (bounds pending open question 2).
When both parameters are `None`, it returns `crud.get_all()` unchanged —
identical code path to today, so no-param behavior is preserved by
construction rather than by coincidence. Otherwise it fetches
`crud.get_page(limit, offset)` and `crud.count_all()`, sets
`response.headers["X-Total-Count"] = str(total)`, and returns the slice list.
Both params are independent: offset without limit skips rows and returns the
remainder; limit without offset takes the first page.

CRUD (`src/app/api/crud.py`): add `get_page(limit, offset)` building
`notes.select().order_by(notes.c.id.asc()).offset(offset).limit(limit)` and
`count_all()` building `select(func.count()).select_from(notes)`. Existing
functions stay untouched.

No new modules or abstractions; no changes to models, db, main, or the other
route handlers.

### Task checklist

- [ ] Add `limit`/`offset` query params, paginated branch, and total-count
  header to `read_all_notes` (`src/app/api/notes.py`).
- [ ] Add `crud.get_page(limit, offset)` and `crud.count_all()`
  (`src/app/api/crud.py`).
- [ ] Update `README.md` collection-route description to describe optional
  pagination and the total-count header.
- [ ] (If approved) author notes-query specification and update
  `docs/development/index.md` status line.
- [ ] Update `src/tests/test_notes.py`: keep the no-param full-list test;
  add paginated-slice + header + ascending-order coverage, validation-error
  coverage, and regression coverage for POST/GET/PUT/DELETE routes.
- [ ] Run the pytest suite and confirm it collects and exits cleanly.

### Requirement verification

- Ascending-ID bounded slice + header: integration test through `TestClient`
  — POST several notes, record their IDs, `GET /notes/?limit=..&offset=..`,
  assert 200, body is the expected subsequence of created IDs in ascending
  order, and the header equals the total note count (cross-checked against a
  pre-request DB count or before/after delta so pre-existing `notes.db` rows
  cannot flake the test).
- Unpaginated behavior unchanged: existing
  `test_read_all_notes` (200, JSON array) plus an assertion that a no-param
  response carries no total-count header, if open question 1 resolves to
  "paginated only".
- FastAPI validation: `GET /notes/?limit=abc` and below-minimum values return
  422 with the standard FastAPI error shape; no custom handler involved.
- Other routes unchanged: existing `test_crud_routes_exist` plus regression
  assertions for read/update/delete status codes and payload shapes.
- Documentation: README text matches implemented behavior in the same
  reviewed change (reviewer check; no automated evidence).

### Implementation decisions and open questions

- Open questions 1–4 above remain unresolved and block final implementation
  details (header scope, bounds, header name, documentation scope). They are
  presented for approval; the plan stays Draft until answered.
- Resolved locally as non-material: parameter names are `limit`/`offset`
  (named by the request); `Optional[int]` typing for Python-version safety;
  both params independently optional; paginated slice returned through the
  same raw-Row serialization as the current full list.

### Documentation

- `README.md` (audience: API consumers): replace the "returns every note"
  sentence with the optional `limit`/`offset` semantics and the
  total-count header. Updated in the same change as the code so no public
  claim is left stale.
- `docs/development/index.md` line "No notes-query specification exists." is
  updated only if the specification is authored (open question 4). No other
  docs restructuring; no placeholder pages.

### Additional implementation verification

- Only distinct material risk: SQLite test-state coupling. `./notes.db`
  persists between runs, so the paginated tests must seed their own notes via
  the API and assert relative properties (created-ID subsequence, count
  delta) instead of absolute database contents. This is folded into the
  verification design above; no separate test infrastructure is needed.
