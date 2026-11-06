# Books Discovery

Add URL-backed discovery controls to the Books page while preserving CRUD and the existing unfiltered API behavior.

## Requirements checklist

- [ ] Users can filter books by read status.
- [ ] Users can search books by title or author.
- [ ] Users can move through bounded pages of results.
- [ ] The URL represents the current discovery state and restores it when opened or revisited.
- [ ] The rendered table, active controls, empty state, browser navigation, and CRUD refreshes remain consistent with the selected discovery view.
- [ ] Existing CRUD behavior and unfiltered `GET /books` API compatibility are preserved.

## Unresolved questions

- Should read status offer `All`, `Read`, and `Unread`, and what matching rules should search use (for example, case-insensitive substring matching)?
- What page size should be used, and what should happen when the URL specifies an invalid or now-out-of-range page?
- Should paged API responses add total/page metadata, and what response shape should be used while leaving parameter-free responses unchanged?
- What URL parameter names and default-state serialization should be supported as the shareable interface?
- After a mutation changes result membership or page count, should the current filters/search be retained and the page clamped to the new last page, or reset to the first page?

## Supporting facts

- The Vue Books component currently fetches the full collection on mount and after each mutation. It renders only title and author and has a single empty state.
- `client/src/api/books.js` already accepts optional query parameters in `getBooks`, while `server/query.py` currently returns all input books and `GET /books` returns a `books` array.
- The Flask route supports list and create on `/books`; update and delete use `/books/<book_id>`.
- Existing client tests mock the API; `client/tests/books.integration.js` explicitly records that production-transport integration coverage does not exist.
- No `docs/index.md`, product discovery specification, client/server README, or nested `AGENTS.md` was found. The root README is a minimal description of the app; `docs/development/index.md` says no book-discovery specification exists.

## Execution plan
Status: Draft

### Design

Keep the Books page as the owner of the discovery experience. Treat the URL query as the durable, shareable view state; initialize from it, react to browser back/forward navigation, and write control changes through Vue Router rather than maintaining a disconnected local copy. The table, controls, empty-state messaging, and mutation refreshes should all derive from the same normalized state and returned result set.

Extend the existing `GET /books` query path to select results using the approved filter, search, and pagination contract. Keep requests with no discovery parameters backward-compatible: they continue to return the existing success envelope with the complete `books` array. The client API wrapper already supports query parameters; preserve its existing mutation calls and refresh them using the active view. Do not settle URL naming, match semantics, page size, invalid-page behavior, or post-mutation page handling until the open questions are answered.

The capability is one cohesive result across Vue state/rendering, client transport, Flask routing, and data selection, so keep it in one task rather than splitting by technical layer. Add focused unit/component and API tests as supporting evidence, and one decisive real-path integration test in `client/tests/books.discovery.integration.js` that mounts the Books page with the router and production HTTP client against the Flask API, covering URL restore/navigation, discovery results, and a CRUD refresh together. Existing tests do not prove that connection.

### Ordered work

1. Resolve the discovery, URL, pagination, and mutation-refresh behavior questions.
2. Implement server-side filtering and bounded paging while preserving the unfiltered response contract.
3. Synchronize controls and results with route query state, including initial load and browser navigation.
4. Preserve mutations and refresh the currently selected view consistently after CRUD changes.
5. Add focused UI/API coverage and the real-component-to-Flask integration check.
6. Update maintained user documentation with the supported Books discovery behavior.

### Implementation decisions and open questions

The single end-to-end task boundary is selected because no layer has an independent user-facing acceptance or ownership boundary here. The query parameter contract, search matching rules, page size, invalid page semantics, paged API metadata/shape, and post-mutation page behavior remain unresolved requirements/design questions listed above; execution must wait for the user's answers before encoding these as behavior. Do not add new CRUD semantics or alter unfiltered API compatibility.

### Documentation

Update the root `README.md` (the only current user-facing product introduction) to describe the supported discovery controls and URL behavior after those behaviors are implemented. Do not add a placeholder specification or documentation page merely to create a new structure.

### Task checklist

- [ ] Resolve open behavior questions with the user.
- [ ] Implement filtering and pagination without breaking unfiltered API responses.
- [ ] Implement URL-synchronized Books state and consistent CRUD refresh.
- [ ] Add focused tests and the decisive real-path integration test.
- [ ] Update user-facing documentation.

### Requirement verification

- [ ] Read-status filtering, title/author search, and bounded paging: verify server selection and parameter handling through focused Flask API tests, including unfiltered `GET /books` retaining its existing envelope and complete list.
- [ ] URL share/restore and browser navigation: verify `client/tests/books.discovery.integration.js` loads the view from a URL through the real Vue Router and back/forward navigation updates controls and results.
- [ ] Table, controls, empty state, navigation, and CRUD consistency: decisive check is a real Books component + Vue Router + production HTTP client against a running Flask API, with exact invocation and setup recorded when implementing the integration harness. Exercise a filtered/paged URL, navigation, empty results, and a mutation followed by refresh through that path.
- [ ] CRUD and unfiltered API compatibility: preserve existing client mutation behavior and verify create/update/delete through API tests plus the decisive integration path; verify parameter-free list behavior via the Flask API test.

### Additional implementation verification

No known requirement depends on a non-product test shortcut. The integration harness must cross the actual router, HTTP client, Flask route, and result selection; mocked component tests alone are not decisive.