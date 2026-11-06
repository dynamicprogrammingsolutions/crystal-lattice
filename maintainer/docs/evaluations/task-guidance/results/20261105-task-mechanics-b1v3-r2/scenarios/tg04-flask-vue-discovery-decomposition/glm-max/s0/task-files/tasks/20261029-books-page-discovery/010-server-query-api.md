# Server query API: filter, search, pagination on GET /books

Add read-status filtering, title/author search, and bounded pagination to
`GET /books` as query parameters, with the response reporting the total match
count. Today's unfiltered response and all CRUD endpoints keep their current
behavior.

Parent Task: tasks/20261029-books-page-discovery/000-main.md

Depends On: (none — first executable child; tasks/20261029-books-page-discovery/020-books-page-discovery-ui.md consumes the contract defined here)

## Requirements checklist

- [ ] R7a — `GET /books?read=true` returns only read books and `read=false` only unread books; absent `read` applies no read filter.
- [ ] R7b — `GET /books?search=<text>` returns books whose title or author contains the text case-insensitively; absent or empty `search` applies no text filter.
- [ ] R7c — `GET /books?page=<n>&page_size=<n>` returns one bounded page of the selected books (1-based `page`); `page_size` has a default and a maximum cap; the response reports `total` (matching books before pagination) so clients can compute page bounds; an out-of-range page returns an empty `books` list with the accurate `total`.
- [ ] R7d — `read`, `search`, `page`, and `page_size` compose in a single request.
- [ ] R6a — `GET /books` with no parameters returns the full book list in the current response shape (`status`, `books`); existing server tests pass unchanged.
- [ ] R6b — `POST /books`, `PUT /books/<id>`, and `DELETE /books/<id>` behavior and responses are unchanged.
- [ ] R8a — The query parameters, defaults, cap, and response fields are documented in the same change that implements them.

There are no unresolved requirement questions; material decisions are recorded in the execution plan below and take effect on plan approval.

## Execution plan

Status: Draft

### Design

- Component responsibilities: `server/app.py` stays a thin route layer — it parses `request.args` and builds the response. All selection, filtering, and pagination logic lives in `server/query.py`, extending the existing `list_books` seam into a pure function over the book list so the logic stays independently testable and the route contract stays declarative.
- Contract (owned by this child, consumed by `020-books-page-discovery-ui.md`):
  - `read`: `true` or `false` (case-insensitive); absent → all books.
  - `search`: case-insensitive substring match against `title` or `author`; absent or empty → no text filter.
  - `page`: 1-based integer; absent or unparseable → 1.
  - `page_size`: positive integer, default 10, capped at 100; absent or unparseable → default.
  - Response: `{"status": "success", "books": [<page items>], "total": <int>}` where `total` counts matching books before pagination. With no parameters the response is the full list (`books` = all books, `total` = count) — the current shape plus the additive `total` field.
  - Ordering remains the existing insertion order; no sorting is introduced.
- Data flow: `request.args` → parse/normalize → pure selection function (read filter → search filter → pagination slice) returning `(page_items, total)` → JSON response.
- Compatibility state: the unfiltered `GET /books` response keeps returning every book; mutation endpoints and their responses are untouched. Adding `total` is additive and backward-compatible for existing consumers.
- Lenient parsing: values that do not parse fall back to the documented defaults rather than introducing a new error-response contract; out-of-range pages are empty results, not errors. The client owns presenting valid bounds.

### Steps

1. Extend `server/query.py`: parse helpers for boolean and bounded-integer parameters, and a pure selection function returning `(page_items, total)`.
2. Wire `server/app.py`: parse `request.args` on GET, call the selection function, include `total` in the response; leave POST/PUT/DELETE paths untouched.
3. Extend `tests/test_books_api.py` at the HTTP boundary: each parameter alone, composition of all four, `total` accuracy, first/last/out-of-range pages, `page_size` cap, case-insensitive title and author matches, unfiltered response shape, and existing CRUD tests passing unchanged.
4. Update the root README with the `/books` query-parameter reference (parameters, defaults, cap, `total`).
5. Run the full pytest suite; all tests collect and pass.

### Implementation decisions and open questions

- Parameter names and defaults (`read`, `search`, `page`, `page_size` default 10, cap 100) — material because they are public API surface; chosen to mirror the URL state the client will use and to keep the response change additive. Plan approval covers them.
- Lenient parsing instead of a 400 error contract — avoids inventing an error-response shape for inputs the request does not specify; the behavior is documented either way.
- `total` added to the response body — the minimal additive change that lets clients render bounded pages; alternatives (pagination headers, a metadata object) rejected as more structure than this API needs.
- Test-state isolation: `BOOKS` is module-level and mutated by CRUD tests; new tests must not leak rows (self-cleaning, like the existing mutation test).

### Documentation

- Root README gains a short `/books` query-parameter reference in the same change as the code (AGENTS.md policy: new public claims ship with the code that makes them true). Audience: API consumers and developers. No new documentation pages or directories.

### Task checklist

- [ ] Implement selection and parsing in `server/query.py`.
- [ ] Wire parameter parsing and `total` into `GET /books` in `server/app.py`.
- [ ] Add HTTP-boundary tests for R7a–R7d and R6 compatibility.
- [ ] Document the query parameters in the root README.
- [ ] Full pytest suite passes cleanly.

### Requirement verification

- R7a–R7d → new pytest route tests through the real Flask app in `tests/test_books_api.py`; the HTTP boundary is the public surface for this child and no mocks are involved.
- R6a → existing `test_books` passes unchanged, plus a new explicit assertion that the no-parameter response carries the full list in the current shape.
- R6b → existing `test_book_mutations` passes unchanged.
- R8a → README diff reviewed in the same change as the code.

### Additional implementation verification

- Repeated query parameters (e.g. `?read=true&read=false`) and integer edge values (`page=0`, negative, non-numeric) behave per the documented lenient rules — asserted once each so parsing is not accidental.
- Confirm the unfiltered response remains byte-identical apart from the additive `total` field by asserting the full documented shape in the no-parameter test.
