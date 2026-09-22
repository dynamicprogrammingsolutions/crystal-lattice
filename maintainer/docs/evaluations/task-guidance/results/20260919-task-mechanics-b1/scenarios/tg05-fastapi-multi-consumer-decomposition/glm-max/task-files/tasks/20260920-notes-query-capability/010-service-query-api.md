# Service: notes query on the public HTTP API

Implement the frozen notes-query contract on the existing `GET /notes/`
collection route — bounded pagination, stable sorting, optional text filtering —
without changing unparameterized behavior, and publish the contract
specification in the same change so consumers can rely on a stable, documented
contract.

Parent Task: tasks/20260920-notes-query-capability/000-main.md

Depends On: none (this is the contract-first subtask; `020` and `030` depend on
this one).

## Requirements checklist

- [ ] `GET /notes/` accepts optional query parameters implementing the contract
      decided in the parent plan (decisions 1–8): `limit` bounded by a
      server-enforced maximum, `offset >= 0`, `sort` restricted to `id`,
      `title`, `description`, `order` restricted to `asc`/`desc`, and optional
      `q` text filtering; violations return `422`.
- [ ] Any parameterized request returns deterministically ordered results
      (chosen field + direction, `id` ascending tiebreaker), so pages are
      stable with no gaps or overlaps.
- [ ] Unparameterized `GET /notes/` behaves exactly as today: `200`, every
      note, bare JSON array, no added default ordering or page size.
- [ ] The contract is documented in a maintained specification page under
      `docs/` matching the implemented behavior, and `docs/development/index.md`
      no longer says the specification is missing.
- [ ] Root `README.md` describes the supported query capability alongside the
      existing collection behavior.
- [ ] Evidence is collected through the public HTTP route against the real app
      and storage: pagination bounds and windows, sort stability with tie
      collisions, filter semantics, validation errors, and unparameterized
      equivalence.

## Supporting details

Current behavior (facts from inspection):

- `src/app/api/notes.py:8` — `read_all_notes()` returns `crud.get_all()`; no
  parameters accepted today. Router mounted at `/notes` (`src/app/main.py:15`).
- `src/app/api/crud.py:4` — `get_all()` runs a bare `notes.select()`.
- Storage: SQLite via `databases`; columns `id` (int PK), `title` (str 50),
  `description` (str 50) (`src/app/db.py:11`).
- Existing tests (`src/tests/test_notes.py`) assert the unparameterized
  collection returns a list and that POST works; both must stay green
  unchanged.
- `docs/development/index.md` states "No notes-query specification exists."
- SQLite `LIKE` is case-insensitive for ASCII only — this must be documented
  in the `q` semantics rather than hidden.

Assumed contract (from approved parent plan; freeze exactly this in the spec):

- Parameters: `limit` (1..LIMIT_MAX, recommended 100), `offset` (>= 0, default
  0), `sort` (`id` | `title` | `description`), `order` (`asc` default | `desc`),
  `q` (case-insensitive substring over `title` or `description`).
- Absent `limit` → every matching note (preserves current behavior); bounds
  apply only when `limit` is supplied.
- Ordering applies whenever any query parameter is present: `ORDER BY
  <sort> <order>, id ASC` (default sort `id`, default order `asc`).
- Unparameterized requests: no ordering guarantee added, exact current path.
- Response: bare JSON array of `{id, title, description}` in all cases.
- Invalid values → `422` (FastAPI validation).

Known risk: `src/app/db.py` hardcodes `sqlite:///./notes.db`, so service tests
share one database file. Tests needing controlled data should seed via the
public POST route and use unique payloads (or clean up) rather than touching
the schema.

## Execution plan

Status: Draft

Extend the collection route handler with `fastapi.Query` parameters carrying
the validation constraints (`ge`/`le` bounds, allowed value sets), and push the
actual filtering/sorting/paging into `crud` as a query builder over the
existing SQLAlchemy table: `WHERE` clauses from `q`, `ORDER BY <sort> <dir>,
id ASC` applied whenever any parameter is present, `LIMIT`/`OFFSET` from
`limit`/`offset`. No schema or CRUD-route changes. Author `docs/notes-query.md`
to state the contract exactly as implemented (parameters, defaults, bounds,
error behavior, ordering guarantee, unparameterized preservation, response
shape), update `docs/development/index.md` and root `README.md` in the same
change, and cover everything with route-level integration tests.

### Implementation decisions and open questions

None local to this subtask — all contract decisions were made and approved at
the parent level (parent plan decisions 1–8). Two local, reversible
implementation choices are resolved here: the page-size constant lives in the
service module as `LIMIT_MAX` (single source for code and spec), and the
`ORDER BY` clause is applied when at least one query parameter is present.

### Documentation

- New `docs/notes-query.md`: the stable HTTP contract for the notes collection
  query. Audience: HTTP API consumers — client maintainers, CLI users, direct
  API users. Must state parameters, bounds, defaults, ordering and tiebreaker
  guarantee, `q` semantics (including the ASCII case-folding caveat), `422`
  behavior, and the preserved unparameterized behavior.
- `docs/development/index.md`: replace "No notes-query specification exists."
  with a pointer to `docs/notes-query.md`.
- Root `README.md`: extend the collection description with the supported
  query capability; keep the unparameterized behavior statement true.

### Task checklist

- [ ] Add query parameters and validation to `read_all_notes`
      (`src/app/api/notes.py`).
- [ ] Extend `crud` with the query builder (filter, ordered select, paging)
      (`src/app/api/crud.py`).
- [ ] Define `LIMIT_MAX` and wire bounds.
- [ ] Write `docs/notes-query.md`; update `docs/development/index.md` and root
      `README.md`.
- [ ] Add integration tests: pagination window + bounds rejection; sort
      stability with duplicate sort-key values (seeded shuffled, ties broken
      by `id`); filter match/no-match/empty; combined parameters; `422` cases;
      unparameterized equivalence with seeded data.
- [ ] Run the service test suite and confirm existing tests pass unchanged.

### Requirement verification

- Bounded pagination: seeded multi-page dataset; `?limit=2&offset=2` returns
  exactly the third/fourth items of the deterministic order; `?limit=0`,
  `?limit=<LIMIT_MAX+1>`, `?offset=-1` → `422`; absent `limit` returns all
  matching notes.
- Stable sorting: seed titles with duplicates in shuffled insertion order;
  `?sort=title&order=desc` → titles descending, ties ordered by `id`
  ascending; the union of consecutive pages equals the full sorted list with
  no overlap — proves cross-page stability.
- Optional text filtering: seeded matching and non-matching notes; `?q=` hit
  in title, hit in description, case-insensitive match, no-match → empty array,
  absent/empty `q` → unfiltered.
- Unparameterized preservation: seeded notes; bare `GET /notes/` returns `200`
  and exactly the created notes as a bare array; existing
  `src/tests/test_notes.py` runs green unchanged.
- Contract/implementation agreement: spec text reviewed against the pinned
  tests in the same change (tests assert the documented LIMIT_MAX, defaults,
  and error status, so drift is caught).

### Additional implementation verification

- SQLite `LIKE` ASCII caveat: if non-ASCII seed data is used in filter tests,
  assert and document only the guaranteed ASCII behavior; do not silently
  promise Unicode case-insensitivity the storage layer does not provide.