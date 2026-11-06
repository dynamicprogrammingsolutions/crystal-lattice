# Add optional limit/offset pagination to GET /notes/

Add optional `limit`/`offset` query parameters to the notes collection route so
clients can request a bounded ascending-ID slice and receive the total note
count in a response header. Requests without the parameters keep the current
full-list array behavior. Planning only — implementation is not authorized by
this file.

Parent context: standalone task (no subtasks). The change is one delivery at
the service's public HTTP boundary; implementation, tests, and the README
update stay together.

## Requirements checklist

- [ ] R1: `GET /notes/` accepts optional integer query parameters `limit` and
  `offset`. When at least one is provided, the response body is the notes
  ordered by `id` ascending, skipping the first `offset` notes, and containing
  at most `limit` notes (a request with only `offset` returns all remaining
  notes).
- [ ] R2: A paginated `GET /notes/` response includes the total number of notes
  in the collection in a response header (name per approved decision:
  `X-Total-Count`).
- [ ] R3: `GET /notes/` requests without `limit` and `offset` keep the current
  behavior: every note returned as a JSON array and no added response header.
- [ ] R4: Invalid `limit`/`offset` values are rejected by FastAPI's standard
  query validation (HTTP 422) through the parameter declarations, including
  the approved bound constraints; no custom validation or error handling.
- [ ] R5: The other CRUD routes (`POST /notes/`, `GET /notes/{note_id}/`,
  `PUT /notes/{note_id}/`, `DELETE /notes/{note_id}/`) are behaviorally
  unchanged.
- [ ] R6: `README.md` describes the updated collection-route behavior (default
  full array plus optional pagination and the total-count header) in the same
  reviewed change as the code (required by `AGENTS.md` documentation policy).

## Questions and decisions

Open items that change the public contract; each needs approval with the plan
(recommendations and tradeoffs in the plan's
"Implementation decisions and open questions"):

- Header name for the total count — recommendation: `X-Total-Count`.
- `limit` bounds — recommendation: `limit > 0` (so `limit=0` is a 422);
  alternative: allow `limit=0` as an empty page.
- `offset` bounds — recommendation: `offset >= 0`.
- Decided from R3's wording, override at approval: the total-count header is
  sent only on paginated requests; non-paginated responses gain no header.
- Decided at plan level (test infrastructure only, not user-visible): tests
  get a dedicated SQLite file via an environment-variable override in
  `app/db.py` (default URL unchanged) plus a per-test table wipe.

## Supporting details

Current behavior and code layout (verified by reading the source):

- `src/app/main.py` mounts one router at prefix `/notes` with a lifespan that
  connects/disconnects `databases`.
- `src/app/api/notes.py` defines the five routes. `read_all_notes` currently
  takes no parameters and returns `crud.get_all()` directly.
- `src/app/api/crud.py` `get_all()` runs `notes.select()` with no `ORDER BY`,
  `LIMIT`, or `OFFSET`.
- `src/app/db.py` defines `notes` with autoincrement `id` (Integer primary
  key), `title`, `description`, and hardcodes `DATABASE_URL =
  "sqlite:///./notes.db"` (relative to the current working directory).
- `README.md` currently says the collection route "returns every note as a
  JSON array" — still true for non-paginated requests but incomplete after
  this change (R6).
- `docs/development/index.md` states no notes-query specification exists; no
  specification page is requested, so it stays untouched.

Baseline test evidence (gathered during planning in a throwaway venv outside
the repo; FastAPI 0.162.0, starlette 1.10.0, SQLAlchemy 2.1.6, Python 3.11):

- The existing suite (`src/tests/test_notes.py`, fixture `test_app` returning
  a bare `TestClient(app)`) passes: 2 passed. Lifespan runs and the real
  SQLite file is used, so the harness exercises HTTP → routing → crud →
  `databases` → SQLite.
- The test database is `./notes.db` relative to the working directory, is not
  gitignored, and accumulates rows across runs (the POST test inserts a row
  every run). Existing assertions are robust to that; new total-count and
  exact-slice assertions are not — hence the isolation decision above.
