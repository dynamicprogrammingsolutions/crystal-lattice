# Add optional limit/offset pagination to GET /notes/

Extend the notes collection route with optional `limit` and `offset` query
parameters that return a bounded ascending-ID slice and carry the total note
count in a response header, while preserving the current full-list array
behavior for requests without pagination and leaving every other CRUD route
unchanged. Plan only — execution is not approved yet.

## Requirements checklist

- [ ] `GET /notes/` accepts optional `limit` and `offset` query parameters; when pagination is requested, the response body is the bounded slice of notes ordered by ascending ID, with `offset` applied before `limit` (exact single-parameter semantics: open question 3).
- [ ] A paginated response carries the total note count of the whole collection in a response header (header name and presence rule: open questions 1–2).
- [ ] A request without pagination parameters returns the current full-list JSON array behavior, unchanged.
- [ ] Invalid pagination values are rejected through normal FastAPI request validation (422), with no custom error handling added.
- [ ] `POST /notes/`, `GET /notes/{note_id}/`, `PUT /notes/{note_id}/`, and `DELETE /notes/{note_id}/` behave exactly as before.
- [ ] The maintained README description of the collection route reflects the new supported behavior, updated in the same change as the code.

## Open questions and decisions (unresolved, material)

All four change user-visible API behavior; recommendations live in
`### Implementation decisions and open questions` and each needs an answer
(or approval of the recommendation) before the plan can be marked Approved:

1. Header name for the total count (recommendation: `X-Total-Count`).
2. Whether the header appears only on paginated responses (recommendation:
   yes) or on every collection response.
3. Behavior when only one of `limit` / `offset` is provided (recommendation:
   the missing one is treated as unbounded; `offset` defaults to 0).
4. Validation bounds: is `limit=0` invalid (recommendation: yes, `limit >= 1`,
   `offset >= 0`, integers only)?

## Research and supporting facts

- Route: `src/app/api/notes.py:8-10` — `read_all_notes()` currently returns
  `await crud.get_all()`; no query parameters, no response model, no headers.
- CRUD: `src/app/api/crud.py:4-5` — `get_all()` runs
  `database.fetch_all(notes.select())` with no explicit ordering, limit, or
  offset. Only `read_all_notes()` calls it.
- Data model: `src/app/db.py` — single `notes` table (`id` integer primary
  key, `title`, `description`), SQLite through `databases` + SQLAlchemy.
  `metadata.create_all(engine)` runs at import time, creating `./notes.db`
  in the working directory; `notes.db` is **not** gitignored, so rows can
  persist across test runs. Tests must not assume an empty table.
- Tests: `src/tests/test_notes.py` has two tests (list returns 200 + array;
  POST returns 201) sharing a `test_app` TestClient fixture from
  `src/tests/conftest.py` that exercises the real app and real SQLite
  database. pytest is imported by conftest but not declared in
  `pyproject.toml`; the executor must provide an environment with the
  pyproject dependencies plus pytest. No prepared environment exists in the
  worktree (a nearby shared `.venv` lacks `databases`).
- Tests must run from `src/` (e.g. `python -m pytest tests`) so
  `from app.main import app` in conftest resolves.
- Docs: `README.md` states "The collection route currently returns every
  note as a JSON array." — this claim becomes false when pagination exists
  and must change in the same reviewed change. `docs/development/index.md`
  records that no notes-query specification exists; creating one is not in
  scope. This variant has no separate client package or CLI, so the HTTP API
  is the only affected public boundary.
- `pyproject.toml` declares no `requires-python`; use `typing.Optional[int]`
  rather than `int | None` in the plan unless a version floor is confirmed.

## Execution plan

Status: Draft

### Design

Behavior (pending the open questions below):

- `read_all_notes` gains `limit: Optional[int] = Query(default=None, gt=0)`,
  `offset: Optional[int] = Query(default=None, ge=0)`, and an injected
  `response: Response` parameter.
- Neither parameter provided → return `await crud.get_all()` exactly as
  today, and (per recommendation on question 2) no header is added, so
  no-pagination responses stay identical to the current ones in body and
  headers.
- Either parameter provided → fetch the slice with explicit ascending-ID
  ordering and set the total-count header. The value is the count of all
  notes in the table, not the page size. The body remains a plain JSON array
  of note objects (no envelope), so paginated and non-paginated bodies
  differ only in length.

Data layer (`src/app/api/crud.py`), leaving `get_all()` untouched so the
non-paginated query (including its implicit ordering) stays byte-identical:

- `get_slice(offset, limit)`: `notes.select().order_by(notes.c.id.asc())`,
  applying `.offset(offset)` when `offset` is not None and `.limit(limit)`
  when `limit` is not None; `database.fetch_all`. SQLAlchemy handles
  offset-only queries on SQLite.
- `count_all()`: `select(func.count()).select_from(notes)` via
  `database.fetch_val`.

Header mechanism: mutate the injected `response.headers` and return the list
as today. FastAPI merges those headers into the final response and keeps its
existing row serialization (the same `Record` objects FastAPI already
serializes for the full list), so no manual row→dict conversion is needed.

OpenAPI: the two optional integer query parameters appear automatically on
`/notes/`; no response-model change.

### Ordered steps

1. Add `get_slice(offset, limit)` and `count_all()` to `src/app/api/crud.py`;
   do not modify `get_all()`.
2. Update `read_all_notes` in `src/app/api/notes.py` with the two optional
   Query params, `response: Response` injection, and the conditional
   total-count header (name per approved decision); keep the no-param path
   calling `crud.get_all()` with no ordering change.
