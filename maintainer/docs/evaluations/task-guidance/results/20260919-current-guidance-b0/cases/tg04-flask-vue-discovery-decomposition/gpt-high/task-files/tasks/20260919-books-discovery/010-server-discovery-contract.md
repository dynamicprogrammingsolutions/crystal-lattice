# Server discovery contract

Define and verify the Flask API behavior needed for status filtering, title or
author search, bounded pagination, and compatibility with existing consumers.

Parent Task: tasks/20260919-books-discovery/000-main.md

## Requirements checklist

- [ ] `GET /books` supports the approved read-status filter.
- [ ] `GET /books` supports the approved title/author search semantics.
- [ ] `GET /books` supports bounded, deterministic pagination and returns
      metadata sufficient to render page controls.
- [ ] Omitted discovery parameters retain the existing unfiltered books
      response compatibility required by current consumers.
- [ ] Invalid or out-of-range parameters follow the approved normalization or
      rejection policy.
- [ ] Existing POST, PUT, and DELETE routes retain their supported behavior.
- [ ] Server tests cover the query combinations and boundaries at the HTTP
      endpoint.

## Supporting facts

- `server/app.py` owns the `/books` GET and CRUD routes.
- `server/query.py:list_books` is currently a passthrough and can become the
  reusable selection boundary.
- The current list response is a JSON object with `status` and `books`; the
  compatibility requirement must be explicit before adding metadata or
  changing the unfiltered representation.

## Execution plan

Status: Draft

Define the approved query vocabulary and response contract first. Implement
selection as a deterministic pipeline (status filter, normalized search,
stable ordering, then page slicing) in the server query boundary. Adapt the
route to parse request parameters and return the approved pagination metadata,
while preserving mutation routes. Add endpoint tests for defaults,
combinations, page edges, empty results, invalid inputs, and unfiltered
compatibility.

### Implementation decisions and open questions

This subtask depends on the main task’s decisions about parameter names,
case/whitespace matching, page size, response metadata, and malformed-input
handling. Do not settle those public-contract questions locally.

### Documentation

If the project README or another maintained development document describes
`GET /books`, update that source with the approved query and response
contract. Do not add a new API document without an identified owner and
audience.

### Task checklist

- [ ] Confirm the approved query and response contract.
- [ ] Implement the server selection/pagination boundary.
- [ ] Preserve and test unfiltered GET and CRUD compatibility.
- [ ] Add endpoint tests for filters, search, pagination, and invalid inputs.
- [ ] Record evidence and any deviations in the parent task.

### Requirement verification

Use Flask test-client requests against `/books` with real fixture data. The
tests must prove both the filtered response and the metadata that the client
will consume, plus a request with no discovery parameters that preserves the
legacy contract.

### Additional implementation verification

- Verify stable ordering across requests so page transitions do not reshuffle
  unchanged data.
- Verify pagination metadata is internally consistent for zero results and the
  final page.
- Verify POST/PUT/DELETE do not require or accidentally apply list parameters.