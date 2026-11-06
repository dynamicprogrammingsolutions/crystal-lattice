# Books Collection Discovery

Plan the Books page improvements that let users find books in larger collections and preserve the current discovery view.

## Requirements checklist

- [ ] Users can filter books by read status and search by title or author.
- [ ] Users can navigate bounded pages of results.
- [ ] The URL represents the current discovery state so it can be shared and restored.
- [ ] The table, active controls, empty state, browser navigation, and CRUD refreshes stay consistent with the selected view.
- [ ] Existing CRUD behavior and unfiltered API compatibility are preserved.

## Unresolved questions

- What page size should the interface use, and should users be able to change it?
- Which URL parameter names and read-status values should form the shareable URL contract?
- Should search apply immediately or through an explicit submit/debounce interaction?

## Supporting details

- **Fact:** The Books view is `client/src/components/Books.vue`; it currently fetches the unfiltered collection on mount and after each CRUD operation.
- **Fact:** `client/src/api/books.js` passes optional query parameters to `GET /books`, while `server/app.py` currently ignores query parameters and returns the complete collection.
- **Fact:** The API response is an object with `status` and `books`; the initial fixture includes a boolean `read` field.
- **Fact:** Existing client tests are in `client/tests/Books.spec.js`; no server tests or discovery integration tests were located during planning.
- **Decision:** Keep this as one end-to-end task. UI state, URL synchronization, query transport, API selection, and CRUD refresh behavior jointly deliver the requested discovery experience; splitting by technical layer would separate dependent work without an independent acceptance result.
- **Recommendation:** Implement collection selection in the API and treat the URL as the durable UI state; preserve the existing response envelope and behavior when no discovery parameters are supplied. Confirm the public query contract before implementation.

## Execution plan
Status: Draft

Implement discovery as one connected path. The Books view owns the active search, read-status filter, and bounded-page state, synchronizes that state with the Vue Router query, and uses it to request and render the current result set. The Flask list route applies the supplied selection and pagination while retaining the current full-list response for an unfiltered request. Keep the existing `status`/`books` response envelope and CRUD endpoints. Refreshes after mutations must request the selected view again and reconcile an out-of-range page when collection size changes, rather than silently displaying results from another view.

Do not finalize parameter spellings, page-size behavior, or search interaction until the questions above are answered. URL state restoration must also cover invalid or missing query values consistently; do not invent a new error contract before agreeing on the public URL contract.

1. Confirm page-size, URL-query, and search-interaction decisions.
2. Define API query parsing and selection while preserving unfiltered behavior.
3. Connect Books controls and visible results to route query state and API results.
4. Keep route navigation, empty states, and post-CRUD refreshes view-consistent.
5. Add focused unit and integration evidence, including the real UI-to-API discovery path.
6. Update maintained user/developer documentation for the supported URL and API behavior.

### Implementation decisions and open questions

- The public query contract and page-size interaction remain unresolved above; obtain answers before approving implementation.
- The recommendation is API-side search/filter/pagination, since the endpoint already accepts optional query parameters and large collections are the stated use case. The unfiltered request must remain compatible.
- Search timing (immediate, debounced, or submitted) remains a user-visible decision and is not assumed.

### Documentation

- Update the root `README.md` with supported Books discovery and shareable URL behavior once implemented.
- Document any public API query contract in the same maintained location; no API-specific documentation page currently exists, so prefer the existing README unless implementation reveals a clear, maintained API documentation owner.

### Task checklist

- [ ] Resolve the discovery URL, page-size, and search interaction decisions.
- [ ] Implement the API query path and maintain unfiltered API compatibility.
- [ ] Implement URL-backed UI controls, paging, and consistent CRUD refreshes.
- [ ] Add focused tests and update maintained documentation.

### Requirement verification

- Requirements 1–3: exercise read-status selection, title/author matching, bounded-page navigation, and URL restoration through the Books page using the real router and API path.
- Requirement 4: through the same connected path, verify active controls, displayed rows and empty state after route changes and browser back/forward; create, update, and delete while filtered or paginated and verify the selected view remains correct.
- Requirement 5: verify existing CRUD flows and a request to `GET /books` without discovery parameters retain the existing response envelope and complete-list behavior.
- No existing test located during planning proves these cross-layer behaviors; add or extend integration coverage rather than relying only on mocked component tests and direct route tests.

### Additional implementation verification

- Run the focused client tests and server tests after implementation; also run an end-to-end integration check through the production route, HTTP client, and Flask API boundary.