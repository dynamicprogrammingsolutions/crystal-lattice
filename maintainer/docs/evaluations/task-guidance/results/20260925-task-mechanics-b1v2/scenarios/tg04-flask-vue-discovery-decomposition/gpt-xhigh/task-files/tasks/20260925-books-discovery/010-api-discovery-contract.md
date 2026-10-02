# Flask Books discovery API contract

Define and implement the server-side read-status filter, title/author search,
bounded pagination, and compatibility behavior needed by the Books page.

Parent Task: `tasks/20260925-books-discovery/000-main.md`

Depends On: None.

## Requirements checklist

- [ ] The `GET /books` endpoint applies the approved read-status and
  title/author search semantics before pagination.
- [ ] The endpoint returns enough approved pagination metadata for the client
  to render bounded navigation and the selected page.
- [ ] The no-parameter `GET /books` response remains compatible with the
  existing `{status, books}` contract, and POST, PUT, and DELETE behavior is
  preserved.

## Requirement questions and decisions

This subtask is blocked on the parent’s public-contract questions about
parameter names, status values, search matching, page defaults/limits,
invalid values, and the compatible response shape. It must not invent
fallbacks or expose a different API contract to make the implementation
convenient.

## Supporting facts

- `server/app.py` owns the public `/books` routes and currently returns the
  entire mutable `BOOKS` list for GET.
- `server/query.py` is the natural owner for reusable selection logic, but
  currently only copies the input sequence.
- Existing tests use Flask’s test client through `tests/conftest.py`.
- The current tests do not assert response contents, query behavior, or
  isolation of the mutable collection.

## Execution plan

Status: Draft

Keep query parsing at the HTTP boundary and keep collection selection in a
small testable server-side helper. Apply status and search selection before
stable pagination, and return metadata using the approved compatibility
strategy. The mutation routes remain independent of discovery parameters and
retain their current request/response behavior.

Implementation order:

1. Apply the parent-approved query and response contract to the route and
   query helper.
2. Ensure ordering is deterministic and page bounds are explicit, including
   the approved behavior for an empty or out-of-range page.
3. Add Flask boundary tests with representative read/unread titles and
   authors, including combined filters and searches with no matches.
4. Extend compatibility tests for an unfiltered request plus POST, PUT, and
   DELETE, taking care that the module-level fixture data does not make tests
   order-dependent.
5. Hand the exact request parameters, response fields, and boundary behavior
   to the page subtask.

### Implementation decisions and open questions

- The helper should be reusable without Flask request state; parsing and
  validation belong at the route boundary.
- Pagination metadata must be sufficient for the page to disable or hide
  navigation at both bounds without reimplementing collection math.
- The unfiltered compatibility path must be tested as a public response, not
  only through an internal helper.
- Exact query names, metadata names, page-size policy, and malformed-input
  policy remain open until approved in the parent task.

### Documentation

After implementation, document the verified `GET /books` query contract and
response metadata in the maintained development documentation selected by the
parent task. No documentation is changed while this plan is Draft.

### Task checklist

- [ ] Resolve the parent API-contract questions.
- [ ] Implement the approved server selection and pagination behavior.
- [ ] Preserve the no-parameter GET response and mutation routes.
- [ ] Add focused Flask endpoint and helper coverage.
- [ ] Provide the final request/response contract to the page subtask.

### Requirement verification

- Filter/search: Flask test-client requests with approved query parameters
  must return only matching records and must combine predicates as specified.
- Pagination: endpoint tests must prove first, middle, last, empty, and
  out-of-range behavior under the approved page-size and bounds policy.
- Compatibility: a no-parameter `GET /books` and the existing POST, PUT, and
  DELETE sequence must pass through the public routes with the existing
  response contract intact.

### Additional implementation verification

- Check stable ordering across repeated requests and page boundaries.
- Check that malformed or unsupported values follow the approved policy
  without silently selecting an unrelated view.