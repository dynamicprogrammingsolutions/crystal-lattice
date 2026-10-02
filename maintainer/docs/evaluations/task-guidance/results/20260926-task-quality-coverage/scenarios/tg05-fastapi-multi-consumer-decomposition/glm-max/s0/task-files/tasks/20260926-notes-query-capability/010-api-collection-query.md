# Public API: bounded, sorted, filtered notes collection query

Implement and lock the approved query contract on the notes collection route
(`GET /notes/`): bounded pagination, stable sorting, and optional text
filtering, with unparameterized behavior preserved and the contract recorded
in the maintained service documentation.

Parent Task: tasks/20260926-notes-query-capability/000-main.md
Depends On: none — this is the first subtask; the contract it implements is
approved with the parent plan (decisions D1–D4, D8).

## Requirements checklist

- [ ] `GET /notes/` accepts optional query parameters per the approved
      contract: `limit` (integer 1..100), `offset` (integer ≥ 0), `sort`
      (`id|title|description`, optionally `-`-prefixed for descending), `q`
      (case-insensitive literal substring on `title`).
- [ ] Pagination is bounded by the server: `limit` outside 1..100 is rejected
      with 422; malformed `offset` or unknown `sort` values are rejected with
      422.
- [ ] Results are totally ordered: the requested `sort` field is primary and
      `id` ascending is always appended as tie-break; when `sort` is absent
      the order is `id` ascending.
- [ ] Unparameterized `GET /notes/` returns the full collection as a bare
      JSON array of `{id, title, description}` in `id` order, identical to
      current behavior; the existing service tests pass unmodified.
- [ ] The contract is recorded in the same change: root `README.md` updated
      and (per D8) a notes-query specification under `docs/development/` with
      `index.md` updated.
- [ ] The generated OpenAPI schema reflects the new parameters.

## Execution plan

Status: Draft

Approach:
- Add FastAPI `Query` parameters to `read_all_notes` (`src/app/api/notes.py`):
  `limit` with `ge=1, le=100`, `offset` with `ge=0`, `sort` validated against
  an allow-list of the six permitted values, `q` as a plain optional string.
  Validation failures become contractual 422 responses.
- Extend `crud.get_all` (`src/app/api/crud.py`) to accept the optional
  parameters and build the SQLAlchemy select: optional
  `where(notes.c.title.ilike(...))` with `%`, `_`, and the escape character
  escaped in the user value so matching stays literal; `order_by` on the
  requested column plus `notes.c.id.asc()` as tie-break; `offset`; `limit`.
  Absent parameters leave the query unchanged, preserving current behavior.
- Keep the response a bare list — no envelope, no shape change (D1).

Tests (additions in `src/tests/`, existing tests kept unmodified):
- Seed via the public POST route, then assert:
  - unparameterized: 200, bare array, full collection, `id` ascending;
  - `limit`/`offset` windowing, including limit-absent full result;
  - `limit=101` and `limit=0` → 422; `offset=-1` → 422;
  - `sort=title` and `sort=-title` with duplicate titles → ties broken by
    ascending `id` (stability proof);
  - unknown `sort` value → 422;
  - `q` matches case-insensitively, `%`/`_` match literally, no match → `[]`;
  - combined `q` + `sort` + `limit` + `offset`.
- Verify how the fixture's `TestClient(app)` invocation connects the database
  (lifespan); if the installed Starlette does not run lifespan outside a
  context manager, adjust the fixture to a context-manager client without
  weakening the boundary.
- Assert the generated OpenAPI schema exposes the new parameters.

Environment: execution must first establish a test environment (no
virtualenv or declared test dependencies exist) and run from an isolated
working directory, because the service writes `./notes.db` relative to the
working directory.

### Implementation decisions and open questions

- Contract values (bounds, sort fields, filter semantics, response shape)
  come from parent decisions D1–D4; this subtask implements them and locks
  them with tests. Open questions: none at this scope.
- Local choices resolved here: validation via FastAPI `Query` constraints
  (contractual 422s), literal-match escaping in the CRUD layer, `sort`
  validated as an explicit allow-list.

### Documentation

- Root `README.md`: update the "returns every note as a JSON array"
  description to the current collection behavior plus the query parameters,
  in the same change as the code.
- If D8 approved: add the notes-query specification under `docs/development/`
  describing the frozen contract and update `index.md`; otherwise leave
  `docs/development/` untouched.

### Task checklist

- [ ] Implement query parameters and CRUD selection with stable ordering
- [ ] Add HTTP-boundary integration tests (new behavior and unparameterized regression)
- [ ] Update root `README.md` (and the spec per D8) in the same change
- [ ] Run the service suite; confirm existing tests pass unmodified

### Requirement verification

- Parent R1 → the integration tests listed above (windowing, bounds, sort
  directions with tie stability, literal filter matching, 422s).
- Parent R2 → unmodified existing tests plus the unparameterized regression
  test asserting bare-array shape, full collection, `id` order.
- Parent R5 → the recorded contract (README/spec) reviewed in the same change
  as the implementation; generated OpenAPI asserted to match.
- Parent R7 (service part) → README/spec diff in this change.