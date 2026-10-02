# Define the Books discovery API

Own the server-side filtering, title/author search, bounded pagination, and
unfiltered compatibility contract needed by the larger-collection Books page.

Parent Task: tasks/books-discovery/000-main.md

## Requirements checklist

- [ ] `GET /books` supports the agreed optional read-status filter.
- [ ] `GET /books` supports the agreed title-or-author search behavior.
- [ ] Parameterized requests return bounded pages and enough metadata for the
  client to render valid navigation.
- [ ] Requests without discovery parameters remain compatible with existing
  callers, including the current unfiltered response shape and collection.
- [ ] Existing POST, PUT, and DELETE behavior remains available to current
  callers.

## Supporting facts

- The route in `server/app.py` currently ignores `request.args` and returns
  the mutable global collection directly in a `status`/`books` envelope.
- `server/query.py` is the existing home for list-selection logic but currently
  only copies an input iterable.
- `tests/test_books_api.py` has no assertions for response contents, query
  parameters, pagination, or mutation effects beyond HTTP status.

## Execution plan
Status: Draft

Define the optional query contract first, including accepted values,
case/whitespace behavior, page numbering, page size, ordering, and metadata.
Keep the no-argument branch compatible with the current response contract.
Place reusable filtering/search/pagination calculations in the query module and
keep the Flask route responsible for request parsing and response assembly.
Do not alter mutation endpoint shapes unless the resolved discovery contract
shows a necessary compatibility-preserving correction.

Add server tests at the Flask test-client boundary for unfiltered
compatibility, each selection dimension, combined selection, page limits,
out-of-range behavior, and no-match responses. Retain the existing mutation
tests and add assertions only where needed to demonstrate that CRUD endpoints
remain usable.

### Implementation decisions and open questions

This subtask recommends server-side selection because the requested use case is
a larger collection and the repository already exposes an API query-parameter
hook. The public parameter names, matching rules, page-size policy, metadata
shape, and out-of-range behavior remain unresolved in the parent task and
must be approved before this subtask starts.

### Documentation

Provide the API facts needed by the parent task's maintained development guide
after the contract is implemented. Do not update current documentation during
the planning-only phase.

### Task checklist

- [ ] Resolve the API contract questions from the parent task.
- [ ] Implement selection logic and route parsing.
- [ ] Preserve and test the no-parameter response contract.
- [ ] Add or update server API tests for selection and pagination.
- [ ] Report response and ordering facts back to the parent task.

### Requirement verification

- The Flask test client must prove filtered and paginated results at the
  public `/books` boundary, not only test a helper in isolation.
- A no-parameter request must prove the existing envelope and full collection
  remain available.
- Existing POST, PUT, and DELETE tests must continue to collect and pass.
