# Client discovery view (controls, bounded pagination, view-consistent CRUD refresh)

Build the Books page browsing experience on the 010 API contract: read-status
filter, title/author search, bounded pagination controls, view-consistent
table and empty states, and CRUD refreshes that honor the current view. Owns
the first real client↔server transport integration evidence, which the
existing mocked-transport component test cannot provide.

Parent Task: tasks/20260926-books-page-discovery/000-main.md

Depends On: tasks/20260926-books-page-discovery/010-server-discovery-api.md

## Requirements checklist

- [ ] C1 — The page renders active controls reflecting the current view:
      read-status filter (all/read/unread), search input, and bounded
      pagination (prev/next disabled at bounds, page indicator from response
      metadata).
- [ ] C2 — Control changes refetch via the API with the view's params; the
      table, controls, and empty state render the response rows and metadata.
- [ ] C3 — The empty state is consistent with the selected view:
      "No books found." for an empty collection; a distinct no-matches state
      when filter/search match nothing (parent D7; a clear-filters affordance
      only if approved there).
- [ ] C4 — Add/update/delete refresh using the current view params; when the
      refreshed page is out of range, the view resolves to a valid page before
      rendering (R7).
- [ ] C5 — Existing CRUD behavior through the page keeps working; the existing
      component regression (empty state, CRUD methods) is preserved and
      extended.
- [ ] C6 — Evidence: component tests at the view boundary (transport mocked)
      plus the first integration coverage of the real client transport against
      the real Flask server for filter/search/page through the production
      path.

## Execution plan

Status: Draft

Design: `Books.vue` owns a single reactive view object `{ read, q, page }` and
one `refresh()` path that calls `getBooks(viewParams)` and stores rows plus
pagination metadata (`page`, `page_size`, `total`, `total_pages`). All CRUD
methods call `refresh()` instead of paramless `getBooks()`. The single-owner
view object is deliberate: 030 binds this same object to the route query
without reworking state. `client/src/api/books.js` needs no contract change
(it already forwards params); param mapping lives in one place. Search applies
debounced (~300 ms, parent D6); page changes apply immediately. Out-of-range
clamping uses the response metadata. Component tests mock the API module and
cover view-boundary logic; the integration file drives the real stack.

Steps:

1. Baseline: npm install; run the existing vitest suite. If the component
   spec cannot run for lack of a DOM environment, add the minimal
   environment config (e.g. jsdom) and confirm the existing spec passes
   before extending it; record what the baseline required.
2. Implement view state, `refresh()`, and the params mapping in `Books.vue`
   against the 010 contract (always-explicit params per D3).
3. Render controls and pagination from response metadata with bounds; apply
   D6 debounce and D7 empty states as approved.
4. Rework the CRUD methods to refresh with the view; implement out-of-range
   clamping using metadata.
5. Component tests (extend `client/tests/Books.spec.js`) per C6: controls →
   params mapping, filter/search application, pagination bounds and
   indicator, no-matches vs. no-books states, CRUD refresh carries view
   params, clamp behavior, and the existing regressions.
6. Integration: populate `client/tests/books.integration.js` — start the real
   Flask server on port 5000 (matching `client/src/http.js`), drive the
   mounted page over real transport/routing/selection, assert
   filtered/searched/paginated rows, and tear the server process down. The
   harness must stay runnable via `npm test`.

### Implementation decisions and open questions

- Parent decisions D1–D8 govern (contract, always-explicit params, debounce,
  empty states). Child-local, reversible choices: control markup and test
  selectors, the debounce constant, and clamping to the last valid page.
- The integration harness (spawning Flask from vitest) is maintained test
  infrastructure per the testing policy and is verified through this suite as
  its real consumer.

### Documentation

- Add the page-behavior section (controls, pagination, empty states) to
  `docs/development/index.md` and a README sentence for filter/search/
  pagination, in the same change as the behavior, per the parent plan's
  `### Documentation` section.

### Task checklist

- [ ] Component test baseline established (existing spec runs; environment
      changes recorded).
- [ ] View state + `refresh()` + params mapping implemented per the 010
      contract.
- [ ] Controls, bounded pagination, and empty states rendered per approved
      D6/D7.
- [ ] CRUD refresh honors the view; out-of-range clamp implemented.
- [ ] Component tests extended per C6; suite passes.
- [ ] `client/tests/books.integration.js` populated; runs cleanly via
      `npm test`.
- [ ] Docs and README updated.

### Requirement verification

- C1/C2 → decisive: component tests asserting the controls reflect the view
  state and emit the mapped API params, with bounds and indicator from
  metadata.
- C3 → decisive: component tests covering both empty states.
- C4 → decisive: component tests asserting refresh uses the current view
  params and clamps on out-of-range metadata.
- C5 → decisive: retained/extended CRUD component regressions.
- C6 integration → decisive for the R1–R3 end-to-end chain: real axios →
  real Flask routing/selection → rendered rows. Transport and server are not
  mocked in this check; mocked-transport component tests are supporting
  evidence for view logic only.

### Additional implementation verification

- Run the component and integration suites together once to confirm the
  shared harness and the mocked-transport suite do not interfere (shared
  state, server port).