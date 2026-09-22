# Notes list pagination: optional limit/offset on GET /notes/

Optional `limit`/`offset` query parameters on `GET /notes/` returning a bounded
ascending-ID slice of notes, with the total note count exposed in a response
header. Requests without pagination keep the current full-list array behavior;
other CRUD routes and their code paths stay untouched.

Planned 2026-09-19. No implementation has been done; execution waits on plan
approval and on the open questions below.

## Requirements checklist

- [ ] `GET /notes/` accepts optional `limit` and `offset` query parameters,
  usable independently or together. When supplied, the response body is a
  slice of the notes collection ordered by ascending `id`: the first `offset`
  notes are skipped and at most `limit` notes are returned. Items keep the
  current serialization shape (`id`, `title`, `description`).
- [ ] `GET /notes/` responses expose the total number of notes in the
  collection in a response header. Exact header name pending approval
  (recommendation: `X-Total-Count`).
- [ ] `GET /notes/` without pagination parameters keeps the current behavior:
  a JSON array of all notes with unchanged serialization. (Whether the total
  header is also present on these responses is pending approval.)
- [ ] Invalid `limit`/`offset` values (non-integers, negatives) are rejected
  through FastAPI's normal query validation (422 with the standard error
  body); no custom validation or error handling is added.
- [ ] The other CRUD routes (`POST /notes/`, `GET /notes/{id}/`,
  `PUT /notes/{id}/`, `DELETE /notes/{id}/`) keep their current
  request/response behavior and are not modified.
- [ ] The collection-route description in `README.md` is updated to current
  behavior in the same reviewed change as the code (repo AGENTS.md policy:
  keep new public claims in the same change that makes them true).

## Open questions (block execution)

Requirement questions — answers change the public contract:

1. **Total-count header name.** Recommendation: `X-Total-Count` (common
   convention for collection totals). Alternatives if preferred: `X-Total`,
   `Total-Count`.
2. **Header presence on unpaginated responses.** Recommendation: present on
   every successful `GET /notes/` response, including the no-pagination
   full-list response, since "total note count" is equally meaningful there.
   Alternative: only when `limit`/`offset` is supplied.
3. **Upper cap on `limit`.** "Bounded" is read as bounded by `limit`/`offset`
   only, with no additional application cap. If a maximum page size is
   wanted, state the value and the expected rejection status.

Design decision taken by convention unless overruled:

4. **Offset base is zero-based** (`offset=0` returns the first notes), matching
   the SQL/limit-offset convention used by the parameter names.

## Supporting facts (from inspection)

- Route handler `read_all_notes` (`src/app/api/notes.py:8-10`) calls
  `crud.get_all()` (`src/app/api/crud.py:4-5`), which runs `notes.select()`
  with no ORDER BY. Ascending-ID order is currently implicit (SQLite rowid
  order), not a guaranteed contract; the paginated slice must order
  explicitly by `notes.c.id` ascending.
- Storage is the `databases` library over a SQLAlchemy `notes` table
  (`src/app/db.py`): columns `id` (integer primary key), `title`,
  `description`, in a sqlite file `./notes.db` created at import time.
- Rows are returned as `databases.Record` mappings and serialized directly;
  item shape today is `{"id", "title", "description"}`.
- Tests use `fastapi.testclient.TestClient(app)` via the `test_app` fixture
  (`src/tests/conftest.py`). `src/tests/test_notes.py` currently asserts only
  list-shape and POST 201. The suite shares the on-disk `./notes.db`, so
  deterministic pagination tests need setup/cleanup of table contents.
- `README.md` states the collection route "currently returns every note as a
  JSON array" — that claim needs updating when pagination ships.
  `docs/development/index.md` records that no notes-query specification
  exists, so there is no spec page to update.
- Dependencies (`pyproject.toml`): `fastapi`, `databases[sqlite]`,
  `sqlalchemy`, `httpx`. `pytest` is not declared; its availability must be
  confirmed at execution and any environment gap reported rather than silently
  adding dependencies.
- This fixture variant has only the FastAPI app (no client package or CLI),
  so the deliverable is a single HTTP-boundary change; one task file, no
  subtasks.

## Execution plan

Status: Draft

### Approach

1. **Query parameters and validation** (`src/app/api/notes.py`): change
   `read_all_notes` to declare `limit: int | None = Query(default=None, ge=0)`
   and `offset: int | None = Query(default=None, ge=0)`. Integer typing plus
   `ge=0` yields FastAPI's standard 422 for non-integer and negative values;
   no bespoke validation. `limit=0` is valid and yields an empty slice. Each
   parameter is honored independently: `offset` alone returns everything from
   that point on; `limit` alone implies `offset=0`.
