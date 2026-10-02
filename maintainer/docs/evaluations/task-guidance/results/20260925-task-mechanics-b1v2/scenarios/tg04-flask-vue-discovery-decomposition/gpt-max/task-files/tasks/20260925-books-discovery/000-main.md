# Books discovery and URL state

Plan the end-to-end Books-page discovery capability: server-backed read-status
filtering, title/author search, bounded pagination, and URL-backed state that
remains coherent across rendering, navigation, and CRUD refreshes.

## Requirements checklist

- [ ] **R1 — Discovery controls:** Users can filter books by read status and
  search across title or author.
- [ ] **R2 — Bounded results:** Users can move through the available result
  pages, with page controls reflecting the first and last valid page.
- [ ] **R3 — Shareable and restorable state:** The current discovery criteria
  and page are represented in the `/books` URL, can initialize the page when
  opened directly, and are restored by browser back/forward navigation.
- [ ] **R4 — One selected view:** The active controls, table rows, pagination,
  and empty state all represent the same selected status/search/page rather
  than mixing stale local and remote state.
- [ ] **R5 — CRUD consistency:** Existing add, update, and delete behavior is
  preserved; after a mutation the collection is refreshed using the selected
  discovery view and remains valid if the result count changes.
- [ ] **R6 — Unfiltered API compatibility:** An existing no-argument
  `GET /books` caller continues to receive the current complete collection
  contract, and existing POST/PUT/DELETE behavior remains compatible.

## Scope and workstreams

The scope is the existing Books collection and its `/books` route. It includes
server-side selection and pagination, the Vue controls and rendering, Vue
Router synchronization, CRUD refetch behavior, regression coverage, and the
documentation owned by this subsystem.

Sorting, page-size selection, authentication, bulk actions, and a redesign of
the existing CRUD surface are out of scope unless the open questions below are
answered differently. The planning pass creates only task files; it does not
change application or test code.

## Unresolved requirement questions

These choices affect the public API or user-visible navigation and should be
answered before execution:

1. What exact names and values should the API and URL use for status, search,
   and page? A low-friction recommendation is one shared vocabulary such as
   `status=all|read|unread`, `q=<text>`, and `page=<positive integer>`, with a
   fixed server page size.
2. Is page size fixed for this feature, or should users be able to choose it?
   The plan assumes a fixed page size unless a selector is explicitly
   requested.
3. Should search be a case-insensitive, trimmed substring match against either
   title or author? That is the recommended interpretation of “search by title
   or author”; exact matching, tokenization, and ranking are otherwise
   unspecified.
4. How should invalid or out-of-range query values be handled, and should a
   new status/search criterion reset the page to 1? The recommended user
   experience is canonicalizing valid URL state, resetting page for new
   criteria, and returning a bounded result/page state, but the API response
   for malformed values (for example, `page=abc`) needs an explicit choice.
5. Which discovery changes should create browser-history entries? The
   recommendation is to push committed filter/search/page changes, replace
   only normalization/correction, and debounce or explicitly commit free-text
   search so every keystroke does not become a history entry.
6. The working compatibility interpretation is that no-query `GET /books`
   remains the legacy full-list response while query-bearing discovery
   requests may carry pagination metadata. Confirm whether “compatibility”
   also requires byte-for-byte preservation of the legacy JSON body, including
   rejection of additive fields.

## Supporting facts

- `client/src/components/Books.vue` currently stores only `books`, renders a
  table or `No books found.`, and refetches after `add`, `update`, and `remove`.
  It has no controls, pagination, route-state handling, or loading-state
  contract to preserve.
- `client/src/api/books.js` already exposes `getBooks(params = {})`, so the
  transport has a parameter channel without changing its public function
  signature. Mutation helpers are separate and should remain intact.
- `client/src/router.js` has a `/books` route using `createWebHistory()` but
  currently does not interpret query parameters.
- `server/app.py` returns the complete in-memory `BOOKS` list from `GET
  /books`; POST appends, PUT updates, and DELETE removes. There is no current
  query parsing or pagination metadata.
