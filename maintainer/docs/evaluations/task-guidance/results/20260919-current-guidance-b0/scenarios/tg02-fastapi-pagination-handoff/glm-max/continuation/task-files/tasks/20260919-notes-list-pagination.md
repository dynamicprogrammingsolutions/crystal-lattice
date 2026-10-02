# Add optional limit/offset pagination to GET /notes/

Planning handoff for adding optional `limit`/`offset` pagination to the notes
collection route: a bounded ascending-ID slice on request, the total note count
in a response header, unchanged full-list behavior without pagination,
standard FastAPI validation for bad values, and no changes to the other CRUD
routes. Planning only — implementation has not been approved or started.

## Requirements checklist

- [ ] R1 — `GET /notes/` accepts optional `limit` and `offset` query parameters; a paginated request returns a bounded slice of notes ordered by ascending `id`, as a bare JSON array with the same per-note shape as today.
- [ ] R2 — A paginated response carries the total note count in a response header (total = count of all notes in the table, not the remaining window; header name and presence scope per Q1/D1 below).
- [ ] R3 — A request without pagination parameters returns the current full-list JSON array, unchanged.
- [ ] R4 — Invalid `limit`/`offset` values (negative, non-integer) are rejected by FastAPI's standard validation (422); no custom validation code.
- [ ] R5 — All other routes (`POST /notes/`, `GET /notes/{note_id}/`, `PUT /notes/{note_id}/`, `DELETE /notes/{note_id}/`) keep their current behavior.
- [ ] R6 — `README.md` documents the changed collection behavior in the same reviewed change (AGENTS.md documentation policy).

## Open requirement questions (block execution)

- Q1 — Header presence scope: only on paginated responses, or on every `GET /notes/` response? Recommendation: paginated-only, so unpaginated responses stay byte-identical to today (strictest reading of R3) and every paginating client still receives the total.
- Q3 — Mixed parameter presence: either parameter alone triggers pagination (missing `offset` defaults to 0, missing `limit` means no upper bound), or both must be supplied together (422 otherwise). Recommendation: per-parameter defaults — simplest coherent contract; a lone `offset` returns the ascending tail.

## Supporting facts

- Routes live in `src/app/api/notes.py`; the router is mounted with prefix `/notes` (`src/app/main.py:15`). `GET /notes/` currently returns `await crud.get_all()` with no parameters, no `response_model`, and no headers (`src/app/api/notes.py:8-10`).
- `crud.get_all()` runs `database.fetch_all(notes.select())` with no explicit ORDER BY (`src/app/api/crud.py:4-5`). Other crud functions: `get`, `post`, `put`, `delete` (`src/app/api/crud.py:8-26`). CRUD route handlers take no query parameters.
- Data layer: `databases` async wrapper over SQLAlchemy Core against a SQLite file `./notes.db`, created at import time via `metadata.create_all(engine)` (`src/app/db.py`). Table columns: `id` (PK), `title`, `description`.
- Tests: `src/tests/test_notes.py` has two tests (full list → 200 + list; POST → 201). `src/tests/conftest.py` exposes a `test_app` fixture returning `TestClient(app)` without a context manager.
- Verified 2026-09-19 in a temporary venv (deps installed there, since removed; workspace untouched): with fastapi 0.141.1, starlette 1.6.0, databases 0.9.0, sqlalchemy 2.0.54, pydantic 2.13.5, Python 3.12 — the existing suite passes (2 passed) without lifespan running, because databases 0.9.0's SQLite backend connects lazily (`SQLiteBackend.connect()` is a no-op; the pool opens a connection per query). Dependencies in `pyproject.toml` are unpinned, so the executor must re-baseline at execution time.
- Verified in the same temporary environment with a throwaway app replicating the planned route shape:
  - `notes.select().order_by(notes.c.id.asc()).offset(o).limit(l)` returns the expected window; applying `.limit()` only when `limit` is not None works; `offset` beyond the table end returns `[]`; `limit=0` returns `[]`.
  - Count via `select(func.count()).select_from(notes)` + `fetch_one(...)[0]` returns the full-table count.
  - Setting a header on an injected `Response` parameter merges with the returned list body (no `JSONResponse` refactor needed).
  - `Query(default=None, ge=0)` yields 422 with the offending parameter located for `limit=-1`, `offset=-3`, `offset=abc`, `limit=1.5`; `limit=0&offset=-2` reports `offset`.
  - FastAPI auto-documents both optional parameters in `openapi.json`.
- Running the app or tests creates `./notes.db` relative to the CWD; `.gitignore` does not currently list it.
- Documentation surfaces: `README.md` (root, service-owned; currently states the collection route "returns every note as a JSON array"), `docs/development/index.md` ("No notes-query specification exists"), `docs/development/documentation.md` (process guidance). This variant has no client package or CLI.

## Execution plan

Status: Draft

Approach: keep the existing unpaginated code path untouched and add a paginated branch to the same route handler.

- Route (`src/app/api/notes.py`, `read_all_notes` only):
  - New parameters: `response: Response`, `limit: int | None = Query(default=None, ge=0)`, `offset: int | None = Query(default=None, ge=0)`.
  - Branch: when both `limit` and `offset` are `None` → `return await crud.get_all()` (current behavior, including absence of the header if Q1 is decided paginated-only).
  - Otherwise (paginated): `total = await crud.count()`, rows from `crud.get_paginated(limit, offset)` with missing `offset` treated as 0 and missing `limit` meaning no cap (per Q3), then `response.headers[...] = str(total)` and return the rows.
