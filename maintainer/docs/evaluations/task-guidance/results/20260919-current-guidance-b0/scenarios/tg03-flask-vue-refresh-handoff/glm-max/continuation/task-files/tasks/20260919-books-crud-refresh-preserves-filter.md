# Books CRUD refresh must preserve the selected filter

The Books page's All/Read/Unread filter is ignored when add, update, or delete
refresh the collection: the refetch always uses the unfiltered default. This
task plans the client-side fix so every CRUD refresh re-applies the active
filter while leaving the HTTP contract and unfiltered behavior untouched.
Planning only — no implementation performed for this task yet.

## Requirements checklist

- [ ] **R1 — CRUD refresh re-applies the selected filter.** After add, update,
  or delete, the collection refresh uses the currently selected filter
  (`all` / `read` / `unread`), so the visible list continues to reflect that
  filter instead of falling back to the unfiltered list. (Request: "reapply it
  whenever CRUD refreshes the collection".)
- [ ] **R2 — The selected filter stays visibly active.** Across CRUD
  refreshes, the filter control's pressed state keeps reflecting the user's
  selection (no reset to `all`) and the list content matches that selection.
  (Request: "Keep the selected filter visibly active".)
- [ ] **R3 — HTTP contract preserved.** Same endpoints and request semantics
  (`read=true` / `read=false` for filtered GETs, no query params for
  unfiltered GETs) and same `{status, books}` / `{status, book}` response
  shapes; `server/app.py` and the request mapping in
  `client/src/api/books.js` are not modified. (Request: "Preserve the existing
  API response shape".)
- [ ] **R4 — Unfiltered behavior preserved.** With All selected, add, update,
  and delete refreshes continue to display the full collection exactly as they
  do today. (Request: "Preserve … unfiltered behavior".)

Out of scope (not approved outcomes): initial-load fetch behavior (the
component fetches only on filter selection or after CRUD today), empty-state
copy, filter styling beyond the existing `aria-pressed` signal, and any server
behavior change.

## Open questions and decisions

- None unresolved. Two consequences follow directly from R1 and are treated as
  expected behavior, not bugs: a newly added or edited book that does not
  match the active filter does not appear until the filter changes, and
  deleting the last book matching an active filter shows the existing
  "No books found." empty state while the filter stays active.
- Interpretation note (flagged, not blocking): "visibly active" is taken to
  mean the existing `aria-pressed` signal keeps reflecting the selection — the
  fixture has no other pressed styling. Adding CSS-level selected styling
  would be new scope.

## Supporting details

- Defect location: `client/src/components/Books.vue:30-41` — `add`, `update`,
  and `remove` each perform the mutation, then refetch with `getBooks()`
  (default `"all"`), discarding the active filter. The code carries
  `// regression: filter lost` comments on all three call sites.
- The pressed state is not currently reset: `selectedFilter`
  (Books.vue:24) is only written by `selectFilter` (Books.vue:26-28). After a
  CRUD refresh the buttons keep showing the old selection via `aria-pressed`
  (Books.vue:3-12) while the table shows the unfiltered list — the defect is
  the list content, not the control state.
- Filter → request mapping (unchanged by this fix):
  `client/src/api/books.js:3-6` — `getBooks(filter = "all")`; `read` →
  `?read=true`, `unread` → `?read=false`, `all` → no params. Mutations: POST
  `/books`, PUT/DELETE `/books/<id>` (books.js:8-10).
- Server behavior (no change needed): `server/app.py:15-20` filters GET
  `/books` by the `read` arg only when it is `"true"`/`"false"`; POST returns
  `{"status": "success", "books": …}` (app.py:14); PUT/DELETE return
  `{"status": "success", "book": …}` (app.py:30).
- No lifecycle fetch: the component loads books only via `selectFilter` or a
  post-CRUD refresh; on mount it renders the empty state (exercised by
  `client/tests/Books.spec.js:13-17`). Changing this is out of scope.
- Existing tests: `client/tests/Books.spec.js` (vitest + @vue/test-utils, api
  module mocked at `../src/api/books`) and `tests/test_books_api.py` using the
  Flask test client from `tests/conftest.py`. Server tests currently assert
  status codes only — they do not pin the unfiltered response body or shape;
  the plan closes that gap with a small assertion.
- Component-level mock note: the refresh currently calls `getBooks()` with no
  argument; after the fix the All case calls `getBooks("all")` explicitly.
  Equivalent at the HTTP boundary (no params either way), but component-test
  mock assertions must expect the explicit `"all"` argument.

## Execution plan

Status: Draft

### Approach

Collapse the four collection fetches in `Books.vue` onto a single path. Add a
`refreshBooks()` method that awaits `getBooks(this.selectedFilter)` and
assigns `this.books` from `response.data.books`. `selectFilter` sets
`selectedFilter` and then calls `refreshBooks()`; `add`, `update`, and
`remove` perform their mutation and then call `refreshBooks()`. Because the
api module already maps `"all"` to a parameterless GET, the All case issues a
byte-identical request to today's, satisfying R3 and R4 with no server
changes. `selectedFilter` is never reassigned by CRUD operations, so R2 holds
by construction, and the component tests pin it so a future refactor cannot
quietly reset it.

Evidence boundary: the changed logic is the component's refresh path, so the
decisive tests are component tests (vitest + @vue/test-utils) that mock the
api module at `../src/api/books` and assert both the filter argument passed to
`getBooks` and the rendered list. The api-module mapping and Flask routing are
unchanged code, evidenced on their own sides (file unchanged plus existing and
slightly strengthened Python tests).

### Implementation decisions and open questions

- Decision (resolved, local and reversible): route all four fetches through a
  shared `refreshBooks()` helper instead of editing the three CRUD call sites
  to pass the filter inline. One refresh path prevents the regression from
  recurring per-method; behavior is identical.
- Decision (resolved): pass `"all"` explicitly from the component rather than
  relying on the api module's default parameter, so the refresh path is
  uniform and mock assertions are deterministic. The HTTP request is
  unchanged (no params either way).
- No open questions; see the task's "Open questions and decisions" section for
  the flagged interpretation note about `aria-pressed` being the only pressed
  signal in this fixture.

### Documentation

- No maintained documentation describes the Books filter or CRUD-refresh
  behavior today; `docs/development/index.md` records that no book-discovery
  specification exists. The fix changes no public contract and introduces no
  new user-facing claim, so no documentation changes are planned.
- If a Books-page specification is added later, the filter-persistence
  behavior belongs there with the client package (audience: developers on
  this fixture; no new pages for this fix).

### Task checklist

- [ ] T1. `client/src/components/Books.vue`: add `refreshBooks()`; route
  `selectFilter`, `add`, `update`, and `remove` through it (mutation first,
  then refresh with the selected filter); remove the
  `// regression: filter lost` comments.
- [ ] T2. `client/tests/Books.spec.js`: give the `getBooks` mock per-call
  queued responses and add cases: (a) selecting a filter fetches and renders
  that filter's books; (b) after add, update, and remove the refetch uses the
  active filter and the list reflects the queued response; (c) `aria-pressed`
  stays on the active filter after each CRUD refresh; (d) with `all`
  selected, CRUD refetch calls `getBooks("all")` and renders the full list;
  (e) deleting the last matching book under an active filter renders
  "No books found." with the filter still pressed.
- [ ] T3. `tests/test_books_api.py`: extend `test_books` to assert the
  unfiltered GET returns both seed books inside
  `{"status": "success", "books": […]}` (pins shape and unfiltered
  semantics; assertions stay read-only because `BOOKS` is module-level shared
  state).
- [ ] T4. Run `npm test` in `client/` and `python -m pytest tests/`; record
  results in Implementation Notes and update this checklist as tasks
  complete.

### Requirement verification

- **R1** → T2(b): after `selectFilter("read")` / `selectFilter("unread")`,
  each CRUD operation causes `getBooks` to be called with that filter and the
  table renders the mocked filtered response. Decisive because the assertions
  cover the component's actual refresh call and rendered output; the api mock
  sits at the component's own boundary and does not bypass the changed logic.
- **R2** → T2(c): `aria-pressed` remains `"true"` on the selected button after
  each CRUD refresh, and no `getBooks("all")` call occurs while a real filter
  is selected.
- **R3** → diff review confirms `server/app.py` and the request mapping in
  `client/src/api/books.js` are untouched; T3 pins the unfiltered GET body and
  shape; the existing `test_book_mutations` still passes.
- **R4** → T2(d): with `all` selected, post-CRUD refetch calls
  `getBooks("all")` and renders the full list; the server half is evidenced by
  the T3 unfiltered-GET body assertion.

No requirement needs human-only verification; all are machine-checkable via
the component and Python test runs in T4.

### Additional implementation verification

- Residual seam gap (accepted, recorded): the component tests mock
  `../src/api/books`, so the full component → axios → Flask path is not
  exercised end-to-end, and the axios param mapping in `books.js` is covered
  by no automated test either before or after this fix. The fixture has no
  e2e/hosted harness; preservation of the mapping rests on non-modification,
  and the server tolerates any `read` value outside `true`/`false` as
  unfiltered. No new harness is to be built for this fix.
- Shared mutable state: `BOOKS` in `server/app.py` is module-level; keep new
  and extended server assertions read-only and order-independent.