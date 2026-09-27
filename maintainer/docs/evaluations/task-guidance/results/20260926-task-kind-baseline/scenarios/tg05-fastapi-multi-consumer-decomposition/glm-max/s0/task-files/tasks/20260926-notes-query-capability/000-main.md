# Notes query capability across the public API, Python client, and CLI

Add one supported notes-collection query capability end to end: the public
HTTP API gains bounded pagination, stable sorting, and optional text filtering
on the notes collection; the reusable `notes_client` package and the `notes`
CLI expose the same capability, each preserving its current unparameterized
behavior. The public contract is defined and frozen before the client and CLI
rely on it, and one named end-to-end check proves the real CLI → real client →
real running service path.

## Requirements checklist

- [ ] R1 — The notes collection HTTP operation (`GET /notes/`) supports
      bounded pagination (server-enforced maximum page size), stable sorting
      (deterministic total order), and optional text filtering, per an
      approved written contract.
- [ ] R2 — Unparameterized API behavior is preserved: `GET /notes/` with no
      query parameters returns the full collection as a bare JSON array
      exactly as today, and existing service tests keep passing unmodified.
- [ ] R3 — `notes_client.NotesClient.list_notes()` accepts the query
      parameters and forwards them to the service; the no-argument call sends
      the same request as today and returns the same parsed JSON list.
- [ ] R4 — `notes list` exposes the capability through CLI flags and forwards
      them through the client; the no-flag invocation and its `{id}: {title}`
      output format are unchanged.
- [ ] R5 — The public query contract (parameters, defaults, bounds, ordering,
      response shape, error semantics) is recorded and frozen before the
      client and CLI are implemented against it; task order enforces
      API-contract work first.
- [ ] R6 — One named decisive check exercises the production client-to-service
      path end to end: real CLI invocation, real `NotesClient`, real HTTP
      server running the real app. Per-side mocked tests alone do not satisfy
      this.
- [ ] R7 — Maintained documentation is updated in the same reviewed changes as
      the behavior it describes: service-facing docs (root `README.md`, and
      the notes-query specification if approved),
      `packages/notes_client/README.md`, and `apps/notes_cli/README.md`.

## Subtasks

- [ ] tasks/20260926-notes-query-capability/010-api-collection-query.md
- [ ] tasks/20260926-notes-query-capability/020-client-query-parameters.md
- [ ] tasks/20260926-notes-query-capability/030-cli-query-flags-and-production-path.md

## Decisions pending plan approval

Contract-level choices below are presented with tradeoffs in
`## Execution plan` → `### Implementation decisions and open questions`.
Approving the plan freezes them as the v1 public contract; later changes
become breaking for consumers.

- D1 — Extend `GET /notes/` in place; keep the bare JSON array response shape.
- D2 — `limit`/`offset` pagination with a server-enforced maximum page size;
      absent `limit` means full collection (required for R2).
- D3 — Single `sort` parameter (`field` or `-field`); `id` ascending always
      appended as tie-break; default order `id` ascending.
- D4 — Single `q` text filter; case-insensitive literal substring match on
      `title` only.
- D5 — Extend the existing `list_notes()` with optional keyword-only
      parameters instead of adding a new client method.
