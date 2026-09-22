# Books page discovery controls and URL-backed state

Connect the approved server discovery contract to the Vue Books page so controls, rendered results, browser navigation, sharing, and CRUD refreshes remain synchronized.

Parent Task: tasks/20260920-books-discovery/000-main.md
Depends On: tasks/20260920-books-discovery/010-api-discovery-contract.md

## Requirements checklist

- [ ] The Books page exposes the approved read-status filter, title/author search, and bounded pagination controls.
- [ ] The active controls and current page are initialized from the `/books` query string.
- [ ] User changes update the URL so the current discovery state can be copied and restored.
- [ ] Browser back/forward restores the corresponding discovery state and result set.
- [ ] The table, active controls, page controls, and empty state are derived from the same current result.
- [ ] Add, update, and delete preserve existing CRUD behavior and refresh using the selected discovery state.

## Requirement questions and material decisions

- The parent’s unresolved questions about URL parameter names, history entry behavior, defaults, malformed values, and post-mutation page reconciliation apply here.
- The UI must decide whether search updates on every keystroke or through an explicit submit/debounce interaction. This is user-visible behavior not specified by the request and should be approved before implementation.
- The UI must decide how loading and fetch errors interact with the current table/empty state. No new error policy should be invented under this task without approval.

## Supporting facts

- `Books.vue` currently fetches once on mount and stores only `books`; all mutation methods re-fetch without preserving any query state.
- `getBooks(params = {})` already provides the intended adapter seam for query parameters.
- The router already exposes `/books` through `createWebHistory`, so query state can remain on the existing route.
- Current component coverage mocks the API module and only verifies the empty text; it does not verify the actual route or transport parameter flow.

## Execution plan

Status: Draft

Consume the approved server response through the existing `getBooks` adapter. Establish one normalized discovery-state model for read filter, search text, page, and page size; derive the request params, active-control display, table, empty state, and pagination controls from it; and synchronize it with the `/books` route query. Route updates and route changes must trigger fetches without creating loops, and browser navigation must restore both controls and results.

Refactor CRUD refreshes to issue the same current-state request after each successful mutation. Apply the approved page-reconciliation rule when the mutation changes the available result set. Keep the existing mutation methods and API calls intact unless a change is required to preserve the selected view.

Add component tests for result rendering and empty states, route-level tests for initialization and navigation, and an integration check that observes the actual request params passed through the client adapter. Include mutation tests that verify the selected query is retained on refresh. Use a real router instance where navigation behavior is under test; use transport stubs only at the HTTP boundary.

### Implementation decisions and open questions

- Decision: the route query is the shareable source of truth for the selected discovery state; component-local state is a normalized projection used to render and fetch.
- Decision: reuse the existing `/books` route and `getBooks` adapter rather than adding a second page or transport API.
- Open: history push/replace semantics, search interaction timing, and malformed/out-of-range state behavior need approval.
- Open: the client must follow the server’s approved metadata and page-reconciliation contract from the dependency task.

### Documentation

- Document the supported `/books` query-string fields, their defaults, and how copied URLs restore the page’s controls and results.
- Keep UI guidance concise and colocated with the development documentation for the discovery contract; do not create a separate placeholder guide.

### Task checklist

- [ ] Resolve and record the client-facing URL and interaction contract.
- [ ] Implement normalized route-backed discovery state.
- [ ] Add filter, search, and bounded pagination controls.
- [ ] Keep table, active controls, and empty state synchronized.
- [ ] Preserve discovery state through CRUD refreshes.
- [ ] Add component, router, and transport-boundary coverage.
- [ ] Verify browser navigation and share/restore behavior through the production route.
- [ ] Update the maintained discovery documentation.

### Requirement verification

- Controls and active state: component tests that mount the actual Books component and assert the selected filter, search value, page, table rows, pagination state, and empty text all correspond to one returned result.
- URL initialization and sharing: router/component tests that start at a URL with approved query values and verify both the request params and visible controls/results.
- Browser navigation: a real Vue Router test that changes discovery state, navigates back/forward, and verifies the restored request and rendered state.
- CRUD refreshes: tests invoking the existing add/update/remove methods and asserting the subsequent `getBooks` request retains the selected discovery params and updates the visible result.
- Client transport boundary: verify the production `getBooks` function forwards the normalized params to `http.get`; do not count a test that replaces `getBooks` itself as proof of serialization.