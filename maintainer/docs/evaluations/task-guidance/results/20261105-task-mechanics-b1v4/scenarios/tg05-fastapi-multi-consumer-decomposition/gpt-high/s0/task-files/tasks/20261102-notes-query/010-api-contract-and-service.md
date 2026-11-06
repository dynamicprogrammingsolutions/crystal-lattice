# Public Notes Query Contract and Service

Settle and implement the public HTTP query contract before either consumer depends on it.

Parent Task: `tasks/20261102-notes-query/000-main.md`

## Requirements checklist

- [ ] `GET /notes/` supports bounded pagination, deterministic sorting, and optional text filtering under a reviewed public contract.
- [ ] Requests without query options preserve the existing bare-array response and collection behavior.
- [ ] The finalized HTTP contract is documented for consumers before their implementation starts.

## Questions and decisions

- **Requirement question:** Which query parameter names/model, defaults, and maximum page bounds are required?
- **Requirement question:** Which fields can be sorted and searched, what matching semantics apply, and which tie-breaker makes sorting deterministic?
- **Requirement question:** Does the response remain a bare array for all requests, or is pagination metadata required?
- **Design decision:** This service task is the contract gate. Client and CLI implementation must wait until these questions have reviewed answers and the contract documentation is stable.

## Supporting details

- `src/app/api/notes.py` currently returns `crud.get_all()` directly from `GET /`.
- `src/app/api/crud.py` currently selects all notes without ordering or pagination.
- `src/tests/test_notes.py` checks only that the route succeeds and returns a list.
- `README.md` states that the collection route returns every note as a JSON array.

## Implementation plan

Status: Draft

Resolve the public query semantics first, then implement validation and query execution at the service boundary. Ensure ordering includes a unique tie-breaker so records with equal primary sort values have deterministic order across pages. Preserve the existing unparameterized behavior rather than silently changing the result envelope. Document the decided parameters and response semantics where service API users currently learn about the API, and ensure that documentation is ready before consumer work proceeds.

Order matters because the client and CLI must not encode provisional names or semantics. Once the contract and focused route evidence are in place, the service subtask can stop safely and unblock the consumers. The main compatibility risk is changing the no-parameter array behavior; regression coverage and a narrowly scoped implementation provide the rollback path.

### Implementation decisions and open questions

The service remains the sole owner of filtering, page bounds, and sort semantics. Resolve the listed requirement questions before implementation; do not guess defaults, field choices, matching rules, or response shape.

### Documentation

Document the approved query contract and preserve the no-option description in `README.md` or a service-owned API document. Consumers must use this documentation as the source for their matching public options.

### Task checklist

- [ ] Resolve and review public query semantics.
- [ ] Implement bounded pagination, deterministic sorting, and optional filtering.
- [ ] Preserve and test unparameterized collection behavior.
- [ ] Publish the API contract documentation for consumer use.

### Requirement verification

The query capability is verified with focused requests to the public `GET /notes/` route, covering each approved query option, bounds, stable ordering, filtering semantics, and their supported combinations. The check does not cover client or CLI behavior.

Compatibility is verified by a no-parameter request asserting the prior bare-array shape and collection result. Contract readiness is verified by the published service API documentation matching the route behavior and serving as the consumer implementation reference.

### Additional implementation verification

Run the focused service test suite after implementation.