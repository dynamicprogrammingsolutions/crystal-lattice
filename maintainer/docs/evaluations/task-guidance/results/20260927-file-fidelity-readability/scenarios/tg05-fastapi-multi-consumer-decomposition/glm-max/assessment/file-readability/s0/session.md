# Session — tg05-fastapi-multi-consumer-decomposition · file-readability-assessment-glm-max-s0 · glm max

- Run: `20260928T203028.675520Z-task-guidance-file-readability-tg05-fastapi-multi-consumer-decomposition-glm-max-s0-55c6f00c`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `08db300c869d85e5…`)
- Config: [glm-assessor-max](../../../../../../shared/configs/glm-assessor-max.json)
- Activity: 3 messages · 0 tool calls · 0 tool results
- Usage: unknown — saved session contains no provider usage metadata

## Transcript

**User**

Assess how easily a human reader can work with the task files below.
You are that reader: a maintainer who must find, understand, and act on
what the files say. Judge every top-level section that is present; do
not invent sections that are absent, and do not grade files or sections
that do not appear.

Grade each present top-level section `readable`, `partial`, or
`unreadable`: can a reader take in that section's content with
reasonable effort — scan it, hold it, and use it? A section is
`unreadable` when a reader must re-read dense prose or wall-like list
items to extract what matters; `partial` when parts strain the reader.

Then grade the whole file's navigation `navigable`, `partial`, or
`confusing`: can a reader find the thing they are looking for — the
outcome, the constraint, the open question, the plan status — from the
file's structure alone?

Measured structure facts are provided per section; anchor on these
numbers rather than impressions. They are facts, not rules: no shape is
banned or required. Formatting elements — tables, ordered lists, code
snippets, short paragraphs — are tools among many; what is graded is
the reader's experience, never the presence of a specific element.

Every grade carries findings: concrete `{where, quote, why}` items. A
non-top grade with empty findings is invalid. Then hunt for
presentation mistakes explicitly — prose walls, list items that mix
several facts, buried load-bearing facts, headings that do not match
their content, walls of unchecked boxes — and list each as
`{where, quote, why}` in `mistakes`.

Depth must match impact: a short section is not a defect; a dense
section is not automatically one either. Verbosity is not rewarded;
brevity that loses nothing is not penalized.

Return JSON only:

{
  "schema_version": 1,
  "scenario_id": "tg05-fastapi-multi-consumer-decomposition",
  "assessment": {
    "sections": {
      "SECTION TITLE": {
        "grade": "readable|partial|unreadable",
        "findings": [{"where": "...", "quote": "...", "why": "..."}]
      }
    },
    "navigation": {"grade": "navigable|partial|confusing", "findings": []},
    "mistakes": [{"where": "...", "quote": "...", "why": "..."}],
    "summary": "concise evidence-based interpretation"
  }
}

`sections` contains exactly the top-level sections listed in the
measured facts, keyed by the exact Section values of that table
(`<file path> — <section title>`), so multi-file task sets stay
addressable.

What these files are for:

# FastAPI multi-consumer query decomposition

Recognize valid service, SDK, and application boundaries without fragmenting each component into phases.

Category: decomposition

Measured structure facts (per file, per top-level section):

#### tasks/20260926-notes-query-capability/000-main.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-notes-query-capability/000-main.md — Requirements checklist | 235 | 0 | 0 | 7 | 12 | 0 | 0 | 0 | 9 |
| tasks/20260926-notes-query-capability/000-main.md — Subtasks | 12 | 0 | 0 | 3 | 1 | 0 | 0 | 0 | 0 |
| tasks/20260926-notes-query-capability/000-main.md — Decisions pending plan approval | 241 | 2 | 34 | 9 | 15 | 0 | 0 | 0 | 27 |
| tasks/20260926-notes-query-capability/000-main.md — Supporting facts | 265 | 0 | 0 | 8 | 13 | 0 | 0 | 0 | 36 |
| tasks/20260926-notes-query-capability/000-main.md — Execution plan | 1308 | 7 | 121 | 36 | 15 | 6 | 6 | 0 | 77 |

