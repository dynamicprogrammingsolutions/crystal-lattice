# Books discovery for larger collections

Plan the cross-layer work that makes the Books page usable with a larger
collection while preserving existing CRUD behavior and callers of the
unfiltered API.

## Requirements checklist

- [ ] The Books page lets users filter books by read status.
- [ ] The Books page searches by title or author.
- [ ] The Books page lets users move through bounded result pages.
- [ ] The current discovery state can be shared and restored through the URL,
  including after a reload or a direct visit to a copied URL.
- [ ] The table reflects the selected discovery view, including its current
  page of results.
- [ ] The filter and search controls visibly reflect the selected discovery
  state.
- [ ] The empty state accurately describes the selected view when it has no
  matching books and updates after navigation or a mutation without showing
  stale rows.
- [ ] Browser back and forward navigation restore the corresponding discovery
  state and results.
- [ ] Add, update, and delete refreshes retain the active discovery state and
  leave the table, controls, pagination, and empty state consistent with the
  refreshed collection.
- [ ] Existing CRUD operations and endpoint behavior remain usable.
- [ ] A request to the books API without discovery parameters remains
  compatible with existing callers and returns the unfiltered collection in
  its current response shape.

## Unresolved requirement questions and decisions

- **Question — discovery parameter vocabulary:** What public query keys and
  values should represent read status, text search, and page selection? The
  working recommendation is `read`, `q`, and `page`, with an omitted `read`
  meaning all books and a one-based `page`.
- **Question — search semantics:** Should title/author matching be
  case-insensitive substring matching, and should surrounding whitespace be
  trimmed? The working recommendation is trimmed, case-insensitive matching
  against either field, combined with the read-status filter.
- **Question — page size:** Should the page size be fixed by the API or
  user-selectable? The working recommendation is a fixed bounded page size so
  the URL only represents discovery choices named in the request.
- **Question — response metadata:** How should filtered requests expose total
  results and page bounds? The working recommendation is to add pagination
  metadata for parameterized requests while leaving the no-parameter response
  shape unchanged.
- **Question — canonical URL and mutations:** Should default values be omitted
  from the URL, and should a mutation that removes the last item on a page
  clamp to the final valid page or return to page one? The working
  recommendation is to omit defaults, reset to page one when search/filter
  criteria change, and clamp a now-invalid page to the final valid page.

These questions must be resolved before execution because their answers affect
the public API, shareable URLs, and visible navigation behavior.

## Research and supporting facts

- `server/app.py` currently returns the entire `BOOKS` list for every GET
  request to `/books`; it does not inspect query parameters. The no-parameter
  response is `{"status": "success", "books": ...}`.
- `server/query.py` currently contains only `list_books(books)`, which returns
  a copy of its input and is an available ownership point for selection
  logic.
- `client/src/api/books.js` already accepts an optional `params` object for
  `getBooks`, but `Books.vue` only calls it without parameters.
- `client/src/components/Books.vue` stores only the loaded books, renders a
  table or `No books found.`, and refreshes after add, update, and delete
  without preserving a discovery context.
- `client/src/router.js` currently defines only the `/books` route and uses
  Vue Router history mode; no query-state behavior is configured or tested.
- Existing server coverage checks only the GET status and basic mutation
  status codes. The Books component has one empty-state test, and the client
  integration file contains no production transport coverage.
- `docs/development/index.md` states that no book-discovery specification
  exists. No implementation or documentation changes are authorized by this
  planning request.

## Scope and workstreams

The work is intentionally split at independently owned boundaries:

1. Define and test optional server-side selection and pagination while keeping
   the no-parameter API contract intact.
2. Connect the selection contract to URL query state, including initialization,
   canonical updates, and browser navigation.
3. Integrate the state into the Books view so rendering and CRUD refreshes use
   one selected view.

Cross-boundary verification and documentation remain part of the main task
because they validate the complete user-visible behavior rather than
constituting another independently useful product layer.

## Subtasks

