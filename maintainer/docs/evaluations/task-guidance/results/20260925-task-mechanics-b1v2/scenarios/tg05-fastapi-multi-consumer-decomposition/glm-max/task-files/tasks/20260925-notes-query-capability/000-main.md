# Notes query capability across API, client, and CLI

Add one supported notes-query capability — bounded pagination, stable
sorting, and optional text filtering — through the public HTTP API, the
reusable `notes_client` package, and the `notes` CLI, behind a single public
contract that is specified and pinned before consumers rely on it.

## Requirements checklist

- [ ] `GET /notes/` supports the query contract (bounded pagination, stable
  sorting, optional text filtering) while requests without query parameters
  behave exactly as today (full collection, JSON array, unchanged ordering).
- [ ] `NotesClient.list_notes()` supports the same contract through optional
  keyword arguments; the no-argument call keeps its current request and
  behavior.
- [ ] `notes list` supports the same contract through CLI flags; the
  unparameterized `notes list` keeps its current output and behavior.
- [ ] Pagination is bounded: the server enforces a maximum page size and
  rejects out-of-bounds values; paging is deterministic across sequential
  requests.
- [ ] Sorting is stable: whenever the query parameters are in use, responses
  are in a deterministic total order (explicit sort with an id tiebreak, or
  id order by default) so pages are stable and disjoint.
- [ ] Text filtering is optional and matches case-insensitively against note
  title and description.
- [ ] The public contract is written down in a maintained specification and
  pinned by API tests before the client and CLI subtasks rely on it.
- [ ] The CLI capability is proven by an automated end-to-end check through
  the production path: real CLI invocation → real `notes_client` (real httpx
  transport) → real running service, with no mocked client or transport in
  that check.
- [ ] Maintained documentation is updated in the same changes as the
  behavior it describes: root `README.md`,
  `packages/notes_client/README.md`, `apps/notes_cli/README.md`, and
  `docs/development/index.md`.
- [ ] Existing API, client, and CLI tests covering preserved behavior still
  pass.

## Scope

In: one shared query capability mirrored on the three public surfaces; the
contract specification; per-boundary implementation with focused evidence;
one decisive production-path end-to-end test from the CLI; documentation
updates in the owning changes.

Out: cursor-based pagination, response-envelope or metadata changes, new
authentication, filtering by fields other than title/description,
restructuring documentation beyond one specification page, and changes to
write routes.

## Decisions affecting scope (awaiting approval)

All material contract decisions — route shape, parameter names, page-size
bound, client signature, CLI flags, text-match semantics — are collected
with recommendations in `### Implementation decisions and open questions`
below and require approval before execution. Execution has not been
authorized; this task currently tracks planning only.

## Supporting facts

- `GET /notes/` (src/app/api/notes.py:8) is unparameterized and returns the
  full collection as a JSON array via `crud.get_all()`
  (src/app/api/crud.py:4); storage is SQLite through `databases` +
  SQLAlchemy with columns `id`, `title`, `description` (src/app/db.py).
- `NotesClient.list_notes()` (packages/notes_client/notes_client/client.py:20)
  performs `transport.get("/notes/")`; the client test fake's `get` already
  accepts `**kwargs`, so query parameters can be introduced without breaking
  the existing harness.
- The CLI `list` command (apps/notes_cli/cli.py:5) prints `id: title` from
  `client.list_notes()`; CLI tests inject a fake client object.
- The three surfaces are independently maintained (separate `pyproject.toml`
  for the service, `notes-client`, and `notes-cli`). Per AGENTS.md, these
  public HTTP, package, and application compatibility boundaries justify
  separate deliverables — the decomposition is by boundary, not by file or
  test level.
- `docs/development/index.md` currently states "No notes-query
  specification exists." — the contract specification belongs there.
- Documentation guidance (`docs/development/documentation.md`) was read
  during planning; the smallest sufficient structure is one specification
  page plus updates to the existing READMEs.

## Subtasks

- [ ] tasks/20260925-notes-query-capability/010-public-query-contract.md
- [ ] tasks/20260925-notes-query-capability/020-api-query-parameters.md
- [ ] tasks/20260925-notes-query-capability/030-client-query-parameters.md
- [ ] tasks/20260925-notes-query-capability/040-cli-query-end-to-end.md

## Execution plan

Status: Draft

### Design

One capability, one contract, three mirrors. The HTTP API owns the contract;
`notes_client` mirrors it as keyword arguments on `list_notes()`; the CLI
mirrors it as flags on `notes list`. No surface invents divergent semantics.

Component responsibilities:

- Contract specification (010): one page in `docs/development/` pins
  parameter names, semantics, bounds, errors, and compatibility guarantees
  for all three surfaces. Consumers rely on it only after this page is
  approved and the API tests in 020 pin the contract.
- API (020): `read_all_notes` gains optional validated query parameters
  (FastAPI `Query` constraints produce the 422 behavior); `crud.get_all`
  gains optional limit/offset/order/filter while keeping a no-argument path
  that issues today's unmodified `notes.select()`, so the unparameterized
  response cannot drift.
- Client (030): `list_notes()` gains optional keyword-only arguments and
  sends only provided values as query parameters; the no-argument request
  stays identical to today's.
- CLI (040): the `list` subparser gains the flags and forwards provided
  values; output stays `id: title`. 040 additionally owns the decisive
  production-path check.

