# Session — tg05-fastapi-multi-consumer-decomposition · file-fidelity-assessment-glm-max-s0 · glm max

- Run: `20261102T084151.538697Z-task-guidance-file-fidelity-tg05-fastapi-multi-consumer-decomposition-glm-max-s0-812f8fdd`
- Model: glm-5.3-flash (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-c440c4f661a7.md) — captured (original SHA-256 `a9156a1922a724ca…`)
- Config: [glm-assessor-max](../../../../../../shared/configs/glm-assessor-max.json)
- Activity: 3 messages · 0 tool calls · 0 tool results
- Usage: 0 input · 0 cached · 0 output · provider cost $0.0000000

## Transcript

**User**

Assess the task files one agent produced for a fixed scenario, together
with that agent's final conversation response. Judge whether the files
carry what a continuing agent and a human reviewer need: the decided
design, the conversation's durable context, content in the right
sections, a plan justified by planning that actually happened, and
acceptance evidence that fits the work's kind.

Grade these dimensions:

- `plan_design_completeness`: a reader of the implementation plan alone
  can reconstruct the decided design — component responsibilities,
  interfaces or data flow, compatibility and dependency states, material
  decisions, and how the requirements are verified. An ordered list of
  work steps without the design behind it is `poor`; covering some
  design elements is `partial`.
- `durable_context_preservation`: every approved outcome, material
  decision, verified fact with its source, and verification approach the
  conversation established appears in the task files — compressed, not
  dropped. Use `not checked here` only when the conversation established
  nothing durable.
- `section_appropriateness`: content sits where a continuing agent looks
  for it — outcomes and constraints in requirements, rationale and
  learned facts in supporting details, direction in the implementation
  plan, unresolved items in questions and decisions.
- `plan_justification`: the implementation plan reflects planning that
  actually happened. `justified` when the plan restates or organizes the
  conversation's planning; `not_applicable` when no plan section exists;
  `fabricated` when the plan asserts design detail the conversation
  never established.
- `task_kind_fit`: the file uses the sections the work needs and states
  acceptance evidence appropriate to the work's kind — tests for code,
  review acceptance for documentation, rollback and verification for
  operations, brief or style acceptance for content, recorded decisions
  for tracking work. `forced` when inapplicable sections are filled
  mechanically; `missing` when the work's own acceptance evidence is
  absent.

Every grade carries findings: concrete `{where, quote, why}` items
backing it. A non-top grade with empty findings is invalid. Then hunt
for mistakes explicitly — dropped facts, invented decisions or scope,
content a continuing agent would look for in the wrong place, missing
acceptance evidence — and list each as `{where, quote, why}` in
`mistakes`. Grades stay completeness judgments; the mistake hunt is
your search strategy, not a grade.

Do not reward verbosity or formatting of its own. Do not penalize
brevity that loses nothing. The target excerpt and the natural user
request define what is material.

Return JSON only:

{
  "schema_version": 1,
  "scenario_id": "tg05-fastapi-multi-consumer-decomposition",
  "assessment": {
    "dimensions": {
      "plan_design_completeness": {
        "grade": "complete|partial|poor",
        "findings": [{"where": "...", "quote": "...", "why": "..."}]
      },
      "durable_context_preservation": {"grade": "...", "findings": []},
      "section_appropriateness": {"grade": "...", "findings": []},
      "plan_justification": {
        "grade": "justified|not_applicable|fabricated",
        "findings": []
      },
      "task_kind_fit": {"grade": "fits|forced|missing", "findings": []}
    },
    "mistakes": [{"where": "...", "quote": "...", "why": "..."}],
    "summary": "concise evidence-based interpretation"
  }
}

Reviewed target excerpt:

# FastAPI multi-consumer query decomposition

Recognize valid service, SDK, and application boundaries without fragmenting each component into phases.

Category: decomposition

Approved outcomes:

- QUERY-1: One approved public query contract covers filtering, sorting, pagination, validation, and compatibility.
- QUERY-2: The FastAPI service implements the contract through production HTTP and real storage behavior.
- QUERY-3: The reusable Python client exposes the capability while preserving current calls.
- QUERY-4: The CLI exposes the capability and proves the CLI-to-client-to-service path.
- QUERY-5: Each independently delivered public surface has accurate current documentation.

Open questions:

- Exact filter grammar and sort fields require public-contract approval.