- D6 — CLI flags `--limit`, `--offset`, `--sort`, `--filter` on the `list`
      subparser (`--filter` carries the contract's `q` value).
- D7 — The end-to-end check runs a real uvicorn server on an ephemeral local
      port (adds `uvicorn` as a test dependency of the CLI app) rather than an
      in-process ASGI transport.
- D8 — Record the contract in a short specification under `docs/development/`
      and update `docs/development/index.md`, in addition to README updates.
- D9 — Record the implicit `notes-cli` → `notes-client` dependency in the CLI
      README (and optionally in `pyproject.toml`) instead of leaving it
      undocumented.

No unresolved requirement questions: the request fixes the capability, the
three compatibility-preserving boundaries, the contract-first ordering, and
the production-path proof. Everything above is a design decision awaiting
approval.

## Supporting facts

- Service: FastAPI app with router prefix `/notes` (`src/app/main.py`);
  storage is SQLite via `databases`/SQLAlchemy, table
  `notes {id, title, description}` (`src/app/db.py`, hardcoded
  `sqlite:///./notes.db`).
- Today the collection route returns `crud.get_all()` — a bare list of every
  note (`src/app/api/notes.py:8`, `src/app/api/crud.py:4`); there are no query
  parameters, no ordering contract, and no pagination.
- Client: `NotesClient(transport)` with `from_environment()` reading
  `NOTES_API_URL` (default `http://127.0.0.1:8000`); `list_notes()` does
  `GET /notes/` and returns `.json()`
  (`packages/notes_client/notes_client/client.py`).
- CLI: `notes list` prints `{id}: {title}` per note through the client
  (`apps/notes_cli/cli.py`); `apps/notes_cli/pyproject.toml` declares no
  dependency on `notes-client` despite importing it (D9).
- Current tests are per-boundary and shallow: service tests assert only list
  shape and one POST route; the client test uses a fake transport; the CLI
  test uses a fake client. No test today crosses CLI → client → service,
  which is why R6 requires a new named decisive check.
- `docs/development/index.md` states "No notes-query specification exists."
  Root `README.md` describes the collection route as returning every note as
  a JSON array. Both are maintained touchpoints for this change.
- No virtualenv or test dependencies exist in the workspace: runtime deps
  (`fastapi`, `databases`, `sqlalchemy`, `httpx`) are not installed, `pytest`
  is not declared in any pyproject, and `.gitignore` does not cover
  `notes.db`. Execution must first establish a test environment and
  invocation paths (service tests import `app` from `src/`; client/CLI tests
  import `notes_client`).
- Not yet verified (assumption to check during execution): whether the
  installed Starlette version runs the app lifespan for the existing
  `TestClient(app)` fixture pattern; if not, the fixture must enter the
  client as a context manager so `database.connect()` runs. The real-server
  end-to-end check runs lifespan regardless.

## Execution plan

Status: Draft

### Design

One supported query operation, extended in place at each of the three
boundaries. The service owns the contract; the client serializes it; the CLI
exposes it and owns the production-path proof.

Proposed v1 contract for `GET /notes/` (all parameters optional; violations
rejected with 422 by query validation):

| Parameter | Range / values | Default | Semantics |
| --------- | -------------- | ------- | --------- |
| `limit`   | integer 1..100 | absent  | Page size. Absent → full collection (preserves R2). Outside 1..100 → 422. This server-side cap is the pagination bound. |
| `offset`  | integer ≥ 0    | 0       | Rows skipped after filtering and sorting. |
| `sort`    | `id`, `title`, `description`, each optionally `-`-prefixed | `id` ascending | Primary sort field and direction; `id` ascending is always appended as final tie-break, so the total order is deterministic. Unknown value → 422. |
| `q`       | any string     | absent  | Case-insensitive literal substring match on `title`; `%` and `_` are matched literally. |

Response body is unchanged: a bare JSON array of `{id, title, description}`
objects. The unparameterized response is the full collection in `id` order —
in practice identical to today's SQLite insertion order, but now contractual
rather than incidental.

Component responsibilities and compatibility states:
- Service (010) owns the contract and its validation: FastAPI `Query`
  constraints on the collection handler; `crud.get_all` gains optional
  parameters building the SQLAlchemy select (escaped `ilike` filter,
  `order_by` with `id` tie-break, `offset`, `limit`). Absent parameters leave
  the query unchanged.
- Client (020) forwards optional keyword-only parameters as query-string
  parameters, omitting unset ones; no client-side validation; unchanged
  return type.
- CLI (030) parses flags and maps them 1:1 to client parameters, keeps the
  existing output format, and owns the decisive end-to-end check.
- Each boundary keeps its unparameterized behavior (same request, same
  response, same output); new behavior is reachable only through the newly
  added optional parameters/flags. Dependencies enforce 010 → 020 → 030.

Interpretation note: "stable sorting" means a deterministic total order
(field plus `id` tie-break), not snapshot stability of offset pagination
under concurrent writes; the latter is out of scope.

Verification strategy:
- 010: integration tests through the real FastAPI app and SQLite at the HTTP
  boundary (existing `src/tests` pattern) — pagination windows and bounds,
  sort directions and tie stability, filter matching incl. literal `%`/`_`,
  combined parameters, 422s, and an unparameterized regression.
- 020: component tests with a request-capturing fake transport — parameter
  serialization and an unparameterized call that sends no query string.
- 030: CLI unit test (flags → client arguments, output format) plus the named
  decisive check — a real uvicorn server serving `app.main`, notes seeded via
  the public POST route, `NOTES_API_URL` set, real
  `NotesClient.from_environment()`, real `main([...])` invocation, asserting
  a parameterized query's stdout and the unparameterized full listing through
  the same path.
- All three existing suites pass unmodified.

### Implementation decisions and open questions

- D1 (route and response shape) — extend `GET /notes/` in place and keep the
  bare array. Alternatives rejected: an envelope would break the current
  shape for unparameterized consumers or make the shape depend on which
  parameters are sent; a separate `/notes/query` route would fragment "one
  capability" into two collection operations. Consequence: no total-count
  field; consumers detect page end by receiving a short page.
- D2 (pagination) — `limit`/`offset` with a server-enforced cap of 100.
  Absent `limit` means the full collection; a default page size would change
  unparameterized behavior and violate R2. Out-of-range values → 422. The
  cap (100) is arbitrary but fixed in the contract; change it before
  approval, not after consumers rely on it.
- D3 (sorting) — one `sort` parameter, `field` or `-field`, over the three
  existing columns; `id` ascending always appended as tie-break; default `id`
  ascending. A separate `order` parameter was rejected: one parameter carries
  the same information.
- D4 (filtering) — one `q` parameter, case-insensitive literal substring
  match on `title` only. Matching `description` too would be more useful but
  widening the match later changes results for existing consumers, so the
  narrower, easier-to-document semantics are recommended for v1.
- D5 (client surface) — optional keyword-only parameters on the existing
  `list_notes()`. A separate `query_notes()` method was rejected: two methods
  for one collection operation invite divergence, and the no-arg call must
  stay unchanged.
- D6 (CLI surface) — flags `--limit`, `--offset`, `--sort`, `--filter` on the
  existing `list` subparser; `--filter` maps to the contract's `q`. Flag
  forwarding only; the CLI adds no semantics of its own.
- D7 (end-to-end harness) — real uvicorn server on an ephemeral `127.0.0.1`
  port in the decisive check, added as a test dependency of the CLI app; the
  socket-level server is what makes this the production path (lifespan, real
  HTTP round trips, `NOTES_API_URL` construction). An in-process
  `httpx.ASGITransport` fallback exists but simulates the socket; not
  recommended for R6.
- D8 (contract artifact) — a short specification under `docs/development/`
  (updating `index.md`'s "no notes-query specification exists" note) in
  addition to README updates. The spec is the reviewed artifact that makes
  the contract stable and inspectable before consumers depend on it; the
  generated OpenAPI schema remains the machine-readable contract, changed
  through its maintained source (the route definitions).
- D9 (CLI packaging gap) — record the `notes-cli` → `notes-client` dependency
  in the CLI README; optionally also declare it in `pyproject.toml`. Left as
  a decision because the workspace has no package index, so an added install
  requirement may not resolve; the README note is safe either way.
- Minor version bumps (`notes-client`, `notes-cli` 0.1.0 → 0.2.0) are
  optional since both changes are backward-compatible; not required by this
  task.

Open question: none at requirement level. Approval of this plan approves
D1–D9 as the frozen v1 contract.

### Documentation

- Root `README.md` (service audience): the collection route description
  gains the query parameters; owned by 010, same change as the API code.
- Notes-query specification under `docs/development/` plus `index.md` update
  (if D8 approved); owned by 010 — the service owns the contract.
- `packages/notes_client/README.md` (Python integrators): parameter
  documentation; owned by 020.
- `apps/notes_cli/README.md` (end users): flag documentation and the client
  dependency note (D9); owned by 030.
- No new documentation structure beyond the single spec page; no placeholder
  pages.

### Task checklist

- [ ] 010 — API collection query implemented, contract locked with tests and
      documentation
      (tasks/20260926-notes-query-capability/010-api-collection-query.md)
- [ ] 020 — Client query parameters implemented with regression tests and
      docs, after 010
      (tasks/20260926-notes-query-capability/020-client-query-parameters.md)
- [ ] 030 — CLI query flags plus the decisive production-path end-to-end
      check and docs, after 010 and 020
      (tasks/20260926-notes-query-capability/030-cli-query-flags-and-production-path.md)

### Requirement verification

- R1 → 010 integration tests at the HTTP boundary (real app + SQLite):
  windowing, bounds, ordering, filtering, 422s.
- R2 → existing `src/tests` pass unmodified plus a new unparameterized
  regression test asserting the bare-array full collection in `id` order.
- R3 → 020 captured-request component tests (forwarded parameters;
  no-arg call sends no query string) plus the 030 end-to-end check.
- R4 → 030 CLI unit test (flags → client arguments; unchanged output format)
  plus the end-to-end check.
- R5 → process constraint made structural: 020 and 030 declare
  `Depends On: 010`; the contract is written down (README/spec) in 010's
  reviewed change and frozen by plan approval before 020/030 execute.
- R6 → the named decisive check in 030: real uvicorn service + real
  `NotesClient` via `NOTES_API_URL` + real CLI `main()` invocation, asserting
  both a parameterized query and the unparameterized full listing through
  stdout. The client component test and the service route tests are
  supporting evidence only and do not substitute for this.
- R7 → documentation diffs reviewed with their owning code changes
  (010/020/030).

### Additional implementation verification

- 010 asserts the generated OpenAPI schema (read via the maintained route
  definitions) lists the new parameters — a cheap contract cross-check.
- Watch `notes.db` side effects: the service writes `./notes.db` relative to
  the working directory and it is not gitignored; run verification from an
  isolated working directory so execution leaves no stray database file in
  the repository.
- None beyond the above; the per-child plans carry the focused evidence.