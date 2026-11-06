# Books page discovery: filter, search, pagination, URL state

Make the Books page practical for a larger collection: filter by read status,
search by title or author, move through bounded pages, and share or restore
the current view through the URL. The table, active controls, empty state,
browser navigation, and CRUD refreshes stay consistent with the selected
view. Existing CRUD behavior and unfiltered API compatibility are preserved.

## Requirements checklist

- [ ] R1 — Read-status filter: the Books page can show only read, only unread, or all books, and the table, active controls, and empty state reflect the selected filter.
- [ ] R2 — Search: the Books page can filter by a text query matching title or author, composing with the read-status filter and pagination.
- [ ] R3 — Pagination: the Books page moves through bounded pages of the current view; page controls, table contents, and empty state agree on the selected page.
- [ ] R4 — URL state: the selected read filter, search text, and page are encoded in the `/books` URL; opening a shared URL restores the view; browser back/forward moves between views with the page staying consistent.
- [ ] R5 — CRUD consistency: add, update, and delete refresh the page within the selected view (the refresh uses the active filter/search/page; the page clamps if the view shrinks below the current page).
- [ ] R6 — API compatibility: `GET /books` without query parameters returns the full list exactly as today, and the POST/PUT/DELETE book endpoints keep their current behavior.
- [ ] R7 — Data selection API: `GET /books` supports read-status filtering, title/author search, and bounded pagination through query parameters, usable independently of the Vue client.
- [ ] R8 — Documentation: maintained documentation describes the new Books page behavior and the new public query parameters in the same changes that make them true (AGENTS.md documentation policy).

Requirement → owner mapping: R6, R7, R8 (API reference) → `010-server-query-api.md`; R1–R5, R8 (page behavior) → `020-books-page-discovery-ui.md`. R6 compatibility is additionally re-observed on the client by 020's preserved specs.

## Subtasks

- [ ] tasks/20261029-books-page-discovery/010-server-query-api.md — server-side data selection on `GET /books`; owns the public query contract and the compatibility constraint.
- [ ] tasks/20261029-books-page-discovery/020-books-page-discovery-ui.md — Books page capability end-to-end; depends on 010 and owns the decisive client↔server integration check.

## Open questions

- Documentation destination: extend the root README (recommended — smallest structure; it is currently the only maintained product documentation) versus adding a book-discovery specification page under `docs/` (`docs/development/index.md` records "No book-discovery specification exists"). No specification was requested; README-only is recommended unless a specification is wanted.

## Decisions

- Discovery runs server-side: `GET /books` gains query parameters and the client sends them through the existing `getBooks(params)` path. Implied by the request's "unfiltered API compatibility" (the API itself gains filtering) and required for bounded pages over a larger collection; client-side-only filtering was rejected.
- The default view is unchanged: no query parameters mean all books, page 1.
- No sorting and no page-size control: the request names filter, search, bounded pages, and URL state only; anything else is excluded.

## Supporting facts (research)

- Server: `server/app.py` keeps an in-memory `BOOKS` list (records carry `id`, `title`, `author`, `read`); `GET/POST /books` and `PUT/DELETE /books/<id>` respond `{"status": "success", ...}`. `server/query.py:list_books` is an unused seam that copies the list — the natural home for selection logic.
- Client: `client/src/api/books.js:getBooks(params)` already forwards query parameters; `client/src/http.js` hardcodes `baseURL: "http://localhost:5000"`; `client/src/router.js` uses vue-router 4 (`createWebHistory`) with a single `/books` route; `Books.vue` renders a table or "No books found." and re-fetches all books after add/update/remove.
- Tests: pytest with the Flask test client (`tests/test_books_api.py`) covers the unfiltered list and CRUD; vitest (`client/tests/Books.spec.js`) mounts `Books` with the API module mocked; `client/tests/books.integration.js` is a stub stating that no production transport integration coverage exists — the intended home for the decisive client↔server check.
- Tooling: server deps via `pyproject.toml` (flask); client deps via `client/package.json` (vue 3, vue-router 4, axios, vitest, @vue/test-utils). `client/package.json` defines no dev/build scripts — only `npm test`.