- Query patterns verified against `app.db`: `notes.select()
  .order_by(notes.c.id.asc()).limit(n).offset(m)` returns the expected
  ascending slice; the same with only `.offset(m)` returns the remaining rows;
  `database.fetch_val(select(func.count()).select_from(notes))` returns the
  total row count; `Record` objects serialize through FastAPI as they do
  today.
- Note IDs are autoincrementing, so seeded IDs sort ascending by creation
  order.

## Implementation plan

Status: Draft

### Design

One route gains two optional query parameters; everything else is additive.

- `src/app/api/crud.py` — add two functions; change nothing existing:
  - `get_page(limit, offset)`: `notes.select().order_by(notes.c.id.asc())`,
    applying `.limit(limit)` / `.offset(offset)` (SQLAlchemy omits the clause
    when the value is `None`) and `database.fetch_all`.
  - `count_all()`: `database.fetch_val(select(func.count()).select_from(notes))`
    (import `func` and `select` from SQLAlchemy).
- `src/app/api/notes.py` — `read_all_notes` becomes:

  ```python
  @router.get("/")
  async def read_all_notes(
      response: Response,
      limit: int | None = Query(default=None, gt=0),
      offset: int | None = Query(default=None, ge=0),
  ):
      if limit is None and offset is None:
          return await crud.get_all()
      response.headers["X-Total-Count"] = str(await crud.count_all())
      return await crud.get_page(limit=limit, offset=offset)
  ```

  Branching on "both absent" keeps the legacy path byte-for-byte compatible:
  same CRUD call, no extra count query, no header. R4 is satisfied purely by
  the `int` type and `gt`/`ge` constraints in the `Query` declarations —
  FastAPI produces the 422 responses. Add `Query` and `Response` to the
  `fastapi` import.

- Test harness (`src/app/db.py`, `src/tests/conftest.py`):
  - `db.py`: `DATABASE_URL = os.environ.get("NOTES_DATABASE_URL",
    "sqlite:///./notes.db")` — production default unchanged; tests point the
    variable at a session-scoped temp file so total counts and slices are
    deterministic and runs no longer depend on (or pollute) a developer's
    `notes.db`.
  - `conftest.py`: set `NOTES_DATABASE_URL` to a temp path before importing
    `app.main`, and add an autouse fixture that wipes the `notes` table before
    each test using the existing sync `engine` (`with engine.begin() as conn:
    conn.execute(notes.delete())`) — the table exists because `db.py` runs
    `metadata.create_all` at import. Wiping via the sync engine avoids
    ordering problems with the async connection, which `TestClient` opens per
    request. Existing tests stay green against the emptied table
    (`test_read_all_notes` asserts only list-ness).

- Tests (`src/tests/test_notes.py`), all through `test_app` so each crosses
  HTTP → validation → route → crud → `databases` → SQLite:
  - Seed helper: create notes via `POST /notes/` and keep the returned IDs.
  - No params: 200, body equals the full seeded list (as a set of IDs), and
    `X-Total-Count` is absent (R3 guard).
  - `limit=2` with ≥3 seeded: 200, exactly the two lowest IDs ascending,
    header equals the seeded total (R1+R2).
  - `offset=1` only: the seeded list minus the lowest ID, ascending, header
    total (R1 offset-only case).
  - `limit=2&offset=1` with 4+ seeded: exact inner slice (2nd and 3rd IDs)
    (R1 combined case).
  - Validation: `limit=abc` → 422; `limit=0` → 422 (per approved bound);
    `offset=-1` → 422 (R4).

### Risks, blast radius, and rollback

- Blast radius: one route handler, two new crud functions, test-only `db.py`
  env override, conftest, one new test module section, README. No persisted
  data, no client-visible change to existing requests (additive parameters
  and a header only on paginated requests).
- Main regression risks: (a) an `ORDER BY` or count query leaking into the
  non-paginated path — prevented by the untouched `crud.get_all` branch and
  covered by the no-header/no-params test; (b) the header leaking into
  non-paginated responses — covered by the same test; (c) the harness change
  masking environment problems — the default URL is unchanged and one
  verification run happens from a different working directory.
