# Supported notes-query capability across API, client, and CLI

Add one supported way to query notes — bounded pagination, stable sorting, and
optional text filtering — consistently across the three independently
maintained components: the public FastAPI notes API (`src/app/`), the reusable
`notes_client` package (`packages/notes_client/`), and the `notes` CLI
(`apps/notes_cli/`). Existing unparameterized behavior is preserved at every
boundary, the public HTTP contract is stable before consumers build on it, and
the CLI proves the production client-to-service path end to end.

Planning only: this file records outcomes and a draft approach. No execution is
authorized yet.

## Requirements checklist

- [ ] The notes HTTP API supports querying notes with bounded pagination, stable (deterministic) sorting, and optional text filtering. Owner: `tasks/20261101-notes-query-capability/010-api-query-contract.md`
- [ ] The query contract is stable before consumers rely on it: written into maintained public docs, pinned by tests, and completed before client or CLI work starts. Owner: `tasks/20261101-notes-query-capability/010-api-query-contract.md`
- [ ] Current unparameterized behavior is preserved: `GET /notes/` without parameters still returns every note as a JSON array with today's behavior, and existing `NotesClient.list_notes()` still sends the same parameter-free request and returns the parsed JSON list. Owners: `tasks/20261101-notes-query-capability/010-api-query-contract.md` + `tasks/20261101-notes-query-capability/020-client-query-support.md`
- [ ] The reusable Python client exposes the query capability against the stable contract. Owner: `tasks/20261101-notes-query-capability/020-client-query-support.md`
- [ ] The CLI exposes the query capability, and its production client-to-service path is proven end to end: a real CLI invocation through the production `NotesClient` against a running service. Owner: `tasks/20261101-notes-query-capability/030-cli-query-command.md`
- [ ] Each component's maintained documentation describes the new supported behavior in the same change that makes it true. Owners: all three subtasks, each for its own docs.

## Subtasks

- [ ] `tasks/20261101-notes-query-capability/010-api-query-contract.md` — define, implement, document, and pin the public query contract.
- [ ] `tasks/20261101-notes-query-capability/020-client-query-support.md` — expose the query capability on `NotesClient`. Depends On: `tasks/20261101-notes-query-capability/010-api-query-contract.md`
- [ ] `tasks/20261101-notes-query-capability/030-cli-query-command.md` — expose the query capability on the CLI and prove the production path. Depends On: `tasks/20261101-notes-query-capability/010-api-query-contract.md` and `tasks/20261101-notes-query-capability/020-client-query-support.md`

Order is strict: 010 → 020 → 030. The `Depends On` declarations are the
operative constraints; filename numbering only reflects them.

## Questions and decisions

There are no unresolved requirement questions: the capability, the three
boundaries it must span, the preservation constraint, and both sequencing
constraints (contract stability, production-path proof) are fixed by the
request. The material design decisions that shape the public contract are
collected with recommendations in the plan below under
`### Implementation decisions and open questions`; they are approved together
with the plan before any subtask executes. The most consequential:

- The query surface is proposed as optional parameters on the existing
  `GET /notes/` route (not a new endpoint), keeping the bare JSON array
  response shape.
- Deterministic ordering applies only when a query parameter is used; the fully
  unparameterized request keeps today's behavior exactly, including its
  currently unspecified row ordering.

## Supporting details

**Components and boundaries.** Three separately owned deliverables, each with
its own compatibility boundary; this is why the work decomposes into three
children rather than one change:

- Public API: `src/app/` — FastAPI app with router prefix `/notes`
  (`src/app/api/notes.py`), CRUD helpers (`src/app/api/crud.py`),
  `NoteCreate`/`Note` models (`src/app/api/models.py`), SQLite via
  `databases` + SQLAlchemy core (`src/app/db.py`). `GET /notes/` returns
  `crud.get_all()` — every note, no ordering, no parameters.
- Client package: `packages/notes_client/` — own `pyproject.toml`
  (`notes-client` 0.1.0, depends on `httpx` only). `NotesClient` takes an
  injected transport; `from_environment()` uses `NOTES_API_URL` (default
  `http://127.0.0.1:8000`). `list_notes()` GETs `/notes/` and returns parsed
  JSON.
- CLI app: `apps/notes_cli/` — own `pyproject.toml` (`notes-cli`, console
  script `notes = "notes_cli.cli:main"`). `list` subcommand prints
  `{id}: {title}` per note via the client.
- Maintained docs: root `README.md` (API, currently says the collection route
  returns every note as a JSON array), per-component READMEs, and
  `docs/development/index.md`, which records that no notes-query specification
  exists.

**Definitions used by this task.**

- Bounded pagination: the requested page size is capped by a server-enforced
  maximum; requests beyond the cap are rejected.
- Stable sorting: a deterministic total order (requested sort key with unique
  `id` as final tiebreaker) so pages never skip or repeat rows across offsets.
