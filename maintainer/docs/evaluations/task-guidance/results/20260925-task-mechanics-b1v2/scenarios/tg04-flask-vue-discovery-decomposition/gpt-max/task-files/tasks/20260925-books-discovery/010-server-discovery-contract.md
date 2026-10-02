# Server discovery contract

Define the Flask collection-query behavior needed by the Books page while
preserving the existing no-query collection and CRUD API behavior.

Parent Task: `tasks/20260925-books-discovery/000-main.md`
Depends On: None

## Requirements checklist

- [ ] **S1 — Queryable collection:** A query-bearing `GET /books` can select
  by read status and search title or author according to the approved matching
  semantics.
- [ ] **S2 — Bounded pagination:** A query-bearing collection response exposes
  the selected page and enough totals/bounds for a client to render valid
  navigation controls, with deterministic ordering.
- [ ] **S3 — Legacy compatibility:** A no-query `GET /books` remains a
  successful complete-collection response for existing callers, subject to the
  approved byte-level compatibility decision.
- [ ] **S4 — Mutation compatibility:** Existing POST, PUT, and DELETE routes
  retain their current behavior and data effects; discovery selection does not
  mutate the source collection.

## Supporting facts

- `server/app.py` owns the `/books` route and currently returns
  `{"status": "success", "books": BOOKS}` for GET without query handling.
- `server/query.py` has no current policy beyond copying the iterable, so
  selection, search normalization, ordering, and page slicing can be isolated
  there without making the route itself the data-selection implementation.
- `tests/test_books_api.py` currently proves only status codes and does not
  protect the response shape, filtering, pagination, or no-query full-list
  behavior.
- The global in-memory `BOOKS` fixture means tests must avoid relying on
  mutation order or leaking created records into later cases; fixture reset or
  controlled snapshots may be needed during implementation.

## Execution plan

Status: Draft

Keep request parsing and HTTP envelope decisions in `server/app.py`, and keep
pure collection transformation in `server/query.py`. The query-bearing path
should normalize the approved status/search/page values, filter without
changing `BOOKS`, apply a stable ordering, slice to the fixed or approved page
size, and return metadata sufficient for the Vue page to know the total number
of pages. The no-query path should continue to return the complete collection
contract rather than accidentally becoming paginated for existing callers.

Add route-level tests with representative read/unread books, title-only and
author-only matches, no-match results, first/middle/last page bounds, and
legacy no-query behavior. Keep mutation tests on the same public routes so
compatibility is demonstrated at the HTTP boundary rather than only through
the helper.

### Implementation decisions and open questions

- This child owns the server’s reusable HTTP/data-selection boundary; it does
  not own Vue route state or UI wording.
- The response field names, query names, page-size value, malformed-value
  response, and out-of-range policy are inherited from the parent task’s open
  questions and must be settled before implementation.
- The recommended compatibility boundary is to preserve the no-query
  full-list response and introduce pagination metadata only where the
  discovery query contract requires it. If exact JSON preservation is required,
  the route tests must assert that explicitly.

### Documentation

Document the approved server query parameters, matching rules, pagination
metadata, invalid/out-of-range behavior, and no-query compatibility in the
maintained Books-discovery developer document planned by the parent task.
Keep the API claims out of current guidance until the route and tests exist.

### Task checklist

- [ ] Resolve the inherited API contract questions.
- [ ] Implement pure selection/search/pagination behavior in the server query
      boundary and connect it to `GET /books`.
- [ ] Preserve and regression-test no-query GET plus POST/PUT/DELETE behavior.
- [ ] Add focused route tests for matching, page bounds, metadata, and empty
      results.
- [ ] Record the HTTP-boundary evidence and pass the contract to the page
      subtask.

### Requirement verification

- **S1:** Flask test-client requests with real query parameters and a
  representative collection must assert both title and author matches,
  status filtering, and the returned rows.
- **S2:** Flask test-client requests must assert page metadata and bounded
  slices at first and last pages, including a no-match/zero-result case.
- **S3:** A no-query test must assert the complete collection and legacy
  response fields; exact-body assertions depend on the compatibility answer.
- **S4:** Existing mutation tests plus a post-mutation GET through the same
  Flask routes must show that CRUD effects remain visible and discovery
  selection itself is read-only.