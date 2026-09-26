# Preserve the selected Books filter across CRUD refreshes

Plan the client-side fix so the Books page keeps its All, Read, or Unread
selection active and uses that selection whenever a successful add, edit, or
delete refreshes the collection.

## Requirements checklist

- [ ] Keep the selected All, Read, or Unread filter visibly active after adding
      a book.
- [ ] Keep the selected filter visibly active after editing a book.
- [ ] Keep the selected filter visibly active after deleting a book.
- [ ] Reapply the selected filter to each CRUD collection refresh so the
      displayed books remain filtered.
- [ ] Preserve the existing Flask API response shape.
- [ ] Preserve unfiltered collection behavior when All is selected or no
      filter is supplied.

## Scope

In scope: the Vue Books component's selected-filter state and the refresh path
used after add, update, and delete operations, plus focused regression and
contract tests.

Out of scope: changing Flask routes, changing the API response envelope,
adding new filter values, changing CRUD semantics, or adding a new
documentation section.

## Requirement questions and decisions

Unresolved requirement questions: none identified.

Decisions:

- Treat this as one end-to-end client behavior task because the filter state,
  collection refresh, and visible active state are owned by `Books.vue`.
- Keep the existing `getBooks(filter = "all")` API wrapper contract and pass the
  component's current `selectedFilter` into every post-mutation refresh.
- Consolidate collection loading behind a component refresh method so filter
  selection and CRUD operations cannot diverge again. The existing filter
  selection path should use the same method where practical.
- Do not modify the Flask API. Its current `GET /books` behavior already
  supports `read=true`/`read=false` and an unfiltered request while returning
  the same `{status, books}` shape.

## Research and supporting facts

- `client/src/components/Books.vue` initializes `selectedFilter` to `"all"`,
  passes the selected value to `getBooks` from `selectFilter`, and binds
  `aria-pressed` to that state.
- The component's `add`, `update`, and `remove` methods currently call
  `getBooks()` without an argument, which invokes the wrapper's default
  `"all"` filter.
- `client/src/api/books.js` maps `"read"` to `{ read: true }`, `"unread"` to
  `{ read: false }`, and `"all"` to no query parameters.
- `server/app.py` returns `jsonify({"status": "success", "books": ...})` for
  both filtered and unfiltered `GET /books` requests.
- `client/tests/Books.spec.js` currently covers only the empty state and mocks
  the Books API module. `tests/test_books_api.py` currently checks route
  success statuses but not the response envelope or filter behavior.
- `client/package.json` exposes `npm test` as `vitest run`; the Python project
  has Flask and the existing server tests but no additional test runner
  configuration in the repository.

## Execution plan

Status: Draft

### Design and data flow

`Books.vue` remains the owner of the selected filter. A single collection
refresh method will read `selectedFilter`, call `getBooks(selectedFilter)`,
and assign `response.data.books`. `selectFilter` will update
`selectedFilter` before invoking that refresh. After `addBook`, `updateBook`,
or `deleteBook` succeeds, the mutation method will invoke the same refresh
method without resetting the selection. The existing `aria-pressed` binding
will therefore continue to expose the selected value throughout each refresh,
including for `all`.

The API wrapper and Flask route remain compatibility boundaries: the wrapper
continues translating the three UI values into the current query convention,
and the server continues returning the current response envelope. No
server-side filtering or response-shape change is part of this task.

### Ordered implementation and verification work

1. Update `Books.vue` to centralize filtered collection loading and route the
   filter-selection and post-CRUD refreshes through it. Ensure the current
   selected value is passed unchanged for `"all"`, `"read"`, and `"unread"`.
2. Extend `client/tests/Books.spec.js` with rendered-component regression
   coverage that:
   - selects Read and Unread and verifies the corresponding button remains
     `aria-pressed="true"`;
   - invokes add, update, and delete while each filter is selected;
   - verifies each refresh requests the selected filter and renders the
     returned books, rather than falling back to the unfiltered list.
   The test should exercise the public component interaction path and keep API
   responses in the existing `{ data: { books } }` client shape.
3. Add focused API-wrapper coverage, if needed by the existing client test
   setup, for the mapping of All/read/unread to the current Axios query
   parameters. This protects the transport boundary without changing it.
4. Strengthen `tests/test_books_api.py` at the Flask route boundary to verify
   that an unfiltered `GET /books` returns the existing status/books envelope
   and full collection, while the existing filtered query behavior returns the
   matching subset with that same envelope.
5. Run the client Vitest suite and the Python API test suite. Record any
   environment or dependency block rather than weakening the checks.
6. Perform one decisive production-path check with the real Vue component,
   client API wrapper, Flask route, and seeded data together: start the Flask
   app on its configured port and the client test/development host as
   available, select Read and then Unread, perform each CRUD action, and
   confirm the selected button remains active and the displayed collection
   stays filtered. Use the exact host/start commands supported by the
   repository environment when execution begins; do not add a test-only
   shortcut.

### Implementation decisions and open questions

- The implementation decision is to preserve filter state in the component and
  reuse one refresh path, rather than adding filter parameters to mutation
  endpoints or changing server responses.
- No material requirement question is open. The execution agent should resolve
  only local implementation details such as method naming and test fixture
  setup.
- If the real production-path check cannot be run because this fixture has no
  client dev/start script, retain the automated component and Flask boundary
  evidence and report the manual check as blocked; do not change scope to
  create infrastructure.

### Documentation

No maintained user or developer documentation currently describes Books
filtering; `docs/development/index.md` explicitly says no book-discovery
specification exists. Therefore no documentation file is planned for this
small behavior correction. If implementation reveals an existing maintained
Books guide, update that guide in the same change to state that the selected
filter remains applied after CRUD refreshes.

### Task checklist

- [ ] Update `client/src/components/Books.vue` to reuse the selected filter
      during all collection refreshes.
- [ ] Add component regression coverage for visible selection and filtered
      results after add, update, and delete.
- [ ] Verify the client API filter mapping and preserve the All/no-query path.
- [ ] Add Flask route assertions for the unchanged response envelope and
      unfiltered behavior.
- [ ] Run the client and server test suites.
- [ ] Complete or explicitly report the real production-path check.
- [ ] Update this task with implementation and completion notes after execution;
      this draft does not authorize implementation.

### Requirement verification

- Selected filter remains visibly active after add, update, and delete:
  the rendered `Books.vue` regression test selects each non-default filter,
  performs the corresponding mutation, and asserts the selected button's
  `aria-pressed` state plus the displayed returned books.
- CRUD refreshes reapply the selected filter:
  the same component test asserts `getBooks` receives the current filter for
  each mutation, and the decisive real-component/API/Flask check confirms the
  resulting filtered collection through the production data flow.
- Existing API response shape is preserved:
  `tests/test_books_api.py` asserts the unfiltered and filtered route JSON
  objects retain the `status` and `books` keys and expected values.
- Existing unfiltered behavior is preserved:
  the Flask route test asserts `GET /books` without a query returns the full
  collection, while the client API mapping test asserts All produces no
  filter query.

### Additional implementation verification

- Run `npm test` from `client/` and the repository's configured Python test
  command after implementation.
- Inspect the final diff to confirm no Flask endpoint, response envelope, or
  mutation API contract changed.