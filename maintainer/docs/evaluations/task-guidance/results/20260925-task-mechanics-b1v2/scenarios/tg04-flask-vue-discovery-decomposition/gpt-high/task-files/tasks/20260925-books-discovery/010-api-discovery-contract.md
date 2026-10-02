# Establish the Books discovery API contract

Define and implement the Flask-side filtering, search, pagination, and compatibility behavior that lets the Books page request a bounded view of a larger collection.

Parent Task: `tasks/20260925-books-discovery/000-main.md`

## Requirements checklist

- [ ] `GET /books` can select by the approved read-status values.
- [ ] `GET /books` can search title and author using the approved matching semantics.
- [ ] `GET /books` can return a bounded page and metadata sufficient for the client to determine current, first, and last-page states.
- [ ] Status filtering and search compose before pagination, with deterministic result ordering preserved from the existing collection unless a different ordering is approved.
- [ ] A request without discovery parameters preserves the existing unfiltered response contract and collection behavior.
- [ ] Existing `POST /books`, `PUT /books/<book_id>`, and `DELETE /books/<book_id>` behavior remains compatible.

## Unresolved requirement questions

- Confirm the query parameter names, page size, and response metadata shape with the parent task before changing the public contract.
- Confirm whether invalid values should be rejected or normalized; do not add undocumented fallback behavior.
- Confirm the approved out-of-range page behavior, since it affects both API semantics and page refreshes after CRUD.

## Research and supporting facts

- `server/app.py` owns the HTTP route and currently returns `{"status": "success", "books": BOOKS}` for both an unfiltered GET and a POST.
- `server/query.py:list_books` is currently a pure pass-through and can become the reusable selection boundary without coupling tests to Flask request parsing.
- `tests/test_books_api.py` has only status-code coverage today, so response contents, parameter composition, pagination bounds, and compatibility need focused tests.
- The server stores books in process-global `BOOKS`; tests that mutate it need isolation or cleanup so discovery assertions do not depend on prior test order.

## Execution plan

Status: Draft

Keep request parsing and collection selection separate. Parse only the approved query contract at the Flask boundary, pass normalized values to `list_books`, and let the query function perform status filtering, title/author matching, stable ordering, and page slicing. Build the response without removing the existing `status` and `books` fields; add only the approved pagination information. The no-parameter path must continue to expose the existing unfiltered collection semantics, including compatibility for callers that do not know about discovery metadata.

Add route-level tests against Flask’s test client for each supported filter, composed search/filter cases, page boundaries, no-match results, invalid or out-of-range behavior once approved, and the no-parameter legacy response. Keep mutation tests and add a regression asserting that mutation responses still use their existing shape. Verify selection logic independently where that reduces duplication, but treat the route tests as the decisive API evidence.

### Implementation decisions and open questions

- `server/query.py` owns selection calculations; `server/app.py` owns HTTP parsing and response compatibility.
- Do not move CRUD behavior into the query helper or change mutation status codes/response keys.
- The public parameter names, metadata shape, invalid-input policy, and out-of-range policy require parent-task approval before execution.

### Documentation

- Contribute the verified query parameters, response metadata, compatibility guarantee, and examples to the maintained Books discovery developer documentation selected by the parent task.
- Document only behavior covered by route tests.

### Task checklist

- [ ] Confirm the approved API/query contract.
- [ ] Implement the reusable selection behavior and Flask parameter parsing.
- [ ] Preserve the unfiltered and mutation response contracts.
- [ ] Add route and query tests for supported combinations and boundary cases.
- [ ] Record test evidence and hand off the stable contract to `020-books-page-discovery-state.md`.

### Requirement verification

- Filtering and search: Flask test-client requests with real query parameters and assertions on returned book IDs and metadata.
- Pagination: first, middle, final, and no-result page requests through `/books`, with assertions on bounds/metadata.
- Compatibility: an unparameterized `/books` request and existing POST/PUT/DELETE tests, including response keys and status codes.