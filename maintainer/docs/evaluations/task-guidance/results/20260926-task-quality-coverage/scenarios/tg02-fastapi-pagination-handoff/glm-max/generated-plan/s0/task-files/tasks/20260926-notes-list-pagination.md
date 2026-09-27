# Notes list pagination (`GET /notes/`)

Add optional `limit`/`offset` pagination to the notes collection route so
clients can request a bounded ascending-ID slice plus a total-count response
header, while requests without pagination parameters keep the current
full-list array behavior.

## Requirements checklist

- [ ] `GET /notes/` accepts optional `limit` and `offset` query parameters.
- [ ] When pagination parameters are provided, the response body is the
      bounded slice of notes ordered by ascending `id`: notes are skipped by
      `offset`, then at most `limit` notes are returned.
- [ ] When pagination parameters are provided, the response carries the total
      number of notes in a response header.
- [ ] When no pagination parameters are provided, the route returns the full
      note list as a JSON array exactly as it does today (no envelope, no new
      response header).
- [ ] Invalid `limit`/`offset` values are rejected by FastAPI's standard query
      validation (422 with the standard error body); no hand-written
      validation logic.
- [ ] The other routes (`GET /notes/{note_id}/`, `POST /notes/`,
      `PUT /notes/{note_id}/`, `DELETE /notes/{note_id}/`) and their handlers
      remain unchanged.
- [ ] `README.md` (the maintained user-facing description of the notes API)
      reflects the collection route's pagination behavior, updated in the same
      change as the code that makes it true.

## Open questions and decisions

Unresolved material decisions; both are user-visible in the public HTTP
contract and need user confirmation before execution. Recommendations given;
the Draft plan is otherwise executable.

- **Total-count header name** (design decision, public contract): no name was
  specified. Recommendation: `X-Total-Count` (de-facto standard for collection
  totals; no compatibility constraint since no such header exists today).
- **Is `limit=0` valid?** (question affecting the validation boundary):
  Recommendation: valid — declare `limit` with `ge=0`, so `?limit=0` returns an
  empty slice plus the total header (a coherent "count only" request), while
  negative values and non-integers remain standard 422 validation errors.
  Alternative: `ge=1`, making `?limit=0` a 422.

## Supporting details

Facts about the current codebase, verified by reading the source:

- `src/app/api/notes.py:8` — `read_all_notes` returns `await crud.get_all()`
  with no query parameters. `src/app/api/crud.py:4` runs `notes.select()`
  with no `ORDER BY`, so today's ordering is SQLite's default (typically
  insertion/rowid order, not a query-level guarantee).
- Storage is a file-backed SQLite database via `databases` +
  `sqlalchemy` (`src/app/db.py`); `notes.db` is created relative to the
  process CWD, and the table is created at import time
  (`metadata.create_all(engine)`). `notes.db` is not in `.gitignore`, so test
  runs leave an untracked artifact to clean up.
- Tests (`src/tests/`) drive `TestClient(app)` against the real app and the
  real SQLite backend; no mocks. `conftest.py` returns `TestClient(app)`
  without entering it, so the app lifespan (`database.connect()`) does not
  run; verified that this is harmless for SQLite because `databases`' SQLite
  backend creates its pool eagerly (connect is a no-op), and Starlette 1.7.0
  runs lifespan only via the context manager. No harness change is needed.
- The app is imported as namespace packages with no `__init__.py` files; tests
  must run with `src/` as the working directory (`python -m pytest tests/`)
  so `from app.main import app` resolves.
- `pyproject.toml` declares `databases[sqlite]`, `fastapi`, `httpx`,
  `sqlalchemy` but not `pytest`; the verification environment must install
  pytest separately. There is no build-system section, so installing the
  package itself is unreliable; installing the dependencies directly and
  running pytest from `src/` is the working setup.
- This variant has no Python client package or CLI; the only affected public
  boundary is the HTTP API of the FastAPI app.
- `docs/development/index.md` records that no notes-query specification
  exists; the README is the only maintained user-facing API documentation.
  Read `docs/development/documentation.md` before doc work (done while
  planning; no structure change is needed for a README sentence update).

