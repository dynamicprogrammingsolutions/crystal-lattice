# Notes query capability across API, client, and CLI

Add one supported notes-query capability — bounded pagination, stable sorting, and
optional text filtering — to the three public boundaries of this repository: the
FastAPI notes service (`src/app`), the reusable `notes-client` package
(`packages/notes_client`), and the `notes` CLI (`apps/notes_cli`). Current
unparameterized behavior must be preserved at every boundary, the HTTP contract
must be frozen in a maintained specification before the client and CLI rely on
it, and the CLI evidence must cross the production client-to-service path.

Planning only. Nothing here is implemented, and this plan is `Draft` until
approved.

## Requirements checklist

- [ ] R1 — The public HTTP API supports one notes-query capability implementing
      the frozen contract: bounded pagination (server-enforced page-size bound),
      stable sorting (deterministic order with an explicit tiebreaker), and
      optional text filtering (absent parameter means unfiltered). Owner:
      `tasks/20260920-notes-query-capability/010-service-query-api.md`.
- [ ] R2 — Current unparameterized behavior is preserved at the HTTP boundary:
      `GET /notes/` with no parameters still returns `200` with every note as a
      bare JSON array. Owner:
      `tasks/20260920-notes-query-capability/010-service-query-api.md`.
- [ ] R3 — The public HTTP contract (parameters, bounds, ordering and filtering
      semantics, response shape, error behavior) is pinned in a maintained
      specification and is stable before the client and CLI are built on it.
      Owner: `tasks/20260920-notes-query-capability/010-service-query-api.md`;
      gates `020` and `030`.
- [ ] R4 — The client package exposes the same query capability (mirroring the
      frozen contract) and current unparameterized `NotesClient.list_notes()`
      behavior is preserved exactly (same request path, no added parameters).
      Owner: `tasks/20260920-notes-query-capability/020-client-query-support.md`.
- [ ] R5 — The CLI exposes the same query capability and current unparameterized
      `notes list` behavior (command, flags, output format) is preserved.
      Owner: `tasks/20260920-notes-query-capability/030-cli-query-command.md`.
- [ ] R6 — CLI evidence proves the production path: a real CLI invocation using
      the production default client (`NotesClient.from_environment()`) against a
      real running service, with no fake client or transport on that path.
      Owner: `tasks/20260920-notes-query-capability/030-cli-query-command.md`.
- [ ] R7 — Maintained documentation is updated in the same reviewed changes that
      make the claims true: the contract specification plus the root, client,
      and CLI READMEs. Owners: `010` (spec + root README), `020` (client
      README), `030` (CLI README).

## Subtasks

- [ ] `tasks/20260920-notes-query-capability/010-service-query-api.md`
- [ ] `tasks/20260920-notes-query-capability/020-client-query-support.md`
- [ ] `tasks/20260920-notes-query-capability/030-cli-query-command.md`

Execution order is `010` → `020` → `030`. The `Depends On` declarations in the
subtask files make any other order unsafe, which is intentional: the contract
(R3) must exist and be stable before consumers rely on it, and the CLI's
decisive evidence (R6) must run the real package, not a stand-in.

## Open decisions needing approval

These are material public-contract decisions. The recommendations below are the
assumed contract throughout the subtask plans; approving this plan approves
them. Full tradeoffs are in the plan body under "Implementation decisions and
open questions".

1. Extend the existing `GET /notes/` collection route with optional query
   parameters (recommended) rather than adding a new endpoint.
2. `limit`/`offset` pagination with a server-enforced maximum `limit`
   (recommended) rather than cursor pagination.
3. Out-of-range parameter values are rejected with `422` (recommended) rather
   than silently clamped.
4. The unparameterized request keeps today's exact behavior, including no
   added default ordering (recommended); deterministic ordering is guaranteed
   for any parameterized query.
5. `q` is a case-insensitive substring filter over `title` and `description`
   (recommended).
6. Parameter and flag names mirror one-to-one across all three boundaries
   (`limit`, `offset`, `sort`, `order`, `q` / `--limit`, `--offset`, `--sort`,
   `--order`, `--q`) (recommended).
7. Minor version bumps for `notes-client` and `notes-cli` in the same change
   (recommended, both are at 0.1.0).

## Scope

In scope: the single query capability at all three boundaries; the contract
specification; tests as evidence per boundary; README/spec updates. Out of
scope: any other CRUD behavior, database schema changes (existing columns
suffice), auth, cursor pagination, envelope/metadata response shapes, error
behavior for unreachable services (unspecified today; not invented here), and
any implementation before plan approval.

## Supporting details

Facts, verified by inspection of the working tree:

- Service: router mounted at `/notes` (`src/app/main.py:15`); `GET /notes/`
  returns `crud.get_all()` — a full `notes.select()` — as a bare JSON array
  (`src/app/api/notes.py:8`, `src/app/api/crud.py:4`). Storage is SQLite
  (`sqlite:///./notes.db`) via `databases` + SQLAlchemy; columns `id` (int PK),
  `title`, `description` (`src/app/db.py:11`).
- Client: `NotesClient.list_notes()` calls `self.transport.get("/notes/").json()`
  (`packages/notes_client/notes_client/client.py:20`); `from_environment()` builds
  an `httpx.Client` from `NOTES_API_URL` (default `http://127.0.0.1:8000`). The
  package is at version `0.1.0` with no declared dev dependencies.
- CLI: `notes list` prints `f"{id}: {title}"` per note via `client.list_notes()`;
  `main()` defaults to `NotesClient.from_environment()` when no client is injected
  (`apps/notes_cli/cli.py:5`, `apps/notes_cli/cli.py:15`). Console script `notes`
  is declared in `apps/notes_cli/pyproject.toml`. Version `0.1.0`.
- Test reality: service tests use `TestClient` against the real app
  (`src/tests/`); client tests use a fake transport and never cross real HTTP
  (`packages/notes_client/tests/`); CLI tests inject a fake client
  (`apps/notes_cli/tests/test_cli.py`). None of the client/CLI tests exercise
  the production path today — this is the gap R6 closes.