- `server/query.py` currently only returns a list copy, making it the natural
  owner for pure selection/pagination logic if the API contract is approved.
- Existing evidence is minimal: `tests/test_books_api.py` checks only basic
  status codes, `client/tests/Books.spec.js` mocks the API and checks the empty
  message, and `client/tests/books.integration.js` explicitly has no
  production transport coverage.
- No Books-discovery documentation exists. `docs/development/index.md` says
  that no discovery specification exists, and the documentation guidance has
  been reviewed before planning this public behavior.

## Subtasks

- [ ] `tasks/20260925-books-discovery/010-server-discovery-contract.md`
      — own the independently useful Flask query, selection, pagination, and
      legacy-compatibility contract.
- [ ] `tasks/20260925-books-discovery/020-books-page-discovery.md`
      — consume that contract in the Vue page and router, preserve CRUD
      refreshes, and own the decisive live API/component integration check.

## Execution plan

Status: Draft

The API subtask owns data selection and the public HTTP compatibility boundary.
The Books-page subtask owns the route query as the canonical discovery state,
the visible controls, and the rendering derived from the current response.
The page should not independently filter a previously fetched array: one
normalized state should determine the API request, active controls, table,
pagination, and empty state. A query-bearing request should return enough
metadata to determine the bounded page controls. The no-query legacy request
must remain available for existing clients.

When a mutation completes, the page will refetch using the current selected
state. If deletion or another mutation makes the current page invalid, the
approved out-of-range policy will determine the canonical page and URL update;
the controls and rendered rows must then be updated from that same response.
The router-driven path must be tested with a live Flask process and the real
client transport so the decisive check crosses component, router, HTTP, and
server selection boundaries together.

### Implementation decisions and open questions

- The parent is decomposed by independently owned boundary, not by making
  tests or documentation standalone subtasks. The server contract can serve
  future clients, while the Vue task owns the user-facing connection.
- The URL is the proposed source of truth for restorable discovery state; local
  component state may hold the latest response and request status but must not
  silently diverge from the route.
- The exact parameter names, response envelope, fixed page size, search
  matching, malformed-query behavior, history granularity, and byte-level
  legacy compatibility remain open questions listed above. Execution should
  return to Draft if any answer changes the requirements.

### Documentation

After implementation, add the smallest maintained developer-facing page for
the discovery contract, likely `docs/development/books-discovery.md`, and link
it from `docs/development/index.md`. It should document the approved API query
parameters and metadata, URL restoration/history behavior, pagination bounds,
CRUD refresh semantics, and the preserved no-query contract. No current user
guidance should claim this behavior until the implementation and verification
are complete.

### Task checklist

- [ ] Resolve the material contract questions and update this Draft plan.
- [ ] Execute `010-server-discovery-contract.md` and record HTTP-boundary
      evidence.
- [ ] Execute `020-books-page-discovery.md`, including the real Flask-backed
      component/router integration check.
- [ ] Update maintained documentation through its source boundary.
- [ ] Run the required server, client, and cross-layer checks, then update
      requirement evidence and completion status.

### Requirement verification

- **R1–R2:** The decisive check is the live-API Books integration test owned by
  `020-books-page-discovery.md`, asserting that selected controls produce the
  real request, the table renders the returned page, and first/last page
  controls are bounded. Server route tests provide focused selection evidence.
- **R3–R4:** The mounted Books/router integration coverage starts from a
  populated query URL, changes discovery state, exercises router back/forward,
  and verifies that controls, rows, pagination, and empty state all follow the
  restored route.
- **R5:** The same production-path integration coverage performs or invokes
  add/update/delete through the existing client helpers, then verifies the
  selected query is used for each refresh and the resulting page remains
  coherent. Existing mutation assertions remain regression evidence.
- **R6:** `tests/test_books_api.py` must assert the no-query response and
  mutation behavior through Flask’s real route, with no discovery query
  required for legacy callers.