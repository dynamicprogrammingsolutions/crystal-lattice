# Preserve selected Books filter across CRUD refreshes

The Books page (`client/src/components/Books.vue`) offers All/Read/Unread
filtering, but its add, update, and remove flows refresh the collection with
the default unfiltered request, so the rendered list stops matching the
still-active filter. This task plans the client-side fix. Planning only — no
code changes have been made.

## Requirements checklist

- [ ] After `add`, `update`, or `remove`, the Books page refreshes the
      collection using the currently selected filter, so the rendered list
      matches the active All/Read/Unread selection. The selection is
      reapplied, not reset.
- [ ] The selected filter remains visibly active through CRUD refreshes: the
      active filter button keeps `aria-pressed="true"` and the rendered list
      corresponds to that same filter.
- [ ] Existing filter-switching behavior is preserved, including All
      rendering the unfiltered collection and Read/Unread sending their
      respective filter requests.
- [ ] The Flask API contract is unchanged: response shapes
      (`{"status", "books"}` for the collection endpoints, `{"status",
      "book"}` for item mutations) and unfiltered `GET /books` behavior
      remain as implemented; the fix requires no server changes.

Unresolved requirement questions: none.

## Supporting details

**Facts**

- The regression is entirely in `client/src/components/Books.vue`:
  `add` (line 32), `update` (line 36), and `remove` (line 40) call
  `getBooks()` with the default `"all"` filter, while `selectFilter`
  (lines 26–29) correctly passes `selectedFilter`. `selectedFilter` is never
  reset by CRUD, so the button's pressed state stays on the old selection
  while the list silently falls back to the unfiltered collection.
- `client/src/api/books.js:3-6` maps `getBooks(filter = "all")` to no query
  params for `"all"` and `read: true|false` for `"read"`/`"unread"`;
  `server/app.py:10-20` filters `GET /books` on a `read=true|false` query
  param and returns all books otherwise. Reapplying the filter is therefore
  purely a client-side change: pass `selectedFilter` through the CRUD
  refresh calls.
- Reapplying the filter implies a newly added book that does not match the
  active filter will not appear until the user changes filters. This follows
  from the request; auto-switching the filter to make a new item visible was
  rejected because it contradicts "keep the selected filter."
- Known limitation, unchanged by this fix: if the user switches filters while
  a CRUD refresh is in flight, responses can resolve out of order; no request
  ordering or cancellation exists today and none is added.
- The component template exposes no add/edit/delete controls; `add`,
  `update`, and `remove` are invoked programmatically, so component tests
  must drive them via the component instance.
- Test tooling in this workspace: `pytest` 9.1.1 is available but `flask` is
  not installed, and the client has no `node_modules`, so executing
  verification requires installing `flask` and running `npm install` in
  `client/`. `client/tests/Books.spec.js` currently mocks the API module and
  covers only the empty state.
- The initial file read in this session rendered mangled punctuation for
  `server/app.py` and `client/src/api/books.js`; hex dumps and
  `python3 -m py_compile` confirmed the actual sources are well-formed. Do
  not "fix" syntax errors from that stale view — there are none.

## Execution plan

Status: Draft

### Implementation decisions and open questions

- Decision: reapply `selectedFilter` after each CRUD mutation instead of
  resetting to All. Resetting would contradict the explicit request.
- Decision: add a shared `refresh()` method to the Books component that
  fetches with the active selection and reuse it from `selectFilter`,
  `add`, `update`, and `remove` (`selectFilter` sets `selectedFilter`
  first). Local and reversible; avoids repeating the filtered call in three
  methods.
- Decision: no changes to `client/src/api/books.js`, `client/src/http.js`,
  or `server/app.py`. When the filter is All, `getBooks("all")` sends no
  params, so unfiltered refresh behavior is preserved exactly; the server
  response shapes are untouched.
- No template change is needed: the pressed state already derives from
  `selectedFilter`, which is untouched; once the list matches the filter
  again the visible state is consistent.
- Open questions: none.

### Documentation

- No maintained documentation describes the Books filter behavior: the root
  `README.md` is one generic sentence and `docs/development/index.md`
  records that no book-discovery specification exists. No documentation
  changes are planned, and no placeholder pages will be created for this
  fix.

### Task checklist

- [ ] Update `client/src/components/Books.vue` so `add`, `update`, and
      `remove` refresh through a shared `refresh()` that passes
      `selectedFilter` to `getBooks` (and have `selectFilter` reuse it).
- [ ] Extend `client/tests/Books.spec.js` with component tests: for each of
      add/update/remove with Read or Unread active, assert `getBooks` was
      called with the active filter, the rendered rows match the filtered
      payload, and the active button keeps `aria-pressed="true"`.
- [ ] Include an All-path check: selecting All and mutating renders the
      unfiltered payload with no filter param sent.
- [ ] Optionally add a small test asserting `getBooks` maps
      `"all"`/`"read"`/`"unread"` to the expected axios params, guarding the
      full client param path.
- [ ] Run the client suite (`npm install` then `npm test` in `client/`) and
      the server suite (install `flask`, run `pytest`) unchanged; record
      evidence.
- [ ] Confirm the diff touches only `client/src/components/Books.vue` and
      client tests; `server/` and `client/src/api/` unchanged.

### Requirement verification

- Reapply-on-CRUD + visibly active filter: the new component tests are the
  decisive evidence — they exercise the real Books component across the
  boundary user click → filter state → mutation → transport call arguments →
  rendered rows → `aria-pressed` state. The API module mock records the
  requested filter rather than supplying the claimed behavior, and the param
  mapping it relies on is guarded by the optional mapping test.
- Filter switching and All behavior preserved: component test selecting All
  renders the unfiltered payload; the existing empty-state spec must stay
  green; Read/Unread selection is asserted in the same specs.
- API response shape and unfiltered behavior preserved: `server/app.py` and
  `client/src/api/books.js` remain untouched (clean `git diff` for those
  paths) and the existing `tests/test_books_api.py` passes unmodified.

### Additional implementation verification

- Run the full client suite to confirm no regression in the unrelated
  empty-state spec. No further material risks identified; the
  stale-response race is recorded above as an unchanged known limitation.