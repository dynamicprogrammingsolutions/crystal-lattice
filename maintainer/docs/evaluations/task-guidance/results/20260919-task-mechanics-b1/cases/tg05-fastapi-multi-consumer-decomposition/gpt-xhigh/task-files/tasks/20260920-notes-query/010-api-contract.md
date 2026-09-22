# Define and deliver the notes-query API contract

Own the public HTTP contract and FastAPI implementation for bounded,
deterministically sorted, optionally filtered note collection queries. This
subtask must establish the contract before downstream package or CLI work
depends on it.

Parent Task: tasks/20260920-notes-query/000-main.md

## Requirements checklist

- [ ] The notes-query HTTP contract is explicitly documented and approved
  before client or CLI query parameters are implemented.
- [ ] `GET /notes/` supports the approved bounded pagination behavior.
- [ ] `GET /notes/` returns a stable deterministic ordering under the approved
  sorting contract, including its tie-breaking behavior.
- [ ] `GET /notes/` supports the approved optional text-filter behavior.
- [ ] An unparameterized `GET /notes/` continues to return the existing
  collection JSON array shape and all notes expected by the preserved
  unparameterized behavior.

## Scope and boundary

This subtask owns the wire-level parameter names and validation, response
shape, query semantics, database selection/order behavior, API specification,
and service-level tests. It does not own Python keyword names or CLI flags
except where those must mirror the approved wire contract.

## Research and supporting facts

- The route is registered by `src/app/main.py` under `/notes`; the collection
  handler is `read_all_notes()` in `src/app/api/notes.py`.
- `src/app/api/crud.py:get_all()` currently returns
  `database.fetch_all(notes.select())`, with no explicit order, bounds, or
  filter.
- `src/tests/test_notes.py` currently checks only the 200 response and list
  type for the collection route, so focused query coverage is required.
- `docs/development/index.md` currently says that no notes-query
  specification exists.

## Execution plan

Status: Draft

1. Resolve the parent task's public-contract questions, especially wire
   parameter names, page defaults and maximum, invalid-value behavior, sorting
   and tie-breaking, filter fields/matching, and response shape.
2. Write the approved contract in `docs/development/notes-query.md` and link
   it from `docs/development/index.md`. Keep any pre-implementation
   specification visibly proposed/not implemented until the service is ready.
3. Implement the collection query at the API/CRUD boundary using the
   documented validation and database semantics while keeping the no-argument
   route compatible.
4. Add service-level tests using `TestClient(app)` and controlled records to
   prove page bounds, stable ordering, filter behavior, invalid inputs, and
   the unparameterized JSON-array response.
5. Hand the settled wire contract to the client and CLI subtasks without
   changing it ad hoc during consumer implementation.

### Implementation decisions and open questions

- Decision: this subtask is the contract owner and the only place allowed to
  settle the wire-level query semantics before consumers begin.
- Decision: decisive evidence crosses the real FastAPI route and database
  access boundary; a CRUD mock is not sufficient for the collection query.
- Open: all public choices listed in the parent task remain unanswered,
  including whether query responses carry metadata or remain bare arrays.

### Documentation

- Own `docs/development/notes-query.md` and its link from
  `docs/development/index.md`.
- Ensure the specification states parameter names, types, defaults, maximum
  bounds, validation/error behavior, ordering/tie-breaking, filter semantics,
  response shape, and no-argument compatibility.
- Update the root README's API description when implementation is complete;
  do not present an unimplemented target as current supported behavior.

### Task checklist

- [ ] Obtain answers to the public contract questions.
- [ ] Draft and settle the API specification before consumer implementation.
- [ ] Implement the API/CRUD query behavior.
- [ ] Add real route-level regression and feature tests.
- [ ] Update API-facing documentation and report the decisive evidence to the
  parent task.

### Requirement verification

- The approved specification is inspected for every agreed query parameter,
  bound, sorting rule, filter rule, response rule, and compatibility rule.
- A `TestClient(app)` test seeds notes that distinguish pages, sort ties, and
  filter matches, then calls `GET /notes/` through the public route and
  asserts the complete approved response.
- A no-argument `GET /notes/` assertion confirms a JSON array and preserved
  collection behavior.
- Invalid and over-bound inputs are tested at the HTTP boundary according to
  the approved error contract.

### Additional implementation verification

- Existing create/read/update/delete route tests remain green.
- The implementation uses an explicit database ordering rather than relying
  on SQLite's incidental row order.
- The final API docs and actual route behavior agree before this subtask is
  marked complete.