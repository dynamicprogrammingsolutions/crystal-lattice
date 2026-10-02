# Integrate discovery into the Books view

Own the Books page controls, active-state rendering, bounded navigation,
empty-state behavior, and CRUD refresh consistency.

Parent Task: tasks/books-discovery/000-main.md

Depends On: tasks/books-discovery/010-api-discovery-contract.md,
tasks/books-discovery/020-url-state-transport.md

## Requirements checklist

- [ ] The page renders a read-status control whose active value matches the
  normalized discovery state.
- [ ] The page renders title/author search and keeps its displayed value
  synchronized with discovery state.
- [ ] The table renders only the selected page of matching books.
- [ ] Bounded pagination controls expose valid navigation and active position
  using API metadata.
- [ ] The no-match empty state reflects the active view without displaying a
  stale prior page.
- [ ] Add, update, and delete refreshes request and render the active
  discovery view, including the approved behavior when a mutation invalidates
  the current page.
- [ ] Existing CRUD methods and behavior remain usable.

## Supporting facts

- `Books.vue` currently has only a `books` array in component data and no
  controls, pagination state, loading state, or route state.
- The component already refreshes after `add`, `update`, and `remove`, but
  every refresh calls `getBooks()` without parameters.
- The existing component test covers only the empty text and mocks all API
  methods; there is no evidence for populated rows, controls, URL state, or
  mutation refreshes.

## Execution plan
Status: Draft

Render controls from the normalized route/discovery state and route all
criteria and page changes through the URL-state owner. Render the table from
the current response page and use the approved pagination metadata to disable
or hide invalid navigation. Keep the empty state tied to the current
response, so no-match results cannot leave stale rows visible and a valid
non-empty page cannot show the no-match message.

Refactor the existing post-CRUD reload path to reuse the active normalized
discovery state. Apply the approved page correction when a mutation changes
the result count, then update the URL and reload once through the same path
used by navigation. Preserve the existing mutation API calls and their
successful refresh behavior.

Extend component tests for active controls, filtered/search results, page
navigation, no-match state, page-boundary behavior, and each CRUD refresh
under a non-default view. Add the smallest router-backed integration coverage
needed to ensure this component responds to browser navigation rather than
only to synthetic local state changes.

### Implementation decisions and open questions

The visible page behavior depends on the parent decisions about read values,
search matching, page size/metadata, URL canonicalization, and mutation
clamping. In particular, the page should not invent a separate local page
calculation if the API is the source of truth for bounds.

The current template has no visible add/edit/delete controls, although the
component exposes mutation methods. This plan preserves those methods and
their refresh behavior; adding new CRUD affordances is out of scope unless
the product owner separately requires them.

### Documentation

Document the final control labels, empty-state meaning, pagination behavior,
and mutation refresh semantics in the maintained Books/discovery development
guide after implementation. Do not add user-facing claims during planning.

### Task checklist

- [ ] Consume the approved normalized discovery state and API metadata.
- [ ] Add read-status and title/author search controls.
- [ ] Add bounded pagination and active-state presentation.
- [ ] Keep table and empty state synchronized with the selected response.
- [ ] Preserve active state during add, update, and delete refreshes.
- [ ] Add component and router-backed integration coverage.

### Requirement verification

- Component tests must prove control values and table rows correspond to the
  selected state for populated and no-match responses.
- Pagination tests must prove first/last-page bounds and the approved behavior
  for an invalidated page after mutation.
- CRUD tests must invoke each existing mutation method while a non-default
  filter/search/page is active and assert the follow-up GET retains that state.
- Router-backed tests must verify that view rendering changes when browser
  history restores a different discovery state.