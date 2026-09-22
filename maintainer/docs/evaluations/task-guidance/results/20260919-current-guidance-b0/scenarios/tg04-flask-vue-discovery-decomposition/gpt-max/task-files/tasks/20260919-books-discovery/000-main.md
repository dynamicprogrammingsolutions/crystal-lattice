# Make the Books discovery view scalable and shareable

Plan the Books-page discovery feature so a larger collection can be filtered, searched, paged, and shared through the URL while retaining the existing CRUD and unfiltered API contracts.

## Requirements checklist

- [ ] The Books page lets users filter by read status, search by title or author, and move through bounded pages.
- [ ] The selected discovery state is reflected consistently by the controls, active-control indicators, table rows, pagination bounds, and empty state.
- [ ] The current discovery state is shareable and restorable through the `/books` URL, including direct visits, reloads, and browser back/forward navigation.
- [ ] Add, update, and delete operations preserve the selected discovery view and refresh the table, controls, pagination, empty state, and URL consistently.
- [ ] Existing CRUD behavior remains available, and an unfiltered `GET /books` remains compatible with its current full-list response contract.

## Scope and workstreams

The work is split into independently owned boundaries:

1. Define the optional server-side discovery contract and data-selection behavior.
2. Build the client-side discovery state, transport parameters, controls, table, pagination, and empty-state rendering.
3. Synchronize that state with the router/history and make CRUD refreshes use the same state.
4. Add boundary-focused evidence and update the maintained development documentation after the behavior exists.

The task does not include sorting, bulk actions, authentication, persistence changes, or implementation in this planning pass.

## Open requirement questions

These public-behavior choices are not specified by the request and should be resolved before approval for execution:

- What query parameter names and response metadata should define the API/URL contract? A likely shape is a read-status value, a search term, a one-based page, and a fixed page size with total/page metadata, but the names and page size are not yet approved.
- Should title/author search be case-insensitive substring matching, and should one term be matched against either field? That is the recommended user-facing behavior, but it is still a semantic choice.
- When a filter or search changes, should the page reset to the first page? Resetting is the usual way to avoid an empty out-of-range view, but it changes navigation behavior.
- How should invalid or out-of-range page values be handled: normalize to a valid page, return a client error, or show an empty result? The choice affects both the API and URL canonicalization.
- What history granularity is desired for search input: every committed change, a debounced change, or a submit action? Filter and page changes can naturally create browser-history entries, but typing behavior needs an explicit policy.

## Research and supporting facts

- `server/app.py` currently serves `GET` and `POST` from the same `/books` route and returns `{"status": "success", "books": BOOKS}` for a GET with no query parameters.
- `server/query.py` currently exposes only a pass-through `list_books(books)` helper; no filtering or pagination exists.
- `client/src/api/books.js` already accepts an optional `params` object in `getBooks`, so the transport boundary can carry discovery parameters without changing the mutation functions.
- `client/src/components/Books.vue` currently keeps only a `books` array, loads the complete collection on mount, renders a minimal table or `No books found.`, and reloads the complete collection after each mutation.
- `client/src/router.js` declares `/books` with browser history but currently has no query-state parsing or navigation synchronization.
- Existing server coverage checks only basic GET and mutation status codes. The only Books component test covers the empty state with a mocked empty response; there is no router or production-transport integration coverage.
- `docs/development/index.md` currently states that no book-discovery specification exists. No feature documentation should be added until the supported behavior is implemented and verified.

## Execution plan

Status: Draft

Treat the approved API/query contract as the shared seam between the Flask and Vue work. Keep a canonical client discovery state rather than deriving separate values for the controls, request, table, and URL. Every state transition should pass through the same load-and-normalize path, including initial URL restoration, browser navigation, control changes, and CRUD refreshes.

The server work will add optional discovery selection while preserving the no-query behavior: an unfiltered `GET /books` continues to return the complete collection with the existing status and `books` fields, and POST/PUT/DELETE routes retain their current endpoints and mutation semantics. Filtered or explicitly paged requests will return the bounded result and the metadata required to render reliable page controls, subject to the unresolved contract decisions above.