3. Add tests to `src/tests/test_notes.py` (inventory in Requirement
   verification) using baseline-relative assertions because `notes.db`
   persists between runs; leave the shared conftest and the two existing
   tests untouched.
4. Update the README.md collection-route paragraph in the same change to
   describe optional pagination, ascending-ID ordering, the total-count
   header (per approved decisions), and unchanged no-param behavior.
5. Run the full test suite from `src` with the project dependencies
   installed and record results, including the two pre-existing tests.

### Implementation decisions and open questions

Resolved internal choices (no user impact, do not re-ask):

- Set the header by mutating an injected `response: Response` rather than
  returning `JSONResponse`; this preserves FastAPI's existing
  serialization of `databases` `Record` rows.
- Keep `crud.get_all()` unchanged and add separate slice/count functions so
  the non-paginated path is provably untouched (no new `ORDER BY` on it).
- Use `typing.Optional[int]` (no `requires-python` floor is declared).
- The header value is the count over the whole `notes` table, computed from
  a separate count query, not from the page.

Open questions (material — each needs an answer before approval):

1. **Header name.** Recommendation: `X-Total-Count`, the common convention
   for collection total headers. Alternatives: `X-Total`, `Total-Count`.
2. **Header presence.** Recommendation: present only when `limit` or
   `offset` is provided; absent from non-paginated responses so today's
   responses are unchanged beyond the new capability. Alternative: always
   include it (simpler mental model, but adds a header to every existing
   response, which the "keep current behavior" requirement arguably
   excludes).
3. **Partial pagination.** Recommendation: independent optionals —
   `limit` only → first `limit` notes ascending; `offset` only → notes from
   `offset` to the end ascending; neither → current full list. Alternative:
   require both or neither and 422 otherwise (stricter, more custom
   validation logic than "normal FastAPI validation" implies).
4. **Validation bounds.** Recommendation: integers only with `limit > 0`
   (`gt=0`) and `offset >= 0` (`ge=0`), so `limit=0`, negatives, and
   non-integers all 422 through stock FastAPI validation. Alternative:
   treat `limit=0` as a valid empty page.

### Documentation

- Update `README.md` (the only maintained doc describing the route; audience:
  API consumers) in the same change as the code so the new public claim is
  true in the reviewed state.
- No new pages or directories: `docs/development/index.md` correctly states
  no notes-query specification exists, and none is planned; this is the
  smallest structure that helps the reader.
- OpenAPI documents the new parameters automatically; nothing generated to
  maintain.

### Task checklist

- [ ] 1. `src/app/api/crud.py`: add `get_slice(offset, limit)` and
      `count_all()`; leave `get_all()` untouched.
- [ ] 2. `src/app/api/notes.py`: extend `read_all_notes` with optional
      `limit`/`offset` Query params, `response: Response` injection, and the
      conditional total-count header; no-param path unchanged.
- [ ] 3. `src/tests/test_notes.py`: add the pagination, header, equivalence,
      and validation tests described in Requirement verification.
- [ ] 4. `README.md`: update the collection-route description.
- [ ] 5. Run the full suite from `src` and record results.

### Requirement verification

All HTTP evidence runs through the existing `test_app` TestClient fixture
(real FastAPI app, real route registration, real SQLite via `databases`) —
the realistic public path for this service, with no mocks of the behavior
under test. Tests create their own notes via `POST /notes/` and assert
against baseline-relative values (e.g., `offset=<baseline count>`) because
`notes.db` is persistent; created ids are ascending and greater than any
pre-existing ids under SQLite autoincrement.

- Paginated ascending slice (requirement 1): `GET /notes/?offset=<baseline>&limit=2`
  after POSTing 3 notes returns exactly the first two created notes in
  ascending ID order (proves offset applied before limit); `?offset=<baseline>`
  alone returns all 3 created notes ascending; `?limit=2` alone returns
  exactly the two smallest IDs of the full list.
- Total-count header (requirement 2): the same requests assert the header
  (name per decision 1) equals baseline + 3 — the whole-collection count,
  not the page length.
- No-param equivalence (requirement 3): `GET /notes/` with no params returns
  the full array with length equal to the measured total and (per decision 2)
  without the total-count header; the pre-existing `test_read_all_notes`
  continues to pass; inspection confirms `crud.get_all()` is unmodified.
- Normal FastAPI validation (requirement 4): `?limit=0`, `?limit=abc`, and
  `?offset=-1` each return 422 from stock request validation; no custom
  exception handler or validator is added.
- Other CRUD routes unchanged (requirement 5): the full suite passes with the
  two pre-existing tests unmodified, and the diff is confined to `crud.py`
  additions, `read_all_notes`, tests, and README.
- README updated in the same change (requirement 6): inspection that the new
  README text matches the approved behavior once decisions 1–4 are resolved.

### Additional implementation verification

- Cheap drift check: assert via TestClient that `/openapi.json` lists
  `limit` and `offset` as optional integer query parameters on `/notes/`,
  confirming the generated API contract matches the implemented one.

Risks and notes for the executor:

- Do not install dependencies or run the suite in ways that leave artifacts:
  running the app or tests creates `notes.db` (untracked, not gitignored).
  If one is created during verification, remove it before handoff unless the
  user wants it kept.
- If the persistent shared database makes an assertion flaky (unexpected
  rows), prefer baseline-relative assertions over adding global cleanup that
  would change the shared test harness in this change.