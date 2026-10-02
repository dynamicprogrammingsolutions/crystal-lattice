# Implement the notes-query capability in the notes API

Extend the notes collection operation in `src/app` to support the approved
HTTP contract from `010` — bounded pagination, stable sorting, optional text
filtering — while preserving unparameterized behavior, with regression and
capability evidence at the public HTTP boundary and the root README updated in
the same change.

Parent Task: `tasks/20260919-notes-query-capability/000-main.md`

Depends On: `tasks/20260919-notes-query-capability/010-query-contract.md`
(the approved contract is the authority for every parameter, bound, and
default below; do not start before C3 in 010 is recorded).

## Requirements checklist

- [ ] A1: The collection operation accepts the contract's optional query
      parameters and implements bounded pagination, stable sorting, and
      optional text filtering exactly as specified (parameter names, bounds,
      whitelist, matching semantics, response shape).
- [ ] A2: Unparameterized `GET /notes/` behavior is preserved: every note,
      bare JSON array, no sorting or filtering or page cap — proven by a
      regression test, not by assertion.
- [ ] A3: Invalid parameters are rejected per the contract (expected 422 for
      out-of-bounds or unknown values as specified in 010).
- [ ] A4: The root `README.md` describes the collection route's query
      capability as current supported behavior, updated in the same reviewed
      change as the code that makes it true.

## Supporting facts

- Current code: `read_all_notes` (`src/app/api/notes.py:8`) →
  `crud.get_all` (`src/app/api/crud.py:4`) →
  `database.fetch_all(notes.select())`. Implementation point: extend the crud
  function (or add a query function it delegates to) to compose
  `.where()`, `.order_by()`, `.limit()`, `.offset()` on the SQLAlchemy Core
  select; no new dependency.
- "Absent" vs "default" matters: parameters must be declared with `None`
  defaults so that FastAPI distinguishes "not provided" (legacy path, nothing
  applied) from "provided" (contract path). A non-`None` default for `limit`
  would silently change unparameterized behavior and break A2/R5.
- Existing test fixture: `src/tests/conftest.py` provides `test_app`
  (`TestClient(app)`), which runs the real FastAPI app including lifespan
  (real `databases` connection) against SQLite — the right boundary for A1–A3
  evidence, since routing, validation, and SQL all interact.
- The tests share the on-disk SQLite file `./notes.db` (cwd-relative, created
  at import in `src/app/db.py`); existing tests already insert rows and the
  database is not reset per test. New tests must seed identifiable notes and
  assert relative order/content, never assume an empty or exclusively-owned
  table.
- Sorting/filtering interact with pagination correctness: offset paging must
  be composed with the same filter and sort in every page request — this is
  what makes "stable sorting" observable, so the tests should page through a
  seeded set and assert no overlap/gap.

## Execution plan

Status: Draft

1. Extend the crud layer with the query composition (filter → sort →
   limit/offset order per the approved contract), keeping `get_all`'s
   unparameterized call path intact.
2. Extend `read_all_notes` with the contract's optional `Query` parameters,
   `None` defaults, and the contract's validation constraints (A1, A3).
3. Add tests to `src/tests/test_notes.py`:
   - Unparameterized regression (A2): seed notes, assert the full seeded set
     is returned as a bare list.
   - Pagination (R2): page through a seeded set with `limit`/`offset`,
     assert correct windowing including a final partial page; assert the
     contract's bound rejection (e.g. oversized `limit` → 422).
   - Sorting (R3): seed notes whose insertion order differs from sort order;
     assert deterministic ordering and the tie-break.
   - Filtering (R4): matching and non-matching `q` values; absence means all.
   - A combined pagination+sort+filter query paged end-to-end without
     overlap/gap.
   All tests tolerate pre-existing rows (relative assertions only).
4. Update the root `README.md` collection-route description (A4) in the same
   change as the code.
5. Run the `src/tests` suite; existing tests must pass unmodified.

### Implementation decisions and open questions

- Contract-resolved values (parameter names, bounds, whitelist, matching,
  response shape) come from the approved 010 specification and are not
  re-decided here. If execution exposes a gap or defect in the contract, stop
  and route the change back through 010 for re-approval; do not improvise
  contract behavior in the API.
- Local, reversible choices (function shape in `crud.py`, exact test
  seeding, fixture reuse) are resolved during implementation without further
  approval.

### Documentation

- Root `README.md` (audience: HTTP API users): describe the query capability
  as supported behavior with a brief parameter summary, replacing/extends the
  current sentence "The collection route currently returns every note as a
  JSON array" only in the change where that becomes true.

### Task checklist

- [ ] Crud + router changes implemented per the approved contract
- [ ] API tests added (pagination + bounds, sort, filter, combined, and the
      unparameterized regression)
- [ ] Root `README.md` updated in the same change
- [ ] `src/tests` suite passes, existing tests unmodified

### Requirement verification

- A1: new API tests through `test_app` — the public HTTP boundary, crossing
  real routing, validation, and SQLite storage. This is decisive evidence for
  R2–R4 on the service side; no mock substitutes for the app or database.
- A2: the unparameterized regression test at the same boundary (R5).
- A3: 422 assertions for each rejected-parameter case in the contract.
- A4: the README diff reviewed in the same change as the code.
- This subtask does not prove client or CLI behavior; that evidence belongs
  to 030 and 040.

### Additional implementation verification

- Full `src/tests` run, confirming the two existing tests still pass
  unmodified (regression protection beyond the new targeted tests).
- Confirm no change to `src/app/main.py` route registration or to the note
  create/read/update/delete behavior (out of scope; untouched).