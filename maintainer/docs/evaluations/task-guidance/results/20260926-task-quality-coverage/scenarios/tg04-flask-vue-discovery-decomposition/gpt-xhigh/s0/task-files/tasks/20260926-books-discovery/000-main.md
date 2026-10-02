# Books discovery controls, pagination, and URL state

Plan the end-to-end Books discovery capability across the Flask list endpoint
and the Vue Books page without changing production code in this planning
handoff.

## Requirements checklist

- [ ] The Books page lets users filter by read status, search by title or
  author, and move through bounded result pages.
- [ ] The active discovery state can be shared and restored through the
  `/books` URL, including restoration on initial load and browser
  back/forward navigation.
- [ ] The table, active controls, and empty state represent the same selected
  view, including filtered, searched, and paginated no-result cases.
- [ ] Add, update, and delete operations retain the selected discovery view
  when they refresh the list, while keeping the view valid when its result set
  changes.
- [ ] The existing unfiltered `GET /books` behavior remains compatible, and
  existing create, update, and delete behavior remains available.

## Scope and workstreams

This is one end-to-end product capability with two independently owned
workstreams:

1. The server workstream defines and implements selection, search, pagination,
   stable ordering, and compatibility at the Flask list boundary.
2. The client workstream owns the Books page controls, route-query state,
   rendering, browser navigation, transport parameter forwarding, and CRUD
   refresh behavior.

The parent owns the connection between those workstreams and the final
production-path verification. Sorting, bulk actions, new CRUD operations, and
unrelated visual redesign are out of scope.

## Unresolved requirement questions

These public behavior choices must be confirmed before the Draft plan is
approved for execution:

- What query parameter names and values should represent read status, search
  text, page number, and page size, and should the equivalent URL keys use the
  same names?
- Should search be a case-insensitive substring match across either title or
  author, or is another matching rule required?
- Is page size fixed for this feature, or should users be able to choose it?
  If fixed, what default size should bound the page controls?
- When a mutation removes the last result from the current page, should the
  page clamp to the last valid page and update the URL, or should the selected
  page remain visible with the empty state?
- Should default discovery values be omitted from the canonical URL, and
  should changing a control replace the current history entry or create a new
  one?

Recommended defaults for review, not yet resolved requirements: use
case-insensitive substring matching across title or author, a fixed page size,
canonical query keys that omit defaults, `replace` while editing search, and
clamping to the last valid page after a mutation.

## Supporting facts

- `client/src/components/Books.vue` currently owns only a local `books` array,
  loads all books on mount, renders a table or one generic empty message, and
  refetches without parameters after each mutation.
- `client/src/api/books.js` already accepts an optional `params` object for
  `getBooks`, but the component does not use it.
- `client/src/router.js` already exposes `/books` through Vue Router history,
  but the route has no discovery-state handling.
- `server/app.py` currently returns the complete mutable `BOOKS` collection
  from `GET /books` in a `{status, books}` envelope. The same route also
  handles POST, while the item route handles PUT and DELETE.
- `server/query.py:list_books` is currently a pass-through helper and is not
  used by the route.
- Existing client coverage only mounts the component with a mocked API and
  checks the generic empty state. `client/tests/books.integration.js` is a
  placeholder with no production transport coverage.
- Existing server coverage checks list and mutation status codes but does not
  assert filtering, searching, pagination, response metadata, or unfiltered
  result compatibility.
- The repository has no discovery specification. The maintained root
  `README.md` is the smallest existing place to document the supported
  public behavior after implementation.

## Subtasks

- [ ] `tasks/20260926-books-discovery/010-server-discovery-contract.md`
- [ ] `tasks/20260926-books-discovery/020-books-page-discovery-state.md`

## Execution plan

Status: Draft

The server is the source of truth for filtering, searching, stable ordering,
and page boundaries. Query-bearing list responses must provide the client
enough information to render bounded controls and to reconcile a page after a
CRUD refresh. The no-parameter `GET /books` path must retain its current
unfiltered contract for existing consumers; any additional metadata needed for
discovery should be introduced in the agreed query-bearing contract without
changing existing mutation routes.