Acceptable alternatives:

- Keep the short contract in the parent when one clear maintained owner remains.
- Combine service and client only when release, ownership, and compatibility are not independent.
- Use a separate integration child only when production integration is itself independently maintained.

Natural user request:

Add one supported notes-query capability across the public API, reusable Python client, and CLI. It must support bounded pagination, stable sorting, and optional text filtering while preserving current unparameterized API and client behavior. The public contract must be stable before consumers rely on it, and the CLI must prove the production client-to-service path. Plan the work and create the appropriate task structure without implementing it.

The producer's final conversation response (the durable-context source
the files must preserve):

````markdown
The task structure is planned and stored — nothing implemented. Here's the summary for your approval.

## Task structure created

`tasks/20261101-notes-query-capability/` — one main file plus three subtasks, because the fixture has three independently maintained deliverables at distinct compatibility boundaries (public HTTP API, `notes-client` package, `notes-cli` app), which AGENTS.md explicitly names as valid deliverable splits:

| File | Deliverable | Depends on |
|---|---|---|
| `010-api-query-contract.md` | Query contract on `GET /notes/`: implemented, documented, pinned | — |
| `020-client-query-support.md` | `NotesClient` query surface + conformance proof vs. the real service | 010 |
| `030-cli-query-command.md` | CLI query flags + the production-path end-to-end proof | 010, 020 |

**Outcome:** one query capability (bounded pagination, stable sorting, optional text filtering) live at all three boundaries. **Untouched:** unparameterized `GET /notes/` behavior, `NotesClient.list_notes()` request shape, CLI rendering, DB schema.

**Order logic:** contract first (stability gate before consumers rely on it), then package, then CLI — each a safe stopping point; all changes additive and individually revertible, no persisted-data changes.

**Proposed contract (recommendation, in the Draft for approval):** optional `limit` (1–100, default 20), `offset` (≥ 0), `sort` (`id`/`title`/`description`, `-` for descending, `id` tiebreaker), `q` (case-insensitive substring on title/description) on the existing route; bare JSON array response; deterministic order only when a parameter is supplied.

**Acceptance evidence:** per-boundary decisive checks — API route tests through the real app, real-client-over-real-HTTP conformance test, and one end-to-end CLI check (real `main()` → production `NotesClient.from_environment()` → uvicorn-served service) as the single full-connection proof. Fakes stay supporting-only.

