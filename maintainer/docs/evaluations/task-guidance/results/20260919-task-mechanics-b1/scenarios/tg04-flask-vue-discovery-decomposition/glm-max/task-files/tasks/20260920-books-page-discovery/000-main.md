# Books page discovery (filter, search, pagination, URL state)

Make the Books page practical for a larger collection. Users filter by read
status, search by title or author, move through bounded pages, and share or
restore the current discovery state through the URL. The table, active
controls, empty state, browser navigation, and CRUD refreshes stay consistent
with the selected view. Existing CRUD behavior and unfiltered API compatibility
are preserved.

Planning only — execution has not been approved.

## Requirements checklist

- [ ] Books can be filtered by read status end to end; the control, table, and
      empty state reflect the active filter.
      Owner: `tasks/20260920-books-page-discovery/010-read-status-filter.md`
- [ ] Books can be searched by title or author end to end; search composes with
      the read filter.
      Owner: `tasks/20260920-books-page-discovery/020-title-author-search.md`
- [ ] Results are served and navigated as bounded pages over the filtered and
      searched set.
      Owner: `tasks/20260920-books-page-discovery/030-bounded-pagination.md`
- [ ] The combined discovery state round-trips through the URL: a shared link
      restores the view and browser back/forward keeps the view consistent.
      Owner: `tasks/20260920-books-page-discovery/040-url-state-and-view-consistency.md`
- [ ] The table, active controls, and empty state stay consistent with the
      selected view in every state (fresh, filtered, restored, navigated, after
      CRUD). Decisive check: `040-url-state-and-view-consistency.md`
- [ ] Existing CRUD behavior is preserved and CRUD refreshes re-run the current
      discovery query. Owned per slice; decisive check in
      `040-url-state-and-view-consistency.md`
- [ ] `GET /books` without query parameters keeps returning the exact current
      unfiltered response. Decisive check:
      `010-read-status-filter.md` (first server change).

## Subtasks

- [ ] `tasks/20260920-books-page-discovery/010-read-status-filter.md`
- [ ] `tasks/20260920-books-page-discovery/020-title-author-search.md`
- [ ] `tasks/20260920-books-page-discovery/030-bounded-pagination.md`
- [ ] `tasks/20260920-books-page-discovery/040-url-state-and-view-consistency.md`

`040` depends on `010`, `020`, and `030`. `010`–`030` are mutually independent:
each composes with whichever discovery parameters have already landed and
introduces any shared piece (e.g. the differentiated no-matches empty state) if
it runs first. Recommended order: 010 → 020 → 030 → 040.

## Requirement questions (need user answers before execution)

- **Q1 — Pagination contract.** Server-side bounded pages behind query
  parameters, or client-side paging of the full list? Changes the public API
  surface.
- **Q2 — Response envelope.** When any discovery parameter is present, respond
  with `{"status":"success","books":[…],"page":…,"pageCount":…,"total":…}`; a
  parameter-less `GET /books` keeps today's exact two-field response. Confirms
  what "unfiltered API compatibility" preserves.
- **Q3 — Page size.** Fixed server constant (proposed: 10), not
  user-configurable in this iteration.
- **Q4 — Invalid / out-of-range state.** Proposed: unknown `read` values are
  treated as absent; non-numeric or `page` < 1 restores page 1; `page` beyond
  `pageCount` clamps to the last page; changing filter or search resets page
  to 1.
- **Q5 — Search semantics.** Proposed: one query matching case-insensitive
  substrings in title OR author, ANDed with the read filter.
- **Q6 — Read-status column.** Proposed: the table gains a read-status column
  so the filter's effect is visible (the current table omits `read`).
- **Q7 — CRUD refetch semantics under discovery.** Proposed: after add /
  update / delete, re-run the current discovery query; if the result set
  shrank (e.g. deletion), clamp the page into range; a book that no longer
  matches the active filter drops from the view.

Recommendations for each live in `### Implementation decisions and open
questions` below.

## Supporting details

Current state (verified by inspection):

