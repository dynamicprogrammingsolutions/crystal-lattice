# `GET /notes/` optional limit/offset pagination

Add optional `limit`/`offset` pagination to the notes collection route so
clients can request a bounded ascending-ID slice and receive the total note
count in a response header. Unpaginated requests keep the current full-list
array behavior, invalid values fall out to standard FastAPI validation, and
the other CRUD routes stay unchanged. Planning only — execution is not
approved yet.

## Requirements checklist

- [ ] `GET /notes/` accepts optional `limit` and `offset` integer query
      parameters; when the client requests pagination, the response body is a
      bounded slice of notes ordered by ascending `id`.
- [ ] Paginated responses carry the total note count in a response header
      (header name and presence semantics are pending approval — see open
      questions).
- [ ] Requests without pagination parameters keep the current full-list JSON
      array behavior, unchanged.
- [ ] Invalid `limit`/`offset` values are rejected through standard FastAPI
      validation (default 422 responses); no custom validation or error
      handling.
- [ ] `GET /notes/{note_id}/`, `POST /notes/`, `PUT /notes/{note_id}/`, and
      `DELETE /notes/{note_id}/` keep their current behavior.
- [ ] The maintained README description of the collection route is updated in
      the same change as the behavior.

## Open requirement questions

Answers are required before execution; tradeoffs and recommendations are in
the plan's decision section.

1. Response-header name for the total count.
2. Whether the header appears only on paginated requests or on every
   collection response.
3. Whether the slice applies when only `limit` or only `offset` is provided,
   and what the missing parameter defaults to.
4. (Design, low stakes) Whether `limit` needs a server-side maximum.

## Supporting facts

- `read_all_notes` (`src/app/api/notes.py:8`) returns `crud.get_all()`
  (`src/app/api/crud.py:4`), which runs `notes.select()` with no explicit
  ordering, over SQLite (`./notes.db`) through the `databases` library
  (`src/app/db.py`).
- `id` is an integer primary key, so an ascending-ID slice is expressible with
  standard SQLAlchemy Core (`order_by(notes.c.id).offset(...).limit(...)`).
- The total count needs its own aggregate query (`sqlalchemy.func.count`
  fetched with `database.fetch_one`); it cannot be derived from the slice.
- The route returns a plain list of `databases` Record rows; FastAPI
  serializes them through its Mapping fallback. Returning the same kind of
  list on the paginated path keeps serialization identical. There is no
  `response_model` today and none is needed.
- The route's OpenAPI docs are auto-generated; the new optional query
  parameters will appear without manual maintenance.
- Harness: `src/tests/conftest.py:6` returns `TestClient(app)` without a
  context manager. Starlette runs the app lifespan (and therefore
  `database.connect()`) only inside a `with` block. Fact: the harness is
  written that way. Assumption: the database may therefore be unconnected in
  tests; the executor must verify this against a real consuming test and
  adapt the fixture if needed.
- `./notes.db` persists between runs (created at import of `app.db`, not
  gitignored). Tests asserting exact slices/counts need deterministic state,
  e.g. clearing the `notes` table through the real database connection before
  seeding.
- No Python environment with the project dependencies is available in this
  workspace; dependencies were not installed during planning.

## Execution plan

Status: Draft

### Design

Route layer (`src/app/api/notes.py`):

- `read_all_notes` gains two optional integer query parameters declared with
  FastAPI `Query` plus the injected `Response`. With neither parameter present
  the handler calls the existing `crud.get_all()` unchanged. With pagination
  requested it fetches the slice and the total through new CRUD functions,
  sets the total-count header (value cast to `str`), and returns the list
  exactly like today.
- Validation is expressed with standard `Query` constraints only (bounds per
  the approved decision), so invalid values produce FastAPI's default 422. No
  custom validators, error handlers, or `response_model`.

CRUD layer (`src/app/api/crud.py`):

- Add `get_page(offset, limit)` using
  `notes.select().order_by(notes.c.id).offset(offset).limit(limit)` via
  `database.fetch_all`, and `count_notes()` using `func.count` via
  `database.fetch_one`.
- `get_all` and the existing single-note, insert, update, and delete functions
  stay untouched.

Untouched: `src/app/api/models.py`, `src/app/main.py`, `src/app/db.py`, and
all other routes.

Compatibility and behavior boundaries:

- Default path: identical body shape (JSON array of note objects) and content;
  the unpaginated query keeps today's unordered `notes.select()` so default
  behavior is preserved rather than re-ordered.
- Paginated path: additive — two optional query parameters and one header; the
  body remains a plain JSON array of note objects, not an envelope object.
