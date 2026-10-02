# Books page discovery for larger collections

Plan and track the Books page discovery capability: read-status filtering,
title/author search, bounded pagination, and URL share/restore, with the
table, active controls, empty state, browser navigation, and CRUD refreshes
kept consistent with the selected view. Existing CRUD behavior and unfiltered
API compatibility must be preserved. Planning only — implementation is not
authorized until the plans below are approved.

## Requirements checklist

- [ ] Books can be filtered by read status (all / read / unread) on the Books page.
- [ ] Books can be searched by title or author, matching case-insensitively.
- [ ] Results can be paged with a server-enforced, bounded page size.
- [ ] The selected discovery state (filter, search, page) is encoded in the URL so it can be shared and restored.
- [ ] Opening a shared URL restores the same view, and browser back/forward moves between discovery states.
- [ ] The table, active controls, empty state, browser navigation, and CRUD refreshes stay consistent with the selected view.
- [ ] Existing CRUD behavior (POST /books, PUT/DELETE /books/<book_id>) is preserved.
- [ ] `GET /books` without discovery query params keeps returning the full unfiltered list in the current response shape.

## Requirement questions

- Q1 — Should the table show each book's read status (column or badge) so the
  active read filter is legible? This adds visible UI beyond the literal
  request. Recommendation: yes, a minimal read indicator. Unresolved; gates
  subtask 020's template scope.

## Subtasks

- [ ] tasks/20260919-books-page-discovery/010-server-discovery-query.md — API selection and compatibility (no dependency)
- [ ] tasks/20260919-books-page-discovery/020-books-page-discovery-controls.md — page controls and view consistency (depends on 010)
- [ ] tasks/20260919-books-page-discovery/030-url-discovery-state.md — URL share/restore and history (depends on 020)

## Supporting facts

Verified from the current codebase:

- `server/app.py` keeps an in-memory `BOOKS` list and serves `GET/POST /books`
  (`{"status": "success", "books": [...]}`) and `PUT/DELETE /books/<book_id>`
  (`{"status": "success", "book": ...}`). No query parameters are read today.
- `server/query.py::list_books(books)` is a passthrough and is not imported by
  `app.py` — a currently unused seam that gives selection logic an owned home.
- `client/src/api/books.js::getBooks(params = {})` already forwards params as
  query parameters, so client transport needs no change to send discovery params.
- `client/src/components/Books.vue` loads all books on mount, renders a
  title/author table with the "No books found." empty state, and re-fetches via
  `getBooks()` after each add/update/remove.
- `client/src/router.js` is vue-router 4 with `createWebHistory` and a single
  `/books` route; `client/src/http.js` is axios with baseURL
  `http://localhost:5000`.
- Existing coverage: `tests/test_books_api.py` asserts only status codes for
  the unfiltered list and CRUD (it does not prove response shape);
  `client/tests/Books.spec.js` mounts the component with a mocked api module
  and asserts the empty state; `client/tests/books.integration.js` is an empty
  placeholder with no transport integration coverage.
- `docs/development/index.md` currently states "No book-discovery
  specification exists." — the intended home for the discovery spec.

Constraints from AGENTS.md: avoid layer-only splits (each slice must leave an
independently useful or owned result); use the least expensive test that
proves behavior at the real boundary; update maintained documentation in the
same change that makes new claims true.

## Execution plan

Status: Draft

Decompose into three capability slices, executed in dependency order. Server
selection comes first because the page and URL slices consume its contract;
the page slice delivers user-visible discovery; the URL slice adds
share/restore on top of the stabilized state model. No slice is a layer-only
split: each leaves an independently useful or owned result (an API capability,
a working page discovery view, shareable links).

Cross-cutting verification: run the pytest suite (`tests/`) and the vitest
suite (`client/tests/`) after each slice and once at the end. Compatibility
regressions (unfiltered `GET /books`, CRUD endpoints) are asserted explicitly
in 010; existing component coverage is kept as a default-view regression
anchor with its mock updated to the new API contract. No end-to-end or hosted
harness is added in this task.

Risks:

- The discovery query parameters and response additions are public API
  surface; keep changes additive and leave the param-less path exactly as it
  is today.
- Router query sync can loop (route watcher vs control writer); bound it with
  memory-history component tests and a single source of truth.
- The existing `Books.spec.js` mock must carry the new contract (e.g.
  `total`) once the component consumes it; update the maintained test harness
  to the real contract rather than special-casing the component.
- The store is in-memory, so CRUD can shrink the filtered set; clamp the page
  after refreshes so the view never rests on an empty out-of-range page.

### Implementation decisions and open questions

These need approval before execution (public API / user-visible behavior):

- D1 — API contract (recommendation): discovery params `read` (`read` |
  `unread`), `q` (case-insensitive substring over title and author), and
  `page` (1-based); page size is a fixed server constant (10), not a client
  parameter. The response adds `total` (count of books matching filter and
  search); `books` holds the selected page's items when any discovery param is
  present and the full list when none are.
- D2 — Out-of-range page requests (recommendation): the server returns an
  empty `books` page with the correct `total`; the client clamps to the last
  valid page after refreshes (D5).
- D3 — URL encoding (recommendation): mirror the API params (`read`, `q`,
  `page`) in the router query; omit defaults (no filter value, empty `q`,
  page 1) so the default view keeps a clean URL.
- D4 — History behavior (recommendation): committed changes (filter change,
  search submission, page change) push a history entry; live typing does not.
- D5 — Post-refresh clamping (recommendation): if the current page exceeds the
  last valid page after a CRUD refresh, clamp to the last valid page and
  update the URL with `replace`.
- D6 — Invalid URL/API values (recommendation): unknown `read` values and
  non-positive or non-numeric `page` are treated as absent (defaults) rather
  than rejected; document the rule. Flagged because it is API-visible
  behavior.
- Q1 (from above, requirement question) — read-status indicator in the table.

### Documentation

Audience: developers using the API and the Books page. Replace the "No
book-discovery specification exists." placeholder in
`docs/development/index.md` with a concise book-discovery specification
covering the API contract (010), page controls and view consistency (020),
and URL share/restore behavior (030). Each subtask updates its slice in the
same change that makes the claims true. No new directories or placeholder
pages.

### Task checklist

- [ ] tasks/20260919-books-page-discovery/010-server-discovery-query.md
- [ ] tasks/20260919-books-page-discovery/020-books-page-discovery-controls.md
- [ ] tasks/20260919-books-page-discovery/030-url-discovery-state.md
- [ ] Final integration check: both test suites pass, documentation updated, requirement verification current in every subtask.

### Requirement verification

- Discovery API (filter/search/pagination/total), unfiltered compatibility,
  and CRUD preservation → subtask 010, pytest at the Flask HTTP boundary
  (`tests/test_books_api.py`). Existing coverage asserts only status codes, so
  new explicit compatibility assertions are required rather than assumed.
- Page controls, table/empty-state/CRUD view consistency → subtask 020,
  component tests at the api-module boundary (`client/tests/Books.spec.js`);
  the existing empty-state test remains the default-view regression anchor
  once its mock carries the new contract.
- URL share/restore and back/forward consistency → subtask 030, component
  tests with a vue-router memory history instance.
- No requirement is claimed complete until its subtask records passing
  evidence at the boundary named above.