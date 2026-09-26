# 010 — Read-status filter (All / Read / Unread)

Deliver read-status filtering end to end: `GET /books` accepts a `read` query param, the Books page gains a status control and a read indicator, the table and empty state reflect the selection, the URL encodes it, and CRUD refreshes preserve it. This subtask also establishes the shared live integration harness reused by 020–040.

Parent Task: tasks/20260925-books-discovery/000-main.md
Depends On: None (first subtask; establishes the query-state sync pattern and the live-path harness)

## Requirements checklist

- [ ] `GET /books?read=true` returns only read books and `GET /books?read=false` only unread; the param absent returns the full list in the existing envelope.
- [ ] The Books page offers an All/Read/Unread control; the table shows a read indicator; rows and empty state reflect the selection.
- [ ] Selecting a status updates the URL (`?read=true|false`; All removes the param) and re-fetches; opening a URL with `?read=…` restores the filtered view.
- [ ] add / update / remove behave exactly as before, and their refresh keeps the active filter (view stays consistent).
- [ ] Unfiltered API compatibility and existing CRUD behavior verified against the current tests.

## Supporting details

- The table currently renders title/author only, and CRUD refreshes call bare `getBooks()` (`client/src/components/Books.vue:18-31`); the refresh path is where filtered re-fetching hooks in without changing CRUD semantics.
- `getBooks(params)` already forwards params (`client/src/api/books.js:3-5`).
- Extend the unused `server/query.py` seam (`list_books(books, params)`) rather than filtering inline in `server/app.py`.
- The live harness lives in `client/tests/books.integration.js` (currently a placeholder): spawn Flask on an ephemeral port, override the axios base URL via environment, mount Books with the real history router. First consumed by this subtask's decisive test; reused by 020–040.
- Shared contract and history semantics are defined in the parent plan and apply here once approved.

## Execution plan

Status: Draft

1. Server: parse `read` from `request.args`; delegate to `list_books(books, {"read": value})` in `server/query.py`; unknown values treated as absent; envelope unchanged; POST/PUT/DELETE untouched.
2. Client: `Books.vue` reads `read` from `route.query` as the source of truth; the control writes via `router.push` (approved history semantics); a watcher triggers `getBooks({read})`; the table gains a read indicator column; CRUD refresh passes the current params.
3. Empty state: filtered-no-match message when the selection yields nothing; collection-empty message unchanged.
4. Tests: pytest — filtered queries, absent-param full list, unknown value, CRUD round-trip unchanged; vitest component spec — control reflects and updates selection, table, empty state; decisive live-path test in `books.integration.js`.
5. Docs: README Books API section documents `read` and the compatibility statement in this same change.

### Implementation decisions and open questions

- Material (see parent plan, pending approval): `read` param naming/values, unknown-value handling, filtered empty-state copy, history semantics.
- Local: read indicator as text ("Read" / "Unread"); control as a three-option group. Reversible.
- Execution-time dependency note: the harness needs a DOM environment for mounting (vitest default is `node`); adding jsdom as a devDependency (or an equivalent environment config) is part of this subtask's harness work.

### Documentation

- Root `README.md`: add the Books API section covering `read` and the compatibility statement; mention Books-page filtering in the description. Same change as the code.

### Task checklist

- [ ] Server `read` param + `server/query.py` selection + unchanged envelope
- [ ] Client query-derived state, status control, read column, filtered fetch and CRUD refresh with params
- [ ] Live-path harness created in `client/tests/books.integration.js`
- [ ] pytest param/compatibility tests; vitest component spec; decisive live-path test
- [ ] README API section updated

### Requirement verification

- Decisive (R1; URL facet of R4): live-path test — real router + real axios + spawned Flask: activating Unread updates the query and shows only unread rows; a fresh mount with `?read=false` restores the filtered table and control.
- Supporting: pytest route tests (param filtering, absent-param full list, unknown value); component spec (control state, table, empty state).
- R6 evidence: `tests/test_books_api.py` passes unmodified; an explicit no-params shape test is added here.

### Additional implementation verification

- The harness is verified through this subtask's decisive consumer test; later subtasks reuse it rather than re-creating transport setups.