# Implement API query parameters for the notes collection

Extend `GET /notes/` with the optional, bounded query contract and pin it
with integration tests through the real ASGI app and SQLite, preserving
today's unparameterized behavior exactly.

Parent Task: tasks/20260925-notes-query-capability/000-main.md
Depends On: tasks/20260925-notes-query-capability/010-public-query-contract.md

## Requirements checklist

- [ ] `GET /notes/` accepts optional `limit` (integer 1–100), `offset`
  (integer >= 0), `sort` (`id` | `title`), `order` (`asc` | `desc`), and
  `text`, per the approved contract.
- [ ] Out-of-contract values (limit outside 1–100, negative offset, unknown
  sort or order) are rejected with 422.
- [ ] Whenever any parameter is present, the response is in a deterministic
  total order: explicit `sort` with an `id` tiebreak, or `id` ascending by
  default; sequential pages are stable and disjoint.
- [ ] `text` filters case-insensitively across `title` and `description`.
- [ ] A request with no query parameters returns exactly today's response:
  full collection, JSON array, no ordering change.
- [ ] The contract is pinned by tests through the real ASGI app and SQLite
  (existing `test_app` fixture), including a regression test for the
  unparameterized behavior.
- [ ] Root `README.md` documents the query capability and the spec's
  `Not implemented` marker is removed, both in the same change.

## Supporting facts

- Current handler: src/app/api/notes.py:8 `read_all_notes()` →
  `crud.get_all()` (src/app/api/crud.py:4), issuing an unmodified
  `notes.select()`.
- Existing tests (src/tests/test_notes.py) cover the unparameterized 200 +
  list response and the POST route; they must keep passing unchanged.
- Storage uses `databases` + SQLAlchemy Core over SQLite; the query is
  composed with Core constructs (`where` + `or_`/`ilike`, `order_by`,
  `offset`/`limit`).
- SQLite `LIKE` is case-insensitive for ASCII by default; the filter
  behavior should be asserted by test rather than assumed.

## Execution plan

Status: Draft

- Extend `read_all_notes` with optional `Query` parameters carrying the
  bounds and choices, so FastAPI produces the 422 behavior without custom
  error handling.
- Extend `crud.get_all` with optional arguments; when all are absent the
  issued query is exactly today's `notes.select()`, so the unparameterized
  path is provably unchanged; otherwise compose filter/order/offset/limit
  with the `id` tiebreak.
- Extend `src/tests/test_notes.py`: one case per parameter, a combined
  case, each 422 case, cross-page stability, filter matching, and the
  unparameterized regression; seed data through the existing POST route.
- Update the root README and flip the spec status marker.

### Implementation decisions and open questions

None beyond the approved contract; internal composition of the SQL
conditions and the exact SQLAlchemy expression forms are local, reversible
implementation choices.

### Documentation

Root `README.md` (API users) and the spec status marker, both inside this
change so the public claim ships with the behavior that makes it true.

### Task checklist

- [ ] Add query parameters + validation to the route
- [ ] Extend `crud.get_all` with the query composition
- [ ] Add integration/contract tests including the unparameterized
  regression
- [ ] Update root README and spec status marker

### Requirement verification

- Decisive: new tests in `src/tests` drive the real app via `TestClient`
  over real SQLite — paging windows, sort asc/desc with tiebreak, text
  filter, each 422 case, and the unparameterized full-collection response.
- Regression: existing `src/tests/test_notes.py` tests pass unchanged.
- Run: the `src/tests` suite collects and exits cleanly.

### Additional implementation verification

- Page stability across two sequential requests with the same sort
  (windows disjoint and contiguous) — guards the "stable sorting"
  requirement beyond single-page assertions.