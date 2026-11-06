# Add Optional Notes List Pagination

Add optional limit/offset pagination to `GET /notes/` while preserving its current response behavior for requests without pagination.

## Requirements checklist

- [ ] `GET /notes/` accepts optional limit and offset pagination parameters and returns the requested slice in ascending note-ID order.
- [ ] Collection responses expose the total note count in a response header.
- [ ] Requests without pagination continue to return the current full-list JSON array.
- [ ] Invalid pagination values use normal FastAPI request validation.
- [ ] Other CRUD routes remain unchanged.

## Questions and decisions

- **Requirement question:** What exact response-header name should carry the total note count?
- **Design decision:** Should the total-count header be present only when pagination is requested, or on every `GET /notes/` response?
- **Design decision:** Should negative `limit` or `offset` values be rejected through FastAPI validation? If so, should `limit=0` be allowed?
- **Design decision:** If only `offset` is supplied, should the route return every remaining note? The plan assumes standard limit/offset behavior but leaves this open for confirmation.

## Supporting details

- **Fact:** `src/app/api/notes.py` currently implements `read_all_notes()` by returning `crud.get_all()` directly.
- **Fact:** `src/app/api/crud.py` currently uses `notes.select()` without an explicit sort; paginated selection needs explicit ascending-ID ordering to satisfy the requested slice order.
- **Fact:** `src/tests/test_notes.py` currently has a minimal collection-route check and a basic CRUD-route check; `src/tests/conftest.py` uses FastAPI `TestClient`.
- **Fact:** `README.md` describes the current collection route as returning every note in a JSON array. `docs/development/index.md` says no notes-query specification exists.

## Implementation plan

Status: Draft

Keep pagination scoped to the collection-list path. The existing no-query path must preserve its full-list array behavior. When pagination is used, obtain a total count over all notes and fetch the selected notes ordered by ascending ID, applying the requested offset and limit. Return the selected notes as the same array shape and expose the total count through the agreed response header. Use FastAPI query parameter declarations for request parsing and validation; do not alter the detail, create, update, or delete endpoints. Avoid requiring a new specification page for this focused API behavior.

The header name, when to emit it, negative-value rules, and omitted-limit semantics are material user-visible contract choices and remain unresolved above. Do not finalize those details until they are confirmed. In particular, preserve FastAPI's ordinary validation response for values defined as invalid rather than adding custom error handling.

Order work from contract confirmation to implementation and verification: these decisions determine route parameters and response assertions. The decisive automated evidence should exercise the real `GET /notes/` route through `TestClient` and the application's real persistence setup, checking total count, ID ordering, slice boundaries, full-list behavior without parameters, and validation behavior for the agreed invalid inputs. It should also verify the other CRUD route behavior remains unaffected; direct helper tests or mocked route tests alone do not prove the public contract.

The blast radius is limited to collection retrieval, its persistence query support if needed, focused API tests, and the README's current API description. A regression could change list ordering, default behavior, or the header contract. Keep the implementation additive and confined to the list path; rollback by reverting the collection-route/query and documentation changes together, then rerun the existing and focused tests.

### Implementation decisions and open questions

- Resolve the questions listed above before implementation; no public header or edge-case behavior is chosen by this draft.
- Keep detail/create/update/delete route contracts and behavior untouched.
- Decide during implementation whether collection persistence helpers need a narrowly scoped extension or whether the existing retrieval helper can cleanly support the behavior.

### Documentation

- Update `README.md` in the same change as the behavior, documenting supported query parameters, the confirmed total-count header, and the preserved no-pagination response.
- Do not add a placeholder page or modify `docs/development/index.md` solely to establish a documentation structure.

### Task checklist

- [ ] Confirm the open contract details above.
- [ ] Implement collection-only optional limit/offset pagination with ascending-ID ordering and a total-count response header.
- [ ] Add route-level integration coverage for paginated results, total count, no-pagination compatibility, and invalid values.
- [ ] Exercise create, detail-read, update, and delete through the real API to verify their behavior is unchanged.
- [ ] Update the README to match the implemented public behavior.

### Requirement verification

- **Pagination, ascending-ID slice, and total count:** A `TestClient` integration test against the actual `GET /notes/` route and persistence setup verifies page boundaries, ascending IDs, and the agreed response header. This does not cover performance under large datasets.
- **No-pagination compatibility:** The same public-route test verifies a request without pagination returns the full list as a JSON array. It does not prescribe ordering beyond the existing behavior.
- **Invalid values:** Public-route requests using each confirmed invalid value verify FastAPI's standard validation response. They do not define behavior for unresolved or unapproved inputs.
- **Other CRUD routes:** A `TestClient` smoke sequence through the real API and persistence setup exercises create, detail-read, update, and delete after the collection-route change, asserting their existing response behavior. This verifies the neighboring public routes without claiming broader application-wide compatibility.

### Additional implementation verification

- Run the focused notes API tests, then the repository's broader test suite if available. These are supporting quality checks and do not substitute for the route-level contract evidence above.