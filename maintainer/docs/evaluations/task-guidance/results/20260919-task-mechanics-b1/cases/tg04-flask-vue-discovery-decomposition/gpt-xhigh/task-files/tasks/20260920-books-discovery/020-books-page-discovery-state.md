# Synchronize Books discovery state with the URL

Build the client-owned discovery experience on top of the approved list API:
controls, selected-page rendering, URL sharing/restoration, browser history,
and CRUD refreshes that remain inside the selected view.

Parent Task: tasks/20260920-books-discovery/000-main.md

Depends On: tasks/20260920-books-discovery/010-api-query-contract.md

## Requirements checklist

- [ ] The Books page exposes the approved read-status filter, title/author
  search, and bounded page controls.
- [ ] Active controls, table rows, empty state, and page controls all derive
  from one approved discovery state.
- [ ] The approved discovery state is encoded in `/books` query parameters,
  restored on direct navigation, and restored by browser back/forward.
- [ ] Changing discovery controls updates the URL and fetches the matching
  server view without leaving stale results or stale active controls.
- [ ] Add, update, and delete continue to use the existing CRUD behavior and
  refresh the currently selected view, including when a mutation changes
  whether an item belongs on the current page.

## Scope and ownership

This child owns the client API parameter mapping, component state,
rendering/controls, router query synchronization, history behavior, and
client-side CRUD refresh orchestration. It owns the mounted component and
router evidence for these interactions. The server query implementation and
its HTTP contract belong to the API child.

## Unresolved requirement questions and decisions

- URL key names, value vocabulary, default omission/canonicalization, search
  normalization, page size, and out-of-range behavior are inherited from the
  parent and API child; do not create a second client-only vocabulary.
- Decide whether search updates are committed on every input or through an
  approved debounce. This is a UX detail that must not compromise direct-load
  or back/forward restoration.
- Decide whether a control change replaces or pushes history entries after the
  contract is settled. Recommendation: use the router behavior that makes
  deliberate discovery states restorable without creating unusable history
  noise, and verify it explicitly.

## Research and supporting facts

- `client/src/api/books.js:getBooks` already accepts an optional Axios
  `params` object, so the transport extension can remain compatible with
  existing unfiltered callers.
- `Books.vue` currently fetches once on mount and replaces its local full list
  after each mutation; it has no controls, pagination metadata, route
  watcher, or loading/error state.
- `router.js` uses `createWebHistory` and exposes `/books`, which provides the
  route boundary needed for query restoration and browser navigation tests.
- Current client tests mock every API function and only assert the empty
  state. The new tests must add router-backed behavior without making the
  existing CRUD methods test-only shortcuts.

## Execution plan

Status: Draft

1. Consume the API child’s approved query and response metadata contract.
2. Establish one normalized discovery-state model with canonical defaults and
   conversion in both directions: route query to state and state to route
   query.
3. Extend `getBooks` usage to send the selected state and retain the returned
   page metadata.
4. Add status/search/page controls whose active values, disabled bounds,
   table, and empty state all derive from the current fetched view.
5. Watch or otherwise subscribe to route query changes so direct loads and
   browser back/forward restore the complete view without stale data.
6. Refactor add/update/delete refreshes to request the current discovery state,
   then handle an invalidated page according to the approved API behavior.
7. Add component and router-backed integration tests for controls, URL
   restoration, history, empty views, page bounds, and CRUD refreshes.
8. Update the maintained developer guidance with the URL-facing behavior.

### Implementation decisions and open questions

The client must not maintain a second interpretation of the API vocabulary.
Resolve the inherited contract first, then record the canonical URL and
history behavior here before execution.

### Documentation

Document the shareable `/books` query state, defaults, direct-load behavior,
browser navigation behavior, and how CRUD refreshes preserve the selected
view. Cross-link the API query contract rather than copying server details
that may diverge.

### Task checklist

- [ ] Resolve the inherited API contract and client history/debounce choices.
- [ ] Mark this child `Approved` after its dependency is complete or the
  approved contract is otherwise available.
- [ ] Add query/state conversion and production API parameter mapping.
- [ ] Implement controls, table state, empty state, and bounded pagination.
- [ ] Implement direct-load and browser history restoration.
- [ ] Preserve discovery state across add/update/delete refreshes.
- [ ] Add and run focused component/router integration tests.
- [ ] Update the maintained client guidance.
- [ ] Append completion notes with evidence and any deferred UX decisions.

### Requirement verification

- The decisive rendering check mounts the real `Books.vue` with a real
  router, supplies approved API responses, and asserts active controls,
  current-page rows, empty state, and disabled/enabled navigation.
- The decisive URL check starts from a query-bearing `/books` route, verifies
  restored state, changes state through controls, then exercises router
  back/forward and verifies both the URL and fetched/rendered view.
- The decisive CRUD check invokes the existing add/update/delete methods while
  a non-default discovery state is active, verifies requests retain that
  state, and covers a mutation that invalidates the current last page.

### Additional implementation verification

- Verify canonical defaults do not create URL churn or lose meaningful state
  during route synchronization.
- Verify rapid route changes cannot leave a result from an older discovery
  state displayed as the current view, if the chosen request orchestration
  permits overlapping requests.
- Verify the existing unfiltered mount and CRUD behavior continue to work for
  callers that do not provide discovery parameters.