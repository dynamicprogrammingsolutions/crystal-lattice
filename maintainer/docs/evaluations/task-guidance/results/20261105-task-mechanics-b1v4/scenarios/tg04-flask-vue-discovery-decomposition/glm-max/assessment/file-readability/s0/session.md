# Session — tg04-flask-vue-discovery-decomposition · file-readability-assessment-glm-max-s0 · glm max

- Run: `20261102T102800.469473Z-task-guidance-file-readability-tg04-flask-vue-discovery-decomposition-glm-max-s0-f50dcd49`
- Model: glm-5.3-flash (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-c440c4f661a7.md) — captured (original SHA-256 `690b500e79aa3366…`)
- Config: [glm-assessor-max](../../../../../../shared/configs/glm-assessor-max.json)
- Activity: 3 messages · 0 tool calls · 0 tool results
- Usage: 0 input · 0 cached · 0 output · provider cost $0.0000000

## Transcript

**User**

Assess how easily a human reader can work with the task files below.
You are that reader: a maintainer who must find, understand, and act on
what the files say. Judge every top-level section that is present; do
not invent sections that are absent, and do not grade files or sections
that do not appear.

Grade each present top-level section `readable`, `partial`, or
`unreadable`: can a reader take in that section's content with
reasonable effort — scan it, hold it, and use it? A section is
`unreadable` when a reader must re-read dense prose or wall-like list
items to extract what matters; `partial` when parts strain the reader.

Then grade the whole file's navigation `navigable`, `partial`, or
`confusing`: can a reader find the thing they are looking for — the
outcome, the constraint, the open question, the plan status — from the
file's structure alone?

Measured structure facts are provided per section; anchor on these
numbers rather than impressions. They are facts, not rules: no shape is
banned or required. Formatting elements — tables, ordered lists, code
snippets, short paragraphs — are tools among many; what is graded is
the reader's experience, never the presence of a specific element.

Every grade carries findings: concrete `{where, quote, why}` items. A
non-top grade with empty findings is invalid. Then hunt for
presentation mistakes explicitly — prose walls, list items that mix
several facts, buried load-bearing facts, headings that do not match
their content, walls of unchecked boxes — and list each as
`{where, quote, why}` in `mistakes`.

Depth must match impact: a short section is not a defect; a dense
section is not automatically one either. Verbosity is not rewarded;
brevity that loses nothing is not penalized.

Return JSON only:

{
  "schema_version": 1,
  "scenario_id": "tg04-flask-vue-discovery-decomposition",
  "assessment": {
    "sections": {
      "SECTION TITLE": {
        "grade": "readable|partial|unreadable",
        "findings": [{"where": "...", "quote": "...", "why": "..."}]
      }
    },
    "navigation": {"grade": "navigable|partial|confusing", "findings": []},
    "mistakes": [{"where": "...", "quote": "...", "why": "..."}],
    "summary": "concise evidence-based interpretation"
  }
}

`sections` contains exactly the top-level sections listed in the
measured facts, keyed by the exact Section values of that table
(`<file path> — <section title>`), so multi-file task sets stay
addressable.

What these files are for:

# Flask/Vue book discovery decomposition

Partition a large full-stack release into a few end-to-end product capabilities rather than technical phases.

Category: decomposition

Measured structure facts (per file, per top-level section):

#### tasks/20261102-books-page-discovery/000-main.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261102-books-page-discovery/000-main.md — Requirements checklist | 181 | 0 | 0 | 8 | 29 | 0 | 0 | 0 | 4 |
| tasks/20261102-books-page-discovery/000-main.md — Questions and decisions | 128 | 2 | 23 | 3 | 12 | 0 | 0 | 0 | 9 |
| tasks/20261102-books-page-discovery/000-main.md — Supporting details | 233 | 1 | 13 | 8 | 12 | 0 | 0 | 0 | 30 |
| tasks/20261102-books-page-discovery/000-main.md — Subtasks | 8 | 0 | 0 | 2 | 1 | 0 | 0 | 0 | 0 |
| tasks/20261102-books-page-discovery/000-main.md — Implementation plan | 1216 | 10 | 93 | 23 | 15 | 8 | 10 | 0 | 48 |