- [ ] [tasks/books-discovery/010-api-discovery-contract.md](010-api-discovery-contract.md)
  — define server-side filtering, search, pagination, and compatibility
  coverage.
- [ ] [tasks/books-discovery/020-url-state-transport.md](020-url-state-transport.md)
  — connect API selection parameters to shareable URL state and browser
  navigation.
- [ ] [tasks/books-discovery/030-books-view-discovery.md](030-books-view-discovery.md)
  — render controls and bounded navigation and keep table, empty state, and
  CRUD refreshes synchronized.

## Execution plan
Status: Draft

Resolve the public query vocabulary, matching rules, page-size policy, response
metadata, and mutation clamping behavior before implementation begins. Then
execute the subtasks in dependency order:

1. Implement and test the optional API selection contract in the Flask layer.
2. Use that contract in the client transport and Books route/view URL state,
   with browser navigation driving the same state-to-fetch path as initial
   loading.
3. Add the visible controls, active-state presentation, bounded page
   navigation, no-match handling, and mutation refresh behavior.
4. Verify the full path at server, component, and router/integration
   boundaries. Confirm that unfiltered API callers and existing CRUD behavior
   remain covered.
5. Update the maintained development documentation with the implemented API
   query contract and URL behavior; do not present the target behavior as
   current guidance before implementation is complete.

The implementation should have one normalized discovery-state representation
used for URL serialization, API requests, rendering, and post-mutation
refreshes. Criteria changes should invalidate an old page selection, while
browser navigation should restore the exact state encoded by each history
entry. The final behavior should make no-match results distinguishable from a
successful page containing books without introducing a second, contradictory
state source.

### Implementation decisions and open questions

The proposed main-task-plus-three-subtask structure matches the ownership
boundaries already present in the repository: `server/query.py` and the Flask
route own selection, the API adapter/router own transport and URL state, and
`Books.vue` owns rendering and mutation refreshes. The split should be
reconsidered if the resolved API contract makes selection entirely client-side,
because that would remove the independently useful server workstream.

The material open questions are the five questions listed above. In
particular, changing the no-parameter response shape would violate the
compatibility requirement, while changing query names or default omission
rules would change shareable URLs. Resolve these with the product owner before
marking the plan Approved.

### Documentation

After implementation, add the smallest maintained developer-facing
documentation needed for the new public behavior under `docs/development/`.
It should cover the optional `/books` query parameters, response pagination
metadata, URL query state, default omission/canonicalization, and how CRUD
refreshes preserve the selected view. Update
`docs/development/index.md` if a new focused guide is added. Do not create
documentation during this planning-only task.

### Task checklist

- [ ] Resolve the requirement questions and approve the API/URL contract.
- [ ] Complete `010-api-discovery-contract.md`.
- [ ] Complete `020-url-state-transport.md`.
- [ ] Complete `030-books-view-discovery.md`.
- [ ] Add cross-boundary evidence for shared URLs, browser navigation, and
  mutation refreshes.
- [ ] Update maintained development documentation after the behavior exists.
- [ ] Append completion notes only after all requirements have evidence.

### Requirement verification

- **Filtering, search, bounded pages:** server API tests should exercise each
  supported read-status and search combination, page boundaries, empty
  results, and metadata used by the client. Component or integration tests
  should prove the controls issue the selected request and render its result.
- **Share/restore and browser navigation:** router-level tests should start
  from a URL, verify controls and results, navigate to another state, and
  exercise back/forward restoration through the real route/query mechanism.
- **Consistent table, active controls, and empty state:** Books view tests
  should cover a populated page, no matches for active criteria, and a valid
  empty page after a refresh or clamped navigation state.
- **CRUD refresh consistency:** view tests should invoke add, update, and
  delete with a non-default discovery state and assert that the subsequent
  GET uses that same normalized state and updates all visible regions.
- **Compatibility:** Flask API tests should assert the existing no-parameter
  response shape and full collection, alongside unchanged POST, PUT, and
  DELETE behavior. Existing tests count as evidence only when the enhanced
  implementation still satisfies their original boundary.
