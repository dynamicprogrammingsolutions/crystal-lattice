# Write user-facing books interface copy

Create concise, plain-language copy for the Books app’s user-facing states. The
task covers the home page introduction, book-list empty state, search-with-no-
results state, and the messages shown when loading or saving a book fails. A
maintainer reviews the proposed copy against the brief and style checklist
below before the task is complete.

## Requirements checklist

- [ ] Provide a short home page introduction that explains the purpose of the
  books experience and gives the user a clear orientation.
- [ ] Replace the book-list empty-state placeholder with copy that describes
  the absence of books in the current list and, where an existing action is
  available, points to the appropriate next step.
- [ ] Provide distinct copy for a search that returns no results. It must not
  describe an empty result as a loading or system error.
- [ ] Provide a clear message for a failure to load books.
- [ ] Provide a clear message for a failure to save a book.
- [ ] Keep all copy concise and in the app’s existing plain tone.
- [ ] Have a maintainer review every proposed string against the copy brief
  and style checklist in this task.
- [ ] Make no behavior changes: preserve state transitions, search semantics,
  transport/API behavior, controls, data handling, and error handling.

## Open requirement questions and decisions

- Requirement questions: none. The requested copy surfaces and copy-only
  constraint are defined by the brief.
- Decision: target strings must be attached to existing production states.
  Adding missing loading, saving, search, or navigation behavior is outside
  this task and requires a separately approved scope change.

## Scope and constraints

This is a copy-only change. Update user-facing strings in the owning Vue
views/components and their focused UI assertions as needed; do not refactor
the component, add new state, introduce retry or navigation actions, change
accessibility structure, or alter the Flask API.

If a requested surface is not represented by an existing production UI state,
stop and raise that scope issue before adding behavior. Copy may describe an
existing action, but it must not create or imply a new action that the
interface does not provide.

## Copy brief

- Home introduction: orient the user quickly, explain what they can do with
  their books, and invite the primary existing workflow.
- Book-list empty state: say that the current list has no books, using the
  list/filter context when it is already available. Keep this distinct from a
  failed request.
- Search with no results: acknowledge the query produced no matches and, only
  where the existing UI supports it, suggest a simple next step such as
  adjusting the search.
- Loading failure: state that the books could not be loaded. Give a recovery
  instruction only when the existing UI already exposes that recovery action.
- Saving failure: state that the book could not be saved and give a recovery
  instruction only when the existing UI already exposes one.

## Style checklist

- [ ] Use short, direct sentences and familiar words.
- [ ] Use sentence case and consistent punctuation across the states.
- [ ] Keep the tone calm, helpful, and matter-of-fact; do not blame the user.
- [ ] Prefer “books” and other terms already used by the app; avoid technical
  terms such as “request,” “endpoint,” or “payload.”
- [ ] Make empty, no-results, loading-failure, and saving-failure meanings
  clearly distinct.
- [ ] Tell the user what happened before suggesting a next step.
- [ ] Do not promise an action, recovery, or result that the current UI does
  not support.
- [ ] Ensure each message remains understandable when read without an icon,
  color, or surrounding implementation detail.
- [ ] Keep the strings brief enough for the existing layout and avoid
  unnecessary repetition.

## Supporting facts

- `client/src/components/Books.vue` currently renders `No books found.` when
  its `books` collection is empty.
- `client/tests/Books.spec.js` currently asserts that placeholder string.
- The compact fixture currently does not expose home-page, search,
  loading-failure, or saving-failure states in `Books.vue`; execution must
  locate their owning production surfaces before editing.
- No maintained user-facing documentation page currently defines this UI
  copy. The task brief and the reviewed strings are the source of truth for
  this change.

## Execution plan

Status: Draft

Keep the copy owned by the Vue surface that renders each state. First map each
requested string to an existing production view/state, then draft alternatives
using the copy brief and style checklist. Replace only the placeholder text and
assertions needed to verify the rendered copy. Existing transport or state
setup may be used to reach a real UI state in tests, but tests must exercise the
production component and must not supply the claimed copy or bypass rendering.

The maintainer review is a completion gate: review the final strings against
every checklist item, including the distinction between empty/no-results
states and failures. If any requested state is absent, record the scope issue
and seek approval rather than implementing new behavior.

### Implementation decisions and open questions

The implementation boundary is UI text only. No requirements are unresolved.
The only permitted adaptation is choosing the existing owning component for
each state after the surface map is confirmed.

### Documentation

No separate documentation update is planned. The reviewed UI strings are the
maintained user-facing copy; a documentation change would be needed only if a
separate copy catalog or product guide is introduced.

### Task checklist

- [ ] Map all five requested copy surfaces to existing production views and
  states.
- [ ] Draft the home introduction and four state messages against the brief.
- [ ] Replace only the corresponding user-facing placeholders.
- [ ] Update or add focused UI assertions for the rendered strings without
  bypassing the production component.
- [ ] Run the relevant client test command and inspect the rendered states.
- [ ] Obtain maintainer review against the full style checklist.

### Requirement verification

- Home introduction: a maintainer review confirms that the rendered
  introduction orients the user, is concise/plain, and does not claim
  unsupported behavior.
- Book-list empty state: the production component test renders an empty
  collection and asserts the reviewed string; the test also confirms the
  existing empty-state path remains the path being rendered.
- Search no-results state: the owning production component test renders an
  existing no-results state and asserts copy distinct from an error. If no
  such state exists, verification is blocked and must not be satisfied by
  adding behavior under this task.
- Loading failure: the owning production component test reaches the existing
  load-failure state and asserts the reviewed message. The maintainer confirms
  any recovery wording matches an existing action.
- Saving failure: the owning production component test reaches the existing
  save-failure state and asserts the reviewed message. The maintainer confirms
  any recovery wording matches an existing action.
- No behavior changes: focused client tests plus inspection of the diff confirm
  that only user-facing strings and their assertions changed; no API,
  transport, state, control, or data behavior changed.
- Copy quality: maintainer sign-off records review against every item in the
  style checklist.