## Execution plan

Status: Draft

### Design

Component responsibilities and data flow:

- `src/app/api/crud.py` gains two read helpers; the five existing functions
  are untouched:
  - `get_page(limit, offset)` —
    `notes.select().order_by(notes.c.id.asc()).offset(offset).limit(limit)`
    fetched with `database.fetch_all`. The explicit `ORDER BY id ASC` makes
    the ascending-ID guarantee query-level rather than an accident of SQLite
    rowid order. `limit=None` renders no LIMIT clause; with only `offset`
    provided, SQLAlchemy renders the SQLite-compatible `LIMIT -1 OFFSET n`.
  - `count_all()` —
    `database.fetch_val(sqlalchemy.select(sqlalchemy.func.count()).select_from(notes))`.
    This form works on both SQLAlchemy 1.4 and 2.x and counts the whole
    collection, independent of limit/offset.
- `src/app/api/notes.py` — `read_all_notes` gains an injected
  `response: Response` (used only to set the header) and two optional query
  parameters: `limit: int | None = Query(default=None, ge=0)` and
  `offset: int | None = Query(default=None, ge=0)`. Declaring them as
  `int | None` distinguishes "not provided" from an explicit `0`, so
  `?offset=0` is honored as a paginated request. Mode switch:
  - Neither parameter provided → `return await crud.get_all()` — the exact
    current path, unchanged: full JSON array, no header, no ordering clause.
  - Either parameter provided → `items = await crud.get_page(limit=limit,
    offset=offset or 0)`, `total = await crud.count_all()`, set
    `response.headers["X-Total-Count"] = str(total)`, return `items`. The
    body stays a JSON array (no envelope); headers set on the injected
    `Response` are merged into the final JSON response.
- `src/app/api/models.py`, `src/app/db.py`, `src/app/main.py`: unchanged.

Compatibility:

- Requests without pagination parameters execute the same code path and
  produce the same response as today. The only observable additions are the
  two optional query parameters and the header in paginated mode.
- Status code remains 200 in both modes.

Validation:

- Declarative `Query(ge=0)` constraints only. FastAPI/pydantic reject
  non-integer and negative values with the standard 422 `{"detail": [...]}`
  body before the handler runs, and the OpenAPI schema picks up the optional
  integer parameters with `minimum: 0` automatically. No custom validation
  code, no behavior change on other routes.

Documentation:

- Update the README sentence describing the collection route so it covers:
  default full-list array, optional `limit`/`offset` yielding ascending-ID
  slices, and the total-count header (name per the approved decision). Kept
  to the existing README; no new pages (see AGENTS.md documentation policy
  and `docs/development/documentation.md`).

Verification strategy:

- pytest through the real app (`TestClient`) with the real SQLite backend —
  in-process ASGI crossing the full request → validation → route → crud →
  databases/sqlalchemy → response path; no mocks. Establish the baseline by
  running the existing suite before making changes. Test expectations are
  computed relative to a live full-list read (the suite shares a persistent
  `notes.db`, so absolute counts are not stable).

### Implementation decisions and open questions

Open (need user approval; requirements do not change either way):

- Header name: recommend `X-Total-Count`.
- `limit` lower bound: recommend `ge=0` (making `limit=0` a valid empty
  slice); alternative `ge=1` rejects `limit=0` with a 422. Test the
  `?limit=0` behavior only after this is resolved.

Decided (derived from the request; flag for review if disputed):

- Paginated mode is triggered when either `limit` or `offset` appears in the
  request, including an explicit `?offset=0` (the optional `int | None`
  parameters make presence distinguishable from the default).
- The response body is a JSON array of notes in both modes (no envelope or
  metadata fields).
- The header appears only in paginated mode; the non-paginated response is
  exactly today's behavior.
- No upper bound (`le`) on `limit` is introduced; the request did not ask for
  a maximum page size.
- The header value is the count of the whole notes collection, not the page
  size, and is not affected by limit/offset.

### Documentation

