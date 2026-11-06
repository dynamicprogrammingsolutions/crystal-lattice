# Books page discovery for larger collections

Make the Books page practical for a larger collection: read-status filtering,
title/author search, bounded pagination, and discovery state shared through the
URL. The table, active controls, empty state, browser navigation, and CRUD
refreshes must stay consistent with the selected view. Existing CRUD behavior
and unfiltered `GET /books` compatibility are preserved.

Planning only — nothing is implemented. The plans below are `Draft`.

## Requirements checklist

- [ ] Books page can filter books by read status (all / read / unread).
- [ ] Books page can search books by title or author text.
- [ ] Books page moves through bounded pages, showing the current position, with prev/next disabled at the bounds.
- [ ] The selected discovery state (read filter, search text, page) is encoded in the `/books` URL so it can be shared, restored on load, and traversed with browser Back/Forward.
- [ ] Table rows, active control states, empty state, and post-CRUD refreshes all reflect the same selected view; a delete that empties the current page steps back to the previous page.
- [ ] Existing CRUD behavior is preserved end to end: add, update, and remove still work through the Flask API and refresh the table; mutation routes, payloads, and responses are unchanged.
- [ ] Unfiltered `GET /books` (no query parameters) returns the same response as today for existing consumers.
- [ ] Maintained documentation describes the delivered discovery behavior and the `GET /books` selection contract (documentation policy in `AGENTS.md`).

## Questions and decisions

No unresolved requirement questions.

Material decisions are recorded with the plan (see
`### Implementation decisions and open questions`) and need plan approval
before execution. The most consequential:

- Decision (pending approval): unfiltered `GET /books` keeps the exact legacy
  response; any selection parameter switches to a paged response with additive
  `total` / `page` / `per_page` metadata.
- Decision (pending approval): the URL carries `read`, `q`, and `page` only;
  page size stays a client-side constant and is not shared.
- Open question: whether browser-level verification of Back/Forward is in
  scope. This fixture has no dev-serving path for it (no CORS configuration,
  no `dev` script, absolute axios base URL), so the recommendation is to treat
  the browser check as a named manual step and not expand this task into
  dev-serving work.

## Supporting details

Facts below were verified by reading the listed files; nothing has been run.

- Server: `server/app.py` serves `GET/POST /books` and `PUT/DELETE /books/<id>`
  over an in-memory `BOOKS` list. `GET /books` ignores query parameters and
  always returns `{"status": "success", "books": BOOKS}`.
- `server/query.py` holds `list_books(books)` (shallow copy, currently unused
  by `app.py`) — the natural home for selection logic.
- Client: `client/src/components/Books.vue` loads all books on mount and
  re-fetches all books with no parameters after every add/update/remove. The
  table renders title and author; the empty state is "No books found.".
- `client/src/api/books.js:getBooks(params)` already forwards query parameters
  to `GET /books`; the transport needs no structural change.
- `client/src/router.js` uses `createWebHistory` with a single `/books` route;
  query parameters are unused so far.
- Tests: `tests/test_books_api.py` (pytest, Flask test client) covers
  unfiltered GET and one CRUD cycle. `client/tests/Books.spec.js` mocks the API
  module and asserts the empty state. `client/tests/books.integration.js` is a
  placeholder with no coverage.
- Harness gaps (from file inventory, not verified by running): `client/` has
  no lockfile or `node_modules`, no vitest config, and no `jsdom`-style DOM
  dependency although `Books.spec.js` mounts components; `package.json` has
  only a `test` script. The Flask app sets no CORS headers while
  `client/src/http.js` targets the absolute `http://localhost:5000`, so a
  browser on a dev server would be CORS-blocked. In the default `python3`,
  `flask` is not installed (pytest 9.1.1 is).
- `docs/development/index.md` states "No book-discovery specification
  exists."; per the documentation policy a book-discovery specification
  belongs in `docs/development/`.

## Subtasks

- [ ] tasks/20261102-books-page-discovery/010-server-books-selection.md
- [ ] tasks/20261102-books-page-discovery/020-books-page-discovery-view.md

## Implementation plan

Status: Draft

### Design

Two results are delivered by two subtasks, split at the only boundary that
leaves an independently useful result: the selection capability of the JSON
API (usable by any client) and the end-to-end Books page discovery capability.

**1. Server selection (subtask 010).** `GET /books` gains optional selection
parameters; mutation routes are untouched.

- Parameters: `read=true|false` (case-insensitive), `q=<text>` (case-
  insensitive substring match against title or author), `page=<positive
  integer>` (default 1), `per_page=<positive integer>` (default 10, clamped to
  a maximum of 100).
- If any selection parameter is present, the response is
  `{"status": "success", "books": [<page items>], "total": <filtered total>,
  "page": <page>, "per_page": <effective per_page>}`. A page beyond the last
  returns an empty `books` list with the correct `total` and status 200.
- If no selection parameter is present, the response stays exactly today's
  `{"status": "success", "books": [all books]}` with no added fields.
- Malformed values return 400 with an error body: `read` not `true`/`false`,
  or `page`/`per_page` not a positive integer. `per_page` above 100 is clamped,
  not rejected.
- Selection logic is a pure function in `server/query.py` (filter, search,
  slice, count); `app.py` only parses and validates request args and shapes
  responses. POST/PUT/DELETE behavior is unchanged.

**2. Client discovery view (subtask 020).** `Books.vue` is rebuilt around one
view state — `{ read, q, page }` plus a constant page size — derived from the
`/books` route query, which is the single source of truth.