#### tasks/20260926-notes-query-capability/010-api-collection-query.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-notes-query-capability/010-api-collection-query.md — Requirements checklist | 156 | 0 | 0 | 6 | 12 | 0 | 0 | 0 | 21 |
| tasks/20260926-notes-query-capability/010-api-collection-query.md — Execution plan | 491 | 3 | 127 | 25 | 14 | 4 | 0 | 0 | 47 |

#### tasks/20260926-notes-query-capability/020-client-query-parameters.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-notes-query-capability/020-client-query-parameters.md — Requirements checklist | 90 | 0 | 0 | 4 | 11 | 0 | 0 | 0 | 7 |
| tasks/20260926-notes-query-capability/020-client-query-parameters.md — Execution plan | 260 | 2 | 70 | 16 | 13 | 4 | 0 | 0 | 9 |

#### tasks/20260926-notes-query-capability/030-cli-query-flags-and-production-path.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-notes-query-capability/030-cli-query-flags-and-production-path.md — Requirements checklist | 132 | 0 | 0 | 5 | 14 | 0 | 0 | 0 | 12 |
| tasks/20260926-notes-query-capability/030-cli-query-flags-and-production-path.md — Execution plan | 451 | 2 | 210 | 20 | 15 | 4 | 0 | 0 | 29 |

The produced task files:

### tasks/20260926-notes-query-capability/000-main.md

````markdown
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
````

### tasks/20260926-notes-query-capability/010-api-collection-query.md

````markdown
# Public API: bounded, sorted, filtered notes collection query

Implement and lock the approved query contract on the notes collection route
(`GET /notes/`): bounded pagination, stable sorting, and optional text
filtering, with unparameterized behavior preserved and the contract recorded
in the maintained service documentation.

Parent Task: tasks/20260926-notes-query-capability/000-main.md
Depends On: none — this is the first subtask; the contract it implements is
approved with the parent plan (decisions D1–D4, D8).

## Requirements checklist

- [ ] `GET /notes/` accepts optional query parameters per the approved
      contract: `limit` (integer 1..100), `offset` (integer ≥ 0), `sort`
      (`id|title|description`, optionally `-`-prefixed for descending), `q`
      (case-insensitive literal substring on `title`).
- [ ] Pagination is bounded by the server: `limit` outside 1..100 is rejected
      with 422; malformed `offset` or unknown `sort` values are rejected with
      422.
- [ ] Results are totally ordered: the requested `sort` field is primary and
      `id` ascending is always appended as tie-break; when `sort` is absent
      the order is `id` ascending.
- [ ] Unparameterized `GET /notes/` returns the full collection as a bare
      JSON array of `{id, title, description}` in `id` order, identical to
      current behavior; the existing service tests pass unmodified.
- [ ] The contract is recorded in the same change: root `README.md` updated
      and (per D8) a notes-query specification under `docs/development/` with
      `index.md` updated.
- [ ] The generated OpenAPI schema reflects the new parameters.

## Execution plan

Status: Draft

Approach:
- Add FastAPI `Query` parameters to `read_all_notes` (`src/app/api/notes.py`):
  `limit` with `ge=1, le=100`, `offset` with `ge=0`, `sort` validated against
  an allow-list of the six permitted values, `q` as a plain optional string.
  Validation failures become contractual 422 responses.
- Extend `crud.get_all` (`src/app/api/crud.py`) to accept the optional
  parameters and build the SQLAlchemy select: optional
  `where(notes.c.title.ilike(...))` with `%`, `_`, and the escape character
  escaped in the user value so matching stays literal; `order_by` on the
  requested column plus `notes.c.id.asc()` as tie-break; `offset`; `limit`.
  Absent parameters leave the query unchanged, preserving current behavior.
- Keep the response a bare list — no envelope, no shape change (D1).

