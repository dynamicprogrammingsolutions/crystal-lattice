# Notes query capability across API, client, and CLI

Add one supported notes-query capability end to end. The public HTTP API, the
reusable `notes_client` package, and the `notes` CLI each expose bounded
pagination, stable sorting, and optional text filtering for the notes
collection, while current unparameterized API and client behavior is preserved.

## Requirements checklist

- [ ] The notes-query public HTTP contract (bounded pagination, stable sorting,
      optional text filtering) is defined, documented, and stable before the
      client package or CLI relies on it. (Owner: 010)
- [ ] The service implements the approved contract: optional pagination
      parameters with an enforced maximum page size, deterministic stable
      ordering, optional case-insensitive text filtering, and validation that
      rejects out-of-contract input. (Owner: 010)
- [ ] Current unparameterized API behavior is preserved: `GET /notes/` without
      query parameters returns the full JSON array exactly as it does today.
      (Owner: 010)
- [ ] `notes_client` exposes the query capability while current zero-argument
      `NotesClient.list_notes()` behavior is preserved (unparameterized
      request, unchanged return type). (Owner: 020)
- [ ] The CLI exposes the query capability while current flagless `notes list`
      output behavior is preserved. (Owner: 030)
- [ ] The CLI deliverable's acceptance evidence proves the production
      client-to-service path end to end: real CLI entry point → real
      `notes_client` → real running notes service → SQLite. One named decisive
      check traverses the real components together; stub-based tests do not
      satisfy this requirement. (Owner: 030)
- [ ] Maintained documentation carries each boundary's new public claims in the
      same change that makes them true. (Owners: 010, 020, 030)

## Subtasks

- [ ] tasks/20261029-notes-query-capability/010-service-query-endpoint.md
- [ ] tasks/20261029-notes-query-capability/020-client-query-support.md
- [ ] tasks/20261029-notes-query-capability/030-cli-query-command.md

Execution order is 010 → 020 → 030; dependencies are declared in the subtask
files. Ordering is what enforces "contract stable before consumers rely on it":
020 must not start before 010 has published the contract, and 030 must not
start before 020 is complete.

## Open decisions (require approval before execution)

These change the public contract and are pending user approval. Recommended
resolutions are recorded; the plan stays `Draft` until they are approved.

1. **Parameterized response shape.** Recommended: the collection route keeps
   returning a bare JSON array of note objects for parameterized requests too
   (item shape unchanged; no envelope, no total count). Alternative: an
   envelope (`{"items": [...], "total": n}`) for parameterized requests, which
   changes the response type consumers must handle and the client return type.
   The request does not require a total count, so the array is recommended.
2. **Query contract details.** Recommended package (all one approval):
   - Parameters on the existing `GET /notes/` route: `limit` (integer 1..100;
     100 is the enforced maximum page size), `offset` (integer ≥ 0, default 0),
     `sort` (one of `id`, `-id`, `title`, `-title`, `description`,
     `-description`), `q` (case-insensitive substring match against `title` or
     `description`).
   - Out-of-contract values (`limit` outside 1..100, negative `offset`,
     unknown `sort` value) are rejected with HTTP 422, not silently clamped.
   - Any request that supplies at least one query parameter is ordered: default
     `sort=id` ascending, with `id` ascending always applied as the final
     tiebreaker so equal sort keys have a deterministic order.
   - A request with no query parameters at all keeps the legacy code path
     exactly, so current behavior is provably preserved rather than merely
     equivalent.
3. **Client surface.** Recommended: extend `NotesClient.list_notes()` with
   keyword-only optional parameters (`limit`, `offset`, `sort`, `q`), defaulting
   to `None`; an all-`None` call sends the unparameterized request exactly as
   today. Alternative: a new `query_notes()` method, leaving `list_notes()`
   untouched entirely.
4. **CLI flags.** Recommended: `notes list --limit N --offset N --sort FIELD
   --filter TEXT`, where `--filter` maps to the contract's `q` parameter;
   flagless invocation is byte-for-byte today's output.

## Supporting details

Facts about the current state (verified by inspection):