The Vue page should treat the route query as the shareable discovery state.
It should parse and normalize route values on initial load and route changes,
forward the resulting selection to `getBooks`, and write user changes back
through the router. Rendering should derive from the same loaded result and
normalized state so active controls, the table, pagination bounds, and the
empty message cannot drift apart. CRUD methods should refresh using that
current state rather than reverting to an unfiltered fetch.

Implementation order:

1. Resolve the public query, URL, page-size, matching, history, and
   post-mutation page-boundary choices listed above.
2. Execute the server child: add the query/data-selection contract, preserve
   the no-parameter list behavior and CRUD routes, and add focused API
   evidence.
3. Execute the client child against the agreed response contract: add
   controls, route-query synchronization, browser navigation handling,
   bounded pagination, consistent states, and parameter-preserving CRUD
   refreshes.
4. Update the maintained README with the supported user controls, URL state,
   and public list-query contract. Do not add a new documentation hierarchy
   for this feature.
5. Run the focused server and client tests, then run a decisive integration
   check through the real client API module, Vue route/component, HTTP
   transport, and Flask endpoint together. The existing placeholder
   `client/tests/books.integration.js` is the planned home for that boundary
   check, or it should be replaced by an equivalent real-path test if its
   harness cannot host the server safely.

### Implementation decisions and open questions

- The parent keeps the two-layer split because the server list contract is an
  independently useful API result, while the user-facing feature is accepted
  only when the real Vue-to-Flask path works together.
- The exact public query/URL names, matching semantics, page size, history
  policy, and out-of-range-page behavior remain requirement questions above.
  They must be settled before changing the API contract.
- No compatibility shim or alternate legacy query syntax is planned unless
  compatibility evidence shows an existing consumer needs one.

### Documentation

Update `README.md` in the implementation change with current, verified
behavior: supported read-status and text discovery controls, bounded page
navigation, URL restoration/browser navigation, and the agreed public
`GET /books` query contract. Keep the plan’s unresolved choices out of
current user/developer guidance until they are implemented and verified.

### Task checklist

- [ ] Resolve the listed public behavior questions and record the decisions.
- [ ] Complete `010-server-discovery-contract.md`.
- [ ] Complete `020-books-page-discovery-state.md` after the server contract is
  fixed.
- [ ] Add or update the maintained README.
- [ ] Run focused server and client evidence.
- [ ] Run the real client-to-Flask production-path integration check.
- [ ] Update this task’s requirement evidence and append completion notes after
  implementation is actually complete.

### Requirement verification

- The filter/search/page outcome is an explicit combination of
  `010-server-discovery-contract.md` (selection and bounded response) and
  `020-books-page-discovery-state.md` (controls and rendering). The decisive
  check is the real-path integration test in
  `client/tests/books.integration.js`, invoked with `cd client && npm test --
  --run tests/books.integration.js` while its managed Flask fixture is
  available.
- URL sharing, initial restoration, and browser back/forward are owned by
  `020-books-page-discovery-state.md` and verified with a routed component test
  that exercises the actual Vue Router history/query behavior rather than
  directly setting component data.
- Consistency among active controls, table, pagination, and the empty state is
  owned by `020-books-page-discovery-state.md` and verified through component
  cases for each discovery dimension and a no-result combination.
- CRUD refresh preservation is owned by
  `020-books-page-discovery-state.md` and verified through the component’s
  real mutation methods with the selected route query retained, plus the
  production-path integration check for transport parameters.
- Unfiltered API compatibility and CRUD preservation are owned by
  `010-server-discovery-contract.md` and verified with direct Flask tests that
  compare the no-parameter list shape/results and exercise POST, PUT, and
  DELETE. The parent integration check confirms the client still uses those
  routes.

### Additional implementation verification

- Use a deterministic seed/reset fixture so query tests do not depend on
  mutation order or leak records between cases.
- Verify that page metadata and ordering remain coherent when filters reduce
  the result set, and that stale responses cannot overwrite a newer route
  selection if requests overlap.
- Keep the existing mocked component tests focused on local rendering while
  ensuring the real-path integration check crosses the transport boundary
  that mocks would bypass.