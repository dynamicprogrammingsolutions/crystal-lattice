# Make the Books page scalable and shareable

Make the Books page useful for larger collections by adding read-status
filtering, title/author search, bounded pagination, and URL-backed discovery
state while preserving the existing CRUD workflows and unfiltered API
behavior.

## Requirements checklist

- [ ] The Books page lets users choose a read-status view, including the
      unfiltered/all-books view.
- [ ] The Books page lets users search by book title or author.
- [ ] Search and read-status filtering are applied to the same collection that
      is paginated, and the UI exposes bounded navigation for the resulting
      pages.
- [ ] The active filter, search, and page controls visibly reflect the
      selected discovery state.
- [ ] The table renders the current page of the current discovery result, and
      the empty state is correct for an empty filtered/search result as well as
      an empty collection.
- [ ] The current discovery state is represented in the `/books` URL so that a
      copied URL restores the same view on direct load.
- [ ] Browser back and forward navigation restore the corresponding discovery
      state and result without leaving stale controls, table rows, pagination,
      or empty-state content.
- [ ] Adding, updating, and deleting a book preserve their existing CRUD
      behavior and refresh the table using the active discovery state. Refresh
      behavior remains coherent when a mutation changes the current result or
      leaves the current page out of range.
- [ ] The Flask books endpoint accepts optional discovery inputs while a
      request with no discovery inputs remains compatible with the existing
      unfiltered response contract.
- [ ] The client transport passes discovery state through the public books API
      without changing the existing mutation interfaces.
- [ ] Automated evidence covers the API compatibility and discovery contract,
      the component's state/rendering/navigation behavior, and at least one
      production-path check connecting the Books page, transport, Flask route,
      filtering/pagination, and CRUD refresh behavior.
- [ ] Maintained project documentation describes the supported discovery query
      contract and URL state once the behavior is implemented; target behavior
      is not presented as current guidance before implementation.

## Unresolved requirement questions

These questions affect the public API or user-visible behavior and must be
answered before this Draft can become Approved:

- What are the canonical query-string names and values? A recommended
  contract is `read=all|true|false`, `q=<text>`, `page=<positive integer>`, and
  `page_size=<positive integer>`, with omitted values representing the
  default view.
- Should the server use a fixed page size, expose a user-selectable page size,
  or accept `page_size` only as an internal/client-controlled bounded value?
- What matching rules should search use: case-insensitive substring matching
  across title and author (the recommended default), and should whitespace be
  trimmed and normalized?
- What stable ordering should pagination use, and should it be explicitly
  documented? The recommended default is the current `BOOKS` order, with a
  deterministic tie-breaker if filtering/search implementation introduces
  sorting.
- What response metadata should discovery requests return so the client can
  bound navigation (for example `total`, `page`, `page_size`, and `pages`)?
  The recommended compatibility shape is to retain the current
  `{status, books}` shape when no discovery inputs are supplied and add
  pagination metadata for discovery requests.
- How should invalid or out-of-range page/filter values be handled? The
  recommended UI behavior is to normalize invalid values and clamp a page
  beyond the available range after a result-changing action, but the HTTP
  status and payload for malformed external requests need confirmation.

## Supporting facts and scope

- `server/app.py` currently returns every book from `GET /books` with
  `{status: "success", books: [...]}` and has separate PUT/DELETE routes.
- `server/query.py` currently only returns a copied list and is the natural
  owner for reusable filtering/search/pagination selection logic if that
  remains useful after the contract is settled.
- `client/src/api/books.js` already accepts an optional parameter object in
  `getBooks`, while mutation functions have stable existing signatures.
- `client/src/components/Books.vue` currently loads once, renders only a table
  or `No books found.`, and reloads without parameters after each mutation.
- `client/src/router.js` already owns the `/books` route but does not currently
  define query-state synchronization.
- Existing tests only establish basic route/mutation status responses and the
  component's empty state; there is no current transport integration coverage.
- This is intentionally one task rather than API/UI subtasks: the selected
  state, URL contract, server result metadata, and CRUD refresh behavior form
  one independently acceptable product outcome. Per-layer checks belong in the
  plan, while the decisive acceptance check must cross the real production
  connection.
- No implementation, task approval, or current-user documentation change is
  authorized by creating this Draft.

## Execution plan

Status: Draft

The implementation should establish one canonical discovery-state model shared
by the route query, the Books component, and the books transport. The model
should distinguish the all-books/read-status choice, normalized search text,
and bounded page information. Route query parsing must produce the same
normalized state used by controls and requests; state changes should write the
canonical query so copied URLs and browser history are meaningful. The
component should render from the latest server result and metadata rather than
maintaining a second, independently filtered copy of the collection.

