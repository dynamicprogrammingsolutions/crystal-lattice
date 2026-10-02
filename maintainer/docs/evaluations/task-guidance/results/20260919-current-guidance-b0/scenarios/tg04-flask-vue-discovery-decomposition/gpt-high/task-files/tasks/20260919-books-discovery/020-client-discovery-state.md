# Client discovery state and Books page

Consume the approved API contract in a single normalized Books discovery state
that controls rendering, URL restoration, browser navigation, and CRUD
refreshes.

Parent Task: tasks/20260919-books-discovery/000-main.md
Depends On: tasks/20260919-books-discovery/010-server-discovery-contract.md

## Requirements checklist

- [ ] The client sends the approved status, search, and page parameters to
      `GET /books`.
- [ ] The page exposes active read-status and search controls whose values
      match the current discovery state.
- [ ] The table renders only the selected page and the empty state reflects
      the selected filter/search combination.
- [ ] Pagination controls show the current/available page state and disable
      or omit invalid navigation.
- [ ] The current discovery state serializes to `/books` and is restored from
      a shared URL on initial load.
- [ ] Browser back/forward applies prior serialized state and reloads the
      corresponding results.
- [ ] Add, update, and delete reload the current discovery query, retaining
      selected controls and correcting an invalid page when required.
- [ ] Client tests cover state/rendering transitions and URL/history behavior.

## Supporting facts

- `Books.vue` currently owns loading and all three CRUD refreshes but has no
  route access or discovery state.
- `getBooks(params = {})` already forwards Axios query parameters.
- `router.js` currently maps `/books` directly to `Books`, so route-level
  state can be added without changing the public path.
- The current component test mocks all API functions and only asserts the
  empty state; it will need richer response and request assertions.

## Execution plan

Status: Draft

Introduce a normalized discovery-state model with approved defaults and
conversion helpers for route query values. Use one loader for initial route
restoration, control changes, browser navigation, and CRUD refreshes. Keep
URL serialization and history behavior at the router/page boundary, and keep
rendering derived from the current state plus the API response. Add explicit
handling for stale/out-of-range pages after mutations so the selected status
and search remain intact.

### Implementation decisions and open questions

This subtask depends on the server contract and the main task’s decisions on
history push/replace behavior, debouncing, invalid URL normalization, and
empty-page handling. Do not introduce a separate client-side filtering or
pagination implementation that could diverge from server results.

### Documentation

Update an existing maintained page or README only if it documents how users
reach or share the Books discovery view. The URL query vocabulary should be
documented from the approved source of truth, not duplicated as an
independent specification.

### Task checklist

- [ ] Confirm the server response and URL-state decisions.
- [ ] Add the client query/state mapping and route synchronization.
- [ ] Add status/search/pagination controls and consistent rendering states.
- [ ] Route CRUD refreshes through the selected discovery state.
- [ ] Add component/router tests for controls, URL restore, history, and CRUD.
- [ ] Record evidence and any deviations in the parent task.

### Requirement verification

Mount the real Books component with controlled API responses and exercise
control changes, page transitions, empty results, initial query restoration,
back/forward navigation, and each CRUD refresh. Assert both the rendered
result and the request parameters/route query so a visually plausible but
unfiltered implementation cannot pass.

### Additional implementation verification

- Verify a route change does not trigger an update loop between the component
  and router.
- Verify rapid search changes cannot leave a stale response displayed as the
  current query.
- Verify mutation refreshes preserve the approved state even when the result
  count changes.