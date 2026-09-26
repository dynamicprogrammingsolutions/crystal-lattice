# Books page discovery controls and URL state

Connect the approved Books API discovery contract to the Vue page so controls,
rendering, browser navigation, and CRUD refreshes all represent one
shareable discovery view.

Parent Task: `tasks/20260925-books-discovery/000-main.md`

Depends On: `tasks/20260925-books-discovery/010-api-discovery-contract.md`

## Requirements checklist

- [ ] The page exposes read-status filtering, title/author search, and
  bounded page navigation, with active controls matching the selected view.
- [ ] The table, pagination controls, and empty state are rendered from the
  same loaded discovery result and remain consistent when there are no
  matches.
- [ ] Direct `/books` URLs restore discovery state, control changes update
  the shareable URL, and browser back/forward restores the corresponding
  controls and results.
- [ ] The client forwards the selected discovery state to `GET /books`, and
  add, update, and delete refresh the current view without changing existing
  CRUD behavior.

## Requirement questions and decisions

The page inherits the unresolved public-contract questions from
`tasks/20260925-books-discovery/000-main.md`. In particular, it must wait for
the approved URL/query names, default values, page bounds, and invalid-value
policy before exposing controls or normalizing route state.

## Supporting facts

- `client/src/api/books.js:getBooks(params = {})` already supports Axios query
  parameters, while mutation helpers are separate and should remain
  unchanged.
- `client/src/components/Books.vue` currently owns only a `books` array,
  loads once on mount, renders a table or `No books found.`, and reloads after
  each mutation.
- `client/src/router.js` uses `createWebHistory` and has a single `/books`
  route, so route query synchronization belongs at this boundary rather than
  in a second ad hoc state store.
- `client/tests/Books.spec.js` mocks the books API and only verifies the
  empty state. `client/tests/books.integration.js` is an unused placeholder,
  and the package currently has no browser start/build script.

## Execution plan

Status: Draft

Use one normalized discovery-state model for route parsing, API request
parameters, active controls, and rendering. Route changes—including direct
loads and browser back/forward—must load from the route state. Control changes
must update the route through the router, and the page must avoid duplicate
or stale loads when both a control event and a route watcher are involved.
CRUD methods should call the same loader with the current route-derived state;
if a mutation invalidates the current page, apply the API-approved bounds
policy and keep the URL synchronized.

Implementation order:

1. Add route-state parsing/serialization around the approved contract,
   including defaults and the approved malformed/out-of-range behavior.
2. Pass the normalized state to `getBooks`, consume the API’s pagination
   metadata, and render controls, active values, rows, empty state, and page
   bounds from the response/state together.
3. Wire control changes, direct URL restoration, and router back/forward
   events through the same load path.
4. Refactor add, update, and remove refreshes to retain the active route
   state while preserving their existing exported/method behavior.
5. Add focused component/router tests and a real-transport integration check.
   The integration check must not replace the API with a mock: run the Flask
   app through its public HTTP route and exercise the client’s real
   `getBooks`/page-loading path. Establish the client launch command during
   execution because this fixture currently has no client runtime entrypoint.

### Implementation decisions and open questions

- Recommended direction, pending parent approval: make the URL query the
  canonical serialized state and keep transient loading data separate from
  it.
- Preserve the existing `getBooks(params)` and mutation helper boundaries;
  add only the state needed to pass discovery parameters and consume the
  approved response.
- Do not claim browser-navigation coverage from a component test that merely
  mutates local data; the router must participate in the decisive test.
- Search update timing (immediate versus an approved debounced interaction)
  and control reset behavior are user-visible details and remain open if the
  parent does not specify them.

### Documentation

After implementation, contribute the verified page URL examples and browser
restoration behavior to the maintained development documentation selected by
the parent task. Do not add a placeholder page during planning.

### Task checklist

- [ ] Receive the finalized API/query contract from
  `tasks/20260925-books-discovery/010-api-discovery-contract.md`.
- [ ] Implement normalized route-backed discovery state and API requests.
- [ ] Implement controls, active state, bounded navigation, table, and empty
  state.
- [ ] Preserve discovery state across add, update, and delete refreshes.
- [ ] Add component/router regression tests.
- [ ] Add and run the real client-to-Flask transport check.

### Requirement verification

- Controls/rendering: component tests with mocked responses must verify
  read-status, search, active values, page bounds, table rows, and no-match
  empty rendering as one state.
- URL restoration/navigation: router-backed tests must start at a URL with
  discovery query values, change a control, then traverse back and forward;
  each step must assert both the URL query and rendered controls/results.
- CRUD refresh: invoke each existing mutation method while a non-default
  discovery view is active and assert that the next real API call contains
  the same discovery state (plus any approved page correction).
- Connection: the decisive check must use the actual `getBooks` transport
  against a running Flask server and the page’s real load path. Mocked
  `client/src/api/books.js` tests are supporting evidence only.

### Additional implementation verification

- Check that rapid route changes cannot display a stale response as the
  current view.
- Check direct loading of default and non-default URLs, including a filtered
  result with no rows.
- Check that controls and page navigation remain usable at both page bounds
  and after CRUD changes alter the result count.