#### tasks/20261102-books-page-discovery/010-server-books-selection.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261102-books-page-discovery/010-server-books-selection.md — Requirements checklist | 226 | 0 | 0 | 8 | 11 | 0 | 0 | 0 | 23 |
| tasks/20261102-books-page-discovery/010-server-books-selection.md — Supporting details | 123 | 0 | 0 | 5 | 14 | 0 | 0 | 0 | 12 |
| tasks/20261102-books-page-discovery/010-server-books-selection.md — Implementation plan | 418 | 4 | 92 | 11 | 12 | 7 | 0 | 0 | 20 |

#### tasks/20261102-books-page-discovery/020-books-page-discovery-view.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261102-books-page-discovery/020-books-page-discovery-view.md — Requirements checklist | 321 | 0 | 0 | 11 | 13 | 0 | 0 | 0 | 6 |
| tasks/20261102-books-page-discovery/020-books-page-discovery-view.md — Supporting details | 148 | 0 | 0 | 6 | 10 | 0 | 0 | 0 | 11 |
| tasks/20261102-books-page-discovery/020-books-page-discovery-view.md — Implementation plan | 678 | 5 | 144 | 18 | 14 | 7 | 0 | 0 | 19 |

The produced task files:

### tasks/20261102-books-page-discovery/000-main.md

````markdown
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
````

### tasks/20261102-books-page-discovery/010-server-books-selection.md

````markdown
# Server: `GET /books` selection parameters

Add optional selection parameters to `GET /books` — read-status filter,
title/author search, and bounded pagination — while keeping the unfiltered
response and all mutation behavior exactly as today. This is the data-selection
layer of the book-discovery capability and is independently useful to API
consumers.

Parent Task: tasks/20261102-books-page-discovery/000-main.md

Depends On: none. This subtask lands first; the unfiltered default keeps the
current client working until subtask 020 lands.

## Requirements checklist

- [ ] `GET /books` accepts optional `read` (`true`/`false`, case-insensitive),
      `q` (case-insensitive substring match against title or author), `page`
      (positive integer, default 1), and `per_page` (positive integer, default
      10, clamped to a maximum of 100).
- [ ] When any selection parameter is present, the response is
      `{"status": "success", "books": [<page items>], "total": <filtered
      total>, "page": <page>, "per_page": <effective per_page>}`; a page
      beyond the last returns an empty `books` list with the correct `total`
      and status 200.
- [ ] When no selection parameter is present, the response is unchanged:
      `{"status": "success", "books": [all books]}` with no added fields.
- [ ] Malformed values return 400 with an error body: `read` not
      `true`/`false`, or `page`/`per_page` not a positive integer. `per_page`
      above 100 is clamped, not rejected.
- [ ] `POST /books`, `PUT /books/<id>`, and `DELETE /books/<id>` behavior and
      responses are unchanged.
- [ ] Selection logic (filter, search, slice, count) is a pure function in
      `server/query.py`; `app.py` only parses and validates request args and
      shapes responses.
- [ ] API tests cover: the exact legacy unfiltered body, each parameter alone,
      combined parameters, per_page clamping, out-of-range page, each 400
      case, and the existing CRUD cycle still passing.
- [ ] `docs/development/book-discovery.md` exists with the selection contract
      section, and `docs/development/index.md` links it in place of the
      "No book-discovery specification exists." line, in the same change as
      the code.

## Supporting details

- `server/app.py` currently returns `{"status": "success", "books": BOOKS}`
  for all GET requests and ignores query parameters; `BOOKS` is an in-memory
  list of `{"id", "title", "author", "read"}` dicts.
- `server/query.py:list_books(books)` returns a shallow copy and is not called
  by `app.py`. Extending this module keeps selection testable without HTTP.