## Execution plan

Status: Draft

### Approach

Two children split at the client/server compatibility boundary, each leaving an independently acceptable result:

1. `010-server-query-api.md` — adds read-status filtering, title/author search, and bounded pagination to `GET /books`, and owns the public contract. Independently useful to API consumers, independently accepted at the HTTP boundary, and it owns the compatibility constraint (unfiltered GET and CRUD unchanged).
2. `020-books-page-discovery-ui.md` — builds the Books page capability (controls, URL share/restore, browser navigation, CRUD-refresh consistency) on that contract and owns the one decisive check that traverses real client transport, HTTP routing, and server data selection together.

The client capability is one child: filter, search, pagination, and URL state are one view state. Splitting them would leave no child with an independently acceptable result — URL sync without controls has nothing meaningful to restore, and controls without URL state fail share/restore. Testing, integration, and documentation stay inside the child that owns the outcome. Execution order: 010 before 020; 020 consumes the contract 010 defines.

### Design

- The URL mirrors the API: `read`, `search`, and `page` use the same names and semantics in `/books` query strings and `GET /books` query parameters, so view-state translation is direct and a shared link is a literal API query. Default state (all books, page 1) is encoded by absent parameters.
- `page_size` stays fixed at the server default in the UI; the page renders "Page X of Y" from the API response `total`.
- CRUD refreshes reuse the component's derived query parameters; if a delete empties the current page while earlier pages exist, the page clamps back so controls, table, and empty state never contradict each other.
- The full query contract (names, parsing, response shape, defaults, caps) is specified in `010-server-query-api.md`; 020 consumes it as-is.

### Verification strategy

- 010: pytest route tests through the real Flask app cover each parameter, their composition, `total`, page bounds, and unfiltered/CRUD compatibility (existing tests must pass unchanged).
- 020: component tests with the real component and real vue-router (transport mocked) cover view state, URL encoding, restore, back/forward, and CRUD-refresh consistency; one decisive integration test (replacing the `client/tests/books.integration.js` stub) mounts the real component against the real Flask server through production HTTP.
- After each child, run the full existing suites (pytest; `npm test`) to catch regressions.

### Implementation decisions and open questions

- Server-side selection — decided; implied by "unfiltered API compatibility" and "bounded pages" (see Decisions above).
- Decomposition into server contract (010) and client capability (020); no further layering.
- Open question: documentation destination (see Open questions above) — README-only recommended; a spec page would be target documentation the request did not ask for.

### Documentation

- Root README is the intended reader surface for both audiences: 010 adds the `/books` query-parameter reference, 020 adds the Books page behavior description — each in the same change as the code that makes it true. No new documentation pages or directories.

### Task checklist

- [ ] Execute tasks/20261029-books-page-discovery/010-server-query-api.md (query contract + compatibility evidence + API docs).
- [ ] Execute tasks/20261029-books-page-discovery/020-books-page-discovery-ui.md (page capability + decisive integration check + page docs).

### Requirement verification

- R1–R5 → 020 evidence: component tests at the client state/routing/rendering boundary, plus the decisive integration test through real client transport, HTTP routing, and server selection (no mocked bypass for the product connection).
- R6 → 010 evidence: existing server tests pass unchanged plus new explicit no-parameter response assertions; re-observed on the client by 020's preserved empty-state/CRUD specs.
- R7 → 010 evidence: route tests at the HTTP boundary for each parameter and their composition; usable independently of the client.
- R8 → documentation diffs reviewed within 010 (API reference) and 020 (page behavior).

### Additional implementation verification

- Run the entire existing pytest and vitest suites after each child; both must collect and exit cleanly, with no existing test modified to accommodate new behavior except where 020 extends the Books specs.
