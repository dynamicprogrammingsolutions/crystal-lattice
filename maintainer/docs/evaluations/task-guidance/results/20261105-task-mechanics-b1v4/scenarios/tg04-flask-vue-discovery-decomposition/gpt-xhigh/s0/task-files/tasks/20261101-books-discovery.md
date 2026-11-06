# Books Discovery State

Plan filtering, search, pagination, and shareable discovery state for the Books page without implementing the feature.

## Requirements checklist

- [ ] Users can filter books by read status and search by title or author; filters can be combined.
- [ ] The table, active controls, and empty state reflect the current discovery selection.
- [ ] Users can move through bounded result pages, with the selected page kept valid as results change.
- [ ] The URL shares and restores the current filter, search, and page; browser back and forward restore the matching view.
- [ ] Existing create, update, and delete behavior remains available, and successful mutations refresh the selected view.
- [ ] An unparameterized `GET /books` retains its current full-list behavior and response contract.

## Questions and decisions

- **Search matching:** Should search be exact or partial, and case-sensitive or insensitive? Recommendation: trim the term and use a case-insensitive substring match against either title or author.
- **Page size:** What fixed page size should the Books view use? Recommendation: 20 rows.
- **URL and API contract:** Are `read`, `q`, `page`, and `page_size` acceptable query keys? Recommendation: omit default filter/search/page values from the share URL, and return pagination metadata only for parameterized API requests while keeping the no-query response unchanged.
- **History behavior:** How should search edits affect browser history? Recommendation: submit search explicitly; committed search, filter, and page changes create navigable history entries, with back/forward restoring each committed state.
- **Browser-level verification:** Is adding a browser-capable test runner and minimal page harness acceptable to verify actual Back/Forward behavior? Recommendation: yes; current tests have no browser runner or app entry point, and mocked API tests cannot prove the requested UI/API/URL connection.

## Supporting details

- `client/src/components/Books.vue` currently loads the full collection and refetches it after each mutation. It renders only a table or a single empty message.
- `client/src/api/books.js` already allows `getBooks` query parameters to pass through Axios.
- `server/app.py` currently returns `{status, books}` for `GET /books`; `server/query.py` only copies the supplied collection.
- The client router uses `createWebHistory` at `/books`, but the repo has no application entry point or browser test runner.
- `client/tests/Books.spec.js` mocks the API and only tests the empty state. `client/tests/books.integration.js` is a placeholder; it does not exercise production transport.
- The Flask API test fixture uses the in-memory `BOOKS` list and does not reset it between tests.
- `README.md` is the only maintained user-facing product documentation and currently describes only loading and mutating books.

## Implementation plan

Status: Draft

### Design

Keep this as one end-to-end task: filtering, pagination, transport, URL state, and refresh behavior form one user-visible capability and do not deliver an independently useful layer result.

Treat the `/books` route query as the selected discovery state. The Vue page initializes controls from it, requests matching server-filtered and paginated results, and reflects each response in the table, active controls, page navigation, and empty state. Flask performs selection and pagination so the page does not need to download the entire collection to navigate a large result set. The exact URL/API keys, search semantics, and page size remain subject to the decisions above.

Keep the existing no-query API response and full-list behavior unchanged. Query-aware requests return only the selected page and enough count/page metadata for bounded navigation. After a successful CRUD operation, refetch using the current discovery state; if a deletion makes the selected page unavailable, move to a valid page before displaying the refreshed result. Browser history navigation must update both the route-derived controls and rendered data.

### Risks and rollback

- Query parsing, result counts, or page correction can cause API and UI state to diverge. Cover the connection with a real full-path check, not only isolated mocks.
- Changing default API behavior could break existing clients. Keep no-query requests on the existing full-list contract and add query behavior separately.
- A browser runner adds test infrastructure to a very small fixture. Keep it limited to the path required for route history and the real UI/API connection; if rejected, return with a revised verification plan rather than substituting mocked transport tests.
- The feature is additive. If the new query path regresses, removing query handling and route controls restores the existing unfiltered page and API behavior.

### Order logic

Resolve the visible search, pagination, URL, and test-runner decisions before implementation. Then extend and test the API query contract while preserving no-query behavior; the Vue page depends on that response contract. Next connect route state, controls, rendering, and CRUD refreshes. Finally exercise the production UI/transport/API path and update the user documentation. The API milestone can be reviewed independently, but the feature is not complete until the full path and browser-history behavior pass together.

### Implementation decisions and open questions

- No independent subtasks: one task owns the UI, URL, API selection, compatibility, and end-to-end evidence.
- The listed recommendations are proposals, not approved requirements. Resolve the outstanding questions before implementation, particularly the browser test infrastructure decision.
- Do not change CRUD endpoint behavior or the no-query API contract as part of discovery support.

### Documentation

Update `README.md` with the supported read-status filter, title/author search, bounded pagination, URL sharing/restoration, and preserved CRUD behavior once implemented. Keep the documentation change with the feature; do not create a new documentation hierarchy for this capability.

### Task checklist

- [ ] Confirm discovery semantics, URL/API query contract, page size, history behavior, and browser verification approach.
- [ ] Add optional server-side filtering and pagination while preserving unparameterized `GET /books`.
- [ ] Synchronize page controls and results with route query state, including browser history and CRUD refreshes.
- [ ] Add API regression tests and a real browser integration test across the Vue page, Axios transport, Flask route, and browser history.
- [ ] Update `README.md` with the implemented user-facing behavior.

### Requirement verification

- Requirements 1–4: A browser-level integration test must load the actual Books page and router, use the real Axios client against Flask, and verify combined selection, active controls, visible rows, empty results, bounded navigation, share/restore, and back/forward. It must not mock the API or replace browser history with memory history. This check does not cover deployment infrastructure or browser engines beyond the runner used.
- Requirement 5: In the same full-path test, perform create, update, and delete through the page's existing mutation methods, then verify the refreshed selection and valid page. This does not introduce or validate new CRUD endpoint semantics.
- Requirement 6: Flask API tests must assert that `GET /books` without query parameters still returns the full list using the existing `{status, books}` contract. Parameterized API tests must cover filtering, pagination metadata, and page boundaries; these direct route tests do not replace the full-path integration test.

### Additional implementation verification

- Run the focused client and server test suites after the decisive integration and API tests pass.