- OpenAPI changes are auto-generated additions (two optional parameters).
- Natural edge semantics with no special casing: `limit=0` and an offset past
  the end both yield an empty array.

### Implementation decisions and open questions

Pending approval — public HTTP contract; tests must not exercise these until
decided:

1. **Header name.** Recommend `X-Total-Count` — the common convention for
   collection totals; no name is specified in the request.
2. **Header presence.** Recommend present only when pagination parameters are
   supplied, because the requirement freezes unpaginated requests to the
   current behavior. Always-on would add a header to the default path, a
   user-visible contract change.
3. **Partial-parameter semantics.** Recommend each parameter independent:
   `limit` alone returns the first `limit` notes, `offset` alone returns the
   tail from `offset` (default offset 0, default limit none); "without
   pagination" means neither parameter is present. Requiring both instead
   would need a specified error for partial input, which is unspecified.
4. **Value bounds.** Recommend `ge=0` on both parameters so negative values
   are standard 422s; without bounds, SQLite's own semantics would silently
   reinterpret them (negative `LIMIT` means unbounded, negative `OFFSET`
   means 0). Recommend no server-side maximum on `limit` since none was
   specified; a cap can be added later.

Resolved locally (reversible implementation choices):

- The paginated query orders explicitly by `notes.c.id`; the unpaginated query
  keeps today's `notes.select()` verbatim.
- New CRUD functions are additive; `get_all` is not modified, so the other
  routes and the default path cannot drift.
- The header is set through FastAPI's injected `Response`; the handler still
  returns a plain list, so serialization and the JSON array shape stay as
  today.
- Names and file placement follow the existing module layout; no new
  dependencies.

### Documentation

Audience: API clients reading the maintained `README.md`. The sentence "The
collection route currently returns every note as a JSON array"
(`README.md:3-4`) must be rewritten in the same reviewed change as the code to
describe the optional `limit`/`offset` parameters and the approved total-count
header. `docs/development/index.md` records that no notes-query specification
exists; creating one is out of scope unless requested. No generated
documentation exists for the route, so the generator boundary is unaffected.

### Task checklist

- [ ] 1. Add `get_page(offset, limit)` and `count_notes()` to
       `src/app/api/crud.py`; leave all existing CRUD functions unchanged.
- [ ] 2. Extend `read_all_notes` in `src/app/api/notes.py` with optional
       validated `limit`/`offset` query parameters, the approved total-count
       header, and an unchanged unpaginated path.
- [ ] 3. Confirm the test harness runs the app lifespan so the database is
       connected during tests, and make paginated tests deterministic by
       clearing `notes` through the real database before seeding.
- [ ] 4. Add HTTP-boundary tests in `src/tests/test_notes.py` for: the exact
       ascending-ID slice and header value on paginated requests; the
       unchanged full-array response on unpaginated requests (including the
       approved header-presence assertion); standard 422 validation for
       `limit=abc` and the approved negative-value cases; and a roundtrip over
       the remaining CRUD routes as regression evidence.
- [ ] 5. Update the `README.md` collection-route description in the same
       change.
- [ ] 6. Run the full pytest suite and confirm the intended tests collect,
       run, and exit cleanly.

### Requirement verification

Evidence crosses the real app path (TestClient → FastAPI routing → CRUD →
SQLite); no mock substitutes for the claimed behavior.

- Bounded ascending-ID slice: test `GET /notes/?limit=..&offset=..` against
  seeded notes, asserting exactly the expected window in ascending-`id` order
  with the same object shape as the unpaginated response. Decisive.
- Total-count header: the same paginated test asserts the approved header
  equals the full count of seeded notes (an aggregate query, not the slice
  length). Decisive.
- Unpaginated compatibility: test `GET /notes/` returns every seeded note as a
  JSON array; existing `test_read_all_notes` keeps passing; header-presence
  assertion added per approved decision 2.
- FastAPI validation: `limit=abc` returns the standard 422 validation body;
  negative-value 422s per approved decision 4.
- Other routes unchanged: code review confirms no edits, plus a real
  roundtrip test (POST → GET/{id} → PUT → DELETE) through the production
  path; existing `test_crud_routes_exist` keeps passing.
- README updated: diff reviewed in the same change as the code.

### Additional implementation verification

- Spot-check `GET /openapi.json` after implementation to confirm the two
  optional query parameters appear and the collection route's response schema
  is unchanged.
- The full-suite clean run (task 6) is the success gate. If the
  lifespan/harness issue in Supporting facts is confirmed, the fixture fix is
  maintained-harness work verified through the new paginated tests as real
  consumers.