Tests (additions in `src/tests/`, existing tests kept unmodified):
- Seed via the public POST route, then assert:
  - unparameterized: 200, bare array, full collection, `id` ascending;
  - `limit`/`offset` windowing, including limit-absent full result;
  - `limit=101` and `limit=0` → 422; `offset=-1` → 422;
  - `sort=title` and `sort=-title` with duplicate titles → ties broken by
    ascending `id` (stability proof);
  - unknown `sort` value → 422;
  - `q` matches case-insensitively, `%`/`_` match literally, no match → `[]`;
  - combined `q` + `sort` + `limit` + `offset`.
- Verify how the fixture's `TestClient(app)` invocation connects the database
  (lifespan); if the installed Starlette does not run lifespan outside a
  context manager, adjust the fixture to a context-manager client without
  weakening the boundary.
- Assert the generated OpenAPI schema exposes the new parameters.

Environment: execution must first establish a test environment (no
virtualenv or declared test dependencies exist) and run from an isolated
working directory, because the service writes `./notes.db` relative to the
working directory.

### Implementation decisions and open questions

- Contract values (bounds, sort fields, filter semantics, response shape)
  come from parent decisions D1–D4; this subtask implements them and locks
  them with tests. Open questions: none at this scope.
- Local choices resolved here: validation via FastAPI `Query` constraints
  (contractual 422s), literal-match escaping in the CRUD layer, `sort`
  validated as an explicit allow-list.

### Documentation

- Root `README.md`: update the "returns every note as a JSON array"
  description to the current collection behavior plus the query parameters,
  in the same change as the code.
- If D8 approved: add the notes-query specification under `docs/development/`
  describing the frozen contract and update `index.md`; otherwise leave
  `docs/development/` untouched.

### Task checklist

- [ ] Implement query parameters and CRUD selection with stable ordering
- [ ] Add HTTP-boundary integration tests (new behavior and unparameterized regression)
- [ ] Update root `README.md` (and the spec per D8) in the same change
- [ ] Run the service suite; confirm existing tests pass unmodified

### Requirement verification

- Parent R1 → the integration tests listed above (windowing, bounds, sort
  directions with tie stability, literal filter matching, 422s).
- Parent R2 → unmodified existing tests plus the unparameterized regression
  test asserting bare-array shape, full collection, `id` order.
- Parent R5 → the recorded contract (README/spec) reviewed in the same change
  as the implementation; generated OpenAPI asserted to match.
- Parent R7 (service part) → README/spec diff in this change.
````

### tasks/20260926-notes-query-capability/020-client-query-parameters.md

````markdown
# Python client: query parameters on list_notes

Expose the approved query contract on the reusable client so Python consumers
can paginate, sort, and filter the notes collection, while the no-argument
`list_notes()` call keeps its current request and return behavior.

Parent Task: tasks/20260926-notes-query-capability/000-main.md
Depends On: tasks/20260926-notes-query-capability/010-api-collection-query.md
(the contract is implemented and locked before the client relies on it)

## Requirements checklist

- [ ] `NotesClient.list_notes()` accepts optional keyword-only `limit`,
      `offset`, `sort`, and `q`, and forwards provided values as query
      parameters on `GET /notes/` exactly as the approved contract defines
      them — no client-side transformation, defaulting, or validation.
- [ ] The no-argument call issues the same request as today (no query
      parameters) and returns the parsed JSON list — unchanged return type.
- [ ] Component tests prove parameter serialization via a captured request
      and prove the unchanged unparameterized request.
- [ ] `packages/notes_client/README.md` documents the parameters in the same
      change.

## Execution plan

Status: Draft

Approach:
- Extend `list_notes` in
  `packages/notes_client/notes_client/client.py` to
  `list_notes(self, *, limit=None, offset=None, sort=None, q=None)`; build a
  params mapping from the set values and pass it to
  `self.transport.get("/notes/", params=...)` only when non-empty, so the
  unparameterized call stays byte-identical to today's request.
