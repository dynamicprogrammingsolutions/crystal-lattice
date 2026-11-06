# Preserve Books Filter on CRUD Refresh

Keep the selected status filter active and applied when the Books page refreshes its collection after adding, editing, or deleting a book.

## Requirements checklist

- [ ] The selected All, Read, or Unread filter remains visibly active after add, edit, and delete operations.
- [ ] Each CRUD refresh requests the collection using the currently selected filter.
- [ ] Preserve the existing API response shape and the unfiltered All behavior.

## Open Questions

- None. The current component owns the filter state and already passes it to `getBooks` when a filter is selected.

## Supporting Facts

- `client/src/components/Books.vue` stores the current filter as `selectedFilter` and uses it for `aria-pressed`.
- The add, update, and remove methods currently refresh via `getBooks()` with no filter argument.
- `client/src/api/books.js` maps `all` to empty query params and maps Read/Unread to the existing `read` query parameter.
- The Flask endpoint returns the existing `{status, books}` collection response; CRUD calls and their response shapes are outside this change.
- The existing client test mocks the Books API and only checks the empty state. The Flask tests currently check status codes but do not assert response payloads.

## Execution plan

Status: Draft

Keep the change within the Books component: after each successful mutation, call the existing `getBooks` function with `selectedFilter`, then replace the visible collection with the returned `data.books` as before. Keep the selected filter state unchanged, and retain the existing pressed-state accessibility signal while adding a clear visual selected-state treatment to the filter buttons if the current styling does not visibly distinguish it. Do not alter the client API helper, Flask routes, or their response formats; `all` must continue to mean an unfiltered request.

Add component tests that select Read and Unread and exercise each CRUD refresh, verifying that the API helper receives the selected filter and that the corresponding button remains active. Add or strengthen API contract coverage for the unfiltered `GET /books` response to confirm the existing response shape and unfiltered collection behavior remain intact. Run the focused client and Flask tests.

### Implementation decisions and open questions

- Use the existing `selectedFilter` as the single source of truth; do not add a parallel filter state or change API contracts.
- Share the existing collection-loading behavior across CRUD refreshes only if it avoids duplication without obscuring the filter argument; otherwise pass `selectedFilter` directly at each refresh.
- No requirement questions remain open.

### Documentation

- Update the root `README.md` with a concise user-facing description of the Books status filters and their persistence through CRUD refreshes, keeping the claim in the same change as the implemented behavior.

### Task checklist

- [ ] Update Books component refreshes to use the selected filter and make its active state visually clear.
- [ ] Add component regression coverage for add, edit, and delete while Read and Unread are selected.
- [ ] Strengthen Flask coverage for the unfiltered collection response contract.
- [ ] Update the root README to describe the supported filter behavior.
- [ ] Run focused client and Flask tests.

### Requirement verification

- Requirements 1 and 2: component tests exercise the actual Books component and assert each CRUD refresh calls the existing API helper with the selected filter, while confirming the selected button remains active.
- Requirement 3: Flask route tests assert an unfiltered `GET /books` retains the `{status, books}` shape and returns the unfiltered collection; review confirms no API implementation or client transport contract changes.

### Additional implementation verification

- Run `npm test` from `client/`.
- Run `pytest` from the repository root.