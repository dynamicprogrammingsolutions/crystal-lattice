# Books page discovery controls and view consistency

Add read-status filter, title/author search, and bounded pagination controls
to the Books page, driven by the server discovery API, with the table, active
controls, empty state, and CRUD refreshes kept consistent with the selected
view. Independently useful: users can work a larger collection on the page.

Parent Task: tasks/20260919-books-page-discovery/000-main.md
Depends On: tasks/20260919-books-page-discovery/010-server-discovery-query.md

## Requirements checklist

- [ ] A read-status control (all / read / unread) constrains the visible table.
- [ ] A search control matches titles or authors case-insensitively.
- [ ] Pagination controls move between pages bounded by the server-reported total.
- [ ] The table always reflects the current filter, search, and page selection.
- [ ] The empty state appears whenever the selected view returns no books and stays consistent with the active selection.
- [ ] Add, update, and delete keep their existing behavior and refresh by re-applying the current discovery state; if the current page is beyond the last valid page after a refresh, the view clamps to the last valid page.
- [ ] Requests send the current discovery state through `getBooks(params)`; with defaults selected the request stays unfiltered.
- [ ] The page-usage slice of the discovery documentation is updated in the same change.

## Requirement questions

- Q1 (inherited from the main task, unresolved): read-status indicator in the
  table — affects this subtask's template scope. Do not add it without
  approval.

## Supporting facts

- `Books.vue` already re-fetches after every mutation via `getBooks()`; the
  change re-applies the current params there rather than introducing a
  separate refresh path.
- `getBooks(params = {})` already forwards query params; no transport change
  is expected (verify while implementing).
- `client/tests/Books.spec.js` mocks the api module and asserts the empty
  state; it is the maintained component boundary. Its mock data must gain the
  new contract field(s) when the component starts consuming them.
- The component currently renders title/author columns only.

## Execution plan

Status: Draft

Hold the discovery state (filter, search, page) as component state; derive
request params from it; bind the controls to the state; and route the
mount/refresh fetches through `getBooks(currentParams)`. Keep `total` from
the response to bound pagination (prev/next disabled at the edges, current
position shown). After each CRUD mutation, re-apply the current selection and
clamp the page to the last valid page when the selection shrinks (main-task
D5). The default view (defaults selected) must issue the same unfiltered
request as today.

Verification: extend `client/tests/Books.spec.js` — assert the param-less
default request, that control changes issue param'd requests and update the
table, the filtered empty state, and that add/update/delete re-apply the
current selection including the clamp case. The component boundary is
appropriate here: the API contract itself is proven by subtask 010's HTTP
tests, so mocking the api module does not bypass the behavior under test.

### Implementation decisions and open questions

- Search commit semantics (live vs on submit/debounce) follow main-task D4
  (committed changes) and are recommendation-level until approved.
- Local choice: pagination renders as prev/next plus a current-position
  indicator — the smallest useful control for a large collection.

### Documentation

Update `docs/development/index.md`: describe the Books page controls and the
consistency rules (view, empty state, CRUD refreshes).

### Task checklist

- [ ] Discovery state and controls in `Books.vue`
- [ ] Param'd fetches and CRUD re-apply with clamping
- [ ] Component tests extended (params, table, empty state, CRUD re-apply)
- [ ] Page-usage documentation updated

### Requirement verification

- Controls, table consistency, empty state, and CRUD re-apply →
  `Books.spec.js` at the api-module boundary with a mocked `getBooks`
  capturing params (existing harness, extended — not bypassed).
- The existing empty-state test remains valid as the default-view anchor once
  its mock carries the new contract.