# Books discovery: filtering, search, pagination, and URL state

Plan the end-to-end Books-page discovery capability for larger collections while preserving existing CRUD behavior and the legacy unfiltered API contract.

## Requirements checklist

- [ ] Users can filter books by read status.
- [ ] Users can search by title or author.
- [ ] Users can move through bounded result pages.
- [ ] The current discovery state can be shared and restored through the `/books` URL, including browser back/forward navigation.
- [ ] The table, active controls, pagination controls, and empty state all describe the same selected view.
- [ ] Create, update, and delete continue to work, and their refreshes retain and reconcile the selected discovery view.
- [ ] `GET /books` without discovery parameters remains compatible with the existing response shape and existing callers.

## Requirement questions and material decisions

The following affect the public API or user-visible URL contract and remain unresolved in this draft. They must be answered before approval or execution:

- What query names and values should be public? A possible convention is `q`, `read=all|read|unread`, `page`, and `page_size`, but the current code does not establish these names.
- What default page size and maximum page size define “bounded pages”?
- Should title/author search be case-insensitive substring matching, and should one query match either field (recommended) or require a more specific mode?
- What should happen for malformed or out-of-range `read`, `page`, or page-size values, including a URL that points beyond the final page after a mutation?
- Should changing a control replace the current URL entry or create a browser-history entry? Browser restoration must remain reliable either way.
- When a CRUD mutation changes the current result set, should the page be clamped to the nearest valid page, or should the view return to its first page?

These are recommendations for discussion, not additional requirements. The implementation may resolve local details such as component decomposition and query-string serialization once the public choices are approved.

## Supporting facts

- `server/app.py` currently returns `{"status": "success", "books": [...]}` for `GET /books`, with no query handling.
- `server/query.py` currently only copies the supplied collection.
- `client/src/api/books.js` already passes an optional `params` object to `GET /books`.
- `client/src/components/Books.vue` owns the fetched list and re-fetches after add, update, and delete, but currently has no controls, route-state synchronization, or pagination metadata.
- The only route is `/books`; `vue-router` is already installed and configured with history mode.
- Existing API tests only assert status codes for listing and mutations, and the only Books component test covers the empty state with a mocked API.
- There is no current discovery specification or maintained user/developer page describing the list contract.

## Scope and ownership

This is one end-to-end capability with two independently owned workstreams:

- The server workstream owns selection, pagination metadata, bounded query parsing, and unfiltered compatibility.
- The client workstream owns route-backed state, controls, rendering consistency, browser navigation, and CRUD refresh behavior.

The parent owns the cross-workstream acceptance criteria and the final documentation/testing coordination. It does not authorize implementation until this draft is approved.

## Requirement ownership

- Read-status filtering, title/author search, bounded pagination, selection ordering, pagination metadata, and unfiltered API compatibility are owned by `010-api-discovery-contract.md`.
- The filter/search/page controls, active-control state, table and empty-state consistency, URL sharing/restoration, and browser navigation are owned by `020-books-page-url-state.md`.
- CRUD preservation is shared: the API child protects the existing mutation routes, while the client child owns re-fetching and reconciling the selected discovery view after each mutation.
- The end-to-end connection between the approved API response and the route-backed Books page is jointly verified by both children, with the client child owning the decisive production-path integration check.

## Subtasks

- [ ] [tasks/20260920-books-discovery/010-api-discovery-contract.md](tasks/20260920-books-discovery/010-api-discovery-contract.md)
- [ ] [tasks/20260920-books-discovery/020-books-page-url-state.md](tasks/20260920-books-discovery/020-books-page-url-state.md)

## Execution plan

Status: Draft

First settle the public query and URL decisions above, then implement the server contract and its direct regression evidence. Use that contract from the existing client API adapter, and implement the Books page as a route-backed state machine whose fetches, controls, empty state, pagination, and mutation refreshes all derive from one normalized discovery state. Validate the decisive connections through the production route/API path available in this fixture, with focused tests at each lower boundary and an integration check for the component-to-transport request flow.

The server child is ordered first because the client needs a stable response and metadata contract. The client child then consumes that contract and owns the browser-navigation and CRUD consistency checks. Any change to the public choices above returns this plan to Draft and requires the affected requirements and evidence to be reconsidered.

### Implementation decisions and open questions

- Decision: retain the existing `/books` endpoint and extend it additively; do not create a parallel discovery endpoint.
- Decision: keep mutation endpoints and their existing response behavior in scope only for preserving CRUD and refreshing the selected list; mutation semantics are not otherwise redesigned.
- Decision: keep the existing client API adapter as the transport boundary and pass discovery state through its existing `params` support.
- Open questions: the query names, matching semantics, page defaults/limits, invalid-input behavior, and mutation page-reconciliation behavior listed above require approval.

### Documentation

- Update the maintained development documentation with the approved `GET /books` query parameters, response metadata, compatibility rule, and `/books` URL state contract.
- Keep target-only statements visibly marked as not implemented while this plan remains Draft; do not present the planned behavior as current guidance.

### Task checklist

- [ ] Resolve the public query, pagination, URL, and invalid-input questions.
- [ ] Approve this plan and the two child plans.
- [ ] Complete the API discovery contract child.
- [ ] Complete the Books page URL/state child.
- [ ] Run the requirement-level verification across server and client boundaries.
- [ ] Update maintained documentation and record completion evidence.

### Requirement verification

- Filter, search, page selection, bounds, pagination metadata, and legacy unfiltered compatibility: direct Flask API tests through `tests/test_books_api.py`, with no query-bypassing mock.
- Control state, active indicators, table/empty-state consistency, and pagination rendering: Vue component tests against the real component behavior with transport responses supplied only at the HTTP boundary.
- URL sharing/restoration and browser back/forward: router/component integration coverage through the real `/books` route and its query state.
- CRUD refresh consistency: tests that exercise `add`, `update`, and `remove`, then verify the next request carries the selected discovery state and the rendered result reflects that response.
- Component-to-API parameter serialization: integration coverage of the production `getBooks` adapter and request configuration; if the repository’s test harness cannot host both sides, record the exact unverified boundary rather than treating a mocked `getBooks` call as decisive evidence.