- `tests/conftest.py` provides the Flask test client via `app.test_client()`;
  `tests/test_books_api.py` covers unfiltered GET and one CRUD cycle.
- The current client calls `GET /books` with no parameters on mount and after
  every mutation, so the legacy default is what keeps it working between this
  subtask and subtask 020.
- Fixture note: `flask` is not installed in the default `python3` (pytest
  9.1.1 is); the executor must use the project environment or install
  dependencies before running the suite.

## Implementation plan

Status: Draft

### Approach

Add a pure selection function to `server/query.py`, roughly
`select_books(books, *, read=None, q=None, page=1, per_page=10) -> tuple[list, int]`
returning the page items and the filtered total. Keep the existing
`list_books` helper untouched. In `app.py`, parse `request.args` for the four
parameters, validate them (400 on malformed `read`/`page`/`per_page`, clamp
`per_page` to 100), and choose the response mode: if any of the four
parameters is present, return the paged body with metadata; otherwise return
today's body unchanged. The "any parameter present" trigger — not "any filter
value set" — is what keeps the compatibility boundary unambiguous.

### Steps

1. Add the selection function in `server/query.py` with filter, case-
   insensitive substring search, slice, and count.
2. Wire `app.py` GET parsing, validation, and both response modes; leave all
   mutation routes untouched.
3. Extend `tests/test_books_api.py` with the coverage listed in the
   requirements, including a test pinning the exact legacy body.
4. Create `docs/development/book-discovery.md` with the API selection
   contract (both response modes, validation, bounds) and update
   `docs/development/index.md` to link it.
5. Run the server suite and confirm all tests, including the pre-existing
   ones, pass.

### Risks and the way back

- A wrong default (e.g. globally applied page size) would silently truncate
  the current client's list; the pinned legacy-body test guards this.
- Response-shape divergence can confuse API consumers; both modes are
  documented in the same change.
- No persisted data exists; rollback is reverting this subtask's commit,
  which also reverts its documentation claims.

### Implementation decisions and open questions

Mirrors the parent plan (pending overall approval): parameter names and
defaults; strict legacy response when no selection parameter is present;
clamp-`per_page`-but-400-malformed; 200-with-empty-list for out-of-range
pages; selection logic pure in `server/query.py`. No subtask-local open
questions.

### Documentation

Owned by this subtask: creation of `docs/development/book-discovery.md` with
the selection contract, and the `docs/development/index.md` link update — both
in the same reviewed change as the code. Audience: developers consuming the
API.

### Task checklist

- [ ] Selection function added in `server/query.py`; `app.py` wired for both
      response modes; mutation routes untouched.
- [ ] API tests added per the requirements checklist; full suite passes.
- [ ] Specification page created and index link updated.

### Requirement verification

pytest through the Flask test client is the decisive evidence: it crosses the
real routing, parsing, validation, and selection path of the app in one run.
The legacy-body test pins unfiltered compatibility; parameterized tests pin
filtering, search, paging, clamping, and the 400 cases; the existing CRUD
test proves mutations are preserved. This deliberately does not cover real
network transport (covered at the next boundary by subtask 020's integration
test), client rendering, or POST body validation (unchanged and untested
today; no new gap introduced).
````

### tasks/20261102-books-page-discovery/020-books-page-discovery-view.md

````markdown
# Books page: discovery view with URL-shared state

Rebuild the Books page around a URL-driven view state: read-status filter,
title/author search, and bounded pagination, with the table, active controls,
empty state, browser navigation, and CRUD refreshes all consistent with the
selected view. This subtask owns the end-to-end product connection and holds
the decisive checks for the parent capability.

Parent Task: tasks/20261102-books-page-discovery/000-main.md

Depends On: tasks/20261102-books-page-discovery/010-server-books-selection.md
(the view needs the selection parameters and page metadata).

## Requirements checklist

- [ ] Controls set the selected view: a read-status filter (all / read /
      unread), a search input matching title or author text, and pagination
      controls showing the current position with prev/next disabled at the
      bounds.
