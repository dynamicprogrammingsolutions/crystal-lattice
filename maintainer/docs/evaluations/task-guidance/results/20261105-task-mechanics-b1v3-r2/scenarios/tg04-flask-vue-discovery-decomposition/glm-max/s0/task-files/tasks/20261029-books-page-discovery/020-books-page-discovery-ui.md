# Books page discovery UI: filter, search, pagination, URL state

Build the Books page capability on the server query contract: a read-status
filter, title/author search, bounded pagination, URL share/restore with
browser navigation, and CRUD refreshes that stay inside the selected view.

Parent Task: tasks/20261029-books-page-discovery/000-main.md

Depends On: tasks/20261029-books-page-discovery/010-server-query-api.md (consumes the `GET /books` query contract defined there)

## Requirements checklist

- [ ] R1a — A read-status control (all / read / unread) drives the view; the table, active control state, and empty state reflect the selected filter.
- [ ] R2a — A search input filters by title or author and composes with the read filter and the selected page.
- [ ] R3a — Pagination controls move through bounded pages of the current view; bounds come from the API `total`; the controls stay truthful at the first and last page.
- [ ] R4a — The selected read filter, search text, and page are encoded in the `/books` URL; opening a shared URL restores exactly that view.
- [ ] R4b — Browser back and forward move between view states; table, controls, and empty state stay consistent with each restored view.
- [ ] R5a — Add, update, and delete refresh the list within the selected view; if the view shrinks below the current page, the page clamps so the table is never empty on a page while earlier pages exist.
- [ ] Ra — Consistency invariant: the table, active controls, pagination indicator, and empty state always describe the same selected view.
- [ ] R6c — Existing client behavior is preserved: CRUD flows still work end-to-end and the existing empty-state rendering assertion keeps passing.
- [ ] R8b — The Books page behavior (filter, search, pagination, shareable URL) is documented in the same change that implements it.

There are no unresolved requirement questions; material decisions are recorded in the execution plan below and take effect on plan approval.

## Execution plan

Status: Draft

### Design

- Single source of truth: the URL. The component derives `read`, `search`, and `page` from `route.query` (same names and semantics as the contract from `010-server-query-api.md`; absent parameters mean the defaults — all books, page 1). Every control change writes back through `router.push`, and a watcher on the effective query triggers the `getBooks` fetch. Deep links, back/forward, and control changes then all flow through one path, which is what makes the consistency invariant hold structurally rather than through per-case handling.
- Data flow: URL query → derived params → `getBooks(params)` → `{ books, total }` → table rows, "Page X of Y" indicator, prev/next enablement, and the empty state. The empty state shows whenever the selected view returns zero rows (including filtered-empty), preserving the existing "No books found." behavior.
- CRUD: `add`/`update`/`remove` keep their existing mutation calls, then re-fetch using the current derived params. After a refresh, if the current page exceeds the last valid page (`total` shrank), the component pushes the clamped page, which re-fetches — the table never shows a page the controls should not claim.
- Controls: a select for read status (All/Read/Unread), a text input for search (debounced before it writes to the URL so typing does not flood browser history), and prev/next buttons with the page indicator. No page-size control; the server default applies.
- Component boundary: `Books.vue` stays the single owner of the view; extract helper modules only if the component becomes unwieldy during execution, keeping the URL as the source of truth.

### Steps

1. Extend the Books spec harness to mount the component with a real vue-router instance so `route.query` and history navigation are real.
2. Derive view params from the route, fetch through `getBooks(params)`, and render rows, the page indicator, and the empty state from `{ books, total }`.
3. Add the controls; write changes back to the URL (debounced search); watch the route to re-fetch.
4. Implement CRUD refreshes via the derived params plus page clamping.
5. Component tests: URL encoding of each control change; deep-link restore; back/forward consistency; fetch params for filter/search/page combinations; CRUD refresh params; page clamp on delete; empty state versus rows.
6. Replace the `client/tests/books.integration.js` stub with the decisive integration test (see Requirement verification): mount the real `Books` component with real vue-router and real axios (no transport mock) against the real Flask app, and assert rendered results for composed views.
7. Update the root README's Books page description (filter, search, pagination, shareable URL).
8. Run the full client suite (`npm test`) and the server suite (pytest); all green.

### Implementation decisions and open questions

- URL as single source of truth — material because it defines user-visible navigation semantics; the alternative (component state mirrored to the URL) creates two sources and breaks the consistency invariant the request requires.
- History semantics: committed control changes and page changes push history entries so back/forward traverses views; keystrokes during search typing are debounced so only the committed value enters history. Recorded here so back/forward behavior is deliberate rather than incidental.
- Default parameters are omitted from the URL (a clean `/books` is the unfiltered first page) — share links stay minimal and the default view is unchanged.
- No page-size selector and no sorting — not requested; excluded.

### Documentation

- Root README Books page section updated in the same change (audience: page users and developers). The API parameter reference is owned by `010-server-query-api.md` and only referenced here. No new documentation pages.

### Task checklist

- [ ] Mount specs with a real router; derive view state from `route.query`.
- [ ] Render table, page indicator, and empty state from `{ books, total }`.
- [ ] Add filter/search/pagination controls that write to the URL.
- [ ] CRUD refreshes use the active params with page clamping.
- [ ] Component tests for URL state, restore, back/forward, consistency, CRUD refresh, and clamping.
- [ ] Decisive integration test through the real Flask server and real transport (replaces the stub).
- [ ] README Books page section updated.
- [ ] Full client and server suites pass.

### Requirement verification

- R1a–R3a and Ra → component tests with the real component and real vue-router (transport mocked): the client state/routing/rendering boundary owns these outcomes; assert URL, fetch params, rows, indicator, and empty state together.
- R4a and R4b → component tests exercising real router history (deep-link mount, then `back()`/`forward()`) asserting table/controls consistency after each navigation.
- R5a → component tests asserting re-fetch params after mutations and the clamp re-fetch when the last page empties.
- R6c → the existing Books spec (empty-state assertion) passes unchanged; CRUD flows asserted through the same component tests.
- Product connection (page params → HTTP routing → server selection → rendered rows) → the decisive integration test from step 6: real `Books` component + real axios + real Flask HTTP in one run, seeded through the real POST endpoint; if an environment cannot spawn the Flask server from vitest, the named manual equivalent is: run `python -m flask --app server.app run --port 5000` from the repository root, then `cd client && npm test`, with the integration test attaching to the already-running server — same traversal, externally hosted.

### Additional implementation verification

- Debounced search versus history: assert that typing produces no history entries and that back lands on the last committed view.
- Default-view compatibility visible on the client: mounting at plain `/books` renders the full unfiltered list with no controls set.
- Port note: `client/src/http.js` hardcodes `localhost:5000` (the production baseURL), so the integration test uses that port; a busy port is an environment risk, not something to route around with a test-only transport override.
- Server state bleed: the in-memory `BOOKS` list persists across integration requests within one server process; seed and clean up through the real endpoints.