The client work will make the discovery state explicit, send the selected state through `getBooks`, and render controls that remain visible and truthful when a query has no matches. The table will render only the selected page, pagination controls will be disabled or hidden at the appropriate bounds, and loading/empty results will not silently fall back to an unfiltered collection. Mutation methods will call the same state-aware loader after the existing API operation.

The router work will parse the `/books` query on entry and navigation, serialize canonical state changes back to the URL, and distinguish programmatic synchronization from user navigation so back/forward restores state without loops or stale results. If a mutation makes the current page invalid, the approved normalization policy will update both the displayed view and the URL.

Evidence will be added at the API boundary for selection, pagination, unfiltered compatibility, and mutation regressions; at the component/router boundary for controls, rendering, URL restoration, browser navigation, and CRUD refreshes; and at the nearest realistic integration boundary for transport/query wiring. Once verified, the maintained development documentation will describe the supported discovery query and URL behavior.

### Implementation decisions and open questions

- Decision: keep `/books` as the public route and use its query string for discovery state; do not introduce a second discovery route.
- Decision: preserve the existing no-query full-list GET contract and existing CRUD endpoints as compatibility constraints.
- Decision: use one canonical discovery state as the source for request parameters, controls, rendered results, and URL synchronization.
- Open: approve the parameter names, page size, response metadata, search semantics, page-reset behavior, invalid-page policy, and history granularity listed above before execution.
- Recommendation: use case-insensitive matching against either title or author, a fixed default page size, one-based pages, and reset to page one when the filter/search changes. Record the final choices in the task before changing status to Approved.

### Documentation

- No documentation changes are made during this planning-only task.
- After implementation and verification, update `docs/development/index.md` or create a specifically owned feature page only if the final behavior needs more space. Document the supported read-status values, search semantics, pagination/query parameters, URL restoration, and mutation-refresh behavior.
- Do not describe target behavior as current guidance before the implementation is complete.

### Task checklist

- [ ] `tasks/20260919-books-discovery/010-api-discovery-contract.md` — define the Flask query/data-selection contract and compatibility evidence.
- [ ] `tasks/20260919-books-discovery/020-client-discovery-state.md` — define the Vue state, controls, rendering, pagination, and transport integration.
- [ ] `tasks/20260919-books-discovery/030-url-history-and-refresh.md` — define URL/history synchronization and state-preserving CRUD refreshes.
- [ ] `tasks/20260919-books-discovery/040-evidence-and-documentation.md` — define cross-boundary tests and the maintained documentation update.
- [ ] Resolve the open requirement questions and update the affected plan sections before execution approval.
- [ ] Keep this parent task in Draft until the requirements and public query contract are approved.

### Requirement verification

- Filter, search, and bounded-page behavior: verify through Flask API tests using the real route and data-selection helper, then through a Books component/integration test that sends the selected parameters and renders the returned page and metadata.
- Consistency of controls, active state, table, pagination, and empty state: verify with component tests covering an initial result, a filtered result, a no-match result, and a page-boundary result.
- URL sharing and restoration: verify with a router-backed test that mounts `/books` with query parameters, reloads/enters the route, changes state, and exercises back/forward navigation while asserting both request parameters and rendered controls.
- CRUD refresh consistency: verify through tests that add, update, and delete retain the canonical discovery state, reload through the selected query, and reconcile an invalidated page according to the approved policy.
- Existing CRUD and unfiltered API compatibility: verify the existing mutation route tests plus a no-query GET assertion that the full collection and current response fields remain available.

### Additional implementation verification

- Check for request/watch loops between component state and router query state.
- Check that a late response from an obsolete discovery request cannot overwrite a newer URL-selected view.
- Check that query serialization omits defaults or normalizes them consistently so equivalent views do not create needless history churn.