# Books discovery: read-status filter, search, pagination, shareable view state

Make the Books page practical for a larger collection. Users filter by read status, search by title or author, move through bounded pages, and share or restore the current discovery state through the URL. The table, active controls, empty state, browser navigation, and CRUD refreshes stay consistent with the selected view, while existing CRUD behavior and the unfiltered `/books` API remain unchanged.

No unresolved requirement-level questions: the four user outcomes and the compatibility constraint come from the approved request. Material design decisions (API/URL contract, clamping, history semantics, empty-state copy) are collected in the plan's decisions section below and need approval before execution.

## Requirements checklist

- [ ] R1 — Books can be filtered by read status (All / Read / Unread); the table, active control, empty state, and CRUD refreshes reflect the selection. Owner: 010.
- [ ] R2 — Books can be searched by title or author (case-insensitive substring, either field), combined with the read-status filter. Owner: 020.
- [ ] R3 — Results are paginated with a bounded page size and bounded page range; the page stays consistent with filter, search, and CRUD changes. Owner: 030.
- [ ] R4 — The complete discovery state (read status, search, page) is encoded in the URL, shareable, restorable on refresh or deep link, and consistent with browser back/forward. Owner: 040 (individual params are encoded by 010–030 as they land).
- [ ] R5 — View consistency holds for every state combination: table, active controls, empty state, browser navigation, and CRUD refreshes all agree with the selected view. Owner: explicit combination — per-state facets in 010–030, combined-state facets in 040.
- [ ] R6 — Existing CRUD behavior (add / update / remove) and the unfiltered `GET /books` contract (full list in the existing envelope) are preserved. Owner: 010 for explicit compatibility evidence; 020–040 must not regress it.

## Scope

In scope: the Books view (controls, table, read indicator, empty state), vue-router query sync, the `GET /books` query contract (filter, search, paging params plus additive paging metadata), server-side selection in `server/query.py`, and the tests and documentation covering these.

Out of scope: CRUD semantics changes, sorting, a page-size control, persistence beyond the URL, storage model changes (stays in-memory), other routes or pages.

## Subtasks

- [ ] tasks/20260925-books-discovery/010-read-status-filter.md — Read-status filter: API param, control, read indicator, URL param, filtered-view consistency; establishes the shared live integration harness.
- [ ] tasks/20260925-books-discovery/020-title-author-search.md — Title/author search combined with the read filter; URL `q` param.
- [ ] tasks/20260925-books-discovery/030-pagination.md — Bounded pagination: server envelope, pager UI, URL page param, reset and clamping consistency.
- [ ] tasks/20260925-books-discovery/040-url-state-navigation.md — Combined-state URL share/restore and browser navigation; closes R4 and the combined facets of R5.

## Supporting details

Facts from inspection (2026-09-25):

- `client/src/components/Books.vue` renders a title/author table with a "No books found." empty state, loads via bare `getBooks()`, and re-fetches with bare `getBooks()` after add/update/remove; those CRUD methods exist but the template has no controls invoking them.
- `getBooks(params)` already forwards query params (`client/src/api/books.js:3-5`); the axios base URL is hardcoded to `http://localhost:5000` (`client/src/http.js:3`).
- `client/src/router.js` creates a history-mode router with a `/books` route and no query handling. No app entry file exists (`createApp` appears nowhere), so the integration harness must compose router + component the way production wiring would.
- `server/app.py` serves an in-memory `BOOKS` list; `GET /books` returns `{status, books}` with the full list; POST/PUT/DELETE perform no validation and have no param interplay. `server/query.py` defines an unused `list_books(books)` seam for data selection.
- Tests: pytest runs through `app.test_client()` (`tests/conftest.py`) with two tests (GET status, CRUD round-trip). Vitest has one component spec that mocks the API module (`client/tests/Books.spec.js`). `client/tests/books.integration.js` is an explicit placeholder stating no production-transport integration coverage exists yet.
- Seed data is two books; discovery behavior must be exercised by seeding through the real POST API in tests, not by changing production seeds.
- Assumptions: pytest is available in the environment (existing suite imports it); vitest mounting needs a DOM environment (vitest default is `node`), so the harness work in 010 likely adds a jsdom-based environment — an execution-time dependency decision.

## Execution plan

Status: Draft

Design:

