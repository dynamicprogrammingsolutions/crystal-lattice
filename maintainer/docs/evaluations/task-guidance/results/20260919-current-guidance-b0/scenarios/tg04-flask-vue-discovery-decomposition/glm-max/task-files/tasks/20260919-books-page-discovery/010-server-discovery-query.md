# Server discovery query support for /books

Add read-status filtering, title/author search, and bounded pagination to the
books listing API while keeping the unfiltered response and all CRUD endpoints
unchanged. Independently useful: the API gains a testable selection capability
that any client can consume.

Parent Task: tasks/20260919-books-page-discovery/000-main.md

## Requirements checklist

- [ ] `GET /books` accepts an optional read-status filter returning only read or only unread books.
- [ ] `GET /books` accepts an optional case-insensitive substring search matching title or author.
- [ ] `GET /books` accepts an optional 1-based page selector served in fixed-size, server-enforced pages, applied after filter and search.
- [ ] The listing response exposes the total number of books matching the active filter and search so clients can render bounded pages.
- [ ] Filter, search, and page combine in a single request.
- [ ] `GET /books` without discovery params returns the full unfiltered list in the current response shape.
- [ ] POST /books and PUT/DELETE /books/<book_id> behavior and responses are unchanged.
- [ ] The API contract slice of the discovery documentation is updated in the same change.

## Supporting facts

- `server/app.py` currently reads no query parameters; the list response is
  `{"status": "success", "books": BOOKS}` and the item response is
  `{"status": "success", "book": current}`.
- `server/query.py::list_books` is an unused passthrough — extend this module
  so selection logic has an owned home, and route list requests through it.
- `tests/test_books_api.py` asserts status codes only; it does not prove
  response-shape compatibility, so explicit compatibility assertions are new
  work.
- The Flask test client (`tests/conftest.py`) is the maintained harness for
  HTTP-boundary evidence.
- Contract details (param names, page size, `total` field, invalid-value
  handling) are recommendations D1/D2/D6 in the main task, pending approval.

## Execution plan

Status: Draft

Implement selection as pure functions in `server/query.py`: filter by read
status, case-insensitive substring match over title and author, slice the
resulting list by page against the fixed page size, and return the page items
plus the match count. `app.py` parses `request.args` on GET only and passes
the values through the selection module; POST/PUT/DELETE stay untouched. The
param-less path must produce exactly the current response body.

Verification: unit tests for the selection math (filter, search
case-insensitivity, pagination bounds, combined params, out-of-range page) and
pytest HTTP tests for parameter handling, the combined case, unfiltered
compatibility (exact shape and full list), and CRUD regression. Unit tests are
appropriate for the pure selection functions; the HTTP boundary proves
routing and selection interacting.

### Implementation decisions and open questions

- Contract details follow main-task D1/D2/D6 and are recommendation-level
  until approved; treat them as inputs, not settled decisions.
- Local, reversible choices: selection functions return `(page_items, total)`;
  an out-of-range page yields an empty item list with the real total.

### Documentation

Update `docs/development/index.md`: document the discovery query parameters,
the fixed page size, the `total` field, and the unchanged unfiltered behavior.

### Task checklist

- [ ] Selection logic in `server/query.py` with unit tests
- [ ] Query-param wiring in `server/app.py` (GET only)
- [ ] HTTP tests: filter, search, pagination, combined, unfiltered compatibility, CRUD regression
- [ ] API contract documented in `docs/development/index.md`

### Requirement verification

- Selection behavior → unit tests over `server/query.py` (pure boundary).
- HTTP behavior and compatibility → pytest via the Flask test client
  (`tests/test_books_api.py`), the real routing boundary. The existing tests
  remain as a status-level regression anchor only; they do not assert shape.