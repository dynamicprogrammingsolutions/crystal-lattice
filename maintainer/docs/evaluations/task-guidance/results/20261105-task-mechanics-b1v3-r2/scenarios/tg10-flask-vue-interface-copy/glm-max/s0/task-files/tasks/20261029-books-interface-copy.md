# Books interface copy

Write the user-facing copy for the Vue Books client, replacing the placeholder
texts: the home page introduction, the empty-state texts for the book list and
for search with no results, and the messages shown when loading or saving a
book fails. Copy-only work; no behavior changes.

## Requirements checklist

- [ ] Home page introduction: concise introduction copy is shown at the top of
      the Books page (`client/src/components/Books.vue`, the app's home view).
- [ ] Book-list empty state: new copy replaces the `No books found.`
      placeholder shown when the book list is empty.
- [ ] Search no-results state: copy exists for a search or filter that matches
      nothing and is distinct from the plain empty-list copy.
- [ ] Failure messages: copy exists for failing to load the books and for
      failing to save a book change (two messages).
- [ ] All copy satisfies the style checklist below and matches the app's
      concise, plain tone.
- [ ] A maintainer has reviewed the final copy against this brief and the
      style checklist and approved it (human verification).
- [ ] No behavior changes: copy/text only. Filtering, data flow, API calls,
      and routing logic are unchanged; the client test suite passes, with
      assertions updated only where they asserted replaced text.

## Requirement questions (open)

- Q1 (search no-results): The client has no search input. The closest state is
  the `all`/`read`/`unread` filter, which currently reuses the same
  empty-state paragraph for every empty result (`Books.vue:13-16`). Does this
  task also add the minimal template distinction so the no-results copy is
  displayed, or is the copy written now and wired in a later change?
- Q2 (failure messages): No failure UI exists; load/save calls are awaited
  without error handling (`Books.vue:26-41`), so a failed request currently
  surfaces nothing to the user. Showing the failure copy requires minimal new
  error display, which is new failure-path UI. In scope here, or draft-only
  for a later change?

## Writing brief

- Home introduction: 1–2 short sentences on what the page is for (browse the
  book list, filter by read status). No marketing language.
- Book-list empty state: state plainly that there are no books yet. Reference
  a next action only if the page actually offers it (it currently offers
  filtering only; there is no add-book form on the page).
- Search no-results: acknowledge that the current filter matched nothing and
  point to the way back to the full list (the `all` filter).
- Load failure: say the books could not be loaded and suggest trying again.
- Save failure: say the change could not be saved and suggest trying again.
- Error and empty states must be true of the actual UI; do not promise
  functions the page does not have.

## Style checklist (maintainer review criteria)

- [ ] Concise: shortest clear phrasing; no filler or marketing words.
- [ ] Plain: everyday words, active voice, no jargon.
- [ ] Consistent with existing terms: "books", "read", "unread".
- [ ] Sentence case; full-sentence messages end with a period; short labels
      do not.
- [ ] Each message states the situation and, where the UI offers one, the
      next step.
- [ ] No blame, humor, exclamation marks, or "Oops"/"Sorry" filler in error
      and empty states.
- [ ] No placeholder tokens (Lorem, TODO, "coming soon", "example").
- [ ] Each string stands alone, without referring to text that is not shown.

## Supporting facts (verified in this workspace)

- All UI copy lives inline in `client/src/components/Books.vue`; there is no
  copy or i18n module, no `App.vue`, and no HTML entry file. The Books page is
  the app's only view, so the home introduction belongs at its top.
- Current texts: filter labels `all`/`read`/`unread` (`Books.vue:5`); one
  shared empty-state paragraph `No books found.` (`Books.vue:16`).
- `client/tests/Books.spec.js:16` asserts the exact string `No books found.`,
  so replacing that copy requires updating the assertion in the same change.
- `getBooks`/`addBook`/`updateBook`/`deleteBook` (`client/src/api/books.js`)
  have no catch paths and no error surface anywhere in the component.
- `Books.vue` carries marked functional regressions ("regression: filter
  lost", lines 32/36/40). Out of scope; do not fix them in this task.
- Tone evidence: `No books found.` (short, declarative, terminal period),
  lowercase single-word filter labels, and the plain README description. The
  Flask server (`server/app.py`) returns JSON only and carries no user-facing
  copy.

## Execution plan

Status: Draft

Copy is drafted against the brief, applied to the single page component, and
reviewed by a maintainer before the copy requirements are marked complete.
Copy stays inline in `Books.vue`; no copy/i18n infrastructure is introduced.

1. Resolve Q1 and Q2 with the requester; scope the wiring accordingly.
2. Draft the five strings (introduction, empty list, no results, load
   failure, save failure) against the brief and style checklist.
3. Apply the introduction and empty-state copy in `Books.vue` (static
   template text only).
4. If Q1/Q2 put the wiring in scope: add the minimal template distinction for
   the filtered no-results state and the minimal error display for failed
   load/save; otherwise record the no-results and failure copy as drafted
   with placement deferred.
5. Update `client/tests/Books.spec.js` asserted strings to match shipped copy
   (assert new strings only if they are wired and rendered).
6. Run the client suite (`npm test` in `client/`) and keep it green.
7. Submit the applied copy to the maintainer with this brief and checklist;
   record the review outcome before ticking the review requirement.

### Implementation decisions and open questions

- Decision: copy remains inline in `Books.vue`; no new dependencies or
  copy-management modules, keeping the change copy-only and matching the
  current structure.
- Open: Q1 and Q2 above (wiring scope for no-results and failure copy).

### Documentation

No documentation changes. This is UI copy, not maintained documentation, and
no maintained docs describe the page text (`docs/development/index.md`
records that no book-discovery specification exists). No behavior changes, so
no documentation updates are triggered.

### Task checklist

- [ ] Q1/Q2 resolved with the requester
- [ ] Five strings drafted
- [ ] Introduction and empty-state copy applied to `Books.vue`
- [ ] No-results / failure wiring applied, or placement explicitly deferred
- [ ] `Books.spec.js` assertions match shipped copy
- [ ] Client suite green (`npm test` in `client/`)
- [ ] Maintainer review recorded against the brief and checklist

### Requirement verification

- Introduction / empty-state / no-results / failure copy shown as intended:
  render assertions in `client/tests/Books.spec.js` against the real component
  (the API is mocked at the transport boundary, which is acceptable here
  because the claim is the rendered text, not the transport). Applies to
  wired copy; draft-only copy is evidenced by the approved copy text recorded
  in this task plus the maintainer review.
- Tone/style and the review requirement: maintainer approval recorded in this
  task; human verification, left unchecked until confirmed.
- No behavior changes: diff inspection (copy, static template text, and
  asserted test strings only) plus the full client suite passing.

### Additional implementation verification

- Grep the client source for placeholder tokens (`Lorem`, `TODO`,
  `placeholder`, `coming soon`) and confirm none remain.