- CRUD (`src/app/api/crud.py`; `get_all` and the other four functions untouched):
  - `count()` → `database.fetch_one(select(func.count()).select_from(notes))`, return `row[0]`.
  - `get_paginated(limit, offset)` → `notes.select().order_by(notes.c.id.asc()).offset(offset)`, applying `.limit(limit)` only when `limit is not None`.
- API surface stays otherwise identical: no `response_model`, body remains a bare JSON array with the same per-note record shape, count is the full-table count, two sequential queries in paginated mode with no transaction wrapping.
- Explicitly out of scope: page-size cap (`le=`), page/next-link metadata, pagination on any other route, changes to `crud.get_all()` or the other route handlers.

### Implementation decisions and open questions

Decisions (visible for approval; locally reversible unless noted):

- D1 — Header name `X-Total-Count` (de-facto convention for collection totals; value is the decimal string of the full-table count). Public contract: confirm at approval.
- D2 — Validation bounds: `ge=0` on both parameters; `limit=0` is valid and returns an empty slice. No upper bound on `limit` (none requested; adding a cap would be a new constraint).
- D3 — Paginated response body stays a bare JSON array with the same per-note shape; no `response_model` added, keeping serialization identical to the current record dicts.
- D4 — The count query runs only on paginated requests (pairs with Q1 paginated-only). Accepted: a tiny read-consistency window between count and slice, acceptable at fixture scale.
- D5 — Only the paginated query is explicitly ordered `id asc`; `get_all()` stays unordered so the unpaginated path is unchanged (R3).
- D6 — CRUD helper names: `count()` and `get_paginated(limit, offset)`, matching the existing lowercase crud style.

Open (must be answered before approval; see top-level questions):

- Q1 — Header presence: paginated-only (recommended) vs every `GET /notes/` response.
- Q3 — Partial parameters: per-parameter defaults (recommended) vs requiring both together (422 otherwise).

### Documentation

- `README.md` (service-owned user documentation, root): extend the collection paragraph in the same reviewed change — unpaginated requests return the full array; optional `limit`/`offset` return an ascending-ID slice; paginated responses include the `X-Total-Count` header with the total note count (scope per Q1); invalid values produce standard FastAPI 422 errors. Shipped with the code, so no `Not implemented` marker.
- No new pages or directories: `docs/development/index.md` stays unchanged (no specification requested), and OpenAPI parameter documentation is generated automatically by FastAPI — no maintained generated source to regenerate.

### Task checklist

- [ ] 1. Baseline: create a venv, install `pyproject.toml` dependencies plus `pytest`, run `pytest src/tests` from the repo root, confirm the 2 existing tests pass, and record resolved versions (harness consumer check; note that this creates `./notes.db`).
- [ ] 2. `src/app/api/crud.py`: add `count()` and `get_paginated(limit, offset)` per the approach; leave `get_all` and the other functions untouched.
- [ ] 3. `src/app/api/notes.py`: extend `read_all_notes` with the parameters, branch, and header per the approach; leave the other four route handlers untouched.
- [ ] 4. Tests in `src/tests/test_notes.py` (using the existing `test_app` fixture; seed via `POST /notes/`; derive expectations differentially from a preceding full-list fetch so tests stay robust to rows left by other tests):
  - [ ] 4a. `limit=2&offset=1` returns ids 2–3 of the ascending-sorted full list; `X-Total-Count` equals the full-list length.
  - [ ] 4b. `limit=2` alone returns the first 2 ascending ids; `offset=2` alone returns the ascending tail from position 2.
  - [ ] 4c. `limit=0` → empty array + header; `offset` beyond the total → empty array + header.
  - [ ] 4d. Unpaginated request → 200 full array and (if Q1 paginated-only) no `X-Total-Count` header.
  - [ ] 4e. 422 for `limit=-1`, `offset=-2`, `offset=abc`, `limit=1.5` (standard FastAPI error body).
  - [ ] 4f. Regression round-trip for the other routes: create → read → update → delete; existing two tests remain untouched and passing.
- [ ] 5. `README.md`: update the collection paragraph in the same change as the code (audience: API clients of the notes service).
- [ ] 6. `.gitignore`: add `notes.db` (runtime artifact of running the app or tests).
- [ ] 7. Run the full suite twice (state-independence check against the persistent sqlite file) and confirm all tests pass; update the requirement evidence and this checklist.

### Requirement verification

- R1 + R2 — New integration tests through `TestClient` (real app + real SQLite across the HTTP boundary): window equality against the ascending-sorted full list, and `X-Total-Count` equal to the full-list length. No mocks bypassing the boundary.
- R3 — Existing `test_read_all_notes` still passes, plus the explicit no-header assertion (4d) if Q1 is paginated-only; diff review confirms `crud.get_all()` and the route defaults are untouched.
- R4 — 422 assertions in 4e against the standard FastAPI error body.
- R5 — Existing tests plus the new round-trip test (4f); diff review confirms the other route handlers are unchanged.
- R6 — Inspection of `README.md` in the same change; wording matches the implemented behavior.

### Additional implementation verification

- Run the suite twice in one session to prove tests do not depend on the persistent `./notes.db` contents (differential expectations should make this robust).
- After execution, `git status` should show only the intended files (`crud.py`, `notes.py`, `test_notes.py`, `README.md`, `.gitignore`, this task file) — `notes.db` must be ignored, not committed.