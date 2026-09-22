# Books discovery experience

Plan the Books page and API changes needed to make a larger collection
discoverable through read-status filtering, title/author search, bounded
pagination, and URL-backed state. This is a planning handoff only; the target
behavior is **Not implemented**.

## Requirements checklist

- [ ] The Books page lets users filter by read status, with the selected
      filter represented in the active controls and applied to the table.
- [ ] The Books page lets users search by title or author, composes search with
      the read-status filter, and keeps the active search visible.
- [ ] The result set uses bounded pages with controls that reflect the
      available range and cannot navigate outside it.
- [ ] The complete discovery state can be shared and restored through the
      `/books` URL, including browser back/forward navigation.
- [ ] The table, active controls, empty state, URL state, and pagination remain
      mutually consistent when the selected view changes.
- [ ] Add, update, and delete preserve their existing CRUD behavior while
      refreshing the currently selected discovery view and handling a view
      whose page contents change after a mutation.
- [ ] A request to `GET /books` without discovery parameters retains the
      existing unfiltered API behavior and response compatibility.
- [ ] Existing CRUD endpoint contracts remain compatible.

## Subtasks

- [ ] [tasks/20260920-books-discovery/010-server-discovery-query.md](./010-server-discovery-query.md)
- [ ] [tasks/20260920-books-discovery/020-books-page-discovery.md](./020-books-page-discovery.md)

## Unresolved requirement questions

These public-contract and user-visible details are not specified by the
request and must be confirmed before the Draft plan becomes Approved:

- What query parameter names and values should represent read status, search,
  page, and page size? A concrete proposal is `status=all|read|unread`,
  `search=<text>`, `page=<positive integer>`, and a fixed or explicit
  `per_page`.
- Should search be a case-insensitive substring match over either title or
  author, and how should surrounding whitespace be handled?
- What default and maximum page sizes are required? Should malformed or
  out-of-range pages be rejected, clamped, or normalized to a valid page?
- What stable ordering should pagination use? The current API exposes the
  in-memory insertion order; retaining that order is the least surprising
  compatibility choice unless a different order is required.
- Must the no-parameter `GET /books` response remain byte-for-byte in shape
  (the existing `status` and `books` keys only), or may compatible pagination
  metadata be added? The plan assumes the legacy no-parameter response stays
  unchanged and discovery requests carry any new metadata, pending approval.
- When a filter/search change leaves the current page invalid, should the page
  reset to one. When deleting the last result on a page, should the view move
  to the last remaining page. These choices affect the URL and CRUD refresh
  behavior.
- Should default discovery values be omitted from canonical URLs, and is page
  size user-selectable or an implementation constant?

## Research and supporting facts

- `server/app.py` currently serves all in-memory `BOOKS` from `GET /books`;
  it parses no query parameters and returns `{"status": "success", "books":
  BOOKS}`. The same module owns the existing POST, PUT, and DELETE routes.
- `server/query.py:list_books` currently returns a shallow list copy and is the
  natural server-side selection boundary.
- `client/src/api/books.js:getBooks` already accepts an optional `params`
  object, but `client/src/components/Books.vue` never supplies one.
- `Books.vue` currently stores only the returned books, renders a table or the
  fixed `No books found.` empty state, and refetches without parameters after
  each mutation.
- `client/src/router.js` already provides a history-mode `/books` route, so
  query state can be owned by the existing router instead of introducing a
  second navigation mechanism.
- Existing API coverage only checks a successful list and CRUD status codes.
  Existing client coverage checks the empty state; the integration file
  explicitly has no production transport coverage.
- `docs/development/index.md` currently states that no book-discovery
  specification exists. No current user-facing discovery documentation
  should be fabricated during this planning-only change.

## Execution plan

Status: Draft

Implement the feature across the two owned boundaries after the open contract
questions are answered:

1. Establish the approved query/response and URL contract, including matching,
   ordering, page bounds, invalid-state normalization, and compatibility
   behavior.
2. Complete the server workstream. Normalize optional discovery inputs, select
   by read status and title/author search, paginate within the approved bounds,
   and return the metadata the client needs. Keep the no-parameter list path
   and all mutation routes compatible. Add Flask-client tests at the actual
   HTTP boundary.
