# Public Notes Query API

Define and implement the notes collection query contract on the FastAPI public boundary.

Parent Task: `tasks/20261029-notes-query/000-main.md`

## Requirements checklist

- [ ] The collection endpoint supports bounded pagination, stable sorting, and optional text filtering according to the approved contract.
- [ ] Requests without query parameters preserve the current full-array response behavior.
- [ ] The public query contract is documented for API users.

## Unresolved questions

- Query parameter names, pagination defaults/maxima and out-of-range behavior are not specified.
- Supported sort fields, direction syntax, and stable tie-breaking are not specified.
- Filtered text fields and matching/case semantics are not specified.

Resolve these contract questions before execution; do not make consumer-facing choices implicitly.

## Supporting details

- **Fact:** `src/app/api/notes.py` currently exposes `GET /notes/` and returns `crud.get_all()`.
- **Fact:** `src/app/api/crud.py` currently selects all notes without ordering or filtering.
- **Fact:** `src/tests/test_notes.py` verifies only that the result is a list.

## Execution plan
Status: Draft

Implement the agreed public contract at the collection route and data-query layer. Validate request constraints at the HTTP boundary, apply deterministic sorting and approved filtering before pagination, and retain the no-parameter full-array behavior. Update the root README in the same reviewed change. The client and CLI depend on this contract and should not settle incompatible semantics independently.

### Implementation decisions and open questions

- Public parameter names and all semantics listed above require approval before execution.
- Choose the minimal query-layer implementation consistent with the approved contract.

### Documentation

- Update the root `README.md` with the supported contract, parameter bounds/defaults, ordering, filtering, and examples once approved.

### Task checklist

- [ ] Implement the approved collection query contract.
- [ ] Add focused HTTP-boundary tests for accepted/rejected query inputs and query behavior.
- [ ] Verify no-query behavior and update API documentation.

### Requirement verification

- Exercise the actual `/notes/` route with populated notes to verify filtering, stable sorting, and bounded pagination together according to the approved contract.
- Exercise omitted query parameters through `/notes/` and assert the existing full-array response shape and content.

### Additional implementation verification

- Run the focused API suite and applicable full project tests.