- No validation in the client: the service is the contract boundary; the
  client passes values through (parent decision D5).

Tests (component level, `packages/notes_client/tests/`):
- Fake transport capturing path and query parameters:
  - each parameter appears in the captured query string with the expected
    encoding;
  - unset parameters are omitted;
  - the no-argument call sends no query string (regression) and returns the
    parsed JSON list.
- The existing client test passes unmodified. The full client-to-service
  path is not proven here: it is owned by the named decisive check in 030.

### Implementation decisions and open questions

- D5 (extend `list_notes`; no new method) is approved at the parent level.
  Local choices resolved here: keyword-only parameters to keep the no-arg
  call unambiguous, omission (not empty strings) for unset values.
- Open questions: none.

### Documentation

- `packages/notes_client/README.md`: document the optional parameters and
  note that the no-argument call is unchanged (Python integrator audience).

### Task checklist

- [ ] Add keyword-only query parameters to `list_notes()`
- [ ] Add component tests for serialization and the unparameterized regression
- [ ] Update `packages/notes_client/README.md`
- [ ] Run the client suite

### Requirement verification

- Parent R3 → captured-request component tests prove the forwarded parameters
  and the unchanged no-arg request/return; the production path is proven
  once, end to end, by the decisive check in 030.
- Parent R7 (client part) → README diff in the same change.
````

### tasks/20260926-notes-query-capability/030-cli-query-flags-and-production-path.md

````markdown
# CLI: query flags and the production client-to-service path

Expose the query capability on `notes list` and prove — through the real
production path — that the CLI, the client, and the running service work
together: a real server, the real `NotesClient`, the real `main()`.

Parent Task: tasks/20260926-notes-query-capability/000-main.md
Depends On: tasks/20260926-notes-query-capability/010-api-collection-query.md
and tasks/20260926-notes-query-capability/020-client-query-parameters.md

## Requirements checklist

- [ ] `notes list` supports `--limit`, `--offset`, `--sort`, and `--filter`
      (parent decision D6), forwarding provided values to the client's
      parameters.
- [ ] The no-flag `notes list` invocation and its `{id}: {title}` output
      format are unchanged.
- [ ] A CLI unit test proves the flags map to client arguments and the output
      format is unchanged.
- [ ] The named decisive end-to-end check runs the production path: a real
      uvicorn server serving the real app, notes seeded through the public
      POST route, the real `NotesClient` via `NOTES_API_URL`, and a real
      `main([...])` invocation with no injected test double — asserting a
      parameterized query's stdout and the unparameterized full listing
      through the same path.
- [ ] `apps/notes_cli/README.md` documents the flags and the
      `notes-client` dependency (parent decision D9) in the same change.

## Execution plan

Status: Draft

Approach:
- `apps/notes_cli/cli.py`: add options to the `list` subparser
  (`--limit` int, `--offset` int, `--sort` str, `--filter` str, all defaulting
  to unset) and pass only provided values to `client.list_notes(...)`; keep
  the print loop and line format unchanged.