- **State and data flow.** The vue-router query on `/books` is the single source of truth for the discovery view. `Books.vue` derives `{read, q, page}` from `route.query`, fetches `/books` with those params through `getBooks`, and writes control changes back through the router. CRUD refreshes re-fetch with the current query params, so the selected view survives every mutation.
- **API contract (additive only).** `GET /books` accepts `read=true|false` (absent = all), `q` (case-insensitive substring against title or author; AND-combined with `read`), and `page` (1-based) with a fixed bounded `per_page` (default 5, max 50, not user-configurable). The response keeps `{status, books}` and adds `total`, `page`, `per_page` metadata. POST/PUT/DELETE handlers are untouched.
- **Server selection.** `server/query.py` owns selection — `list_books(books, params)` applies read status, search, and paging; `server/app.py` only parses `request.args` and serializes. Unknown `read` values are treated as absent; out-of-range or invalid `page`/`per_page` clamp to the nearest valid value rather than erroring.
- **Client controls.** Read-status control (All/Read/Unread), search input, pager (Prev/Next with "Page X of Y"), and a read indicator column so filter effects are visible. Filtered-empty results show a filter-aware empty-state message; the collection-empty message stays as is; the pager is hidden when no results match.
- **History semantics.** Read-status and page changes push history entries; search typing is debounced and written with `router.replace`, so one settled query is one entry and back/forward restores prior discovery states.
- **Shared live-path harness.** `client/tests/books.integration.js` becomes the production-path harness: spawn the Flask server on an ephemeral port, point axios at it via an env-overridable base URL (default unchanged), mount Books with the real history router and real axios. 010 creates and first consumes it; 020–040 reuse it. It is maintained test infrastructure, verified through its real consumer tests — no transport mocks in the decisive checks.
- **Execution order.** 010 → 020 → 030 → 040, each a declared dependency of the next: 020 combines search with 010's filter, 030 resets/clamps the page on 010/020 state changes, 040 verifies the combined URL contract and navigation.

### Implementation decisions and open questions

Material decisions pending approval (execution waits; recommendations given):

1. Query contract naming and shape — `read=true|false` (absent = all) rather than a `status` enum; `q`; `page`; fixed `per_page`; additive `total`/`page`/`per_page` response metadata. (Recommended: mirrors the model field and keeps the unfiltered contract untouched.)
2. Out-of-range or invalid `page`/`per_page` — clamp to the nearest valid value rather than returning 400. (Recommended: shared URLs never become failure states.)
3. History semantics — push for read-status and page changes; debounced `replace` for search text. (Recommended: back/forward restores prior views without one entry per keystroke.)
4. Filtered empty-state copy — "No books match your filters." for filter/search empty results; "No books found." kept for an empty collection. (Recommended: makes the empty state reflect the selected view.)
5. No page-size control in this iteration; `per_page` is a fixed server default. (Recommended: smallest change that satisfies "bounded pages".)

Local, reversible decisions taken in-plan: unknown `read` values treated as absent; axios base URL becomes env-overridable with unchanged default; read indicator rendered as text ("Read" / "Unread").

### Documentation

- Root `README.md` gains a concise Books API section (query params, paging metadata, unfiltered-compatibility statement) plus Books-page usage notes; each subtask updates it in the same change that makes the claims true (010: `read` + compatibility; 020: `q`; 030: paging; 040: share/restore via URL).
- `docs/development/index.md` currently says no book-discovery specification exists; once the contract is documented it will point to it instead. No new directories or placeholder pages.

### Task checklist

- [ ] tasks/20260925-books-discovery/010-read-status-filter.md
- [ ] tasks/20260925-books-discovery/020-title-author-search.md (depends on 010)
- [ ] tasks/20260925-books-discovery/030-pagination.md (depends on 010, 020)
- [ ] tasks/20260925-books-discovery/040-url-state-navigation.md (depends on 010, 020, 030)

### Requirement verification

- R1 → decisive: live-path integration test in 010 — real history router + real axios against the spawned Flask server: activating Unread writes `?read=false`, re-fetches, and shows only unread rows; a fresh mount with `?read=false` restores the filtered table and control. Supporting: pytest route tests for the `read` param; component spec for control and table rendering.
- R2 → decisive: live-path test in 020, including filter+search combination through the full path. Supporting: `server/query.py` selection unit tests; pytest route tests.
- R3 → decisive: live-path test in 030 — page navigation through the real path, page reset when filter/search changes, clamping after a delete shrinks the last page. Supporting: pytest tests for envelope metadata and bounds.
- R4 → decisive: live-path test in 040 — fresh load of `/books?read=…&q=…&page=…` restores table, controls, and pager; router back/forward moves between prior discovery states with consistent views. (No manual browser check is defined in this fixture; the automated live path traverses router, axios transport, Flask routing, and query selection together.)
- R5 → facet owners: 010 (filtered table, empty state, refresh), 020 (combined active controls, empty state), 030 (pager, reset, clamp), 040 (combined-state navigation and CRUD refresh).
- R6 → decisive: existing `tests/test_books_api.py` passes unmodified plus an explicit no-params full-list/shape test added in 010; re-run per subtask.

### Additional implementation verification

- Guard against cross-test pollution: `BOOKS` is module-global; new pytest tests use unique book ids, and the harness starts a fresh Flask process per run.
- Confirm the paging envelope change never alters the `books` array contract itself (same fields, insertion order preserved through filtering and slicing).