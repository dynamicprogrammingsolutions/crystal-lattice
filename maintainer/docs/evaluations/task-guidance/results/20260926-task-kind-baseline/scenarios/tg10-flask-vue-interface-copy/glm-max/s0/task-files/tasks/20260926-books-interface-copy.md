# Books interface copy: replace placeholder texts

Write final user-facing copy for the Books interface — the home page introduction, the empty states for the book list and for search with no results, and the messages shown when loading or saving a book fails. Copy follows the app's existing concise, plain tone; a maintainer reviews it against the brief and the style checklist in this task. No behavior changes: only the existing book-list empty-state string is replaced in code; copy for surfaces that do not exist yet is drafted and recorded in this task.

## Requirements checklist

- [ ] Copy is written for the home page introduction (Brief).
- [ ] Copy is written for the book list empty state (Brief).
- [ ] Copy is written for the search no-results empty state (Brief).
- [ ] Copy is written for the message shown when loading books fails (Brief).
- [ ] Copy is written for the message shown when saving a book fails (Brief).
- [ ] The copy follows the app's concise, plain tone; every text passes the Style checklist.
- [ ] The approved book-list empty-state copy replaces the placeholder in `client/src/components/Books.vue` (text-only change) and `client/tests/Books.spec.js` asserts the new text.
- [ ] Approved copy for the four surfaces with no current UI is recorded in this task for later implementation.
- [ ] A maintainer has reviewed the copy against the Brief and the Style checklist and approved it.

The maintainer-review item is human verification: leave it unchecked until a maintainer confirms. Mark the other items complete only with evidence (the diff, the updated test run).

## Open questions and decisions

No open requirement questions. Decisions made while creating this task — flag them if wrong:

- **Draft copy for surfaces that do not exist yet** (home page introduction, search no-results, load-failure message, save-failure message) is written and recorded in this task, not added to the code. The client has no home page, no search UI, and no error handling; adding any of them would be a behavior change, which the request excludes. Recorded here rather than in a new documentation file per the smallest-documentation-structure rule in `AGENTS.md`.
- **The book-list empty state is replaced in code.** That surface exists today, and swapping the placeholder string for approved copy is a text-only change, not a behavior change. `client/tests/Books.spec.js` asserts the old string, so it is updated in the same change.

## Brief

Audience: readers of the Books page. Tone: the app's existing concise, plain voice (Style checklist below). All texts appear in the page, in English.

1. **Home page introduction** — no home page exists yet (`client/src` has no entry component; the Flask server serves only the JSON API). Purpose: one or two short sentences telling a first-time reader what the Books app is and what they can do here. Drafted for the future home page; not placed in code by this task.
2. **Book list empty state** — exists today: `client/src/components/Books.vue:16` renders "No books found." whenever the list has no rows. That single string currently covers every empty case, including "no books at all" and "the selected read/unread filter matches nothing"; splitting the cases would be a behavior change, so the approved copy must read correctly for both. This text replaces the placeholder.
3. **Search with no results** — no search UI exists (the read/unread status filter is the only lookup today, and it shares the list empty state). Purpose: one short sentence telling the reader the search matched nothing. Drafted for the future search feature; not placed in code by this task.
4. **Loading fails** — no such message exists: no API call in `Books.vue` handles errors. Purpose: one short sentence telling the reader the books could not be loaded. Drafted for future error handling; not placed in code by this task.
5. **Saving fails** — no such message exists (same gap). Purpose: one short sentence telling the reader the book could not be saved. Drafted for future error handling; not placed in code by this task.

## Style checklist (the copy must pass every item)

- [ ] Sentence case; ends with a period; no exclamation marks; no emoji.
- [ ] Short: an empty state or error message is one sentence; the introduction is at most two.
- [ ] Plain everyday words; no jargon or internal terms (API, endpoint, JSON).
- [ ] From the reader's point of view: says what happened or what is shown, without blame, status codes, or technical detail.
- [ ] Uses the interface's own words — "book", "books", "search" — consistently; no synonyms like "item" or "record".

## Facts verified in this workspace

- Client user-facing strings today: the filter button labels `all` / `read` / `unread` (`client/src/components/Books.vue:5`, out of scope) and the empty-state text "No books found." (`Books.vue:16`).
- No home page surface: `client/src` contains only `api/books.js`, `http.js`, and `components/Books.vue`; `vue-router` is a declared dependency but unused; the Flask server (`server/app.py`) serves only the JSON API.
- The empty-state string renders whenever the book list has no rows (`v-if="books.length"` / `v-else`), so it currently covers both "no books at all" and "filter matches nothing".
- No error handling exists in `Books.vue`: `selectFilter`, `add`, `update`, and `remove` await the API without catching failures, and nothing renders failure messages.
- `client/tests/Books.spec.js:16` asserts the literal "No books found.".
- No maintained documentation (`README.md`, `docs/`) references these strings, so this task requires no documentation updates.