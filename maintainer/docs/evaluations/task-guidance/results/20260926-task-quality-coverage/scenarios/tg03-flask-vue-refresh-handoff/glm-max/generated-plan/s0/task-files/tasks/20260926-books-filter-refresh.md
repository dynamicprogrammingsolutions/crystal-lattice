# Books page: keep selected filter applied across CRUD refreshes

After adding, editing, or deleting a book, the Books page refreshes the
collection without the active status filter, so an All/Read/Unread selection
stops matching the displayed list. Plan only — implementation requires plan
approval.

## Requirements checklist

- [ ] After add, update, or delete completes, the Books page refreshes the
  collection using the currently selected filter (`all`, `read`, `unread`),
  so the displayed list keeps matching the active filter instead of
  reverting to all books.
- [ ] The selected filter stays visibly active through CRUD refreshes: the
  selection is not reset and the active indication (`aria-pressed` on the
  selected filter button, the only active-state mechanism in the template)
  persists.
- [ ] Clicking All / Read / Unread continues to fetch and display the
  matching list exactly as today (existing filter-selection behavior
  preserved).
- [ ] The Flask API contract is unchanged: `GET`/`POST /books` keep the
  `{"status", "books"}` response shape, `PUT`/`DELETE /books/<id>` keep
  `{"status", "book"}`, and a `GET /books` without a `read` parameter still
  returns all books.

No unresolved requirement questions; the requested outcome is fully
specified.

## Research and supporting facts

**Bug location** — `client/src/components/Books.vue`: `add`, `update`, and
`remove` refresh with `getBooks()` (defaults to `"all"`, see
`client/src/api/books.js:3`), so the re-fetched collection ignores
`selectedFilter` while the filter button still shows as pressed (in-code
markers at `client/src/components/Books.vue:32,36,40`). `selectFilter`
already fetches with the filter (`client/src/components/Books.vue:28`).

**Server already supports filtered reads** — `GET /books` accepts
`read=true|false` and returns only matching books (`server/app.py:15-20`);
the client mapping `filter → read` param already exists in `getBooks`
(`client/src/api/books.js:3-6`). No API change is needed; the fix is
confined to the component.

**Empty filtered result** — deleting the last book matching the filter
renders the existing `v-else` empty state ("No books found."), so no new UI
state is required (`client/src/components/Books.vue:13-16`).

**Test seams** — client tests are Vitest + `@vue/test-utils` with the api
module mocked (`client/tests/Books.spec.js`); the api layer imports a single
axios instance from `client/src/http.js`, which can be mocked to observe
request params. Server tests use the Flask test client
(`tests/conftest.py`). The `read`-param filtering path on the server is
currently untested.

**Docs** — `docs/development/index.md` records that no book-discovery
specification exists, and no maintained doc describes the filter behavior,
so this fix requires no documentation change.

## Execution plan

Status: Draft

### Approach

Client-only change in `client/src/components/Books.vue`. Introduce one
`refreshBooks()` method that fetches with the current selection:

```js
async refreshBooks() {
  this.books = (await getBooks(this.selectedFilter)).data.books;
}
```

and route every collection refresh through it:

- `selectFilter(value)` — set `selectedFilter`, then `refreshBooks()`
  (behavior identical to today).
- `add(book)` / `update(book)` / `remove(id)` — await the mutation call,
  then `refreshBooks()`. Because `selectedFilter` is never reset, the filter
  button stays visibly active, and the re-fetched collection is already
  filtered by the server (`read=true|false` param; no params for `all`).

No changes to `client/src/api/books.js`, `client/src/http.js`, or
`server/app.py`: response shapes and unfiltered behavior are untouched,
which satisfies the API-preservation constraint by construction.

Alternative rejected: filtering client-side after an unfiltered fetch. It
would duplicate the selection logic the `read` param already implements and
change the request pattern the API supports.

### Verification strategy

No single automated test can traverse Vue + axios + Flask in this fixture
(no browser harness), so the chain is verified at each real boundary, with
the component test closest to the user boundary:

1. **Component tests** (extend `client/tests/Books.spec.js`, api module
   mocked with per-filter payloads): after selecting `read` (and `unread`),
   invoking `add`, `update`, and `remove` on the mounted component must
   re-fetch with the selected filter (assert `getBooks` called with
   `"read"`/`"unread"`, not the `"all"` default), render the rows from the
   filtered payload, and keep `aria-pressed="true"` on the selected filter
   button. Also assert the `all` selection still fetches without filter
   args. Await promise flushes with `flushPromises` from `@vue/test-utils`
   (the refresh is a chained async call).
2. **API unit test** (new, e.g. `client/tests/api-books.spec.js`,
   `../src/http` mocked): `getBooks("read")` requests `/books` with
   `params {read: true}`, `getBooks("unread")` with `{read: false}`, and
   `getBooks()` / `getBooks("all")` with no params — closing the middle
   link of the chain.
3. **Server tests** (extend `tests/test_books_api.py`): `GET
   /books?read=true` and `?read=false` return only matching books with the
   `{"status", "books"}` shape, and `GET /books` without the param returns
   all books in the same shape — guarding the unfiltered behavior the fix
   must preserve.
4. **Suites**: run `npm test` in `client/` and `pytest` at the repo root;
   both must collect and exit cleanly.

### Implementation decisions and open questions

- Decision (local, reversible): implement the fix client-side by reusing the
  existing `getBooks(filter)` mapping in a shared `refreshBooks()` method;
  no API parameter, response-shape, or server change.
- Decision (local, reversible): keep `selectedFilter` untouched during CRUD
  refreshes rather than re-deriving it; the refresh call passes the current
  selection.
- No open questions. Non-goals carried from the request: no changes to API
  shape or unfiltered behavior; no new filter UI; no error-handling
  behavior added for failed mutations (current semantics retained).

### Documentation

None required. No maintained documentation describes the Books filter
behavior (`README.md` covers only the page/API relationship;
`docs/development/index.md` records that no book-discovery specification
exists), and the fix restores intended behavior without changing any public
contract.

### Task checklist

- [ ] Add `refreshBooks()` in `Books.vue` fetching with `selectedFilter`
- [ ] Route `add` / `update` / `remove` refreshes through `refreshBooks()`
- [ ] Route `selectFilter` through `refreshBooks()` (behavior unchanged) and
  drop the "regression: filter lost" comments
- [ ] Extend `client/tests/Books.spec.js` with CRUD-refresh filter
  persistence and `aria-pressed` coverage for `read` and `unread`, plus
  `all` no-param behavior
- [ ] Add api param-mapping unit test for `getBooks`
- [ ] Extend `tests/test_books_api.py` with `read`-param filtering and
  unfiltered shape checks
- [ ] Run `client` Vitest suite and root pytest suite; both exit clean

### Requirement verification

- **CRUD refresh re-applies the selected filter** → component tests in
  `client/tests/Books.spec.js`: mocked api asserts `getBooks` receives the
  selected filter after `add`/`update`/`remove`, and rendered rows match the
  filtered payload (Vue component boundary; transport mocked one layer
  down).
- **Filter stays visibly active** → same component tests assert the selected
  filter button keeps `aria-pressed="true"` after CRUD refreshes.
- **Filter-selection behavior preserved** → component test asserts clicking
  All/Read/Unread fetches with/no params and renders the matching list.
- **API shape and unfiltered behavior preserved** → server tests in
  `tests/test_books_api.py` assert the `{"status", "books"}` and
  `{"status", "book"}` shapes and that `GET /books` without `read` returns
  all books; combined with zero diff to `server/app.py` and the api unit
  test pinning `all` → no params.

### Additional implementation verification

- Run both suites together as the final step to catch cross-layer drift
  (client expectations vs. server behavior).
- Confirm `getBooks`'s default remains `"all"` so existing unfiltered
  callers keep their behavior.