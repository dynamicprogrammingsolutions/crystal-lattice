# Books discovery, pagination, and URL state

Target outcome: make the `/books` page practical for a larger collection by
adding read-status filtering, title/author search, bounded pagination, and
shareable/restorable discovery state while keeping the rendered view, controls,
browser navigation, and CRUD refreshes synchronized. This task records a
planning-only handoff; the target behavior is not implemented.

## Requirements checklist

- [ ] The Books page lets users filter the collection by read status.
- [ ] The Books page lets users search by title or author.
- [ ] Results are presented as bounded pages with controls that cannot navigate
      beyond the available page range.
- [ ] The current discovery state can be shared and restored through the
      `/books` URL, including browser back/forward navigation.
- [ ] The table, active control values, empty state, and page controls all
      represent the same selected discovery view.
- [ ] Add, update, and delete operations preserve the selected discovery view
      when they refresh the collection, including the approved behavior when a
      mutation changes the available page range.
- [ ] Existing CRUD endpoints and behavior remain usable.
- [ ] An unfiltered `GET /books` remains compatible with the existing API
      contract.

## Scope and workstreams

This is one end-to-end task. The capability crosses server-side selection,
client transport, Vue state/rendering, and router URL state; no layer is an
independently acceptable delivery for the requested outcome. The task therefore
keeps the API, page, integration evidence, and documentation under one owner
instead of creating frontend/backend subtasks whose separate checks could miss
the production connection.

## Unresolved requirement questions

These public or user-visible choices must be answered before the Draft can
become Approved:

1. What query parameter names and values should define status, search, page,
   and page size? Should the URL expose page size, or use one fixed page size?
2. Should search be a case-insensitive substring match across either title or
   author, and what stable ordering should pagination preserve? The existing
   collection is insertion-ordered and no alternate sort is specified.
3. Should malformed or out-of-range URL values be normalized to defaults,
   rejected, or reported? After a deletion makes the current page unavailable,
   should the page clamp to the last available page and update the URL?
4. Which control changes should create browser-history entries, and should
   rapidly changing search text replace rather than accumulate entries?
5. May filtered/paginated responses add metadata while the no-parameter
   response remains exactly `{status, books}`, or is a single response shape
   required for all GET requests?

## Research and supporting facts

- `client/src/components/Books.vue` currently owns only a `books` array,
  fetches the unparameterized collection on mount, renders title and author
  rows, and shows one empty message. Its add, update, and remove methods
  re-fetch without preserving any view state.
- `client/src/api/books.js` already accepts an optional `params` object in
  `getBooks`, while the mutation helpers target the existing POST, PUT, and
  DELETE endpoints.
- `client/src/router.js` exposes `/books` with `createWebHistory()` but does
  not currently define or synchronize query state.
- `server/app.py` currently ignores `GET /books` query parameters and returns
  the full in-memory collection in `{"status": "success", "books": ...}`.
  POST, PUT, and DELETE are the existing mutation routes and must remain
  compatible.
- `server/query.py` currently contains only a pass-through `list_books`
  helper, so filtering, matching, ordering, and pagination have no existing
  selection contract to preserve.
- `client/tests/Books.spec.js` covers only the mocked empty state.
  `client/tests/books.integration.js` explicitly records that no production
  transport integration coverage exists.
- `tests/test_books_api.py` currently checks only successful GET/mutation
  status codes; it does not assert the unfiltered response shape or discovery
  semantics.
- `README.md` is the only package-level overview. `docs/development/index.md`
  states that no book-discovery specification exists, so no current discovery
  guidance needs to be preserved.

## Execution plan

Status: Draft

The proposed design keeps the existing `/books` path and CRUD routes. Optional
discovery parameters are interpreted by the server selection boundary, where
status and title/author search are applied before bounded pagination over a
stable order. A discovery response will expose enough pagination information
for the client to render and bound navigation; the exact parameter names,
defaults, metadata shape, and invalid-input policy remain open above. A
request with no discovery parameters will retain the current unfiltered
response contract unless the requirement decision explicitly changes that
compatibility rule.

On the client, the normalized route query is the durable source of discovery
state. The Books page will derive active controls and its request parameters
from that state, update the route when controls change, and watch route changes
so direct links and browser back/forward restore the same view. A single
refresh path will be shared by initial loading, route changes, and CRUD
completion so the table, empty state, pagination bounds, and controls cannot
drift apart. Mutation refreshes will retain the current query and apply the
approved out-of-range policy if the result count changes.

The plan will be executed in this order after the questions above are resolved:

