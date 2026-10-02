# Books discovery state across the API and page

Plan the Books collection experience for read-status filtering, title/author
search, bounded pagination, and URL-backed discovery state while preserving
the existing CRUD and unfiltered API contracts.

## Requirements checklist

- [ ] R1. The Books collection supports filtering by read status, searching
  title or author, and navigating a bounded set of pages.
- [ ] R2. The table, active discovery controls, pagination controls, and empty
  state describe the same selected view, including views with no matching
  books.
- [ ] R3. The current discovery state can be shared and restored through the
  `/books` URL, and browser back/forward navigation restores the corresponding
  controls and results without stale state.
- [ ] R4. Add, update, and delete retain their existing behavior, and every
  CRUD refresh reuses the selected discovery state so the page does not fall
  back to an unrelated collection view.
- [ ] R5. `GET /books` without discovery parameters remains compatible with
  existing consumers, and the existing POST, PUT, and DELETE behavior remains
  available.

## Requirement questions and decisions

The following public-contract questions must be answered before execution
starts; the plan does not silently choose values for them:

- What query keys and URL query keys should represent status, search, page,
  and page size? Should the client use the same names for both surfaces?
- Which status values are supported, and what is the default/all-books value?
  The likely control set is all, read, and unread, but that is not yet an
  approved contract.
- What are the default and maximum page sizes, and is the page number
  one-based? “Bounded pages” requires a defined upper bound and behavior when
  a requested page is outside the result set.
- Should search be case-insensitive, trimmed substring matching across either
  title or author, and combined with status filtering using AND semantics?
- When a URL contains an unknown, malformed, or out-of-range value, should
  the page normalize the URL, fall back locally, or surface an error?
- How should pagination metadata be added while preserving the current
  unfiltered response shape (`status` plus `books`) for existing clients?

## Workstreams

- `tasks/20260925-books-discovery/010-api-discovery-contract.md` owns the
  independently useful Flask query, selection, pagination metadata, and
  compatibility contract.
- `tasks/20260925-books-discovery/020-books-page-discovery.md` depends on the
  API contract and owns the Vue controls, route synchronization, rendering,
  client transport, and CRUD refresh behavior.

## Supporting facts

- `server/app.py` currently returns the complete module-level `BOOKS` list
  from `GET /books`; the same route handles POST, while PUT and DELETE are
  handled by `/books/<book_id>`.
- `server/query.py:list_books` currently performs no selection and returns a
  list copy.
- `client/src/api/books.js:getBooks` already accepts an optional `params`
  object, but `Books.vue` currently calls it without parameters.
- `client/src/router.js` already owns a history-mode `/books` route, while
  `Books.vue` does not currently read or write route state.
- `Books.vue` reloads after each CRUD method, but those reloads have no shared
  discovery-state input.
- Existing server tests only assert successful status codes, the component
  test only covers an empty mocked response, and
  `client/tests/books.integration.js` contains no production transport
  coverage.
- `docs/development/index.md` currently records that no book-discovery
  specification exists.

## Execution plan

Status: Draft

The implementation should keep the server-side collection selection and
pagination contract at the Flask boundary, with the client treating the
approved route query as the serialized discovery state. The API client should
forward that state to `GET /books`; the page should render only the response
for that state and use one reload path for initial loading and CRUD refreshes.
The route watcher/navigation path must also be able to restore state on direct
load and browser back/forward without leaving controls, results, or empty
state out of sync.

The two subtasks are separated by ownership: the API contract is useful to
other clients and has an independent compatibility boundary, while the page
subtask owns the user-facing connection of controls, URL state, rendering, and
mutations. The parent acceptance check remains end-to-end because both
boundaries are necessary for the requested behavior.

Ordered execution:

1. Resolve the public-contract questions above and update the affected
   subtask plans without changing the requirements.
2. Execute the API subtask: implement and test selection, search, bounded
   pagination, response metadata, and the no-parameter compatibility path.
3. Execute the page subtask: add controls and active-state rendering, bind the
   approved state to the route, support browser navigation and direct URL
   restoration, pass state through the client API, and preserve it during CRUD
   refreshes.
4. Run focused server and client tests, then perform the named
   cross-boundary smoke check against a real Flask process and the real client
   transport. The current client package has no start/build script or app
   entrypoint, so the exact browser-launch command must be established during
   execution rather than implied here.
5. Update the maintained development documentation with the final supported
   API and URL contract only after the behavior is implemented and verified.

### Implementation decisions and open questions

- Recommended direction, pending the answers above: treat the route query as
  the canonical shareable representation, derive the request parameters from
  it, and update the route through the router when controls change.
- Keep a single page-loading path that accepts the current discovery state so
  initial load, route changes, browser navigation, and CRUD refreshes cannot
  silently use different query parameters.
- Do not change mutation endpoint shapes or require discovery parameters on
  POST, PUT, or DELETE.
- Do not add a new documentation page merely to reserve a location. Update
  `docs/development/index.md` or introduce a focused page only if the
  approved contract needs more space.
- The client runtime is incomplete in this fixture; establishing a supported
  browser smoke-test command is an execution/verification task, not a reason
  to weaken the required cross-boundary check.

### Documentation

No maintained documentation changes are made during planning. During
execution, document the verified query keys, status/search semantics,
pagination metadata, URL restoration behavior, and compatibility guarantees
in the smallest existing development-documentation location. Do not describe
the target behavior as current before implementation is complete.

### Task checklist

- [ ] Resolve and record the public API/URL contract questions.
- [ ] Complete `tasks/20260925-books-discovery/010-api-discovery-contract.md`.
- [ ] Complete `tasks/20260925-books-discovery/020-books-page-discovery.md`.
- [ ] Verify the unfiltered API and all existing CRUD operations.
- [ ] Verify controls, table, active state, empty state, pagination bounds,
  direct URL restoration, and browser navigation.
- [ ] Run the real client-to-Flask discovery smoke check.
- [ ] Update maintained development documentation after verification.

### Requirement verification

- R1: direct Flask endpoint tests must exercise each approved status/search
  combination and page boundary, and the page-level tests must show the
  corresponding controls and bounded navigation.
- R2: a Vue component test must assert that the rendered rows, active
  controls, pagination state, and no-match empty state all derive from one
  selected view. A filtered empty response must be distinguished from an
  unfiltered loading/empty condition if the approved UX requires that
  distinction.
- R3: router/component tests must cover direct loading of a shared URL,
  changing controls, and back/forward navigation while checking both route
  query and rendered state.
- R4: mutation tests must invoke add, update, and delete while a non-default
  discovery view is active and assert that the subsequent request retains
  that view.
- R5: Flask tests must assert the no-parameter response remains consumable by
  the existing shape and that POST, PUT, and DELETE still succeed. The
  decisive connection check must run the actual Flask route through the
  actual client transport and page loading path; mocked API tests alone do
  not satisfy this requirement.

### Additional implementation verification

- Verify deterministic ordering so moving between pages does not produce
  unstable results.
- Verify that a mutation making the current page invalid follows the approved
  out-of-range policy and leaves the URL, controls, and table consistent.
- Verify repeated route changes do not leave stale responses visible after a
  newer discovery request completes.

## Subtasks

- [ ] `tasks/20260925-books-discovery/010-api-discovery-contract.md`
- [ ] `tasks/20260925-books-discovery/020-books-page-discovery.md`