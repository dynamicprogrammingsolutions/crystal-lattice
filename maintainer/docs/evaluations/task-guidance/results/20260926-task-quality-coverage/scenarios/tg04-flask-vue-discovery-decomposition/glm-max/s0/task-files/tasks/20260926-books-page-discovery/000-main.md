# Books page discovery (read filter, search, bounded pagination, URL state)

Make the Books page practical for a larger collection: users filter by read
status, search by title or author, move through bounded pages, and share or
restore the current discovery state through the URL, while table, active
controls, empty state, browser navigation, and CRUD refreshes stay consistent
with the selected view and existing CRUD behavior plus unfiltered API
compatibility are preserved. Planning only — execution awaits approval.

## Requirements checklist

- [ ] R1 — Books page filters books by read status (all / read / unread).
- [ ] R2 — Books page searches books by title or author (case-insensitive
      substring; a match in either field satisfies the query).
- [ ] R3 — Books page presents results in bounded pages the user can move
      through (visible bounds, no navigation past the last page).
- [ ] R4 — The current discovery state (read filter, search text, page) is
      encoded in the `/books` URL and restored when that URL is opened; the
      default view keeps a clean URL.
- [ ] R5 — Browser back/forward navigation keeps the table, active controls,
      and loaded data consistent with the URL-restored view.
- [ ] R6 — The table, active controls (filter, search, pagination), and empty
      state always reflect the selected view.
- [ ] R7 — Add/update/delete refreshes the table using the selected view
      (refetch honors the view; a page left out of range resolves to a valid
      page) without changing CRUD semantics.
- [ ] R8 — Existing CRUD behavior is preserved (POST `/books`,
      PUT/DELETE `/books/<id>` semantics unchanged).
- [ ] R9 — Unfiltered API compatibility is preserved (GET `/books` without
      discovery params returns the current envelope with the full list).
- [ ] R10 — Maintained documentation describes the shipped behavior
      (discovery specification plus README) in the same changes as the code
      (AGENTS.md documentation policy).
- [ ] R11 — Changed behavior has verification evidence at the boundaries it
      crosses: Flask HTTP API, Vue view, and the real client↔server transport
      (AGENTS.md testing policy).

## Subtasks

- [ ] tasks/20260926-books-page-discovery/010-server-discovery-api.md
- [ ] tasks/20260926-books-page-discovery/020-client-discovery-view.md (depends on 010)
- [ ] tasks/20260926-books-page-discovery/030-url-share-restore.md (depends on 010, 020)

## Questions and decisions

- No unresolved requirement questions: the requested outcomes and the two
  preserved contracts (existing CRUD behavior, unfiltered API compatibility)
  are fully specified by the request and current behavior.
- Material design decisions that define the public API contract and
  user-visible URL/UX behavior (D1–D7) are collected with recommendations in
  `### Implementation decisions and open questions` below and await approval
  together with the plan. None are resolved unilaterally.

## Supporting facts (research)

Verified in the current tree:

- `server/app.py:10-24` — GET `/books` returns `{"status": "success",
  "books": BOOKS}` (full list; no query params are read). POST/PUT/DELETE
  mutate a module-level `BOOKS` list; a missing id raises via `next()`.
- `server/query.py:1-2` — `list_books(books)` exists but is unused; it is the
  data-selection seam this capability should own.
- `client/src/api/books.js:3-5` — `getBooks(params)` already forwards query
  params to axios; CRUD helpers are unaffected.
- `client/src/components/Books.vue:17-32` — the component holds only the
  fetched `books` array, and every CRUD method refetches with paramless
  `getBooks()`, so refreshes would ignore any view.
- `client/src/router.js` — vue-router 4 in history mode, `/books` route, no
  query handling.
- `client/src/http.js:3` — axios baseURL hardcoded to `http://localhost:5000`.
- `tests/test_books_api.py` — smoke-level HTTP tests only; `tests/conftest.py`
  uses the module-level `BOOKS` list, so selection tests need deterministic
  seeding/reset.
