# Public Notes Query API

Establish and deliver the notes-query contract at the public FastAPI collection route before downstream consumers rely on it.

## Requirements checklist

- [ ] The public collection route supports the approved bounded-pagination, stable-sorting, and optional text-filtering contract.
- [ ] A request without query parameters retains the current complete JSON-array response.
- [ ] The public contract is documented and testable before client or CLI implementation begins.

Parent Task: tasks/20261102-notes-query/000-main.md

## Supporting details

- **Fact:** `src/app/api/notes.py` exposes `GET /notes/` and delegates to `crud.get_all()`.
- **Fact:** `src/app/api/crud.py` currently returns all rows from `notes.select()` without explicit ordering or query parameters.
- **Fact:** `src/app/db.py` stores notes in an existing SQLite table with `id`, `title`, and `description` columns.
- **Fact:** `src/tests/test_notes.py` checks that the unparameterized collection response is a JSON array.
- **Constraint:** Query names, bounds/defaults, sortable fields, tie-breaking, and text matching semantics are unresolved in the parent task and must be approved before implementation.

## Implementation plan

Status: Draft

The API owns the shared contract. Once the parent task's public-interface questions are resolved, encode the approved query parameters and validation in the collection route, and apply filtering, explicit deterministic ordering, and bounded selection in the database query path. Keep the existing no-parameter request as a compatibility path that returns all notes in the existing JSON-array shape. Do not add a second endpoint or alter note representation unless the approved contract requires it.

This deliverable blocks the client and CLI subtasks. Finish the public contract, route behavior, focused route/database tests, and API README update before consumer work begins. This milestone gives consumers one stable source of truth rather than allowing each package to infer API semantics.

Risks include accidental truncation of legacy requests, an unstable ordering for equal sort values, and filtering performed only after fetching all rows. Verify the public route against the database with data that exercises pagination edges, ties, and matches/non-matches. If the new behavior fails, remove or correct the query extension while retaining the original no-parameter route; no database migration should be needed.

### Implementation decisions and open questions

The parent task's unresolved public API decisions must be answered before implementation. This subtask does not choose query names, limits, sort fields, or search semantics independently.

### Documentation

Update the root `README.md` with the approved collection query parameters, their semantics and bounds, and the preserved unparameterized behavior. Ensure FastAPI's generated OpenAPI representation reflects the same contract. Do not create a standalone specification page unless the parent approves that documentation direction.

### Task checklist

- [ ] Resolve the parent task's API contract questions.
- [ ] Implement query validation and database filtering, ordering, and pagination.
- [ ] Add public-route tests for approved query behavior and legacy behavior.
- [ ] Update the root README and verify generated OpenAPI.
- [ ] Mark the API contract milestone complete before consumer implementation.

### Requirement verification

- **Query behavior and legacy compatibility:** Tests through the public collection route with the real application/database verify each approved query condition and the unchanged no-query JSON-array response. They deliberately do not verify client argument mapping, CLI options, or the live network path.
- **Contract readiness:** Inspect the maintained API documentation and generated OpenAPI alongside the passing route tests before unblocking the client and CLI subtasks.

### Additional implementation verification

Check that the selected ordering includes a deterministic tie-breaker and that page selection occurs in the database query rather than only in application memory.