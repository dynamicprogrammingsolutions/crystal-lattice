# Session — tg05-fastapi-multi-consumer-decomposition · file-readability-assessment-glm-max-s0 · glm max

- Run: `20261102T104249.288634Z-task-guidance-file-readability-tg05-fastapi-multi-consumer-decomposition-glm-max-s0-7f5ec7e8`
- Model: glm-5.3-flash (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-c440c4f661a7.md) — captured (original SHA-256 `54d87b13cce512df…`)
- Config: [glm-assessor-max](../../../../../../shared/configs/glm-assessor-max.json)
- Activity: 3 messages · 0 tool calls · 0 tool results
- Usage: 0 input · 0 cached · 0 output · provider cost $0.0000000

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

#### tasks/20261101-notes-query-capability/000-main.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261101-notes-query-capability/000-main.md — Requirements checklist | 174 | 0 | 0 | 6 | 39 | 0 | 0 | 0 | 9 |
| tasks/20261101-notes-query-capability/000-main.md — Subtasks | 71 | 1 | 21 | 3 | 19 | 0 | 0 | 0 | 8 |
| tasks/20261101-notes-query-capability/000-main.md — Questions and decisions | 119 | 1 | 68 | 2 | 13 | 0 | 0 | 0 | 2 |
| tasks/20261101-notes-query-capability/000-main.md — Supporting details | 599 | 5 | 26 | 15 | 14 | 0 | 5 | 0 | 51 |
| tasks/20261101-notes-query-capability/000-main.md — Implementation plan | 1167 | 4 | 78 | 38 | 14 | 9 | 6 | 0 | 60 |

#### tasks/20261101-notes-query-capability/010-api-query-contract.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261101-notes-query-capability/010-api-query-contract.md — Requirements checklist | 171 | 1 | 10 | 5 | 36 | 0 | 0 | 0 | 7 |
| tasks/20261101-notes-query-capability/010-api-query-contract.md — Supporting details | 269 | 3 | 81 | 9 | 12 | 0 | 0 | 0 | 35 |
| tasks/20261101-notes-query-capability/010-api-query-contract.md — Implementation plan | 427 | 6 | 101 | 7 | 16 | 4 | 0 | 0 | 36 |

#### tasks/20261101-notes-query-capability/020-client-query-support.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261101-notes-query-capability/020-client-query-support.md — Requirements checklist | 125 | 1 | 18 | 4 | 41 | 0 | 0 | 0 | 6 |
| tasks/20261101-notes-query-capability/020-client-query-support.md — Supporting details | 240 | 3 | 43 | 9 | 14 | 0 | 0 | 0 | 26 |
| tasks/20261101-notes-query-capability/020-client-query-support.md — Implementation plan | 354 | 6 | 87 | 8 | 13 | 4 | 0 | 0 | 14 |

#### tasks/20261101-notes-query-capability/030-cli-query-command.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261101-notes-query-capability/030-cli-query-command.md — Requirements checklist | 120 | 1 | 15 | 4 | 39 | 0 | 0 | 0 | 6 |
| tasks/20261101-notes-query-capability/030-cli-query-command.md — Supporting details | 293 | 3 | 60 | 8 | 13 | 0 | 0 | 0 | 33 |
| tasks/20261101-notes-query-capability/030-cli-query-command.md — Implementation plan | 480 | 6 | 134 | 9 | 18 | 4 | 0 | 0 | 26 |

The produced task files:

### tasks/20261101-notes-query-capability/000-main.md

````markdown
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
````

### tasks/20261101-notes-query-capability/010-api-query-contract.md

````markdown
# API: define and stabilize the notes query contract

Add optional query parameters for bounded pagination, stable sorting, and
optional text filtering to `GET /notes/`, keep the unparameterized response
identical to today, write the contract into the maintained public docs, and
pin it with route tests. This subtask completes before either consumer builds
on the contract.

Parent Task: tasks/20261101-notes-query-capability/000-main.md

## Requirements checklist

- [ ] `GET /notes/` accepts the approved optional query parameters implementing bounded pagination, stable sorting, and optional text filtering; out-of-range or disallowed values are rejected with 422. Parameter specifics are the parent plan's proposed contract, binding once approved.
- [ ] When any query parameter is supplied, results return in a deterministic total order: the requested sort key with unique `id` as final tiebreaker, `id` ascending when sort is not given.
- [ ] The unparameterized `GET /notes/` response is unchanged — every note as a JSON array, content, shape, and ordering exactly as today — proven by regression evidence.
- [ ] The contract (parameters, defaults, bounds, ordering rule, response shape, error behavior) is documented in the root `README.md` in the same change, with OpenAPI reflecting it from route code.
- [ ] Route tests through the real app prove: page bounds and cap enforcement, deterministic ordering including the tiebreaker, text filtering, combined parameters, and the unparameterized regression case.

Depends On: none. Must complete before
`tasks/20261101-notes-query-capability/020-client-query-support.md` and
`tasks/20261101-notes-query-capability/030-cli-query-command.md` start.

## Supporting details