- `server/app.py` holds a module-level `BOOKS` list (2 seed books). `GET
  /books` returns `{"status":"success","books":[…]}` with no parameter
  handling; POST appends the request body; `PUT`/`DELETE /books/<id>` mutate by
  id. No filter, search, or pagination exists anywhere.
- `server/query.py` contains `list_books(books)` — an unused selection seam,
  the natural home for discovery selection.
- `client/src/components/Books.vue` fetches all books on mount, renders a
  title/author table, shows `No books found.` when the list is empty, and
  exposes `add`/`update`/`remove` methods that refetch all books. No template
  element invokes those methods, and `read` is not rendered.
- `client/src/api/books.js:getBooks(params)` already forwards query parameters
  to axios, so client transport work is thin.
- `client/src/router.js` serves `/books` via `createWebHistory`; the component
  is not router-aware yet.
- `client/src/http.js` hard-codes `baseURL: "http://localhost:5000"`.
- Tests: `tests/test_books_api.py` (pytest, Flask test client; the mutation
  test self-cleans against shared module state); `client/tests/Books.spec.js`
  (mounts with a mocked api module, asserts the empty state);
  `client/tests/books.integration.js` is a placeholder with no coverage.
- Docs: `docs/development/index.md` states "No book-discovery specification
  exists."; root `README.md` is a one-sentence summary.

Assumptions and gaps to resolve during execution:

- No vitest config and no jsdom/happy-dom dependency were found, so the
  component test harness may not run as-is. `010` verifies it first and
  establishes it if needed.
- pytest and the node toolchain are assumed available; if installation is
  blocked, report it rather than substituting weaker evidence.

Out of scope (excluded unless the user extends scope): user-configurable page
size, sorting, per-page selectors, virtualization, server-side persistence
(`BOOKS` stays in-memory), a real-browser E2E harness, and UI framework or
styling changes.

Decomposition rationale: the project context directs end-to-end capability
slices (server selection + transport + UI + URL) rather than per-layer tasks.
Filter, search, and pagination are each independently useful increments; URL
state sharing is a distinct cross-cutting capability over the combined state
and is built once in `040` instead of as three partial serializations.

## Execution plan

Status: Draft

Approach: four end-to-end slices. Server selection lands in
`server/query.py` as pure selection over the book list (no Flask imports);
`server/app.py` parses query parameters and shapes responses. On the client,
`Books.vue` owns discovery state, controls, and the differentiated empty
state; `api/books.js` forwards parameters; `040` adds route-query
synchronization through the real router. Each slice lands its own focused
tests and documentation updates in the same change as the behavior.

Boundaries: the public JSON API (`/books` parameters and envelope), the Books
page UI (controls, table, empty state, pager), and the `/books` URL query. No
schema, persistence, or dependency changes beyond the test-environment need
recorded above.

Risks:

- Shared module-level `BOOKS` state can leak between pytest tests; mitigated
  by a per-test snapshot fixture (decision D5, lands in `010`).
- The component test harness may not currently run (no jsdom environment);
  verified and established in `010` before slice tests build on it.
- The integration harness spawns a real Flask process on the port matching the
  axios base URL (5000); port collisions would block it — report rather than
  weaken the boundary.
- URL state edge cases (unknown or out-of-range values) are user-visible
  behavior deferred until Q4 is approved; do not pre-implement a rule.

### Implementation decisions and open questions

Local decisions (reversible; end behavior is identical either way):

- **D1 — Slice shape.** End-to-end capability slices per project context; URL
  state is built once over the combined state in `040`.
- **D2 — URL shape.** `/books?read=false&q=dune&page=2`; `read` ∈
  {`true`,`false`}, `q` is free text, `page` is 1-based. Default state omits
  all discovery parameters so shared links stay clean.
- **D3 — Server layering.** Selection logic in `server/query.py` (pure
  functions over the list); `app.py` owns parameter parsing and response
  shaping. Envelope metadata names: `page`, `pageCount`, `total` (proposed,
  part of Q1/Q2).