- Optional text filtering: a consumer-supplied text term narrowing results;
  proposed as case-insensitive substring match on title or description.
- Preservation: unparameterized requests keep current behavior exactly —
  content, shape, and ordering.

**Verification shape.** One named decisive check per product connection;
per-side fakes stay supporting evidence only and do not substitute for the
connection checks.

| Product connection | Owner | Decisive check | Deliberately not covered there |
| --- | --- | --- | --- |
| Public API contract behavior | 010 | Route tests through `app.main.app` (TestClient) on a seeded temp SQLite DB | Real socket transport; consumer surfaces |
| Client ↔ service contract conformance | 020 | Real `NotesClient` over real HTTP against the running app | CLI rendering |
| CLI → client → service production path | 030 | E2E: `main([...])` with production `NotesClient.from_environment()` against a subprocess-served app; stdout asserts paging/sort/filter results | Hosted deployment; concurrency |

The 030 check is the single full-connection proof for the feature. API route
tests and the existing fake-transport/fake-client unit tests do not satisfy
the production-path requirement.

**Known harness facts, defects, and assumptions** (verified by inspection; no
test was run during planning — the environment lacks the project
dependencies):

- `DATABASE_URL` is hardcoded to `sqlite:///./notes.db`, relative to the
  process CWD. Any test that runs the real service must launch it from a
  temporary working directory for isolation.
- `src/tests/conftest.py` builds `TestClient(app)` without using it as a
  context manager, while `database.connect()` runs in the lifespan hook.
  Assumption to verify during execution: the DB may not be connected in the
  current suite; route tests should use `with TestClient(app)` or otherwise
  ensure the connection.
- Importing `app.db` materializes `./notes.db` at import time
  (`metadata.create_all`). The file is not gitignored; keep it out of commits.
- No `uvicorn` is declared anywhere in the fixture, so proving real-server
  paths requires introducing it as a dependency (see plan decision 11).
- The CLI's console script points at a `notes_cli` package directory that does
  not exist (`apps/notes_cli/` contains `cli.py` directly), and
  `apps/notes_cli/tests/test_cli.py` calls `list_command` without importing
  it — the current CLI test is defective as shipped. 030 must make the real
  CLI code importable and fix the import incidentally, reporting the fix.
- The CLI's `pyproject.toml` declares no dependency on `notes-client` despite
  importing it (see plan decision 10).
- Existing client tests use a fake transport and CLI tests a fake client;
  both are kept as unit-level regression evidence only.

## Implementation plan

Status: Draft

### Proposed query contract (binding once this plan is approved)

`GET /notes/` gains optional query parameters. Supplying none reproduces
today's behavior exactly.

| Parameter | Type / range | Default in parameterized use | Semantics |
| --- | --- | --- | --- |
| `limit` | int, 1–100 | 20 | Page size; 0, negative, or >100 → 422 |
| `offset` | int, ≥ 0 | 0 | Rows to skip |
| `sort` | one of `id`, `title`, `description`, optional leading `-` for descending | `id` ascending | Deterministic total order via `id` tiebreaker |
| `q` | string | none | Case-insensitive substring match on title or description |

- Response stays a bare JSON array of note objects (up to `limit` items);
  empty array for no matches. No envelope, no total count.
- Whenever any parameter is supplied, results are returned in the
  deterministic total order (sort key, then `id`).
- Invalid values yield FastAPI's standard 422 responses.

### Component responsibilities

- API (010): parse and validate parameters with `fastapi.Query`; translate to
  SQLAlchemy `where`/`order_by`/`offset`/`limit` in `crud` while keeping the
  unparameterized path on today's code branch. No schema changes.
- Client (020): `list_notes(limit=None, offset=None, sort=None, q=None)`
  builds the query string only from supplied values, so an unparameterized
  call sends exactly today's parameter-free request; returns the parsed JSON
  list.
- CLI (030): extend the `list` subcommand with `--limit`, `--offset`,
  `--sort`, `--query`; argparse validates ranges and choices locally so normal
  CLI use never triggers a 422; rendering unchanged; values pass through to
  the production client.

### Order logic and milestones

010 first because both other components consume its contract, and the request
requires the contract to be stable before consumers rely on it. 020 needs the
stable contract to code against and the real service to run conformance tests.
030 needs both the contract and the client method. Safe stopping points: after
010 the API is releasable on its own; after 020 the package is releasable;
after 030 the user-facing capability is complete and proven end to end.

### Risks and the way back

- All changes are additive; no SQLite schema or persisted-data changes.
  Reverting any subtask's change restores that boundary's prior behavior.
- Largest risk is drift between the documented contract and its implementation
  across three components; 020's conformance test and 030's end-to-end check
  run the real consumers against the real service, so drift fails loudly.
- Pagination without a total order silently skips or duplicates rows;
  the `id` tiebreaker plus explicit multi-page assertions address this.
- `q` case folding on SQLite is ASCII-only (`ilike` compiles to `lower()`);
  document this honestly rather than over-claiming Unicode support.