3. Complete the client workstream after the server contract is fixed. Derive
   one normalized discovery state from router query parameters, send that
   state through `getBooks`, and keep controls, table, empty state, page
   controls, and route updates synchronized. Make browser back/forward restore
   the same state without watcher loops or stale local state.
4. Refactor the existing CRUD refreshes to reload the current discovery
   request. Apply the approved page-normalization rule when a mutation removes
   or moves the last visible result, while preserving existing mutation calls
   and response handling.
5. Add focused client component/router coverage and a production-path
   transport check for query serialization. Run the existing API and client
   suites, then update the maintained developer documentation with the
   approved public API and URL contract.

The server workstream is a prerequisite for the client workstream because the
client state and tests depend on the agreed response metadata. Neither
workstream should add a client-side fetch-all/filter workaround: the purpose
of the API contract is to keep large collections bounded.

## Risks and boundaries

- Two sources of truth (local component state and `route.query`) could drift;
  the client task must define one-way synchronization and a canonicalization
  rule before adding controls.
- Filtering or mutating while a request is in flight can display a response
  for an older view. Tests should cover the chosen request-order strategy if
  the implementation introduces concurrent refreshes.
- Adding metadata to an unfiltered response could break strict existing
  consumers even if `books` remains present. Compatibility must be tested
  explicitly rather than inferred from the client.
- Pagination after CRUD can leave the current URL pointing at an empty or
  invalid page. The approved normalization rule must be applied consistently
  by API and UI.
- The task does not authorize changes to persistence, authentication,
  sorting beyond what is needed for stable paging, or unrelated router
  routes.

### Implementation decisions and open questions

- The parent is split into two subtasks because the server discovery contract
  is an independently owned API result and the Vue page has an independently
  owned URL/rendering result. Verification and documentation stay with those
  owners.
- The plan remains Draft until the unresolved public API and URL semantics
  above are answered or explicitly delegated as implementation decisions.
- The planned implementation must preserve the existing no-query list path
  and CRUD endpoints; any response extension needs explicit compatibility
  evidence.

### Documentation

- No maintained documentation is changed in this planning-only pass.
- After implementation, update the smallest owned developer documentation
  location with the approved query parameters, response metadata, URL
  serialization, and navigation/mutation behavior. If a discovery spec is
  introduced, link it from `docs/development/index.md`; do not publish the
  target behavior as current guidance before it exists.

### Task checklist

- [ ] Resolve the open API, URL, matching, ordering, and page-transition
      questions.
- [ ] Approve this plan and change both child plans from Draft to Approved.
- [ ] Complete `tasks/20260920-books-discovery/010-server-discovery-query.md`.
- [ ] Complete `tasks/20260920-books-discovery/020-books-page-discovery.md`.
- [ ] Run the decisive API, client, and transport/navigation verification.
- [ ] Update maintained documentation and record completion evidence.

### Requirement verification

- **Read-status filtering and title/author search:** API integration tests
  should seed books covering each status and match location, exercise the
  production `GET /books` route with the approved parameters, and assert the
  page result and count metadata. A Books-page test should assert the same
  parameters are sent when controls change and that the table/active controls
  show only that view.
- **Bounded pagination:** API tests should assert page size, total/page
  metadata, stable ordering, and the approved invalid/out-of-range behavior.
  A rendered-page test should assert disabled/hidden boundary controls and
  that navigating a page updates both the request and table.
- **Share/restore and browser navigation:** mount the Books component with the
  real router configuration, load a URL containing the approved query state,
  and assert controls and results restore from it. Push at least two states,
  invoke router back/forward, and assert the complete view returns each time.
- **Consistent table, controls, empty state, and CRUD refresh:** exercise a
  non-default filtered/search page through the component's production API
  functions, then perform add/update/delete and assert refreshes retain the
  selected query and apply the approved page-transition rule. Include a
  no-match view whose empty state identifies the selected view without
  showing stale rows.
- **Unfiltered API and CRUD compatibility:** Flask test-client coverage must
  assert the no-parameter list response keeps the existing status/books
  contract and that POST, PUT, and DELETE retain their current status and
  response behavior. This check must not be satisfied by mocking the route.
