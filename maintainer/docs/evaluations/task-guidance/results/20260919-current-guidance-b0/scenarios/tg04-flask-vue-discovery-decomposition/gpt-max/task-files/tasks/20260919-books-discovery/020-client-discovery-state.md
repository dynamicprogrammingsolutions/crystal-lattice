# Build the client Books discovery state and view

Plan the Vue-side state, transport parameters, controls, table rendering, pagination, and empty-state behavior for the approved Books discovery contract.

Parent Task: tasks/20260919-books-discovery/000-main.md
Depends On: tasks/20260919-books-discovery/010-api-discovery-contract.md

## Requirements checklist

- [ ] The component has one canonical discovery state for read status, search, page, and the approved page-size/default values.
- [ ] Controls send the selected state through the existing API adapter and visibly retain their active values.
- [ ] The table renders only the selected page, and bounded pagination reflects the approved page metadata and disables or hides unavailable movement.
- [ ] The empty state represents the selected discovery query without clearing or hiding the active controls.
- [ ] Existing add, update, and remove methods remain available and can reload through the current discovery state.

## Research and supporting facts

- `client/src/components/Books.vue` currently stores only `books`, fetches all books in `mounted`, and has no controls or pagination.
- `client/src/api/books.js` already exposes `getBooks(params = {})`, so the client can pass query parameters without changing `addBook`, `updateBook`, or `deleteBook`.
- The current component test mocks all API functions and checks only the empty-state text; it does not assert request parameters or mutation refreshes.

## Execution plan

Status: Draft

Introduce an explicit discovery model whose normalized values drive the request, controls, table, pagination, and empty state. Keep the server response separate from the derived page display so metadata is not lost. Build the GET request from that model through `getBooks`, and make loading/error transitions preserve the selected controls rather than falling back to an unfiltered list.

Render the read-status selector and title/author search control as active, accessible inputs. Render the current page of rows and bounded navigation using the API’s approved metadata. Keep the controls visible when there are no matching rows and make the empty message describe the selected result set without implying that the underlying collection is empty unless that distinction is part of the approved copy.

Use one state transition path for initial values, user changes, and responses. Apply the approved page-reset and normalization rules when a query change invalidates the current page. Keep this subtask focused on component state and rendering; URL serialization and browser-history ownership are defined in the dependent URL/history subtask.

Add component tests with controlled API responses for default state, each read-status selection, search parameter construction, returned page rendering, first/last-page controls, no matches, and preservation of state through the mutation refresh hooks. Use a router-backed test only where the URL subtask needs it.

### Implementation decisions and open questions

- Decision: the component’s request, rendered content, and controls must derive from one canonical discovery state.
- Decision: continue using the existing `getBooks`/CRUD adapter boundary rather than adding a second transport path.
- Open: exact state field names, default page size, search timing, and page-reset/normalization policy follow the parent contract.
- Recommendation: make filter changes and committed searches reset to page one, while keeping the search input’s displayed value stable during loading.

### Documentation

- Capture control semantics, empty-state behavior, and page navigation in the maintained Books/development documentation after implementation.
- Do not document unverified UI behavior during planning.

### Task checklist

- [ ] Resolve the API response fields and canonical client-state defaults.
- [ ] Define the control-to-state and state-to-request mappings.
- [ ] Define table, pagination, loading, and empty-state rendering rules.
- [ ] Define how mutation callbacks invoke the state-aware loader.
- [ ] Plan component tests for active controls, rendered page, boundaries, empty results, and refreshes.

### Requirement verification

- Canonical controls and request state: component test asserting control values and the exact `getBooks` parameters after each supported interaction.
- Table and pagination: component test with multi-page metadata asserting row IDs and navigation availability at both bounds.
- Empty state: component test with a no-match response asserting the empty message while active controls remain selected.
- CRUD refresh behavior: component test stubbing each mutation and asserting the follow-up GET uses the unchanged canonical discovery state.