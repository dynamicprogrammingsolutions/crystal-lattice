# Notes collection pagination (`GET /notes/`)

Add optional `limit`/`offset` pagination to the notes collection route so
clients can request a bounded ascending-ID slice and receive the total note
count in a response header, while requests without pagination parameters keep
the current full-list array behavior. Planning handoff only — implementation
has **not** started and is not authorized by this file alone.

## Requirements checklist

All requirements are open; nothing has been implemented or verified.

- [ ] R1. `GET /notes/` accepts optional `limit` and `offset` query parameters, and requests that use pagination receive a bounded slice of the notes list.
- [ ] R2. Paginated responses return notes ordered by ascending `id`, skipping the first `offset` notes and returning at most `limit` notes; the body remains a JSON array of note objects in the current `{id, title, description}` shape.
- [ ] R3. Paginated responses include a response header carrying the total number of notes currently stored — the total across all notes, not only the returned slice. (Header name pending Q1.)
- [ ] R4. Requests without either pagination parameter are unchanged: the full notes list as a JSON array, with no total-count header added.
- [ ] R5. Invalid pagination values are rejected by FastAPI's standard request validation (422 responses); no hand-written validation logic. Whether negative values count as invalid is pending Q3.
- [ ] R6. The other routes — `GET /notes/{note_id}/`, `POST /notes/`, `PUT /notes/{note_id}/`, `DELETE /notes/{note_id}/` — behave exactly as before.
- [ ] R7. `README.md` (the maintained user-facing description of the public API) describes the new optional pagination and the total-count header, updated in the same change as the code per the `AGENTS.md` documentation policy.

## Open decisions before implementation

User-visible contract details that need approval together with the plan;
tradeoffs are in "Implementation decisions and open questions" below.

- Q1. Exact name of the total-count response header. Recommendation: `X-Total-Count`.
- Q2. When pagination activates and what the defaults are. Recommendation: pagination applies when either `limit` or `offset` is present; missing `offset` → `0`; missing `limit` → all remaining notes from `offset`.
- Q3. Whether negative values are invalid. Recommendation: declare both parameters with `ge=0` so negatives are rejected by FastAPI's normal validation (422), consistent with R5.

## Supporting details

Repository facts (inspected 20260920; working tree clean at `cd0a7727`):

- `GET /notes/` is `read_all_notes` in `src/app/api/notes.py:8-10`, returning
  `crud.get_all()` (`src/app/api/crud.py:4-5`): `database.fetch_all(notes.select())`
  with no `ORDER BY` and no response model. The router is mounted at `/notes`
  (`src/app/main.py:15`); all five routes share `src/app/api/crud.py`.
- Storage is `databases` + SQLAlchemy over file-backed SQLite `./notes.db`
  (`src/app/db.py`); table columns: `id` (integer PK), `title`, `description`.
- `README.md` documents the public API and currently says the collection route
  "returns every note as a JSON array" — accurate for no-parameter requests but
  incomplete after this change; it is the only maintained user-facing doc.
  `docs/development/index.md` records that no notes-query specification exists;
  this change does not require creating one, and no generated docs exist.
- Existing tests: `src/tests/test_notes.py` (GET full list is a 200 JSON array;
  POST returns 201) via `fastapi.testclient.TestClient` over the real app
  (`src/tests/conftest.py`) — integration through the HTTP boundary against the
  real SQLite database. Existing coverage proves only the GET-shape and POST
  cases, so it is not sufficient evidence for R6.
- Test-state hazard: `notes.db` is a real file that is not recreated between
  runs and is not gitignored. New tests must not assume an empty database;
  derive expectations from a baseline fetched through the API (the full list)
  rather than from absolute counts or IDs.
- Environment: `pytest` 9.1.1 is importable, but `fastapi`, `databases`,
  `sqlalchemy`, and `httpx` are **not installed** in the default `python3`
  (3.12.1). `uv` is available. The verification environment must be created at
  execution time (e.g. `uv run --with fastapi --with 'databases[sqlite]'
  --with sqlalchemy --with httpx --with pytest python -m pytest src/tests`);
  no dependency installation was performed during planning.
- Mechanism notes: inject `response: Response` into the handler and set the
  header before returning the body; typed query parameters declared with
  `Query(default=None, ge=0)` produce 422s without custom code;
  `sqlalchemy.func.count()` over `notes` provides the total. `Optional[int]`
  annotations keep the change compatible with the unpinned FastAPI.
- Scope boundary: this fixture variant has no separate client package or CLI,
  so the only affected public boundary is the HTTP API of the notes service —
  therefore a single task with no subtasks.

## Execution plan

Status: Draft

### Approach

1. `src/app/api/notes.py`: extend `read_all_notes` with
   `limit: Optional[int] = Query(default=None, ge=0)` and
   `offset: Optional[int] = Query(default=None, ge=0)` (per Q3), plus an
   injected `response: Response` for the header.
2. Branch in the handler: when neither parameter is present, call the existing
   `crud.get_all()` unchanged — the no-parameter request path is not touched
   (R4). Otherwise use the new crud functions.
