# Books filter persists through CRUD refresh

After adding, editing, or deleting a book, the Books page refreshes the
collection with the unfiltered list even when a Read/Unread filter is active.
The fix makes every collection refresh reuse the currently selected filter,
keeps the filter visibly active, and leaves the API contract untouched.

## Requirements checklist

- [ ] After a completed add, update, or delete, the collection refresh requests
      the currently selected filter, so the rendered list matches the selected
      All/Read/Unread filter instead of falling back to the unfiltered list.
- [ ] The selected filter stays visibly active across CRUD refreshes: the
      active-state indicator (`aria-pressed` on the filter buttons) remains on
      the selected filter and stays consistent with the rendered list.
- [ ] The existing API contract is preserved with no server-side changes:
      `GET /books` keeps the `{"status": "success", "books": [...]}` response
      shape, `?read=true|false` filtering is unchanged, requests without the
      `read` parameter still return all books, and the exported signatures in
      `client/src/api/books.js` are unchanged.

## Questions and decisions

No unresolved requirement questions. No material design decisions: the fix is
confined to one client component with no interface, data, compatibility, or
user-visible contract change beyond the required behavior itself.

## Supporting details

- Root cause (fact): `client/src/components/Books.vue:32`, `:36`, and `:40` —
  `add`, `update`, and `remove` each call `getBooks()` with no argument, and
  the default in `client/src/api/books.js:3` is `"all"`. Each site is marked
  `// regression: filter lost`.
- `selectedFilter` is never reset by CRUD today (fact), so `aria-pressed`
  already persists; the defect is only the fetch argument, which makes the
  list diverge from the active filter.
- Correct pattern already in the file (fact): `selectFilter`
  (`Books.vue:26-29`) sets `selectedFilter` then fetches with it. The fix
  extends that pattern to the CRUD refreshes.
- Filter-to-query mapping (fact): `getBooks(filter)` sends no params for
  `"all"` and `?read=true|false` otherwise
  (`client/src/api/books.js:3-6`). The Flask route filters on the `read`
  query param and returns `{"status": "success", "books": [...]}`;
  POST returns the same books-list shape, PUT/DELETE return
  `{"status": "success", "book": ...}` (`server/app.py:10-30`). None of this
  changes.
- Fetch triggers (fact): the component has no on-mount fetch; the only fetch
  paths are `selectFilter` and the three CRUD methods. The template has no
  CRUD form, so the component methods are the only entry points for
  add/update/remove in this fixture.
- Existing tests (fact): `client/tests/Books.spec.js` has one empty-state test
  and mocks the API module via `vi.mock("../src/api/books")`, which resolves
  to the same module the component imports. `tests/test_books_api.py` covers
  unfiltered `GET /books` plus mutation status codes. Nothing covers
  `?read=` filtering or post-CRUD refresh behavior.
- Test entry points (fact): `npm test` in `client/` (vitest), `pytest` at the
  repo root (conftest imports `server.app`).
- Assumption: `Books.vue` is the only consumer of the `getBooks` API wrapper;
  no other client source files exist in the fixture.

## Implementation plan

Status: Draft

### Design

Make `selectedFilter` the single source for every collection refresh inside
`Books.vue`. Add a `refreshBooks()` method that performs
`this.books = (await getBooks(this.selectedFilter)).data.books` and route all
four fetch paths through it:

- `selectFilter(value)` sets `this.selectedFilter = value`, then awaits
  `refreshBooks()` — identical observable behavior to today.
- `add`, `update`, and `remove` await their mutation call, then await
  `refreshBooks()`, replacing the three unfiltered refreshes and dropping the
  `// regression: filter lost` comments.

No changes to `client/src/api/books.js`, `client/src/http.js`, or
`server/app.py`. The `filter = "all"` default stays, so the never-filtered
flow keeps fetching the full list exactly as before, and the axios request
for `all` continues to send no `read` parameter.

### Verification strategy

