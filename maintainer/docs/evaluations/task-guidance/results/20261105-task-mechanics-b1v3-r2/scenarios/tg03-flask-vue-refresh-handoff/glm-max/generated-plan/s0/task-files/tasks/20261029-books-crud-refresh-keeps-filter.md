# Books CRUD refresh keeps the selected status filter

After adding, editing, or deleting a book, the Books page refetches the
unfiltered collection even when the All/Read/Unread filter is active, so the
pressed filter button no longer matches the data shown. Plan only — execution
requires approval.

## Requirements checklist

- [ ] R1: When an add, update, or delete completes, the collection refresh
  reuses the currently selected filter (`all`, `read`, or `unread`) instead of
  falling back to the unfiltered list.
- [ ] R2: The selected filter stays visibly active through CRUD-driven
  refreshes: the corresponding filter button keeps its pressed state
  (`aria-pressed="true"`) and the filter is never reset to `all` to match the
  stale data.
- [ ] R3: Unfiltered behavior is preserved: with `all` selected — including the
  initial default state before any filter click — CRUD refreshes fetch and
  render the full collection exactly as before the fix.
- [ ] R4: The HTTP contract is preserved: Flask routes, query parameters, and
  JSON response shapes (`{"status", "books"}` for GET/POST `/books`,
  `{"status", "book"}` for PUT/DELETE `/books/<id>`) and the client
  `api/books` helper signatures are unchanged by this fix.

No unresolved requirement questions.

## Supporting details

### Root cause (fact)

`client/src/components/Books.vue` — the `add`, `update`, and `remove` methods
call `getBooks()` with no argument. `client/src/api/books.js` defaults
`filter = "all"`, so every CRUD refresh issues an unfiltered `GET /books`.
`selectedFilter` is not touched by CRUD, so the button row keeps showing the
old filter as pressed while the table shows unfiltered data.

### Existing mechanisms (facts)

- The server already implements filtering: `server/app.py:15-20` filters
  `GET /books` on the `read=true|false` query parameter. `selectFilter`
  already exercises it, so clicking a filter works today; only the CRUD
  refresh path drops the filter.
- `getBooks(filter = "all")` maps `read`/`unread` to `{ read: true|false }`
  params and `all` to no params (`client/src/api/books.js:3-6`).
- Response shapes: GET/POST `/books` → `{"status": "success", "books": [...]}`;
  PUT/DELETE `/books/<id>` → `{"status": "success", "book": {...}}`.
- The Books template wires no add/edit/delete form; the component methods are
  the CRUD entry points (a component test invokes them via `wrapper.vm`).
- `Books.vue` has no `mounted` hook: the initial `books` array is empty and
  the first fetch happens on a filter click. "Initial default state" in R3
  therefore means CRUD performed with no prior filter click.
- Test harness: `client/tests/Books.spec.js` mocks `../src/api/books` at the
  module seam and mounts the component (`vitest` + `@vue/test-utils`, run via
  `npm test` in `client/`). Server tests: `tests/test_books_api.py` via
  `pytest` at the repo root (assert status codes only today).
- Environment as of planning: `client/node_modules` is absent (no lockfile —
  `npm install` needed), and `flask`/`pytest` are not importable from the
  default `python3`; the executor must provision both before running suites.

### Decided boundaries

- Fix is confined to the client component layer. The server already provides
  the needed filtering; changing it would risk R3/R4 for no benefit.
- Excluded approach: resetting `selectedFilter` to `all` after CRUD so state
  matches the unfiltered fetch. This violates R2 and is not acceptable.
- Consequence accepted: a newly added book that does not match the active
  filter (e.g. an unread book added while `read` is active) will not appear in
  the list until the user switches filters. This is the direct meaning of
  "reapply the selected filter".

## Execution plan

Status: Draft

### Design

`selectedFilter` in `Books.vue` is the single source of truth for what the
list should show. Today only `selectFilter` reads it; the three CRUD methods
bypass it. The fix introduces one refresh path used by all four call sites:
a `refreshBooks()` method that fetches with the filter value read at call
time (`getBooks(this.selectedFilter)`) and assigns the result to `books`.
Because `getBooks("all")` sends no params, the `all` path is byte-identical
to today's unfiltered request, satisfying R3 without touching the API helper
or the server (R4). `selectedFilter` is never written outside `selectFilter`,
so the pressed-button state (existing `:aria-pressed` binding) stays stable
through CRUD refreshes (R2). Data flow after the fix:

    click button ─→ selectFilter(v) ─→ selectedFilter = v ─→ refreshBooks()
    add/update/remove ─→ api mutation ─→ refreshBooks() ─→ books = filtered data

No dependency changes, no server deploy, no data or persisted-state changes.
Component state and rendering only.

### Ordered steps

1. Write the regression component tests first (see Task checklist item 1 for
   scenarios). Run `npm install` in `client/`, then `npm test`, and confirm
   the new tests fail against the current component (they should, because
   CRUD refreshes call `getBooks()` with no filter argument).