On the server, keep the no-argument `GET /books` path compatible with the
existing response and apply optional discovery inputs through a focused
selection boundary. The discovery response must expose enough bounded-result
metadata for the client to disable or enable previous/next navigation. Keep
POST/PUT/DELETE routes and payload expectations intact. Define normalization,
matching, ordering, and invalid-input behavior from the answers above before
implementation.

On the client, extend `getBooks` to carry the settled query contract and make
the Books page own the synchronization lifecycle: initialize from the route,
request the corresponding result, update the route when controls change,
respond to route changes caused by browser navigation, and prevent stale
responses from replacing a newer view if requests overlap. Keep add/update/
remove methods on the existing mutation API and re-fetch through the active
discovery state. When a mutation invalidates the current page, use the settled
clamping/normalization rule and update the URL and result together.

Implement and verify in this order:

1. Resolve and record the discovery API, URL, matching, ordering, page-size,
   and invalid-input decisions in this task before changing code.
2. Add focused server selection/route coverage for read status, title/author
   search, bounded pages, response metadata, normalization, and the unchanged
   no-argument response and mutation routes.
3. Add the client transport contract and Books component state/rendering tests
   for controls, active state, table/empty-state transitions, page bounds,
   direct URL restoration, and back/forward route changes.
4. Implement the real route-to-transport-to-Flask flow and CRUD refresh path,
   then add or update the production-path integration check so it exercises
   the actual component and transport boundary rather than supplying the
   filtered result through a mock.
5. Update the maintained README with the final supported API query and URL
   behavior, run the focused server/client suites and the required
   production-path check, and record any blocked verification.

### Implementation decisions and open questions

- This Draft recommends server-side filtering and pagination because the
  feature targets larger collections; client-side slicing would not provide a
  bounded transport result.
- The API's exact parameter names, metadata shape, page-size policy, search
  semantics, ordering, and invalid-input behavior remain requirement
  questions above. Do not turn the recommendations into a public contract
  without approval.
- The existing unfiltered response must remain a supported compatibility
  path. Adding metadata to every no-argument response would be a material
  contract change and is not assumed here.
- Route query state is the shareable source of truth. Local component state
  may represent loading/result data, but it must not diverge from the
  normalized URL discovery state.
- No new task split is proposed unless an independently owned compatibility
  or deployment boundary appears during contract review.

### Documentation

- After implementation, update the root `README.md` with the final supported
  `GET /books` discovery inputs, response metadata, and `/books` URL-state
  behavior. Keep the description concise and current.
- Do not create a separate documentation hierarchy for this capability unless
  the settled contract outgrows the README; the repository currently has no
  Books discovery specification or user guide.
- If the contract is not implemented, leave current documentation unchanged
  and keep this Draft as planning material rather than publishing target
  behavior.

### Task checklist

- [ ] Resolve the requirement questions and record approved contract decisions.
- [ ] Mark this plan Approved before implementation begins.
- [ ] Implement and test the server-side discovery selection and optional
      route contract.
- [ ] Implement and test the client transport and canonical route/component
      state synchronization.
- [ ] Preserve and verify existing CRUD behavior, unfiltered API compatibility,
      and mutation refreshes under an active discovery view.
- [ ] Run the decisive production-path integration check plus focused server
      and client suites.
- [ ] Update maintained documentation with the implemented contract.
- [ ] Record implementation and completion notes only after execution starts
      and the work is actually complete.

### Requirement verification

- Read-status filter, title/author search, bounded pages, result metadata, and
  unfiltered compatibility: server route tests that issue real `GET /books`
  requests with and without discovery inputs and assert both returned rows and
  metadata/legacy shape.
- Active controls, table rows, filtered/search empty state, page bounds, direct
  URL restoration, and browser navigation: Books component/router tests that
  mount the real component with a controlled router and exercise query changes
  and history navigation.
- URL sharing and transport propagation: a route-to-client-API test asserting
  canonical query values are sent to `getBooks` and reconstruct the same state
  from an initial `/books` URL.
- CRUD preservation and refresh consistency: a production-path integration
  check that performs add/update/delete through the existing API functions
  while a non-default discovery state is active, then verifies the displayed
  page, active controls, URL, and empty/page-bound behavior.
- Documentation: inspection of the updated README against the implemented
  public contract after the behavior exists.

### Additional implementation verification

- Verify that an old caller using `GET /books` with no query still receives
  the existing status and complete books list, and that existing POST/PUT/
  DELETE payload expectations still pass.
- Verify request/result race handling or equivalent stale-response protection
  when a user changes search/filter/page quickly.
- Verify page clamping after deleting the final item on a page and after a
  search or read-status change reduces the result count.
- Verify browser refresh on a copied URL does not depend on prior in-memory
  component state.