**Material decisions awaiting your approval** (12 in the main file's plan, each with a recommendation): extend `GET /notes/` vs. new endpoint; bare array vs. envelope; strict unparameterized preservation (no implicit ordering added); exact `limit`/`offset` numbers; sort whitelist; `q` semantics; extend `list_notes()` vs. new method; extend `notes list` vs. new subcommand; client error handling explicitly out of scope; `notes-client` → 0.2.0 + CLI's undeclared `notes-client` dependency; introducing `uvicorn` for real-server tests; READMEs (+ generated OpenAPI) as the docs destination, no new spec pages.

**Findings recorded during inspection:** the fixture ships real harness defects — the CLI console script targets a nonexistent `notes_cli` package directory, `test_cli.py` calls `list_command` without importing it, no `uvicorn` exists anywhere in the dependency set, and the DB path is CWD-relative. Each subtask's plan handles its own instance; the CLI repairs would be reported, not silent.

**Risks/way back:** drift between documented contract and implementations is caught by the conformance and e2e checks running real consumers against the real service; any subtask can be reverted independently.

Execution waits for your approval of the plan and the decisions above — say the word and I'll mark the plans Approved and begin with 010, or adjust the contract first.
````

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
    "dimensions": {
      "plan_design_completeness": {
        "grade": "complete",
        "findings": [
          {
            "where": "000-main.md § Implementation plan → Proposed query contract",
            "quote": "`limit` | int, 1–100 | 20 | Page size; 0, negative, or >100 → 422",
            "why": "The full public interface — parameters, types, defaults, bounds, error behavior — plus response shape ('Response stays a bare JSON array... No envelope, no total count') is specified, so the contract is reconstructable from the plan alone."
          },
          {
            "where": "000-main.md § Implementation plan → Component responsibilities",
            "quote": "Client (020): `list_notes(limit=None, offset=None, sort=None, q=None)` builds the query string only from supplied values, so an unparameterized call sends exactly today's parameter-free request",
            "why": "Per-component responsibilities and the request-construction data flow are stated, including the mechanism by which preservation holds; 010's design adds the server-side flow ('applied only when at least one parameter is supplied... preservation holds by construction')."
          },
          {
            "where": "000-main.md § Implementation decisions 1–12",
            "quote": "2. Bare JSON array for parameterized pages vs. an envelope with total count. Recommend bare array: maximally compatible with today's shape",
            "why": "All material decisions appear with the considered alternative and rationale (including dependency states: decision 10's 0.2.0 bump and CLI dependency, decision 11's uvicorn introduction)."
          },
          {
            "where": "010-api-query-contract.md § header block",
            "quote": "Depends On: none. Must complete before `tasks/20261101-notes-query-capability/020-client-query-support.md` and `tasks/20261101-notes-query-capability/030-cli-query-command.md` start.",
            "why": "Compatibility/dependency states (ordering, stability gate before consumers) are explicit in the plan structure, not just implied by numbering."
          },
          {
            "where": "000-main.md § Requirement verification",
            "quote": "Contract stability before consumers rely on it → 010's README section and OpenAPI parameters published in the same reviewed change, tests pinning the behavior, and 010 completing before 020/030 begin (dependency declarations).",
            "why": "Every requirement is mapped to named verification evidence with explicit coverage limits ('Does not cover real socket transport or consumer surfaces'), so verification of the requirements is reconstructable."
          }
        ]
      },
      "durable_context_preservation": {
        "grade": "complete",
        "findings": [
          {
            "where": "000-main.md § Requirements checklist",
            "quote": "Current unparameterized behavior is preserved: `GET /notes/` without parameters still returns every note as a JSON array with today's behavior, and existing `NotesClient.list_notes()` still sends the same parameter-free request",
            "why": "The response's 'Untouched' list (API behavior, client request shape, CLI rendering, DB schema) is carried as requirement constraints ('All changes are additive; no SQLite schema or persisted-data changes', 'rendering unchanged')."
          },
          {
            "where": "000-main.md § Implementation decisions 1–12",
            "quote": "9. Scope exclusion: client HTTP error handling stays as is (no `raise_for_status` is added).",
            "why": "All twelve decisions the response listed as awaiting approval appear with recommendations, including the out-of-scope exclusion (echoed in 020: 'Parent decision 9 keeps it that way')."
          },
          {
            "where": "000-main.md § Supporting details → Known harness facts",
            "quote": "The CLI's console script points at a `notes_cli` package directory that does not exist",
            "why": "All four inspection findings are recorded (console-script path, missing `list_command` import, no uvicorn anywhere, CWD-relative DB) with handling assigned to owning subtasks and 'reported, not silent' preserved in 030's checklist."
          },
          {
            "where": "000-main.md § Supporting details → Verification shape table",
            "quote": "E2E: `main([...])` with production `NotesClient.from_environment()` against a subprocess-served app; stdout asserts paging/sort/filter results",
            "why": "The response's acceptance-evidence design is preserved: the single full-connection proof ('The 030 check is the single full-connection proof') and fakes as supporting-only ('per-side fakes stay supporting evidence only')."
          },
          {
            "where": "000-main.md § header",
            "quote": "Planning only: this file records outcomes and a draft approach. No execution is authorized yet.",
            "why": "The response's gating ('Execution waits for your approval') is preserved via Draft status and 'none blocks planning, all block execution'."
          }
        ]
      },
      "section_appropriateness": {
        "grade": "complete",
        "findings": [
          {
            "where": "000-main.md § Requirements checklist",
            "quote": "The query contract is stable before consumers rely on it: written into maintained public docs, pinned by tests, and completed before client or CLI work starts.",
            "why": "Outcomes and constraints sit in requirements where a continuing agent checks scope; subtask checklists restate their own slices of the same constraints."
          },
          {
            "where": "000-main.md § Supporting details → Known harness facts",
            "quote": "`DATABASE_URL` is hardcoded to `sqlite:///./notes.db`, relative to the process CWD.",
            "why": "Learned inspection facts (including explicitly flagged assumptions like the TestClient lifespan question) live in supporting details, not mixed into requirements or direction."
          },
          {
            "where": "000-main.md § Implementation plan → Order logic and milestones",
            "quote": "010 first because both other components consume its contract, and the request requires the contract to be stable before consumers rely on it.",
            "why": "Sequencing direction with rationale is in the implementation plan, mirrored by each subtask's own Order logic."
          },
          {
            "where": "000-main.md § Questions and decisions",
            "quote": "The material design decisions that shape the public contract are collected with recommendations in the plan below",
            "why": "Unresolved approvals are routed to the questions-and-decisions home; the scenario's open question (filter grammar, sort fields) is kept open as decisions 4–6 ('confirm these as the contract numbers'), with subtasks cross-referencing ('Governed by parent plan decisions 4–7, 9–11') rather than duplicating authority."
          }
        ]
      },
      "plan_justification": {
        "grade": "justified",
        "findings": [
          {
            "where": "000-main.md § Implementation plan → Order logic and milestones",
            "quote": "020 needs the stable contract to code against and the real service to run conformance tests. 030 needs both the contract and the client method.",
            "why": "The plan restates the conversation's order logic (contract first, then package, then CLI, each a safe stopping point) with the same reasoning the response gave."
          },
          {
            "where": "000-main.md § Implementation decisions, decision 11",
            "quote": "The alternative — `httpx.ASGITransport` — is rejected for the production-path check because it skips the real server and lifespan",
            "why": "The plan elaborates the conversation's uvicorn decision rather than inventing new direction; every enumerated plan element (contract numbers, 12 decisions, four findings, order logic, way back) has an antecedent in the response."
          },
          {
            "where": "010-api-query-contract.md § Implementation plan",
            "quote": "**Order logic.** Implementation, tests, and README contract section land as one reviewed change; the milestone is a stable, documented, pinned contract.",
            "why": "Subtask plans organize the conversation's contract-first stability gate into per-subtask steps; no design detail is asserted that the conversation never established — the contract remains explicitly 'binding once approved', matching the scenario's open question."
          }
        ]
      },
      "task_kind_fit": {
        "grade": "fits",
        "findings": [
          {
            "where": "010-api-query-contract.md § Requirement verification",
            "quote": "Unparameterized preservation → the exact-response regression test on seeded rows.",
            "why": "Code work carries test-based acceptance evidence named per requirement, with 030's e2e check specified to the invocation and assertions level."
          },
          {
            "where": "020-client-query-support.md § Requirement verification",
            "quote": "Documentation → the changed `packages/notes_client/README.md` page, reviewed in the same change as the code.",
            "why": "Documentation deliverables carry review-based acceptance appropriate to their kind, repeated at every boundary."
          },
          {
            "where": "000-main.md § Implementation plan → Risks and the way back",
            "quote": "Reverting any subtask's change restores that boundary's prior behavior.",
            "why": "Rollback and verification framing fits additive multi-boundary work; sections that could be mechanical (subtask 'Questions and decisions') instead state governance scope, so nothing is filled forcedly."
          },
          {
            "where": "000-main.md § Implementation decisions preamble",
            "quote": "none blocks planning, all block execution",
            "why": "The planning-kind deliverable's own acceptance — plan approval before execution — is itself recorded, matching the 'without implementing it' request."
          }
        ]
      }
    },
    "mistakes": [
      {
        "where": "000-main.md § Supporting details → Components and boundaries",
        "quote": "Three separately owned deliverables, each with its own compatibility boundary; this is why the work decomposes into three children rather than one change",
        "why": "The response justified the three-way split partly by 'AGENTS.md explicitly names as valid deliverable splits'; the files keep the substantive rationale but drop the AGENTS.md warrant, which appears nowhere in any file. Minor: the decomposition and its boundary reasoning survive; only the convention citation is lost."
      }
    ],
    "summary": "The four files faithfully carry the conversation's durable context: the three-way structure with dependency ordering, the untouched-boundary constraints, the exact proposed contract numbers, all twelve pending decisions with recommendations, the four inspection findings with their assigned owners and report-not-silent handling, and the approval gate (Draft status, execution unauthorized). Plans are designs, not mere step lists — contract table, per-component responsibilities and data flow, preservation-by-construction mechanism, coverage-delimited verification mapping — so a continuing agent can reconstruct and execute from them. Content sits in conventional sections, the plan restates planning that actually happened without invented direction, and acceptance evidence matches the work's kinds (route/integration/e2e tests for code, same-change doc review, revertibility, plan approval for the planning deliverable itself). The only gap found is the dropped AGENTS.md citation behind the decomposition choice; substantively minor."
  }
}
```
