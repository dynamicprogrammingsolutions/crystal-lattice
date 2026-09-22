# Books CRUD refresh must reapply the selected status filter

The Books page filter (`all`/`read`/`unread`) is dropped when add, update, or
delete refreshes the collection: those refreshes call `getBooks()` with the
default `all` filter, so the list shows unfiltered books while the filter
control still shows the previous selection as active. The fix is client-side;
the API contract and unfiltered behavior are preserved.

## Requirements checklist

- [ ] After a successful add, update, or delete, the collection refresh reuses
  the currently selected filter (`all`/`read`/`unread`) so the displayed books
  match the active filter. Refresh moments and component method signatures
  (`selectFilter(value)`, `add(book)`, `update(book)`, `remove(id)`) are
  unchanged, and refresh still happens only after the mutation succeeds.
- [ ] The selected filter remains visibly active across CRUD refreshes: the
  filter control's active/pressed state continues to reflect the user's
  selection and is not reset or desynced from the refreshed list.
- [ ] Flask API endpoints and response shapes are unchanged: `GET /books` →
  `{"status": "success", "books": [...]}`, `POST /books` →
  `{"status": "success", "books": [...]}`, `PUT/DELETE /books/<id>` →
  `{"status": "success", "book": ...}`. The fix is client-side only.
- [ ] Unfiltered behavior is preserved: `all` (the default) continues to fetch
  every book with no `read` query parameter, both when the filter is selected
  and during CRUD refreshes while `all` is selected.

## Questions and decisions

- No unresolved requirement questions. Interpretation used for planning:
  "visibly active" means the existing active-state signal (`aria-pressed` on
  the filter buttons, `client/src/components/Books.vue:7`) stays correct and
  consistent with the list; no new styling is requested. Flagged for
  confirmation at plan approval.

## Supporting facts

- Regression location: `client/src/components/Books.vue:32,36,40` —
  add/update/remove refetch with `getBooks()` (default `all`), discarding the
  selection (marked `// regression: filter lost`). `selectedFilter` is not
  reset, so the control stays pressed while the list becomes unfiltered —
  the reported state/content mismatch.
- Filter mechanics: buttons iterate `['all', 'read', 'unread']`
  (`client/src/components/Books.vue:5`); `selectedFilter` defaults to `"all"`
  (`client/src/components/Books.vue:24`); `selectFilter` already fetches with
  the chosen value (`client/src/components/Books.vue:26-29`).
- Client transport already supports filters: `getBooks(filter = "all")` sends
  no params for `all` and `{ read: true|false }` otherwise
  (`client/src/api/books.js:3-6`). No client API change is needed.
- Server contract (`server/app.py:10-30`): GET filters via `?read=true|false`;
  POST appends and returns `{"status", "books"}`; PUT/DELETE return
  `{"status", "book"}`. This fix does not touch the server, which preserves
  the response shapes.
- There is no mounted/initial fetch; the list loads only via `selectFilter`
  or a CRUD refresh. Initial-load behavior is out of scope.
- Existing coverage: `client/tests/Books.spec.js` mocks the api module and
  only checks the empty state; `tests/test_books_api.py` covers unfiltered
  GET and the CRUD happy path. Nothing pins the CRUD-refresh filter today.
- Rejected approach: resetting the filter to `all` after mutations, or
  refetching without params — both reintroduce the reported inconsistency.
  No server-side filter persistence is needed.

## Execution plan

Status: Draft

Approach — single-layer client fix. The capability touches no other layer
with an independently useful or owned result, so no per-layer split.

1. `client/src/components/Books.vue`: add a `refresh()` method that sets
   `this.books = (await getBooks(this.selectedFilter)).data.books;` and call
   it from `selectFilter`, `add`, `update`, and `remove`. This makes the
   selected filter the single source of truth for every refresh and keeps the
   pressed state consistent with the list.
2. No changes to `client/src/api/books.js` or `server/app.py`; request and
   response handling is untouched, preserving API shapes and unfiltered
   behavior.

Verification:

- Extend `client/tests/Books.spec.js`: after `selectFilter("read")`, invoke
  `add`, `update`, and `remove`, asserting the mocked `getBooks` was last
  called with `"read"` after each refresh and the `read` button still has
  `aria-pressed="true"`. Add an `all`-path assertion (select `all`, then
  `add` → last call `"all"`). Keep the existing empty-state test passing.
  Tests must call methods via `wrapper.vm` because the fixture wires no CRUD
  controls to these methods.
- New `client/tests/api-books.spec.js` (mock `../src/http`): pin the
  `getBooks` mapping — `all` → `GET /books` with `{ params: {} }`, `read` →
  `{ params: { read: true } }`, `unread` → `{ params: { read: false } }`.
- Run `npm test` in `client/` and `pytest` at the repo root; existing server
  tests must pass untouched (no diffs under `server/` or `client/src/api/`).

Risks / notes:

- Component tests assert the api-client seam with a mock; they do not catch
  param-mapping regressions in `api/books.js` — mitigated by the new api spec.
- If a mutation rejects, no refresh occurs (unchanged behavior; no new error
  handling is introduced).
- No e2e layer exists in this fixture; component + api unit tests are the
  proportionate evidence.

Exclusions: initial-load fetching, filter control styling, server changes,
CRUD error handling, new documentation pages.

### Implementation decisions and open questions

- Decision (local, resolved): extract `refresh()` rather than repeating
  `getBooks(this.selectedFilter)` in three methods — removes the duplication
  that caused the regression and keeps `selectedFilter` authoritative.
- Open questions: none. The "visibly active" interpretation above is the only
  judgment call; confirm it at approval.

### Documentation

None required. No maintained documentation describes the filter or refresh
behavior (`README.md:3` is generic; `docs/development/index.md:3` records that
no book-discovery specification exists). The change restores intended behavior
without introducing new public claims, so no pages are added or edited. If
maintained docs describing refresh behavior are discovered during execution,
update them in the same change.

### Task checklist

- [ ] Add `refresh()` to `Books.vue` and route `selectFilter`/`add`/`update`/
  `remove` through it; remove the stale `// regression: filter lost` markers.
- [ ] Extend `client/tests/Books.spec.js` with CRUD-refresh filter and
  `aria-pressed` coverage (read path and all path).
- [ ] Add `client/tests/api-books.spec.js` pinning the filter→params mapping.
- [ ] Run the client vitest suite and root pytest suite; confirm green and no
  server/api diffs.

### Requirement verification

- Filter reused on CRUD refresh → component test: mocked `getBooks` last
  called with the selected filter after each of add/update/remove (boundary:
  component→api-client seam; the mock records the argument the fix controls
  rather than bypassing the behavior under test).
- Filter stays visibly active → component test: `aria-pressed="true"` on the
  selected button after each CRUD refresh (boundary: rendered component DOM).
- API response shapes preserved → no diff to `server/app.py` or
  `client/src/api/books.js` handling; existing `tests/test_books_api.py`
  passes unmodified (boundary: Flask test client).
- Unfiltered behavior preserved → api spec asserts `all` → `GET /books` with
  empty params; the existing unfiltered server test passes; the component
  `all`-path assertion (boundary: client request contract + Flask test
  client).

### Additional implementation verification

- Optional, cheap server pin: extend `tests/test_books_api.py` with a
  `GET /books?read=true` assertion returning only read books. That behavior
  is pre-existing and unchanged by this fix; include it only if desired when
  executing.