- [ ] The table shows exactly the books of the current page for the selected
      view as returned by the API.
- [ ] The empty state reflects the selected view: a filter/search selection
      with no matches shows a no-matches message; an empty unfiltered
      collection keeps "No books found.".
- [ ] The selected view is encoded in the `/books` query (`read`, `q`, `page`,
      with defaults omitted) so a pasted URL restores the same view on load.
- [ ] User-initiated control changes create history entries; browser
      Back/Forward move between previous discovery states and the table and
      controls follow.
- [ ] After add/update/delete the table refreshes using the current selection;
      a delete that empties the current page steps back one page; a book added
      while the active filter/search excludes it may remain invisible
      (consistent with the view).
- [ ] Existing CRUD behavior is preserved: the add/update/remove API calls and
      the refresh-after-mutation flow still work; API module changes are
      limited to passing selection parameters and reading page metadata.
- [ ] Component tests cover: restoring the view from URL parameters on mount,
      control changes updating the route and refetching with selection
      parameters, table and empty-state rendering, pagination bounds, and CRUD
      refresh with the current selection including the page step-back.
- [ ] An integration test over real HTTP — the client API module against a
      running Flask server — proves selection parameters and page metadata
      cross the transport boundary, replacing the placeholder in
      `client/tests/books.integration.js`.
- [ ] Component and integration evidence runs cleanly via the client test
      script.
- [ ] `docs/development/book-discovery.md` gains the user-facing discovery
      behavior section (controls, empty states, URL sharing, CRUD
      consistency) matching delivered behavior, in the same change.

## Supporting details

- `client/src/components/Books.vue` currently loads all books on mount and
  re-fetches all books with no parameters after each mutation; the empty
  state is "No books found.".
- `client/src/api/books.js:getBooks(params)` already forwards query
  parameters; no structural transport change is needed.
- `client/src/router.js` uses `createWebHistory` with a single `/books` route;
  query parameters are unused so far, and vue-router 4 is already a
  dependency.
- `client/tests/Books.spec.js` mocks the API module and asserts the empty
  state; it mounts components, but the harness has no DOM environment
  configured (no vitest config, no jsdom/happy-dom dependency) and no
  lockfile — setup is part of this subtask's plan.
- `client/tests/books.integration.js` is a placeholder with no coverage.
- Fixture constraints: `client/src/http.js` targets the absolute
  `http://localhost:5000`, the Flask app sets no CORS headers, and
  `package.json` has only a `test` script — so a browser-level check needs
  dev-serving decisions that are out of scope unless the parent's open
  question is approved.

## Implementation plan

Status: Draft

### Approach

`Books.vue` holds one view state — `{ read, q, page }` plus a constant page
size (10) — derived from the `/books` route query, which is the single source
of truth. Mount parses and normalizes `route.query` (invalid values reset to
defaults) and fetches `getBooks({ read, q, page, per_page })`. Control changes
push the normalized query with `router.push`; a watcher on the resolved query
performs the fetch, so Back/Forward traversal flows through the same path as
control changes. The table, active control states, pagination position, and
empty state all render from that state plus the `total` metadata. CRUD methods
keep their existing mutation calls and then refetch through the same
selection-driven path; when a delete empties the current page while
`total > 0` and `page > 1`, the view steps back one page via the route.
Normalization uses `router.replace` so it does not spam history.

### Steps

1. Complete the minimal test harness: install client dependencies, add a DOM
   environment (jsdom) with a vitest config, and confirm the existing
   `Books.spec.js` still passes.
2. Introduce the view state and the route-query-driven fetch; render the
   table from the page items and keep the unfiltered empty state.
3. Add the read-status, search, and pagination controls with active states,
   bounds, and empty-state messaging for filtered selections.
4. Add URL sync (push on user changes, replace for normalization) and
   Back/Forward support through the route watcher.
