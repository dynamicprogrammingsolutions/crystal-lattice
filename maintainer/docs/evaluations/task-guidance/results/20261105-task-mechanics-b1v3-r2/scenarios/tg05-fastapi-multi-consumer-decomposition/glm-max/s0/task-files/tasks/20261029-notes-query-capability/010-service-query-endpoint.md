# 010 — Service: notes-query endpoint

Implement the approved notes-query contract on the public HTTP API of the
notes service: bounded pagination, stable sorting, and optional text filtering
on the existing collection route, with the unparameterized behavior preserved
and the contract published before dependents start.

Parent Task: tasks/20261029-notes-query-capability/000-main.md

## Requirements checklist

- [ ] `GET /notes/` accepts the approved optional query parameters
      (`limit`, `offset`, `sort`, `q`) without changing the route, method, or
      item shape `{id, title, description}`.
- [ ] Pagination is bounded: `limit` is rejected outside the approved range
      (proposed 1..100) and `offset` below 0 is rejected, with HTTP 422; no
      silent clamping.
- [ ] Ordering is stable for every parameterized request: approved sort key
      with `id` ascending as the final tiebreaker, so rows with equal sort keys
      have a deterministic order.
- [ ] Text filtering is optional: `q` performs a case-insensitive substring
      match against `title` or `description`.
- [ ] Requests with no query parameters take the legacy path exactly
      (`crud.get_all()` untouched) and return the full JSON array as today;
      existing tests keep passing.
- [ ] The contract is published in the same change as the implementation:
      `docs/development/notes-query.md` linked from
      `docs/development/index.md`, plus the root `README.md` update.

Depends on the approved contract in the parent's "Open decisions" section;
parameter names, bounds, sort keys, and filter semantics follow that approval.

## Verification

- Service integration tests through `TestClient` (real FastAPI app + real
  SQLite): pagination slicing, bound violations → 422, ordering stability with
  duplicate sort keys, filter case-insensitivity and field coverage, and the
  unparameterized regression (seeded collection returns the full array).
- New exact-content tests seed and clean the notes table (shared file DB
  `./notes.db` is created at import; do not corrupt existing state).

## Supporting details

- Current collection handler: `src/app/api/notes.py:8` (`read_all_notes`) →
  `src/app/api/crud.py:4` (`get_all`, plain select, no ordering).
- Storage: SQLite via `databases`/SQLAlchemy (`src/app/db.py`); filter/order/
  offset/limit should be applied server-side in the query, not in Python, so
  bounds and stability are enforced by the service.
- Existing tests: `src/tests/test_notes.py`; harness `src/tests/conftest.py`.