- Rollback: revert the change set; no data migration or client coordination
  needed.

### Order logic

1. crud functions (inert additions, suite stays green).
2. Route wiring (behavior change lands; existing suite still green because no
   test sends the new parameters yet).
3. Harness isolation, then the new tests (each milestone keeps the full suite
   green, so work can stop safely after any step).
4. README in the same change, per the AGENTS.md rule that new public claims
   ship with the code that makes them true.

### Implementation decisions and open questions

- Open (public contract, needs approval): header name — recommend
  `X-Total-Count`, the common convention for collection totals; alternatives
  (`X-Total`, `Total-Count`) are cosmetic but equally sticky once clients
  depend on them.
- Open (public contract, needs approval): `limit` bound — recommend `gt=0`
  (simplest strict "bounded slice" semantics; `limit=0` → 422); accepted
  alternative is `ge=0`, which makes `limit=0` a way to fetch only the total
  count.
- Open (public contract, needs approval): `offset` bound — recommend `ge=0`;
  unbounded negative offsets would otherwise silently behave as 0 in SQLite.
- Decided from R3 wording: header only when paginating; "keep the current
  behavior" is read literally, so non-paginated responses gain nothing.
- Decided: no maximum `limit` cap — none requested; adding one would be a new
  contract term.
- Decided: non-paginated path keeps no `ORDER BY` (its current contract has
  none; adding one is out of scope).
- Decided: `int | None` annotation style (environment is Python 3.11/3.12;
  FastAPI 0.162 supports it).
- Decided: test isolation via `NOTES_DATABASE_URL` env override + per-test
  wipe; test infrastructure only, production default preserved.

### Documentation

- `README.md` (user-facing, owns the API's public description): replace the
  final sentence with current-guidance text, shipped in the same change, e.g.:
  "The collection route returns every note as a JSON array, or an
  ascending-ID slice when the optional `limit` and `offset` query parameters
  are used; paginated responses include the total note count in the
  `X-Total-Count` response header." (Header name per approved decision.)
- No new pages or directories; no specification file requested.
- `docs/development/index.md` stays untouched.

### Task checklist

- [ ] Add `get_page` and `count_all` to `src/app/api/crud.py` (no changes to
      existing functions).
- [ ] Extend `read_all_notes` in `src/app/api/notes.py` with the `Query`
      parameters, the both-absent branch, and the total-count header.
- [ ] Add the `NOTES_DATABASE_URL` override to `src/app/db.py` and the temp-db
      + wipe fixtures to `src/tests/conftest.py`; confirm the existing suite
      still passes.
- [ ] Add the pagination tests listed in the design to
      `src/tests/test_notes.py`.
- [ ] Run the full suite green from a working directory outside the repo;
      confirm no `notes.db` appears in the repo root.
- [ ] Update `README.md` as specified.
- [ ] Re-run the suite once more after the README change; update this file's
      requirements checklist with evidence and add the completion entry.

### Requirement verification

- R1 (slice): the limit-only, offset-only, and combined tests assert exact
  ascending ID slices through the real HTTP path and real SQLite. Not
  covered: performance/large datasets, non-SQLite backends.
- R2 (header): the paginated tests assert the header equals the seeded total.
  Not covered: header formatting beyond the integer string.
- R3 (legacy behavior): the no-params test asserts the full list and the
  header's absence; the pre-existing `test_read_all_notes` remains green.
- R4 (validation): 422 assertions for a non-integer `limit`, and for the
  approved bound violations. Not covered: exotic inputs that traverse the
  same Pydantic validator path (e.g., empty strings).
- R5 (other routes): decisive evidence is the reviewed diff — those handlers
  and their crud functions are untouched — supported by the existing suite
  passing (`test_crud_routes_exist` and the read-all test).
- R6 (docs): the published `README.md` states the default array behavior, the
  optional parameters, and the header accurately; checked by reading the
  final page. Not covered: pages that do not describe this route.

### Additional implementation verification

- Run the suite from two different working directories to prove the env-var
  isolation removed the CWD-dependent `notes.db` behavior.
- Confirm `git status` shows no `notes.db` and no other stray artifacts after
  a full test run.
