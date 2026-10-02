# Preserve the Books filter after CRUD refreshes

The Vue Books page must keep the selected All, Read, or Unread filter active
and use that filter whenever adding, editing, or deleting a book refreshes the
collection. The existing Flask API response contract and unfiltered behavior
must remain unchanged.

## Requirements checklist

- [ ] The selected All, Read, or Unread filter remains active after an add,
  update, or delete operation, including the existing `aria-pressed` active
  indicator.
- [ ] Every CRUD-triggered collection refresh reapplies the currently selected
  filter, so the displayed books remain consistent with that selection.
- [ ] The Flask API response shape and the behavior of an unfiltered books
  request remain unchanged.

## Requirement questions and decisions

- Requirement questions: None identified. The existing `aria-pressed` binding
  is the component's active-filter indicator, and the request does not require
  a new visual styling convention.
- Decisions:
  - Keep this as one end-to-end task owned by the Books page. The API already
    accepts the required `read` query and does not need a contract change.
  - Keep `selectedFilter` as the single source of truth and centralize the
    collection refresh around the selected value so the three mutation paths
    cannot silently fall back to the default.

## Research and supporting facts

- `client/src/components/Books.vue` stores `selectedFilter`, passes the chosen
  value to `getBooks` from `selectFilter`, and binds button `aria-pressed` to
  that state.
- The `add`, `update`, and `remove` methods currently call `getBooks()` with no
  argument after the mutation, which requests the unfiltered collection.
- `client/src/api/books.js` maps `all` to no query parameter, `read` to
  `read=true`, and `unread` to `read=false`.
- `server/app.py` returns the existing JSON object containing `status` and
  `books`; omitting `read` returns the complete `BOOKS` collection.
- `client/tests/Books.spec.js` currently covers only the empty state. The API
  tests cover mutation status codes but do not assert the response shape or
  filtered/unfiltered collection semantics.

## Execution plan

Status: Draft

The Books component remains responsible for the selected filter and the
rendered collection. Introduce one component-level refresh path that requests
books using the current `selectedFilter`, and use it after add, update, and
delete. The filter-selection path should continue to update the state before
loading the corresponding collection. This keeps the active button state and
the displayed data driven by the same value.

No Flask route or API response changes are planned. The existing transport
mapping remains the compatibility boundary: `all` continues to omit `read`,
while `read` and `unread` continue to send their respective boolean query
values.

Execution order:

1. Update the Books component's refresh flow so all three CRUD methods request
   the current filter, preferably through the shared component refresh path.
2. Extend the Books component test with realistic mocked responses and cover
   each filter through add, update, and delete. Assert both that the selected
   button remains `aria-pressed="true"` and that each refresh receives the
   selected filter value.
3. Strengthen the Flask API coverage at its public route boundary to assert
   the existing `{status, books}` response shape, that an omitted filter still
   returns the unfiltered collection, and that `read=true` and `read=false`
   continue to select the correct books.
4. Run the client test command from `client/` and the server test command from
   the repository root. Inspect the final diff to confirm no API contract or
   unrelated behavior changed.

### Implementation decisions and open questions

- The component's current `selectedFilter` state and `aria-pressed` binding
  are retained; no new filter state or API shape is introduced.
- A shared refresh method is the preferred implementation boundary because it
  makes all CRUD refreshes use the same filter-preserving behavior.
- No open requirement questions remain. Whether the helper is named or
  inlined is an implementation detail and does not change the accepted
  behavior.

### Documentation

- No maintained user or developer documentation currently describes the
  Books filter behavior, and the API contract is intentionally unchanged.
- Do not add placeholder documentation for this fix. If implementation
  uncovers maintained guidance that claims CRUD refreshes are unfiltered,
  update that source in the same change; otherwise the task file is the only
  planning documentation needed.

### Task checklist

- [ ] Update `client/src/components/Books.vue` to refresh with
  `selectedFilter` after add, update, and delete.
- [ ] Add component regression coverage for active-filter state and all CRUD
  refresh paths across All, Read, and Unread.
- [ ] Add or update Flask route coverage for response shape and unfiltered
  behavior without changing the endpoint contract.
- [ ] Run client and server tests and review the diff.

### Requirement verification

- Selected filter remains active: the Books component test mounts the real
  filter controls, selects each non-default filter, invokes each CRUD method,
  and verifies the selected button remains `aria-pressed="true"` after each
  refresh.
- CRUD refreshes reapply the selected filter: the same component-level test
  verifies that add, update, and delete each call the production
  `getBooks` interface with `all`, `read`, or `unread` matching the current
  selection, while also checking the refreshed collection rendered by the
  component.
- API compatibility: Flask route tests verify the public JSON response keeps
  the `status` and `books` fields, an omitted `read` parameter returns the
  complete collection, and explicit true/false filters still select by read
  status.

### Additional implementation verification

- Run `npm test` in `client/`.
- Run `pytest` from the repository root.
- Confirm the final diff is limited to the component and focused regression
  coverage, with no server implementation or response-shape changes.