- `client/tests/Books.spec.js` — component test mocks the API module and
  asserts only the empty state;
  `client/tests/books.integration.js` is an explicit placeholder ("No
  production transport integration coverage exists yet").
- Docs: `README.md` describes the app in one line;
  `docs/development/index.md` states "No book-discovery specification
  exists."; `docs/development/documentation.md` was read as required before
  planning doc changes.

Assumptions / risks (unverified — installing dependencies during planning is
out of scope):

- `client/package.json` declares no jsdom/happy-dom and no vitest environment
  config; the existing component spec may not run until a DOM environment is
  configured. Establish the runner baseline before extending the suite.
- No node_modules or lockfile exists in the fixture; runs require dependency
  installation at implementation time.

## Execution plan

Status: Draft

### Design

The capability is one data flow crossing four boundaries:

    URL query → view state → API params → server selection → rows + metadata → table / controls / empty state

Three slices, split by end-to-end capability rather than by mechanical layer,
per the project guidance (split only where a layer leaves an independently
useful, owned result):

1. **Server discovery API (010)** — the public API contract and its
   compatibility boundary. Independently usable by API consumers without the
   Vue client, with its own HTTP-boundary acceptance and the unfiltered
   compatibility constraint named in the request.
2. **Client discovery view (020)** — in-session browsing: controls, bounded
   pagination, view-consistent table/empty states, and CRUD refreshes that
   honor the view. Owns the first real client↔server transport integration
   evidence, which component tests with a mocked transport cannot provide.
3. **URL share/restore (030)** — the state-travels-through-URL capability:
   encode, restore, normalize, back/forward, and URL sync after CRUD/clamp.
   Depends on 020's view state.

State model: `Books.vue` owns a single reactive view object
`{ read, q, page }` with one `refresh()` path that calls
`getBooks(viewParams)` and stores rows plus pagination metadata; all CRUD
methods call `refresh()`. This shape is chosen in 020 deliberately so 030
binds the same object to the route query without reworking state.

Compatibility strategy: paramless GET `/books` keeps the exact current
envelope (R9); CRUD routes are untouched (R8); the Vue client always sends
explicit discovery params (at minimum `page`) so the page always consumes the
paginated envelope while the paramless path remains untouched for external
consumers (D3).

Verification strategy: evidence at each boundary — pytest through the Flask
test client for the API contract (010), vitest component tests with the
transport mocked for view logic (020/030), and vitest integration tests
against the real Flask server over real axios for the client↔server chain
(020) and the deep-link restore path (030). Component tests with a mocked API
are supporting evidence, never the decisive check for a connection that
crosses the transport.

### Implementation decisions and open questions

All decisions below are recommendations awaiting approval with the plan.
D1–D4 define the public API contract; D5–D7 are user-visible behavior.

- **D1 — Selection executes server-side.** GET `/books` gains optional
  `read` (`true`/`false`; absent = all), `q` (case-insensitive substring on
  title OR author), and `page` (1-based positive integer); page size is a
  fixed server constant, recommended 10. Rationale: "practical for a larger
  collection" plus the provided `server/query.py` seam; client-side
  pagination of an unbounded fetch would not scale. Rejected alternative:
  filtering the full list in the client.
- **D2 — Response envelope.** When any discovery param is present, the
  response is the current envelope plus pagination metadata:
  `{"status", "books", "page", "page_size", "total", "total_pages"}`. A
  paramless GET returns the current body unchanged — the strictest reading of
  "unfiltered API compatibility."
- **D3 — Client always sends explicit params.** The page always requests the
  paginated envelope (at minimum `page`), so it never depends on shape
  branching; the paramless path stays intact for external consumers.
- **D4 — Validation policy.** Malformed `read` or `page` values → 400;
  an out-of-range `page` → empty `books` with correct metadata (the client
  clamps using metadata; URL normalization normally prevents out-of-range
  requests).
- **D5 — URL encoding.** `/books?read=unread&q=dune&page=2`; only
  non-default params are present (`read` tokens: `read`/`unread`; `q`
  URL-encoded; `page` positive integer). Default view = clean URL.
- **D6 — Search timing and history policy.** Search applies debounced
  (~300 ms) on input; each applied filter/search/page change is a history
  `push` so back/forward walks result states; normalization on load uses
  `replace` so no spurious history entries appear. Alternative (replace for
  everything) causes less history traffic but makes back/forward useless for
  result states.
- **D7 — Empty-state distinction.** "No books found." remains the
  collection-empty state; a filtered view matching nothing shows a distinct
  no-matches message. A "clear filters" affordance is recommended as the
  escape hatch for shared filtered URLs — confirm inclusion.

### Documentation

- Audience: maintainers and developers of this app (`docs/development`) and
  README readers.
- Destination: extend `docs/development/index.md` — replace the "No
  book-discovery specification exists." line with a concise book-discovery
  specification grown by each child: API contract (010), page behavior (020),
  URL state (030). Update `README.md` as user-facing behavior lands (020
  page features; 030 shareable state).
- No new documentation directories or placeholder pages — smallest structure
  that helps the reader, per documentation policy. Each doc claim lands in
  the same change as the code that makes it true.

### Task checklist

- [ ] Execute `tasks/20260926-books-page-discovery/010-server-discovery-api.md`
      (no dependencies).
- [ ] Execute `tasks/20260926-books-page-discovery/020-client-discovery-view.md`
      (depends on 010).
- [ ] Execute `tasks/20260926-books-page-discovery/030-url-share-restore.md`
      (depends on 010 and 020).

### Requirement verification

- R1/R2 (read filter, search) → 010 owns the API contract; decisive HTTP
  tests assert param selection (read true/false, q on title and author with
  case-insensitivity, combined). 020 owns the page behavior; decisive
  end-to-end check: 020's integration test through real axios + real Flask,
  from control to selected rows.
- R3 (bounded pagination) → 010 decisive HTTP tests for totals, page
  metadata, and out-of-range behavior; 020 decisive component test for
  bounds (prev/next disabled at edges) and indicator, plus integration
  paginating through the real server.
- R4 (share/restore) → 030; decisive: deep-link restore with the real router
  (component) and an integration case through the real server for the full
  production path.
- R5 (browser navigation) → 030; decisive: component test with the real
  history-mode router stepping back/forward. If jsdom cannot exercise real
  history navigation, the named fallback check is manual browser
  verification with exact steps recorded — not a silent memory-router
  substitute.
- R6 (view consistency) → 020 decisive component tests for table, controls,
  and both empty states; 030 extends consistency to URL-driven state.
- R7 (CRUD consistent with view) → 020 decisive component tests for
  refetch-with-view and out-of-range clamping; 030 decisive component test
  for URL sync after CRUD/clamp.
- R8 (CRUD preserved) → 010 decisive HTTP regression tests (unchanged CRUD
  semantics); 020 retains CRUD component regressions.
- R9 (unfiltered compatibility) → 010 decisive HTTP test asserting the
  paramless GET body is unchanged.
- R10 (docs) → each child updates the documentation its change makes true;
  verified by review in each child's checklist.
- R11 (evidence) → the per-child test tasks above; 020 owns the first real
  transport integration coverage; 030 extends it for URL restore.

### Additional implementation verification

- Full suite runs (pytest; client vitest including the integration file)
  collect and exit cleanly after each child; no skipped tests.
- After 030, a manual smoke of the production path (Flask on port 5000 plus
  the client): apply filter/search/page, open a shared deep link in a fresh
  context, and use browser back/forward — recorded with exact steps. This is
  the named manual check for R5 only if the automated history check proves
  impossible in jsdom; otherwise it is corroborating evidence.