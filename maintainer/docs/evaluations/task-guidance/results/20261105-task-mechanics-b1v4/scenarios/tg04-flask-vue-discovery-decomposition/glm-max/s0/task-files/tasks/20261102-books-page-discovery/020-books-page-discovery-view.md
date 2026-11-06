# Books page: discovery view with URL-shared state

Rebuild the Books page around a URL-driven view state: read-status filter,
title/author search, and bounded pagination, with the table, active controls,
empty state, browser navigation, and CRUD refreshes all consistent with the
selected view. This subtask owns the end-to-end product connection and holds
the decisive checks for the parent capability.

Parent Task: tasks/20261102-books-page-discovery/000-main.md

Depends On: tasks/20261102-books-page-discovery/010-server-books-selection.md
(the view needs the selection parameters and page metadata).

## Requirements checklist

- [ ] Controls set the selected view: a read-status filter (all / read /
      unread), a search input matching title or author text, and pagination
      controls showing the current position with prev/next disabled at the
      bounds.
- [ ] The table shows exactly the books of the current page for the selected
      view as returned by the API.
- [ ] The empty state reflects the selected view: a filter/search selection
      with no matches shows a no-matches message; an empty unfiltered
      collection keeps "No books found.".
- [ ] The selected view is encoded in the `/books` query (`read`, `q`, `page`,
      with defaults omitted) so a pasted URL restores the same view on load.
- [ ] User-initiated control changes create history entries; browser
      Back/Forward move between previous discovery states and the table and
      controls follow.
- [ ] After add/update/delete the table refreshes using the current selection;
      a delete that empties the current page steps back one page; a book added
      while the active filter/search excludes it may remain invisible
      (consistent with the view).
- [ ] Existing CRUD behavior is preserved: the add/update/remove API calls and
      the refresh-after-mutation flow still work; API module changes are
      limited to passing selection parameters and reading page metadata.
- [ ] Component tests cover: restoring the view from URL parameters on mount,
      control changes updating the route and refetching with selection
      parameters, table and empty-state rendering, pagination bounds, and CRUD
      refresh with the current selection including the page step-back.
- [ ] An integration test over real HTTP — the client API module against a
      running Flask server — proves selection parameters and page metadata
      cross the transport boundary, replacing the placeholder in
      `client/tests/books.integration.js`.
- [ ] Component and integration evidence runs cleanly via the client test
      script.
- [ ] `docs/development/book-discovery.md` gains the user-facing discovery
      behavior section (controls, empty states, URL sharing, CRUD
      consistency) matching delivered behavior, in the same change.

## Supporting details

- `client/src/components/Books.vue` currently loads all books on mount and
  re-fetches all books with no parameters after each mutation; the empty
  state is "No books found.".
- `client/src/api/books.js:getBooks(params)` already forwards query
  parameters; no structural transport change is needed.
- `client/src/router.js` uses `createWebHistory` with a single `/books` route;
  query parameters are unused so far, and vue-router 4 is already a
  dependency.
- `client/tests/Books.spec.js` mocks the API module and asserts the empty
  state; it mounts components, but the harness has no DOM environment
  configured (no vitest config, no jsdom/happy-dom dependency) and no
  lockfile — setup is part of this subtask's plan.
- `client/tests/books.integration.js` is a placeholder with no coverage.
- Fixture constraints: `client/src/http.js` targets the absolute
  `http://localhost:5000`, the Flask app sets no CORS headers, and
  `package.json` has only a `test` script — so a browser-level check needs
  dev-serving decisions that are out of scope unless the parent's open
  question is approved.

## Implementation plan

Status: Draft

### Approach

`Books.vue` holds one view state — `{ read, q, page }` plus a constant page
size (10) — derived from the `/books` route query, which is the single source
of truth. Mount parses and normalizes `route.query` (invalid values reset to
defaults) and fetches `getBooks({ read, q, page, per_page })`. Control changes
push the normalized query with `router.push`; a watcher on the resolved query
performs the fetch, so Back/Forward traversal flows through the same path as
control changes. The table, active control states, pagination position, and
empty state all render from that state plus the `total` metadata. CRUD methods
keep their existing mutation calls and then refetch through the same
selection-driven path; when a delete empties the current page while
`total > 0` and `page > 1`, the view steps back one page via the route.
Normalization uses `router.replace` so it does not spam history.

### Steps

1. Complete the minimal test harness: install client dependencies, add a DOM
   environment (jsdom) with a vitest config, and confirm the existing
   `Books.spec.js` still passes.
2. Introduce the view state and the route-query-driven fetch; render the
   table from the page items and keep the unfiltered empty state.
3. Add the read-status, search, and pagination controls with active states,
   bounds, and empty-state messaging for filtered selections.
4. Add URL sync (push on user changes, replace for normalization) and
   Back/Forward support through the route watcher.
5. Make CRUD refreshes selection-consistent with the step-back rule.
6. Replace `client/tests/books.integration.js` with a real-HTTP integration
   test that starts the Flask server and exercises selection parameters and
   page metadata through the client API module.
7. Add the user-facing section to `docs/development/book-discovery.md`.
8. Run the client suite and the server suite; perform the named manual check
   or record it as blocked (see verification).

### Risks and the way back

- URL/router edge cases (invalid or partial query values) could crash or
  desync the view; client-side normalization is specified and tested.
- The browser-level Back/Forward check is blocked by the fixture's CORS and
  dev-serving gap; the evidence split below keeps automated coverage at the
  router and transport boundaries and names the manual step explicitly.
- Harness setup may uncover tooling quirks (jsdom versions, axios in node);
  the harness is maintained test infrastructure verified through the real
  component tests.
- No persisted data and no server changes in this subtask; rollback is
  reverting this subtask's commit, which also reverts its documentation
  section.

### Implementation decisions and open questions

Mirrors the parent plan (pending overall approval): URL carries `read`, `q`,
`page` only with page size as a client constant; push for user-initiated
changes and replace for normalization; client-side normalization resets
invalid URL values to defaults; step-back rule for emptied pages. No
subtask-local open questions; the parent's dev-serving open question gates
only the optional browser check.

### Documentation

Owned by this subtask: the user-facing discovery behavior section of
`docs/development/book-discovery.md`, written in the same reviewed change as
the view code. Audience: maintainers of the Books page and users of its
documented behavior.

### Task checklist

- [ ] Harness completed and existing spec passing.
- [ ] View state, fetch wiring, table, controls, pagination, and empty states
      implemented per requirements.
- [ ] URL sync and Back/Forward working through the route-driven fetch.
- [ ] CRUD refreshes selection-consistent with step-back.
- [ ] Component tests and real-HTTP integration test added; both suites pass.
- [ ] Documentation section added.

### Requirement verification

Component tests run through a real vue-router instance (mocked API module) —
decisive for URL restore on mount, control-to-route-to-fetch flow, pagination
bounds, empty-state consistency, and CRUD refresh with the current selection;
the mocked transport is acceptable there because the transport boundary is
covered separately. The real-HTTP integration test (client API module against
a running Flask server) is decisive for selection parameters and page metadata
crossing the production transport. For the full browser traversal
(rendering plus Back/Forward in a real browser), the named check is manual:
start the API (`flask --app server.app run`) and a dev server, open
`/books?read=false&q=dune&page=1`, confirm table/controls/empty-state
consistency, then use Back/Forward; record the result or the blocking reason
(the CORS/dev-serving gap) in implementation notes.

Deliberately not covered: visual styling, cross-origin browser transport, and
any server behavior (owned by subtask 010).