5. Make CRUD refreshes selection-consistent with the step-back rule.
6. Replace `client/tests/books.integration.js` with a real-HTTP integration
   test that starts the Flask server and exercises selection parameters and
   page metadata through the client API module.
7. Add the user-facing section to `docs/development/book-discovery.md`.
8. Run the client suite and the server suite; perform the named manual check
   or record it as blocked (see verification).

### Risks and the way back

- URL/router edge cases (invalid or partial query values) could crash or
  desync the view; client-side normalization is specified and tested.
- The browser-level Back/Forward check is blocked by the fixture's CORS and
  dev-serving gap; the evidence split below keeps automated coverage at the
  router and transport boundaries and names the manual step explicitly.
- Harness setup may uncover tooling quirks (jsdom versions, axios in node);
  the harness is maintained test infrastructure verified through the real
  component tests.
- No persisted data and no server changes in this subtask; rollback is
  reverting this subtask's commit, which also reverts its documentation
  section.

### Implementation decisions and open questions

Mirrors the parent plan (pending overall approval): URL carries `read`, `q`,
`page` only with page size as a client constant; push for user-initiated
changes and replace for normalization; client-side normalization resets
invalid URL values to defaults; step-back rule for emptied pages. No
subtask-local open questions; the parent's dev-serving open question gates
only the optional browser check.

### Documentation

Owned by this subtask: the user-facing discovery behavior section of
`docs/development/book-discovery.md`, written in the same reviewed change as
the view code. Audience: maintainers of the Books page and users of its
documented behavior.

### Task checklist

- [ ] Harness completed and existing spec passing.
- [ ] View state, fetch wiring, table, controls, pagination, and empty states
      implemented per requirements.
- [ ] URL sync and Back/Forward working through the route-driven fetch.
- [ ] CRUD refreshes selection-consistent with step-back.
- [ ] Component tests and real-HTTP integration test added; both suites pass.
- [ ] Documentation section added.

### Requirement verification

Component tests run through a real vue-router instance (mocked API module) —
decisive for URL restore on mount, control-to-route-to-fetch flow, pagination
bounds, empty-state consistency, and CRUD refresh with the current selection;
the mocked transport is acceptable there because the transport boundary is
covered separately. The real-HTTP integration test (client API module against
a running Flask server) is decisive for selection parameters and page metadata
crossing the production transport. For the full browser traversal
(rendering plus Back/Forward in a real browser), the named check is manual:
start the API (`flask --app server.app run`) and a dev server, open
`/books?read=false&q=dune&page=1`, confirm table/controls/empty-state
consistency, then use Back/Forward; record the result or the blocking reason
(the CORS/dev-serving gap) in implementation notes.

Deliberately not covered: visual styling, cross-origin browser transport, and
any server behavior (owned by subtask 010).
````


**Assistant** *(reasoning present)*

