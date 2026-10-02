# Books filter persists through CRUD refreshes

After adding, editing, or deleting a book, the Books page refresh falls back to
the unfiltered list while the All/Read/Unread filter stays pressed. Plan the
client-side fix so CRUD refreshes reapply the selected filter, without touching
the API contract or unfiltered behavior. Planning only — not yet implemented.

## Requirements checklist

- [ ] After add, update (edit), or delete on the Books page, the collection
      refresh reuses the currently selected filter (`all`, `read`, or `unread`)
      via the same request path used by manual filter selection, instead of
      falling back to the unfiltered list.
- [ ] The selected filter remains visibly active across CRUD refreshes: the
      pressed-state binding (`aria-pressed`) still reflects `selectedFilter`,
      and the rendered list is consistent with that filter.
- [ ] The Books API contract is unchanged: no changes to endpoints, request
      handling, or response shapes (`{status, books}` for GET/POST,
      `{status, book}` for PUT/DELETE), and the parameter-less GET still
      returns the unfiltered collection.
- [ ] Unfiltered behavior is preserved: with `all` selected (the default),
      load and CRUD refreshes render the full book list.
- [ ] Changed behavior has focused evidence at the component boundary, and the
      existing client and server suites still pass.

## Questions and decisions

None requiring user input. The requested outcome is fully specified; remaining
choices below are local and reversible.

## Supporting details

- Bug location: `client/src/components/Books.vue` — `add`, `update`, and
  `remove` refresh with `getBooks()` (no argument, defaulting to `"all"`),
  each marked `// regression: filter lost`. `selectFilter(value)` is the only
  caller that passes the selection.
- `selectedFilter` is never mutated by CRUD methods, so `aria-pressed` already
  stays on the chosen button today. The visible defect is the unfiltered list
  contradicting the pressed filter; the fix must keep both consistent.
- `client/src/api/books.js` — `getBooks(filter = "all")` maps `"all"` to no
  query params and `"read"`/`"unread"` to `{ read: true/false }`. Unchanged by
  this fix.
- `server/app.py` — GET `/books` returns `{"status": "success", "books": [...]}`;
  `?read=true|false` filters, absent or other values return the full list.
  POST returns the same shape; PUT/DELETE return `{"status": "success",
  "book": <current>}`. The server already supports everything the fix needs;
  no server change is planned.
- The component fetches only inside `selectFilter` and the CRUD methods; there
  is no mount-time fetch, so first render shows "No books found." until an
  action runs. This behavior is out of scope and must not change.
- The template wires only the filter buttons; `add`/`update`/`remove` have no
  template wiring in this fixture, so component tests invoke the methods
  directly. Filter selection is exercised through real button clicks.
- Existing coverage: `client/tests/Books.spec.js` mocks the whole api module
  and asserts only the empty state; `tests/test_books_api.py` asserts status
  codes for GET and POST/PUT/DELETE. Neither covers the `read` query param or
  refresh filter behavior.
- A failed mutation currently skips the refresh (the mutation `await` throws
  before the fetch). Keep these semantics; do not add error handling.
- Environment facts from planning inspection: `client/node_modules` is not
  installed and `flask` is not importable from the active Python env, so no
  baseline test run was possible. Running the server suite requires executing
  `python3 -m pytest tests/` from the repo root (plain `pytest tests/` fails
  to import `server.app`); installing `flask` is required either way.

## Execution plan

Status: Draft

### Approach

Single client-side change in `client/src/components/Books.vue`, plus focused
test updates. No transport, routing, or server changes.

1. Add a private `refreshBooks()` method to `Books.vue` that fetches with the
   current selection: `this.books = (await getBooks(this.selectedFilter)).data.books`.
2. Call `refreshBooks()` from `selectFilter` (after assigning `selectedFilter`)
   and from `add`, `update`, and `remove` after their mutation awaits. This
   makes CRUD refreshes use the identical request path as manual filter
   selection, so the filter param mapping cannot drift between the two.
