# Add optional limit/offset pagination to `GET /notes/`

Add optional `limit`/`offset` query pagination to the notes collection route:
clients can request a bounded, `id`-ascending slice and receive the total note
count in a response header. Requests without pagination keep the current
full-list array behavior, invalid query values rely on normal FastAPI
validation, and the other CRUD routes do not change. Planning only — nothing
has been implemented.

## Requirements checklist

- [ ] `GET /notes/` accepts optional `limit` and `offset` query parameters.
      When pagination is requested, the response body is the bounded slice of
      notes ordered by `id` ascending: `offset` rows skipped first, at most
      `limit` rows returned.
- [ ] Paginated responses carry the total note count in a response header
      (header name recommended as `X-Total-Count`, pending approval — see Q1).
- [ ] Requests without pagination parameters keep the current behavior: 200
      with the full, unbounded JSON array of every note as the body.
- [ ] Invalid query values are rejected by normal FastAPI validation (standard
      422 error body); no hand-rolled validation or custom error handling.
- [ ] The other CRUD routes (`GET /notes/{note_id}/`, `POST /notes/`,
      `PUT /notes/{note_id}/`, `DELETE /notes/{note_id}/`) keep their current
      signatures, status codes, and behavior.
- [ ] `README.md` documents the optional pagination and count header in the
      same reviewed change as the code (repo documentation policy).

## Requirement questions and material decisions (pending approval)

These are recommendations recorded in the Draft plan; approving the plan
approves them as written, or tell me which to change.

- **Q1 — Header name** (material, public contract): recommend `X-Total-Count`,
  the common convention for collection-count headers. Any name works
  mechanically; clients will depend on the exact string.
- **Q2 — Header on non-paginated responses** (requirement question): recommend
  the header only when pagination is requested, so non-paginated responses
  stay exactly as today (no new header) — the strictest reading of "keep the
  current full-list array behavior". Alternative: always send the header.
- **Q3 — Negative values** (material, public validation behavior): recommend
  declaring `ge=0` on both parameters via `Query`, so `?limit=-1` is a normal
  422. Unconstrained ints would pass validation and reach obscure SQLite
  semantics (negative `LIMIT` means "no limit"). `limit=0` stays valid: empty
  array plus count header.
- **Q4 — One parameter alone** (material, public behavior): recommend the
  parameters are independent — either one activates pagination; missing
  `offset` means 0, missing `limit` means no upper bound. Alternative: require
  both together (422 on exactly one).

## Supporting facts

- Current chain: `read_all_notes` in `src/app/api/notes.py` → `get_all()` in
  `src/app/api/crud.py` → `database.fetch_all(notes.select())` — no
  parameters, no `ORDER BY`; FastAPI serializes the returned rows as a JSON
  array. Existing `test_read_all_notes` asserts only 200 + list.
- App shape: FastAPI router mounted at `/notes` (`src/app/main.py`); async
  `databases` + SQLAlchemy core over a SQLite file `./notes.db` created at
  import time relative to the working directory; table
  `notes(id PK, title, description)` (`src/app/db.py`).
- The response body stays a JSON array in both modes; only paginated responses
  add the count header. No `response_model` changes are needed or planned.
- Tests use `fastapi.testclient.TestClient` against the real app
  (`src/tests/conftest.py`). There is no DB reset between tests and
  `notes.db` persists on disk, so pagination tests need deterministic seeding
  (a harness reset) to assert exact slices and totals.
- Verified run command (baseline: 2 passed, working tree restored afterward):
  `cd src && UV_PROJECT_ENVIRONMENT=<tmp-dir> uv run --project <repo-root>
  --with pytest python -m pytest -q`. pytest is not declared in
  `pyproject.toml`, so `uv run --with pytest` supplies it. Plain `python3`
  (no deps installed) and the pyenv 3.11.12 env (missing `databases`) cannot
  run the suite.
- `uv run` creates an untracked `uv.lock` at the repo root and the test run
  creates an untracked `src/notes.db`; both were removed after the baseline
  probe.
