# Server discovery contract

Define and implement the Flask list-endpoint behavior needed by the Books
page for read-status filtering, title/author search, and bounded pagination,
while preserving the existing unfiltered API and CRUD routes.

Parent Task: `tasks/20260926-books-discovery/000-main.md`

## Requirements checklist

- [ ] Query-bearing `GET /books` supports the agreed read-status filter,
  title-or-author search, and bounded page selection.
- [ ] The response gives a client enough stable, explicit information to
  render page bounds and reconcile a selected page after a result-set change.
- [ ] Filtering and search are applied before pagination using a deterministic
  ordering.
- [ ] A no-parameter `GET /books` remains compatible with the current
  unfiltered response and result behavior.
- [ ] Existing POST, PUT, and DELETE behavior remains available and does not
  require discovery parameters.

## Unresolved requirement questions

- Confirm the public query parameter names and accepted read-status values.
- Confirm matching semantics for title and author search.
- Confirm fixed/default page size and behavior for invalid or out-of-range
  page values.
- Confirm whether query-bearing responses may extend the existing envelope
  with metadata or need a separate compatibility-preserving shape.

## Supporting facts

- `server/app.py` currently returns the global `BOOKS` list directly for
  `GET /books`, with no query processing.
- `server/query.py` contains only `list_books(books)`, so it is a natural
  home for isolated selection/pagination logic if that ownership remains
  useful.
- `tests/test_books_api.py` currently checks only status codes and mutates the
  module-level collection without a reset fixture.

## Execution plan

Status: Draft

Keep the route responsible for parsing the agreed public query contract and
delegate pure selection/pagination calculations to a small query-layer
boundary. The selection pipeline should use a stable order, apply read status
and title/author matching before slicing, and return explicit page metadata for
query-bearing requests. The route must leave the current no-parameter
`{status, books}` behavior intact and must not alter POST, PUT, or DELETE
semantics.

1. Resolve the public query and response questions with the parent task.
2. Add focused query-layer tests for each filter, the OR search behavior,
   boundary pages, zero-result selections, and stable ordering.
3. Implement query parsing/selection and the agreed metadata shape in the
   route/query boundary.
4. Add Flask API tests for the public query contract and no-parameter
   compatibility, using isolated seeded data.
5. Re-run the existing mutation tests and verify no discovery query is needed
   by POST, PUT, or DELETE.

### Implementation decisions and open questions

- The server child owns data selection and the public list response; it does
  not own Vue URL naming or control rendering.
- Stable ordering is a necessary pagination invariant, but its exact field
  and compatibility implications should be recorded when the API contract is
  decided.
- Do not silently choose coercion or fallback behavior for malformed query
  values; settle the public behavior before implementation.

### Documentation

Provide the verified query-bearing `GET /books` contract to the parent for
inclusion in `README.md`. No standalone server documentation page is needed
for this small API.

### Task checklist

- [ ] Resolve the server-facing public contract.
- [ ] Add query-layer and route-level evidence.
- [ ] Preserve and verify no-parameter list compatibility.
- [ ] Preserve and verify CRUD behavior.
- [ ] Hand the response shape and boundary rules to the client child.

### Requirement verification

- Filtering, search, page slicing, and metadata are verified at the Flask
  route with requests to the real `GET /books` endpoint, not only by calling a
  helper.
- No-parameter compatibility is verified by a direct `client.get("/books")`
  assertion against the established envelope and complete seeded result set.
- CRUD preservation is verified through direct POST, PUT, and DELETE requests
  after query behavior is present.

### Additional implementation verification

- Reset the module-level book collection per test or otherwise isolate test
  data so query assertions are deterministic.
- Include first, middle, last, empty, and beyond-boundary page cases according
  to the approved invalid-page policy.