**Proposed contract slice (binding once the parent plan is approved).**
Optional parameters on `GET /notes/`: `limit` (int 1–100, default 20 when any
parameter is used), `offset` (int ≥ 0, default 0), `sort` (one of `id`,
`title`, `description`, optional leading `-` for descending, default `id`
ascending), `q` (case-insensitive substring on title or description). Response
stays a bare JSON array of note objects, up to `limit` items, empty array for
no matches; no envelope, no total. Supplying no parameters reproduces today's
behavior exactly.

**Current code facts.**

- `src/app/api/notes.py:8-10` — `read_all_notes()` returns `crud.get_all()`;
  no parameters, no ordering. `src/app/api/crud.py:4-5` — `get_all()` fetches
  the whole table.
- Schema (`src/app/db.py`): `id` (PK), `title` (String(50)),
  `description` (String(50)). No timestamps, so the sort whitelist is limited
  to these three columns.
- Stack: `databases` + SQLAlchemy core; selects support
  `.where()/.order_by()/.offset()/.limit()`; `ilike` is available for `q`.
- `fastapi.Query(ge=..., le=...)` produces the framework's standard 422
  responses; the app has no other custom error surface today.
- Router prefix is `/notes` (`src/app/main.py:15`).

**Harness facts.**

- `src/tests/conftest.py` builds `TestClient(app)` without a context manager
  while `database.connect()` runs in the lifespan hook; the connection may not
  be established in the current suite. Route tests should use
  `with TestClient(app)` or otherwise ensure connection — verify during
  execution.
- Importing `app.db` creates `./notes.db` in the process CWD at import time;
  the file is not gitignored. Keep it out of commits.
- The SQLite DB path is CWD-relative; irrelevant for in-process TestClient
  tests, critical for any subprocess-served run (020/030).
- `docs/development/index.md` records that no notes-query specification
  exists. Do not create a spec page under `docs/` unless the parent plan's
  documentation decision is changed by approval (smallest-structure rule).

## Implementation plan

Status: Draft

**Design.** Extend `read_all_notes` with the four optional `fastapi.Query`
parameters. Add a query path in `crud` that applies `where` (for `q`, as
`OR(ilike(title), ilike(description))`), `order_by` (whitelisted column,
descending on `-` prefix, then `id` ascending as tiebreaker), `offset`, and
`limit` — applied only when at least one parameter is supplied. The
unparameterized request keeps calling today's `get_all()` branch unchanged, so
preservation holds by construction, not by coincidence. Validate `sort`
against the whitelist in the handler (422 on unknown values) and bounds via
`Query` constraints.

**Order logic.** Implementation, tests, and README contract section land as
one reviewed change; the milestone is a stable, documented, pinned contract.
Nothing downstream may start until this subtask's requirements are checked.

**Verification.** Decisive evidence: route tests through `app.main.app` via
TestClient on a seeded temporary SQLite DB, crossing routing, validation,
handler, and serialization at the public boundary. Cases: unparameterized
response equals the full seeded set exactly; pagination across multiple pages
reconstructs the set without gaps or duplicates; `limit=100` accepted,
`limit=101`, `limit=0`, and negative rejected with 422; `sort=title` with
duplicate titles shows the `id` tiebreaker and is stable across repeated
requests; `sort=-title` reverses; `q` matches case-insensitively in either
field; `q` with no matches returns `[]`; combined `q`+`sort`+`limit`+`offset`
behaves as the intersection. Deliberately not covered here: real socket
transport (covered in 020/030) and consumer surfaces.