- Docs state current behavior only: root README ("returns every note as a JSON
  array"), client README ("returns the unparameterized collection"), CLI README.
  `docs/development/index.md` explicitly records that no notes-query
  specification exists. `docs/development/documentation.md` was read before
  planning documentation; it requires docs to live with the owning subsystem and
  new public claims to land in the same reviewed change as the behavior.
- The decomposition into three subtasks follows the project context in
  `AGENTS.md`: public HTTP, package, and application compatibility boundaries
  justify separate deliverables. Each boundary has independent consumers and
  compatibility state; splitting further by file or test level would not.

## Execution plan

Status: Draft

Approach: define and freeze one HTTP contract for the notes collection query,
implement it once at each boundary in dependency order, and prove each boundary
with the least expensive evidence that still crosses that boundary's real
public path.

Sequence:

1. `010` implements the capability on the existing collection route and
   publishes the contract specification in the same change, so the contract is
   both documented and true at the same review boundary. Unparameterized
   behavior is pinned by explicit tests (regression protection).
2. `020` extends `NotesClient.list_notes()` with optional keyword parameters
   mirroring the contract. When called with no arguments it must issue the
   identical request as today (no `params` at all), so existing client users
   are unaffected. Evidence: component tests for parameter mapping plus one
   integration test through a real `httpx` client against a real running
   service, because the package's purpose is real HTTP.
3. `030` adds optional flags to `notes list`. Its decisive evidence runs the
   production entry point with the default `from_environment()` client against
   a real service — the only test level that can prove the production
   client-to-service path (R6). Existing fake-based rendering tests stay as
   cheap unit evidence for output formatting.

Boundary discipline: each subtask's evidence crosses exactly its own boundary —
HTTP route for `010`, real HTTP transport for `020`, full production invocation
for `030`. No test-only shortcuts on any public path; the shared service-boot
harness needed by `020`/`030` is maintained test infrastructure and is verified
through its real consumers.

### Implementation decisions and open questions

All items below are material because they define the public contract or
user-visible surfaces. Recommendations are stated; approving the plan approves
them as a package. None are hidden requirements — they are decisions recorded
here for approval.

1. Route shape — extend `GET /notes/` with optional query parameters vs. add a
   new query endpoint. Recommendation: extend the existing route. It is the
   smallest change, keeps one capability in one place, and makes preservation
   of the unparameterized behavior a directly testable property of the same
   route. A separate endpoint would duplicate the collection concept and force
   consumers to migrate to benefit.
2. Pagination style — `limit`/`offset` vs. cursor. Recommendation:
   `limit`/`offset`. The dataset and contract are simple; cursors would add
   opaque tokens across all three boundaries for no demonstrated need. Bounds:
   `limit` must be `1..LIMIT_MAX` (server-enforced constant, recommended 100),
   `offset >= 0`; out-of-range values get FastAPI's `422` validation error
   rather than silent clamping, because silent clamping hides contract
   violations from consumers.
3. Bounded vs. preserving unparameterized behavior — resolving the tension in
   the request. Recommendation: bounds apply when `limit` is supplied; an
   absent `limit` still returns every matching note. A default page size would
   silently truncate the collection for existing unparameterized consumers and
   break the documented "every note" contract.
4. Default ordering — apply deterministic ordering only to parameterized
   queries; the fully unparameterized request keeps today's behavior with no
   new ordering guarantee. Recommendation: strict preservation (as stated).
   Alternative considered: always ordering by `id` asc, which would make the
   whole collection deterministic but adds a guarantee to a path the requirement
   says must be preserved; rejected as the riskier reading. Whenever any query
   parameter is present, results are ordered by the chosen field and direction
   with `id` ascending as tiebreaker, so pages are stable and complete
   (no gaps/overlaps across pages).
5. Text filtering semantics — `q` is optional; absent or empty means unfiltered;
   otherwise case-insensitive substring match against `title` or `description`
   (SQL `LIKE`). Caveat to document: SQLite `LIKE` case-folds ASCII only.
6. Naming — one-to-one mirroring `limit`/`offset`/`sort`/`order`/`q` across
   HTTP parameters, client keyword arguments, and CLI flags (`--limit`,
   `--offset`, `--sort`, `--order`, `--q`). Recommendation: mirror, for a single
   traceable contract. Alternative: friendlier CLI names (e.g. `--filter`),
   rejected as a second name for the same thing.
7. Sort field vocabulary — allowed values `id`, `title`, `description`;
   direction `asc` (default) or `desc`. Unknown field or direction → `422`.
   Tiebreaker always `id` ascending, regardless of direction.
8. Response shape — stays a bare JSON array of `{id, title, description}` for
   parameterized and unparameterized calls alike. Consequence of decision 3:
   no envelope, therefore no total-count metadata; consumers bound their own
   traversal by empty pages. Recorded as an accepted consequence, not a hidden
   requirement.
9. Versioning — bump `notes-client` and `notes-cli` to `0.2.0` in the same
   change that grows their public surface (both currently `0.1.0`).

No requirement questions are open: the request fixes the outcomes (one
capability, three boundaries, bounded pagination, stable sorting, optional
filtering, preservation, contract-first, production-path CLI evidence); the
decisions above choose within them.

### Documentation

- `010`: new contract specification page under `docs/` (recommended location
  `docs/notes-query.md` — the service owns the HTTP contract and `docs/` is its
  documentation home; `docs/development/index.md` currently records that no
  such spec exists and will be updated to point at it). Root `README.md`
  updated to describe the now-supported query capability next to the existing
  collection description. Audience: HTTP API consumers (client maintainers,
  CLI users, direct API users). Spec content must match implemented behavior —
  no `Not implemented` markers needed since both land in the same change.
- `020`: `packages/notes_client/README.md` — document the new optional
  `list_notes()` parameters for client users; keep the unparameterized usage
  shown as the default behavior.
- `030`: `apps/notes_cli/README.md` — document the new flags for CLI users.

### Task checklist

- [ ] `010`: implement query parameters on `GET /notes/` (pagination bounds,
      stable sort with tiebreaker, optional filter, validation errors);
      write `docs/notes-query.md`; update root `README.md` and
      `docs/development/index.md`; add/adjust service tests; run suite.
- [ ] `020`: extend `NotesClient.list_notes()` with mirroring optional keyword
      parameters and exact-preservation no-arg path; update client README;
      add component + real-service integration tests; run suite.
- [ ] `030`: add mirroring flags to `notes list`; update CLI README; add
      parser-mapping unit tests and the production-path invocation test; run
      suite; bump package versions if decision 9 approved.
- [ ] Cross-boundary pass: contract text, parameter names, bounds, and
      semantics agree across spec, service, client, and CLI; all suites green.

### Requirement verification

- R1 — Service integration tests through the public HTTP route (real app +
  storage): bounded `limit` (accepted values, rejected out-of-range),
  `offset` windows, sort determinism with seeded tie collisions, filter
  matching/non-matching/empty, `422` on invalid values.
- R2 — Unparameterized equivalence test: with seeded data, `GET /notes/`
  returns `200` and every created note as a bare array; existing
  `src/tests/test_notes.py` tests remain green unchanged.
- R3 — `docs/notes-query.md` exists, matches implemented behavior (values,
  defaults, error behavior), and lands in the same change as the
  implementation; `020`/`030` declare `Depends On` `010`, so consumers cannot
  be approved before the contract exists.
- R4 — Client component tests asserting the exact request issued (no params
  when called bare; contract-matching params otherwise) plus one integration
  test of the real client against a real running service; existing client test
  stays green.
- R5 — CLI unit tests for flag mapping (stubbed only at the CLI→client
  interface) and a no-flags run preserving current output; existing CLI test
  stays green.
- R6 — Production-path test: real service running, CLI invoked as the installed
  console script (or `main()` with no injected client) using
  `NotesClient.from_environment()` via `NOTES_API_URL`; asserts rendered output
  reflects pagination, sorting, and filtering. No fake on the path.
- R7 — Spec + README updates present in the same changes as their behavior;
  verified by review of the diff in each subtask.

### Additional implementation verification

- Cross-boundary consistency: after `030`, one production-path run using every
  parameter (limit, offset, sort, order, q) confirms the CLI, client, and
  service agree on names and semantics in a single real chain — the strongest
  available evidence that the frozen contract is what all three implement.