Decisive client evidence is a component test in `client/tests/Books.spec.js`
that makes the `getBooks` mock respond based on its filter argument, so the
rendered rows differ between `all` and `read`. One test exercises the
production path through the real DOM for filter selection (click the `read`
button, assert filtered rows and `aria-pressed`) and then invokes the exposed
`add`, `update`, and `remove` methods, asserting each one re-fetches with
`"read"` and leaves the filtered rows and `aria-pressed` intact. A companion
case confirms CRUD without a prior selection still fetches `"all"`.

Server-side contract evidence extends `tests/test_books_api.py` with a
filtered `GET /books?read=true|false` assertion returning only matching books
in the unchanged response shape; the existing `test_books` already covers the
unfiltered shape.

Named gaps: the real axios transport and the live client↔server round trip
are not exercised — the component test mocks the API module and the pytest
suite tests the server in isolation, and the fixture has no E2E harness.
Visual active state beyond `aria-pressed` does not exist to verify.

### Order logic

Single-layer client change, so ordering is simple: component change first,
then its regression test, then `npm test` (milestone 1 — the fix is complete
and demonstrable). The server contract test is an independent guard for the
requirement the fix depends on and can land in the same change; `pytest`
closes milestone 2. Either milestone stops safely; there are no cross-task
dependencies.

### Risks and way back

- Blast radius is one component plus two test files; no server, API wrapper,
  or transport changes, so no compatibility or persisted-data risk.
- Refactoring `selectFilter` could accidentally change its behavior —
  mitigated by delegating to the same `refreshBooks()` helper so its fetch
  semantics stay identical.
- Tests invoking `wrapper.vm.add/update/remove` could mask template wiring —
  acceptable because CRUD has no UI in this fixture; the filter path is still
  exercised through a real DOM click.
- Rollback: revert `Books.vue` and the two test files. No data, config, or
  generated artifacts are involved.

### Implementation decisions and open questions

- Decided (local, reversible): fix confined to `Books.vue` using a shared
  refresh helper; the `getBooks` `"all"` default is kept so the no-selection
  flow is untouched.
- Decided: client tests invoke the exposed component methods for CRUD because
  the fixture ships no CRUD form; these methods are the only entry points.
- Open question: none. A failed refresh after a successful mutation keeps the
  current semantics (no added error handling or state rollback) — behavior
  was unspecified and none is invented.

### Documentation

No maintained documentation claims filter or refresh behavior: `README.md` is
a one-line summary and `docs/development/index.md` records that no
book-discovery specification exists. No documentation updates are required,
and the change introduces no new public claims.

### Task checklist

- [ ] Add `refreshBooks()` to `client/src/components/Books.vue`; route
      `selectFilter`, `add`, `update`, and `remove` through it; remove the
      three `// regression: filter lost` comments
- [ ] Extend `client/tests/Books.spec.js`: filter argument drives the mocked
      response; add/update/remove re-fetch with the selected filter and keep
      rows plus `aria-pressed` consistent; unselected (`all`) flow unchanged
- [ ] Extend `tests/test_books_api.py`: `GET /books?read=true|false` returns
      only matching books in the unchanged `{"status", "books"}` shape
- [ ] Run `npm test` in `client/` and `pytest` at the repo root; both exit
      clean

### Requirement verification

- Filter reapplied after CRUD (R1) and filter stays visibly active (R2) →
  `client/tests/Books.spec.js` regression: after each CRUD invocation the
  `getBooks` mock is called with the selected filter and the rendered rows
  and `aria-pressed` match it; the `all` case proves the unfiltered flow.
  Deliberately not covered: real axios transport and the full client↔server
  round trip (no E2E harness exists); server filtering is verified separately
  at the server boundary.
- API contract preserved, no server changes (R3) → the extended
  `tests/test_books_api.py` filtered-GET assertion plus an empty diff on
  `server/app.py` and `client/src/api/books.js`; the existing `test_books`
  already proves unfiltered behavior and shape.
