# Session — tg05-fastapi-multi-consumer-decomposition · task-creation-assessment-glm-max-s0 · glm max

- Run: `20261102T044008.538853Z-task-guidance-semantic-tg05-fastapi-multi-consumer-decomposition-glm-max-s0-7368ed46`
- Model: glm-5.3-flash (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-c440c4f661a7.md) — captured (original SHA-256 `e1943a0354ca02b4…`)
- Config: [glm-assessor-max](../../../../../../shared/configs/glm-assessor-max.json)
- Activity: 3 messages · 0 tool calls · 0 tool results
- Usage: 0 input · 0 cached · 0 output · provider cost $0.0000000

## Transcript

**User**

Assess the task set produced for one fixed scenario. Use the reviewed
target, not raw task count, as the authority.

Judge whether the task set preserves approved outcomes and partitions work
into coherent deliverables. A technical layer is a valid separate task only
when completion leaves an independently usable, acceptable, deferable, owned,
or reviewable result. Identify subtasks that are merely phases or layer
fragments and could merge without losing independent value. Also identify
overpacked tasks that hide several independent deliverables.

The natural user request is part of the authority. Do not label behavior
explicitly requested there or listed in approved outcomes as added scope.
A coordinating parent file such as `000-main.md` is not an implementation
deliverable: exclude it from `actual_task_count`, fragmentation ratio, and
unmatched tasks unless it contains separately assigned implementation work.
For `crossing_ownership`, apply the target's exact `important_crossings`.
Separate mocked component tests and direct route/helper tests do not prove a
required production connection. Mark the crossing complete only when the task
names at least one check through that exact connection; otherwise mark it
partial or missing and explain the gap.

Do not reward verbosity, exact filenames, or matching the target's task count
mechanically. Do not penalize an acceptable alternative partition described by
the target. Treat tests, documentation, implementation, review, and deployment
as work within a deliverable unless their result is independently required.

Assess these issue dimensions separately:

- `fragmentation`: the overall mismatch between actual tasks and coherent
  deliverables;
- `phase_only_children`: implementation, testing, documentation, deployment,
  cleanup, or review children that only complete another delivery;
- `layer_split_without_independent_value`: frontend, backend, transport,
  storage, or package children that lack independent users, ownership,
  compatibility, acceptance, or a complete product outcome;
- `evidence_reownership`: a final integration, verification, or documentation
  child re-owning evidence that belongs with outcome-delivery children;
- `unsafe_dependencies`: missing, unnecessary, or wrong dependencies that
  permit a broken intermediate state or serialize independently deliverable
  work;
- `piecewise_crossing_evidence`: separate mocks, component checks, direct
  routes, or helper tests without one decisive check through the required
  production connection.

For fragmentation use `none|low|medium|high`. For every other dimension use
`none|partial|present`. `none` means the issue is absent, `partial` means a
limited or incomplete instance, and `present` means a material instance.
List concrete occurrences separately. Do not invent numeric scores; the
evaluator derives them deterministically from these statuses.

Return JSON only with this shape:

{
  "schema_version": 3,
  "scenario_id": "tg05-fastapi-multi-consumer-decomposition",
  "assessment": {
    "outcome_coverage": "complete|partial|poor",
    "missing_outcomes": ["OUTCOME-ID"],
    "added_obligations": ["description"],
    "semantic_deliverable_count": 0,
    "actual_task_count": 0,
    "deliverable_mappings": [
      {
        "deliverable_id": "target id",
        "task_paths": ["tasks/..."],
        "coverage": "complete|partial|missing",
        "coherence": "coherent|fragmented|overpacked",
        "reason": "short evidence"
      }
    ],
    "mergeable_groups": [
      {"task_paths": ["tasks/..."], "reason": "why these are one deliverable"}
    ],
    "unmatched_tasks": ["tasks/..."],
    "overpacked_tasks": ["tasks/..."],
    "valid_layer_boundaries": ["tasks/..."],
    "automatic_layer_fragments": ["tasks/..."],
    "dependency_issues": ["description"],
    "crossing_ownership": "complete|partial|missing",
    "fragmentation_severity": "none|low|medium|high",
    "fragmentation_ratio": 0.0,
    "quality_metrics": {
      "fragmentation": {
        "status": "none|low|medium|high",
        "occurrences": [
          {
            "task_paths": ["tasks/..."],
            "description": "concrete occurrence"
          }
        ]
      },
      "phase_only_children": {
        "status": "none|partial|present",
        "occurrences": []
      },
      "layer_split_without_independent_value": {
        "status": "none|partial|present",
        "occurrences": []
      },
      "evidence_reownership": {
        "status": "none|partial|present",
        "occurrences": []
      },
      "unsafe_dependencies": {
        "status": "none|partial|present",
        "occurrences": []
      },
      "piecewise_crossing_evidence": {
        "status": "none|partial|present",
        "occurrences": []
      }
    },
    "partition_quality_score": 0,
    "handoff_quality_score": 0,
    "summary": "concise evidence-based interpretation"
  }
}

Scores are integers from 0 through 100. `fragmentation_ratio` is actual task
files divided by the semantic coherent-deliverable count, or 0 when no
deliverable exists; it is descriptive rather than decisive.

Reviewed target:

{
  "acceptable_alternatives": [
    "Keep the short contract in the parent when one clear maintained owner remains.",
    "Combine service and client only when release, ownership, and compatibility are not independent.",
    "Use a separate integration child only when production integration is itself independently maintained."
  ],
  "acceptable_partition_sizes": [
    3,
    4,
    5
  ],
  "approved_outcomes": [
    {
      "id": "QUERY-1",
      "outcome": "One approved public query contract covers filtering, sorting, pagination, validation, and compatibility."
    },
    {
      "id": "QUERY-2",
      "outcome": "The FastAPI service implements the contract through production HTTP and real storage behavior."
    },
    {
      "id": "QUERY-3",
      "outcome": "The reusable Python client exposes the capability while preserving current calls."
    },
    {
      "id": "QUERY-4",
      "outcome": "The CLI exposes the capability and proves the CLI-to-client-to-service path."
    },
    {
      "id": "QUERY-5",
      "outcome": "Each independently delivered public surface has accurate current documentation."
    }
  ],
  "category": "decomposition",
  "coherent_deliverables": [
    {
      "dependencies": [],
      "id": "QUERY-D1",
      "independent_value": "A stable public contract independently unblocks multiple owners and consumers.",
      "outcomes": [
        "QUERY-1"
      ],
      "title": "Approve the shared query contract"
    },
    {
      "dependencies": [
        "QUERY-D1"
      ],
      "id": "QUERY-D2",
      "independent_value": "The public API is independently usable by external and first-party consumers.",
      "outcomes": [
        "QUERY-2",
        "QUERY-5"
      ],
      "title": "Deliver the FastAPI service capability"
    },
    {
      "dependencies": [
        "QUERY-D1"
      ],
      "id": "QUERY-D3",
      "independent_value": "The client is an independently published reusable package with its own compatibility boundary.",
      "outcomes": [
        "QUERY-3",
        "QUERY-5"
      ],
      "title": "Deliver the reusable Python client capability"
    },
    {
      "dependencies": [
        "QUERY-D2",
        "QUERY-D3"
      ],
      "id": "QUERY-D4",
      "independent_value": "The CLI is a separately accepted application and owns the complete first-party integration path.",
      "outcomes": [
        "QUERY-4",
        "QUERY-5"
      ],
      "title": "Deliver the CLI workflow and production integration"
    }
  ],
  "fragmentation_examples": [
    "Service model, query, route, tests, and docs as separate tasks.",
    "Client transport, models, errors, tests, and docs as separate tasks.",
    "CLI parsing, output, tests, and documentation as separate tasks.",
    "A generic final review or integration-test phase."
  ],
  "handoff": {
    "fresh_agent_plan": "A fresh agent recognizes valid component boundaries while keeping each component's work, tests, and docs together.",
    "omit_plan": "Preserve package facts, public questions, ownership boundaries, and crossings without the four-component task partition.",
    "retain_plan": "Preserve contract, ownership, compatibility, parallelism, and final integration dependencies."
  },
  "important_crossings": [
    "HTTP route to real storage.",
    "Python client transport to production API.",
    "CLI through the actual client package and HTTP service."
  ],
  "open_questions": [
    "Exact filter grammar and sort fields require public-contract approval."
  ],
  "overpacking_examples": [
    "One child for service, reusable client, and CLI hides independent package ownership and compatibility."
  ],
  "plan_target": {
    "required_content": [
      {
        "content": "The public query contract as the first-class design object: filtering, sorting, pagination, validation, and compatibility in one approved form.",
        "derived_from": [
          "QUERY-1"
        ],
        "id": "PLAN-1"
      },
      {
        "content": "How the FastAPI service implements the contract through production HTTP and real storage behavior.",
        "derived_from": [
          "QUERY-2"
        ],
        "id": "PLAN-2"
      },
      {
        "content": "How the reusable Python client exposes the capability while preserving current calls.",
        "derived_from": [
          "QUERY-3"
        ],
        "id": "PLAN-3"
      },
      {
        "content": "How the CLI exposes the capability so the CLI-to-client-to-service path is proven.",
        "derived_from": [
          "QUERY-4"
        ],
        "id": "PLAN-4"
      },
      {
        "content": "The delivery order \u2014 contract settled before the surfaces that consume it \u2014 with each independently delivered public surface documented as it lands.",
        "derived_from": [
          "QUERY-5"
        ],
        "id": "PLAN-5"
      }
    ]
  },
  "project": {
    "fixture_id": "tg05-fastapi-multi-consumer",
    "kind": "public service, reusable Python client, and CLI",
    "name": "FastAPI notes multi-consumer fixture",
    "revision": "4fa7ae952ece61e228135285de1b6a5ff65a1dc8",
    "upstream": "https://github.com/testdrivenio/fastapi-crud-async"
  },
  "scenario_id": "tg05-fastapi-multi-consumer-decomposition",
  "schema_version": 1,
  "task_summary": "Recognize valid service, SDK, and application boundaries without fragmenting each component into phases.",
  "title": "FastAPI multi-consumer query decomposition"
}

Natural user request:

Add one supported notes-query capability across the public API, reusable Python client, and CLI. It must support bounded pagination, stable sorting, and optional text filtering while preserving current unparameterized API and client behavior. The public contract must be stable before consumers rely on it, and the CLI must prove the production client-to-service path. Plan the work and create the appropriate task structure without implementing it.

Subject material:

{
  "response": "The task structure is planned and stored \u2014 nothing implemented. Here's the summary for your approval.\n\n## Task structure created\n\n`tasks/20261101-notes-query-capability/` \u2014 one main file plus three subtasks, because the fixture has three independently maintained deliverables at distinct compatibility boundaries (public HTTP API, `notes-client` package, `notes-cli` app), which AGENTS.md explicitly names as valid deliverable splits:\n\n| File | Deliverable | Depends on |\n|---|---|---|\n| `010-api-query-contract.md` | Query contract on `GET /notes/`: implemented, documented, pinned | \u2014 |\n| `020-client-query-support.md` | `NotesClient` query surface + conformance proof vs. the real service | 010 |\n| `030-cli-query-command.md` | CLI query flags + the production-path end-to-end proof | 010, 020 |\n\n**Outcome:** one query capability (bounded pagination, stable sorting, optional text filtering) live at all three boundaries. **Untouched:** unparameterized `GET /notes/` behavior, `NotesClient.list_notes()` request shape, CLI rendering, DB schema.\n\n**Order logic:** contract first (stability gate before consumers rely on it), then package, then CLI \u2014 each a safe stopping point; all changes additive and individually revertible, no persisted-data changes.\n\n**Proposed contract (recommendation, in the Draft for approval):** optional `limit` (1\u2013100, default 20), `offset` (\u2265 0), `sort` (`id`/`title`/`description`, `-` for descending, `id` tiebreaker), `q` (case-insensitive substring on title/description) on the existing route; bare JSON array response; deterministic order only when a parameter is supplied.\n\n**Acceptance evidence:** per-boundary decisive checks \u2014 API route tests through the real app, real-client-over-real-HTTP conformance test, and one end-to-end CLI check (real `main()` \u2192 production `NotesClient.from_environment()` \u2192 uvicorn-served service) as the single full-connection proof. Fakes stay supporting-only.\n\n**Material decisions awaiting your approval** (12 in the main file's plan, each with a recommendation): extend `GET /notes/` vs. new endpoint; bare array vs. envelope; strict unparameterized preservation (no implicit ordering added); exact `limit`/`offset` numbers; sort whitelist; `q` semantics; extend `list_notes()` vs. new method; extend `notes list` vs. new subcommand; client error handling explicitly out of scope; `notes-client` \u2192 0.2.0 + CLI's undeclared `notes-client` dependency; introducing `uvicorn` for real-server tests; READMEs (+ generated OpenAPI) as the docs destination, no new spec pages.\n\n**Findings recorded during inspection:** the fixture ships real harness defects \u2014 the CLI console script targets a nonexistent `notes_cli` package directory, `test_cli.py` calls `list_command` without importing it, no `uvicorn` exists anywhere in the dependency set, and the DB path is CWD-relative. Each subtask's plan handles its own instance; the CLI repairs would be reported, not silent.\n\n**Risks/way back:** drift between documented contract and implementations is caught by the conformance and e2e checks running real consumers against the real service; any subtask can be reverted independently.\n\nExecution waits for your approval of the plan and the decisions above \u2014 say the word and I'll mark the plans Approved and begin with 010, or adjust the contract first.",
  "task_files": {
    "tasks/20261101-notes-query-capability/000-main.md": "# Supported notes-query capability across API, client, and CLI\n\nAdd one supported way to query notes \u2014 bounded pagination, stable sorting, and\noptional text filtering \u2014 consistently across the three independently\nmaintained components: the public FastAPI notes API (`src/app/`), the reusable\n`notes_client` package (`packages/notes_client/`), and the `notes` CLI\n(`apps/notes_cli/`). Existing unparameterized behavior is preserved at every\nboundary, the public HTTP contract is stable before consumers build on it, and\nthe CLI proves the production client-to-service path end to end.\n\nPlanning only: this file records outcomes and a draft approach. No execution is\nauthorized yet.\n\n## Requirements checklist\n\n- [ ] The notes HTTP API supports querying notes with bounded pagination, stable (deterministic) sorting, and optional text filtering. Owner: `tasks/20261101-notes-query-capability/010-api-query-contract.md`\n- [ ] The query contract is stable before consumers rely on it: written into maintained public docs, pinned by tests, and completed before client or CLI work starts. Owner: `tasks/20261101-notes-query-capability/010-api-query-contract.md`\n- [ ] Current unparameterized behavior is preserved: `GET /notes/` without parameters still returns every note as a JSON array with today's behavior, and existing `NotesClient.list_notes()` still sends the same parameter-free request and returns the parsed JSON list. Owners: `tasks/20261101-notes-query-capability/010-api-query-contract.md` + `tasks/20261101-notes-query-capability/020-client-query-support.md`\n- [ ] The reusable Python client exposes the query capability against the stable contract. Owner: `tasks/20261101-notes-query-capability/020-client-query-support.md`\n- [ ] The CLI exposes the query capability, and its production client-to-service path is proven end to end: a real CLI invocation through the production `NotesClient` against a running service. Owner: `tasks/20261101-notes-query-capability/030-cli-query-command.md`\n- [ ] Each component's maintained documentation describes the new supported behavior in the same change that makes it true. Owners: all three subtasks, each for its own docs.\n\n## Subtasks\n\n- [ ] `tasks/20261101-notes-query-capability/010-api-query-contract.md` \u2014 define, implement, document, and pin the public query contract.\n- [ ] `tasks/20261101-notes-query-capability/020-client-query-support.md` \u2014 expose the query capability on `NotesClient`. Depends On: `tasks/20261101-notes-query-capability/010-api-query-contract.md`\n- [ ] `tasks/20261101-notes-query-capability/030-cli-query-command.md` \u2014 expose the query capability on the CLI and prove the production path. Depends On: `tasks/20261101-notes-query-capability/010-api-query-contract.md` and `tasks/20261101-notes-query-capability/020-client-query-support.md`\n\nOrder is strict: 010 \u2192 020 \u2192 030. The `Depends On` declarations are the\noperative constraints; filename numbering only reflects them.\n\n## Questions and decisions\n\nThere are no unresolved requirement questions: the capability, the three\nboundaries it must span, the preservation constraint, and both sequencing\nconstraints (contract stability, production-path proof) are fixed by the\nrequest. The material design decisions that shape the public contract are\ncollected with recommendations in the plan below under\n`### Implementation decisions and open questions`; they are approved together\nwith the plan before any subtask executes. The most consequential:\n\n- The query surface is proposed as optional parameters on the existing\n  `GET /notes/` route (not a new endpoint), keeping the bare JSON array\n  response shape.\n- Deterministic ordering applies only when a query parameter is used; the fully\n  unparameterized request keeps today's behavior exactly, including its\n  currently unspecified row ordering.\n\n## Supporting details\n\n**Components and boundaries.** Three separately owned deliverables, each with\nits own compatibility boundary; this is why the work decomposes into three\nchildren rather than one change:\n\n- Public API: `src/app/` \u2014 FastAPI app with router prefix `/notes`\n  (`src/app/api/notes.py`), CRUD helpers (`src/app/api/crud.py`),\n  `NoteCreate`/`Note` models (`src/app/api/models.py`), SQLite via\n  `databases` + SQLAlchemy core (`src/app/db.py`). `GET /notes/` returns\n  `crud.get_all()` \u2014 every note, no ordering, no parameters.\n- Client package: `packages/notes_client/` \u2014 own `pyproject.toml`\n  (`notes-client` 0.1.0, depends on `httpx` only). `NotesClient` takes an\n  injected transport; `from_environment()` uses `NOTES_API_URL` (default\n  `http://127.0.0.1:8000`). `list_notes()` GETs `/notes/` and returns parsed\n  JSON.\n- CLI app: `apps/notes_cli/` \u2014 own `pyproject.toml` (`notes-cli`, console\n  script `notes = \"notes_cli.cli:main\"`). `list` subcommand prints\n  `{id}: {title}` per note via the client.\n- Maintained docs: root `README.md` (API, currently says the collection route\n  returns every note as a JSON array), per-component READMEs, and\n  `docs/development/index.md`, which records that no notes-query specification\n  exists.\n\n**Definitions used by this task.**\n\n- Bounded pagination: the requested page size is capped by a server-enforced\n  maximum; requests beyond the cap are rejected.\n- Stable sorting: a deterministic total order (requested sort key with unique\n  `id` as final tiebreaker) so pages never skip or repeat rows across offsets.\n- Optional text filtering: a consumer-supplied text term narrowing results;\n  proposed as case-insensitive substring match on title or description.\n- Preservation: unparameterized requests keep current behavior exactly \u2014\n  content, shape, and ordering.\n\n**Verification shape.** One named decisive check per product connection;\nper-side fakes stay supporting evidence only and do not substitute for the\nconnection checks.\n\n| Product connection | Owner | Decisive check | Deliberately not covered there |\n| --- | --- | --- | --- |\n| Public API contract behavior | 010 | Route tests through `app.main.app` (TestClient) on a seeded temp SQLite DB | Real socket transport; consumer surfaces |\n| Client \u2194 service contract conformance | 020 | Real `NotesClient` over real HTTP against the running app | CLI rendering |\n| CLI \u2192 client \u2192 service production path | 030 | E2E: `main([...])` with production `NotesClient.from_environment()` against a subprocess-served app; stdout asserts paging/sort/filter results | Hosted deployment; concurrency |\n\nThe 030 check is the single full-connection proof for the feature. API route\ntests and the existing fake-transport/fake-client unit tests do not satisfy\nthe production-path requirement.\n\n**Known harness facts, defects, and assumptions** (verified by inspection; no\ntest was run during planning \u2014 the environment lacks the project\ndependencies):\n\n- `DATABASE_URL` is hardcoded to `sqlite:///./notes.db`, relative to the\n  process CWD. Any test that runs the real service must launch it from a\n  temporary working directory for isolation.\n- `src/tests/conftest.py` builds `TestClient(app)` without using it as a\n  context manager, while `database.connect()` runs in the lifespan hook.\n  Assumption to verify during execution: the DB may not be connected in the\n  current suite; route tests should use `with TestClient(app)` or otherwise\n  ensure the connection.\n- Importing `app.db` materializes `./notes.db` at import time\n  (`metadata.create_all`). The file is not gitignored; keep it out of commits.\n- No `uvicorn` is declared anywhere in the fixture, so proving real-server\n  paths requires introducing it as a dependency (see plan decision 11).\n- The CLI's console script points at a `notes_cli` package directory that does\n  not exist (`apps/notes_cli/` contains `cli.py` directly), and\n  `apps/notes_cli/tests/test_cli.py` calls `list_command` without importing\n  it \u2014 the current CLI test is defective as shipped. 030 must make the real\n  CLI code importable and fix the import incidentally, reporting the fix.\n- The CLI's `pyproject.toml` declares no dependency on `notes-client` despite\n  importing it (see plan decision 10).\n- Existing client tests use a fake transport and CLI tests a fake client;\n  both are kept as unit-level regression evidence only.\n\n## Implementation plan\n\nStatus: Draft\n\n### Proposed query contract (binding once this plan is approved)\n\n`GET /notes/` gains optional query parameters. Supplying none reproduces\ntoday's behavior exactly.\n\n| Parameter | Type / range | Default in parameterized use | Semantics |\n| --- | --- | --- | --- |\n| `limit` | int, 1\u2013100 | 20 | Page size; 0, negative, or >100 \u2192 422 |\n| `offset` | int, \u2265 0 | 0 | Rows to skip |\n| `sort` | one of `id`, `title`, `description`, optional leading `-` for descending | `id` ascending | Deterministic total order via `id` tiebreaker |\n| `q` | string | none | Case-insensitive substring match on title or description |\n\n- Response stays a bare JSON array of note objects (up to `limit` items);\n  empty array for no matches. No envelope, no total count.\n- Whenever any parameter is supplied, results are returned in the\n  deterministic total order (sort key, then `id`).\n- Invalid values yield FastAPI's standard 422 responses.\n\n### Component responsibilities\n\n- API (010): parse and validate parameters with `fastapi.Query`; translate to\n  SQLAlchemy `where`/`order_by`/`offset`/`limit` in `crud` while keeping the\n  unparameterized path on today's code branch. No schema changes.\n- Client (020): `list_notes(limit=None, offset=None, sort=None, q=None)`\n  builds the query string only from supplied values, so an unparameterized\n  call sends exactly today's parameter-free request; returns the parsed JSON\n  list.\n- CLI (030): extend the `list` subcommand with `--limit`, `--offset`,\n  `--sort`, `--query`; argparse validates ranges and choices locally so normal\n  CLI use never triggers a 422; rendering unchanged; values pass through to\n  the production client.\n\n### Order logic and milestones\n\n010 first because both other components consume its contract, and the request\nrequires the contract to be stable before consumers rely on it. 020 needs the\nstable contract to code against and the real service to run conformance tests.\n030 needs both the contract and the client method. Safe stopping points: after\n010 the API is releasable on its own; after 020 the package is releasable;\nafter 030 the user-facing capability is complete and proven end to end.\n\n### Risks and the way back\n\n- All changes are additive; no SQLite schema or persisted-data changes.\n  Reverting any subtask's change restores that boundary's prior behavior.\n- Largest risk is drift between the documented contract and its implementation\n  across three components; 020's conformance test and 030's end-to-end check\n  run the real consumers against the real service, so drift fails loudly.\n- Pagination without a total order silently skips or duplicates rows;\n  the `id` tiebreaker plus explicit multi-page assertions address this.\n- `q` case folding on SQLite is ASCII-only (`ilike` compiles to `lower()`);\n  document this honestly rather than over-claiming Unicode support.\n- The unparameterized path is pinned by explicit regression evidence in 010\n  (exact response) and 020 (request shape).\n- Harness risks: CWD-relative DB path, the TestClient lifespan question, and\n  the CLI import defects listed under supporting details; each subtask's plan\n  handles its own instance.\n\n### Implementation decisions and open questions\n\nDecisions 1\u20139 change the public contract or a consumer surface and are\napproved with this plan; 10\u201312 are material maintenance choices. Each carries\na recommendation; none blocks planning, all block execution.\n\n1. Extend the existing `GET /notes/` route with optional parameters vs. a new\n   endpoint. Recommend extending: standard collection-query shape, and\n   unparameterized calls are untouched by construction.\n2. Bare JSON array for parameterized pages vs. an envelope with total count.\n   Recommend bare array: maximally compatible with today's shape and the\n   client's list return; a shorter page signals the end.\n3. Deterministic ordering only for parameterized requests; strict\n   preservation (including unspecified ordering) for unparameterized\n   requests. Recommend strict preservation \u2014 adding an implicit `ORDER BY` to\n   unparameterized responses would change current consumer-visible behavior.\n4. Exact numbers: `limit` default 20, max 100; `offset` default 0. Mechanically\n   any values work; confirm these as the contract numbers.\n5. Sort surface: whitelist {`id`, `title`, `description`} with optional `-`\n   descending prefix and `id` as final tiebreaker. Recommend as proposed.\n6. Filter surface: single `q`, case-insensitive substring across title and\n   description. Alternatives (title-only, exact match) rejected as less\n   useful; ASCII-folding limitation documented.\n7. Client surface: extend `list_notes()` with optional keyword parameters\n   vs. a new `query_notes()` method. Recommend extending: signature-compatible\n   for existing callers, one collection method.\n8. CLI surface: extend `notes list` with flags vs. a new `query` subcommand.\n   Recommend extending `list`: one user surface matching the one client\n   method.\n9. Scope exclusion: client HTTP error handling stays as is (no\n   `raise_for_status` is added). Adding it would change the client package's\n   current error-path behavior; record as a possible follow-up instead.\n10. Maintenance notes: recommend bumping `notes-client` to 0.2.0 in the same\n    change as 020 (additive public surface on a 0.x package), and adding\n    `notes-client` to the CLI's undeclared dependencies in 030. Both are\n    reported changes, not silent ones.\n11. Test harness: introduce `uvicorn` (recommended: root `pyproject.toml`\n    dependencies) to serve the real app in 020/030 checks. The alternative \u2014\n    `httpx.ASGITransport` \u2014 is rejected for the production-path check because\n    it skips the real server and lifespan; it also needs manual\n    `database.connect()` handling.\n12. Documentation destination: the three maintained READMEs plus OpenAPI\n    generated from route code; no new spec pages or directories\n    (smallest-structure rule). A versionable spec page under `docs/` remains\n    available if maintainers want one later.\n\n### Documentation\n\n- Root `README.md` \u2014 query contract section in the same change as 010\n  (audience: API consumers).\n- `packages/notes_client/README.md` \u2014 new client surface in the same change\n  as 020 (audience: Python consumers).\n- `apps/notes_cli/README.md` \u2014 new flags in the same change as 030 (audience:\n  CLI users).\n- OpenAPI is generated from route code; change the source, never the output.\n- No placeholder pages; `docs/development/index.md` needs no change unless a\n  spec page is approved.\n\n### Task checklist\n\n- [ ] `tasks/20261101-notes-query-capability/010-api-query-contract.md` \u2014 contract implemented, documented, pinned.\n- [ ] `tasks/20261101-notes-query-capability/020-client-query-support.md` \u2014 client surface implemented and conformance-proven.\n- [ ] `tasks/20261101-notes-query-capability/030-cli-query-command.md` \u2014 CLI surface shipped and production path proven.\n\n### Requirement verification\n\n- Query capability with bounded pagination, stable sorting, text filtering \u2192\n  010's route tests through the real app (bounds rejection, tiebreaker\n  determinism, filtering, combined parameters). Does not cover real socket\n  transport or consumer surfaces.\n- Contract stability before consumers rely on it \u2192 010's README section and\n  OpenAPI parameters published in the same reviewed change, tests pinning the\n  behavior, and 010 completing before 020/030 begin (dependency declarations).\n  Stability here means decided, documented, and pinned \u2014 not versioned\n  release management, which the fixture has no mechanism for.\n- Preservation of unparameterized API and client behavior \u2192 010's\n  exact-response regression test and 020's request-shape regression test;\n  all three existing suites stay green.\n- Client exposes the capability against the stable contract \u2192 020's\n  conformance test running the real client over real HTTP. Does not cover CLI\n  rendering.\n- CLI exposes the capability and proves the production client-to-service path\n  \u2192 030's end-to-end check: real CLI invocation, production\n  `NotesClient.from_environment()`, subprocess-served real app, stdout\n  assertions. This is the only check that traverses all three components\n  together; it deliberately does not cover hosted deployment or concurrency.\n- Documentation per boundary \u2192 the changed README pages themselves, reviewed\n  in the same change as the code that makes them true.\n\n### Additional implementation verification\n\nRunning all three existing suites green after each subtask is supporting\nregression evidence only; it is not the decisive evidence for any requirement\nabove.\n",
    "tasks/20261101-notes-query-capability/010-api-query-contract.md": "# API: define and stabilize the notes query contract\n\nAdd optional query parameters for bounded pagination, stable sorting, and\noptional text filtering to `GET /notes/`, keep the unparameterized response\nidentical to today, write the contract into the maintained public docs, and\npin it with route tests. This subtask completes before either consumer builds\non the contract.\n\nParent Task: tasks/20261101-notes-query-capability/000-main.md\n\n## Requirements checklist\n\n- [ ] `GET /notes/` accepts the approved optional query parameters implementing bounded pagination, stable sorting, and optional text filtering; out-of-range or disallowed values are rejected with 422. Parameter specifics are the parent plan's proposed contract, binding once approved.\n- [ ] When any query parameter is supplied, results return in a deterministic total order: the requested sort key with unique `id` as final tiebreaker, `id` ascending when sort is not given.\n- [ ] The unparameterized `GET /notes/` response is unchanged \u2014 every note as a JSON array, content, shape, and ordering exactly as today \u2014 proven by regression evidence.\n- [ ] The contract (parameters, defaults, bounds, ordering rule, response shape, error behavior) is documented in the root `README.md` in the same change, with OpenAPI reflecting it from route code.\n- [ ] Route tests through the real app prove: page bounds and cap enforcement, deterministic ordering including the tiebreaker, text filtering, combined parameters, and the unparameterized regression case.\n\nDepends On: none. Must complete before\n`tasks/20261101-notes-query-capability/020-client-query-support.md` and\n`tasks/20261101-notes-query-capability/030-cli-query-command.md` start.\n\n## Supporting details\n\n**Proposed contract slice (binding once the parent plan is approved).**\nOptional parameters on `GET /notes/`: `limit` (int 1\u2013100, default 20 when any\nparameter is used), `offset` (int \u2265 0, default 0), `sort` (one of `id`,\n`title`, `description`, optional leading `-` for descending, default `id`\nascending), `q` (case-insensitive substring on title or description). Response\nstays a bare JSON array of note objects, up to `limit` items, empty array for\nno matches; no envelope, no total. Supplying no parameters reproduces today's\nbehavior exactly.\n\n**Current code facts.**\n\n- `src/app/api/notes.py:8-10` \u2014 `read_all_notes()` returns `crud.get_all()`;\n  no parameters, no ordering. `src/app/api/crud.py:4-5` \u2014 `get_all()` fetches\n  the whole table.\n- Schema (`src/app/db.py`): `id` (PK), `title` (String(50)),\n  `description` (String(50)). No timestamps, so the sort whitelist is limited\n  to these three columns.\n- Stack: `databases` + SQLAlchemy core; selects support\n  `.where()/.order_by()/.offset()/.limit()`; `ilike` is available for `q`.\n- `fastapi.Query(ge=..., le=...)` produces the framework's standard 422\n  responses; the app has no other custom error surface today.\n- Router prefix is `/notes` (`src/app/main.py:15`).\n\n**Harness facts.**\n\n- `src/tests/conftest.py` builds `TestClient(app)` without a context manager\n  while `database.connect()` runs in the lifespan hook; the connection may not\n  be established in the current suite. Route tests should use\n  `with TestClient(app)` or otherwise ensure connection \u2014 verify during\n  execution.\n- Importing `app.db` creates `./notes.db` in the process CWD at import time;\n  the file is not gitignored. Keep it out of commits.\n- The SQLite DB path is CWD-relative; irrelevant for in-process TestClient\n  tests, critical for any subprocess-served run (020/030).\n- `docs/development/index.md` records that no notes-query specification\n  exists. Do not create a spec page under `docs/` unless the parent plan's\n  documentation decision is changed by approval (smallest-structure rule).\n\n## Implementation plan\n\nStatus: Draft\n\n**Design.** Extend `read_all_notes` with the four optional `fastapi.Query`\nparameters. Add a query path in `crud` that applies `where` (for `q`, as\n`OR(ilike(title), ilike(description))`), `order_by` (whitelisted column,\ndescending on `-` prefix, then `id` ascending as tiebreaker), `offset`, and\n`limit` \u2014 applied only when at least one parameter is supplied. The\nunparameterized request keeps calling today's `get_all()` branch unchanged, so\npreservation holds by construction, not by coincidence. Validate `sort`\nagainst the whitelist in the handler (422 on unknown values) and bounds via\n`Query` constraints.\n\n**Order logic.** Implementation, tests, and README contract section land as\none reviewed change; the milestone is a stable, documented, pinned contract.\nNothing downstream may start until this subtask's requirements are checked.\n\n**Verification.** Decisive evidence: route tests through `app.main.app` via\nTestClient on a seeded temporary SQLite DB, crossing routing, validation,\nhandler, and serialization at the public boundary. Cases: unparameterized\nresponse equals the full seeded set exactly; pagination across multiple pages\nreconstructs the set without gaps or duplicates; `limit=100` accepted,\n`limit=101`, `limit=0`, and negative rejected with 422; `sort=title` with\nduplicate titles shows the `id` tiebreaker and is stable across repeated\nrequests; `sort=-title` reverses; `q` matches case-insensitively in either\nfield; `q` with no matches returns `[]`; combined `q`+`sort`+`limit`+`offset`\nbehaves as the intersection. Deliberately not covered here: real socket\ntransport (covered in 020/030) and consumer surfaces.\n\n**Risks.** ASCII-only case folding for `q` (document, don't over-claim);\nunparameterized regression (pinned by the exact-response test); import-time\n`notes.db` artifact (keep out of commits); lifespan/connection harness\nquestion (verify and use `with TestClient(app)`).\n\n### Implementation decisions and open questions\n\nGoverned by the parent plan's decisions 1\u20136 and 12. Local reversible choices\n(helper naming in `crud`, test file layout) resolve at execution.\n\n### Documentation\n\nRoot `README.md` gains the query contract in this same change, replacing the\n\"returns every note as a JSON array\" framing with current supported behavior.\nOpenAPI updates itself from the route signature; never hand-edit generated\noutput.\n\n### Task checklist\n\n- [ ] Add query parameters to `read_all_notes` and the conditional query path in `crud`, preserving the unparameterized branch.\n- [ ] Add route tests for the cases listed under Verification.\n- [ ] Update root `README.md` with the contract.\n- [ ] Existing API suite stays green.\n\n### Requirement verification\n\n- Query capability and its bounds/order/filter semantics \u2192 the route tests\n  named above through the real app. Not covered: real network transport,\n  consumer surfaces.\n- Contract stability \u2192 README section plus OpenAPI parameters published in the\n  same reviewed change, tests pinning behavior, and this subtask completing\n  before 020/030 start. Not covered: release/versioning mechanics (the fixture\n  has none).\n- Unparameterized preservation \u2192 the exact-response regression test on seeded\n  rows. Not covered: client request shape (020's evidence).\n",
    "tasks/20261101-notes-query-capability/020-client-query-support.md": "# Client: expose the notes query capability on NotesClient\n\nExpose the approved query capability on `NotesClient` so any Python consumer\ncan paginate, sort, and filter against the stable HTTP contract, without\nchanging the existing unparameterized call behavior, and prove the client's\ncontract conformance against the real running service.\n\nParent Task: tasks/20261101-notes-query-capability/000-main.md\n\n## Requirements checklist\n\n- [ ] `NotesClient` exposes the query capability with parameters matching the approved contract, mapping them to the stable HTTP contract and omitting any parameter not supplied.\n- [ ] Existing `list_notes()` behavior is preserved: a parameter-free request to `/notes/` returning the parsed JSON list \u2014 proven by request-shape regression evidence.\n- [ ] An integration test proves the real client against the real running service over real HTTP, covering at least one paginated, one sorted, and one filtered round trip. This is the decisive check for this subtask; fake-transport tests stay supporting evidence only.\n- [ ] `packages/notes_client/README.md` describes the new surface in the same change.\n\nDepends On: `tasks/20261101-notes-query-capability/010-api-query-contract.md`\n(the contract must be stable before this package relies on it).\nDepended on by: `tasks/20261101-notes-query-capability/030-cli-query-command.md`.\n\n## Supporting details\n\n**Proposed client surface (binding once the parent plan is approved).**\n`list_notes(limit=None, offset=None, sort=None, q=None)`. Unset parameters are\nomitted from the query string entirely, so an unparameterized call sends\nexactly today's request (`GET /notes/` with no query component) and returns\nthe parsed JSON list.\n\n**Current code facts.**\n\n- `packages/notes_client/notes_client/client.py` \u2014 `NotesClient(transport)`;\n  `from_environment()` builds an `httpx.Client` from `NOTES_API_URL` (default\n  `http://127.0.0.1:8000`); `list_notes()` returns\n  `self.transport.get(\"/notes/\").json()`.\n- Package `pyproject.toml`: `notes-client` 0.1.0, depends on `httpx` only.\n- Existing tests (`packages/notes_client/tests/`) use a fake transport whose\n  `get()` accepts `**kwargs`; they can verify call mapping but not contract\n  conformance.\n- Error-path behavior: the client does not raise on HTTP error statuses today.\n  Parent decision 9 keeps it that way \u2014 do not add `raise_for_status` in this\n  task; record as a possible follow-up instead.\n\n**Harness facts.**\n\n- No `uvicorn` is declared anywhere in the fixture; serving the real app in\n  the integration test requires introducing it (parent plan decision 11:\n  recommend root `pyproject.toml` dependencies).\n- The service DB path is CWD-relative (`sqlite:///./notes.db`): launch the\n  server subprocess from a temporary working directory and wait for readiness\n  before testing.\n- Seed data through the real HTTP API (`POST /notes/` with plain `httpx`) so\n  the fixture itself stays on the production path.\n- Keep this integration harness local to `packages/notes_client/tests/`;\n  `packages/` and `apps/` are independently maintained and share no test code.\n- Recommend bumping `notes-client` to 0.2.0 in this change (additive public\n  surface on a 0.x package) \u2014 parent plan decision 10.\n\n## Implementation plan\n\nStatus: Draft\n\n**Design.** Extend `list_notes()` with the four optional keyword parameters.\nBuild the request's `params` dict from supplied values only and pass it to the\ntransport `get`; absent parameters produce the same parameter-free request as\ntoday. Return the parsed JSON list unchanged.\n\n**Order logic.** Starts only after 010 completes (stable contract, real\nservice to conform to). Its own milestone \u2014 client surface implemented and\nconformance-proven \u2014 gates 030.\n\n**Verification.** Decisive evidence: an integration test that launches the\nreal app via a `uvicorn` subprocess (temporary CWD, ephemeral port, readiness\nwait), seeds notes over HTTP, then drives the real `NotesClient` (via\n`from_environment()` with `NOTES_API_URL` pointed at the test server) through\npaginated, sorted, and filtered calls, asserting results match the seeded\ndata under the approved contract semantics. Request-shape regression: extend\nthe fake-transport unit test to capture the request and assert that\n`list_notes()` with no arguments issues a query-string-free `GET /notes/`.\nDeliberately not covered: CLI rendering (030), hosted deployment.\n\n**Risks.** Contract drift between package and service \u2014 caught by the\nconformance test against the real service; harness flakiness from port or\nreadiness races \u2014 use an ephemeral port and poll readiness with a bounded\ntimeout; `notes.db` leakage \u2014 temporary CWD for the server process.\n\n### Implementation decisions and open questions\n\nGoverned by parent plan decisions 4\u20137, 9\u201311. Local reversible choices (params\ndict construction, fixture structure) resolve at execution.\n\n### Documentation\n\n`packages/notes_client/README.md` documents the new parameters and their\nsemantics in this same change (audience: Python consumers of the package).\n\n### Task checklist\n\n- [ ] Extend `list_notes()` with optional keyword parameters; omit unset values from the query string.\n- [ ] Add the real-service integration test (uvicorn subprocess, temp CWD, seeded over HTTP).\n- [ ] Extend the fake-transport unit test with the request-shape regression case.\n- [ ] Update `packages/notes_client/README.md`; bump package to 0.2.0.\n- [ ] Existing client suite stays green.\n\n### Requirement verification\n\n- Client exposes the capability against the stable contract \u2192 the real-client\n  integration test over real HTTP. Not covered: CLI rendering.\n- Unparameterized preservation \u2192 the request-shape regression case plus the\n  existing suite staying green. Not covered: API response content (010's\n  evidence).\n- Documentation \u2192 the changed `packages/notes_client/README.md` page, reviewed\n  in the same change as the code.\n",
    "tasks/20261101-notes-query-capability/030-cli-query-command.md": "# CLI: query flags and the production-path proof\n\nExpose the query capability to CLI users as flags on the `list` command and\nprove the production client-to-service path end to end: a real CLI invocation\nthrough the production `NotesClient` against a real running service, with no\ntest doubles in that path.\n\nParent Task: tasks/20261101-notes-query-capability/000-main.md\n\n## Requirements checklist\n\n- [ ] CLI users can query notes with pagination, sorting, and filtering flags on `notes list`, passed through to the production client; output rendering is unchanged.\n- [ ] The decisive end-to-end check traverses the real production path \u2014 CLI invocation \u2192 production `NotesClient.from_environment()` \u2192 running service over HTTP \u2014 and asserts that stdout reflects the requested paging, sorting, and filtering. Fake-client unit tests remain supporting evidence only.\n- [ ] Existing `notes list` output behavior is preserved for the unparameterized case, covered by both the unit regression and the end-to-end check.\n- [ ] `apps/notes_cli/README.md` documents the new flags in the same change.\n\nDepends On: `tasks/20261101-notes-query-capability/010-api-query-contract.md`\nand `tasks/20261101-notes-query-capability/020-client-query-support.md`\n(the CLI consumes the client method against the stable contract).\n\n## Supporting details\n\n**Proposed CLI surface (binding once the parent plan is approved).** The\n`list` subcommand gains `--limit` (int \u2265 1), `--offset` (int \u2265 0), `--sort`\n(choices: `id`, `title`, `description` and their `-`-prefixed descending\nforms), and `--query` (free text, mapped to the client's `q`). argparse\nvalidates ranges and choices locally so normal CLI use never triggers a 422;\nvalues pass through to `client.list_notes(...)`.\n\n**Current code facts.**\n\n- `apps/notes_cli/cli.py` \u2014 `main(argv=None, client=None)` builds an\n  argparse parser with a required `list` subcommand; `list_command(client)`\n  prints `{id}: {title}` per note from `client.list_notes()`. A `client`\n  argument already allows injection, but the decisive check uses the\n  production client, not an injected double.\n- `apps/notes_cli/pyproject.toml` \u2014 console script\n  `notes = \"notes_cli.cli:main\"`; declares **no dependencies** despite\n  importing `notes_client` (parent plan decision 10: add the dependency and\n  report it).\n- **Pre-existing defects to fix incidentally and report:** the console script\n  targets a `notes_cli` package directory that does not exist\n  (`apps/notes_cli/` contains `cli.py` directly), and\n  `apps/notes_cli/tests/test_cli.py` calls `list_command` without importing\n  it, so the current CLI test cannot pass as shipped. 030 makes the real CLI\n  code importable in tests and repairs the missing import; that repair is\n  reported, not silent.\n- The CLI module has no `__main__` block, so the automated decisive check\n  invokes `main(argv)` in-process with the production client; the installed\n  `notes` console script remains the manual equivalent.\n- Existing CLI tests use a fake client (`tests/conftest.py`); kept as\n  rendering-regression evidence only.\n\n**Harness facts.**\n\n- Real-service runs need `uvicorn` (introduced per parent plan decision 11)\n  and a subprocess launched from a temporary working directory (the service\n  DB path is CWD-relative), with readiness polling and an ephemeral port.\n- Seed notes over real HTTP (`POST /notes/`) before invoking the CLI.\n- Keep this end-to-end harness local to `apps/notes_cli/tests/`; no shared\n  test code with the client package.\n\n## Implementation plan\n\nStatus: Draft\n\n**Design.** Extend the `list` subparser with `--limit`, `--offset`, `--sort`,\nand `--query`, with argparse-level validation (type/range/choices) matching\nthe approved contract so user errors surface locally with a clean message and\nnonzero exit. Pass validated values through to the production client method;\nleave `list_command` rendering as is.\n\n**Order logic.** Last subtask: consumes the client method (020) against the\nstable contract (010). Its milestone \u2014 the production path proven end to end \u2014\ncompletes the feature.\n\n**Verification.** Decisive evidence, named exactly: start the real app with a\n`uvicorn` subprocess from a temporary CWD on an ephemeral port; poll\nreadiness; seed at least five notes over HTTP including duplicate-title rows\nand filterable text; set `NOTES_API_URL` to the test server; invoke\n`main([\"list\", \"--limit\", \"2\", \"--offset\", \"2\", \"--sort\", \"title\",\n\"--query\", \"<term>\"])` (and variants) with the production\n`NotesClient.from_environment()`; assert stdout lines match the expected\npage of the filtered, title-sorted set, and that the unparameterized\n`main([\"list\"])` output equals today's `{id}: {title}` rendering of every\nnote. No test doubles appear in this path. Supporting evidence: the repaired\nfake-client unit test for rendering. Deliberately not covered: hosted\ndeployment, concurrency, and the console-script packaging itself (the missing\n`notes_cli` package directory is fixed only as far as tests require; if full\nconsole-script installability is wanted, that is a follow-up).\n\n**Risks.** The e2e harness is the most complex test in the feature (process\nlifecycle, ports, readiness) \u2014 bound all waits with timeouts and clean up the\nsubprocess; scope creep via the pre-existing packaging defects \u2014 fix the\nminimum needed for the decisive check and report the rest; regression risk on\nunparameterized output \u2014 covered by the e2e case plus the unit test.\n\n### Implementation decisions and open questions\n\nGoverned by parent plan decisions 4\u20138 and 10\u201311. Local reversible choices\n(exact flag names if `--query` feels wrong, validation messages) resolve at\nexecution; flag names are user-visible, so any deviation is reported.\n\n### Documentation\n\n`apps/notes_cli/README.md` documents the new flags with examples in this same\nchange (audience: CLI users).\n\n### Task checklist\n\n- [ ] Add `--limit`, `--offset`, `--sort`, `--query` to the `list` subcommand with argparse validation; pass through to the production client.\n- [ ] Add the end-to-end production-path test exactly as named under Verification.\n- [ ] Fix the missing `list_command` import in `test_cli.py` and make the CLI module importable; report both repairs.\n- [ ] Add the undeclared `notes-client` dependency to `apps/notes_cli/pyproject.toml`; report it.\n- [ ] Update `apps/notes_cli/README.md`.\n- [ ] Existing CLI suite stays green.\n\n### Requirement verification\n\n- CLI exposes the capability and proves the production client-to-service path\n  \u2192 the named end-to-end check; it is the only check that traverses CLI,\n  client, and service together, which is why it cannot be waived or replaced\n  by the per-side tests. Not covered: hosted deployment, concurrency.\n- Unparameterized CLI output preserved \u2192 the `main([\"list\"])` e2e case plus\n  the fake-client rendering unit test. Not covered: API or client internals\n  (010/020 evidence).\n- Documentation \u2192 the changed `apps/notes_cli/README.md` page, reviewed in the\n  same change as the code.\n"
  },
  "task_tree": {
    "all_dependencies_resolve": true,
    "all_parent_links_resolve": true,
    "coordinating_files": [
      "tasks/20261101-notes-query-capability/000-main.md"
    ],
    "dependencies": [
      {
        "dependency": "tasks/20261101-notes-query-capability/020-client-query-support.md",
        "resolves": true,
        "task": "tasks/20261101-notes-query-capability/010-api-query-contract.md"
      },
      {
        "dependency": "tasks/20261101-notes-query-capability/030-cli-query-command.md",
        "resolves": true,
        "task": "tasks/20261101-notes-query-capability/010-api-query-contract.md"
      },
      {
        "dependency": "tasks/20261101-notes-query-capability/010-api-query-contract.md",
        "resolves": true,
        "task": "tasks/20261101-notes-query-capability/020-client-query-support.md"
      },
      {
        "dependency": "tasks/20261101-notes-query-capability/030-cli-query-command.md",
        "resolves": true,
        "task": "tasks/20261101-notes-query-capability/020-client-query-support.md"
      },
      {
        "dependency": "tasks/20261101-notes-query-capability/010-api-query-contract.md",
        "resolves": true,
        "task": "tasks/20261101-notes-query-capability/030-cli-query-command.md"
      },
      {
        "dependency": "tasks/20261101-notes-query-capability/020-client-query-support.md",
        "resolves": true,
        "task": "tasks/20261101-notes-query-capability/030-cli-query-command.md"
      }
    ],
    "files": [
      {
        "dependencies": [],
        "has_execution_plan": false,
        "parent_task": null,
        "path": "tasks/20261101-notes-query-capability/000-main.md",
        "phase_terms": [],
        "plan_status": null,
        "requirement_count": 6,
        "title": "Supported notes-query capability across API, client, and CLI"
      },
      {
        "dependencies": [
          "tasks/20261101-notes-query-capability/020-client-query-support.md",
          "tasks/20261101-notes-query-capability/030-cli-query-command.md"
        ],
        "has_execution_plan": false,
        "parent_task": "tasks/20261101-notes-query-capability/000-main.md",
        "path": "tasks/20261101-notes-query-capability/010-api-query-contract.md",
        "phase_terms": [],
        "plan_status": null,
        "requirement_count": 5,
        "title": "API: define and stabilize the notes query contract"
      },
      {
        "dependencies": [
          "tasks/20261101-notes-query-capability/010-api-query-contract.md",
          "tasks/20261101-notes-query-capability/030-cli-query-command.md"
        ],
        "has_execution_plan": false,
        "parent_task": "tasks/20261101-notes-query-capability/000-main.md",
        "path": "tasks/20261101-notes-query-capability/020-client-query-support.md",
        "phase_terms": [],
        "plan_status": null,
        "requirement_count": 4,
        "title": "Client: expose the notes query capability on NotesClient"
      },
      {
        "dependencies": [
          "tasks/20261101-notes-query-capability/010-api-query-contract.md",
          "tasks/20261101-notes-query-capability/020-client-query-support.md"
        ],
        "has_execution_plan": false,
        "parent_task": "tasks/20261101-notes-query-capability/000-main.md",
        "path": "tasks/20261101-notes-query-capability/030-cli-query-command.md",
        "phase_terms": [],
        "plan_status": null,
        "requirement_count": 4,
        "title": "CLI: query flags and the production-path proof"
      }
    ],
    "implementation_task_count": 3,
    "parent_links": [
      {
        "child": "tasks/20261101-notes-query-capability/010-api-query-contract.md",
        "parent": "tasks/20261101-notes-query-capability/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20261101-notes-query-capability/020-client-query-support.md",
        "parent": "tasks/20261101-notes-query-capability/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20261101-notes-query-capability/030-cli-query-command.md",
        "parent": "tasks/20261101-notes-query-capability/000-main.md",
        "resolves": true
      }
    ],
    "phase_named_files": [],
    "task_directory_count": 1,
    "task_file_count": 4
  }
}


