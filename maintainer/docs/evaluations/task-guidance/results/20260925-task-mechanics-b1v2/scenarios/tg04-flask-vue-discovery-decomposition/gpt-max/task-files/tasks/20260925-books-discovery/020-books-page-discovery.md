# Books page discovery and URL synchronization

Connect the approved server discovery contract to the Vue Books page so the
visible controls, route URL, browser navigation, table, empty state, pagination,
and CRUD refreshes all describe one selected view.

Parent Task: `tasks/20260925-books-discovery/000-main.md`
Depends On: `tasks/20260925-books-discovery/010-server-discovery-contract.md`

## Requirements checklist

- [ ] **P1 — Practical page controls:** The Books page exposes read-status
  filtering, title/author search, and bounded previous/next or equivalent page
  navigation.
- [ ] **P2 — URL restoration and navigation:** Opening `/books` with approved
  discovery query state restores that view; user changes update the URL, and
  browser back/forward restores the corresponding request and rendered state.
- [ ] **P3 — Consistent rendering:** Active controls, table rows, pagination
  bounds, and the empty state are all derived from the same selected response
  and never leave stale results visible after a route change.
- [ ] **P4 — CRUD refreshes:** Existing `add`, `update`, and `remove` methods
  keep their current API behavior and refetch with the selected discovery
  state, including a valid response when a mutation changes the current
  page’s bounds.

## Supporting facts

- `Books.vue` currently has only a `books` array and refetches with
  parameterless `getBooks()` after every mutation. Any implementation must
  preserve those public component methods because existing consumers/tests may
  call them directly.
- `getBooks(params = {})` already forwards Axios params, while
  `addBook`, `updateBook`, and `deleteBook` are separate helpers. The client
  can add discovery serialization without changing mutation signatures.
- `router.js` uses `createWebHistory()` and defines `/books`; query state is
  therefore available to share and restore, but no watcher or normalization
  exists today.
- `Books.spec.js` mocks all API helpers and only checks the current empty
  message. `books.integration.js` is the available location for a real
  transport/component integration check but currently contains no test.

## Execution plan

Status: Draft

Use the route query as the canonical restorable discovery state. Normalize the
approved query values into one page-state model, derive the `getBooks`
parameters from that model, and render controls, rows, pagination, and empty
state from the response associated with that model. Route changes from
controls should use the approved history policy; route changes from
back/forward should be observed and fetched rather than treated as a
one-time mount concern. New status/search criteria should use the approved
page-reset policy so a previous page cannot silently describe a different
result set. Canonicalization of defaults or invalid values should update the
URL without producing a misleading extra history entry.

Keep CRUD methods and their existing mutation helpers. After each successful
mutation, refetch with the current route-derived discovery parameters. If the
response indicates that the current page is no longer valid, apply the
approved correction, update the route, and render the corrected response so
the URL, active controls, table, empty state, and page controls converge.

Extend component tests for control state, request parameters, table/empty
rendering, pagination disabling, route initialization, and router
back/forward. Then fill `client/tests/books.integration.js` with a live
Flask-backed check that mounts the actual Books component and uses the actual
`getBooks`/Axios path. Run it with the server process started by
`flask --app server.app run --port 5000` and, in the client worktree,
`npm test -- tests/books.integration.js`; this is the decisive check that
connects the Vue page, router state, client transport, HTTP route, and server
selection instead of proving each side against a mock.

### Implementation decisions and open questions

- This child owns user-visible route/query state and all UI consistency
  consequences; it does not redefine the server’s filtering semantics.
- The route is the proposed source of truth. A local response/request model is
  allowed, but it must be replaced or invalidated when the route changes.
- The exact URL vocabulary, search commit/debounce behavior, history granularity,
  page-size exposure, and out-of-range correction are inherited from the
  parent’s unresolved requirement questions. Do not silently settle a
  user-visible choice during implementation.
- The live integration test must use the real Axios base URL and a real Flask
  process. A mocked `getBooks` test remains useful for focused rendering but
  cannot be the decisive cross-layer evidence.

### Documentation

Update the maintained Books-discovery document with the user-facing control
meanings, URL examples, restore/back/forward behavior, empty and page-bound
rules, and CRUD refresh behavior. Link it from `docs/development/index.md` if
that remains the smallest appropriate documentation structure. Do not describe
the target behavior as current until the live integration check passes.

### Task checklist

- [ ] Resolve the inherited URL/history and page-state questions.
- [ ] Connect route query state to `getBooks` parameters and response state.
- [ ] Render active status/search controls, the selected table page, bounded
      pagination, and a state-consistent empty result.
- [ ] Preserve CRUD helpers and refetch/correct the selected view after
      add/update/delete.
- [ ] Expand focused component/router tests.
- [ ] Add and run the live Flask-backed component/transport integration check.
- [ ] Record documentation and requirement evidence for the parent task.

### Requirement verification

- **P1:** `Books.spec.js` should mount the real component, drive each control,
  and assert request parameters plus active control and page-control state.
- **P2:** Router-backed component tests should start from a query URL, change
  state, call back/forward, and assert a new request and restored rendering.
  The live integration test must use the production `getBooks` transport; any
  address-bar/browser-host verification remains a human check if the fixture
  has no browser runner.
- **P3:** Focused tests must cover populated, filtered, paginated, and empty
  responses and assert that the table and empty state do not retain rows from
  the previous route.
- **P4:** The live integration path or an equivalent real-component test must
  exercise add/update/delete refreshes with an active query and verify that
  the selected URL/control state remains in effect. Existing CRUD tests remain
  regression evidence, not the sole proof of discovery consistency.