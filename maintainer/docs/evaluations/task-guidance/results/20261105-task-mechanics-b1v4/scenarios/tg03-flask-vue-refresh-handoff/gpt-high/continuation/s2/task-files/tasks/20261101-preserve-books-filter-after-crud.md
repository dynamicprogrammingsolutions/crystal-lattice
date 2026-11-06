# Preserve the Books filter after CRUD refreshes

Keep the active All, Read, or Unread filter selected and applied when the Books collection refreshes after adding, editing, or deleting a book.

## Requirements checklist
- [ ] The selected filter remains visibly active after adding, editing, or deleting a book.
- [ ] Each CRUD refresh requests and displays books using the currently selected filter.
- [ ] The existing API response shape and unfiltered All behavior remain unchanged.

## Questions and decisions
- No unresolved requirement questions.
- Design decision: keep this change in the Books client component; the existing API client already accepts a filter and maps Read/Unread to request parameters.

## Supporting details
- `client/src/components/Books.vue` stores `selectedFilter` and uses it when a filter button is selected, but the `add`, `update`, and `remove` methods call `getBooks()` without that selection after mutations.
- `client/src/api/books.js` defaults `getBooks` to `"all"` and returns the existing HTTP response unchanged.
- `server/app.py` owns the Flask `/books` response shape. No backend change is needed for this behavior.
- `client/tests/Books.spec.js` currently checks only the empty state; it mocks the API module and can cover selection state and refresh calls at the component boundary.
- `tests/test_books_api.py` currently checks status codes but does not assert the GET response keys.

## Implementation plan
Status: Draft

Keep the fix within the Books component: preserve the selected filter state, and pass that value to `getBooks` for each CRUD-triggered refresh. Leave the API transport and Flask response contracts untouched. Add component coverage that selects Read and Unread, exercises each mutation, and confirms that the selected button remains active and the refreshed collection is requested with the same filter. Also cover the default All path and preserve the existing GET response shape with an API-level assertion if needed to provide explicit regression evidence.

The sequence starts with focused component regression coverage, then applies the shared filter-aware refresh behavior, and finally runs the client and API tests. The component tests are decisive for the filter-to-refresh connection; the API test checks the separate response contract rather than pretending a mocked component test covers it. Do not broaden this into new filtering behavior or change server/API semantics.

The main risk is a refresh path continuing to use the default filter or desynchronizing the visible selection from the data. Testing all three mutations under non-default filters guards those paths. The change is localized and reversible by reverting the component change and related tests; no persisted data or public API contract changes are involved.

### Implementation decisions and open questions
- Reuse the existing `selectedFilter` state as the source of truth; do not add parallel filter state.
- Keep the All behavior and API response contract as-is.
- No open questions block implementation.

### Documentation
- No documentation change is planned: this repairs existing Books-page behavior without adding a new user-facing capability or changing supported API guidance.

### Task checklist
- [ ] Add component regression tests for all CRUD refreshes and all filter selections.
- [ ] Pass the active filter to each CRUD-triggered collection refresh.
- [ ] Add or update API response-shape evidence without changing the contract.
- [ ] Run `npm test` from `client/` and `pytest tests/test_books_api.py`.

### Requirement verification
- Requirements 1 and 2: component tests exercise add, update, and delete after selecting Read and Unread; assert the selected filter button remains `aria-pressed` and `getBooks` receives the selected value. Include All/default behavior. This does not claim to test browser-level interaction or the live network.
- Requirement 3: assert the Flask GET response retains its existing `status` and `books` keys, and verify the client’s All request remains unfiltered. This does not change or expand API behavior.

### Additional implementation verification
- Run `npm test` from `client/`.
- Run `pytest tests/test_books_api.py` from the repository root.