- **D4 — Component test setup.** From `040` on, `Books.vue` tests mount with a
  real router using `createMemoryHistory()` so URL sync runs through real
  router behavior; the api module stays mocked at the transport boundary.
- **D5 — pytest isolation.** Autouse fixture snapshots and restores
  `server.app.BOOKS` per test; makes free test seeding safe (needed by `030`).
- **D6 — URL writing.** Discrete control changes (filter, page) use
  `router.push` so back/forward steps through view changes; search typing
  debounces (~250ms) and `replace`s the entry to avoid one history entry per
  keystroke.
- **D7 — Integration harness.** `client/tests/books.integration.js` spawns the
  real Flask app on port 5000 (matching the axios base URL) in a setup hook
  and terminates it afterwards; born in `010`, extended per slice.

Open questions (material; approval required before the affected slice
executes): Q1–Q7 above. Tradeoffs: server-side paging keeps payloads bounded
and matches "practical for a larger collection" but adds envelope/compat
surface (Q1/Q2); client-side paging would preserve today's response shape but
ships the whole collection to the browser. Ignoring invalid URL state keeps
old shared links working; strict 400 responses would be louder but brittle.
The read column (Q6) makes filter consistency visible; without it users cannot
see why rows are shown or hidden.

### Documentation

- Audience: developers (the fixture has no end-user documentation surface).
- Create `docs/development/book-discovery.md` as the maintained specification
  of current supported discovery behavior: controls, API parameters, envelope,
  URL state, and the preserved unfiltered contract. `docs/development/documentation.md`
  was read during planning, as required before creating the page.
- Each subtask updates the spec page in the same change as the behavior it
  makes true; `010` replaces the "No book-discovery specification exists."
  line in `docs/development/index.md` with a link.
- Root `README.md` gains its discovery sentence in `040`, when the full
  capability set exists, to avoid partial claims.

### Task checklist

- [ ] `010` read-status filter — executed per its plan once Q1–Q7 answers
      touching filtering are approved; unfiltered compatibility regression
      green; spec page created.
- [ ] `020` title/author search — executed and composed with landed params;
      tests and docs updated.
- [ ] `030` bounded pagination — executed with bounding, metadata, and the
      approved reset/clamp rules; tests and docs updated.
- [ ] `040` URL state and view consistency — executed; decisive combined
      scenario green; spec finalized; README refreshed.

### Requirement verification

- Unfiltered API compatibility → pytest in `010`: parameter-less `GET /books`
  returns today's exact response shape and full book list; rerun in every
  later server change.
- Read filter → `010`: pytest at the API boundary (only matching books;
  composes with landed params); component test at the UI boundary (control →
  table → empty state); integration case proving `read` agrees across the real
  client api and Flask over HTTP.
- Search → `020`: same three-boundary pattern for `q`, including composition
  with the read filter.
- Pagination → `030`: pytest proving bounding, metadata, and the approved
  reset/clamp rules; component test proving pager consistency with
  `pageCount`; integration case proving `page` over HTTP.
- URL share/restore and browser navigation → `040`: component tests with
  memory-history router proving serialize/restore, back/forward, invalid-state
  handling, and CRUD-after-restore; integration case proving a shared URL's
  parameter set matches what the live server accepts and returns.
- CRUD preservation → existing pytest mutation tests keep passing unchanged in
  every slice; component tests assert CRUD refetches carry the active
  discovery query; decisive combined check in `040`.
- View consistency → per-slice component assertions for the states each slice
  introduces; the decisive all-states scenario (fresh → filtered → searched →
  paged → shared-link restore → back/forward → mutate) runs in `040`.
- Behaviors pending Q1–Q7 answers are not implemented or tested until
  approved; the affected assertions are written against the approved rules.

### Additional implementation verification

- Integration harness lifecycle (`010`): the Flask child process starts on the
  configured port, serves a real request, and is terminated cleanly — the
  shared harness is maintained test infrastructure verified through a real
  consumer.
- Component harness check (`010`): confirm vitest actually runs the component
  suite (environment/dependency gap) before building slice tests on it.