3. `src/app/api/crud.py`: add `get_page(offset=0, limit=None)` building
   `notes.select().order_by(notes.c.id.asc()).offset(offset)`, appending
   `.limit(limit)` only when a limit is given (Q2), and `count_notes()` via
   `select(func.count()).select_from(notes)`. Leave `get_all()` untouched.
4. Set `response.headers["<Q1 header>"] = str(total)` on paginated responses
   and return the slice as a plain array (R2, R3, R4).
5. Optional, recommended: declare the header in the route's OpenAPI
   `responses` metadata so `/docs` documents the public contract.
6. Update `README.md` (R7) and add the integration tests; run the suite.

Risks: shared mutable `notes.db` state can make brittle absolute-count
assertions (mitigated by baseline-based assertions); unpinned dependencies
mean the executor should confirm `databases` accepts the installed SQLAlchemy
count-query form; the OpenAPI header metadata is optional and must not block
the behavioral change if tooling quirks arise.

### Implementation decisions and open questions

- Q1 (material, blocking): Header name for the total count. This is part of
  the public HTTP contract, so it needs approval. Recommendation:
  `X-Total-Count` — the widely used convention for collection totals.
  Alternative: `Total-Count` (shorter, less conventional). README, tests, and
  any OpenAPI metadata must all use the approved name.
- Q2 (material, blocking): Activation and defaults. Recommendation: pagination
  applies when either `limit` or `offset` is present; missing `offset` → `0`;
  missing `limit` → all remaining notes from `offset` (standard SQL
  LIMIT/OFFSET semantics). Alternatives: require both parameters, or apply
  `ORDER BY id` to all requests — the latter is rejected because it would
  change the no-parameter response path (R4).
- Q3 (minor, recommend resolving with Q1/Q2): Declare both parameters with
  `ge=0` so negative values are also rejected by FastAPI's standard validation
  (422), keeping R5 satisfied entirely by framework validation. Without a
  constraint, negative values would reach SQLite and produce
  implementation-defined results; no custom validation is added either way.
- Resolved decision D1: paginated bodies remain a plain JSON array, not an
  envelope object — the request describes a "slice" of the current array with
  the total in a header, and R4 pins the same shape for the no-parameter case.
- Resolved decision D2: no upper cap on `limit` — none was requested, and
  inventing one would add unspecified behavior.
- Resolved decision D3: the no-parameter path keeps `crud.get_all()` exactly
  as-is (no ordering change), so its current behavior is preserved by
  construction.

### Documentation

Audience: API consumers. Update the collection-route paragraph in `README.md`
to describe the optional `limit`/`offset` parameters (ascending-ID slice,
defaults per Q2), the total-count response header (approved Q1 name), and that
requests without parameters keep returning the full array. No new pages, no
spec file (none exists and none is needed), nothing generated.

### Task checklist

- [ ] T1. Add optional query parameters and `Response` injection to
      `read_all_notes` (`src/app/api/notes.py`).
- [ ] T2. Add `get_page(offset, limit)` and `count_notes()` to
      `src/app/api/crud.py`; leave `get_all()` unchanged.
- [ ] T3. Route the paginated branch through the new crud functions and set
      the total-count header; keep the no-parameter branch on `get_all()`.
- [ ] T4. (Optional, recommended) Add OpenAPI `responses` metadata documenting
      the header on the 200 response.
- [ ] T5. Update `README.md` per the Documentation section.
- [ ] T6. Add integration tests to `src/tests/test_notes.py`.
- [ ] T7. Create the runtime environment (dependencies are not installed) and
      run the full test suite; record results.

### Requirement verification

Evidence boundary for behavioral requirements: HTTP integration through
`fastapi.testclient.TestClient` → real FastAPI app → real SQLite, asserting
against a baseline fetched through the API so pre-existing `notes.db` contents
do not affect results.

- R1 + R2: new tests — `?limit=2&offset=1` returns 200 with body equal to
  `baseline[1:3]` with ascending `id`; `?limit=2` equals `baseline[:2]`;
  `?offset=1` equals `baseline[1:]` (per Q2).
- R3: the same tests assert the approved header equals `str(len(baseline))` on
  paginated responses.
- R4: new test — no-parameter response body equals the full baseline list and
  does not contain the total header; existing `test_read_all_notes` remains as
  a shape smoke test.
- R5: new tests — `?limit=abc` (and, if Q3 is approved, `?limit=-1` and
  `?offset=-1`) produce 422 with FastAPI's standard validation detail; the diff
  contains no custom validation logic.
- R6: new focused regression test exercising `GET /notes/{id}` (existing and
  missing → 404), `POST` (201), `PUT`, and `DELETE`; existing coverage proves
  only POST, so this test is the evidence for the rest.
- R7: not machine-verifiable — confirmed by reviewing the `README.md` diff
  during execution.

### Additional implementation verification

- Offset beyond the end of the list: `?offset=len(baseline)` returns an empty
  array (not an error) with the correct total header — a cheap extra assertion
  in the slice test covering the empty-page edge without needing an empty
  database.
- Confirm the approved header name is used consistently across code, README,
  and test assertions.