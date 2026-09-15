# Test 35: Flask/Vue book-filter requirement quality

Requirement coverage: `DOCGUIDE-005`–`DOCGUIDE-006`, `DOCVAL-010`,
`DOCVAL-011`

## Source project

- Project: Flask-Vue CRUD, a Vue single-page book application with a Flask API.
- Upstream: `https://github.com/testdrivenio/flask-vue-crud`
- Pinned revision: `be91da59a10d07384537c2f76f4505eb344d1682`
- License: MIT

## Project context

The Vue Books page loads `GET /books`, renders title, author, and read status,
and refreshes the complete collection after add, update, or delete. The Flask
route returns `{"status": "success", "books": [...]}` and currently has no
filter parameter.

## Exact user prompt

> Please inspect this Flask and Vue book application. Readers need to switch
> the Books page between All, Read, and Unread books. Prepare a specification
> and requirements for adding this user-facing filter across the Vue client
> and Flask server. All must remain the initial view. Read and Unread must
> request the corresponding server-filtered collection through an optional
> `read` query parameter on `GET /books`; omitting the parameter must keep the
> current all-books response. Preserve the existing JSON response shape. The
> selected filter must remain active when the list refreshes after adding,
> updating, or deleting a book, and the page must show a clear empty result
> when no books match. Existing CRUD behavior must remain compatible. Do not
> implement the change or update current user documentation.

## Exact task-file user prompt

> Please inspect this Flask and Vue book application. Readers need to switch
> the Books page between All, Read, and Unread books. Add this user-facing
> filter across the Vue client and Flask server. All must remain the initial
> view. Read and Unread must request the corresponding server-filtered
> collection through an optional `read` query parameter on `GET /books`;
> omitting the parameter must keep the current all-books response. Preserve
> the existing JSON response shape. The selected filter must remain active
> when the list refreshes after adding, updating, or deleting a book, and the
> page must show a clear empty result when no books match. Existing CRUD
> behavior must remain compatible. Create one task file with a Draft execution
> plan for this change. Do not implement the change.

## Fixture facts

- `Books.vue` loads all books with `axios.get("/books")`.
- The table already displays each book's boolean `read` value.
- Add, update, and delete success and failure paths call `getBooks()`.
- Flask `GET /books` returns all in-memory books in the existing response
  object.
- Existing POST, PUT, and DELETE behavior uses the same route family.
- No book-filter specification exists.
- `TASKS-v7` is not injected for the initial specification baseline.

## Desired target

The evaluator-only target is
[`targets/35-flask-vue-book-filter.json`](targets/35-flask-vue-book-filter.json).
Producing models do not receive it.

## Producer controls

- Start from a fresh fixture with no model-generated seed.
- Inject the requirement-minimal guidance variant.
- Permit changes only under `docs/development/`.
- Do not assert exact requirement wording, count, heading, or file shape.

## Task-file producer controls

- Reuse the same fixture, product outcomes, producers, and efforts.
- Inject the maintained general documentation guidance and effective current
  `TASKS-v7`.
- Request one task file with a Draft plan without separately requesting a
  testing strategy.
- Permit creation of one Markdown task file under `tasks/` only.
- Assess requirement and testing-plan quality from the same output.

## Semantic assessment

Compare generated requirements with the target for visible filter states,
default selection, server query semantics, unchanged response shape, rendered
results, empty state, refresh persistence, and CRUD compatibility. Identify
unnecessary client-only filtering, URL persistence, debounce, pagination,
database, authentication, state-management, or redesign scope.

## Human review

The interpreted baseline summarizes material omissions and additions by model
and effort. Complete generated specification and requirement files remain
optional detail.