1. Confirm the public query/response contract and record the decisions in this
   task. Turn each decision into API and UI acceptance cases before changing
   production code.
2. Implement the server selection boundary and optional `GET /books`
   parameters without changing the existing mutation routes or the
   no-parameter response. Add API tests for filtering, title/author matching,
   page bounds, response metadata, and the unfiltered compatibility contract.
3. Wire the client API request to the approved parameters. Make route query
   state, active controls, result rendering, empty-state messaging, and
   bounded pagination use the same normalized view and synchronize on
   navigation.
4. Route add, update, and delete completion through the same view-aware
   refresh path. Verify that CRUD behavior remains intact and that changes to
   the collection cannot leave stale rows, stale controls, or an invalid
   selected page.
5. Add focused component/router tests for local state and rendering, then a
   real transport integration test that mounts the Books component with an
   actual router and talks to the Flask endpoint rather than mocking
   `getBooks`. That test must cover a shared/restored query, back/forward
   navigation, bounded paging, an empty result, and at least one CRUD refresh.
6. Update the maintained package documentation with the verified user-facing
   discovery behavior and the optional API query contract. Do not add a
   placeholder specification or documentation directory merely for this task.
7. Run the full planned evidence, update this task's checklist and notes, and
   append immutable completion notes only after all requirements have evidence.

### Implementation decisions and open questions

- The task is intentionally one end-to-end workstream; splitting by
  frontend/API layer would make it possible for each side to pass isolated
  tests while the requested discovery connection remains broken.
- The existing no-parameter `GET /books` envelope and mutation routes are
  treated as compatibility constraints in the plan. Whether discovery
  responses add metadata alongside that envelope is still a requirement
  question, not an unapproved implementation decision.
- The URL query schema, matching semantics, stable ordering, page-size policy,
  invalid-value handling, mutation page-clamping behavior, and history-entry
  policy are all material choices listed above. They must be resolved before
  execution; the executor must not silently invent them.

### Documentation

No documentation is changed during planning. Once behavior is implemented and
verified, update `README.md` as the smallest existing package-level surface
with the supported Books discovery controls, URL-restoration behavior, and
the optional `GET /books` contract. Keep the documentation factual and
current; do not describe the target as supported before the implementation
and verification are complete. If execution discovers a more authoritative
maintained API document, update that owner in the same change instead of
duplicating the contract.

### Task checklist

- [ ] Resolve the listed requirement questions and obtain approval for this
      plan.
- [ ] Add and verify the server-side discovery contract while preserving
      unfiltered API and CRUD compatibility.
- [ ] Add client route-state, controls, results, pagination, and shared
      refresh behavior.
- [ ] Add focused client/server regression coverage and the real
      component-to-Flask transport integration check.
- [ ] Update the maintained documentation after behavior is verified.
- [ ] Run all required checks, update requirement evidence, and append
      completion notes.

### Requirement verification

No requirement is complete at planning time. The decisive evidence should be:

- The real Flask API test suite must assert status filtering, title/author
  search, bounded pagination, the approved invalid-input behavior, and the
  unchanged no-parameter response envelope. This covers the selection and
  unfiltered compatibility requirements at the HTTP boundary.
- A real client integration test must run with the Flask app listening at
  `127.0.0.1:5000`, mount `Books.vue` with a router, leave `getBooks`
  unmocked, and exercise a URL containing the selected search/status/page.
  It must change the route back and forward, assert that controls/table/empty
  state/page controls agree, and perform a mutation followed by a refresh of
  the same view. This is the decisive check for the cross-layer product
  connection; component tests with mocked API calls and direct route tests
  remain supporting evidence only.
- Focused Vue tests may isolate normalization and rendering edge cases, but
  they cannot replace the real transport check for URL restoration, server
  selection, or CRUD refresh consistency.
- Existing mutation tests, strengthened to assert the preserved endpoint
  behavior, must remain green alongside the new discovery cases.

The planned cross-layer check has this explicit invocation once the
integration test is implemented:

```text
# Terminal 1, from the repository root:
python -m flask --app server.app run --host 127.0.0.1 --port 5000

# Terminal 2, from the repository root:
npm --prefix client test -- tests/books.integration.js
```

Routine regression commands are:

```text
pytest -q
npm --prefix client test
```

### Additional implementation verification

- Check that route watchers and control updates do not create fetch/history
  loops or leave a stale response visible after a later request.
- Check deterministic ordering at page boundaries and the behavior when a
  mutation removes the final item from the current page.
- Check that an omitted discovery query takes the compatibility path rather
  than accidentally returning a different shape or applying a default filter.