**Assistant** *(reasoning present)*

```json
{
  "schema_version": 3,
  "scenario_id": "tg05-fastapi-multi-consumer-decomposition",
  "assessment": {
    "outcome_coverage": "complete",
    "missing_outcomes": [],
    "added_obligations": [],
    "semantic_deliverable_count": 3,
    "actual_task_count": 3,
    "deliverable_mappings": [
      {
        "deliverable_id": "QUERY-D1",
        "task_paths": ["tasks/20261101-notes-query-capability/010-api-query-contract.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Contract is first-class in the parent plan (filtering, sorting, pagination, validation, compatibility) and realized in 010: implemented, documented in README/OpenAPI, pinned by tests, with 010 required to complete before 020/030 start — the approved alternative of a parent-held contract with one clear maintained owner."
      },
      {
        "deliverable_id": "QUERY-D2",
        "task_paths": ["tasks/20261101-notes-query-capability/010-api-query-contract.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Route and crud implement the contract against real SQLite; decisive route tests through app.main.app cover bounds, tiebreaker determinism, filtering, and unparameterized preservation; root README/OpenAPI land in the same change."
      },
      {
        "deliverable_id": "QUERY-D3",
        "task_paths": ["tasks/20261101-notes-query-capability/020-client-query-support.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Client surface extends list_notes with request-shape regression preserving current calls; decisive conformance test runs the real client over real HTTP; package README and reported 0.2.0 bump in the same change."
      },
      {
        "deliverable_id": "QUERY-D4",
        "task_paths": ["tasks/20261101-notes-query-capability/030-cli-query-command.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "CLI flags plus the single decisive production-path proof (main() → NotesClient.from_environment() → uvicorn-served service, no test doubles); CLI README in the same change. Integration is owned by the CLI delivery, matching the target's D4."
      }
    ],
    "mergeable_groups": [],
    "unmatched_tasks": [],
    "overpacked_tasks": [],
    "valid_layer_boundaries": [
      "tasks/20261101-notes-query-capability/010-api-query-contract.md",
      "tasks/20261101-notes-query-capability/020-client-query-support.md",
      "tasks/20261101-notes-query-capability/030-cli-query-command.md"
    ],
    "automatic_layer_fragments": [],
    "dependency_issues": [],
    "crossing_ownership": "complete",
    "fragmentation_severity": "none",
    "fragmentation_ratio": 1.0,
    "quality_metrics": {
      "fragmentation": {
        "status": "none",
        "occurrences": []
      },
      "phase_only_children": {
        "status": "none",
        "occurrences": []
      },
      "layer_split_without_independent_value": {
        "status": "none",
        "occurrences": []
      },
      "evidence_reownership": {
        "status": "none",
        "occurrences": []
      },
      "unsafe_dependencies": {
        "status": "none",
        "occurrences": []
      },
      "piecewise_crossing_evidence": {
        "status": "none",
        "occurrences": []
      }
    },
    "partition_quality_score": 95,
    "handoff_quality_score": 95,
    "summary": "Three tasks cover all five approved outcomes and map onto the target's four deliverables through an explicitly acceptable alternative: the contract is held first-class in the parent plan with 010 as its single maintained owner (D1+D2 → 010, D3 → 020, D4 → 030), within the acceptable 3–5 partition size. Each task bundles implementation, tests, and documentation for one independently owned surface (public API, package with its own pyproject and 0.x compatibility boundary, CLI app), so no phase-only or layer-fragment children exist and nothing needs merging. Every important crossing has one named decisive check through the exact production connection: route tests through app.main.app on a seeded real SQLite DB (route→storage), real NotesClient over real HTTP against a uvicorn-served app with ASGITransport explicitly rejected (client transport→production API), and a no-doubles CLI→client→service e2e (CLI through actual client and service); fakes are demoted to supporting evidence, so no evidence re-ownership or piecewise substitution. File-level Depends On declarations are acyclic and required (010 gates 020/030 for contract stability as the request demands; 030 also gates on 020); the parsed task_tree metadata showing 010 depending on 020/030 appears to misread the 'Must complete before'/'Depended on by' lines and does not reflect the task files themselves. Incidental additions (uvicorn dependency, notes-client 0.2.0 bump, CLI import/packaging repairs) are reported decisions that serve the requested production-path proof, not scope creep."
  }
}
```