- The unparameterized path is pinned by explicit regression evidence in 010
  (exact response) and 020 (request shape).
- Harness risks: CWD-relative DB path, the TestClient lifespan question, and
  the CLI import defects listed under supporting details; each subtask's plan
  handles its own instance.

### Implementation decisions and open questions

Decisions 1–9 change the public contract or a consumer surface and are
approved with this plan; 10–12 are material maintenance choices. Each carries
a recommendation; none blocks planning, all block execution.

1. Extend the existing `GET /notes/` route with optional parameters vs. a new
   endpoint. Recommend extending: standard collection-query shape, and
   unparameterized calls are untouched by construction.
2. Bare JSON array for parameterized pages vs. an envelope with total count.
   Recommend bare array: maximally compatible with today's shape and the
   client's list return; a shorter page signals the end.
3. Deterministic ordering only for parameterized requests; strict
   preservation (including unspecified ordering) for unparameterized
   requests. Recommend strict preservation — adding an implicit `ORDER BY` to
   unparameterized responses would change current consumer-visible behavior.
4. Exact numbers: `limit` default 20, max 100; `offset` default 0. Mechanically
   any values work; confirm these as the contract numbers.
5. Sort surface: whitelist {`id`, `title`, `description`} with optional `-`
   descending prefix and `id` as final tiebreaker. Recommend as proposed.
6. Filter surface: single `q`, case-insensitive substring across title and
   description. Alternatives (title-only, exact match) rejected as less
   useful; ASCII-folding limitation documented.
7. Client surface: extend `list_notes()` with optional keyword parameters
   vs. a new `query_notes()` method. Recommend extending: signature-compatible
   for existing callers, one collection method.
8. CLI surface: extend `notes list` with flags vs. a new `query` subcommand.
   Recommend extending `list`: one user surface matching the one client
   method.
9. Scope exclusion: client HTTP error handling stays as is (no
   `raise_for_status` is added). Adding it would change the client package's
   current error-path behavior; record as a possible follow-up instead.
10. Maintenance notes: recommend bumping `notes-client` to 0.2.0 in the same
    change as 020 (additive public surface on a 0.x package), and adding
    `notes-client` to the CLI's undeclared dependencies in 030. Both are
    reported changes, not silent ones.
11. Test harness: introduce `uvicorn` (recommended: root `pyproject.toml`
    dependencies) to serve the real app in 020/030 checks. The alternative —
    `httpx.ASGITransport` — is rejected for the production-path check because
    it skips the real server and lifespan; it also needs manual
    `database.connect()` handling.
12. Documentation destination: the three maintained READMEs plus OpenAPI
    generated from route code; no new spec pages or directories
    (smallest-structure rule). A versionable spec page under `docs/` remains
    available if maintainers want one later.

### Documentation

- Root `README.md` — query contract section in the same change as 010
  (audience: API consumers).
- `packages/notes_client/README.md` — new client surface in the same change
  as 020 (audience: Python consumers).
- `apps/notes_cli/README.md` — new flags in the same change as 030 (audience:
  CLI users).
- OpenAPI is generated from route code; change the source, never the output.
- No placeholder pages; `docs/development/index.md` needs no change unless a
  spec page is approved.

### Task checklist

- [ ] `tasks/20261101-notes-query-capability/010-api-query-contract.md` — contract implemented, documented, pinned.
- [ ] `tasks/20261101-notes-query-capability/020-client-query-support.md` — client surface implemented and conformance-proven.
- [ ] `tasks/20261101-notes-query-capability/030-cli-query-command.md` — CLI surface shipped and production path proven.

### Requirement verification

- Query capability with bounded pagination, stable sorting, text filtering →
  010's route tests through the real app (bounds rejection, tiebreaker
  determinism, filtering, combined parameters). Does not cover real socket
  transport or consumer surfaces.
- Contract stability before consumers rely on it → 010's README section and
  OpenAPI parameters published in the same reviewed change, tests pinning the
  behavior, and 010 completing before 020/030 begin (dependency declarations).
  Stability here means decided, documented, and pinned — not versioned
  release management, which the fixture has no mechanism for.
- Preservation of unparameterized API and client behavior → 010's
  exact-response regression test and 020's request-shape regression test;
  all three existing suites stay green.
- Client exposes the capability against the stable contract → 020's
  conformance test running the real client over real HTTP. Does not cover CLI
  rendering.
- CLI exposes the capability and proves the production client-to-service path
  → 030's end-to-end check: real CLI invocation, production
  `NotesClient.from_environment()`, subprocess-served real app, stdout
  assertions. This is the only check that traverses all three components
  together; it deliberately does not cover hosted deployment or concurrency.
- Documentation per boundary → the changed README pages themselves, reviewed
  in the same change as the code that makes them true.

### Additional implementation verification

Running all three existing suites green after each subtask is supporting
regression evidence only; it is not the decisive evidence for any requirement
above.
