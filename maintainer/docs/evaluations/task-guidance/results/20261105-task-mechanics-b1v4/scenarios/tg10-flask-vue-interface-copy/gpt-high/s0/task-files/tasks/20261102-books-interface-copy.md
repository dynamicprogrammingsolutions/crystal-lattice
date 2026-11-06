# Write Books Interface Copy

Replace placeholder user-facing text in the books app with concise, plain copy for the home page introduction, the book-list empty state, search with no results, and failures when loading or saving a book.

## Requirements checklist

- [ ] Write and use copy for the home page introduction.
- [ ] Write distinct copy for an empty book list and a search that returns no results.
- [ ] Write copy for failures when loading a book and when saving a book.
- [ ] Keep the copy consistent with the app's existing concise, plain tone.
- [ ] Have a maintainer review the copy against the brief and style checklist below.
- [ ] Limit changes to user-facing copy; do not change application behavior.

## Brief

Write short, clear interface text that helps people understand the page or state and what it means. Keep the general empty-list message distinct from the no-search-results message. Keep loading and saving failures distinct and accurately tied to the failed action.

## Style checklist

- [ ] Use plain, familiar words and a concise sentence or phrase.
- [ ] Make the relevant page, empty state, or failed action clear.
- [ ] Keep the tone neutral, direct, and consistent with the app.
- [ ] Avoid promising recovery, suggesting actions, or implying behavior the app does not provide.
- [ ] Check punctuation, capitalization, and consistency across all five contexts.

## Supporting details

- `client/src/components/Books.vue` currently renders “No books found.” for an empty book list.
- The inspected component does not currently render a home introduction, search empty state, or loading/saving failure messages. This task is limited to writing and using copy in supported interface contexts; it does not authorize adding behavior or new state handling.