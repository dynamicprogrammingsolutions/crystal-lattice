# Books Collection Discovery

Plan filtering, search, bounded pagination, and URL-restorable discovery state for the Books page while preserving current CRUD operations and unfiltered API compatibility.

## Requirements checklist

- [ ] Users can filter books by read status and search by title or author.
- [ ] Users can navigate bounded pages of the matching collection.
- [ ] The current filter, search, and page state is represented in the URL and restored when opening or navigating browser history.
- [ ] The displayed table, active controls, empty state, and results after CRUD mutations all reflect the selected discovery state.
- [ ] Existing create, update, and delete behavior remains available.
- [ ] Requests to the books API without discovery parameters retain the existing response contract.

## Scope

One cohesive user-facing capability spanning the Books page, URL state, client API adapter, Flask route, and server-side selection. No separate subtasks: these layers do not provide independently acceptable outcomes for this feature.

## Questions and decisions

- **Design decision — discovery API contract:** The existing API accepts no list parameters. Proposed: accept `search`, `read`, `page`, and `per_page` query parameters; apply case-insensitive substring matching across title and author, read-status filtering, then pagination. Preserve the existing response shape for requests without discovery parameters; return pagination metadata with queried results. The exact response metadata fields and invalid-parameter behavior remain to be decided during implementation.
- **Recommendation — URL contract:** Use the same discovery parameter names in the `/books` URL query, omit default/empty values where practical, and treat browser back/forward as state changes that reload the matching results. This keeps shared URLs directly reproducible by the page and API.
- **Open design choice — page size:** The request requires bounded pages but does not specify a page size or whether users can change it. Prefer a fixed default page size initially unless implementation findings show a user-selectable size is needed; do not add a page-size control without approval.

## Supporting details

- `client/src/components/Books.vue` currently fetches all books at mount and after each mutation, then renders only a table or “No books found.” It has no discovery controls or route-state handling.
- `client/src/api/books.js` already accepts optional parameters in `getBooks(params = {})`.
- `server/query.py` currently returns the entire collection, and `server/app.py` returns `status` and `books` for `GET /books`.
- Current API tests cover basic listing and mutations; the Books component test covers the empty state. `client/tests/books.integration.js` explicitly records that production transport integration coverage does not exist.
- `README.md` is the only current package-level guidance; `docs/development/index.md` states that no book-discovery specification exists. Any new supported-behavior guidance should live with the relevant package rather than creating a placeholder documentation structure.

## Implementation plan
Status: Draft

Implement discovery as one data flow: the route query is the restorable source of selection state, the Books page renders controls and results from that state, and the client adapter sends equivalent parameters to Flask. Server-side selection filters before paginating so a larger collection does not need to be transferred in full. The API retains the current unfiltered `GET /books` behavior and CRUD endpoints. After a mutation, refetch using the current discovery state; if the current page no longer has results because of the mutation, reconcile the URL/page with the valid bounded result rather than showing stale rows. Keep filtered and empty results distinct in the interface, while ensuring controls continue to display the active selection.

Execution order:

1. Confirm the list-query and URL contract, including defaults and pagination metadata, before implementation because it is a public API and shareable URL.
2. Implement and test server selection and pagination while retaining the existing no-parameter response contract. This establishes the result shape the client will consume.
3. Connect the client API and Books page to URL-backed controls, results, page bounds, loading/refetch behavior, and mutation refreshes.
4. Add end-to-end boundary evidence that exercises the real page, client transport, Flask route, and selection together; retain focused tests for selection and rendering.
5. Update maintained user guidance only once behavior is implemented and verified.

The backend contract precedes page wiring because the page needs authoritative filtered totals and page bounds. The server and client can each reach a safe stopping point before integration; do not expose the feature as complete until the combined page/API path passes. The main risk is divergence between URL state, server selection, and post-mutation paging, which can produce stale or misleading results. The way back is to remove the discovery parameters and client controls while leaving the existing unfiltered list and CRUD endpoints intact; keep compatibility tests around that path.

### Implementation decisions and open questions

- Confirm query parameter names, search matching semantics, read-status values, default page size, pagination metadata, and invalid or out-of-range parameter behavior before coding.
- Confirm whether page size is fixed or user-selectable. The current recommendation is fixed, with no new page-size control.
- Preserve the current no-parameter response and mutations; do not change CRUD endpoint contracts as part of discovery.

### Documentation

- Update `README.md` or another existing package-owned user guide with verified filter, search, paging, and shareable-URL behavior. Do not create a standalone discovery specification or placeholder docs page solely for this change.

### Task checklist

- [ ] Agree on the discovery query, URL, and pagination contract.
- [ ] Add server-side filtering and bounded pagination with compatibility coverage.
- [ ] Add URL-synchronized controls and paged results to the Books page.
- [ ] Preserve selected-view consistency through browser navigation and CRUD refreshes.
- [ ] Add decisive real page-to-Flask integration evidence and focused regression tests.
- [ ] Update maintained usage documentation.

### Requirement verification

- Requirements 1–4: run an integration check through the real Vue Books page and Flask API that selects read status, searches title/author, moves across bounded pages, reloads a shared URL, traverses browser back/forward, and verifies the table, controls, empty state, and refreshed results after create/update/delete. Component tests with mocked API data alone are not decisive for this connection.
- Requirement 5: exercise create, update, and delete through the existing UI/API path and verify the refreshed selected view remains coherent.
- Requirement 6: test an unfiltered `GET /books` request against the existing `status`/`books` response contract and verify its list semantics are unchanged.

### Additional implementation verification

- Test server filtering, ordering of operations (filter before pagination), totals, and page bounds with focused API/query tests.
- Test URL parsing and serialization, controls, empty-result rendering, and page-bound behavior with focused component tests.
- Run the client and server test suites after focused tests; these routine checks supplement, but do not replace, the real page-to-API integration evidence.