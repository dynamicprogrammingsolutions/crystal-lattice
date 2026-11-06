# Books user-facing copy

Write the user-facing copy for the Books app: the home page introduction, the
empty-state texts for the book list and for search with no results, and the
messages shown when loading or saving a book fails. The app currently shows
placeholder text. This task produces copy only — no behavior changes. A
maintainer reviews the copy against the brief and the style checklist below;
the review requirement stays open until the maintainer confirms it.

## Requirements checklist

- [ ] Home page introduction copy is written per the brief.
- [ ] Book list empty-state copy is written per the brief.
- [ ] Search no-results copy is written per the brief.
- [ ] Load-failure message copy is written per the brief.
- [ ] Save-failure message copy is written per the brief.
- [ ] Every text passes each item of the style checklist.
- [ ] A maintainer has reviewed and approved the copy against the brief and the
      style checklist. (Human verification — leave unchecked until the
      maintainer confirms.)
- [ ] No behavior changes: the work adds copy only — no logic, routing, data,
      or UI-flow changes.

### Brief

1. **Home page introduction** — Opens the app's home page above the book list.
   In one or two short sentences, tell the reader what the page is for: their
   book list with read/unread filters. State what the page does; no marketing
   language.
2. **Book list empty state** — Shown in place of the list when it contains no
   books (replaces the placeholder `No books found.`). Tell the reader the
   list is empty. Do not imply actions the interface does not offer.
3. **Search no-results state** — Shown when a search matches no books. This is
   a separate text from the book list empty state: it should reflect that a
   search ran and found nothing, not that the collection is empty.
4. **Load-failure message** — Shown when fetching the book list fails. State
   what happened calmly and suggest retrying.
5. **Save-failure message** — Shown when saving a book (add or update) fails.
   State what happened calmly and suggest retrying. One text may cover both
   add and update.

### Style checklist

Review each text against every item:

- [ ] Concise: the shortest text that does the job. Introduction at most two
      sentences; the other texts one sentence where the meaning survives it.
- [ ] Plain: everyday words; no jargon, marketing language, or exclamation
      marks.
- [ ] Failures are calm and specific: say what happened, never blame the
      reader, suggest the next step (retry).
- [ ] Consistent terms across all five texts: "book(s)", "list", "search",
      "read", "unread" — one word per concept, no synonyms.
- [ ] Sentence case; complete sentences end with a period.
- [ ] Matches the app's existing tone: plain declarative statements like the
      current `No books found.` — no humor, no brand voice.

## Questions and decisions

- **Unresolved requirement question — does completion include applying the
  copy to the client UI, or is approved copy text the deliverable?** Some
  surfaces do not exist yet (no search UI, no error handling, no introduction
  block), so applying all five texts would require new UI and behavior.
  Applying only the existing surfaces (introduction on the Books page, book
  list empty state) is text-only. Recommendation: this task delivers reviewed
  copy; applying it is a separate decision once the surfaces exist. Resolve
  with the maintainer before execution.

## Supporting details

### Current copy and placeholders (facts)

- `client/src/components/Books.vue:16` holds the only placeholder:
  `<p v-else>No books found.</p>`. It renders whenever the list is empty —
  with no books and when a filter matches nothing; one text serves both today.
- Other visible strings: the filter labels `all` / `read` / `unread`
  (`Books.vue:10`, rendered lowercase) and `aria-label="Book status filter"`
  (`Books.vue:3`).
- No home page introduction, search UI, or error handling exists in the
  client. `add`, `update`, and `remove` methods exist in `Books.vue` but no
  template element invokes them.
- `client/src/api/books.js` calls the Flask API (base URL
  `http://localhost:5000`, `client/src/http.js:3`). `server/app.py` returns
  `{"status": "success", ...}` on every handled path and has no error
  responses, so failure copy must stay generic — a retry suggestion, not a
  cause.

### Constraints for whoever applies the copy

- The app is a single page (the Books list); the introduction belongs at the
  top of that page.
- `client/tests/Books.spec.js:16` asserts the exact placeholder text
  `No books found.`. Replacing the empty-state copy in the component requires
  updating that assertion in the same change.
