# Preserve the Books filter after CRUD refreshes

The Books page must keep its selected All, Read, or Unread filter active and
use that filter whenever adding, editing, or deleting a book refreshes the
collection. The existing Flask API contract and unfiltered behavior remain
unchanged.

## Requirements checklist

- [ ] After adding, editing, or deleting a book, the collection is refreshed
  using the currently selected `all`, `read`, or `unread` filter.
- [ ] The selected filter remains visibly active after each CRUD refresh,
  including the `aria-pressed` state of the corresponding filter button.
- [ ] The existing API response shape is preserved, and the All/unfiltered
  view continues to request and display the unfiltered collection.

## Scope and workstreams

This is one end-to-end client behavior owned by the Books page. The planned
change covers the Vue component and its component regression tests, with a
focused API contract regression check because the component depends on the
existing response and filtering behavior. No subtasks are needed: the UI
selection state, CRUD refresh, and rendered collection form one independently
acceptable outcome.

## Requirement questions and decisions

- Unresolved requirement questions: none identified.
- Decision: keep the fix in the client refresh path. The existing
  `getBooks(filter)` adapter already maps `all` to an unparameterized request
  and `read`/`unread` to the existing `read` query parameter, so changing the
  Flask routes or response payload would expand scope without addressing the
  defect.
- Decision: use a shared Books-page refresh method, or equivalent single
  refresh path, so add, update, and delete cannot independently omit the
  current filter.

## Research and supporting facts

- `client/src/components/Books.vue` stores the active filter in
  `selectedFilter` and binds each filter button’s `aria-pressed` value to it.
- `selectFilter` already passes the selected value to `getBooks`, but `add`,
  `update`, and `remove` currently call `getBooks()` with no filter.
- `client/src/api/books.js` preserves the existing mapping: `all` sends no
  `read` parameter, `read` sends `read=true`, and `unread` sends `read=false`.
- `server/app.py` returns the established JSON envelope with a `books` list
  and treats a missing `read` query as the unfiltered collection.
- Existing client coverage only checks the empty state, and existing Flask
  coverage checks mutation status but does not assert the response envelope or
  unfiltered collection contents.
- No book-discovery specification exists under `docs/development/`; the
  repository README is the only maintained user-facing package summary.

## Execution plan

Status: Draft

The component will retain `selectedFilter` as the single source of truth for
both the active button state and collection refreshes. Consolidate the
post-mutation reload behavior into a component-local refresh path that calls
`getBooks(this.selectedFilter)` and assigns the returned `data.books`.
`selectFilter` may use that same path after updating the selection. Because the
API adapter already treats `all` as the unfiltered request, passing the
explicit current value keeps All behavior equivalent while ensuring Read and
Unread are reapplied after every mutation.

Add focused Vue component coverage that selects Read and Unread, exercises
add, update, and delete, and verifies each refresh receives the selected
filter, renders the refreshed collection, and leaves the matching filter
button `aria-pressed="true"`. Include an All case to verify the unfiltered
refresh remains active. Keep the API module and Flask route implementation
unchanged.

Strengthen the existing Flask contract test only as needed to verify that a
request without `read` returns the established `{status, books}` shape and
the full collection, and that `read=true`/`read=false` continue to select the
corresponding books. This check protects the boundary the client relies on
without introducing a new response format or a test-only route.

### Implementation decisions and open questions

- The refresh helper is a local implementation choice; it should not create a
  new public API or alter the `getBooks` response shape.
- The explicit `all` argument must continue to produce the same unfiltered
  HTTP request as the current default.
- No open requirement questions remain. If implementation discovers that the
  page’s add/edit/delete controls are supplied by another component, keep the
  refresh ownership at the component that owns `selectedFilter` and update the
  focused test boundary accordingly.

### Documentation

During implementation, review `README.md` and add a concise current-behavior
note only if the page behavior is described there in enough detail to warrant
it. Do not create a new specification or documentation directory for this
localized fix. The task file is the retained implementation handoff; no
maintained documentation changes are made while this plan remains Draft.

### Task checklist

- [ ] Update the Books-page CRUD refresh path to pass the current filter.
- [ ] Preserve the selected filter’s visible state through each refresh.
- [ ] Add component regression coverage for All, Read, and Unread across
  add, update, and delete.
- [ ] Add or extend focused Flask contract coverage for response shape,
  unfiltered behavior, and existing filtered behavior.
- [ ] Review maintained documentation and update only if the existing README
  makes a user-facing claim that should include this behavior.
- [ ] Run the focused client and server test commands and record their results.

### Requirement verification

- Current filter reapplied after every CRUD operation: component test
  exercises add, update, and delete from Read and Unread selections and
  asserts the corresponding `getBooks` argument and rendered `data.books`
  result.
- Selected filter visibly active: the same component test asserts the
  selected button remains `aria-pressed="true"` after each asynchronous
  refresh and the other buttons remain inactive.
- API shape and unfiltered behavior preserved: Flask test-client coverage
  asserts the no-query response retains the `status`/`books` envelope and
  contains the full collection; adjacent assertions cover the existing
  `read=true` and `read=false` selections. The client adapter remains
  unchanged.

Execution is not authorized by this Draft plan; implementation begins only
after explicit approval.