- Service: `GET /notes/` is unparameterized (`src/app/api/notes.py:8`) and
  returns `crud.get_all()`, a plain `notes.select()` with no ordering
  (`src/app/api/crud.py:4`). Note shape is `{id, title, description}`
  (`src/app/api/models.py`). Storage is SQLite via `databases`/SQLAlchemy
  (`src/app/db.py`); the DB is a real file `./notes.db` created at import.
- Service tests (`src/tests/test_notes.py`) use `TestClient(app)` against that
  shared file DB and do not assert specific collection contents; new
  exact-content assertions will need controlled seeding/cleanup.
- Client: `NotesClient` takes an injected transport; `list_notes()` returns
  `self.transport.get("/notes/").json()`
  (`packages/notes_client/notes_client/client.py:21`). `from_environment()`
  honors `NOTES_API_URL`. Client tests use a stub transport returning `[]`.
- CLI: console script `notes = "notes_cli.cli:main"` (`apps/notes_cli/pyproject.toml`).
  `list_command` prints `{id}: {title}` per note. CLI tests use a stub client.
- Documentation: root `README.md` states the collection route "currently
  returns every note as a JSON array"; `packages/notes_client/README.md` and
  `apps/notes_cli/README.md` each describe their surface;
  `docs/development/index.md` states "No notes-query specification exists."
- No notes-query specification, pagination, sorting, or filtering exists
  anywhere in the repo today.

## Execution plan

Status: Draft

### Design

The capability crosses three compatibility boundaries that are independently
maintained (separate `pyproject.toml`, separate versioning, separate
consumers), so the work is decomposed by boundary, not by file or test level:

- **Service (010)** owns the public HTTP contract. It decides, documents, and
  implements the query semantics, and publishes the notes-query specification
  before any consumer builds on it. Implementation is additive to the existing
  collection route: optional query parameters on `GET /notes/`, with the
  unparameterized request handled by the untouched legacy path
  (`crud.get_all()`). Parameterized requests use a separate query path in the
  CRUD layer that applies filter → order (with `id` tiebreaker) → offset/limit
  on the server side via SQLAlchemy, so bounds and stability are enforced by
  the service and cannot be bypassed by clients.
- **Client (020)** owns the package API boundary. It serializes the approved
  contract into the URL query string and preserves the zero-argument request
  byte-for-byte. Its unit of proof is the query-string mapping; the full
  client-to-service behavior is decisively proven once, by 030's end-to-end
  check, using the real package — no duplicate live-server harness in 020.
- **CLI (030)** owns the application boundary and the one decisive production
  -path check. Flagless invocation keeps today's behavior; flags map to client
  parameters. The decisive check launches the real app under a real server,
  seeds it over HTTP, and runs the real CLI entry point as a subprocess with
  `NOTES_API_URL` pointing at it, asserting the query output through the full
  CLI → `notes_client` → HTTP → FastAPI → SQLite chain.

Data flow: CLI flags → client keyword arguments → URL query string → FastAPI
validation (422 on out-of-contract values) → CRUD query (filter, stable order,
offset/limit) → SQLite → JSON array → decoded by client → rendered by CLI.

Compatibility states: before 010, the contract does not exist and no consumer
may rely on it; after 010, the contract is published and pinned by tests — any
later contract change is a material change requiring plan re-approval; 020 and
030 preserve their existing no-argument surfaces exactly.

Verification strategy: each boundary is proven at its own public interface —
service behavior through the real app (TestClient exercises routing,
validation, CRUD, and the real SQLite storage; this is the least expensive test
that crosses the HTTP contract boundary without bypassing the app), client
mapping through a stub transport at the package boundary, CLI parsing/rendering
through a stub client at the application boundary, and exactly one end-to-end
test for the production client-to-service path, which the request explicitly
requires the CLI to prove. Stubs are evidence only for the local mapping and
rendering they own; the production path is never proven with a stub.

### Implementation decisions and open questions

Resolved as local, reversible implementation choices (recorded so executors do
not re-litigate):

- Pagination scheme is offset/limit, not cursor-based; the fixture has no
  cursors and the requirement asks only for bounded pagination.
- Bounds are enforced with 422 rejections, not silent clamping (included in
  contract approval item 2 above because it is publicly observable).
- 010's evidence uses `TestClient` (real app, real SQLite); a live network
  listener is required only for 030's decisive check.
