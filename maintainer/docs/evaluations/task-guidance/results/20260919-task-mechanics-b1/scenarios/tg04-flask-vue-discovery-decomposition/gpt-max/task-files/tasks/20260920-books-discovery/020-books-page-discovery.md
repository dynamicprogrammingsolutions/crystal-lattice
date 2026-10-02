# Books page URL-backed discovery state

Connect the Vue Books page to the server discovery contract and make the
controls, table, empty state, pagination, browser navigation, and CRUD
refreshes share one URL-backed view state. This is a planned subtask;
implementation is **Not implemented**.

Parent Task: tasks/20260920-books-discovery/000-main.md

Depends On: tasks/20260920-books-discovery/010-server-discovery-query.md

## Requirements checklist

- [ ] The page exposes read-status and title/author search controls whose
      active values are visible and whose combination is sent to the API.
- [ ] The page renders bounded pagination from server metadata and keeps page
      controls within the approved range.
- [ ] The `/books` query string is the shareable/restorable source for the
      complete discovery state, and browser back/forward restores controls,
      results, pagination, and empty state.
- [ ] The table and empty state always represent the active discovery view;
      stale rows and stale active-control values are not retained.
- [ ] Add, update, and delete refresh the current discovery request, preserve
      the selected view, and apply the approved page-transition behavior.
- [ ] Existing client CRUD calls remain compatible with the existing API
      functions.
- [ ] Component, router, and client transport coverage proves the behavior
      through the production Books page path.

## Unresolved requirement questions

This subtask inherits the parent decisions about URL parameter names,
canonical omission of defaults, page reset/clamping, search semantics, and
post-CRUD page transitions. It must also confirm whether controls update the
URL on each input/change or on an explicit submit; the URL must remain the
single shareable state either way.

## Research and supporting facts

- `client/src/components/Books.vue` currently owns only `books` and calls
  `getBooks()` on mount and after each mutation. It has no controls, loading
  state, pagination metadata, or route access.
- `client/src/api/books.js:getBooks(params = {})` already passes an Axios
  `params` object to `/books`, so transport changes can remain localized.
- `client/src/router.js` uses Vue Router history mode with a `/books` route.
  Query parameters are available without adding a new route.
- Current client coverage only mounts the component with mocked API methods
  and checks `No books found.`; `client/tests/books.integration.js` has no
  production transport coverage.

## Execution plan

Status: Draft

1. Record the approved URL serialization and canonicalization rules, then
   define one normalized discovery-state model containing filter, search,
   page, page size (if exposed), result metadata, and current rows.
2. Initialize that model from `route.query`, serialize control/page changes
   through the existing router, and watch route changes so direct links and
   browser back/forward reload the same view. Prevent route/component
   synchronization loops and discard or supersede stale responses according
   to the chosen request strategy.
3. Update `getBooks` calls to send the normalized server parameters. Render
   the active filter/search values, current table, no-match empty state, and
   bounded page controls from one response/state model.
4. Update add, edit, and remove flows to refetch with the current discovery
   parameters. Apply the approved reset/clamp rule when the mutation changes
   the number of matching pages, and update the URL whenever that rule changes
   the page.
5. Add focused component tests for controls and empty/table states, router
   tests for direct restoration and back/forward, and a transport test that
   verifies query serialization. Exercise CRUD refresh on a non-default view
   so the test does not pass by accidentally falling back to an unfiltered
   request.

The output of this subtask is the user-visible discovery experience. It
depends on the server subtask's final parameter and metadata contract and
does not change unrelated routes or API mutation semantics.

### Implementation decisions and open questions

- Router query state should be the canonical shareable state; local state may
  cache response data but must not become a second independent filter model.
- The page must retain the selected filter/search while refreshing after CRUD;
  the exact handling of an emptied page remains a parent-level decision.
- The existing `getBooks(params)` seam is sufficient unless the approved
  response requires a narrowly scoped client transport adjustment.

### Documentation

- During implementation, document the user-facing URL parameters and the
  behavior of active controls, empty results, browser navigation, and
  mutation refreshes in the smallest maintained Books/developer guide.
- Do not publish this target behavior as current documentation during the
  planning-only pass.

### Task checklist

- [ ] Resolve and record the approved URL and page-transition contract in the
      parent task.
- [ ] Wait for the approved server subtask contract.
- [ ] Mark this subtask Approved before implementation.
- [ ] Implement URL-backed state, controls, pagination, rendering, and CRUD
      refreshes.
- [ ] Add and run component, router/navigation, and transport evidence.
- [ ] Record documentation and verification results.

### Requirement verification

- **Controls and selected view:** mount the real Books component with an API
  response containing metadata, change status/search controls, and assert the
  generated request, active values, and table rows all describe the same
  view.
- **Pagination:** navigate within the rendered bounds and assert the route,
  request parameters, rows, and boundary control states change together.
- **URL restore/navigation:** start at a deep-link query, assert it restores
  the controls and result, then create multiple route states and verify
  browser back/forward restores each complete state.
- **Empty and CRUD refresh:** assert a no-match response renders the selected
  filter/search context without stale rows; perform CRUD on a filtered page
  and assert every refresh uses the current query and follows the approved
  page-transition rule.