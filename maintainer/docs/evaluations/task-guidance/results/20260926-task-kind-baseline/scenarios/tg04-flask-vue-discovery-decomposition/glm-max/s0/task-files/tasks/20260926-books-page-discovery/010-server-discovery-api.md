# Server discovery API (read filter, search, bounded pagination)

Extend GET `/books` with optional read-status filtering, title/author search,
and bounded pagination through the `server/query.py` selection seam, while the
paramless response stays byte-compatible and CRUD routes keep their semantics.
The API contract is independently usable by API consumers and carries its own
HTTP-boundary evidence.

Parent Task: tasks/20260926-books-page-discovery/000-main.md

Depends On: (none)

## Requirements checklist

- [ ] S1 — GET `/books` accepts optional discovery params per the parent plan
      contract (D1): `read` (`true`/`false`; absent = all), `q`
      (case-insensitive substring matching title OR author), `page` (1-based
      positive integer). Requests using any discovery param return the current
      envelope plus pagination metadata (`page`, `page_size`, `total`,
      `total_pages`) with the selected rows (D2).
- [ ] S2 — A paramless GET `/books` returns the current exact envelope with
      the full list (R9).
- [ ] S3 — POST `/books`, PUT `/books/<id>`, DELETE `/books/<id>` semantics
      are unchanged (R8), and created/updated/deleted books are visible to
      subsequent discovery queries.
- [ ] S4 — Selection logic lives in `server/query.py` and is wired into the
      GET route (data-selection seam ownership); no duplicated selection logic
      in `app.py`.
- [ ] S5 — HTTP tests cover: paramless compatibility, read filtering, `q`
      matching on title and author with case-insensitivity and a no-match
      case, combined filter+search, pagination pages/totals/out-of-range,
      validation behavior (per D4), CRUD regression, and CRUD→discovery
      interplay.

## Execution plan

Status: Draft

Design: `server/app.py` reads `request.args` on GET and delegates selection to
`server/query.py`, which returns rows plus metadata given `(books, params)`.
When no discovery param is present the route returns the current body
unchanged; otherwise it returns the envelope with metadata. Page size is a
fixed server constant (10, per D1). `BOOKS` remains module-level in-memory
state; CRUD routes are untouched.

Steps:

1. Establish the baseline: install runtime dependencies and confirm the
   existing pytest suite passes.
2. Implement selection in `server/query.py`: read filter, case-insensitive
   substring search on title or author, pagination with `total` /
   `total_pages`, and validation per D4 (malformed `read`/`page` → 400 raised
   for the route to return; out-of-range `page` → empty rows with correct
   metadata).
3. Wire GET `/books`: paramless → unchanged body; any discovery param →
   paginated envelope. CRUD routes untouched.
4. Tests: add deterministic seeding/reset of `BOOKS` per test (module-level
   state is shared) and extend `tests/test_books_api.py` per S5.
5. Docs: add the API-contract section (params, envelope, compatibility rule)
   to `docs/development/index.md`, replacing the "No book-discovery
   specification exists." line.

### Implementation decisions and open questions

- Contract values (param names, envelope keys, page size 10, validation
  policy) restate parent decisions D1–D4 and inherit their pending-approval
  status; no child-local contract changes are introduced.
- Test seeding mechanism (autouse reset fixture vs. unique ids per test) is a
  local, reversible implementation choice resolved at implementation time.

### Documentation

- Add the API contract section to `docs/development/index.md` in the same
  change as the params, per the parent plan's `### Documentation` section.

### Task checklist

- [ ] Baseline: dependencies installed; existing pytest suite passes.
- [ ] `server/query.py` selection implemented (filter, search, pagination,
      validation).
- [ ] GET `/books` wired; paramless response byte-compatible; CRUD routes
      untouched.
- [ ] `tests/test_books_api.py` extended per S5; full suite passes.
- [ ] `docs/development/index.md` API contract section added.

### Requirement verification

- S1 → decisive: pytest cases through the Flask test client asserting
  filtered rows plus metadata for `read`, `q` (title, author,
  case-insensitivity, no match), combined filter+search, and pagination
  totals/out-of-range. The test client crosses real routing and selection.
- S2 → decisive: pytest asserting the paramless GET body equals the current
  envelope with the full list.
- S3 → decisive: retained/extended HTTP CRUD tests plus a case showing POST
  then a filtered GET returns the new book under the matching view.
- S4 → verified by review: the route delegates selection to
  `server/query.py`.
- S5 → satisfied by the test task above; the suite collects and exits
  cleanly with no skipped tests.

### Additional implementation verification

- Manual curl smoke against the running server (outside the Flask test
  client) comparing the paramless and filtered envelopes, with the exact
  commands recorded in Implementation Notes.