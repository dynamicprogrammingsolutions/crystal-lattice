# Books discovery for larger collections

Plan and coordinate server-backed discovery for the Books page: read-status
filtering, title/author search, bounded pagination, URL persistence, and
consistent refresh behavior across the table, controls, empty state, browser
navigation, and existing CRUD operations.

## Requirements checklist

- [ ] The Books page lets users filter by read status, search by title or
  author, and move through bounded pages of results.
- [ ] The complete discovery state is shareable and restorable through the
  `/books` URL, including direct loads and browser back/forward navigation.
- [ ] The table, active controls, empty state, page bounds, and CRUD refreshes
  all represent the same selected discovery view.
- [ ] Existing add, update, and delete behavior remains available, and each
  mutation refreshes the selected view rather than silently reverting to an
  unrelated list.
- [ ] `GET /books` without discovery parameters remains compatible with the
  existing response and returns the complete unfiltered collection; existing
  mutation routes remain compatible.

## Scope and workstreams

The work is split by independently owned contracts rather than by every
technical layer:

Both children include their focused tests and the documentation they own.
The parent retains the cross-boundary acceptance check and the final
requirement evidence.

Out of scope: sorting, bulk actions, changes to book persistence, new
mutation operations, authentication, and a redesign of the existing CRUD
forms or table beyond what discovery consistency requires.

## Subtasks

- [ ] `tasks/20260920-books-discovery/010-api-query-contract.md` — own
  server-side selection, pagination boundaries, response metadata, and
  unfiltered API compatibility.
- [ ] `tasks/20260920-books-discovery/020-books-page-discovery-state.md` —
  own client transport mapping, Vue state/rendering, router query
  synchronization, browser navigation, and CRUD refresh behavior.

## Unresolved requirement questions and decisions

These questions affect public API or user-visible URL contracts and must be
resolved before execution is approved:

1. What query parameter names and values are public for status, search, page,
   and page size? Recommendation: use stable, descriptive names shared by the
   API and URL, with an explicit all/read/unread status vocabulary.
2. What page size and pagination response shape should be public?
   Recommendation: keep `status` and `books` at the existing response
   boundary, add explicit pagination metadata, and use a documented default
   page size.
3. Should search be a case-insensitive substring match over either title or
   author, and how should blank/whitespace-only search be treated?
   Recommendation: normalize it as a case-insensitive substring search and
   treat blank input as no search.
4. When a mutation makes the current page empty or invalid, should the client
   clamp to the nearest valid page before refreshing or refresh the current
   page and then correct it? Recommendation: clamp using the server's
   pagination metadata so the URL and rendered view converge on a valid page.

Implementation decisions already made for planning:

- Selection and pagination belong on the server so the page does not fetch the
  entire collection as it grows.
- The URL is the shareable source of discovery state; the component must
  initialize from it and react to router history changes.
- There is no separate testing or documentation child: evidence and maintained
  guidance stay with the owner of the behavior they verify.

## Research and supporting facts

- `server/app.py` currently returns every item from `BOOKS` for `GET /books`
  and exposes unchanged `POST /books`, `PUT /books/<book_id>`, and
  `DELETE /books/<book_id>` routes.
- `server/query.py:list_books` currently only copies the input list, so there
  is no existing selection or pagination implementation to preserve.
- `client/src/api/books.js` already accepts an optional `params` object in
  `getBooks`, but the Books component does not pass one.
- `client/src/components/Books.vue` stores only a full `books` array, renders
  a table or `No books found.`, and refetches without any selected-view state
  after mutations.
- `client/src/router.js` has a `/books` route with history mode but no query
  state handling.
- `tests/test_books_api.py` covers only status codes for the unfiltered list
  and CRUD routes. `client/tests/Books.spec.js` covers only the empty state;
  `client/tests/books.integration.js` explicitly has no production transport
  integration coverage.
- `docs/development/index.md` currently says that no book-discovery
  specification exists, so the maintained developer guidance will need a
  focused update after the behavior is implemented.

## Execution plan

Status: Draft

1. Resolve the public query vocabulary, default page size, metadata shape,
   search normalization, and invalid-page behavior.
2. Execute the API child to implement and test server-side filtering/search
   and bounded pagination while retaining the unfiltered response and CRUD
   routes.
3. Execute the client child against that contract to add URL-backed
   discovery state, controls, rendering, browser navigation handling, and
   mutation refreshes.
4. Run the parent cross-boundary checks: a real Flask HTTP request for the
   query contract, the mounted Books page with a real router for URL/history
   behavior, and the existing CRUD paths.
5. Update the maintained developer documentation with the settled API query
   contract and URL state behavior.

### Implementation decisions and open questions

The four questions above remain open. No implementation should begin until
the public contract is approved; changing it after the API and router work
starts would require reopening both children.

### Documentation

After implementation, update the smallest maintained page under
`docs/development/`—preferably the existing index if the contract remains
compact, otherwise one focused Books-discovery page linked from it. Document
the supported query parameters, response metadata, URL state, default
behavior, and the fact that an unparameterized `GET /books` remains
compatible. This planning change does not create or claim current product
guidance.

### Task checklist

- [ ] Resolve and record the public discovery contract.
- [ ] Approve this plan and both child plans.
- [ ] Complete `tasks/20260920-books-discovery/010-api-query-contract.md`.
- [ ] Complete `tasks/20260920-books-discovery/020-books-page-discovery-state.md`.
- [ ] Run the parent cross-boundary verification and existing CRUD regression
  checks.
- [ ] Publish the maintained developer documentation.
- [ ] Append immutable completion notes with evidence and any deferred scope.

### Requirement verification

- Requirements 1 and 5: server tests exercise the real Flask `GET /books`
  boundary for each filter/search combination, pagination boundaries, and the
  no-parameter response; existing mutation tests continue to pass.
- Requirements 1 and 3: mounted Books-page tests exercise active controls,
  table contents, filtered empty state, disabled/enabled page navigation, and
  the selected query passed through the production API module.
- Requirements 2 and 3: a router-backed client integration test starts at a
  query-bearing `/books` URL, verifies restored controls and results, changes
  discovery state, and verifies browser back/forward restoration.
- Requirement 4: component/integration coverage performs add, update, and
  delete through the existing production methods while a non-default
  discovery view is selected, then verifies that the refreshed results and
  URL remain coherent, including the last-item/page-bound case.

### Additional implementation verification

- Run the existing Python API suite and the client Vitest suite after focused
  coverage is added.
- Confirm no request path used by the existing unfiltered client call requires
  new parameters or a new response envelope.