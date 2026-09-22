# Books CRUD refresh must keep and reapply the selected filter

The Books page (`client/src/components/Books.vue`) offers All / Read / Unread
filtering. After `add`, `update`, or `remove` triggers a collection refresh,
the component refetches without the filter, so the visible list falls back to
the unfiltered set while the filter button still shows as active. This task
records the planned fix only; implementation must not start until the plan is
approved.

## Requirements checklist

- [ ] The selected filter stays visibly active after add, update, and delete
      refreshes: `selectedFilter` is not reset and the filter buttons' state
      (`aria-pressed`) continues to reflect the current selection.
- [ ] The collection refresh after add, update, and delete re-applies the
      selected filter: the refetch passes the active filter, so the table
      shows the filtered result rather than the unfiltered list.
- [ ] The Flask API response shape is preserved: `server/app.py` is unchanged
      and responses keep `{"status": "success", "books": [...]}` (GET/POST)
      and `{"status": "success", "book": ...}` (PUT/DELETE).
- [ ] Unfiltered behavior is preserved: with the default `all` filter, CRUD
      refreshes continue to fetch the collection without a `read` query
      parameter and render all books.

## Open requirement questions and decisions changing scope or outcomes

None. The request fixes the outcomes: keep the filter active, reapply it on
CRUD refreshes, and leave the API response shape and unfiltered behavior
untouched. One consequence is implied by the approved requirement rather than
an open question: while `read`/`unread` is active, a mutation can leave the
refreshed list empty or without the mutated book (recorded under supporting
facts; it must not be "fixed" by switching to `all`).

## Research and supporting facts

- Regression location — fact: `client/src/components/Books.vue:30-41`;
  `add`, `update`, and `remove` refresh with `getBooks()` (no argument), which
  defaults to `"all"` in `client/src/api/books.js:3`. Each line is annotated
  `// regression: filter lost`.
- Visible defect — fact: the mutation methods never reset `selectedFilter`, so
  the buttons keep showing the filter as active (`:aria-pressed`,
  `Books.vue:7`) while the table shows the unfiltered list. The fix is the
  refetch argument; leaving `selectedFilter` untouched preserves the visible
  state.
- Transport and data layers already support the fix — fact:
  `client/src/api/books.js:3-6` maps `"read"`/`"unread"` to `?read=true|false`
  and `"all"` to no params; `server/app.py:15-20` already filters GET
  `/books` on the `read` query parameter. No server or api-module change is
  needed.
- Response shapes to preserve — fact: GET/POST `/books` return
  `{"status": "success", "books": [...]}`; PUT/DELETE `/books/<id>` return
  `{"status": "success", "book": ...}` (`server/app.py:10-30`). The client
  ignores mutation payloads and refetches via GET; keep that pattern.
- Implied consequence of the approved requirement — fact: while `read` or
  `unread` is active, an add or update can produce a list that does not
  contain the mutated book (e.g., adding an unread book while `read` is
  selected) or an empty list. Reapplying the active filter is the required
  behavior; do not auto-switch to `all`.
- Test infrastructure — fact: `client/tests/Books.spec.js` uses vitest and
  `@vue/test-utils` with the `../src/api/books` module mocked via `vi.mock`;
  per-test control is done by importing the mocked functions and using
  `mockImplementation` / `mock.calls`. The component performs no fetch on
  mount (`books` starts empty; the existing empty-state test relies on that).
- Suites — fact: client tests run via `npm test` (vitest run) in `client/`;
  server tests are `tests/test_books_api.py` (pytest, with `tests/conftest.py`
  mounting `server.app`). The server is unchanged, so its suite is only a
  cheap regression check.
- Environment — fact: `client/` has no `node_modules` or lockfile, so
  `npm install` in `client/` may be needed before `npm test`; pytest is
  available locally but `flask` must be importable in the active interpreter
  (`pyproject.toml` declares it).
- Documentation — fact: no maintained documentation describes the Books page
  filter behavior (`README.md` is a single line; `docs/development/index.md`
  has no relevant specification), so no documentation changes are required for
  this fix.