- Data flow: mount parses `route.query` and fetches
  `getBooks({ read, q, page, per_page })`; control changes push the normalized
  query via `router.push`; a watcher on the resolved query performs the fetch,
  so Back/Forward navigation flows through the same path; the table, active
  control states, pagination position, and empty state all render from the
  same state and the page metadata (`total`).
- CRUD consistency: add/update/remove keep their existing API calls and then
  refetch with the current selection parameters; if the current page becomes
  empty after a delete while `total > 0`, the view steps back one page through
  the same route-driven path. Books added while the active filter/search
  excludes them may remain invisible — that is the view being consistent.
- URL contract: `?read=false&q=dune&page=2`, omitting parameters at their
  defaults. Invalid URL values are normalized client-side to defaults (the
  server still validates its own API inputs).
- `client/src/api/books.js` changes only to pass selection parameters and read
  page metadata; `client/src/router.js` needs no route changes.

### Order logic, compatibility, and rollback

010 lands first and is independently shippable: it is useful to API consumers
on its own, and the strict legacy default means the current client keeps
working unchanged after 010 (a global default page size would have silently
truncated the old client's list and CRUD refreshes). 020 depends on 010's
parameters and metadata. Stop-safe milestones are therefore: after 010 (API
capability, nothing user-visible broken) and after 020 (full capability).
There is no persisted data (`BOOKS` is in-memory); the way back for each child
is reverting its commit, which also reverts its documentation claims.

### Risks

- Divergent response shapes (legacy vs selection mode) can confuse consumers;
  mitigated by a test pinning the exact legacy body and by documenting both
  modes in the specification page.
- Client test harness gaps (no DOM environment, no lockfile) may surface as
  setup work before any view evidence exists; treated as maintained test
  infrastructure, verified through the real component tests.
- The CORS/dev-serving gap blocks browser-level automation of Back/Forward;
  handled as a named manual check plus router-level and transport-level
  automated evidence, or expanded only if the open question is approved.
- Invalid or partial URL state must not crash the page; client-side
  normalization is specified above.

### Implementation decisions and open questions

Material decisions, pending approval of this plan:

- Unfiltered requests keep the byte-shape legacy response; any selection
  parameter switches to paged response with additive metadata. Alternative
  rejected: always paginate (breaks existing consumers and the old client on
  a staggered landing).
- Parameter names `read`, `q`, `page`, `per_page`, mirrored by the URL.
- `per_page` is clamped to 100 while malformed values return 400: the bound
  exists for resource safety, clamping satisfies it without punishing
  aggressive-but-valid clients.
- Out-of-range pages return 200 with an empty list (simple, stateless); the
  client steps back when it observes an emptied page.
- URL shares `read`, `q`, `page` only; page size is a client constant (10) and
  not shared state.
- User-initiated control changes create history entries (`push`) so Back
  undoes them; programmatic normalization uses `replace`.
- Client-side URL normalization resets invalid values to defaults rather than
  erroring.

Open question (scope): enable browser-level Back/Forward verification by
adding dev-serving (e.g. a `dev` script plus proxy/CORS handling)?
Recommendation: no — keep this task on the discovery capability; accept the
router-level and transport-level automated evidence plus a named manual
browser check, and treat dev-serving as separate work if wanted.

### Documentation

New `docs/development/book-discovery.md`, written incrementally by whichever
child makes its claims true: 010 adds the `GET /books` selection contract
(both response modes, validation, bounds); 020 adds the user-facing discovery
behavior (controls, empty states, URL sharing, CRUD consistency). 010 also
replaces the "No book-discovery specification exists." line in
`docs/development/index.md` with a link, in the same change. The root README's
claim remains true and is left untouched. Audience: developers consuming the
API and maintainers of the Books page.

### Task checklist

- [ ] Execute subtask 010 per its own plan and checklist.
- [ ] Execute subtask 020 per its own plan and checklist.
- [ ] Roll up requirement evidence from both children and append the parent
      completion entry.

### Requirement verification

Each parent requirement maps to one owning child; 020 owns every product
connection and holds the decisive checks through the production path.

| Requirement | Owner | Decisive evidence |
| --- | --- | --- |
| Read-status filter | 010 + 020 | 020 integration test over real HTTP: client api module against a running Flask server asserting `?read=` selection; 010 API tests pin the server side. |
| Title/author search | 010 + 020 | Same integration path with `?q=`; 010 API tests for title and author matches, case-insensitivity. |
| Bounded pagination | 010 + 020 | 010 API tests for `page`/`per_page`, clamping, out-of-range page; 020 tests for position display and disabled bounds. |
| URL share/restore + Back/Forward | 020 | Component tests through a real vue-router instance: restore from query on mount, push on control change; browser traversal via the named manual check. |
| View consistency incl. CRUD refresh | 020 | Component tests: CRUD refetch carries current selection; emptied page steps back; empty state matches selection. |
| CRUD preserved end to end | 010 + 020 | Existing pytest CRUD cycle still passes with mutation routes untouched; 020 component test keeps mutation calls and refresh intact. |
| Unfiltered API compatibility | 010 | pytest asserts the exact legacy response body for parameterless `GET /books`. |
| Documentation current | 010 + 020 | Spec page and index link reviewed in the same change as each behavior. |

Deliberately not covered: automated browser rendering and Back/Forward (named
manual check or accepted gap), visual styling, cross-origin browser transport
(CORS gap recorded), POST body validation (unchanged and untested today — no
new gap introduced), and concurrency of the in-memory store.

### Additional implementation verification

After both children: run the full server suite (`pytest`) and client suite
(`npm test`) cleanly; optionally smoke-test the dev servers manually if the
open question is approved. No other distinct material risks identified.
