# Notes query capability across API, client, and CLI

Add one supported notes-query capability (bounded pagination, stable sorting,
optional text filtering) to the notes HTTP API, the reusable `notes_client`
package, and the `notes` CLI, without changing current unparameterized
behavior. The public HTTP contract is written and approved before the client or
CLI implementation relies on it, and the CLI is proven end-to-end over the
production client-to-service path.

Planning-only handoff: execution is not authorized yet. All plans below are
`Draft`.

## Requirements checklist

- [ ] R1: One supported notes-query capability exists on all three public
      boundaries: the notes HTTP collection operation (`GET /notes/`), the
      `NotesClient` public API, and the `notes` CLI.
- [ ] R2: The capability supports bounded pagination (page size bounded by the
      approved contract; unparameterized calls remain unbounded and unchanged).
- [ ] R3: The capability supports stable sorting (deterministic total order with
      a defined tie-break, so pages are reproducible).
- [ ] R4: The capability supports optional text filtering (no filter means no
      filtering, matching current behavior).
- [ ] R5: Current unparameterized HTTP behavior is preserved: `GET /notes/`
      with no query parameters still returns every note as a JSON array.
- [ ] R6: Current unparameterized client behavior is preserved:
      `NotesClient.list_notes()` keeps its current request (no query string)
      and its JSON-array return contract.
- [ ] R7: The public HTTP query contract is specified in maintained
      documentation and approved (stable) before any client or CLI
      implementation relies on it.
- [ ] R8: The CLI is proven end-to-end over the production path — real CLI
      code, real `notes_client.NotesClient`, live notes service over HTTP, with
      no test stubs on that path.
- [ ] R9: Maintained documentation of each affected boundary reflects the
      supported behavior in the same reviewed change that makes it true (root
      `README.md`, `packages/notes_client/README.md`,
      `apps/notes_cli/README.md`, `docs/development/index.md`).

## Subtasks

- [ ] `tasks/20260919-notes-query-capability/010-query-contract.md` —
      Stabilize the public notes-query HTTP contract (specification + docs
      index). Blocks all implementation.
- [ ] `tasks/20260919-notes-query-capability/020-api-query-capability.md` —
      Implement the query capability in the notes API (HTTP boundary).
- [ ] `tasks/20260919-notes-query-capability/030-client-query-capability.md` —
      Implement the query capability in `notes_client` (package boundary).
- [ ] `tasks/20260919-notes-query-capability/040-cli-query-capability.md` —
      Add CLI query options and prove the production client-to-service path
      (application boundary).

Sequencing: 010 first. 020 and 030 are independent once 010 is approved and may
run in parallel. 040 is last because it consumes the real service (020) and the
real client method (030) for the end-to-end proof.

## Supporting facts

Established by inspection of the current workspace (all verified):

- The collection route `read_all_notes` (`src/app/api/notes.py:8`) calls
  `crud.get_all()` (`src/app/api/crud.py:4`), which runs an unsorted,
  unfiltered `database.fetch_all(notes.select())`. There are no query
  parameters today; the response is a bare JSON array of note rows.
- `NotesClient.list_notes()` (`packages/notes_client/notes_client/client.py:20`)
  issues `GET /notes/` and returns the parsed JSON array. The HTTP transport is
  constructor-injected, and `from_environment()` builds an `httpx.Client` from
  `NOTES_API_URL` (default `http://127.0.0.1:8000`).
- The CLI (`apps/notes_cli/cli.py`) exposes only `notes list`, printing
  `id: title` per note from `client.list_notes()`.
- Current tests stub one layer up each time: CLI tests stub the client,
  client tests stub the transport, API tests use the real app via
  `TestClient`. No existing test crosses the real client-to-service path.
- Storage is SQLite through `databases` + SQLAlchemy Core
  (`src/app/db.py`); `title` and `description` are `String(50)`. SQLAlchemy
  Core supports composing `.where()`, `.order_by()`, `.limit()`, `.offset()`,
  which is sufficient for pagination, sorting, and filtering without a new
  dependency.
- `docs/development/index.md` currently records "No notes-query
  specification exists." — the contract deliverable must update this line.
- The root `pyproject.toml` declares `fastapi`, `httpx`, `sqlalchemy`, and
  `databases[sqlite]`; the workspace is a single Python environment, so all
  three components are importable together (basis for the CLI end-to-end
  proof). `uvicorn` is not currently a dependency.

Assumptions:

- All three test trees run in one interpreter/workspace configuration (as
  `src/tests` already imports `app.main` and the CLI imports `notes_client`).
  If execution discovers otherwise, the affected subtask records it.
- Fixture test data shares the on-disk SQLite file `./notes.db` (cwd-relative);
  API and end-to-end tests must tolerate pre-existing rows rather than assume
  an empty database.

## Execution plan

Status: Draft

Approach: contract-first decomposition by public boundary, following the
fixture guidance that HTTP, package, and application compatibility boundaries
justify separate deliverables (test levels alone do not).

1. `010` writes the notes-query HTTP specification and gets it approved. This
   is the stability gate required by R7; nothing downstream starts earlier.
2. `020` (HTTP API) and `030` (client package) implement the approved contract
   on their boundaries in parallel. Each preserves its unparameterized behavior
   with explicit regression evidence and updates its own maintained docs in the
   same change.
3. `040` (CLI application) adds the user-facing flags and delivers the
   end-to-end proof over the production path (R8), which is also the first
   decisive evidence that the three boundaries compose correctly.
4. The task completes when every subtask's checklist and this main checklist
   are satisfied and all three test suites pass in a full run.

Discovery rule: if implementation of 020/030/040 exposes a gap or defect in the
approved contract, the contract change flows back through 010 (which returns to
`Draft` for re-approval) rather than being improvised downstream. Consumers
never build against an informal contract.

### Implementation decisions and open questions

Material decisions that shape the public contract are recorded and asked about
in `010-query-contract.md` (`### Implementation decisions and open questions`),
because they change user-visible behavior on the HTTP boundary:

- Whether to extend the existing collection operation with optional parameters
  or add a separate query route (recommendation: extend the existing
  operation, since defaults preserve current behavior exactly).
- Pagination bound enforcement (reject out-of-bounds `limit` vs silently cap),
  sort field whitelist / direction syntax / tie-break, filter target and
  matching semantics, and response shape (recommendation: keep the bare array).

Downstream surface decisions that are user-visible on their own boundaries
(client method surface, CLI command/flag surface) are recorded with
recommendations in `030` and `040` respectively and confirmed at those plans'
approval. Resolving the HTTP contract does not by itself authorize those
surfaces; each subtask's own plan approval does.

### Documentation

- `010`: one specification page under `docs/` (placement decided there per
  `docs/development/documentation.md`) plus the `docs/development/index.md`
  status line. Audience: HTTP API consumers and the maintainers of the two
  consuming deliverables.
- `020`: root `README.md` (audience: API users).
- `030`: `packages/notes_client/README.md` (audience: Python consumers).
- `040`: `apps/notes_cli/README.md` (audience: CLI users).
- Specification pages may describe the intended target; boundary READMEs must
  only claim supported behavior in the change that implements it (020/030/040
  own those README updates, not 010).

### Task checklist

The `## Subtasks` list above is the authoritative checklist. During execution,
update it together with each subtask file's own `### Task checklist`; a
subtask counts as done only when its requirement evidence exists, not merely
when its implementation code exists.

### Requirement verification

- R1: verified at completion by the union of boundary evidence — 020 API
  tests, 030 client tests, 040 CLI tests. No separate test; recorded when all
  three subtasks close.
- R2–R4: decisive at the HTTP boundary (020 tests through `test_app` over the
  real app and SQLite); 030 recording-transport tests prove the client forwards
  the parameters; 040 proves the composed behavior once end-to-end.
- R5: 020's unparameterized regression test at the HTTP boundary.
- R6: 030's regression test proving the no-argument call issues the identical
  request as current code (no query string).
- R7: 010's recorded approval of the specification plus the dependency
  ordering (030/040 declare `Depends On` 010 and must not start before it
  closes).
- R8: 040's end-to-end test over a live service with the real client — the
  decisive evidence; stub-based unit tests count only as supporting.
- R9: reviewed documentation diffs in each boundary's change set (010, 020,
  030, 040 respectively).

### Additional implementation verification

- Full regression run across all three suites (`src/tests`,
  `packages/notes_client/tests`, `apps/notes_cli/tests`) at 040 completion;
  existing tests must pass unmodified.
- Shared on-disk SQLite (`./notes.db`) is a real cross-test coupling risk:
  020's tests assert relative order/content of seeded notes, and 040's
  end-to-end server should isolate its database (e.g. run the server process
  with a temporary working directory) rather than mutate shared state.