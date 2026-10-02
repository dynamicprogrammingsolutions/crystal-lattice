# Connect Books discovery to URL state

Own client query serialization, route initialization, share/restore behavior,
and browser history navigation for the Books discovery state.

Parent Task: tasks/books-discovery/000-main.md

Depends On: tasks/books-discovery/010-api-discovery-contract.md

## Requirements checklist

- [ ] The client sends the normalized discovery state using the agreed API
  query keys and values.
- [ ] A direct `/books` URL initializes the default discovery view.
- [ ] A URL containing discovery state restores the same filter, search, and
  page after reload or sharing.
- [ ] State changes produce canonical browser URLs and history entries
  according to the approved navigation policy.
- [ ] Browser back and forward restore the corresponding URL state and trigger
  the matching data view.
- [ ] Unfiltered loading remains compatible with the existing API adapter and
  no-parameter endpoint behavior.

## Supporting facts

- `client/src/api/books.js` already accepts `getBooks(params = {})` and passes
  `params` to Axios, so the transport boundary can be extended without
  changing mutation functions.
- `client/src/router.js` has a single `/books` route using
  `createWebHistory()` but currently has no query-state logic.
- `Books.vue` owns the current fetch calls, so URL-driven state must be made
  available there without creating a second independent state representation.

## Execution plan
Status: Draft

Create one normalized representation for read status, search text, and page.
Define parsing and serialization rules that reject or normalize invalid
values consistently with the approved API contract. Initialize it from the
route query, serialize user changes using the approved push/replace policy,
and ensure route-query changes from browser navigation reuse the same fetch
path as direct user changes.

Keep default state canonical and avoid emitting redundant query keys when the
approved policy says they are omitted. Preserve the active state across
ordinary API refreshes and expose the normalized request parameters to the
Books view so CRUD refreshes cannot accidentally fall back to an unfiltered
request.

Add client tests for direct URL restoration, query serialization, criteria
changes, page changes, back/forward navigation, invalid or missing defaults,
and the no-parameter path. Use router-level coverage for history behavior and
unit/component coverage for pure normalization where useful.

### Implementation decisions and open questions

The parent task recommends `read`, `q`, and `page` as the URL/API vocabulary,
omitting default values and resetting page to one when criteria change. Those
choices are material because they define URLs users can bookmark and share;
do not hard-code them until the parent task resolves the corresponding
questions.

The API dependency is intentional: this subtask must consume the server's
approved metadata and bounds rather than infer page validity from the current
page alone.

### Documentation

Record the final URL query keys, default omission, history behavior, and
reload/share semantics for the parent task's development documentation after
implementation. No current guidance is changed during planning.

### Task checklist

- [ ] Confirm the server query contract and URL vocabulary.
- [ ] Implement normalization, parsing, and serialization.
- [ ] Wire route-query changes to data loading and browser navigation.
- [ ] Preserve the no-parameter client/API path.
- [ ] Add router and client tests for share/restore and history behavior.

### Requirement verification

- A router-level test must mount the real `/books` route, start from a
  parameterized URL, and prove the corresponding API request and visible state.
- The same test boundary must exercise back and forward navigation and prove
  that both URL and results are restored.
- Client transport tests must prove omitted defaults do not create accidental
  query parameters and that the unfiltered call remains valid.