- 030's decisive check needs a real ASGI server; uvicorn is added as a
  test-only dependency where the end-to-end test lives. The check prefers the
  installed `notes` console script; if the package is not installed in a given
  environment, it invokes `notes_cli.cli:main` directly — in either case with
  the real client and a real server, never a stub.
- New exact-content service tests seed and clean the notes table (or use an
  isolated DB) so they do not corrupt the shared `./notes.db` state that the
  existing regression test depends on.
- Test harnesses (`src/tests/conftest.py`, client stub transport, CLI stub
  client) are treated as maintained test infrastructure and extended through
  real consumers (the new tests).

Open (pending user approval — see "Open decisions" above): response shape for
parameterized requests; the query contract parameter package (names, maximum
page size, sortable fields, filter semantics, default ordering, legacy-path
rule); client surface choice (extended `list_notes()` vs new method); CLI flag
names. Nothing here may be executed until these are approved.

### Documentation

All in the same change as the behavior that makes the claims true:

- 010: new specification `docs/development/notes-query.md` (audience:
  HTTP-contract consumers — client, CLI, external integrators), linked from
  `docs/development/index.md` (which currently records that no such
  specification exists); root `README.md` collection-route sentence updated.
  `docs/development/documentation.md` guidance was read before planning this
  structure; one specification page plus README updates is the smallest
  structure that serves the intended reader — no placeholder pages.
- 020: `packages/notes_client/README.md` documents the new parameters and the
  zero-argument guarantee (audience: package consumers).
- 030: `apps/notes_cli/README.md` documents the new flags and flagless
  behavior (audience: CLI users).

### Task checklist

- [ ] tasks/20261029-notes-query-capability/010-service-query-endpoint.md —
      implement approved contract, service tests, publish specification.
      Completes before 020 starts.
- [ ] tasks/20261029-notes-query-capability/020-client-query-support.md —
      client parameters, mapping tests, README. Depends On 010.
- [ ] tasks/20261029-notes-query-capability/030-cli-query-command.md — CLI
      flags, component tests, decisive end-to-end production-path check,
      README. Depends On 020 (and transitively 010).
- [ ] Final cross-boundary run: execute all three test suites together
      (`pytest src/tests packages/notes_client/tests apps/notes_cli/tests`);
      each collects and exits cleanly; confirm the contract is unchanged since
      its publication in 010.

### Requirement verification

- Contract defined, documented, and stable before consumers rely on it →
  evidence: the published `docs/development/notes-query.md` plus linked index
  and README from 010, combined with the declared dependencies (020 Depends On
  010; 030 Depends On 020) and the re-approval rule for post-publication
  contract changes. Process evidence, not automatable.
- Service contract behavior (bounds, 422s, stable ordering with `id`
  tiebreaker under duplicate keys, case-insensitive filter over title and
  description) → service integration tests through `TestClient` against the
  real app and real SQLite: the public HTTP boundary with real storage.
- Unparameterized API preservation → regression tests asserting a seeded
  collection returns the full array via the legacy path; existing
  `test_read_all_notes` keeps passing.
- Client zero-argument preservation and parameter mapping → component tests
  with a stub transport asserting the zero-argument call sends `/notes/` with
  no query string and that each keyword maps to the contract's query string;
  decoded payload passthrough unchanged. (Full client-to-service behavior is
  decisively covered by 030's check, not duplicated here.)
- CLI flagless preservation, parsing, and rendering → component tests with a
  stub client asserting flagless output is unchanged and flags reach the
  client correctly.
- Production client-to-service path → the single decisive check owned by 030:
  real server running the real app on an ephemeral port, seeded over HTTP, real
  CLI entry point as a subprocess with `NOTES_API_URL` set, asserting query
  output (pagination + sort + filter in one realistic invocation). Stubbed
  client/transport tests are explicitly not evidence for this requirement.
- Documentation currency → reviewed in the same change per boundary; each
  boundary's README/spec claim only what its tests prove.

### Additional implementation verification

- Run all three suites together at the end (cross-boundary task above) —
  catches cross-package drift beyond per-subtask runs.
- Manual smoke of the documented exact invocation
  (`NOTES_API_URL=... notes list --limit ... --sort ... --filter ...`) against
  a locally started service, confirming the documented behavior matches
  observed behavior — supports the docs-currency requirement.