**Risks.** ASCII-only case folding for `q` (document, don't over-claim);
unparameterized regression (pinned by the exact-response test); import-time
`notes.db` artifact (keep out of commits); lifespan/connection harness
question (verify and use `with TestClient(app)`).

### Implementation decisions and open questions

Governed by the parent plan's decisions 1–6 and 12. Local reversible choices
(helper naming in `crud`, test file layout) resolve at execution.

### Documentation

Root `README.md` gains the query contract in this same change, replacing the
"returns every note as a JSON array" framing with current supported behavior.
OpenAPI updates itself from the route signature; never hand-edit generated
output.

### Task checklist

- [ ] Add query parameters to `read_all_notes` and the conditional query path in `crud`, preserving the unparameterized branch.
- [ ] Add route tests for the cases listed under Verification.
- [ ] Update root `README.md` with the contract.
- [ ] Existing API suite stays green.

### Requirement verification

- Query capability and its bounds/order/filter semantics → the route tests
  named above through the real app. Not covered: real network transport,
  consumer surfaces.
- Contract stability → README section plus OpenAPI parameters published in the
  same reviewed change, tests pinning behavior, and this subtask completing
  before 020/030 start. Not covered: release/versioning mechanics (the fixture
  has none).
- Unparameterized preservation → the exact-response regression test on seeded
  rows. Not covered: client request shape (020's evidence).
````

### tasks/20261101-notes-query-capability/020-client-query-support.md

````markdown
# Client: expose the notes query capability on NotesClient

Expose the approved query capability on `NotesClient` so any Python consumer
can paginate, sort, and filter against the stable HTTP contract, without
changing the existing unparameterized call behavior, and prove the client's
contract conformance against the real running service.

Parent Task: tasks/20261101-notes-query-capability/000-main.md

## Requirements checklist

- [ ] `NotesClient` exposes the query capability with parameters matching the approved contract, mapping them to the stable HTTP contract and omitting any parameter not supplied.
- [ ] Existing `list_notes()` behavior is preserved: a parameter-free request to `/notes/` returning the parsed JSON list — proven by request-shape regression evidence.
- [ ] An integration test proves the real client against the real running service over real HTTP, covering at least one paginated, one sorted, and one filtered round trip. This is the decisive check for this subtask; fake-transport tests stay supporting evidence only.
- [ ] `packages/notes_client/README.md` describes the new surface in the same change.

Depends On: `tasks/20261101-notes-query-capability/010-api-query-contract.md`
(the contract must be stable before this package relies on it).
Depended on by: `tasks/20261101-notes-query-capability/030-cli-query-command.md`.

## Supporting details

**Proposed client surface (binding once the parent plan is approved).**
`list_notes(limit=None, offset=None, sort=None, q=None)`. Unset parameters are
omitted from the query string entirely, so an unparameterized call sends
exactly today's request (`GET /notes/` with no query component) and returns
the parsed JSON list.

**Current code facts.**

- `packages/notes_client/notes_client/client.py` — `NotesClient(transport)`;
  `from_environment()` builds an `httpx.Client` from `NOTES_API_URL` (default
  `http://127.0.0.1:8000`); `list_notes()` returns
  `self.transport.get("/notes/").json()`.
- Package `pyproject.toml`: `notes-client` 0.1.0, depends on `httpx` only.
- Existing tests (`packages/notes_client/tests/`) use a fake transport whose
  `get()` accepts `**kwargs`; they can verify call mapping but not contract
  conformance.
- Error-path behavior: the client does not raise on HTTP error statuses today.
  Parent decision 9 keeps it that way — do not add `raise_for_status` in this
  task; record as a possible follow-up instead.

**Harness facts.**

- No `uvicorn` is declared anywhere in the fixture; serving the real app in
  the integration test requires introducing it (parent plan decision 11:
  recommend root `pyproject.toml` dependencies).
- The service DB path is CWD-relative (`sqlite:///./notes.db`): launch the
  server subprocess from a temporary working directory and wait for readiness
  before testing.
- Seed data through the real HTTP API (`POST /notes/` with plain `httpx`) so
  the fixture itself stays on the production path.
- Keep this integration harness local to `packages/notes_client/tests/`;
  `packages/` and `apps/` are independently maintained and share no test code.
- Recommend bumping `notes-client` to 0.2.0 in this change (additive public
  surface on a 0.x package) — parent plan decision 10.

## Implementation plan

Status: Draft

**Design.** Extend `list_notes()` with the four optional keyword parameters.
Build the request's `params` dict from supplied values only and pass it to the
transport `get`; absent parameters produce the same parameter-free request as
today. Return the parsed JSON list unchanged.

**Order logic.** Starts only after 010 completes (stable contract, real
service to conform to). Its own milestone — client surface implemented and
conformance-proven — gates 030.

**Verification.** Decisive evidence: an integration test that launches the
real app via a `uvicorn` subprocess (temporary CWD, ephemeral port, readiness
wait), seeds notes over HTTP, then drives the real `NotesClient` (via
`from_environment()` with `NOTES_API_URL` pointed at the test server) through
paginated, sorted, and filtered calls, asserting results match the seeded
data under the approved contract semantics. Request-shape regression: extend
the fake-transport unit test to capture the request and assert that
`list_notes()` with no arguments issues a query-string-free `GET /notes/`.
Deliberately not covered: CLI rendering (030), hosted deployment.

**Risks.** Contract drift between package and service — caught by the
conformance test against the real service; harness flakiness from port or
readiness races — use an ephemeral port and poll readiness with a bounded
timeout; `notes.db` leakage — temporary CWD for the server process.

### Implementation decisions and open questions

Governed by parent plan decisions 4–7, 9–11. Local reversible choices (params
dict construction, fixture structure) resolve at execution.

### Documentation

`packages/notes_client/README.md` documents the new parameters and their
semantics in this same change (audience: Python consumers of the package).

### Task checklist

- [ ] Extend `list_notes()` with optional keyword parameters; omit unset values from the query string.
- [ ] Add the real-service integration test (uvicorn subprocess, temp CWD, seeded over HTTP).
- [ ] Extend the fake-transport unit test with the request-shape regression case.
- [ ] Update `packages/notes_client/README.md`; bump package to 0.2.0.
- [ ] Existing client suite stays green.

### Requirement verification

- Client exposes the capability against the stable contract → the real-client
  integration test over real HTTP. Not covered: CLI rendering.
- Unparameterized preservation → the request-shape regression case plus the
  existing suite staying green. Not covered: API response content (010's
  evidence).
- Documentation → the changed `packages/notes_client/README.md` page, reviewed
  in the same change as the code.
````

### tasks/20261101-notes-query-capability/030-cli-query-command.md

````markdown
# CLI: query flags and the production-path proof

Expose the query capability to CLI users as flags on the `list` command and
prove the production client-to-service path end to end: a real CLI invocation
through the production `NotesClient` against a real running service, with no
test doubles in that path.

Parent Task: tasks/20261101-notes-query-capability/000-main.md

## Requirements checklist

- [ ] CLI users can query notes with pagination, sorting, and filtering flags on `notes list`, passed through to the production client; output rendering is unchanged.
- [ ] The decisive end-to-end check traverses the real production path — CLI invocation → production `NotesClient.from_environment()` → running service over HTTP — and asserts that stdout reflects the requested paging, sorting, and filtering. Fake-client unit tests remain supporting evidence only.
- [ ] Existing `notes list` output behavior is preserved for the unparameterized case, covered by both the unit regression and the end-to-end check.
- [ ] `apps/notes_cli/README.md` documents the new flags in the same change.

Depends On: `tasks/20261101-notes-query-capability/010-api-query-contract.md`
and `tasks/20261101-notes-query-capability/020-client-query-support.md`
(the CLI consumes the client method against the stable contract).

## Supporting details

**Proposed CLI surface (binding once the parent plan is approved).** The
`list` subcommand gains `--limit` (int ≥ 1), `--offset` (int ≥ 0), `--sort`
(choices: `id`, `title`, `description` and their `-`-prefixed descending
forms), and `--query` (free text, mapped to the client's `q`). argparse
validates ranges and choices locally so normal CLI use never triggers a 422;
values pass through to `client.list_notes(...)`.

**Current code facts.**

- `apps/notes_cli/cli.py` — `main(argv=None, client=None)` builds an
  argparse parser with a required `list` subcommand; `list_command(client)`
  prints `{id}: {title}` per note from `client.list_notes()`. A `client`
  argument already allows injection, but the decisive check uses the
  production client, not an injected double.
- `apps/notes_cli/pyproject.toml` — console script
  `notes = "notes_cli.cli:main"`; declares **no dependencies** despite
  importing `notes_client` (parent plan decision 10: add the dependency and
  report it).
- **Pre-existing defects to fix incidentally and report:** the console script
  targets a `notes_cli` package directory that does not exist
  (`apps/notes_cli/` contains `cli.py` directly), and
  `apps/notes_cli/tests/test_cli.py` calls `list_command` without importing
  it, so the current CLI test cannot pass as shipped. 030 makes the real CLI
  code importable in tests and repairs the missing import; that repair is
  reported, not silent.
- The CLI module has no `__main__` block, so the automated decisive check
  invokes `main(argv)` in-process with the production client; the installed
  `notes` console script remains the manual equivalent.
- Existing CLI tests use a fake client (`tests/conftest.py`); kept as
  rendering-regression evidence only.

**Harness facts.**

- Real-service runs need `uvicorn` (introduced per parent plan decision 11)
  and a subprocess launched from a temporary working directory (the service
  DB path is CWD-relative), with readiness polling and an ephemeral port.
- Seed notes over real HTTP (`POST /notes/`) before invoking the CLI.
- Keep this end-to-end harness local to `apps/notes_cli/tests/`; no shared
  test code with the client package.

## Implementation plan

Status: Draft

**Design.** Extend the `list` subparser with `--limit`, `--offset`, `--sort`,
and `--query`, with argparse-level validation (type/range/choices) matching
the approved contract so user errors surface locally with a clean message and
nonzero exit. Pass validated values through to the production client method;
leave `list_command` rendering as is.

**Order logic.** Last subtask: consumes the client method (020) against the
stable contract (010). Its milestone — the production path proven end to end —
completes the feature.

**Verification.** Decisive evidence, named exactly: start the real app with a
`uvicorn` subprocess from a temporary CWD on an ephemeral port; poll
readiness; seed at least five notes over HTTP including duplicate-title rows
and filterable text; set `NOTES_API_URL` to the test server; invoke
`main(["list", "--limit", "2", "--offset", "2", "--sort", "title",
"--query", "<term>"])` (and variants) with the production
`NotesClient.from_environment()`; assert stdout lines match the expected
page of the filtered, title-sorted set, and that the unparameterized
`main(["list"])` output equals today's `{id}: {title}` rendering of every
note. No test doubles appear in this path. Supporting evidence: the repaired
fake-client unit test for rendering. Deliberately not covered: hosted
deployment, concurrency, and the console-script packaging itself (the missing
`notes_cli` package directory is fixed only as far as tests require; if full
console-script installability is wanted, that is a follow-up).

**Risks.** The e2e harness is the most complex test in the feature (process
lifecycle, ports, readiness) — bound all waits with timeouts and clean up the
subprocess; scope creep via the pre-existing packaging defects — fix the
minimum needed for the decisive check and report the rest; regression risk on
unparameterized output — covered by the e2e case plus the unit test.

### Implementation decisions and open questions

Governed by parent plan decisions 4–8 and 10–11. Local reversible choices
(exact flag names if `--query` feels wrong, validation messages) resolve at
execution; flag names are user-visible, so any deviation is reported.

### Documentation

`apps/notes_cli/README.md` documents the new flags with examples in this same
change (audience: CLI users).

### Task checklist

- [ ] Add `--limit`, `--offset`, `--sort`, `--query` to the `list` subcommand with argparse validation; pass through to the production client.
- [ ] Add the end-to-end production-path test exactly as named under Verification.
- [ ] Fix the missing `list_command` import in `test_cli.py` and make the CLI module importable; report both repairs.
- [ ] Add the undeclared `notes-client` dependency to `apps/notes_cli/pyproject.toml`; report it.
- [ ] Update `apps/notes_cli/README.md`.
- [ ] Existing CLI suite stays green.

### Requirement verification

- CLI exposes the capability and proves the production client-to-service path
  → the named end-to-end check; it is the only check that traverses CLI,
  client, and service together, which is why it cannot be waived or replaced
  by the per-side tests. Not covered: hosted deployment, concurrency.
- Unparameterized CLI output preserved → the `main(["list"])` e2e case plus
  the fake-client rendering unit test. Not covered: API or client internals
  (010/020 evidence).
- Documentation → the changed `apps/notes_cli/README.md` page, reviewed in the
  same change as the code.
````


**Assistant** *(reasoning present)*

```json
{
  "schema_version": 1,
  "scenario_id": "tg05-fastapi-multi-consumer-decomposition",
  "assessment": {
    "sections": {
      "tasks/20261101-notes-query-capability/000-main.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "third checklist item",
            "quote": "Current unparameterized behavior is preserved: `GET /notes/` without parameters still returns every note as a JSON array with today's behavior, and existing `NotesClient.list_notes()` still sends the same parameter-free request and returns the parsed JSON list.",
            "why": "The longest item (39 words) bundles two components' preservation requirements and two owners into one checkbox; it is still one coherent requirement, so the six-item list stays scannable."
          },
          {
            "where": "all six items",
            "quote": "Owner: `tasks/20261101-notes-query-capability/010-api-query-contract.md`",
            "why": "Every requirement names its owning subtask inline, so accountability is visible without leaving the section."
          }
        ]
      },
      "tasks/20261101-notes-query-capability/000-main.md — Subtasks": {
        "grade": "readable",
        "findings": [
          {
            "where": "trailing paragraph",
            "quote": "Order is strict: 010 → 020 → 030. The `Depends On` declarations are the operative constraints; filename numbering only reflects them.",
            "why": "The load-bearing sequencing rule is stated once in 21 words directly under the three subtask bullets — nothing to dig for."
          }
        ]
      },
      "tasks/20261101-notes-query-capability/000-main.md — Questions and decisions": {
        "grade": "readable",
        "findings": [
          {
            "where": "opening paragraph",
            "quote": "There are no unresolved requirement questions: the capability, the three boundaries it must span, the preservation constraint, and both sequencing constraints (contract stability, production-path proof) are fixed by the request.",
            "why": "A 68-word paragraph carries three messages — no open questions, where the decisions live, when they are approved — before the two 'most consequential' bullets; one careful read suffices, but it is the densest prose in the section."
          }
        ]
      },
      "tasks/20261101-notes-query-capability/000-main.md — Supporting details": {
        "grade": "readable",
        "findings": [
          {
            "where": "Verification shape table",
            "quote": "Product connection | Owner | Decisive check | Deliberately not covered there",
            "why": "The four-column table maps each requirement's proof to its owner and its exclusions in one scannable row — the strongest presentation in the file set."
          },
          {
            "where": "'Known harness facts, defects, and assumptions' list",
            "quote": "The CLI's console script points at a `notes_cli` package directory that does not exist (`apps/notes_cli/` contains `cli.py` directly), and `apps/notes_cli/tests/test_cli.py` calls `list_command` without importing it",
            "why": "One bullet merges two CLI defects plus a repair-and-report directive; the other seven bullets stay single-topic, so the list overall holds up."
          },
          {
            "where": "'Definitions used by this task'",
            "quote": "Stable sorting: a deterministic total order (requested sort key with unique `id` as final tiebreaker) so pages never skip or repeat rows across offsets.",
            "why": "Four one-line definitions give the section's vocabulary a fixed, look-up-able reference point."
          }
        ]
      },
      "tasks/20261101-notes-query-capability/000-main.md — Implementation plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "'Proposed query contract' table",
            "quote": "`limit` | int, 1–100 | 20 | Page size; 0, negative, or >100 → 422",
            "why": "The binding contract is a four-column table — range, default, semantics per row — the most extractable rendering of the contract anywhere in the set; it carries the 1,167-word section."
          },
          {
            "where": "'Implementation decisions and open questions' numbered list",
            "quote": "11. Test harness: introduce `uvicorn` (recommended: root `pyproject.toml` dependencies) to serve the real app in 020/030 checks. The alternative — `httpx.ASGITransport` — is rejected for the production-path check because it skips the real server and lifespan; it also needs manual `database.connect()` handling.",
            "why": "Each of the 12 decisions packs choice, rejected alternative, and recommendation into one item; the consistent 'Recommend …' pattern keeps it workable, but items like 11 reward a second pass."
          },
          {
            "where": "'Order logic and milestones' paragraph",
            "quote": "010 first because both other components consume its contract, and the request requires the contract to be stable before consumers rely on it.",
            "why": "The section's longest paragraph (78 words) is a single causal narrative with a clear arc; one read is enough."
          }
        ]
      },
      "tasks/20261101-notes-query-capability/010-api-query-contract.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "first checklist item",
            "quote": "Parameter specifics are the parent plan's proposed contract, binding once approved.",
            "why": "The item mixes the requirement with a governance pointer, so the actual parameter values live outside this file; acceptable as a pointer, but the checkbox does not stand alone."
          },
          {
            "where": "fifth checklist item",
            "quote": "Route tests through the real app prove: page bounds and cap enforcement, deterministic ordering including the tiebreaker, text filtering, combined parameters, and the unparameterized regression case.",
            "why": "Five test concerns share one 36-word checkbox via a colon list; parseable, but it is the densest item in the section."
          }
        ]
      },
      "tasks/20261101-notes-query-capability/010-api-query-contract.md — Supporting details": {
        "grade": "partial",
        "findings": [
          {
            "where": "'Proposed contract slice' paragraph",
            "quote": "Optional parameters on `GET /notes/`: `limit` (int 1–100, default 20 when any parameter is used), `offset` (int ≥ 0, default 0), `sort` (one of `id`, `title`, `description`, optional leading `-` for descending, default `id` ascending), `q` (case-insensitive substring on title or description).",
            "why": "This file's central data — the four-parameter contract — is an 81-word run-on paragraph; extracting any single parameter's range and default requires re-reading, while the parent file renders the identical data as a scannable table."
          },
          {
            "where": "'Current code facts' list",
            "quote": "`src/app/api/notes.py:8-10` — `read_all_notes()` returns `crud.get_all()`; no parameters, no ordering.",
            "why": "Five short, file-anchored bullets are easy to scan and verify against the code — the rest of the section does not strain."
          }
        ]
      },
      "tasks/20261101-notes-query-capability/010-api-query-contract.md — Implementation plan": {
        "grade": "partial",
        "findings": [
          {
            "where": "Verification paragraph",
            "quote": "Cases: unparameterized response equals the full seeded set exactly; pagination across multiple pages reconstructs the set without gaps or duplicates; `limit=100` accepted, `limit=101`, `limit=0`, and negative rejected with 422; `sort=title` with duplicate titles shows the `id` tiebreaker and is stable across repeated requests;",
            "why": "Eight-plus required test cases chained with semicolons inside a ~101-word paragraph — the checklist shape this content wants is presented as prose, so enumerating the cases forces re-reading."
          },
          {
            "where": "Design paragraph",
            "quote": "Add a query path in `crud` that applies `where` (for `q`, as `OR(ilike(title), ilike(description))`), `order_by` (whitelisted column, descending on `-` prefix, then `id` ascending as tiebreaker), `offset`, and `limit` — applied only when at least one parameter is supplied.",
            "why": "One sentence carries four parentheticals plus the conditional rule; it yields on a second read, but a first pass does not hold it."
          },
          {
            "where": "bold-led structure",
            "quote": "**Design.** … **Order logic.** … **Verification.** … **Risks.**",
            "why": "Four labeled paragraphs plus titled subsections keep the 427 words navigable despite the dense Verification block."
          }
        ]
      },
      "tasks/20261101-notes-query-capability/020-client-query-support.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "third checklist item",
            "quote": "An integration test proves the real client against the real running service over real HTTP, covering at least one paginated, one sorted, and one filtered round trip. This is the decisive check for this subtask; fake-transport tests stay supporting evidence only.",
            "why": "The 41-word item stacks the requirement, its decisiveness, and the demotion of fake tests; each clause is short, so one pass holds it."
          }
        ]
      },
      "tasks/20261101-notes-query-capability/020-client-query-support.md — Supporting details": {
        "grade": "readable",
        "findings": [
          {
            "where": "'Proposed client surface' paragraph",
            "quote": "`list_notes(limit=None, offset=None, sort=None, q=None)`. Unset parameters are omitted from the query string entirely, so an unparameterized call sends exactly today's request (`GET /notes/` with no query component) and returns the parsed JSON list.",
            "why": "Signature first, then the one semantic rule that matters — 43 words that read in a single pass."
          },
          {
            "where": "'Harness facts' list",
            "quote": "Recommend bumping `notes-client` to 0.2.0 in this change (additive public surface on a 0.x package) — parent plan decision 10.",
            "why": "A versioning decision sits inside the harness list; it does not block reading the section, but it is filed under the wrong heading."
          }
        ]
      },
      "tasks/20261101-notes-query-capability/020-client-query-support.md — Implementation plan": {
        "grade": "partial",
        "findings": [
          {
            "where": "Verification paragraph",
            "quote": "an integration test that launches the real app via a `uvicorn` subprocess (temporary CWD, ephemeral port, readiness wait), seeds notes over HTTP, then drives the real `NotesClient` (via `from_environment()` with `NOTES_API_URL` pointed at the test server) through paginated, sorted, and filtered calls, asserting results match the seeded data under the approved contract semantics",
            "why": "The decisive procedure — five ordered setup steps plus assertions — is one ~87-word sentence with nested parentheticals; a reader implementing it must re-read to reconstruct the sequence."
          },
          {
            "where": "Risks paragraph",
            "quote": "harness flakiness from port or readiness races — use an ephemeral port and poll readiness with a bounded timeout; `notes.db` leakage — temporary CWD for the server process.",
            "why": "Three unrelated risk–mitigation pairs are chained with semicolons in one paragraph; each pair is short, but the chain blurs where one risk ends and the next begins."
          }
        ]
      },
      "tasks/20261101-notes-query-capability/030-cli-query-command.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "second checklist item",
            "quote": "CLI invocation → production `NotesClient.from_environment()` → running service over HTTP",
            "why": "The arrow chain renders the production path at a glance inside the checkbox — the clearest requirement statement in the set."
          }
        ]
      },
      "tasks/20261101-notes-query-capability/030-cli-query-command.md — Supporting details": {
        "grade": "readable",
        "findings": [
          {
            "where": "'Pre-existing defects to fix incidentally and report' bullet",
            "quote": "the console script targets a `notes_cli` package directory that does not exist (`apps/notes_cli/` contains `cli.py` directly), and `apps/notes_cli/tests/test_cli.py` calls `list_command` without importing it, so the current CLI test cannot pass as shipped.",
            "why": "Two separate defects and their shared repair stance occupy one ~60-word bullet; a reader must re-read to attribute each defect, though the bold lead-in flags the item's importance."
          },
          {
            "where": "'Proposed CLI surface' paragraph",
            "quote": "The `list` subcommand gains `--limit` (int ≥ 1), `--offset` (int ≥ 0), `--sort` (choices: `id`, `title`, `description` and their `-`-prefixed descending forms), and `--query` (free text, mapped to the client's `q`).",
            "why": "Four flags with types packed into a 60-word paragraph; the per-flag parentheticals keep it parseable without re-reading."
          }
        ]
      },
      "tasks/20261101-notes-query-capability/030-cli-query-command.md — Implementation plan": {
        "grade": "partial",
        "findings": [
          {
            "where": "Verification paragraph",
            "quote": "start the real app with a `uvicorn` subprocess from a temporary CWD on an ephemeral port; poll readiness; seed at least five notes over HTTP including duplicate-title rows and filterable text; set `NOTES_API_URL` to the test server; invoke `main([\"list\", \"--limit\", \"2\", \"--offset\", \"2\", \"--sort\", \"title\", \"--query\", \"<term>\"])` (and variants)",
            "why": "At 134 words this is the longest paragraph in the file set: an ordered, 'named exactly' procedure, its assertions, its scope exclusions, and its supporting evidence all in one semicolon-chained block; executing it requires re-reading to recover the step order — a numbered list is the natural shape."
          },
          {
            "where": "'Requirement verification' first bullet",
            "quote": "it is the only check that traverses CLI, client, and service together, which is why it cannot be waived or replaced by the per-side tests. Not covered: hosted deployment, concurrency.",
            "why": "Each bullet stacks requirement, evidence, an exclusivity argument, and exclusions; the content is load-bearing, but these are the densest items in the file."
          }
        ]
      }
    },
    "navigation": {
      "grade": "navigable",
      "findings": [
        {
          "where": "all four files",
          "quote": "## Requirements checklist … ## Supporting details … ## Implementation plan",
          "why": "Every file uses the same section skeleton (the parent adds Subtasks and Questions), so a reader knows where the outcome, the context, and the plan live in each file without searching."
        },
        {
          "where": "000-main Subtasks and each subtask's Depends On line",
          "quote": "Depends On: `tasks/20261101-notes-query-capability/010-api-query-contract.md` and `tasks/20261101-notes-query-capability/020-client-query-support.md`",
          "why": "Sequencing is discoverable from structure alone: a strict-order summary in the parent, per-file Depends On lines, and an 'Order logic' subsection in every plan."
        },
        {
          "where": "head of each Implementation plan",
          "quote": "Status: Draft",
          "why": "Plan status is a findable one-line marker repeated in all four files."
        },
        {
          "where": "000-main Questions and decisions",
          "quote": "collected with recommendations in the plan below under `### Implementation decisions and open questions`",
          "why": "The open-questions entry point explicitly routes to the decision log, so no open thread is orphaned."
        },
        {
          "where": "000-main 'Proposed query contract' vs 010 'Proposed contract slice'",
          "quote": "binding once this plan is approved / binding once the parent plan is approved",
          "why": "The same contract appears in two files; precedence is stated in both parentheticals, but a reader must notice them to know which copy governs — a minor, self-resolving ambiguity."
        }
      ]
    },
    "mistakes": [
      {
        "where": "010-api-query-contract.md — Supporting details, 'Proposed contract slice' paragraph",
        "quote": "Optional parameters on `GET /notes/`: `limit` (int 1–100, default 20 when any parameter is used), `offset` (int ≥ 0, default 0), `sort` (one of `id`, `title`, `description`, optional leading `-` for descending, default `id` ascending), `q` (case-insensitive substring on title or description).",
        "why": "Load-bearing contract data rendered as an 81-word run-on paragraph; the parent presents the identical contract as a table, so this prose copy forces re-reading to extract any single parameter's bounds and default."
      },
      {
        "where": "010-api-query-contract.md — Implementation plan, Verification paragraph",
        "quote": "Cases: unparameterized response equals the full seeded set exactly; pagination across multiple pages reconstructs the set without gaps or duplicates; `limit=100` accepted, `limit=101`, `limit=0`, and negative rejected with 422;",
        "why": "Eight-plus required test cases chained with semicolons inside a ~101-word paragraph; the bulleted checklist this wants is compressed into prose."
      },
      {
        "where": "030-cli-query-command.md — Implementation plan, Verification paragraph",
        "quote": "start the real app with a `uvicorn` subprocess from a temporary CWD on an ephemeral port; poll readiness; seed at least five notes over HTTP including duplicate-title rows and filterable text; set `NOTES_API_URL` to the test server;",
        "why": "A 134-word paragraph mixing ordered procedure steps, exact invocations, assertions, scope exclusions, and supporting evidence; a 'named exactly' decisive procedure is the strongest candidate in the set for a numbered list."
      },
      {
        "where": "020-client-query-support.md — Implementation plan, Verification paragraph",
        "quote": "launches the real app via a `uvicorn` subprocess (temporary CWD, ephemeral port, readiness wait), seeds notes over HTTP, then drives the real `NotesClient` (via `from_environment()` with `NOTES_API_URL` pointed at the test server) through paginated, sorted, and filtered calls",
        "why": "A five-step harness procedure plus assertions in one ~87-word sentence; nested parentheticals inside the step chain force slow parsing to reconstruct order."
      },
      {
        "where": "000-main.md — Supporting details, harness facts list",
        "quote": "The CLI's console script points at a `notes_cli` package directory that does not exist (`apps/notes_cli/` contains `cli.py` directly), and `apps/notes_cli/tests/test_cli.py` calls `list_command` without importing it — the current CLI test is defective as shipped.",
        "why": "Two distinct pre-existing defects plus the repair-and-report directive share one bullet; a reader must re-read to attribute each defect and the required action."
      },
      {
        "where": "020-client-query-support.md — Supporting details, 'Harness facts'",
        "quote": "Recommend bumping `notes-client` to 0.2.0 in this change (additive public surface on a 0.x package) — parent plan decision 10.",
        "why": "A release-versioning decision filed under 'Harness facts' — a heading/content mismatch that buries a load-bearing decision where a reader scanning harness setup will not look for it."
      },
      {
        "where": "010-api-query-contract.md — Supporting details, 'Harness facts'",
        "quote": "Do not create a spec page under `docs/` unless the parent plan's documentation decision is changed by approval (smallest-structure rule).",
        "why": "A documentation-scope directive listed under harness facts; related guidance lives in the parent's Documentation section, so its placement here is a bucket mismatch."
      },
      {
        "where": "Contract restated across files: 000-main 'Proposed query contract' table vs 010 Supporting details prose",
        "quote": "`limit` | int, 1–100 | 20 | Page size; 0, negative, or >100 → 422  …  `limit` (int 1–100, default 20 when any parameter is used)",
        "why": "The same binding parameter contract exists as a scannable table in the parent and as a dense prose restatement in 010; two copies must be kept in sync, and the harder-to-use prose copy is the one 010's readers get."
      },
      {
        "where": "'Requirement verification' bullets in all four files (representative: 000-main)",
        "quote": "Contract stability before consumers rely on it → 010's README section and OpenAPI parameters published in the same reviewed change, tests pinning the behavior, and 010 completing before 020/030 begin (dependency declarations). Stability here means decided, documented, and pinned — not versioned release management, which the fixture has no mechanism for.",
        "why": "Each bullet stacks requirement, evidence, sequencing rule, and a definitional caveat into one multi-sentence item; the pattern repeats across all four files and is the densest recurring list shape in the set."
      }
    ],
    "summary": "A consistently signed four-file set: identical section skeletons, inline owner and Depends On pointers, Draft status markers, and a parent that routes open questions to its decision log make outcomes, constraints, and sequencing findable from structure alone (navigable). Most sections read cleanly, including the parent's 1,167-word Implementation plan, which stays workable through nine subsections, tables, and short list items. The recurring strain is load-bearing enumeration compressed into run-on prose: the four-parameter contract as an 81-word paragraph in 010's Supporting details, and the Verification paragraphs in 010 (~101 words of semicolon-chained test cases), 020 (~87-word procedure sentence), and 030 (a 134-word step wall). Secondary issues are bullets that merge two defects with their repair directive, versioning decisions filed under 'Harness facts', and the contract existing in two shapes across files. Readers can navigate everything; the subtask plans' densest paragraphs are where re-reading is unavoidable."
  }
}
```