- Documentation surface: `README.md`'s collection-route sentence ("currently
  returns every note as a JSON array") is the only public claim to update.
  `docs/development/index.md` states no notes-query specification exists; no
  new spec page is warranted for this change (smallest-structure policy).
- This variant has no Python client package or CLI (server-only fixture), so
  no client-side deliverables are in scope.
- `docs/development/documentation.md` was read; only a local factual README
  correction is planned, no doc restructuring.

## Execution plan

Status: Draft

### Approach

Single deliverable at the notes service's public HTTP boundary.

1. `src/app/api/crud.py` — add a total-count helper
   (`database.fetch_val(sqlalchemy.select(func.count()).select_from(notes))`)
   and a paginated fetch
   (`notes.select().order_by(notes.c.id.asc()).offset(offset).limit(limit)`,
   applying each clause only when its value is provided). Leave `get_all()`
   untouched so the non-paginated path is literally the current code.
2. `src/app/api/notes.py` — extend `read_all_notes` with an injected
   `response: Response` plus `limit: Annotated[int | None, Query(ge=0)] = None`
   and `offset: Annotated[int | None, Query(ge=0)] = None` (fall back to
   `Optional[int]` only if the resolved Python needs it). Branch inside the
   handler: either parameter present → paginated slice via the new crud
   functions and set the count header on the injected `Response`; otherwise →
   existing `crud.get_all()` unchanged. No `response_model`, no status-code
   changes, no changes to other route signatures.
3. `src/tests/conftest.py` + `src/tests/test_notes.py` — make DB state
   deterministic (clear the `notes` table between tests through the same
   app/database machinery), then add tests: non-paginated regression (full
   array, no count header per Q2), paginated slice ordering and boundaries
   with seeded rows, header value equal to the seeded total, each
   single-parameter case, `limit=0` empty slice, and 422s for non-integer and
   negative values. Add a small regression test covering
   `GET /notes/{id}/`, `PUT`, and `DELETE` (currently uncovered) to evidence
   the "other routes unchanged" requirement.
4. `README.md` — extend the collection-route sentence with the optional
   parameters, ascending-`id` ordering when paginated, the count header, and
   the unchanged full-array behavior without parameters.

### Implementation decisions and open questions

Covered by Q1–Q4 in "Requirement questions and material decisions" above;
approving the plan resolves all four to the stated recommendations. No
additional open questions. Not proposed: an upper bound (`le`) on `limit` (not
requested), transactional coupling of the count and slice queries
(single-process fixture, low value), and envelope-style response bodies (the
count-header design keeps the body an array in both modes).

### Documentation

- Update `README.md` in the same reviewed change as the code: collection route
  supports optional `limit`/`offset`, results are ordered by `id` ascending
  when paginated, the total count is returned in the `X-Total-Count` response
  header, and behavior without parameters is unchanged. Audience: API users;
  smallest structure (no new pages, no spec).

### Task checklist

- [ ] Add paginated-fetch and total-count helpers in `src/app/api/crud.py`
      without touching `get_all()`.
- [ ] Extend `read_all_notes` in `src/app/api/notes.py` with `limit`/`offset`
      Query parameters, the pagination branch, and the count header.
- [ ] Make test DB state deterministic and add pagination, validation, and
      other-routes regression tests in `src/tests/`.
- [ ] Update the collection-route description in `README.md`.
- [ ] Run the full suite via the verified uv command and clean untracked
      runtime artifacts (`uv.lock`, `src/notes.db`).

### Requirement verification

- R1 paginated slice, R2 count header, R3 non-paginated behavior, R4
  validation: new and existing tests through the public HTTP boundary
  (`TestClient` → real app → SQLite), asserting seeded ids and order, header
  value, full array without the header, and 422 bodies. Existing
  `test_read_all_notes` must keep passing unchanged.
- R5 other routes unchanged: no source changes to those handlers (diff
  review), plus the new read-by-id/update/delete regression test.
- R6 README updated in the same change: the change's diff contains the README
  edit; final wording reviewed by the user.

### Additional implementation verification

- Run the suite from a clean tree (no pre-existing `src/notes.db`) to confirm
  import-time DB creation and the seeding work deterministically.
- Confirm the working tree has no unintended artifacts before finishing.