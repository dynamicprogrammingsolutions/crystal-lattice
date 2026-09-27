# Books page discovery state

Integrate the agreed server discovery contract into the Vue Books page so
controls, URL state, browser navigation, rendering, pagination, and CRUD
refreshes remain one coherent selected view.

Parent Task: `tasks/20260926-books-discovery/000-main.md`
Depends On: `tasks/20260926-books-discovery/010-server-discovery-contract.md`

## Requirements checklist

- [ ] The page exposes read-status filtering, title/author search, and
  bounded page navigation using the server’s agreed contract.
- [ ] The selected discovery state is encoded in the `/books` URL and restored
  on initial navigation.
- [ ] Browser back and forward restore the corresponding controls, request,
  table, pagination bounds, and empty state.
- [ ] Active controls, displayed rows, pagination controls, and no-result
  messaging all describe the same selected view.
- [ ] Add, update, and delete refresh the selected view with its current query
  state instead of reverting to an unfiltered list.

## Unresolved requirement questions

- Confirm the canonical URL keys, default omission policy, and history
  push/replace behavior.
- Confirm how search input commits state (immediate, submit, or another
  interaction) if this affects browser history or request volume.
- Confirm whether a mutation that invalidates the current page clamps the page
  and updates the URL.

## Supporting facts

- `Books.vue` currently has no controls, route access, pagination state, or
  distinction between an unfiltered empty result and a filtered no-result
  result.
- `getBooks(params = {})` already forwards an Axios `params` object, so the
  client transport has a narrow extension point.
- Vue Router is already configured with a `/books` route and web history.
- `Books.spec.js` mocks the API and currently covers only the generic empty
  state; it does not provide a router or real API integration.

## Execution plan

Status: Draft

Use the route query as the canonical shareable state. Normalize route values
into the component’s view model, fetch through `getBooks` with the agreed
parameters, and update the route when controls change. Route changes from
initial navigation or browser history should pass through the same
normalization/fetch path as in-page control changes. The rendered table and
empty state should use the currently loaded result, while active controls and
pagination derive from the normalized query and response metadata.

Keep CRUD methods routed through one refresh operation that reads the current
discovery state. After a mutation, apply the approved page-boundary policy
before rendering so the URL and displayed result do not disagree. Preserve the
existing mutation API calls and payloads.

1. Consume the server child’s agreed response and query contract.
2. Add route-query parsing/serialization and a single state transition path
   for controls, initial load, and browser navigation.
3. Add read-status and search controls, active-state presentation, bounded
   pagination controls, and selected-view empty/table rendering.
4. Refactor add/update/remove refreshes to use the current route state and
   handle the approved out-of-range-page behavior.
5. Extend component tests for controls, route restoration, back/forward,
   result/empty consistency, and mutation refreshes.
6. Replace or complete the placeholder production transport integration test
   without mocking `getBooks`, using the real Vue route/component, Axios
   adapter, and Flask endpoint.

### Implementation decisions and open questions

- The client child owns route synchronization and user-visible state; it does
  not duplicate server-side filtering or infer total pages from the current
  page alone.
- Keep a single refresh path for mount, route changes, and CRUD completion so
  selected-view preservation is tested and maintained in one place.
- Do not finalize URL/history or post-mutation page behavior until the parent
  questions are resolved.

### Documentation

Supply verified control labels, URL examples, browser-navigation behavior,
and no-result behavior to the parent for the root README update. Do not
describe target behavior as current before this child is implemented.

### Task checklist

- [ ] Consume and document the approved server response contract.
- [ ] Implement route state parsing and serialization.
- [ ] Implement controls, active state, table, empty state, and bounded
  pagination.
- [ ] Preserve discovery state across add, update, and delete refreshes.
- [ ] Add routed component evidence and complete the real transport
  integration evidence.

### Requirement verification

- Control-to-request-to-render behavior is verified by mounting the real
  `Books` component with a router and exercising user-facing controls against
  the agreed API response.
- Initial URL restoration and browser navigation are verified through router
  navigation/history operations, asserting both rendered controls and the
  requested parameters.
- Empty and table states are verified for unfiltered, filtered, searched,
  paginated, and zero-result views using the same route state that drives the
  request.
- CRUD preservation is verified by invoking the component’s actual add,
  update, and remove methods and asserting that the refresh uses the existing
  route query.

### Additional implementation verification

- Guard against route-update/fetch loops and stale asynchronous responses when
  users change discovery state quickly.
- Verify canonical query serialization does not lose meaningful values or
  create duplicate history entries for equivalent state.
- Keep the existing CRUD payload and endpoint tests active while replacing
  only the list-refresh assumptions.