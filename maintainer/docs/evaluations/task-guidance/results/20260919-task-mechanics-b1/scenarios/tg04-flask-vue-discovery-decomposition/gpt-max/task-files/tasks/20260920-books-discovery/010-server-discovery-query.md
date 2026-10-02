# Server discovery query and compatibility contract

Define and implement the Flask-side selection, search, and bounded-pagination
contract for Books while retaining the legacy unfiltered list and CRUD
behavior. This is a planned subtask; implementation is **Not implemented**.

Parent Task: tasks/20260920-books-discovery/000-main.md

## Requirements checklist

- [ ] `GET /books` accepts the approved optional read-status and
      title/author-search inputs and composes them against the same collection.
- [ ] Discovery requests return bounded pages with stable ordering and the
      approved metadata and invalid-input behavior.
- [ ] A no-parameter `GET /books` remains compatible with the existing
      unfiltered response contract.
- [ ] Existing POST, PUT, and DELETE routes keep their current behavior and
      response compatibility.
- [ ] Flask test-client coverage proves the discovery and compatibility
      boundaries without bypassing the HTTP route.

## Unresolved requirement questions

This subtask inherits the parent questions that affect the public API. Before
execution, confirm the parameter names/values, search matching rules, default
and maximum page sizes, ordering, invalid-page behavior, metadata shape, and
whether legacy no-parameter responses may gain keys. The server contract must
not silently choose a public behavior that the parent has left open.

## Research and supporting facts

- `server/app.py` owns the `/books` GET/POST route and the `/books/<book_id>`
  PUT/DELETE route.
- `server/query.py:list_books(books)` is currently an identity-style list
  helper and has no query or pagination model.
- The current list response contains `status: "success"` and the complete
  `books` array. Existing API tests do not assert the response body, so
  compatibility assertions need to be added.
- The collection is an in-memory module-level list. The implementation should
  preserve its current mutation semantics unless the approved behavior
  requires a narrowly scoped test-isolation adjustment.

## Execution plan

Status: Draft

1. Record the approved query names, normalized values, default/max bounds,
   stable ordering, page metadata, and no-parameter compatibility rule.
2. Extend the query boundary so filtering and search happen before pagination,
   with the same normalized selection logic used by the route.
3. Update the GET route to distinguish the legacy no-parameter path from
   discovery requests as required by the compatibility decision. Keep
   mutation methods and their response shapes unchanged.
4. Add test data with read/unread books and title/author matches, then cover
   status-only, search-only, combined, empty, first/last, and invalid-page
   requests through Flask's test client.
5. Add a regression assertion for the existing no-parameter response and
   retain the existing CRUD checks.

The output of this subtask is the API contract and evidence that the client
can rely on it. It does not own router state or Vue rendering.

### Implementation decisions and open questions

- The server should perform selection and pagination so large collections are
  not transferred to the browser merely to be filtered there.
- The exact public parameter and metadata names remain open until the parent
  plan is approved.
- No new persistence or sorting policy is authorized by this subtask; stable
  ordering must follow the approved compatibility choice.

### Documentation

- During implementation, document the approved GET query parameters,
  response metadata, bounds, and no-parameter compatibility rule in the
  smallest maintained developer-facing location owned by the server/API.
- Do not create a placeholder API page during this planning-only pass.

### Task checklist

- [ ] Resolve and record the approved server contract in the parent task.
- [ ] Mark this subtask Approved before implementation.
- [ ] Implement the query normalization, selection, and pagination boundary.
- [ ] Preserve and test the legacy list and CRUD routes.
- [ ] Record API test evidence and link any maintained documentation update.

### Requirement verification

- **Status/search selection:** Flask test-client requests against `GET
  /books` must prove each approved filter independently and in combination,
  including no-match results.
- **Bounded pages:** requests for the first, middle, last, and invalid pages
  must prove the approved page size, total/page metadata, stable ordering, and
  boundary behavior.
- **Unfiltered compatibility:** a no-query request must prove the legacy
  `status`/`books` contract and unfiltered contents; existing CRUD requests
  must still return their current success responses.