3. Leave `client/src/api/books.js`, `client/src/http.js`, and `server/app.py`
   untouched. With `all` selected the refresh sends no query params, preserving
   the unfiltered path.

### Tests

Extend `client/tests/Books.spec.js` (component boundary; the api module stays
mocked, with per-filter responses programmed via `vi.mocked(getBooks)`):

- Filtered refresh after each CRUD operation: select `read` (real button
  click), then call `add`, `update`, and `remove` (separate cases). Each case
  asserts `getBooks` was last called with `"read"`, the rendered list contains
  only the response for that filter, and the read button still has
  `aria-pressed="true"`.
- Unfiltered refresh preserved: with `all` selected, a CRUD refresh calls
  `getBooks("all")` and renders the full list.
- Filter selection baseline: clicking a filter button renders that filter's
  list with the correct pressed state, anchoring the refresh cases.

Supporting contract lock in `tests/test_books_api.py` (no code change): assert
GET `/books?read=true`, `?read=false`, and the no-param request return the
expected filtered/unfiltered `books` payloads. This pins the param contract the
fixed refresh depends on and gives the "unfiltered behavior" requirement direct
server-side evidence, which the current status-code-only test lacks.

### Risks

- Low overall. The component tests rely on the existing api-module mock, so
  the axios param mapping itself is covered only indirectly; the added server
  param assertions plus the unchanged `getBooks` mapping keep that contract
  observable.
- Both test toolchains must be installed before verification
  (`npm install` in `client/`; `flask` for the server suite).

### Exclusions

No server or transport changes, no error handling for failed mutations, no
mount-time initial fetch, no race handling for filter changes mid-refresh, and
no new documentation pages (see Documentation).

### Implementation decisions and open questions

- Extract `refreshBooks()` rather than repeating `getBooks(this.selectedFilter)`
  three times: one owner for the refresh path, matching `selectFilter`.
- Keep the current no-error-handling semantics: a rejected mutation still
  leaves the list untouched. Inventing failure behavior is out of scope.
- Component tests call `add`/`update`/`remove` directly because the template
  has no CRUD wiring in this fixture; this exercises the component's public
  methods without bypassing the component boundary where the bug lives.
- No requirement questions are open; no material decisions need approval.

### Documentation

No documentation changes planned. The README describes the app in one sentence
and makes no claims about filtering; `docs/development/index.md` records that
no book-discovery specification exists. No maintained page describes the
filter behavior, so nothing becomes stale, and the smallest helpful structure
is to add none.

### Task checklist

- [ ] Add `refreshBooks()` to `Books.vue` and use it in `selectFilter`, `add`,
      `update`, and `remove` so refreshes carry `selectedFilter`.
- [ ] Extend `client/tests/Books.spec.js` with the filtered-refresh,
      unfiltered-refresh, and filter-selection cases described above.
- [ ] Extend `tests/test_books_api.py` with `read`-param and no-param response
      assertions (supporting evidence).
- [ ] Install client deps (`npm install` in `client/`) and run `npm test`;
      install `flask` and run `python3 -m pytest tests/` from the repo root;
      record results.

### Requirement verification

- Filter reapplied after add/update/remove → client component tests: after
  each CRUD method, `getBooks` last called with the selected filter and the
  rendered list matches that filter's mocked response. Decisive at the
  component ↔ api-client boundary where the regression lives.
- Filter visibly active across refreshes → same tests assert the selected
  button keeps `aria-pressed="true"` after the refresh and the rendered list
  matches it.
- API response shape and unfiltered behavior preserved → no diffs to
  `server/app.py`, `client/src/api/books.js`, `client/src/http.js`; component
  test proves an `all`-selected CRUD refresh renders the full list; server
  suite passes unchanged, with the added param assertions documenting the
  no-param response.
- Focused evidence + green suites → client `npm test` and server
  `python3 -m pytest tests/` runs collecting cleanly (requires dependency
  installation; not runnable in the planning environment).

### Additional implementation verification

None beyond the above. The only distinct risk — the axios param mapping — is
unchanged code exercised identically by the already-working filter buttons;
the supporting server assertions cover its downstream contract.