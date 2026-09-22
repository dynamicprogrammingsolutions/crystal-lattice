# Preserve the Books filter across CRUD refreshes

Update the Vue Books page so the selected All, Read, or Unread filter remains visibly active and is applied when the collection is refreshed after adding, editing, or deleting a book. Preserve the existing Flask API response shape and the current unfiltered behavior.

## Requirements checklist

- [ ] The selected `all`, `read`, or `unread` filter remains the active visible filter after a successful add, edit, or delete operation.
- [ ] Every collection refresh triggered by add, edit, or delete requests and renders the collection for the current selected filter.
- [ ] The existing API response shape and filter transport mapping remain unchanged.
- [ ] The default/unfiltered `all` behavior remains unchanged.

## Unresolved requirement questions

None identified. The request defines the required filter states, CRUD operations, API compatibility, and preserved default behavior.

## Supporting facts

- `client/src/components/Books.vue` stores the current filter in `selectedFilter`, initializes it to `"all"`, exposes it through each button’s `aria-pressed`, and passes the selected value from `selectFilter` to `getBooks`.
- The `add`, `update`, and `remove` methods currently refresh with `getBooks()` and therefore discard the selected filter.
- `client/src/api/books.js` maps `"all"` to no `read` query parameter, `"read"` to `read=true`, and `"unread"` to `read=false`; its GET response is consumed as `response.data.books`.
- `server/app.py` already supports the optional `read` query parameter and returns the existing JSON envelope. No server or API contract change is required by the request.
- `client/tests/Books.spec.js` currently covers only the empty-state render, so it does not protect filter persistence or CRUD refresh behavior.
- No maintained user or developer documentation currently describes the Books filters; `docs/development/index.md` records that no book-discovery specification exists.

## Execution plan

Status: Draft

Implement the fix at the Books component boundary using the existing `selectedFilter` state and `getBooks(filter)` contract. Ensure the three CRUD handlers refresh through the current filter, either directly or through a small shared component refresh method if that keeps the paths consistent. Keep the filter button state tied to the existing `selectedFilter` value so the selected button remains visibly and accessibly active after the refresh.

Add focused Vue component tests that exercise each filter and each CRUD operation through the real component methods and mocked API module:

- select Read and verify an add refresh calls `getBooks("read")`, updates the rendered collection from that response, and leaves the Read button `aria-pressed="true"`;
- select Unread and verify an edit refresh calls `getBooks("unread")` with the same visible state preserved;
- select All and verify a delete refresh calls `getBooks("all")`, preserving the no-query/unfiltered path;
- retain coverage that the component consumes the existing `{ data: { books } }` response shape.

Run the client Vitest suite after implementation. Do not alter the Flask routes, response envelopes, or API helper’s query mapping unless the focused test demonstrates an existing compatibility issue.

### Implementation decisions and open questions

- Decision: Keep this as one task because the accepted behavior crosses component state, the existing client API helper, and rendered collection state but has one user-visible owner and one decisive component-test boundary.
- Decision: Reuse `selectedFilter` as the source of truth; do not introduce a second filter state or change the API response contract.
- Decision: Preserve `"all"` as the initial/default filter and continue representing it through the existing unfiltered GET behavior.
- Open questions: None.

### Documentation

No separate documentation update is planned. There is no maintained Books/filter guide to update, and creating a placeholder specification would add structure without a current audience. If implementation later introduces a maintained user or developer guide for Books, document the filter persistence behavior in that same change.

### Task checklist

- [ ] Update the Books component’s CRUD refresh path to pass the current selected filter.
- [ ] Add component regression coverage for filtered add, edit, and delete refreshes.
- [ ] Verify the selected filter remains reflected by `aria-pressed` after each CRUD refresh.
- [ ] Verify the existing `{ data: { books } }` response consumption and default `all` behavior remain intact.
- [ ] Run `client`’s Vitest suite and record the result.
- [ ] Re-check that no Flask route, response shape, or API query mapping changed.

### Requirement verification

- Selected filter remains visibly active after CRUD: a Vue component test selects each filter, performs the corresponding CRUD method, and asserts the selected button remains `aria-pressed="true"` after the awaited refresh.
- CRUD refreshes reapply the current filter: the same component test observes the actual `getBooks` mock calls and rendered books for add, edit, and delete under Read, Unread, and All.
- API response shape is preserved: the component tests provide and consume the existing `{ data: { books } }` envelope; the unchanged API helper and server tests provide supporting compatibility evidence.
- Unfiltered behavior is preserved: the All-path test verifies `getBooks("all")`, while the existing API helper mapping remains unchanged so All continues to omit the `read` query parameter.

### Additional implementation verification

- Run `npm test` from `client/` with the repository’s installed dependencies.
- If the client test command cannot run because dependencies are unavailable, report that as blocked rather than substituting a test-only shortcut.