2. **Slice and count in the CRUD layer** (`src/app/api/crud.py`): add
   `get_slice(offset, limit)` using
   `notes.select().order_by(notes.c.id).offset(offset).limit(limit)` — the
   explicit ascending `id` ordering makes the "ascending-ID slice" contract
   hold regardless of storage order — and `get_count()` using
   `select(count()).select_from(notes)`. Existing `get_all`, `get`, `post`,
   `put`, `delete` are not modified; the no-pagination path keeps calling
   `get_all()` unchanged, preserving current full-list behavior exactly.
3. **Response header**: `read_all_notes` gains a `response: Response`
   parameter and sets the total-count header on every successful response
   (value = full note count, not slice length), subject to open questions
   1–3. The header name is defined once as a constant shared with the route
   metadata.
4. **OpenAPI accuracy**: declare the response header via `response_headers`
   in the `@router.get("/")` decorator so the generated OpenAPI documents it;
   query parameters are auto-documented by FastAPI. Documentation-only
   metadata, no behavior change.
5. **Tests** (`src/tests/test_notes.py`, HTTP boundary via TestClient against
   the real app and sqlite — the boundary that actually changes):
   - fixture-style cleanup of the notes table plus insertion of a known set
     of notes, so slice assertions are deterministic despite the shared
     on-disk DB;
   - no-pagination response is still the full array with the same item shape
     (assert membership/length, since its ordering is intentionally not being
     pinned down);
   - `?limit=2`, `?offset=1&limit=2`, `?offset` beyond total, and
     `limit` larger than total each return the exact expected ascending-id
     sequences and item fields;
   - total-count header present and equal to the full note count on both
     paginated and unpaginated responses (per open question 2);
   - 422 responses for `?limit=-1`, `?offset=-1`, `?limit=abc`,
     `?offset=abc`;
   - compact regression for the untouched routes: POST → GET one → PUT →
     DELETE with current status codes and returned fields;
   - the two existing tests pass unmodified.
6. **Documentation**: update the README.md sentence describing the collection
   route to current behavior (optional limit/offset slice, ascending-ID
   order, total-count header). No new pages or directories — smallest
   structure that serves API consumers, and no notes-query spec exists to
   extend.

### Implementation decisions and open questions

- Open (requirement questions, see above): total-count header name (1);
  header presence on unpaginated responses (2); upper cap on `limit` (3).
- Decided by convention: zero-based offset (4). Flagged here so the user can
  overrule before execution.
- Decision: explicit `order_by(notes.c.id)` is applied only to the paginated
  slice query. The no-pagination path stays byte-for-byte on `get_all()`
  because the requirement forbids changing full-list behavior; in practice
  SQLite already returns ascending rowid order there. Revisit only if the
  user wants the full list contractually ordered too.
- Decision: parameters are honored independently rather than requiring both
  together — the natural reading of "optional limit/offset", and it avoids
  inventing a co-dependency rule the request did not ask for.

### Documentation

- `README.md`: rewrite the collection-route sentence to describe optional
  `limit`/`offset` pagination (ascending `id`, zero-based offset) and the
  total-count response header, in the same reviewed change as the code.
  Audience: API consumers. No other documentation targets exist for this
  behavior (`docs/development/index.md` confirms no query spec page).

### Task checklist

- [ ] Get user answers to open questions 1–3 (header name, header presence,
      limit cap) and approval of the plan.
- [ ] Implement `limit`/`offset` query parameters, slice + count CRUD
      helpers, and the total-count header (`notes.py`, `crud.py`).
- [ ] Add pagination, validation, header, and unchanged-route regression
      tests (`test_notes.py`).
- [ ] Update `README.md` collection-route description.
- [ ] Run the full pytest suite; confirm all tests (old and new) pass.

### Requirement verification

- Slice, ascending order, item shape → TestClient tests against the real app
  and sqlite asserting exact `id` sequences and `{"id","title","description"}`
  fields for each pagination combination. This crosses the real HTTP + DB
  path; no mocks supply the behavior.
- Total-count header → tests asserting the header on paginated and
  unpaginated responses equals the number of notes created (per open
  question 2).
- No-pagination unchanged → test asserting the unpaginated body is the full
  array with unchanged item shape, plus the existing `test_read_all_notes`
  passing without modification.
- Normal FastAPI validation → tests asserting 422 (not custom error bodies or
  status codes) for negative and non-integer values.
- Other CRUD routes unchanged → code diff confined to the list route and new
  crud helpers; compact POST/GET/PUT/DELETE regression test passes; existing
  tests pass unmodified.
- README updated → inspection of `README.md` in the same change as the code.

### Additional implementation verification

- Inspect the generated `openapi.json` for `GET /notes/` to confirm `limit`,
  `offset`, and the response header are documented (cheap metadata check).
- Confirm the pytest runner works in this environment before relying on the
  suite; if `pytest` is unavailable, report the blocker instead of adding
  undeclared dependencies unprompted.
- Known risk: the suite shares one `./notes.db` file; the planned per-test
  table cleanup must leave no cross-test state. If cleanup through the same
  `database` module proves flaky, revisit test isolation before expanding
  assertions.