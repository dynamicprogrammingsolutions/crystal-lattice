# Session — tg04-flask-vue-discovery-decomposition · file-readability-assessment-glm-max-s0 · glm max

- Run: `20260928T202053.534632Z-task-guidance-file-readability-tg04-flask-vue-discovery-decomposition-glm-max-s0-c8765720`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `7cb7c2891a4b15ae…`)
- Config: [glm-assessor-max](../../../../../../shared/configs/glm-assessor-max.json)
- Activity: 3 messages · 0 tool calls · 0 tool results
- Usage: unknown — saved session contains no provider usage metadata

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

#### tasks/20260926-books-page-discovery/000-main.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-books-page-discovery/000-main.md — Requirements checklist | 264 | 0 | 0 | 11 | 14 | 0 | 0 | 0 | 4 |
| tasks/20260926-books-page-discovery/000-main.md — Subtasks | 19 | 0 | 0 | 3 | 5 | 0 | 0 | 0 | 0 |
| tasks/20260926-books-page-discovery/000-main.md — Questions and decisions | 66 | 0 | 0 | 2 | 11 | 0 | 0 | 0 | 1 |
| tasks/20260926-books-page-discovery/000-main.md — Supporting facts (research) | 241 | 2 | 13 | 11 | 12 | 0 | 0 | 0 | 24 |
| tasks/20260926-books-page-discovery/000-main.md — Execution plan | 1102 | 7 | 72 | 28 | 15 | 6 | 0 | 0 | 34 |

#### tasks/20260926-books-page-discovery/010-server-discovery-api.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-books-page-discovery/010-server-discovery-api.md — Requirements checklist | 160 | 0 | 0 | 5 | 12 | 0 | 0 | 0 | 17 |
| tasks/20260926-books-page-discovery/010-server-discovery-api.md — Execution plan | 429 | 2 | 58 | 19 | 14 | 5 | 0 | 0 | 24 |

#### tasks/20260926-books-page-discovery/020-client-discovery-view.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-books-page-discovery/020-client-discovery-view.md — Requirements checklist | 186 | 0 | 0 | 6 | 13 | 0 | 0 | 0 | 0 |
| tasks/20260926-books-page-discovery/020-client-discovery-view.md — Execution plan | 565 | 2 | 106 | 22 | 13 | 5 | 0 | 0 | 22 |

#### tasks/20260926-books-page-discovery/030-url-share-restore.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-books-page-discovery/030-url-share-restore.md — Requirements checklist | 142 | 0 | 0 | 5 | 14 | 0 | 0 | 0 | 2 |
| tasks/20260926-books-page-discovery/030-url-share-restore.md — Execution plan | 536 | 2 | 87 | 21 | 16 | 5 | 0 | 0 | 17 |

The produced task files:

### tasks/20260926-books-page-discovery/000-main.md

````markdown
# Books page discovery (read filter, search, bounded pagination, URL state)

Make the Books page practical for a larger collection: users filter by read
status, search by title or author, move through bounded pages, and share or
restore the current discovery state through the URL, while table, active
controls, empty state, browser navigation, and CRUD refreshes stay consistent
with the selected view and existing CRUD behavior plus unfiltered API
compatibility are preserved. Planning only — execution awaits approval.

## Requirements checklist

- [ ] R1 — Books page filters books by read status (all / read / unread).
- [ ] R2 — Books page searches books by title or author (case-insensitive
      substring; a match in either field satisfies the query).
- [ ] R3 — Books page presents results in bounded pages the user can move
      through (visible bounds, no navigation past the last page).
- [ ] R4 — The current discovery state (read filter, search text, page) is
      encoded in the `/books` URL and restored when that URL is opened; the
      default view keeps a clean URL.
- [ ] R5 — Browser back/forward navigation keeps the table, active controls,
      and loaded data consistent with the URL-restored view.
- [ ] R6 — The table, active controls (filter, search, pagination), and empty
      state always reflect the selected view.
- [ ] R7 — Add/update/delete refreshes the table using the selected view
      (refetch honors the view; a page left out of range resolves to a valid
      page) without changing CRUD semantics.
- [ ] R8 — Existing CRUD behavior is preserved (POST `/books`,
      PUT/DELETE `/books/<id>` semantics unchanged).
- [ ] R9 — Unfiltered API compatibility is preserved (GET `/books` without
      discovery params returns the current envelope with the full list).
- [ ] R10 — Maintained documentation describes the shipped behavior
      (discovery specification plus README) in the same changes as the code
      (AGENTS.md documentation policy).
- [ ] R11 — Changed behavior has verification evidence at the boundaries it
      crosses: Flask HTTP API, Vue view, and the real client↔server transport
      (AGENTS.md testing policy).

## Subtasks

- [ ] tasks/20260926-books-page-discovery/010-server-discovery-api.md
- [ ] tasks/20260926-books-page-discovery/020-client-discovery-view.md (depends on 010)
- [ ] tasks/20260926-books-page-discovery/030-url-share-restore.md (depends on 010, 020)

## Questions and decisions

- No unresolved requirement questions: the requested outcomes and the two
  preserved contracts (existing CRUD behavior, unfiltered API compatibility)
  are fully specified by the request and current behavior.
- Material design decisions that define the public API contract and
  user-visible URL/UX behavior (D1–D7) are collected with recommendations in
  `### Implementation decisions and open questions` below and await approval
  together with the plan. None are resolved unilaterally.

## Supporting facts (research)

Verified in the current tree:

- `server/app.py:10-24` — GET `/books` returns `{"status": "success",
  "books": BOOKS}` (full list; no query params are read). POST/PUT/DELETE
  mutate a module-level `BOOKS` list; a missing id raises via `next()`.
- `server/query.py:1-2` — `list_books(books)` exists but is unused; it is the
  data-selection seam this capability should own.
- `client/src/api/books.js:3-5` — `getBooks(params)` already forwards query
  params to axios; CRUD helpers are unaffected.
- `client/src/components/Books.vue:17-32` — the component holds only the
  fetched `books` array, and every CRUD method refetches with paramless
  `getBooks()`, so refreshes would ignore any view.
- `client/src/router.js` — vue-router 4 in history mode, `/books` route, no
  query handling.
- `client/src/http.js:3` — axios baseURL hardcoded to `http://localhost:5000`.
- `tests/test_books_api.py` — smoke-level HTTP tests only; `tests/conftest.py`
  uses the module-level `BOOKS` list, so selection tests need deterministic
  seeding/reset.
- `client/tests/Books.spec.js` — component test mocks the API module and
  asserts only the empty state;
  `client/tests/books.integration.js` is an explicit placeholder ("No
  production transport integration coverage exists yet").
- Docs: `README.md` describes the app in one line;
  `docs/development/index.md` states "No book-discovery specification
  exists."; `docs/development/documentation.md` was read as required before
  planning doc changes.

Assumptions / risks (unverified — installing dependencies during planning is
out of scope):

- `client/package.json` declares no jsdom/happy-dom and no vitest environment
  config; the existing component spec may not run until a DOM environment is
  configured. Establish the runner baseline before extending the suite.
- No node_modules or lockfile exists in the fixture; runs require dependency
  installation at implementation time.

## Execution plan

Status: Draft

### Design

The capability is one data flow crossing four boundaries:

    URL query → view state → API params → server selection → rows + metadata → table / controls / empty state

Three slices, split by end-to-end capability rather than by mechanical layer,
per the project guidance (split only where a layer leaves an independently
useful, owned result):

1. **Server discovery API (010)** — the public API contract and its
   compatibility boundary. Independently usable by API consumers without the
   Vue client, with its own HTTP-boundary acceptance and the unfiltered
   compatibility constraint named in the request.
2. **Client discovery view (020)** — in-session browsing: controls, bounded
   pagination, view-consistent table/empty states, and CRUD refreshes that
   honor the view. Owns the first real client↔server transport integration
   evidence, which component tests with a mocked transport cannot provide.
3. **URL share/restore (030)** — the state-travels-through-URL capability:
   encode, restore, normalize, back/forward, and URL sync after CRUD/clamp.
   Depends on 020's view state.

State model: `Books.vue` owns a single reactive view object
`{ read, q, page }` with one `refresh()` path that calls
`getBooks(viewParams)` and stores rows plus pagination metadata; all CRUD
methods call `refresh()`. This shape is chosen in 020 deliberately so 030
binds the same object to the route query without reworking state.

Compatibility strategy: paramless GET `/books` keeps the exact current
envelope (R9); CRUD routes are untouched (R8); the Vue client always sends
explicit discovery params (at minimum `page`) so the page always consumes the
paginated envelope while the paramless path remains untouched for external
consumers (D3).

Verification strategy: evidence at each boundary — pytest through the Flask
test client for the API contract (010), vitest component tests with the
transport mocked for view logic (020/030), and vitest integration tests
against the real Flask server over real axios for the client↔server chain
(020) and the deep-link restore path (030). Component tests with a mocked API
are supporting evidence, never the decisive check for a connection that
crosses the transport.

### Implementation decisions and open questions

All decisions below are recommendations awaiting approval with the plan.
D1–D4 define the public API contract; D5–D7 are user-visible behavior.

- **D1 — Selection executes server-side.** GET `/books` gains optional
  `read` (`true`/`false`; absent = all), `q` (case-insensitive substring on
  title OR author), and `page` (1-based positive integer); page size is a
  fixed server constant, recommended 10. Rationale: "practical for a larger
  collection" plus the provided `server/query.py` seam; client-side
  pagination of an unbounded fetch would not scale. Rejected alternative:
  filtering the full list in the client.
- **D2 — Response envelope.** When any discovery param is present, the
  response is the current envelope plus pagination metadata:
  `{"status", "books", "page", "page_size", "total", "total_pages"}`. A
  paramless GET returns the current body unchanged — the strictest reading of
  "unfiltered API compatibility."
- **D3 — Client always sends explicit params.** The page always requests the
  paginated envelope (at minimum `page`), so it never depends on shape
  branching; the paramless path stays intact for external consumers.
- **D4 — Validation policy.** Malformed `read` or `page` values → 400;
  an out-of-range `page` → empty `books` with correct metadata (the client
  clamps using metadata; URL normalization normally prevents out-of-range
  requests).
- **D5 — URL encoding.** `/books?read=unread&q=dune&page=2`; only
  non-default params are present (`read` tokens: `read`/`unread`; `q`
  URL-encoded; `page` positive integer). Default view = clean URL.
- **D6 — Search timing and history policy.** Search applies debounced
  (~300 ms) on input; each applied filter/search/page change is a history
  `push` so back/forward walks result states; normalization on load uses
  `replace` so no spurious history entries appear. Alternative (replace for
  everything) causes less history traffic but makes back/forward useless for
  result states.
- **D7 — Empty-state distinction.** "No books found." remains the
  collection-empty state; a filtered view matching nothing shows a distinct
  no-matches message. A "clear filters" affordance is recommended as the
  escape hatch for shared filtered URLs — confirm inclusion.

### Documentation

- Audience: maintainers and developers of this app (`docs/development`) and
  README readers.
- Destination: extend `docs/development/index.md` — replace the "No
  book-discovery specification exists." line with a concise book-discovery
  specification grown by each child: API contract (010), page behavior (020),
  URL state (030). Update `README.md` as user-facing behavior lands (020
  page features; 030 shareable state).
- No new documentation directories or placeholder pages — smallest structure
  that helps the reader, per documentation policy. Each doc claim lands in
  the same change as the code that makes it true.

### Task checklist

- [ ] Execute `tasks/20260926-books-page-discovery/010-server-discovery-api.md`
      (no dependencies).
- [ ] Execute `tasks/20260926-books-page-discovery/020-client-discovery-view.md`
      (depends on 010).
- [ ] Execute `tasks/20260926-books-page-discovery/030-url-share-restore.md`
      (depends on 010 and 020).

### Requirement verification

- R1/R2 (read filter, search) → 010 owns the API contract; decisive HTTP
  tests assert param selection (read true/false, q on title and author with
  case-insensitivity, combined). 020 owns the page behavior; decisive
  end-to-end check: 020's integration test through real axios + real Flask,
  from control to selected rows.
- R3 (bounded pagination) → 010 decisive HTTP tests for totals, page
  metadata, and out-of-range behavior; 020 decisive component test for
  bounds (prev/next disabled at edges) and indicator, plus integration
  paginating through the real server.
- R4 (share/restore) → 030; decisive: deep-link restore with the real router
  (component) and an integration case through the real server for the full
  production path.
- R5 (browser navigation) → 030; decisive: component test with the real
  history-mode router stepping back/forward. If jsdom cannot exercise real
  history navigation, the named fallback check is manual browser
  verification with exact steps recorded — not a silent memory-router
  substitute.
- R6 (view consistency) → 020 decisive component tests for table, controls,
  and both empty states; 030 extends consistency to URL-driven state.
- R7 (CRUD consistent with view) → 020 decisive component tests for
  refetch-with-view and out-of-range clamping; 030 decisive component test
  for URL sync after CRUD/clamp.
- R8 (CRUD preserved) → 010 decisive HTTP regression tests (unchanged CRUD
  semantics); 020 retains CRUD component regressions.
- R9 (unfiltered compatibility) → 010 decisive HTTP test asserting the
  paramless GET body is unchanged.
- R10 (docs) → each child updates the documentation its change makes true;
  verified by review in each child's checklist.
- R11 (evidence) → the per-child test tasks above; 020 owns the first real
  transport integration coverage; 030 extends it for URL restore.

### Additional implementation verification

- Full suite runs (pytest; client vitest including the integration file)
  collect and exit cleanly after each child; no skipped tests.
- After 030, a manual smoke of the production path (Flask on port 5000 plus
  the client): apply filter/search/page, open a shared deep link in a fresh
  context, and use browser back/forward — recorded with exact steps. This is
  the named manual check for R5 only if the automated history check proves
  impossible in jsdom; otherwise it is corroborating evidence.
````

### tasks/20260926-books-page-discovery/010-server-discovery-api.md

````markdown
# Server discovery API (read filter, search, bounded pagination)

Extend GET `/books` with optional read-status filtering, title/author search,
and bounded pagination through the `server/query.py` selection seam, while the
paramless response stays byte-compatible and CRUD routes keep their semantics.
The API contract is independently usable by API consumers and carries its own
HTTP-boundary evidence.

Parent Task: tasks/20260926-books-page-discovery/000-main.md

Depends On: (none)

## Requirements checklist

- [ ] S1 — GET `/books` accepts optional discovery params per the parent plan
      contract (D1): `read` (`true`/`false`; absent = all), `q`
      (case-insensitive substring matching title OR author), `page` (1-based
      positive integer). Requests using any discovery param return the current
      envelope plus pagination metadata (`page`, `page_size`, `total`,
      `total_pages`) with the selected rows (D2).
- [ ] S2 — A paramless GET `/books` returns the current exact envelope with
      the full list (R9).
- [ ] S3 — POST `/books`, PUT `/books/<id>`, DELETE `/books/<id>` semantics
      are unchanged (R8), and created/updated/deleted books are visible to
      subsequent discovery queries.
- [ ] S4 — Selection logic lives in `server/query.py` and is wired into the
      GET route (data-selection seam ownership); no duplicated selection logic
      in `app.py`.
- [ ] S5 — HTTP tests cover: paramless compatibility, read filtering, `q`
      matching on title and author with case-insensitivity and a no-match
      case, combined filter+search, pagination pages/totals/out-of-range,
      validation behavior (per D4), CRUD regression, and CRUD→discovery
      interplay.

## Execution plan

Status: Draft

Design: `server/app.py` reads `request.args` on GET and delegates selection to
`server/query.py`, which returns rows plus metadata given `(books, params)`.
When no discovery param is present the route returns the current body
unchanged; otherwise it returns the envelope with metadata. Page size is a
fixed server constant (10, per D1). `BOOKS` remains module-level in-memory
state; CRUD routes are untouched.

Steps:

1. Establish the baseline: install runtime dependencies and confirm the
   existing pytest suite passes.
2. Implement selection in `server/query.py`: read filter, case-insensitive
   substring search on title or author, pagination with `total` /
   `total_pages`, and validation per D4 (malformed `read`/`page` → 400 raised
   for the route to return; out-of-range `page` → empty rows with correct
   metadata).
3. Wire GET `/books`: paramless → unchanged body; any discovery param →
   paginated envelope. CRUD routes untouched.
4. Tests: add deterministic seeding/reset of `BOOKS` per test (module-level
   state is shared) and extend `tests/test_books_api.py` per S5.
5. Docs: add the API-contract section (params, envelope, compatibility rule)
   to `docs/development/index.md`, replacing the "No book-discovery
   specification exists." line.

### Implementation decisions and open questions

- Contract values (param names, envelope keys, page size 10, validation
  policy) restate parent decisions D1–D4 and inherit their pending-approval
  status; no child-local contract changes are introduced.
- Test seeding mechanism (autouse reset fixture vs. unique ids per test) is a
  local, reversible implementation choice resolved at implementation time.

### Documentation

- Add the API contract section to `docs/development/index.md` in the same
  change as the params, per the parent plan's `### Documentation` section.

### Task checklist

- [ ] Baseline: dependencies installed; existing pytest suite passes.
- [ ] `server/query.py` selection implemented (filter, search, pagination,
      validation).
- [ ] GET `/books` wired; paramless response byte-compatible; CRUD routes
      untouched.
- [ ] `tests/test_books_api.py` extended per S5; full suite passes.
- [ ] `docs/development/index.md` API contract section added.

### Requirement verification

- S1 → decisive: pytest cases through the Flask test client asserting
  filtered rows plus metadata for `read`, `q` (title, author,
  case-insensitivity, no match), combined filter+search, and pagination
  totals/out-of-range. The test client crosses real routing and selection.
- S2 → decisive: pytest asserting the paramless GET body equals the current
  envelope with the full list.
- S3 → decisive: retained/extended HTTP CRUD tests plus a case showing POST
  then a filtered GET returns the new book under the matching view.
- S4 → verified by review: the route delegates selection to
  `server/query.py`.
- S5 → satisfied by the test task above; the suite collects and exits
  cleanly with no skipped tests.

### Additional implementation verification

- Manual curl smoke against the running server (outside the Flask test
  client) comparing the paramless and filtered envelopes, with the exact
  commands recorded in Implementation Notes.
````

### tasks/20260926-books-page-discovery/020-client-discovery-view.md

````markdown
# Client discovery view (controls, bounded pagination, view-consistent CRUD refresh)

Build the Books page browsing experience on the 010 API contract: read-status
filter, title/author search, bounded pagination controls, view-consistent
table and empty states, and CRUD refreshes that honor the current view. Owns
the first real client↔server transport integration evidence, which the
existing mocked-transport component test cannot provide.

Parent Task: tasks/20260926-books-page-discovery/000-main.md

Depends On: tasks/20260926-books-page-discovery/010-server-discovery-api.md

## Requirements checklist

- [ ] C1 — The page renders active controls reflecting the current view:
      read-status filter (all/read/unread), search input, and bounded
      pagination (prev/next disabled at bounds, page indicator from response
      metadata).
- [ ] C2 — Control changes refetch via the API with the view's params; the
      table, controls, and empty state render the response rows and metadata.
- [ ] C3 — The empty state is consistent with the selected view:
      "No books found." for an empty collection; a distinct no-matches state
      when filter/search match nothing (parent D7; a clear-filters affordance
      only if approved there).
- [ ] C4 — Add/update/delete refresh using the current view params; when the
      refreshed page is out of range, the view resolves to a valid page before
      rendering (R7).
- [ ] C5 — Existing CRUD behavior through the page keeps working; the existing
      component regression (empty state, CRUD methods) is preserved and
      extended.
- [ ] C6 — Evidence: component tests at the view boundary (transport mocked)
      plus the first integration coverage of the real client transport against
      the real Flask server for filter/search/page through the production
      path.

## Execution plan

Status: Draft

Design: `Books.vue` owns a single reactive view object `{ read, q, page }` and
one `refresh()` path that calls `getBooks(viewParams)` and stores rows plus
pagination metadata (`page`, `page_size`, `total`, `total_pages`). All CRUD
methods call `refresh()` instead of paramless `getBooks()`. The single-owner
view object is deliberate: 030 binds this same object to the route query
without reworking state. `client/src/api/books.js` needs no contract change
(it already forwards params); param mapping lives in one place. Search applies
debounced (~300 ms, parent D6); page changes apply immediately. Out-of-range
clamping uses the response metadata. Component tests mock the API module and
cover view-boundary logic; the integration file drives the real stack.

Steps:

1. Baseline: npm install; run the existing vitest suite. If the component
   spec cannot run for lack of a DOM environment, add the minimal
   environment config (e.g. jsdom) and confirm the existing spec passes
   before extending it; record what the baseline required.
2. Implement view state, `refresh()`, and the params mapping in `Books.vue`
   against the 010 contract (always-explicit params per D3).
3. Render controls and pagination from response metadata with bounds; apply
   D6 debounce and D7 empty states as approved.
4. Rework the CRUD methods to refresh with the view; implement out-of-range
   clamping using metadata.
5. Component tests (extend `client/tests/Books.spec.js`) per C6: controls →
   params mapping, filter/search application, pagination bounds and
   indicator, no-matches vs. no-books states, CRUD refresh carries view
   params, clamp behavior, and the existing regressions.
6. Integration: populate `client/tests/books.integration.js` — start the real
   Flask server on port 5000 (matching `client/src/http.js`), drive the
   mounted page over real transport/routing/selection, assert
   filtered/searched/paginated rows, and tear the server process down. The
   harness must stay runnable via `npm test`.

### Implementation decisions and open questions

- Parent decisions D1–D8 govern (contract, always-explicit params, debounce,
  empty states). Child-local, reversible choices: control markup and test
  selectors, the debounce constant, and clamping to the last valid page.
- The integration harness (spawning Flask from vitest) is maintained test
  infrastructure per the testing policy and is verified through this suite as
  its real consumer.

### Documentation

- Add the page-behavior section (controls, pagination, empty states) to
  `docs/development/index.md` and a README sentence for filter/search/
  pagination, in the same change as the behavior, per the parent plan's
  `### Documentation` section.

### Task checklist

- [ ] Component test baseline established (existing spec runs; environment
      changes recorded).
- [ ] View state + `refresh()` + params mapping implemented per the 010
      contract.
- [ ] Controls, bounded pagination, and empty states rendered per approved
      D6/D7.
- [ ] CRUD refresh honors the view; out-of-range clamp implemented.
- [ ] Component tests extended per C6; suite passes.
- [ ] `client/tests/books.integration.js` populated; runs cleanly via
      `npm test`.
- [ ] Docs and README updated.

### Requirement verification

- C1/C2 → decisive: component tests asserting the controls reflect the view
  state and emit the mapped API params, with bounds and indicator from
  metadata.
- C3 → decisive: component tests covering both empty states.
- C4 → decisive: component tests asserting refresh uses the current view
  params and clamps on out-of-range metadata.
- C5 → decisive: retained/extended CRUD component regressions.
- C6 integration → decisive for the R1–R3 end-to-end chain: real axios →
  real Flask routing/selection → rendered rows. Transport and server are not
  mocked in this check; mocked-transport component tests are supporting
  evidence for view logic only.

### Additional implementation verification

- Run the component and integration suites together once to confirm the
  shared harness and the mocked-transport suite do not interfere (shared
  state, server port).
````

### tasks/20260926-books-page-discovery/030-url-share-restore.md

````markdown
# URL state sharing and restore (deep links, browser navigation)

Bind the 020 view state to the `/books` URL: encode the current discovery
state in query params, restore it from shared or deep links while normalizing
invalid values, keep browser back/forward and CRUD/clamp transitions
consistent with the URL, and complete the discovery documentation.

Parent Task: tasks/20260926-books-page-discovery/000-main.md

Depends On: tasks/20260926-books-page-discovery/010-server-discovery-api.md,
tasks/20260926-books-page-discovery/020-client-discovery-view.md

## Requirements checklist

- [ ] U1 — The current view (read filter, search text, page) is encoded in
      `/books` query params per parent D5; non-default state yields a
      shareable URL; the default view keeps the URL clean.
- [ ] U2 — Opening `/books` with query params restores the view: controls,
      table, and fetch reflect the encoded state; invalid values normalize to
      defaults without errors (parents D4/D5).
- [ ] U3 — Browser back/forward keeps the table, active controls, and loaded
      data consistent with the URL state (R5).
- [ ] U4 — CRUD refreshes and page clamping keep the URL in sync with the
      view actually rendered (R7 extended to the URL).
- [ ] U5 — Evidence: component tests with the real router (restore,
      normalization, back/forward, sync) plus an integration deep-link case
      through the real server for the full production restore path.

## Execution plan

Status: Draft

Design: the route query is the single source of truth for the 020 view object.
A watcher maps `route.query` → view (normalizing invalid values), and applied
view changes map back to router navigation: `push` on applied filter/search/
page changes (parent D6, so back/forward walks result states) and `replace`
when normalizing on load, so no spurious history entries appear. Restores
drive `refresh()` through the same path as control changes, so table,
controls, and empty state stay consistent by construction (R6). Back/forward
is exercised through the real history-mode router.

Steps:

1. Implement query → view parsing and normalization (absent/invalid `read`,
   `q`, `page` → defaults; `replace`-clean the URL when normalization
   occurred).
2. Implement view → URL sync (`push` on applied changes per D6; the default
   view keeps a clean URL).
3. Route restores and back/forward drive `refresh()` through the 020 path;
   CRUD and clamp transitions propagate to the URL.
4. Component tests with the real router (extend
   `client/tests/Books.spec.js`): deep-link restore (read/q/page applied with
   consistent controls and rows), invalid-param normalization (URL cleaned,
   defaults applied), back/forward stepping between applied states, and URL
   sync after CRUD and clamp.
5. Integration: extend `client/tests/books.integration.js` with a deep-link
   case — encoded URL → real router → real fetch → filtered rows from the
   real server — completing the full production path for R4.
6. Docs: URL-state section in `docs/development/index.md`; README sentence
   for shareable/restorable state.

### Implementation decisions and open questions

- Parent decisions D5 (encoding) and D6 (push/replace policy) govern;
  child-local, reversible choices: the exact normalization rules (invalid
  read token, non-numeric or negative page → default).
- If jsdom cannot exercise real history back/forward, do not silently
  substitute a memory router (it is not the production path): record the gap
  and name the manual check — exact steps — needed to evidence U3 through the
  real components, per the parent plan's named-check rule for R5.

### Documentation

- Add the URL-state section to `docs/development/index.md` and the README
  shareable-state sentence, in the same change as the behavior, per the
  parent plan's `### Documentation` section.

### Task checklist

- [ ] Query → view parsing and normalization implemented.
- [ ] View → URL sync (push/replace policy) implemented.
- [ ] Restores, back/forward, and CRUD/clamp consistency wired through
      `refresh()`.
- [ ] Component tests per U5 added; suite passes.
- [ ] Integration deep-link case added; suite passes.
- [ ] Docs and README updated.

### Requirement verification

- U1 → decisive: component test asserting the URL after applying non-default
  state (encoded per D5) and a clean URL for the default view.
- U2 → decisive: component test mounting at a deep-linked URL asserting
  controls, emitted fetch params, and rows; plus a normalization case for
  invalid values.
- U3 → decisive: component test with the real history-mode router stepping
  back/forward and asserting view plus refetch; if that proves impossible in
  jsdom, the manually named check above.
- U4 → decisive: component test asserting the query string after CRUD refresh
  and after an out-of-range clamp.
- U5 integration → decisive for the R4 full path: shared URL → real router →
  real transport → real server → rendered filtered rows.

### Additional implementation verification

- Run the full client suite (component + integration) once to confirm all
  URL-state and view suites collect and exit cleanly together, with the
  harness still runnable via `npm test`.
````


**Assistant** *(reasoning present)*

```json
{
  "schema_version": 1,
  "scenario_id": "tg04-flask-vue-discovery-decomposition",
  "assessment": {
    "sections": {
      "tasks/20260926-books-page-discovery/000-main.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "R7 item",
            "quote": "R7 — Add/update/delete refreshes the table using the selected view (refetch honors the view; a page left out of range resolves to a valid page) without changing CRUD semantics.",
            "why": "Densest of the eleven items: three facts (refetch-with-view, out-of-range clamp, semantics preserved) sit behind nested parentheticals in one line-wrapped bullet. Still a single requirement, and the surrounding R1–R11 items stay one-topic, so the ~264-word checklist scans and holds."
          },
          {
            "where": "whole checklist",
            "quote": "R1 — Books page filters books by read status (all / read / unread).",
            "why": "Stable ID prefixes (R1–R11) plus a uniform one-requirement-per-item shape make the list independently checkable and cross-referenceable from the Execution plan's verification map."
          }
        ]
      },
      "tasks/20260926-books-page-discovery/000-main.md — Subtasks": {
        "grade": "readable",
        "findings": [
          {
            "where": "third item",
            "quote": "tasks/20260926-books-page-discovery/030-url-share-restore.md (depends on 010, 020)",
            "why": "Three items, 19 words total; the dependency graph is compressed to short file-number references and takes one glance."
          }
        ]
      },
      "tasks/20260926-books-page-discovery/000-main.md — Questions and decisions": {
        "grade": "readable",
        "findings": [
          {
            "where": "second bullet",
            "quote": "Material design decisions that define the public API contract and user-visible URL/UX behavior (D1–D7) are collected with recommendations in `### Implementation decisions and open questions` below and await approval together with the plan.",
            "why": "A single ~40-word sentence, but it carries exactly what a reader needs — where the decisions live and their approval status; mild strain, no loss."
          },
          {
            "where": "first bullet",
            "quote": "No unresolved requirement questions: the requested outcomes and the two preserved contracts (existing CRUD behavior, unfiltered API compatibility) are fully specified by the request and current behavior.",
            "why": "Dense one-sentence answer to the open-question scan; wording is deliberately narrowed to 'requirement questions', so it slightly overstates closedness relative to D7's pending confirm-inclusion elsewhere."
          }
        ]
      },
      "tasks/20260926-books-page-discovery/000-main.md — Supporting facts (research)": {
        "grade": "readable",
        "findings": [
          {
            "where": "final Docs bullet",
            "quote": "Docs: `README.md` describes the app in one line; `docs/development/index.md` states \"No book-discovery specification exists.\"; `docs/development/documentation.md` was read as required before planning doc changes.",
            "why": "The only bullet that fuses several unrelated facts (two documentation gaps plus a compliance note), breaking the file:line-per-claim pattern of the other ten items; the reader must split it themselves."
          },
          {
            "where": "verified-facts list",
            "quote": "`server/app.py:10-24` — GET `/books` returns {\"status\": \"success\", \"books\": BOOKS} (full list; no query params are read).",
            "why": "Every research claim pairs a `file:line` anchor with one short assertion; 11 items and 24 code spans stay scannable because the shape never varies."
          }
        ]
      },
      "tasks/20260926-books-page-discovery/000-main.md — Execution plan": {
        "grade": "partial",
        "findings": [
          {
            "where": "Design — Verification strategy paragraph",
            "quote": "Verification strategy: evidence at each boundary — pytest through the Flask test client for the API contract (010), vitest component tests with the transport mocked for view logic (020/030), and vitest integration tests against the real Flask server over real axios for the client↔server chain (020) and the deep-link restore path (030).",
            "why": "One ~70-word sentence carrying five parentheticals that map four check kinds onto three children; a reader must re-read to know which tool proves which boundary."
          },
          {
            "where": "Implementation decisions D6–D7",
            "quote": "Alternative (replace for everything) causes less history traffic but makes back/forward useless for result states.",
            "why": "Each decision bullet fuses policy, rationale, and a rejected alternative into one multi-line item, and D7 ends with an unanchored request ('— confirm inclusion') that belongs with open questions; the D1–D7 tags keep them findable but each bullet needs careful parsing."
          },
          {
            "where": "section scale",
            "quote": "### Requirement verification",
            "why": "At 1102 words, 28 list items and six labeled subsections this is the set's heaviest section; the labels (Design / Implementation decisions / Documentation / Task checklist / Requirement verification / Additional implementation verification) keep it navigable, but the Design block's three 50–70-word strategy paragraphs are read as prose, not scanned."
          },
          {
            "where": "Design — data-flow line",
            "quote": "URL query → view state → API params → server selection → rows + metadata → table / controls / empty state",
            "why": "The indented flow line states the whole capability shape in one glance — an example of the section's better-scanned moments."
          }
        ]
      },
      "tasks/20260926-books-page-discovery/010-server-discovery-api.md — Requirements checklist": {
        "grade": "partial",
        "findings": [
          {
            "where": "S1 item",
            "quote": "S1 — GET `/books` accepts optional discovery params per the parent plan contract (D1): `read` (`true`/`false`; absent = all), `q` (case-insensitive substring matching title OR author), `page` (1-based positive integer). Requests using any discovery param return the current envelope plus pagination metadata (`page`, `page_size`, `total`, `total_pages`) with the selected rows (D2).",
            "why": "The entire public contract — three param grammars, envelope keys, and the compatibility split — is packed into one checkbox item (~55 words, 12+ code spans, seven wrapped lines) with no internal seams; the load-bearing contract is one wall-like item."
          },
          {
            "where": "S5 item",
            "quote": "HTTP tests cover: paramless compatibility, read filtering, `q` matching on title and author with case-insensitivity and a no-match case, combined filter+search, pagination pages/totals/out-of-range, validation behavior (per D4), CRUD regression, and CRUD→discovery interplay.",
            "why": "Eight distinct test obligations enumerated in a single comma chain; nothing is individually checkable or referenceable without unpacking the item."
          },
          {
            "where": "S2 item",
            "quote": "S2 — A paramless GET `/books` returns the current exact envelope with the full list (R9).",
            "why": "Calibration: S2–S4 are single-topic one-liners, so the strain is concentrated in two of five items — partial, not unreadable."
          }
        ]
      },
      "tasks/20260926-books-page-discovery/010-server-discovery-api.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "Design paragraph",
            "quote": "Design: `server/app.py` reads `request.args` on GET and delegates selection to `server/query.py`, which returns rows plus metadata given `(books, params)`.",
            "why": "The densest paragraph is ~58 words of short declarative sentences, one concern each; taken in a single pass, unlike the longer design walls in 020/030."
          },
          {
            "where": "Requirement verification",
            "quote": "S2 → decisive: pytest asserting the paramless GET body equals the current envelope with the full list.",
            "why": "One bullet per S-requirement with the decisive check named; tracing a requirement to its evidence is a lookup, not a search."
          }
        ]
      },
      "tasks/20260926-books-page-discovery/020-client-discovery-view.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "C3 item",
            "quote": "C3 — The empty state is consistent with the selected view: \"No books found.\" for an empty collection; a distinct no-matches state when filter/search match nothing (parent D7; a clear-filters affordance only if approved there).",
            "why": "One behavior, but the conditional approval dependency hides in a trailing parenthetical that is easy to miss on a skim; the item itself stays single-topic."
          },
          {
            "where": "whole checklist",
            "quote": "C2 — Control changes refetch via the API with the view's params; the table, controls, and empty state render the response rows and metadata.",
            "why": "C1–C6 follow a parallel controls→refetch→render grammar with no code-span clutter (0 code spans), so the 186-word list holds without effort."
          }
        ]
      },
      "tasks/20260926-books-page-discovery/020-client-discovery-view.md — Execution plan": {
        "grade": "partial",
        "findings": [
          {
            "where": "Design paragraph",
            "quote": "Design: `Books.vue` owns a single reactive view object `{ read, q, page }` and one `refresh()` path that calls `getBooks(viewParams)` and stores rows plus pagination metadata (`page`, `page_size`, `total`, `total_pages`).",
            "why": "A single ~106-word paragraph (the section's longest, per measured facts) interleaves seven concerns — state ownership, refresh path, the 030 rationale, the API-layer note, debounce, clamping, and the test split — with no internal labels; unlike 000-main's labeled State model/Compatibility/Verification paragraphs, nothing marks the seams, so it takes a second read."
          },
          {
            "where": "Step 6",
            "quote": "Integration: populate `client/tests/books.integration.js` — start the real Flask server on port 5000 (matching `client/src/http.js`), drive the mounted page over real transport/routing/selection, assert filtered/searched/paginated rows, and tear the server process down.",
            "why": "Setup, the load-bearing port-5000 constraint, assertions, and teardown are fused into one dash-chain item; the constraint is easy to lose mid-item."
          },
          {
            "where": "remaining subsections",
            "quote": "### Task checklist",
            "why": "Steps 1–5, the two decision bullets, the seven-item checklist, and the C1–C6 verification map are short and single-topic, so the strain is concentrated in the Design block — partial, not unreadable."
          }
        ]
      },
      "tasks/20260926-books-page-discovery/030-url-share-restore.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "U1 item",
            "quote": "U1 — The current view (read filter, search text, page) is encoded in `/books` query params per parent D5; non-default state yields a shareable URL; the default view keeps the URL clean.",
            "why": "Three clauses in one item, but they are the three facets of a single encoding requirement; U2–U5 stay one-behavior-per-item with parent references (D4/D5) inline, keeping the 142-word list easy to hold."
          }
        ]
      },
      "tasks/20260926-books-page-discovery/030-url-share-restore.md — Execution plan": {
        "grade": "partial",
        "findings": [
          {
            "where": "Design paragraph",
            "quote": "A watcher maps `route.query` → view (normalizing invalid values), and applied view changes map back to router navigation: `push` on applied filter/search/page changes (parent D6, so back/forward walks result states) and `replace` when normalizing on load, so no spurious history entries appear.",
            "why": "The load-bearing push/replace history policy is buried as mid-sentence clauses inside a ~45-word compound sentence (longest paragraph 87 words per measured facts); the reader parses parentheticals to learn which action uses which navigation mode."
          },
          {
            "where": "second decision bullet",
            "quote": "If jsdom cannot exercise real history back/forward, do not silently substitute a memory router (it is not the production path): record the gap and name the manual check — exact steps — needed to evidence U3 through the real components, per the parent plan's named-check rule for R5.",
            "why": "~55 words stacking a prohibition, its rationale, the required action, and a policy reference in one breath; the actionable requirement (record the gap, name the manual check) sits mid-clause."
          },
          {
            "where": "remaining subsections",
            "quote": "### Requirement verification",
            "why": "Steps 1–6, the checklist, and the U1–U5 verification map are single-topic; strain is concentrated in the Design paragraph and one bullet — partial, not unreadable."
          }
        ]
      }
    },
    "navigation": {
      "grade": "navigable",
      "findings": [
        {
          "where": "child file headers",
          "quote": "Depends On: tasks/20260926-books-page-discovery/010-server-discovery-api.md, tasks/20260926-books-page-discovery/020-client-discovery-view.md",
          "why": "Every child states Parent Task and Depends On at the top, so the 010→020→030 graph is reconstructible from any single file without reading the plans."
        },
        {
          "where": "each `## Execution plan` heading",
          "quote": "Status: Draft",
          "why": "Plan status is the first line under the plan heading in all four files — findable at a glance."
        },
        {
          "where": "000-main Requirement verification",
          "quote": "R4 (share/restore) → 030; decisive: deep-link restore with the real router (component) and an integration case through the real server for the full production path.",
          "why": "Every R1–R11 maps to an owning child and a named decisive check, so outcome-to-evidence tracing is a lookup; children mirror this with S/C/U → check bullets."
        },
        {
          "where": "000-main Questions and decisions → decisions subsection",
          "quote": "collected with recommendations in `### Implementation decisions and open questions` below and await approval together with the plan",
          "why": "The explicit pointer makes the D1–D7 list findable one level inside Execution plan; the residual gap is that D7's confirm-inclusion (the only genuinely open item) is not surfaced under the section titled for questions."
        }
      ]
    },
    "mistakes": [
      {
        "where": "000-main — opening paragraph",
        "quote": "Planning only — execution awaits approval.",
        "why": "The load-bearing status is the final clause of a ~70-word single sentence that also enumerates features and preservation constraints; a reader skimming the lede can miss that nothing is approved for execution."
      },
      {
        "where": "000-main — Questions and decisions vs Implementation decisions D7",
        "quote": "A \"clear filters\" affordance is recommended as the escape hatch for shared filtered URLs — confirm inclusion.",
        "why": "The only open confirm-request in the set is the tail of a decision bullet buried under Execution plan, while the dedicated Questions section reports no unresolved items; a reader hunting open questions from its title gets a misleading first answer."
      },
      {
        "where": "010 — Requirements checklist S1",
        "quote": "S1 — GET `/books` accepts optional discovery params per the parent plan contract (D1): ... with the selected rows (D2).",
        "why": "The full public API contract is one checkbox item mixing param grammar, envelope keys, and the compatibility rule; several load-bearing facts with no internal separation."
      },
      {
        "where": "010 — Requirements checklist S5",
        "quote": "HTTP tests cover: paramless compatibility, read filtering, ... and CRUD→discovery interplay.",
        "why": "Eight distinct test obligations enumerated in one comma chain inside a single list item; none is individually scannable or checkable."
      },
      {
        "where": "020 — Execution plan Design paragraph",
        "quote": "The single-owner view object is deliberate: 030 binds this same object to the route query without reworking state.",
        "why": "A ~106-word unlabeled paragraph interleaves state design, rationale, debounce policy, clamping, and test strategy; it is the same kind of content 000-main splits into labeled paragraphs, here presented as one wall that must be re-read to separate the concerns."
      },
      {
        "where": "030 — Execution plan Design paragraph",
        "quote": "`push` on applied filter/search/page changes (parent D6, so back/forward walks result states) and `replace` when normalizing on load",
        "why": "The load-bearing push/replace policy is a mid-sentence clause inside a compound sentence with two parentheticals; the key behavioral rule is easy to read past."
      },
      {
        "where": "000-main — Implementation decisions D6",
        "quote": "Alternative (replace for everything) causes less history traffic but makes back/forward useless for result states.",
        "why": "Decision, rationale, and rejected alternative share one ~50-word item; the secondary rejected-alternative detail competes with the policy in the same breath."
      },
      {
        "where": "000-main — Subtasks vs Design slices vs Task checklist",
        "quote": "Execute `tasks/20260926-books-page-discovery/010-server-discovery-api.md` (no dependencies).",
        "why": "The same 010→020→030 dependency chain is stated three times (Subtasks, Design slice list, Task checklist); consistent numbering keeps each copy scannable, but the restatements add surface without new information."
      }
    ],
    "summary": "The set is structurally strong and genuinely navigable: numbered slices, Parent/Depends On headers, stable R/S/C/U and D1–D7 identifiers, per-child verification maps, and a Status: Draft line make the outcome, constraints, dependencies, and plan status findable from structure alone. Readability strain is concentrated where single containers carry several facts at once: 000-main's 1102-word Execution plan (70-word one-sentence strategy paragraphs and seven multi-clause decision bullets, one hiding an open confirm-request), 010's S1/S5 mega-items (a full API contract and eight test obligations in single checkboxes), 020's 106-word unlabeled Design paragraph, and 030's compound push/replace sentence. Everything is extractable with a second read, which caps those four sections at partial; the six shorter, uniformly shaped sections (checklists in 000/020/030, Subtasks, Questions, research facts, and 010's plan) are readable with no re-reading."
  }
}
```