- Named decisive check (new test in `apps/notes_cli/tests/`):
  - start `uvicorn.Server` serving `app.main.app` on an ephemeral
    `127.0.0.1` port in a daemon thread and wait for startup (`uvicorn` is
    added as a test dependency of the CLI app — parent decision D7);
  - seed notes through the public HTTP POST route so the check uses only
    public behavior;
  - set `NOTES_API_URL` to the server address, build
    `NotesClient.from_environment()`, and call
    `main(["list", "--sort", "title", "--limit", "2", "--filter", ...])` with
    no injected client; assert the exact stdout lines (order, filtering,
    pagination);
  - run the unparameterized `main(["list"])` against the same server and
    assert the full seeded listing — compatibility verified through the
    production path as well.
  - This test traverses the real CLI parser → real client → real httpx →
    real TCP → real FastAPI app → SQLite. The per-side tests (020's
    captured-transport test, 010's route tests) remain supporting evidence
    only and do not substitute for this check.
- CLI unit test (existing pattern with a fake client): flags forwarded as the
  expected client keyword arguments; unchanged formatting.

Environment: execution must first establish a test environment — no
virtualenv or declared test dependencies exist yet, and the end-to-end test
needs `app` (from `src/`), `notes_client`, and `notes_cli` importable
alongside `uvicorn` and `pytest`. Run from an isolated working directory:
the service writes `./notes.db` relative to the working directory.

### Implementation decisions and open questions

- D6 (flag names), D7 (real uvicorn server), and D9 (dependency recording)
  are approved at the parent level. Local choices resolved here: ephemeral
  port with a daemon-thread server; seeding via the public POST route;
  the decisive check uses the `from_environment()` construction path.
- Open questions: none.

### Documentation

- `apps/notes_cli/README.md`: document the new flags and the dependency on
  `notes-client` (D9); end-user audience.

### Task checklist

- [ ] Add query flags to the `list` subparser
- [ ] Add CLI unit test for flag forwarding and output regression
- [ ] Add the named production-path end-to-end check (real server, real client, real CLI)
- [ ] Update `apps/notes_cli/README.md`
- [ ] Run the CLI suite and record the decisive check's run

### Requirement verification

- Parent R4 → CLI unit test (flags → client arguments; unchanged line format)
  plus the end-to-end check.
- Parent R6 → the named decisive check described above; count it successful
  only when the intended tests collect and exit cleanly with the real server
  running.
- Parent R2/R3 production-path cross-check → the unparameterized
  `main(["list"])` assertion through the same real server and client path.
- Parent R7 (CLI part) → README diff in the same change.
````


**Assistant** *(reasoning present)*

```json
{
  "schema_version": 1,
  "scenario_id": "tg05-fastapi-multi-consumer-decomposition",
  "assessment": {
    "sections": {
      "tasks/20260926-notes-query-capability/000-main.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "R1–R7 items",
            "quote": "R1 — The notes collection HTTP operation (`GET /notes/`) supports bounded pagination (server-enforced maximum page size), stable sorting (deterministic total order), and optional text filtering, per an approved written contract.",
            "why": "Every requirement carries a stable R-label and one sentence of scope, so the seven items scan cleanly and remain citable later without re-reading."
          },
          {
            "where": "R7 item",
            "quote": "service-facing docs (root `README.md`, and the notes-query specification if approved), `packages/notes_client/README.md`, and `apps/notes_cli/README.md`",
            "why": "The densest checklist entry: one item enumerates three documentation targets plus an approval condition, though it still parses as a list of paths."
          }
        ]
      },
      "tasks/20260926-notes-query-capability/000-main.md — Subtasks": {
        "grade": "readable",
        "findings": [
          {
            "where": "whole section",
            "quote": "- [ ] tasks/20260926-notes-query-capability/010-api-collection-query.md",
            "why": "Three single-line checkbox paths; the entire decomposition is visible in one glance and nothing needs unpacking."
          }
        ]
      },
      "tasks/20260926-notes-query-capability/000-main.md — Decisions pending plan approval": {
        "grade": "readable",
        "findings": [
          {
            "where": "D-item list",
            "quote": "D3 — Single `sort` parameter (`field` or `-field`); `id` ascending always appended as tie-break; default order `id` ascending.",
            "why": "Each of the nine decisions is one labeled line carrying its operative values, so the block scans decision by decision."
          },
          {
            "where": "intro paragraph",
            "quote": "Contract-level choices below are presented with tradeoffs in `## Execution plan` → `### Implementation decisions and open questions`.",
            "why": "The pointer tells the reader where the detailed rationale lives before they commit to the long plan, so this section summarizes rather than duplicates."
          }
        ]
      },
      "tasks/20260926-notes-query-capability/000-main.md — Supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "tests bullet",
            "quote": "Current tests are per-boundary and shallow: service tests assert only list shape and one POST route; the client test uses a fake transport; the CLI test uses a fake client.",
            "why": "One item mixes four facts (three per-side descriptions plus the gap); the conclusion motivating R6 arrives only in the item's second sentence."
          },
          {
            "where": "environment bullet",
            "quote": "No virtualenv or test dependencies exist in the workspace: runtime deps (`fastapi`, `databases`, `sqlalchemy`, `httpx`) are not installed, `pytest` is not declared in any pyproject, and `.gitignore` does not cover `notes.db`.",
            "why": "Three independent setup gaps share one compound item; building a setup checklist means unpacking a single bullet."
          },
          {
            "where": "assumption bullet",
            "quote": "Not yet verified (assumption to check during execution): whether the installed Starlette version runs the app lifespan",
            "why": "The section's one unverified assumption is flagged in its opening phrase, so it is findable on a scan rather than buried."
          }
        ]
      },
      "tasks/20260926-notes-query-capability/000-main.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "Design → contract table, `sort` row",
            "quote": "Primary sort field and direction; `id` ascending is always appended as final tie-break, so the total order is deterministic. Unknown value → 422.",
            "why": "The authoritative v1 contract sits in one four-row table a reader can scan and quote; the semantics cells carry two or three facts each but keep an arrow-and-clause rhythm that stays scannable."
          },
          {
            "where": "Implementation decisions and open questions, D-bullets",
            "quote": "D7 (end-to-end harness) — real uvicorn server on an ephemeral `127.0.0.1` port in the decisive check, added as a test dependency of the CLI app; the socket-level server is what makes this the production path (lifespan, real HTTP round trips, `NOTES_API_URL` construction).",
            "why": "Each D-bullet is a labeled mini-argument of four to six wrapped lines (choice, rationale, rejected alternative); ten in sequence is the section's heaviest stretch, but the D-labels keep it navigable rather than wall-like."
          },
          {
            "where": "Design → Verification strategy",
            "quote": "filter matching incl. literal `%`/`_`, combined parameters, 422s, and an unparameterized regression",
            "why": "Single items enumerate six or seven test concerns as comma chains; readable as enumerations, though the reader must hold several coverage facts per line."
          },
          {
            "where": "Design → Interpretation note",
            "quote": "Interpretation note: \"stable sorting\" means a deterministic total order (field plus `id` tie-break), not snapshot stability of offset pagination under concurrent writes; the latter is out of scope.",
            "why": "A load-bearing scope clarification is set off as its own labeled paragraph instead of being buried inside a list item, so it is hard to miss."
          }
        ]
      },
      "tasks/20260926-notes-query-capability/010-api-collection-query.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "first item",
            "quote": "`limit` (integer 1..100), `offset` (integer ≥ 0), `sort` (`id|title|description`, optionally `-`-prefixed for descending), `q` (case-insensitive literal substring on `title`).",
            "why": "One item restates the entire four-parameter contract; it is the densest entry, but each parameter keeps its own parenthetical and the five sibling items each carry a single concern."
          },
          {
            "where": "bounds item",
            "quote": "`limit` outside 1..100 is rejected with 422; malformed `offset` or unknown `sort` values are rejected with 422",
            "why": "Error semantics are grouped per mechanism with explicit status codes, so the rejection rules extract in one read."
          }
        ]
      },
      "tasks/20260926-notes-query-capability/010-api-collection-query.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "Tests block",
            "quote": "`limit=101` and `limit=0` → 422; `offset=-1` → 422;",
            "why": "Test coverage is laid out as short concrete sub-bullets rather than prose, so the suite's assertions are visible at a glance."
          },
          {
            "where": "Approach, CRUD bullet",
            "quote": "optional `where(notes.c.title.ilike(...))` with `%`, `_`, and the escape character escaped in the user value so matching stays literal; `order_by` on the requested column plus `notes.c.id.asc()` as tie-break; `offset`; `limit`.",
            "why": "One ~70-word item carries filter escaping, ordering, tie-break, offset, limit and the compat rule; the literal-escaping requirement — the easiest part to implement wrong — sits mid-item rather than leading it."
          },
          {
            "where": "Environment paragraph",
            "quote": "execution must first establish a test environment (no virtualenv or declared test dependencies exist) and run from an isolated working directory",
            "why": "Both operational preconditions are labeled and stated in two sentences, so the setup to-do is extractable in one pass."
          }
        ]
      },
      "tasks/20260926-notes-query-capability/020-client-query-parameters.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "whole section",
            "quote": "The no-argument call issues the same request as today (no query parameters) and returns the parsed JSON list — unchanged return type.",
            "why": "Four items of 90 words total, each a single concern with its compatibility clause; nothing here requires re-reading."
          }
        ]
      },
      "tasks/20260926-notes-query-capability/020-client-query-parameters.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "Approach, first bullet",
            "quote": "only when non-empty, so the unparameterized call stays byte-identical to today's request",
            "why": "The signature, the params-building rule and its compat rationale share one six-line item — dense, but single-purpose inside a 260-word section."
          },
          {
            "where": "Tests block",
            "quote": "the no-argument call sends no query string (regression) and returns the parsed JSON list.",
            "why": "Each test concern is its own sub-bullet, so the regression is separately visible from the serialization tests."
          }
        ]
      },
      "tasks/20260926-notes-query-capability/030-cli-query-flags-and-production-path.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "decisive-check item",
            "quote": "The named decisive end-to-end check runs the production path: a real uvicorn server serving the real app, notes seeded through the public POST route, the real `NotesClient` via `NOTES_API_URL`, and a real `main([...])` invocation with no injected test double",
            "why": "Five components plus the no-double constraint in one checklist item; it works as a summary, but it is the section's densest entry and the concrete steps live in the plan below."
          },
          {
            "where": "flag item",
            "quote": "`notes list` supports `--limit`, `--offset`, `--sort`, and `--filter` (parent decision D6), forwarding provided values to the client's parameters.",
            "why": "The remaining items each name one deliverable plus its parent decision, keeping the section otherwise single-concern."
          }
        ]
      },
      "tasks/20260926-notes-query-capability/030-cli-query-flags-and-production-path.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "decisive check sub-bullets",
            "quote": "This test traverses the real CLI parser → real client → real httpx → real TCP → real FastAPI app → SQLite.",
            "why": "The harness is broken into five short sub-bullets (start server, seed, set URL, run parameterized, run unparameterized) with a one-line path summary, so the decisive check's shape is scannable."
          },
          {
            "where": "Environment paragraph",
            "quote": "the end-to-end test needs `app` (from `src/`), `notes_client`, and `notes_cli` importable alongside `uvicorn` and `pytest`",
            "why": "Two distinct instructions (importability of three packages, isolated working directory) share one four-line paragraph, but both are labeled and short."
          }
        ]
      }
    },
    "navigation": {
      "grade": "navigable",
      "findings": [
        {
          "where": "all four files, Execution plan opening",
          "quote": "Status: Draft",
          "why": "Plan status is declared at the same position in every file, so a reader finds it without searching; the unchecked boxes are consistent with that status rather than misleading."
        },
        {
          "where": "child file headers",
          "quote": "Depends On: tasks/20260926-notes-query-capability/010-api-collection-query.md and tasks/20260926-notes-query-capability/020-client-query-parameters.md",
          "why": "Parent link and ordering constraints sit above the checklist in every subtask, so a reader knows where each file sits in the sequence before reading any plan content."
        },
        {
          "where": "000-main.md — Execution plan → Requirement verification",
          "quote": "R5 → process constraint made structural: 020 and 030 declare `Depends On: 010`",
          "why": "The parent maps each R-number to the subtask and evidence that proves it, closing the loop from requirement to plan without free search."
        },
        {
          "where": "decision blocks, all files",
          "quote": "Open question: none at requirement level.",
          "why": "Every file ends its decision block with an explicit open-questions statement, so the reader never has to infer whether questions remain."
        }
      ]
    },
    "mistakes": [
      {
        "where": "000-main.md — Supporting facts, tests bullet",
        "quote": "Current tests are per-boundary and shallow: service tests assert only list shape and one POST route; the client test uses a fake transport; the CLI test uses a fake client.",
        "why": "One list item mixes four facts (three per-side test descriptions plus the identified gap), forcing the reader to hold all three before reaching the conclusion that motivates R6."
      },
      {
        "where": "000-main.md — Supporting facts, environment bullet",
        "quote": "No virtualenv or test dependencies exist in the workspace: runtime deps (`fastapi`, `databases`, `sqlalchemy`, `httpx`) are not installed, `pytest` is not declared in any pyproject, and `.gitignore` does not cover `notes.db`.",
        "why": "Three independent setup gaps bundled into one compound item; a reader extracting the setup checklist must decompose the bullet themselves."
      },
      {
        "where": "000-main.md — Execution plan → Implementation decisions and open questions, final item",
        "quote": "Minor version bumps (`notes-client`, `notes-cli` 0.1.0 → 0.2.0) are optional since both changes are backward-compatible; not required by this task.",
        "why": "An unlabeled non-decision trails the D1–D9 list, breaking its labeling pattern; a reader scanning D-numbers can misread it as part of D9 or overlook that version policy is a separate open choice."
      },
      {
        "where": "010-api-collection-query.md — Execution plan → Approach, CRUD bullet",
        "quote": "with `%`, `_`, and the escape character escaped in the user value so matching stays literal; `order_by` on the requested column plus `notes.c.id.asc()` as tie-break; `offset`; `limit`.",
        "why": "The escaped-literal requirement — the clause most likely to be implemented wrong — is buried mid-item among ordering and pagination facts in a single ~70-word list item."
      },
      {
        "where": "010-api-collection-query.md — Requirements checklist, first item",
        "quote": "`limit` (integer 1..100), `offset` (integer ≥ 0), `sort` (`id|title|description`, optionally `-`-prefixed for descending), `q` (case-insensitive literal substring on `title`).",
        "why": "The full contract is restated from the parent's table, creating a second authoritative-looking copy of load-bearing values; when the contract changes, the two copies must be edited in sync or they silently diverge."
      },
      {
        "where": "030-cli-query-flags-and-production-path.md — Requirements checklist, decisive-check item",
        "quote": "a real uvicorn server serving the real app, notes seeded through the public POST route, the real `NotesClient` via `NOTES_API_URL`, and a real `main([...])` invocation with no injected test double",
        "why": "A single checklist line carries five harness components plus the no-double constraint; the actionable steps exist only in the plan below, so the item overstates what a checklist entry can hold."
      },
      {
        "where": "000-main.md — Execution plan → Additional implementation verification, final item",
        "quote": "None beyond the above; the per-child plans carry the focused evidence.",
        "why": "A contentless bullet occupies a scan slot in a section otherwise reserved for concrete verification steps; the reader checks it for substance and finds none."
      }
    ],
    "summary": "The task set is consistently easy to work with. Every file opens with an outcome statement and an R-labeled requirements checklist, and every Execution plan repeats the same subsection skeleton (approach, decisions, documentation, task checklist, requirement verification), so the outcome, the constraints, the frozen contract (one four-row table in the parent plan), the explicit 'open questions: none' statements, and the Draft status are all reachable from headings alone. Density concentrates where the content demands it — the ten D-bullets in the parent plan and a few multi-fact items — and labels (R-numbers, D-numbers, parent cross-references) keep even those stretches navigable without re-reading. The residual costs are local: several list items bundle three or more facts (the per-side test summary, the environment-gap bullet, the CRUD bullet with its literal-escaping clause buried mid-item), the contract values are duplicated between the parent table and 010's checklist, one unlabeled item trails the D1–D9 list, and one decisive-check checklist entry holds more than a checklist line should. None of these force re-reading; they are friction points inside an otherwise well-structured set."
  }
}
```
