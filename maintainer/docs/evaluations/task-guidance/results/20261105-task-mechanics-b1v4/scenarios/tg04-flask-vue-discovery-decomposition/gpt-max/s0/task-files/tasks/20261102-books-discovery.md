# Books Collection Discovery

Add practical discovery controls to the Books page while preserving existing CRUD behavior and the unfiltered API contract.

## Requirements checklist

- [ ] Users can filter the collection by read status and search titles or authors.
- [ ] Users can navigate bounded pages of results.
- [ ] The URL represents the current discovery state and restores it on load or browser navigation.
- [ ] The table, active controls, empty state, pagination, and URL remain consistent when discovery state changes.
- [ ] Create, update, and delete operations preserve CRUD behavior and refresh results for the selected discovery view.
- [ ] Existing requests to the Books API without discovery parameters remain compatible and return the unfiltered collection.

## Questions and decisions

- **Design decision:** Keep this as one end-to-end task. Discovery behavior crosses the Flask selection/pagination boundary, client transport, Vue route state, and rendered table; none is independently useful without the others.
- **Open design decision:** Confirm the default and selectable page sizes before implementation; the request specifies bounded pages but not their size.
- **Open design decision:** Confirm whether filtering and pagination are server-side. Recommendation: server-side selection and pagination, with an unfiltered/no-parameter request retaining its current response shape and behavior. This keeps page bounds meaningful for larger collections.

## Supporting details

- **Fact:** `client/src/components/Books.vue` currently loads all rows with `getBooks()` and refreshes the full list after each mutation.
- **Fact:** `client/src/api/books.js` passes optional query parameters to `GET /books`, so client transport already has a parameter path.
- **Fact:** `server/app.py` currently returns `{"status": "success", "books": BOOKS}` for `GET /books`; `server/query.py` currently returns a list without selection logic.
- **Fact:** Existing component coverage only checks the empty state. `client/tests/books.integration.js` explicitly records that production transport integration coverage is absent.
- **Fact:** Existing Flask tests check successful unfiltered listing and basic mutations, but do not assert the response contract or discovery behavior.
- **Fact:** The repository has no `docs/index.md`; `docs/development/index.md` notes there is no book-discovery specification.

## Implementation plan
Status: Draft

Implement discovery as one production-path capability. The Vue page owns the interactive controls and renders the selected result page; Vue Router query state is the durable source for filter, search, and page navigation, including restoration through direct links and browser back/forward. The client API forwards those state parameters to Flask. Flask applies read-status and case-insensitive title/author search before pagination, and returns enough paging metadata for bounded navigation. Keep the existing unfiltered `GET /books` behavior and response compatible; do not alter create, update, or delete semantics.

Reset to the first page when search or read-status filters change. If a CRUD refresh leaves the current page beyond the new result bounds, reconcile the page and URL to a valid page and reload that view. Show an empty-result state that distinguishes a filtered search with no matches from an unfiltered empty collection, while keeping controls and URL in sync. The precise empty-state wording and page-size choices remain local implementation details after the open page-size decision is answered.

### Implementation decisions and open questions

Resolve the two design questions above before implementation: page-size choices, and server-side versus client-side selection. The recommended direction is server-side selection/pagination to support larger collections; retain parameter-free API compatibility either way. Do not change CRUD endpoint contracts or invent unrelated validation/error behavior.

The primary risk is mismatch between URL query state, API selection, and visible results, including stale/out-of-range pages after mutations. Verify through a real Vue Router + client transport + Flask API path using representative records; component tests alone or direct route tests alone are insufficient. Keep changes focused so rollback is limited to the discovery state/API additions, leaving existing CRUD operations intact.

### Documentation

Update the existing maintained developer documentation at `docs/development/index.md` if it remains the appropriate owned location after implementation. Document only the verified query/URL behavior and the preserved no-parameter API behavior; do not create a placeholder specification or user guide solely for this task.

### Task checklist

- [ ] Decide page-size behavior and server/client selection.
- [ ] Add Flask discovery selection and bounded pagination without breaking parameter-free listing.
- [ ] Connect Vue route query state and client requests to the discovery controls and table.
- [ ] Keep empty state, browser navigation, and CRUD refreshes consistent with the selected view.
- [ ] Add focused API and component coverage plus a decisive real-path integration check.
- [ ] Update owned documentation and run the relevant client and Flask tests.

### Requirement verification

Verify filtering, search, bounded paging, and URL-restored view together through a decisive integration check traversing the actual Vue component, Vue Router, production client transport, and Flask endpoint. This check must include browser query navigation and confirm the visible table corresponds to API-selected results. It does not replace focused tests for query selection/pagination and component control/empty-state behavior.

Verify CRUD preservation by creating, updating, and deleting through the existing public API behavior while discovery parameters are active, then assert the rendered selected view and valid page state refresh. Verify backward compatibility by asserting a parameter-free `GET /books` retains the existing success envelope and returns all books. Verify docs against implemented behavior after execution; no documentation changes are part of this planning-only handoff.

### Additional implementation verification

Run focused Flask tests and the client test suite after the integration check. Confirm mutation refresh handles deletion of the last item on a page without leaving pagination or the URL out of bounds.