# Books filter lost on CRUD refresh

The Books page filters by All, Read, or Unread, but after add, update, or delete
the refresh re-fetches the collection without the selected filter, so the list
reverts to all books while the filter button stays visibly active. Fix the
client so every CRUD refresh re-applies the active filter, without changing the
API contract.

## Requirements checklist

- [ ] After add, update, or delete, the selected filter remains visibly active
  and the refresh re-fetches the collection with that filter applied, so the
  displayed list matches the active filter button (including the approved
  consequence that a book falling outside the active filter does not appear
  after the refresh).
- [ ] Unfiltered behavior is preserved: with the "all" filter selected
  (including the component's default state), GET /books sends no `read` query
  parameter and shows the full collection, on selection and after CRUD
  refreshes.
- [ ] The API contract is unchanged: server routes, request parameters, and
  response bodies (`{"status": "success", "books": [...]}` for GET/POST and
  `{"status": "success", "book": ...}` for PUT/DELETE) stay as they are; the
  fix reuses the existing `read` query parameter on the client.
- [ ] Existing filter-selection behavior is retained: clicking a filter
  immediately fetches and renders that filter's list and updates the active
  button state.
- [ ] Focused regression evidence covers the changed behavior: filter
  reapplication after each CRUD operation, the visibly active filter, and the
  unfiltered path (project testing policy).

## Unresolved requirement questions

None. The requested outcome, the preserved API shape, and the unfiltered
behavior are explicit in the request; remaining choices are local and
reversible (see the plan).

## Supporting details

Facts verified from the current code:

- The bug is in `client/src/components/Books.vue`. `add`, `update`, and
  `remove` each call `getBooks()` with no argument (lines 32, 36, 40), which
  falls back to the `"all"` default. `selectedFilter` is never reset, so the
  filter button keeps its `aria-pressed` state — the defect is a mismatch
  between the visibly active filter and the unfiltered list, not a lost
  selection.
- The client API layer already supports the fix:
  `client/src/api/books.js` `getBooks(filter)` maps `"all"` to no params,
  `"read"` to `{read: true}`, and `"unread"` to `{read: false}`. No change
  needed there.
- The server already honors the filter: `server/app.py` GET /books filters on
  the `read` query parameter (`true`/`false`) and returns
  `{"status": "success", "books": [...]}`. PUT/DELETE return
  `{"status": "success", "book": ...}`. No server change is planned.
- Existing tests: `client/tests/Books.spec.js` (Vitest + @vue/test-utils, one
  empty-state test, API module mocked) and `tests/test_books_api.py` with
  `tests/conftest.py` (pytest against the in-memory `BOOKS` list on the shared
  app module; the existing mutation test adds and then deletes its book, so it
  is state-neutral).
- Pre-existing, out-of-scope observations (do not "fix" silently): the
  component performs no fetch on mount, so the initial render is the empty
  state until a filter action occurs; there is no request-ordering guard for
  overlapping refreshes; the CRUD methods are not wired to in-component UI
  events in this fixture.

## Execution plan

Status: Draft

### Design

The fix lives entirely in `client/src/components/Books.vue`; nothing else
changes. Give the component a single refresh path so the active filter cannot
be dropped again:

- Add `async refreshBooks()` that sets `this.books` from
  `(await getBooks(this.selectedFilter)).data.books`.
- `selectFilter(value)` sets `this.selectedFilter = value`, then awaits
  `refreshBooks()` — same behavior as today, one code path.
- `add`, `update`, and `remove` await their mutation call, then await
  `refreshBooks()` instead of calling `getBooks()` unfiltered. This reapplies
  the active filter on every CRUD refresh and leaves `selectedFilter`
  untouched, so the button's visible state is unchanged.

No changes to `client/src/api/books.js` (its filter→params mapping already
preserves the unfiltered behavior for `"all"`), `client/src/http.js`, or
`server/app.py` (response shapes stay identical).

Approved consequence: with a non-"all" filter active, a mutated book outside
that filter (new unread book while "read" is active, a PUT that flips
`read`, or deleting the last matching book) will not appear in the refreshed
list; deleting the last match shows the empty state. This follows directly
from the requested reapplication and is expected, not a bug.

### Steps

1. Add the `refreshBooks()` method in `Books.vue` and route `selectFilter`,
   `add`, `update`, and `remove` through it as described above.
2. Extend `client/tests/Books.spec.js` with the decisive component tests
   (verification below), using the existing API-module mock pattern with
   distinguishable filtered lists per call.
3. Add a small unit test for the `getBooks` filter→params mapping (`"all"` →
   `{}`, `"read"` → `{read: true}`, `"unread"` → `{read: false}`) with `http`
   mocked.
4. Run the client Vitest suite and the Python pytest suite; record results and
   update the task checklist.

### Implementation decisions and open questions

- Resolved local choice: use a single `refreshBooks()` path rather than
  passing `this.selectedFilter` at the three call sites. The helper removes
  the triplication that caused the regression and gives one place to change
  later; the alternative is a smaller diff but keeps three copies. Local and
  reversible; no material decision.
- No material open questions: no public API, persisted data, compatibility,
  security, or user-visible contract changes beyond the requested behavior.
- Known limitation not addressed (pre-existing, out of scope): overlapping
  refreshes have no ordering guard, so interleaved responses could overwrite a
  newer list with a stale one; this exists today for filter clicks and is not
  part of the requirement.

### Documentation

No maintained documentation describes filter or refresh behavior. `README.md`
is a one-line capability statement, and `docs/development/index.md` records
that no book-discovery specification exists. No documentation changes are
planned: the fix makes current UI behavior consistent, introduces no new
public claims, and creating specification pages would violate the smallest
-structure rule.

### Task checklist

- [ ] Add `refreshBooks()` in `Books.vue`; route `selectFilter`, `add`,
  `update`, `remove` through it so CRUD refreshes reapply `selectedFilter`.
- [ ] Extend `client/tests/Books.spec.js`: after selecting "read" (and a
  variant for "unread" or parameterized), each of add/update/remove triggers
  `getBooks` with the selected filter, the rendered list matches the mocked
  filtered response, and `aria-pressed` stays on the selected filter only.
- [ ] Extend `client/tests/Books.spec.js`: with "all" selected, CRUD refreshes
  call `getBooks("all")` and the full mocked list renders.
- [ ] Add unit test for the `getBooks` filter→params mapping.
- [ ] Run `npm test` in `client/` and `pytest` at the repo root; existing
  tests pass unchanged; record results.

### Requirement verification

- Selected filter reapplied and visibly active after CRUD → decisive evidence:
  the extended component test in `client/tests/Books.spec.js`, which crosses
  the component→API boundary with the API module mocked. The mock supplies
  canned responses but does not bypass the component logic under test
  (reapplication and active state are asserted from real component behavior).
- Unfiltered behavior preserved → component assertions that CRUD refreshes
  with "all" call `getBooks("all")`, plus the mapping unit test proving
  `"all"` sends no `read` param, plus the existing pytest GET /books test
  passing unchanged.
- API contract unchanged → the change touches no server or API-layer file
  (verifiable by diff), and the existing pytest suite passes without
  modification.
- Filter-selection behavior retained → the same component test's
  select-then-render assertions (click → fetch with filter → rendered rows →
  active button state).
- Regression evidence → the updated Vitest suite collects and exits cleanly
  and the pytest suite runs clean.

### Additional implementation verification

- The server-side filtered GET (`?read=true|false`) is unchanged existing
  behavior and currently has no automated coverage; this task does not expand
  server tests. If a whole-chain confirmation is desired, an optional manual
  smoke (run the Flask app and the Vue client, select "read", add a read book,
  toggle and delete it, observe list and button) closes that gap by
  observation; it is not required for completion.