2. Apply the client fix in `client/src/components/Books.vue`: add
   `refreshBooks()` and use it in `selectFilter`, `add`, `update`, and
   `remove`. Keep `selectedFilter` writes exclusive to `selectFilter`.
3. Re-run the client suite; the new tests pass and the existing empty-state
   test still passes.
4. Extend `tests/test_books_api.py` to pin the preserved contract: exact
   response shapes for unfiltered GET, `?read=true`/`?read=false` filtering,
   POST, PUT, and DELETE (see Task checklist item 3).
5. Provision the Python environment (flask + pytest), run `pytest` at the
   repo root, and confirm both suites collect and exit cleanly.
6. Verify `git diff` touches only `client/src/components/Books.vue`,
   `client/tests/Books.spec.js`, `tests/test_books_api.py`, and this task
   file — no server or api-helper changes (R4 evidence).
7. Keep this task file current: update the requirement checklist with
   evidence as it lands, record discoveries in `## Implementation Notes`,
   and append `## Completion Notes` when done.

### Implementation decisions and open questions

- Decision: shared `refreshBooks()` helper reading `this.selectedFilter` at
  call time, instead of repeating the argument in three methods. Local,
  reversible choice; single fetch path prevents the regression recurring.
- Decision: fix confined to `client/src/components/Books.vue` plus tests.
  The server's `?read` filtering is correct and already user-reachable.
- Decision: filtered result may exclude a just-added book (see Supporting
  details). Follows from the approved requirement; not an error case.
- Decision: do not reset `selectedFilter` on CRUD (excluded approach above).
- Open questions: none.

### Documentation

No documentation changes planned. No maintained page describes the
filter-refresh behavior; the root README's single claim ("The Vue Books page
loads and mutates books through the Flask JSON API") remains true after the
fix, and `docs/development/index.md` already records that no book-discovery
specification exists. Adding a page for this fix would exceed the
smallest-structure guidance.

### Task checklist

- [ ] 1. Add component regression tests to `client/tests/Books.spec.js`
  (api module mocked at the existing seam). Scenarios: (a) select `read`,
  run `add`, `update`, and `remove` — each must call `getBooks` with `read`
  and render the returned filtered titles; same pass for `unread`;
  (b) the selected button keeps `aria-pressed="true"` and the others `false`
  after each CRUD refresh; (c) filtered-empty case: with `unread` returning
  no books, after a CRUD refresh the empty state shows while `unread` stays
  pressed; (d) with the initial/default `all`, CRUD refreshes call
  `getBooks` with `all` and render the full payload. Confirm the filter
  tests fail before the fix (step 1) and pass after (step 3).
- [ ] 2. Apply the fix in `client/src/components/Books.vue` per the design.
- [ ] 3. Extend `tests/test_books_api.py`: assert unfiltered
  `GET /books` returns the full in-memory list with shape
  `{"status": "success", "books": [...]}`; assert `?read=true` and
  `?read=false` return only matching books; assert POST/PUT/DELETE response
  shapes (`{"status", "books"}` / `{"status", "book"}`).
- [ ] 4. Provision dependencies (`npm install` in `client/`; flask + pytest
  for Python) and run both suites; both collect and exit cleanly.
- [ ] 5. Confirm the diff is limited to the three code/test files plus this
  task file.
- [ ] 6. Update this task file: requirement evidence, `## Implementation
  Notes`, `## Completion Notes`.

### Requirement verification

- R1 → decisive: scenario (a) in checklist item 1 — the mounted component,
  with the api module mocked at its established seam, must pass the selected
  filter to `getBooks` on every CRUD refresh and render that payload. The
  mock supplies data but does not bypass the behavior under test: which
  filter value the component passes and what it renders are the real
  component logic. Boundary: Vue component state + rendering.
- R2 → decisive: scenario (b) — `aria-pressed` asserted on all three buttons
  after each CRUD refresh — plus scenario (c), which proves the filter stays
  active when the filtered result is empty.
- R3 → decisive: scenario (d) — CRUD with the default `all` filter still
  issues the unfiltered request and renders the full payload. Supporting:
  pytest pins from checklist item 3 prove the unfiltered GET returns the
  full list, and both pre-existing suites still pass.
- R4 → decisive: `git diff` shows `server/app.py` and
  `client/src/api/books.js` unchanged, and the pytest pins from checklist
  item 3 assert the exact response shapes and query-parameter behavior.
  Both suites exit cleanly.

### Additional implementation verification

- Accepted residual gap: the axios param serialization inside
  `getBooks` (`read`/`unread` → `{ read: bool }`) stays untested. It is
  unchanged pre-existing code, user-reachable today via the filter buttons;
  not worth a unit test for this fix.
- Pre-existing race, out of scope: a filter click resolving while a CRUD
  refresh is in flight can apply out of order. Unchanged by this fix.
- Optional manual smoke (not required): run the Flask server and the Vue
  client against `http://localhost:5000`, select `unread`, add a read book,
  and observe the list stay filtered with `unread` pressed. Only for
  end-to-end confidence; the changed logic is fully covered at the component
  boundary.
