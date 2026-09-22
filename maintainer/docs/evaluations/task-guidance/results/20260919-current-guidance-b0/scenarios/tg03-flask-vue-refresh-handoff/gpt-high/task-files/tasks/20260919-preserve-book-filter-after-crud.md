# Preserve the selected book filter across CRUD refreshes

The Books page must keep its selected `All`, `Read`, or `Unread` filter active
after adding, editing, or deleting a book, and must refresh the collection
using that same filter.

## Requirements checklist

- [ ] After an add, update, or delete completes, the Books page refreshes the
  collection with the currently selected filter.
- [ ] The selected filter remains visibly active after each CRUD refresh,
  including the `aria-pressed` state used by the filter controls.
- [ ] The existing `All`/unfiltered behavior is preserved, including the
  default collection and the client request behavior for the `all` filter.
- [ ] The existing API response shape and Flask API contract remain unchanged.
- [ ] Component-level regression coverage proves filtered refreshes for CRUD
  operations and the preserved unfiltered path.

## Scope and ownership

This is one cohesive client-side task owned by `client/src/components/Books.vue`
and its component tests. The Flask routes and the `getBooks` response
transformation are existing boundaries to preserve, not separate workstreams:
the defect is that the three CRUD handlers omit the component's
`selectedFilter` when calling `getBooks`.

## Requirement questions and decisions

- No unresolved requirement questions.
- Decision: use a single task file rather than subtasks because the required
  behavior is a localized state-and-refresh interaction whose useful result
  cannot be split into independently complete UI and API changes.
- Decision: keep the fix at the component refresh boundary and do not change
  query encoding, server filtering, or response payloads.

## Research and supporting facts

- `Books.vue` stores the current filter in `selectedFilter` and passes a
  selected value to `getBooks` from `selectFilter`.
- `add`, `update`, and `remove` currently call `getBooks()` without an
  argument, which defaults to the unfiltered `all` request.
- The filter buttons already derive `aria-pressed` from `selectedFilter`, so
  preserving that state does not require a new visual-state mechanism.
- `client/src/api/books.js` maps `all` to an empty query object and maps
  `read`/`unread` to the existing `read` query parameter.
- The Flask API returns collection responses under `books` and mutation
  responses under `book`; no response-shape change is needed.
- There is no `docs/index.md`, and the existing development documentation says
  no book-discovery specification exists. No maintained user or developer page
  currently documents this interaction.

## Execution plan

Status: Draft

Implement the refresh behavior in the Books component by ensuring every CRUD
completion reloads through the current `selectedFilter`. Prefer one small
component-level refresh path if that keeps the three handlers consistent; it
must continue to consume `getBooks(...).data.books` without changing the API
adapter or Flask routes.

Extend `client/tests/Books.spec.js` with deterministic mocked collection
responses and assertions that:

1. selecting `read` or `unread` keeps the corresponding filter control
   pressed and causes each of add, update, and delete to refresh with that
   filter;
2. the refreshed rows reflect the returned filtered collection;
3. selecting or retaining `all` causes CRUD refreshes to use the existing
   unfiltered path; and
4. the filter remains active after the asynchronous refresh completes.

Run the client test command from `client/package.json`. If the test harness
requires a small setup adjustment to exercise the component methods, keep that
adjustment test-only and preserve the real component/API boundary. Inspect the
diff and existing Flask/API tests to confirm no server contract or response
shape was altered; if the current API tests do not assert the response keys,
add focused assertions without changing the route implementation.

### Implementation decisions and open questions

- Use the existing `selectedFilter` value as the single source of truth for
  both the visible control state and post-mutation collection refreshes.
- Keep `getBooks`'s existing default and query mapping intact so `all` remains
  unfiltered and the API response shape remains untouched.
- No open requirement questions remain. A local implementation choice between
  a shared refresh method and direct argument passing may be resolved by the
  executor based on the smallest clear diff; it must satisfy the same tests.

### Documentation

No documentation update is planned because the repository has no maintained
page describing Books filter interactions, and creating a placeholder page
would add no useful audience-facing guidance. If an existing maintained Books
guide is discovered during execution, update it in the same change to describe
that CRUD refreshes retain the selected filter.

### Task checklist

- [ ] Update the Books component so add, update, and delete refresh with
  `selectedFilter`.
- [ ] Add regression tests for `read` and `unread` CRUD refreshes and visible
  filter state.
- [ ] Add or retain coverage for the `all`/unfiltered CRUD refresh path.
- [ ] Run the client test suite and verify the API/server boundary, adding
  focused response-key assertions only if existing tests do not already prove
  the unchanged shape.
- [ ] Record implementation and completion notes after execution begins and
  the evidence is available.

### Requirement verification

- Selected-filter refresh: the Vue component test selects a non-`all` filter,
  executes each CRUD handler with mocked successful mutations, waits for the
  refresh, and asserts `getBooks` received the selected filter and the
  resulting rows come from that filtered response.
- Visible active filter: the same component test asserts the selected
  button's `aria-pressed` value remains `true` and the other filter buttons
  remain inactive after each asynchronous CRUD refresh.
- Preserved unfiltered behavior: a component regression test exercises CRUD
  while `all` is selected and verifies the refresh uses the existing `all`
  path; the unchanged API adapter mapping preserves an empty query for that
  path.
- API contract: inspect the diff and run the Flask API tests, asserting that
  collection responses still expose `status` and `books`, mutation responses
  still expose `status` and `book`, and no route or payload implementation has
  changed.