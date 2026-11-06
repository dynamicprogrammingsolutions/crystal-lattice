# Public Notes Query API

Define and implement the stable HTTP notes-query contract before consumer packages adopt it.

Parent Task: `tasks/20261102-notes-query/000-main.md`

## Requirements checklist
- [ ] The public notes collection supports bounded pagination, stable sorting, and optional text filtering.
- [ ] Requests without query parameters retain the current bare-array response and collection behavior.
- [ ] The parameterized HTTP contract is settled and documented before consumers rely on it.

## Questions and decisions
- Resolve parameter names, defaults, limits, supported sort keys/directions, deterministic tie-breaker, text-match fields and semantics, and parameterized response shape with the user before execution.

## Supporting details
- The route currently returns `crud.get_all()` directly; CRUD currently selects all notes without ordering or filtering.
- API tests currently cover only successful unparameterized collection listing and route existence.

## Implementation plan
Status: Draft

The API owns query semantics and the public compatibility boundary. Define the parameterized contract first, while preserving the current response for requests without parameters. Implement query behavior at the API/data-access boundary appropriate to the approved semantics, and document supported behavior with focused route-level evidence.

This deliverable blocks client and CLI work because both must consume the same finalized HTTP contract. The principal risk is accidental behavior drift or nondeterministic page boundaries; explicit stable ordering and route-level tests mitigate it. If the contract cannot preserve the existing no-parameter response, pause for review rather than changing it implicitly.

### Implementation decisions and open questions
- The contract questions in the parent remain unresolved and require user approval.

### Documentation
- Update the root API documentation once the behavior is implemented and verified.

### Task checklist
- [ ] Resolve query contract and matching semantics.
- [ ] Implement the public route and data-query behavior.
- [ ] Add route-level tests for query behavior and compatibility.
- [ ] Document the supported HTTP contract.

### Requirement verification
- Exercise the public collection route for pagination bounds, deterministic sorting, text filtering, and the no-parameter bare-list response. These checks prove the public HTTP boundary, not client or CLI behavior.

### Additional implementation verification
- Run the focused API test suite.