{
  "schema_version": 1,
  "scenario_id": "tg04-flask-vue-discovery-decomposition",
  "assessment": {
    "sections": {
      "tasks/20261102-books-page-discovery/000-main.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "fifth of 8 items (longest, 29 words)",
            "quote": "Table rows, active control states, empty state, and post-CRUD refreshes all reflect the same selected view; a delete that empties the current page steps back to the previous page.",
            "why": "Two facts share one item via a semicolon, but both belong to the single consistency requirement; every item stays single-requirement, so the 181-word checklist scans in one pass."
          }
        ]
      },
      "tasks/20261102-books-page-discovery/000-main.md — Questions and decisions": {
        "grade": "readable",
        "findings": [
          {
            "where": "third bullet",
            "quote": "Open question: whether browser-level verification of Back/Forward is in scope. This fixture has no dev-serving path for it (no CORS configuration, no `dev` script, absolute axios base URL), so the recommendation is to treat the browser check as a named manual step",
            "why": "One item bundles the question, its fixture evidence, and the recommendation; the 'Open question:' label keeps it findable and the 128-word section still reads in one pass, but the reader must parse the whole bullet to separate the three parts."
          }
        ]
      },
      "tasks/20261102-books-page-discovery/000-main.md — Supporting details": {
        "grade": "readable",
        "findings": [
          {
            "where": "'Harness gaps' bullet",
            "quote": "`client/` has no lockfile or `node_modules`, no vitest config, and no `jsdom`-style DOM dependency although `Books.spec.js` mounts components; `package.json` has only a `test` script.",
            "why": "This one bullet chains three environment clusters (client harness, CORS/dev-serving, Python interpreter) where the other seven bullets each cover exactly one subject; parseable from the semicolons, but it is the section's only slow spot."
          }
        ]
      },
      "tasks/20261102-books-page-discovery/000-main.md — Subtasks": {
        "grade": "readable",
        "findings": [
          {
            "where": "whole section (8 words, 2 items)",
            "quote": "- [ ] tasks/20261102-books-page-discovery/010-server-books-selection.md",
            "why": "Two checkbox links to the child files and nothing else; the brevity loses nothing because each child carries its own plan."
          }
        ]
      },
      "tasks/20261102-books-page-discovery/000-main.md — Implementation plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "Design, 'Data flow' bullet",
            "quote": "mount parses `route.query` and fetches `getBooks({ read, q, page, per_page })`; control changes push the normalized query via `router.push`; a watcher on the resolved query performs the fetch, so Back/Forward navigation flows through the same path; the table, active control states, pagination position, and empty state all render from the same state",
            "why": "Four behaviors are chained by semicolons in one item; each clause is a distinct labeled step so it stays usable, but it needs slower reading than the neighboring one-fact bullets."
          },
          {
            "where": "Order logic, compatibility, and rollback",
            "quote": "010 lands first and is independently shippable... Stop-safe milestones are therefore: after 010 (API capability, nothing user-visible broken) and after 020 (full capability). There is no persisted data (`BOOKS` is in-memory)",
            "why": "Ordering rationale, stop-safe milestones, and rollback share one ~93-word paragraph; a reader looking up only the rollback must read past the ordering argument to reach it."
          },
          {
            "where": "Requirement verification",
            "quote": "| Requirement | Owner | Decisive evidence |",
            "why": "The 8-row requirement-to-owner-to-evidence table is the section's strongest scanning aid, and the 'Status: Draft' first line answers the most common lookup immediately; overall the 1,216 words stay workable because eight labeled subsections chunk them."
          }
        ]
      },
      "tasks/20261102-books-page-discovery/010-server-books-selection.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "first item",
            "quote": "`GET /books` accepts optional `read` (`true`/`false`, case-insensitive), `q` (case-insensitive substring match against title or author), `page` (positive integer, default 1), and `per_page` (positive integer, default 10, clamped to a maximum of 100).",
            "why": "Four parameter definitions share one item, but each is a parenthetical attached to its own parameter and the 23 code spans keep values greppable; one pass is enough."
          }
        ]
      },
      "tasks/20261102-books-page-discovery/010-server-books-selection.md — Supporting details": {
        "grade": "readable",
        "findings": [
          {
            "where": "last bullet",
            "quote": "Fixture note: `flask` is not installed in the default `python3` (pytest 9.1.1 is); the executor must use the project environment or install dependencies before running the suite.",
            "why": "An execution blocker sits as the section's final item, but the 'Fixture note:' label surfaces it and the other four bullets each cover exactly one file or fact."
          }
        ]
      },
      "tasks/20261102-books-page-discovery/010-server-books-selection.md — Implementation plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "Approach",
            "quote": "The \"any parameter present\" trigger — not \"any filter value set\" — is what keeps the compatibility boundary unambiguous.",
            "why": "The ~92-word Approach paragraph is sequential (function, wiring, response-mode choice) with one point per sentence, and its load-bearing compatibility rule gets its own closing sentence instead of being buried; the seven subsections keep the whole section navigable."
          }
        ]
      },
      "tasks/20261102-books-page-discovery/020-books-page-discovery-view.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "sixth of 11 items",
            "quote": "After add/update/delete the table refreshes using the current selection; a delete that empties the current page steps back one page; a book added while the active filter/search excludes it may remain invisible (consistent with the view).",
            "why": "Three behaviors share the CRUD-consistency item; the semicolons keep them separable and the remaining ten items are single-requirement, so the 321-word checklist still scans with reasonable effort."
          }
        ]
      },
      "tasks/20261102-books-page-discovery/020-books-page-discovery-view.md — Supporting details": {
        "grade": "readable",
        "findings": [
          {
            "where": "last bullet",
            "quote": "`client/src/http.js` targets the absolute `http://localhost:5000`, the Flask app sets no CORS headers, and `package.json` has only a `test` script",
            "why": "Three fixture constraints plus a scope consequence are compressed into one item; readable, but the reader must assemble the causal chain rather than see it laid out."
          }
        ]
      },
      "tasks/20261102-books-page-discovery/020-books-page-discovery-view.md — Implementation plan": {
        "grade": "partial",
        "findings": [
          {
            "where": "Approach",
            "quote": "`Books.vue` holds one view state — `{ read, q, page }` plus a constant page size (10) — derived from the `/books` route query, which is the single source of truth. ... Normalization uses `router.replace` so it does not spam history.",
            "why": "A ~144-word paragraph carries six distinct concerns (state model, mount fetch, control pushes, render inputs, CRUD step-back, history modes) with no labels; it is the plan's core and requires re-reading to separate the behaviors, whereas the parent plan presents the same design as labeled bullets that scan far faster."
          },
          {
            "where": "Requirement verification",
            "quote": "Component tests run through a real vue-router instance (mocked API module) — decisive for URL restore on mount, control-to-route-to-fetch flow, pagination bounds, empty-state consistency, and CRUD refresh with the current selection; the mocked transport is acceptable there because the transport boundary is covered separately.",
            "why": "Three evidence tiers (component, real-HTTP integration, manual browser check) are interleaved in one ~150-word prose paragraph instead of being split by tier; the reader must hold all three while working out which test proves what."
          },
          {
            "where": "Steps",
            "quote": "1. Complete the minimal test harness... 8. Run the client suite and the server suite; perform the named manual check or record it as blocked",
            "why": "Eight ordered steps with one outcome each are the section's most usable unit, confirming the density problem is localized to the Approach and verification paragraphs rather than the whole section."
          }
        ]
      }
    },
    "navigation": {
      "grade": "navigable",
      "findings": [
        {
          "where": "all three files, section skeleton",
          "quote": "Requirements checklist / Supporting details / Implementation plan",
          "why": "Every file uses the identical top-level skeleton in the same order, so a reader always knows where the outcome (title plus first paragraph), the constraints (checklist), the verified facts, and the plan live without searching."
        },
        {
          "where": "000-main Subtasks; children headers",
          "quote": "Depends On: tasks/20261102-books-page-discovery/010-server-books-selection.md",
          "why": "Subtask checkboxes plus per-file Parent and Depends On lines make the decomposition graph and landing order recoverable from structure alone."
        },
        {
          "where": "000-main intro and plan headers",
          "quote": "Planning only — nothing is implemented. The plans below are `Draft`.",
          "why": "Status is declared in the parent intro and repeated as 'Status: Draft' atop each plan, and the single open question is labeled in Questions and decisions, so outcome, status, and open question are each one glance away."
        }
      ]
    },
    "mistakes": [
      {
        "where": "000-main.md — Supporting details, 'Harness gaps' bullet",
        "quote": "`client/` has no lockfile or `node_modules`, no vitest config, and no `jsdom`-style DOM dependency although `Books.spec.js` mounts components; `package.json` has only a `test` script. The Flask app sets no CORS headers while `client/src/http.js` targets the absolute `http://localhost:5000`... In the default `python3`, `flask` is not installed (pytest 9.1.1 is).",
        "why": "One list item mixes three independent environment-gap facts, and the flask-not-installed execution blocker is the final clause of the chain; a reader hunting 'what will block me' must parse the whole bullet — sub-bullets would isolate each blocker."
      },
      {
        "where": "000-main.md — Implementation plan, Design, 'Data flow' bullet",
        "quote": "mount parses `route.query` and fetches...; control changes push the normalized query via `router.push`; a watcher on the resolved query performs the fetch...; the table, active control states, pagination position, and empty state all render from the same state",
        "why": "List item mixing several facts: four behaviors joined by semicolons in a single item, slower to hold on first read than the surrounding one-fact bullets."
      },
      {
        "where": "000-main.md — Implementation plan, 'Order logic, compatibility, and rollback'",
        "quote": "010 lands first and is independently shippable... Stop-safe milestones are therefore... There is no persisted data (`BOOKS` is in-memory); the way back for each child is reverting its commit",
        "why": "Three separately-looked-up facts (landing order, milestones, rollback) share one 93-word paragraph; any one of them as its own sentence block or bullet would be findable at a glance."
      },
      {
        "where": "020-books-page-discovery-view.md — Implementation plan, Approach",
        "quote": "`Books.vue` holds one view state... Control changes push the normalized query with `router.push`; a watcher on the resolved query performs the fetch... CRUD methods keep their existing mutation calls and then refetch through the same selection-driven path; when a delete empties the current page while `total > 0` and `page > 1`, the view steps back one page via the route. Normalization uses `router.replace` so it does not spam history.",
        "why": "Prose wall: ~144 words and six concerns in one unlabeled paragraph at the heart of the plan, forcing re-reads; the labeled-bullet treatment used for the identical design in the parent plan shows the fix."
      },
      {
        "where": "020-books-page-discovery-view.md — Implementation plan, Requirement verification",
        "quote": "Component tests run through a real vue-router instance (mocked API module) — decisive for URL restore on mount, control-to-route-to-fetch flow, pagination bounds, empty-state consistency, and CRUD refresh with the current selection; the mocked transport is acceptable there because the transport boundary is covered separately.",
        "why": "Three evidence tiers are interleaved in one ~150-word paragraph, so the decisive evidence for each requirement tier cannot be skimmed; a per-tier split (component / integration / manual) would scan directly."
      },
      {
        "where": "020-books-page-discovery-view.md — Supporting details, last bullet",
        "quote": "`client/src/http.js` targets the absolute `http://localhost:5000`, the Flask app sets no CORS headers, and `package.json` has only a `test` script — so a browser-level check needs dev-serving decisions that are out of scope",
        "why": "List item mixing several facts: three fixture constraints plus a scope conclusion in one item, repeating the same bundling pattern as the parent's harness bullet."
      },
      {
        "where": "020-books-page-discovery-view.md — Requirements checklist, sixth item",
        "quote": "After add/update/delete the table refreshes using the current selection; a delete that empties the current page steps back one page; a book added while the active filter/search excludes it may remain invisible (consistent with the view).",
        "why": "Three distinct behaviors in one checklist box blur what a checker must verify; splitting into refresh / step-back / invisibility items would make each independently checkable."
      }
    ],
    "summary": "The set is easy to navigate and mostly easy to read: all three files share one skeleton (requirements checklist, supporting details, implementation plan with a Draft status line), the parent declares 'planning only' up front, and Subtasks/Depends On lines expose the decomposition and landing order. Short sections — checklists, questions, supporting details, subtasks — scan cleanly, and the parent's 1,216-word plan stays workable because eight labeled subsections and a requirement-to-owner-to-evidence table chunk it. The recurring defect is fact-bundled units: semicolon-chained bullets (harness gaps, fixture constraints, data flow, CRUD consistency) and two prose walls in subtask 020's plan (a 144-word Approach paragraph and a ~150-word verification paragraph), which earn that section the only partial grade. The uniformly unchecked boxes are accurate to the declared planning-only status, not a stale-checkbox problem, and no heading misdescribes its content."
  }
}