- Update `README.md` (user-facing, owns the public notes API description) in
  the same change as the route: keep the existing description of the
  full-list array and add the optional `limit`/`offset` parameters,
  ascending-ID slice semantics, and the total-count header. Approximate
  final wording (adjust to the approved header name):
  "The collection route returns every note as a JSON array. Optionally,
  clients may pass `limit` and `offset` query parameters to receive a bounded
  slice of notes ordered by ascending id; such requests also carry the total
  note count in the `X-Total-Count` response header."
- No other documentation exists for the notes HTTP API; do not create
  placeholder pages. `docs/development/` is unaffected.

### Task checklist

- [ ] Establish verification environment and baseline: install
      `databases[sqlite] fastapi httpx sqlalchemy pytest` into a disposable
      venv (pytest is not declared in `pyproject.toml`); from `src/`, run
      `python -m pytest tests/` and confirm it collects and passes before any
      change. Record the baseline result.
- [ ] Add `crud.get_page(limit, offset)` (ascending-ID ordered, offset/limit
      slice) and `crud.count_all()` in `src/app/api/crud.py` without modifying
      the existing functions.
- [ ] Rework `read_all_notes` in `src/app/api/notes.py`: optional `Query`
      parameters with `ge=0`, mode switch preserving the `crud.get_all()`
      path for non-paginated requests, paginated path with the total-count
      header set on the injected `Response`.
- [ ] Update `README.md` to describe the optional pagination and the
      total-count header (and reconcile the existing "returns every note as a
      JSON array" sentence).
- [ ] Extend `src/tests/test_notes.py`:
  - paginated `?limit=2&offset=1` returns the matching ascending-ID slice of
    the current full list and the `X-Total-Count` header equal to the full
    list length;
  - only-`limit` and only-`offset` requests return the corresponding slices
    with the header;
  - an `offset` beyond the collection size returns an empty array with the
    header;
  - a request without pagination parameters returns the full array with no
    pagination header;
  - `?limit=abc`, `?offset=abc`, `?limit=-1`, `?offset=-1` return 422 with
    the standard `detail` body naming the offending parameter;
  - `?limit=0` returns an empty array with the header (only if the `ge=0`
    decision is approved; otherwise assert a 422 instead);
  - a CRUD round-trip (POST → GET `{note_id}` → PUT → DELETE → GET 404)
    confirming the other routes still work through the real app.
- [ ] Run the full suite from `src/` and confirm all tests collect and pass;
      verify the diff touches only `src/app/api/notes.py`,
      `src/app/api/crud.py` (additions), `src/tests/test_notes.py`, and
      `README.md`; remove any `notes.db` created by test runs (not
      gitignored).

### Requirement verification

- Optional `limit`/`offset` parameters, ascending-ID bounded slice, and the
  total-count header: one integration test through the real app and real
  SQLite backend (`TestClient` against the ASGI app; the actual
  request → validation → route → crud → databases → response path, no mocks)
  asserting the slice equals the corresponding segment of the live full-list
  read with strictly ascending IDs and `X-Total-Count` equal to the total.
- Unchanged non-paginated behavior: integration test asserting the full array
  content (computed from created rows) and absence of the pagination header;
  the existing `test_read_all_notes` remains green and covers the 200 +
  JSON-array shape.
- FastAPI-standard validation: integration tests asserting 422 with the
  standard `detail` structure for non-integer and negative `limit`/`offset`
  values (FastAPI's validation layer runs before the handler on the real
  app).
- Other CRUD routes unchanged: diff review confirming their handlers and the
  existing `crud.py` functions are untouched, plus a round-trip integration
  test exercising POST → GET `{note_id}` → PUT → DELETE through the real app,
  and the existing suite passing.
- README reflects implemented behavior: inspection in the same change-set as
  the code (documentation claims match the resolved header name and default
  behavior).

### Additional implementation verification

- Optional, cheap: request `openapi.json` and assert the `/notes/` GET
  operation lists `limit` and `offset` as optional integer query parameters
  with `minimum: 0`, confirming the public schema reflects the declared
  contract automatically.
- Environment hygiene: confirm no `notes.db` or `__pycache__` artifacts
  remain in the workspace after verification (the sqlite file is not
  gitignored; `__pycache__/` is).