Data flow: CLI flags → `list_notes(**kwargs)` → query string → FastAPI
validation → `crud.get_all(...)` → SQL `WHERE`/`ORDER BY`/`OFFSET`/`LIMIT`.

Compatibility: every parameter is optional; absent parameters preserve
today's route, response shape, and ordering behavior. The client keeps its
existing method name and no-argument signature; the CLI keeps its existing
command and output format. The contract introduces one new failure mode:
422 for out-of-contract parameter values.

Recommended contract (awaiting approval — see decisions below):

- HTTP: `GET /notes/?limit=<1..100>&offset=<>=0>&sort=<id|title>&order=<asc|desc>&text=<substring>`
- Deterministic total order whenever any parameter is present (explicit
  sort with id tiebreak; else id ascending); unparameterized requests
  unchanged.
- Client: `list_notes(*, limit=None, offset=None, sort=None, order=None, text=None)`.
- CLI: `notes list [--limit N] [--offset N] [--sort {id,title}] [--order {asc,desc}] [--text S]`.

Verification strategy: integration/component tests at each boundary (API
tests through the real ASGI app and real SQLite; client request-construction
tests with a recording fake transport; CLI flag-mapping tests with the
existing fake-client harness), plus one decisive automated end-to-end test
in 040 that starts the real service and drives it through the real client —
mocks would not prove the production path this task requires.

### Implementation decisions and open questions

Material decisions, each needing approval before execution;
recommendations included, none resolved yet.

1. Route shape — extend `GET /notes/` with optional query parameters
   (recommended) versus adding a new collection route. Extending keeps one
   collection surface and matches the preservation requirement directly.
2. Pagination parameters — `limit` bounded to 1–100 with server-enforced
   422 outside the bound, and `offset` >= 0 (recommended). Open: confirm the
   100 page-size bound value. When `limit`/`offset` are used without
   `sort`, results default to `id` ascending so pages are stable and
   disjoint.
3. Sorting parameters — `sort` accepting `id` | `title` plus `order`
   accepting `asc` | `desc` (default `asc`), with `id` appended as tiebreak
   (recommended); the alternative single-token form `sort=-title` was
   rejected for weaker explicitness and CLI ergonomics. Title ordering uses
   the database collation, documented in the spec.
4. Text filter — parameter name `text` (recommended; alternatives `q`,
   `search`), case-insensitive substring match against `title` and
   `description`.
5. Client signature — add optional keyword-only parameters to
   `list_notes()` (recommended) versus a new `query_notes()` method; the
   no-argument call must remain unchanged either way.
6. CLI flags — `--limit`, `--offset`, `--sort`, `--order`, `--text` on the
   `list` subcommand (recommended), forwarding only provided values.
7. Versioning — bump `notes-client` and `notes-cli` to 0.2.0 in their
   shipping subtasks (recommended, minor; signals the new capability on
   compatibility boundaries).

### Documentation

- `docs/development/notes-query.md` (new, 010): the public contract for
  developers consuming the API, client, and CLI; carries a visible
  `Not implemented` marker until 020 ships, then 020 removes it.
- `docs/development/index.md` (010): links the spec and drops the stale
  "No notes-query specification exists." line.
- Root `README.md` (020): user-facing API text updated in the change that
  makes the capability true.
- `packages/notes_client/README.md` (030) and `apps/notes_cli/README.md`
  (040): current supported behavior for each surface, same change as the
  code.
No further structure; no placeholder pages.

### Task checklist

- [ ] 010 contract specification written and index updated
- [ ] 020 API query parameters implemented and pinned by tests
- [ ] 030 client query parameters implemented
- [ ] 040 CLI flags implemented with production-path e2e proof
- [ ] All requirement verification entries evidenced

### Requirement verification

- HTTP query behavior (bounds, stable ordering, text filter, 422s):
  integration tests through the real ASGI app against real SQLite
  (`src/tests`, existing `test_app` fixture) — owner 020. Fake-storage or
  mocked-crud tests would not be decisive for the HTTP contract.
- Preserved unparameterized API behavior: a dedicated regression test that
  a no-parameter request returns the full collection in today's shape, plus
  the existing `src/tests` suite passing — owner 020.
- Client parameterization and preserved no-argument call: component tests
  with a recording fake transport asserting the exact request (path,
  params) — owner 030. Component level is decisive for the client's own
  boundary; the full connection is proven once, in 040.
- Production client-to-service path: one automated end-to-end test in 040 —
  a real server hosts `app.main:app` (isolated working directory), notes are
  seeded through real HTTP POSTs, and the CLI runs via
  `notes_cli.cli:main(["list", "--sort", "title", "--limit", "2"],
  client=None)` with `NOTES_API_URL` set, so production
  `NotesClient.from_environment()` and the real httpx transport are
  exercised; the test asserts exact paged/ordered stdout. CLI tests with
  injected fake clients are supporting evidence only and do not substitute
  for this check.
- Contract stability before consumer reliance: the approved spec page (010)
  plus 020's contract-pinning API tests complete before 030/040 complete
  (enforced by subtask dependencies).
- Documentation currency: each README/spec change lands in the same
  subtask as the behavior it describes; verified by inspection per
  subtask.

### Additional implementation verification

- Page stability across two sequential requests under the same sort
  (020 test) — guards the "stable sorting" requirement beyond single-page
  assertions.
- URL encoding of `text` values with spaces through the production path:
  the 040 end-to-end seed data includes a title containing a space so the
  real client/service path exercises query encoding.