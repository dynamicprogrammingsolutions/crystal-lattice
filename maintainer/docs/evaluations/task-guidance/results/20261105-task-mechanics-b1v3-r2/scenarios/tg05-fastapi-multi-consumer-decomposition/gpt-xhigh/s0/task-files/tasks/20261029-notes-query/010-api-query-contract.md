# Public API Notes Query

Define and implement the stable HTTP query contract for listing notes, preserving the existing unparameterized response.

## Requirements checklist

- [ ] `GET /notes/` supports bounded pagination, stable sorting, and optional text filtering under an agreed contract.
- [ ] A request without query parameters continues to return the full collection as a JSON array.
- [ ] The complete query contract and route behavior are documented and verified before client or CLI implementation depends on them.

Parent Task: tasks/20261029-notes-query/000-main.md

## Unresolved questions

- See `tasks/20261029-notes-query/000-main.md` for pagination, sorting, filtering, CLI, and invalid-input contract questions. Resolve the API-specific questions before implementation.

## Supporting details

- `src/app/api/notes.py` currently implements `GET /` by returning `crud.get_all()`.
- `src/app/api/crud.py` currently selects all notes without ordering, filtering, or pagination.
- `src/tests/test_notes.py` exercises the collection route through FastAPI `TestClient`, providing a route/database boundary for focused integration tests.

## Execution plan

Status: Draft

Own the externally visible HTTP semantics and ensure downstream consumers can rely on a settled contract. Once the open contract details are approved, implement query validation and database query behavior at the collection route/CRUD boundary, keeping the existing no-parameter response shape and data behavior. Use route-level tests with actual test database operations to establish bounded pages, deterministic sorting, filtering, invalid-value behavior, and legacy behavior. Document the settled contract in the root README before marking the API task complete.

### Implementation decisions and open questions

- Parameter names, default behavior, numeric bounds, sorting options and tie-breaker, filter fields/matching, and invalid-input responses remain unresolved; do not invent them during execution.
- Keep the unparameterized collection response as all notes in a JSON array unless the user explicitly changes that requirement.

### Documentation

- Update the root `README.md` with the implemented HTTP query semantics, constraints, and legacy no-parameter behavior.

### Task checklist

- [ ] Resolve API query contract questions with the user.
- [ ] Implement collection query parsing and database behavior.
- [ ] Add route/database integration evidence for every agreed query condition and legacy behavior.
- [ ] Document and verify the contract before downstream consumer work begins.

### Requirement verification

- Test the public `GET /notes/` route with persisted test notes that distinguish pages, sort order, matching/non-matching text, and boundary conditions.
- Test a request with no query parameters and verify it returns the full collection as the existing JSON array contract requires.
- Test invalid query values according to the approved contract, without adding unspecified fallback behavior.