## Execution plan

Status: Draft

Approach: client-only change in `client/src/components/Books.vue`. Extract a
single `refresh()` method — `this.books = (await getBooks(this.selectedFilter)).data.books;`
— and use it from `selectFilter` (after assigning `selectedFilter`) and from
`add`, `update`, and `remove`. This removes the three duplicated unfiltered
refetches and makes "reapply the active filter" one code path. `selectedFilter`
is never written by mutation methods, so the buttons' `aria-pressed` state is
preserved without further changes. No changes to `client/src/api/books.js` or
`server/app.py`, and no changes to how mutations are issued or their responses
handled.

Scope boundaries:
- In scope: `Books.vue` and regression coverage in `client/tests/Books.spec.js`.
- Out of scope: server code, `api/books.js`, initial-mount fetching behavior,
  error handling for failed fetches, optimistic updates, filter-button
  styling, and persistence of the filter across page reloads.

Risks and executor notes:
- Async sequencing: each mutation awaits two promises (the mutation call,
  then the refetch); flush promises (`Promise.resolve()` / next tick) before
  asserting rendered output or call arguments.
- `vi.mock` factories are hoisted; import the mocked `getBooks`, `addBook`,
  `updateBook`, and `deleteBook` into the spec and configure return values per
  test instead of editing the factory.
- Keep the existing empty-state test passing: the component must continue to
  perform no fetch on mount.
- Do not "fix" the empty or shorter filtered list after a mutation by
  switching to `all`; reapplying the active filter is the specified behavior.

### Implementation decisions and open questions

- No open requirement questions; requirement outcomes are fixed by the request.
- Local implementation choice (reversible, resolved): a shared `refresh()`
  helper instead of repeating `getBooks(this.selectedFilter)` three times.
  Behavior is identical; the helper keeps a single fetch path for
  `selectFilter` and the three mutations.
- Behavior intentionally left as-is: no fetch on mount; mutation responses
  ignored in favor of a GET refetch.

### Documentation

- No documentation changes required. No maintained user or developer
  documentation describes the Books page filter behavior, so nothing becomes
  false and no new page is warranted. Do not create placeholder documentation.

### Task checklist

- [ ] Add regression tests to `client/tests/Books.spec.js`: after selecting
      `read` (and `unread`), each of add/update/remove refetches with the same
      filter, the refetched filtered list is rendered, and the selected button
      keeps `aria-pressed="true"` while the others are `false`; with `all`
      selected, CRUD refreshes refetch unfiltered.
- [ ] Implement the fix in `client/src/components/Books.vue` using a shared
      `refresh()` helper for `selectFilter`, `add`, `update`, and `remove`.
- [ ] Prepare the environment if needed (`npm install` in `client/`; ensure
      `flask` is importable), run `npm test` in `client/` and `pytest` at the
      repo root, and record the results.

### Requirement verification

- Selected filter stays visibly active (req 1): component tests asserting the
  filter buttons' `aria-pressed` state after selecting a filter and again
  after each CRUD refresh. Decisive boundary: the mounted `Books` component
  (real component logic; transport mocked at the api module).
- Filter reapplied on CRUD refresh (req 2): component tests asserting
  `getBooks` receives the selected filter value after each mutation and that
  the rendered table reflects the filtered refetch. The mocked api records the
  argument, which is exactly the regression point; api/server layers are
  unchanged.
- API response shape preserved (req 3): `git diff` shows `server/app.py`
  untouched, and the existing `tests/test_books_api.py` passes unchanged.
- Unfiltered behavior preserved (req 4): component tests asserting CRUD
  refreshes while `all` is selected call `getBooks` with `"all"` (the
  unchanged module then omits the `read` param), plus the existing server GET
  test covering the full collection.

### Additional implementation verification

- Not needed beyond the above. The change is confined to one component and its
  test; no cross-layer integration, persistence, or compatibility risk is
  introduced.