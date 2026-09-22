# Books discovery, filtering, pagination, and URL state

Plan the cross-layer work that makes the Books page practical for a larger
collection while preserving the existing CRUD behavior and unfiltered API
contract.

## Requirements checklist

- [ ] The Books page lets users select a read-status view that includes all
      books, read books, and unread books.
- [ ] The Books page lets users search by title or author.
- [ ] The result set is divided into bounded pages with controls that expose
      the current page and available navigation, without allowing navigation
      outside the valid range.
- [ ] The current status filter, search text, and page are represented in the
      `/books` URL so the state can be shared and restored when the route is
      opened again.
- [ ] The table, active controls, and empty state all reflect the selected
      discovery state, including filtered searches that produce no matches.
- [ ] Browser back/forward navigation restores the corresponding discovery
      state and result set.
- [ ] Add, update, and delete preserve the current discovery state when they
      refresh the list; deletion or other changes that invalidate the current
      page leave the user on a valid page in the same selected view.
- [ ] The API continues to support the existing unfiltered `GET /books`
      response shape and existing POST, PUT, and DELETE behavior.
- [ ] Filtered and paginated API responses provide enough selection and
      pagination information for the client to render the current view without
      reimplementing server-side selection.
- [ ] Automated evidence covers the server selection contract, client
      rendering/state transitions, URL and browser navigation, and CRUD
      refresh regressions.

## Scope and workstreams

The work is split into three owned results:

1. `010-server-discovery-contract.md` defines and verifies server-side
   filtering, search, pagination, response metadata, and compatibility.
2. `020-client-discovery-state.md` consumes that contract and owns the Books
   page controls, URL synchronization, navigation, rendering, and stateful
   CRUD refreshes.
3. `030-integration-and-regression-evidence.md` proves the public path across
   the client/API boundary and records the maintained documentation update
   without creating a new documentation area unnecessarily.

## Requirement questions

These questions affect the public API or user-visible behavior and must be
resolved before the requirements are marked complete:

- What URL/query parameter names and values should represent status, search,
  page, and page size? A compact recommendation is
  `status=all|read|unread`, `q=<text>`, `page=<one-based integer>`, with a
  server-owned fixed page size unless a page-size control is explicitly
  desired.
- Should title/author search be case-insensitive substring matching, and
  should whitespace be trimmed before matching?
- Is the page size fixed for the feature, or should users choose it? If it is
  fixed, what value is the supported contract?
- When a shared URL contains malformed or out-of-range values, should the
  server/client normalize them to defaults, clamp the page, or reject the
  request? The plan assumes normalization/clamping is preferred, pending
  approval.
- Should changing filters/search/page create browser history entries, or
  should some high-frequency changes (especially typing search text) use
  replacement state? The plan assumes deliberate discovery changes are
  navigable and rapid text updates may be debounced/replaced, pending
  approval.

## Supporting facts

- `client/src/components/Books.vue` currently stores only an in-memory
  `books` array, renders no controls, and reloads `GET /books` after each
  mutation.
- `client/src/api/books.js` already accepts an optional `params` object for
  `getBooks`, so the client transport has a narrow extension point.
- `server/app.py` currently returns `{"status": "success", "books": BOOKS}`
  for both unfiltered GET and POST responses, and its mutation routes retain
  the existing CRUD paths.
- `server/query.py:list_books` is currently a passthrough and is the natural
  owner for reusable selection/pagination logic.
- Existing server tests assert only GET/CRUD status codes; the only client
  component test asserts the unfiltered empty state, and
  `client/tests/books.integration.js` explicitly has no transport coverage.
- There is no current book-discovery specification or user guide. Any
  documentation change should extend an existing maintained location, most
  likely the concise project README or development documentation, rather than
  creating placeholder structure.

## Execution plan

Status: Draft

After the requirement questions are answered and this plan is approved,
execute the work in dependency order:

1. Establish the server query contract in
   `010-server-discovery-contract.md`, including stable defaults for omitted
   parameters and an explicit compatibility path for unfiltered GET.
2. Implement and test the server-owned filtering, title/author search, and
   bounded pagination metadata. Keep POST/PUT/DELETE routes and their
   response behavior intact unless the approved contract requires a narrowly
   documented adjustment.
3. Extend the client API call and Books component around one normalized
   discovery-state model. Make URL parsing/serialization the route boundary,
   then make controls, table, empty state, and page navigation derive from
   that state and the API response.
4. Route browser back/forward through the same state application path as
   initial URL restoration. Ensure CRUD refreshes re-request the selected
   query and reconcile an invalidated page without dropping the other
   selections.
5. Add focused component and server tests, then run the integration/regression
   evidence described in `030-integration-and-regression-evidence.md`.
6. Update only maintained documentation that actually describes the Books
   endpoint or page behavior, and record any approved deviations or blocked
   evidence in the task notes when execution begins.

### Implementation decisions and open questions

The public query vocabulary, matching semantics, page size, malformed-URL
handling, and history-update policy remain open as listed above. The
implementation should keep selection/pagination in the server query boundary,
URL serialization at the router/page boundary, and CRUD refreshes on the same
loader used for initial and navigated discovery state.

No code, tests, or documentation have been changed by this planning task.

### Documentation

During execution, inspect the existing README and development documentation
for a maintained audience that needs the supported query or URL behavior. If
one exists, update it in the same reviewed change as the implementation. Do
not create a new guide or placeholder page solely to document this feature.

### Task checklist

- [ ] Resolve the requirement questions and update this Draft plan.
- [ ] Obtain approval to execute the plan; then change status to `Approved`.
- [ ] Complete [server discovery contract](tasks/20260919-books-discovery/010-server-discovery-contract.md).
- [ ] Complete [client discovery state](tasks/20260919-books-discovery/020-client-discovery-state.md).
- [ ] Complete [integration and regression evidence](tasks/20260919-books-discovery/030-integration-and-regression-evidence.md).
- [ ] Keep requirement evidence and any implementation notes current during execution.
- [ ] Append immutable completion notes only after all approved requirements are evidenced.

### Requirement verification

At completion, map evidence to the smallest public boundary that proves each
requirement:

- Server tests must exercise real `GET /books` requests for status filtering,
  title/author search, pagination boundaries, metadata, default behavior, and
  unfiltered compatibility.
- Client component tests must mount the real Books component with controlled
  API responses and verify active controls, table rows, empty state, page
  transitions, URL restoration, and CRUD reload parameters.
- Browser-history tests must use the router boundary and prove back/forward
  restores state rather than only testing a local parser.
- An integration test must cross the client API module and HTTP adapter path
  for at least the representative filtered/paginated request and mutation
  refresh, without replacing the behavior with a test-only shortcut.
- Existing CRUD status/response tests must continue to pass; add assertions
  only where the approved contract changes or preserves response details.

### Additional implementation verification

- Verify that omitted query parameters preserve the existing unfiltered
  response shape and that mutations do not accidentally inherit list-query
  parameters.
- Verify URL updates do not create request loops or stale responses when the
  user changes controls quickly.
- Verify an empty page after deletion is normalized to a valid page while
  retaining status and search selections.