# Make the Books page practical for larger collections

Plan the end-to-end discovery experience for the Vue Books page and its Flask JSON API: read-status filtering, title/author search, bounded pagination, URL sharing/restoration, and consistent rendering and refresh behavior.

## Requirements checklist

- [ ] Users can filter books by read status and search by title or author.
- [ ] Results move through bounded pages with controls that reflect the available result set.
- [ ] The current discovery state can be shared and restored through the Books URL.
- [ ] Browser back/forward navigation restores the corresponding discovery state and results.
- [ ] The table, active controls, and empty state describe the selected view, including filtered/search views with no matches.
- [ ] Existing add, update, and delete behavior remains available, and each CRUD refresh reflects the selected discovery state.
- [ ] `GET /books` without discovery parameters remains compatible with the existing unfiltered API response and existing CRUD routes remain compatible.

## Unresolved requirement questions

These questions affect public API or user-visible behavior and need approval before the plan becomes executable:

- What page size and parameter model should the API and URL use (`page` plus `per_page`, or an equivalent), and should the page size be fixed or user-selectable?
- What exact read-status values should be exposed (for example, `all`, `read`, and `unread`) and what search matching is required (recommended: case-insensitive substring matching across title and author)?
- What should happen when a URL names a page beyond the available result set, especially after deleting the last item on the current page: clamp to the final page, return an empty page, or redirect/canonicalize?
- Should changing a control create a browser-history entry, and should restoration/canonicalization preserve unknown or invalid query parameters?
- Should the API add pagination metadata alongside the existing `status` and `books` fields for all responses, only discovery responses, or another backward-compatible shape?

## Research and supporting facts

- `client/src/components/Books.vue` currently loads the complete collection on mount and after each mutation; it has no controls, pagination state, or router integration.
- `client/src/api/books.js` already exposes `getBooks(params = {})`, so the transport entry point can carry discovery parameters without changing its call shape.
- `client/src/router.js` has a `/books` route using `createWebHistory()` but no query-state policy.
- `server/app.py` currently returns the complete `BOOKS` list from `GET /books` and uses the same route for `POST`; `PUT` and `DELETE` are separate and should retain their current response contracts.
- `server/query.py` currently only copies the collection, making it the natural owner for reusable filtering, search, and page selection logic.
- Existing tests only assert API status codes and an unfiltered empty component state. `client/tests/books.integration.js` explicitly has no production transport integration coverage.

## Subtasks

- [ ] `tasks/20260925-books-discovery/010-api-discovery-contract.md`
- [ ] `tasks/20260925-books-discovery/020-books-page-discovery-state.md` — Depends On: `tasks/20260925-books-discovery/010-api-discovery-contract.md`

## Execution plan

Status: Draft

The implementation should establish one stable discovery contract across the route, client transport, component state, and server selection:

1. Resolve the public query and URL decisions above, then document the approved contract in the two child tasks before execution.
2. Implement and test server-side selection as a pure query operation used by the Flask route. Optional discovery parameters must be additive: requests without them retain the current unfiltered envelope and ordering, while discovery responses provide enough metadata for bounded navigation.
3. Have the client pass the selected discovery state through `getBooks`, treat the route query as the restorable source of truth, and render controls, rows, pagination bounds, active values, and no-match messaging from the latest response.
4. Make route-query changes trigger the same fetch path as initial loading. CRUD methods must refresh using the current route state; if the result set changes the page must be reconciled according to the approved out-of-range rule.
5. Preserve the existing mutation calls and response expectations, and verify the full connection with server route tests, focused component tests, and a real transport integration check that mounts the Books component while talking to a running Flask API.

The parent owns cross-boundary acceptance and the two child tasks own their implementation details. No separate task is created for documentation or cleanup because those are part of the owning delivery.

### Implementation decisions and open questions

- The work is intentionally decomposed into an independently useful API contract and an end-to-end Books page delivery; URL state is kept with the page state because navigation, rendering, and CRUD refreshes must share one source of truth.
- The API must preserve the no-parameter `GET /books` contract and existing mutation routes. The exact additive metadata shape remains an approval question.
- The exact query names, page size, matching semantics, history behavior, and out-of-range policy remain unresolved above. Do not mark this plan Approved until they are answered.

### Documentation

- During execution, update the maintained developer documentation owned by `docs/development/`: replace the current “No book-discovery specification exists” placeholder with the verified API and URL behavior, or add one focused Books discovery page and link it from `docs/development/index.md` if the contract needs more detail.
- Do not document target behavior as current until the API, page, navigation, and CRUD refresh checks pass.

### Task checklist

- [ ] Resolve the requirement questions and update this draft plus both child plans.
- [ ] Approve the execution plan before implementation begins.
- [ ] Complete `010-api-discovery-contract.md`.
- [ ] Complete `020-books-page-discovery-state.md`.
- [ ] Update maintained documentation with verified behavior.
- [ ] Run the parent-level cross-boundary acceptance checks and record evidence.

### Requirement verification

- Read-status filtering, title/author search, and unfiltered compatibility: server route tests exercising real `GET /books` requests with and without query parameters.
- Bounded pagination and selected-view empty behavior: a real API-backed Books page integration check covering first/last-page bounds and a no-match query, supplemented by focused rendering tests for exact control states.
- URL sharing/restoration and browser navigation: a router-mounted Books page test that starts from a URL, changes discovery controls, and traverses back/forward while asserting both route query and rendered rows.
- CRUD consistency: the API-backed page integration check creates, updates, and deletes records while a non-default discovery query is active, asserting the refreshed result set and active controls.
- Preservation of existing CRUD/API behavior: existing server mutation tests plus an unparameterized `GET /books` assertion that checks the legacy envelope and collection behavior.