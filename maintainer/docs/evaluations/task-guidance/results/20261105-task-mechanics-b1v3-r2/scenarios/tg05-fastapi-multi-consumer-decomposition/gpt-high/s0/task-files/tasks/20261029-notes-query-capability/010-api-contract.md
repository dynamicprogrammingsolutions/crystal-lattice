# Public Notes Query API

Define and implement the stable HTTP query contract for notes before downstream consumers rely on it.

Parent Task: tasks/20261029-notes-query-capability/000-main.md

## Requirements checklist
- [ ] Support bounded pagination, stable sorting, and optional text filtering on `GET /notes/`.
- [ ] Preserve the no-parameter endpoint's current complete JSON-array response.
- [ ] Resolve and document all public query parameter, validation, ordering, filtering, and parameterized response semantics before client implementation.

## Unresolved Questions
- What pagination parameter names and model, default page size, and maximum bound should be public?
- Which fields and directions can be sorted, and what deterministic tie-breaker applies?
- Which fields are text-filtered, and what are the matching semantics?
- What response shape applies when query parameters are provided?

## Supporting Details
- **Fact:** The route currently calls `crud.get_all()` and yields the entire collection; the existing API test checks only that the response is a list.
- **Decision:** This deliverable owns the public HTTP contract and must complete before client or CLI behavior is based on it.

## Execution plan
Status: Draft

Resolve the listed public-contract questions, then implement query parsing/validation and query execution through the service's existing database boundary. Preserve the existing no-parameter array behavior while applying the approved response contract to parameterized requests. Establish deterministic ordering before applying pagination so repeated requests over unchanged data have stable page boundaries. Update maintained service/root documentation in the same implementation change.

### Implementation decisions and open questions
- All questions above require approved answers; do not infer public names, bounds, fields, response shape, or text semantics in consumer work.
- **Decision:** Keep filtering and ordering in the service query path before pagination, as required to make the returned page reflect the complete filtered/sorted collection.

### Documentation
- Document the finalized endpoint contract and no-parameter compatibility in the maintained root/service documentation.

### Task checklist
- [ ] Resolve every listed contract question and record the answers in the implementation/documentation.
- [ ] Implement query validation, filter, deterministic sort, and bounded pagination at the public route/service boundary.
- [ ] Preserve and verify the unparameterized response.
- [ ] Add public-route tests for all approved query semantics and invalid bounds.
- [ ] Update API documentation before dependent client work proceeds.

### Requirement verification
- Requirements 1–2: Call `GET /notes/` through the app's public HTTP route with representative data; assert bounded pages, filtering, stable sort/tie behavior, and the legacy no-parameter JSON array.
- Requirement 3: Review route behavior and maintained API documentation against the resolved contract; dependent client work begins only after the contract is settled.

### Additional implementation verification
- Run the focused service route test suite and report whether it crosses the public route and database boundary.