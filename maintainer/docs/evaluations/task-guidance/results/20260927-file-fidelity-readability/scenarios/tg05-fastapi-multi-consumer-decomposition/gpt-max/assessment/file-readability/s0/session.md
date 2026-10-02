# Session — tg05-fastapi-multi-consumer-decomposition · file-readability-assessment-gpt-max-s0 · glm max

- Run: `20260928T204005.586619Z-task-guidance-file-readability-tg05-fastapi-multi-consumer-decomposition-gpt-max-s0-a6d6b601`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `d39c973d285d353f…`)
- Config: [glm-assessor-max](../../../../../../shared/configs/glm-assessor-max.json)
- Activity: 5 messages · 1 tool calls · 1 tool results
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

#### tasks/20260926-notes-query/000-main.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-notes-query/000-main.md — Requirements checklist | 191 | 0 | 0 | 7 | 11 | 0 | 0 | 0 | 3 |
| tasks/20260926-notes-query/000-main.md — Scope | 78 | 2 | 10 | 7 | 11 | 0 | 0 | 0 | 3 |
| tasks/20260926-notes-query/000-main.md — Unresolved requirement questions | 185 | 1 | 21 | 6 | 15 | 0 | 0 | 0 | 2 |
| tasks/20260926-notes-query/000-main.md — Planning decisions | 74 | 0 | 0 | 3 | 15 | 0 | 0 | 0 | 1 |
| tasks/20260926-notes-query/000-main.md — Supporting facts | 118 | 0 | 0 | 6 | 11 | 0 | 0 | 0 | 12 |
| tasks/20260926-notes-query/000-main.md — Subtasks | 66 | 0 | 0 | 4 | 7 | 0 | 0 | 0 | 4 |
| tasks/20260926-notes-query/000-main.md — Execution plan | 787 | 7 | 86 | 26 | 13 | 5 | 0 | 0 | 20 |

#### tasks/20260926-notes-query/010-contract.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-notes-query/010-contract.md — Requirements checklist | 105 | 2 | 3 | 5 | 13 | 0 | 0 | 0 | 1 |
| tasks/20260926-notes-query/010-contract.md — Scope | 42 | 1 | 42 | 0 | 0 | 0 | 0 | 0 | 0 |
| tasks/20260926-notes-query/010-contract.md — Supporting facts | 48 | 0 | 0 | 4 | 14 | 0 | 0 | 0 | 2 |
| tasks/20260926-notes-query/010-contract.md — Execution plan | 325 | 4 | 53 | 9 | 15 | 4 | 0 | 0 | 10 |

#### tasks/20260926-notes-query/020-api.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-notes-query/020-api.md — Requirements checklist | 104 | 2 | 3 | 5 | 10 | 0 | 0 | 0 | 4 |
| tasks/20260926-notes-query/020-api.md — Scope | 34 | 1 | 34 | 0 | 0 | 0 | 0 | 0 | 0 |
| tasks/20260926-notes-query/020-api.md — Supporting facts | 53 | 0 | 0 | 4 | 12 | 0 | 0 | 0 | 8 |
| tasks/20260926-notes-query/020-api.md — Execution plan | 370 | 5 | 59 | 12 | 14 | 4 | 0 | 0 | 5 |

#### tasks/20260926-notes-query/030-python-client.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-notes-query/030-python-client.md — Requirements checklist | 82 | 2 | 3 | 6 | 11 | 0 | 0 | 0 | 6 |
| tasks/20260926-notes-query/030-python-client.md — Scope | 44 | 1 | 44 | 0 | 0 | 0 | 0 | 0 | 0 |
| tasks/20260926-notes-query/030-python-client.md — Supporting facts | 44 | 0 | 0 | 3 | 11 | 0 | 0 | 0 | 4 |
| tasks/20260926-notes-query/030-python-client.md — Execution plan | 342 | 4 | 57 | 12 | 15 | 4 | 0 | 0 | 4 |

#### tasks/20260926-notes-query/040-cli.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-notes-query/040-cli.md — Requirements checklist | 116 | 2 | 3 | 8 | 12 | 0 | 0 | 0 | 7 |
| tasks/20260926-notes-query/040-cli.md — Scope | 22 | 1 | 22 | 0 | 0 | 0 | 0 | 0 | 0 |
| tasks/20260926-notes-query/040-cli.md — Supporting facts | 52 | 0 | 0 | 3 | 13 | 0 | 0 | 0 | 5 |
| tasks/20260926-notes-query/040-cli.md — Execution plan | 462 | 4 | 68 | 19 | 13 | 4 | 0 | 0 | 10 |

The produced task files:

### tasks/20260926-notes-query/000-main.md

````markdown
# Add a stable notes-query capability across service, client, and CLI

Plan and coordinate one supported notes-query capability across the public
FastAPI service, reusable `notes_client` package, and `notes` CLI while
preserving the existing unparameterized collection behavior.

## Requirements checklist

- [ ] R1. The public query contract defines bounded pagination, stable sorting,
  optional text filtering, response shape, validation, and compatibility
  behavior before the client or CLI implementation relies on it.
- [ ] R2. The public notes collection API supports the approved query contract,
  including bounded pagination, deterministic sorting, and optional text
  filtering.
- [ ] R3. A request to the existing collection route without query parameters
  continues to return the current JSON-array behavior, and existing CRUD
  routes remain compatible.
- [ ] R4. `NotesClient` exposes the approved query capability while
  `list_notes()` with no arguments preserves its current request and return
  behavior.
- [ ] R5. `notes list` exposes the approved query capability through the
  reusable client and preserves the existing no-option command behavior.
- [ ] R6. Verification crosses the relevant public boundaries: the API is
  tested through the service route, the client is tested for contract mapping,
  and the CLI has a decisive test through the production client to a real
  service endpoint.
- [ ] R7. Maintained documentation describes the approved contract and the
  shipped service, client, and CLI behavior without presenting unimplemented
  behavior as current guidance.

## Scope

In scope:

- The collection query on `GET /notes/`.
- The corresponding `NotesClient.list_notes(...)` public method.
- Query options on the existing `notes list` command.
- Contract, compatibility, regression, integration, and documentation work
  owned by those three boundaries.

Out of scope unless the approved contract explicitly requires it:

- Changes to note creation, reading by ID, updating, or deletion.
- New persistence models, authentication, authorization, or unrelated API
  versioning.
- A separate search resource or a second client/CLI abstraction.

## Unresolved requirement questions

These questions change the public contract and must be answered before this
Draft plan becomes Approved or downstream consumer work begins.

- Q1 — Pagination: should the wire contract use `offset`/`limit`,
  page-number/page-size, or another model? What are the minimum, default, and
  maximum bounds, and does an absent pagination argument retain the current
  unbounded array behavior?
- Q2 — Sorting: which sortable fields and directions are public, what is the
  default order, and what unique tie-breaker guarantees deterministic results
  when the selected field has equal values?
- Q3 — Text filtering: which note fields are searched, is matching substring
  and case-insensitive, and what query parameter name and empty-value behavior
  are public?
- Q4 — Response shape: should queried responses remain JSON arrays, or should
  they add pagination metadata in an envelope? The same choice determines the
  client return type and CLI rendering.
- Q5 — Invalid input: what status and error shape should out-of-range,
  unsupported, or conflicting query values produce?
- Q6 — CLI surface: which option names map to the HTTP parameters, and should
  the existing one-line-per-note output remain unchanged when query options
  are supplied?

## Planning decisions

- Use one parent task with separate children for the contract gate, service,
  reusable package, and CLI. Each is an independently maintained public
  boundary with its own acceptance evidence.
- Sequence the work as contract → service → client → CLI. The contract child
  is a gate; it does not authorize consumer implementation while its public
  choices remain unresolved.
- Keep this handoff in `Draft` status. Creating these task files does not
  authorize implementation.

## Supporting facts

- `src/app/api/notes.py` currently exposes `GET /notes/` as an unparameterized
  collection route and returns `await crud.get_all()` directly.
- `src/app/api/crud.py` currently performs an unrestricted `notes.select()`;
  there is no explicit ordering, filtering, or pagination abstraction.
- `packages/notes_client/notes_client/client.py` currently implements
  `list_notes()` as `transport.get("/notes/").json()` with no arguments.
- `apps/notes_cli/cli.py` currently prints every result from
  `client.list_notes()` and already has a `client=None` test seam. Existing
  CLI tests use a fake client, so they do not prove the production
  client-to-service path.
- Existing tests cover only collection existence/array shape, a minimal client
  return type, and CLI output. They do not establish query semantics or
  cross-package integration.
- `docs/development/index.md` explicitly records that no notes-query
  specification exists. The service, package, and CLI READMEs currently
  describe only unparameterized behavior.

## Subtasks

- [ ] `tasks/20260926-notes-query/010-contract.md` — resolve and freeze the
  public notes-query contract before consumer implementation.
- [ ] `tasks/20260926-notes-query/020-api.md` — implement and verify the
  service-side query behavior against the approved contract.
- [ ] `tasks/20260926-notes-query/030-python-client.md` — expose the contract
  through the reusable Python client while preserving its no-argument API.
- [ ] `tasks/20260926-notes-query/040-cli.md` — expose the query through the
  CLI and prove the production client-to-service path.

## Execution plan

Status: Draft

The contract is the compatibility boundary for all three consumers. The first
child will record the parameter names, types, bounds, sorting and filtering
semantics, response shape, invalid-input behavior, and a compatibility matrix
for requests with and without query parameters. A reviewed contract document
must be accepted before service consumers are implemented; if a public choice
changes later, this plan returns to Draft and the dependent work is
reassessed.

After the contract gate, the service child will own the HTTP parameter
validation and database query behavior. The route and CRUD layer should keep
query construction inside the service, apply a unique tie-breaker for stable
ordering, enforce the approved pagination bounds, and retain the existing
no-parameter response behavior. Its decisive evidence is an integration test
through the FastAPI route and real SQLite-backed CRUD path.

The client child will map only the approved options to query parameters.
Omitting all options must continue to call `/notes/` without a query string
and return the existing list-compatible result. Its focused tests can use a
recording transport for serialization and regression behavior; the full
client-to-service connection is deliberately verified by the CLI child.

The CLI child will add the approved command options and keep HTTP ownership in
`NotesClient`. Existing rendering tests may retain a fake client for local
formatting, but the decisive query test must invoke the CLI without injecting a
fake client, configure the production client to an actual HTTP listener, and
assert the result returned by the running FastAPI service. If the repository
needs a test-only server launcher, that dependency and its lifecycle belong
to the CLI integration setup and must not replace the production request path.

Once all children are complete, run the repository's service, client, and CLI
tests together and inspect the maintained documentation for consistency. The
parent remains incomplete until the contract approval and real-path evidence
are recorded.

### Implementation decisions and open questions

The boundary split and execution order are decided for planning purposes. The
following public choices remain open because they affect all consumers:

- Pagination parameter model, bounds, defaults, and the no-parameter case
  (Q1).
- Sortable fields, direction syntax, default order, and deterministic
  tie-breaking (Q2).
- Filter scope and matching semantics (Q3).
- Array versus metadata envelope and corresponding client/CLI behavior (Q4).
- Invalid-input contract (Q5).
- CLI option names and output compatibility (Q6).

As a low-risk compatibility recommendation, evaluate keeping every response as
an array, applying pagination only when explicitly requested, using a bounded
`limit` plus an `offset`, searching title and description with a
case-insensitive substring, and always adding `id` as the final sort
tie-breaker. These are recommendations for review, not requirements or
decisions in this Draft.

### Documentation

- Add the reviewed contract at `docs/development/notes-query.md` and link it
  from `docs/development/index.md`; keep it visibly marked `Not implemented`
  if it is drafted before the feature ships.
- Update `README.md` with the current public API behavior after the service
  implementation is verified.
- Update `packages/notes_client/README.md` with the supported method
  arguments and no-argument compatibility behavior after the client ships.
- Update `apps/notes_cli/README.md` with the supported list options and
  production usage after the CLI ships.
- Do not make current user documentation claim query support before the
  corresponding implementation and verification are complete.

### Task checklist

- [ ] Resolve Q1–Q6 and approve the contract direction.
- [ ] Complete `010-contract.md` and obtain human contract approval.
- [ ] Complete `020-api.md`, including route-level query and regression
  evidence.
- [ ] Complete `030-python-client.md`, including no-argument compatibility
  evidence.
- [ ] Complete `040-cli.md`, including the real CLI → client → service
  integration check.
- [ ] Run the combined verification and update maintained documentation.
- [ ] Append completion evidence only after all requirements are verified.

### Requirement verification

- R1: Human approval of `docs/development/notes-query.md`, followed by API
  contract tests that exercise every approved query condition at
  `GET /notes/`.
- R2: Service integration tests through FastAPI with seeded notes covering
  bounds, filtering, sort ties, and the approved pagination response.
- R3: A regression request to `GET /notes/` with no query parameters asserting
  the existing JSON-array behavior, plus the existing CRUD route checks.
- R4: Client tests asserting exact no-argument request compatibility and
  contract-compliant serialization for each supplied option.
- R5–R6: The CLI child’s named end-to-end test, invoked without a fake client,
  must traverse the CLI parser, production `NotesClient`, an actual HTTP
  service endpoint, and the returned query result.
- R7: Review the contract and each owning README after implementation; any
  target-only documentation remains marked until its behavior is shipped.

### Additional implementation verification

- Run the focused suites at their owners and then the combined command
  `pytest -q src/tests packages/notes_client/tests apps/notes_cli/tests` from
  the repository root, with any package path setup required by the existing
  project harness.
- Include regression cases for equal sort keys, empty result pages, boundary
  values, and invalid query input once Q1–Q5 are resolved.
````

### tasks/20260926-notes-query/010-contract.md

````markdown
# Freeze the notes-query public contract

Define and obtain approval for the stable notes-query contract that the
FastAPI service, reusable Python client, and CLI will all consume.

## Requirements checklist

- [ ] C1. The contract specifies query parameter names, types, bounds,
  defaults, and invalid-input behavior for bounded pagination.
- [ ] C2. The contract specifies sortable fields, direction syntax, default
  ordering, and a deterministic tie-breaker.
- [ ] C3. The contract specifies text-filter scope, matching and
  case-sensitivity rules, empty values, and the public parameter name.
- [ ] C4. The contract specifies the response shape and compatibility behavior
  for both unparameterized and parameterized requests.
- [ ] C5. The contract maps the HTTP options to the client method and CLI
  surface and is human-approved before dependent implementation begins.

Parent Task: `tasks/20260926-notes-query/000-main.md`

Depends On: None

## Scope

This task owns the public decision boundary and its documentation. It does
not implement the route, client, or CLI. It may draft a target contract, but
the document must not be presented as current supported behavior until the
dependent implementation is shipped.

## Supporting facts

- No notes-query specification currently exists.
- The current service route returns a JSON array for `GET /notes/` without
  parameters.
- The current client method has no arguments and returns the decoded JSON
  directly.
- The current CLI has one `list` command and prints one line per note.

## Execution plan

Status: Draft

Resolve the open public choices from the parent task, then write a compact
contract at `docs/development/notes-query.md`. It should include concrete
request examples, response examples, validation/error examples, a
compatibility matrix, and the client/CLI naming map. Keep the contract
independent of internal module names so it remains useful to HTTP consumers.

Review the document as a public API proposal. Once approved, treat parameter
names, response shape, and compatibility rules as frozen for the dependent
service, client, and CLI tasks. If a later implementation discovery requires a
public change, stop dependent work and return this task and the parent to
Draft before changing the document.

### Implementation decisions and open questions

The document must explicitly resolve pagination model and bounds, sorting and
tie-breaking, text matching, response envelope versus array, invalid-input
behavior, and CLI option names. Do not choose a value merely because it is
convenient for the current SQLite implementation; each choice is part of the
consumer-facing contract.

The compatibility recommendation in the parent—array responses, explicit
pagination, bounded `limit`/`offset`, case-insensitive title/description
substring matching, and an `id` tie-breaker—can be used as a review starting
point but requires approval before it becomes binding.

### Documentation

- Create `docs/development/notes-query.md` as the maintained contract source.
- Update `docs/development/index.md` to link to the specification only after
  the contract has been reviewed; while the feature is not shipped, label the
  target behavior `Not implemented`.
- Do not update package or CLI user guidance in this task; those owners will
  document shipped behavior after implementation.

### Task checklist

- [ ] Resolve the public questions recorded in the parent task.
- [ ] Draft the contract with examples and compatibility matrix.
- [ ] Review and approve the contract.
- [ ] Record approval and unlock `020-api.md`, `030-python-client.md`, and
  `040-cli.md`.

### Requirement verification

- C1–C4: Inspect the reviewed contract for complete request, response,
  validation, and compatibility examples; unresolved public choices leave the
  requirements incomplete.
- C5: Human approval is the decisive gate. The dependent task files must not
  move to execution until the approved contract is available.
````

### tasks/20260926-notes-query/020-api.md

````markdown
# Implement notes-query behavior in the public FastAPI service

Implement the approved notes-query contract at the existing collection route,
including real service/database verification and preservation of the
unparameterized API.

## Requirements checklist

- [ ] A1. `GET /notes/` accepts the approved pagination, sorting, and text
  filtering parameters and enforces their approved validation and bounds.
- [ ] A2. Query results have the approved deterministic ordering, including the
  required unique tie-breaker.
- [ ] A3. `GET /notes/` without query parameters preserves the existing
  JSON-array behavior and does not regress the CRUD routes.
- [ ] A4. Service tests exercise the behavior through FastAPI and the
  SQLite-backed CRUD path, including boundary, tie, filter, empty-result, and
  invalid-input cases required by the contract.
- [ ] A5. Service-facing documentation reflects only verified, shipped
  behavior.

Parent Task: `tasks/20260926-notes-query/000-main.md`

Depends On: `tasks/20260926-notes-query/010-contract.md`

## Scope

This task owns the HTTP route, service query construction, and service-level
tests. It does not change client serialization or CLI parsing. The route
shape and all public validation behavior come from the approved contract.

## Supporting facts

- `src/app/api/notes.py` currently delegates the collection route to
  `crud.get_all()` without query parameters.
- `src/app/api/crud.py` currently issues an unrestricted SQLAlchemy select.
- `src/tests/test_notes.py` uses `fastapi.testclient.TestClient` and currently
  verifies only that the collection response is a list.
- The notes table has `id`, `title`, and `description`; no pagination metadata
  or query-specific persistence is currently present.

## Execution plan

Status: Draft

After `010-contract.md` is approved, introduce a service-side query
representation at the route boundary and pass it to CRUD/query construction.
Keep parameter validation at the public HTTP boundary and make the SQL query
apply filtering, ordering, and pagination in a deterministic order. The
ordering implementation must include the contract’s unique tie-breaker even
when multiple notes share the requested sort value.

Preserve the existing no-parameter path deliberately: a request with no query
parameters must retain its current response shape and compatibility semantics.
Do not make consumer behavior depend on undocumented database insertion order;
where the approved contract requires stable ordering, express it in the
query.

Add route-level tests using the actual FastAPI app and SQLite-backed CRUD
operations. Seed notes with duplicate sort values and matching/non-matching
text, then assert the complete approved contract through HTTP responses rather
than calling CRUD functions directly.

### Implementation decisions and open questions

The public decisions are owned by `010-contract.md`; this task must not
silently reinterpret them. Internal choices—such as whether to use a small
validated query model or explicit FastAPI parameters—may be resolved locally
provided they preserve the approved wire contract.

If the existing test database lifecycle makes isolation unreliable, improve
the test fixture within this task without changing production persistence or
adding a test-only route.

### Documentation

- Update the root service README with the verified collection-query usage.
- Keep `docs/development/notes-query.md` as the contract source and update
  its implementation status only after the route tests pass.
- Do not document client or CLI behavior here; those claims belong to their
  owning tasks.

### Task checklist

- [ ] Confirm the approved contract from
  `tasks/20260926-notes-query/010-contract.md`.
- [ ] Implement route validation and service/CRUD query behavior.
- [ ] Add route-level regression and query integration tests.
- [ ] Run the service-focused suite and record evidence.
- [ ] Update service-facing documentation with verified behavior.

### Requirement verification

- A1–A2: HTTP integration tests through `TestClient` with real CRUD/database
  execution cover each approved query feature and deterministic ordering.
- A3: A no-query request asserts the existing JSON-array shape and the CRUD
  route regression tests remain green.
- A4: The decisive evidence is the service suite crossing the route, FastAPI
  validation, CRUD, SQL query, and response serialization boundaries.
- A5: Review the root README and contract status after the implementation
  tests succeed.
````

### tasks/20260926-notes-query/030-python-client.md

````markdown
# Expose notes-query through the reusable Python client

Map the approved notes-query contract onto `NotesClient` while keeping the
existing no-argument `list_notes()` call compatible.

## Requirements checklist

- [ ] P1. `NotesClient.list_notes(...)` accepts the approved query options and
  serializes them to the documented HTTP request.
- [ ] P2. `list_notes()` with no arguments continues to request `/notes/`
  without query parameters and returns the current list-compatible result.
- [ ] P3. Client tests cover option mapping, omission of unset values, response
  decoding, and no-argument regression behavior.
- [ ] P4. The package README documents the verified query interface and
  compatibility behavior.

Parent Task: `tasks/20260926-notes-query/000-main.md`

Depends On:

- `tasks/20260926-notes-query/010-contract.md`
- `tasks/20260926-notes-query/020-api.md`

## Scope

This task owns the reusable package API and HTTP request serialization. It
does not own FastAPI query semantics or CLI option parsing. It must consume
the frozen contract rather than expose package-specific names that diverge
from the public HTTP interface without a documented reason.

## Supporting facts

- `NotesClient` accepts an injected transport and has a
  `from_environment()` constructor that creates an `httpx.Client`.
- The current implementation calls `transport.get("/notes/").json()` with no
  arguments.
- The existing client test uses a minimal recording-compatible transport but
  does not assert the requested path or query parameters.

## Execution plan

Status: Draft

After the contract and service are stable, extend `list_notes` with the
approved, clearly named options. Build request parameters from values actually
supplied by the caller so the zero-argument call remains an unparameterized
request. Preserve the client’s direct JSON decoding unless the approved
response contract requires a deliberately documented result model or
envelope.

Expand the client tests with a recording transport that captures path and
keyword arguments. Assert exact serialization and URL-safe handling for each
query option, omission of unset values, decoding of the approved response,
and the unchanged no-argument behavior. Keep one focused client test per
mapping concern; the full service connection is verified by the CLI
integration task.

### Implementation decisions and open questions

The method signature and return type are public package behavior. They remain
blocked on the approved response and option contract. Do not add a second
method or silently change the no-argument return type to make pagination
metadata convenient.

The transport abstraction should remain usable for existing callers. Any
change needed to support a real-path integration test must preserve the
constructor and environment behavior unless the contract explicitly approves
an additive compatibility change.

### Documentation

- Update `packages/notes_client/README.md` with the verified method signature,
  option semantics, response handling, and no-argument compatibility.
- Link to the maintained query contract where appropriate.
- Do not state support until the client tests and dependent service behavior
  are verified.

### Task checklist

- [ ] Confirm the approved HTTP contract and service behavior.
- [ ] Extend `NotesClient.list_notes(...)` with the approved options.
- [ ] Add serialization and no-argument regression tests.
- [ ] Run the package-focused suite and record evidence.
- [ ] Update the package README with current behavior.

### Requirement verification

- P1: Client tests with a recording transport assert the exact path and query
  mapping for every approved option.
- P2: A no-argument test asserts the path `/notes/`, absence of query
  parameters, and the existing list-compatible decoded result.
- P3: The package test suite must collect and pass with the real client class,
  not only a fake client.
- P4: Review the package README against the approved contract and passing
  tests.
````

### tasks/20260926-notes-query/040-cli.md

````markdown
# Expose notes-query through the CLI and prove the production path

Add the approved query options to `notes list`, preserve existing output for
the no-option command, and verify the real CLI → `NotesClient` → FastAPI
service path.

## Requirements checklist

- [ ] L1. `notes list` exposes the approved query options with documented
  names, validation, and forwarding behavior.
- [ ] L2. `notes list` with no query options preserves the current command
  behavior and output contract.
- [ ] L3. The CLI delegates all service access to the production
  `NotesClient`; it does not implement a second HTTP/query protocol.
- [ ] L4. A decisive integration test invokes the CLI without a fake client,
  reaches an actual HTTP-served FastAPI application through the production
  client, and proves the approved pagination, sorting, and filtering result.
- [ ] L5. CLI documentation and tests describe only the verified behavior.

Parent Task: `tasks/20260926-notes-query/000-main.md`

Depends On:

- `tasks/20260926-notes-query/010-contract.md`
- `tasks/20260926-notes-query/020-api.md`
- `tasks/20260926-notes-query/030-python-client.md`

## Scope

This task owns CLI parsing, forwarding, rendering, and the end-to-end
consumer-path evidence. It does not change HTTP semantics or duplicate client
serialization.

## Supporting facts

- `apps/notes_cli/cli.py` currently defines only `notes list`, prints
  `id: title`, and uses `NotesClient.from_environment()` when no client is
  injected.
- Existing CLI tests inject a fake client and therefore prove formatting only.
- The client’s environment-based constructor targets `NOTES_API_URL`, so a
  production-path test must configure that variable and avoid the injected
  fake-client seam.

## Execution plan

Status: Draft

After the contract and client are approved, add the documented list options
to the argument parser and pass only supplied values to
`NotesClient.list_notes(...)`. Keep the existing rendering path for the
approved response shape; if metadata is introduced, define its presentation
in the contract before changing output.

Retain focused unit tests for parser and rendering behavior with a small fake
client where that is the narrowest useful evidence. Add a separate decisive
integration test that:

1. Starts the real FastAPI application behind an actual HTTP listener with
   isolated test data.
2. Seeds notes through a supported service path.
3. Sets `NOTES_API_URL` to that listener.
4. Invokes the CLI production entry point or `main(...)` with no injected
   client and the approved query options.
5. Asserts the command succeeds and prints exactly the notes selected and
   ordered by the running service.

The test must use the production `NotesClient.from_environment()` path and a
real service response. A fake client, mocked transport, direct CRUD call, or
direct invocation of the route is not decisive evidence for L4. Record the
exact focused invocation used by the test suite, for example
`pytest -q apps/notes_cli/tests/test_cli_integration.py`, after the fixture
and server dependency are settled.

### Implementation decisions and open questions

CLI option names and output behavior remain blocked on the approved contract.
The current `client=None` seam may remain for unit-level rendering tests, but
it must not be used by the decisive integration test. If an HTTP server
launcher or test dependency is needed, choose one that exercises the actual
ASGI application and record its lifecycle and dependency ownership; do not
replace the production request with a mocked response.

### Documentation

- Update `apps/notes_cli/README.md` with the verified options, examples, and
  no-option compatibility behavior.
- Link to the query contract without duplicating conflicting semantics.
- Document the real-path integration command in developer-facing test
  guidance only if it is stable and maintained.

### Task checklist

- [ ] Confirm the approved contract and completed client interface.
- [ ] Add parser options and forwarding through `NotesClient`.
- [ ] Preserve and test no-option rendering behavior.
- [ ] Add and pass the real CLI → client → HTTP service integration test.
- [ ] Run the CLI-focused suite and record the exact invocation.
- [ ] Update the CLI README with verified behavior.

### Requirement verification

- L1: Parser tests and a recording-client test assert option names, defaults,
  and forwarding without duplicating HTTP serialization.
- L2: The existing no-option command test remains green and asserts unchanged
  output semantics.
- L3: Code inspection plus tests confirm the CLI calls `NotesClient` rather
  than constructing service requests itself.
- L4: The decisive evidence is the integration test invocation
  `pytest -q apps/notes_cli/tests/test_cli_integration.py` (or its recorded
  maintained equivalent), run with no injected client and an actual
  HTTP-served FastAPI app.
- L5: Review the CLI README against the approved contract and passing tests.
````


**Assistant** *(reasoning present)*

- `Read` {"file_path": "/dev/null/nonexistent-verification-placeholder", "limit": 1}

**Tool `Read`** — failed

> Access denied for path: /dev/null/nonexistent-verification-placeholder

**Assistant** *(reasoning present)*

{
  "schema_version": 1,
  "scenario_id": "tg05-fastapi-multi-consumer-decomposition",
  "assessment": {
    "sections": {
      "tasks/20260926-notes-query/000-main.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "R1 item",
            "quote": "R1. The public query contract defines bounded pagination, stable sorting, optional text filtering, response shape, validation, and compatibility behavior before the client or CLI implementation relies on it.",
            "why": "Seven items at roughly 25–30 words each; R1 is the densest (six contract facets in one sentence), but R-numbering and one-requirement-per-item keep the whole list scannable in a single pass."
          }
        ]
      },
      "tasks/20260926-notes-query/000-main.md — Scope": {
        "grade": "readable",
        "findings": [
          {
            "where": "Out-of-scope list header",
            "quote": "Out of scope unless the approved contract explicitly requires it:",
            "why": "The qualifier is load-bearing (these exclusions are revocable) and lives in the list intro rather than an item, so a reader skimming only the bullets could take the exclusions as absolute; the two-list split itself scans cleanly."
          }
        ]
      },
      "tasks/20260926-notes-query/000-main.md — Unresolved requirement questions": {
        "grade": "readable",
        "findings": [
          {
            "where": "Q1–Q6 items",
            "quote": "Q1 — Pagination: should the wire contract use `offset`/`limit`, page-number/page-size, or another model? What are the minimum, default, and maximum bounds, and does an absent pagination argument retain the current unbounded array behavior?",
            "why": "Six labeled items of 25–35 words each are takeable in one pass because every bullet opens with a topic label; the strain is that each item stacks two to four distinct sub-questions, so answering one Q means unpacking a compound sentence."
          }
        ]
      },
      "tasks/20260926-notes-query/000-main.md — Planning decisions": {
        "grade": "readable",
        "findings": [
          {
            "where": "Sequencing bullet",
            "quote": "Sequence the work as contract → service → client → CLI. The contract child is a gate; it does not authorize consumer implementation while its public choices remain unresolved.",
            "why": "Three short bullets, one decision each; the load-bearing gate rule gets its own item and is found on the first read."
          }
        ]
      },
      "tasks/20260926-notes-query/000-main.md — Supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "CLI fact bullet",
            "quote": "`apps/notes_cli/cli.py` currently prints every result from `client.list_notes()` and already has a `client=None` test seam. Existing CLI tests use a fake client, so they do not prove the production client-to-service path.",
            "why": "Six bullets anchored by code-span paths scan well; this one bullet carries three related facts (behavior, seam, coverage gap), so the gap that justifies R6 is the least prominent element in the section."
          }
        ]
      },
      "tasks/20260926-notes-query/000-main.md — Subtasks": {
        "grade": "readable",
        "findings": [
          {
            "where": "Child bullets",
            "quote": "`tasks/20260926-notes-query/010-contract.md` — resolve and freeze the public notes-query contract before consumer implementation.",
            "why": "Four bullets, each pairing a child file path with a one-line role; the decomposition is graspable at a glance and doubles as the file map for the task set."
          }
        ]
      },
      "tasks/20260926-notes-query/000-main.md — Execution plan": {
        "grade": "partial",
        "findings": [
          {
            "where": "Opening prose run (paragraphs 2–5)",
            "quote": "After the contract gate, the service child will own the HTTP parameter validation and database query behavior. The route and CRUD layer should keep query construction inside the service, apply a unique tie-breaker for stable ordering, enforce the approved pagination bounds, and retain the existing no-parameter response behavior.",
            "why": "Roughly 500 consecutive prose words across five paragraphs (longest 86 words) cover four children, each paragraph mixing actions, constraints, and evidence with no per-child heading; the reader must hold the whole run to compare what each child owns, and rules like the Draft-return trigger sit mid-paragraph."
          },
          {
            "where": "Implementation decisions and open questions — recommendation paragraph",
            "quote": "evaluate keeping every response as an array, applying pagination only when explicitly requested, using a bounded `limit` plus an `offset`, searching title and description with a case-insensitive substring, and always adding `id` as the final sort tie-breaker.",
            "why": "Five discrete recommendations are compressed into one prose sentence; a reviewer cannot scan, challenge, or reference any single recommendation without re-parsing the sentence."
          },
          {
            "where": "Requirement verification — R5–R6 bullet",
            "quote": "R5–R6: The CLI child’s named end-to-end test, invoked without a fake client, must traverse the CLI parser, production `NotesClient`, an actual HTTP service endpoint, and the returned query result.",
            "why": "One bullet serves two requirement IDs, so an auditor checking R5 alone cannot tell which clause of the sentence discharges it; every other requirement gets its own line."
          },
          {
            "where": "Subsections (Documentation, Task checklist, Requirement verification)",
            "quote": "- [ ] Complete `040-cli.md`, including the real CLI → client → service integration check.",
            "why": "The back half of the section is short labeled lists — five documentation bullets, seven checkboxes, one-requirement verification lines — and these scan with no effort; the strain is concentrated in the opening prose, not the whole section."
          }
        ]
      },
      "tasks/20260926-notes-query/010-contract.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "C5 item",
            "quote": "C5. The contract maps the HTTP options to the client method and CLI surface and is human-approved before dependent implementation begins.",
            "why": "Five one-sentence items each covering one contract dimension (pagination, sorting, filtering, shape, mapping/approval); the trailing Parent/Depends lines are two short self-labeling lines that do not interfere."
          }
        ]
      },
      "tasks/20260926-notes-query/010-contract.md — Scope": {
        "grade": "readable",
        "findings": [
          {
            "where": "Whole paragraph",
            "quote": "It may draft a target contract, but the document must not be presented as current supported behavior until the dependent implementation is shipped.",
            "why": "A 42-word paragraph holding three sentences, each one ownership rule; no re-reading needed."
          }
        ]
      },
      "tasks/20260926-notes-query/010-contract.md — Supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "Fact bullets",
            "quote": "The current service route returns a JSON array for `GET /notes/` without parameters.",
            "why": "Four one-fact bullets restating current service, client, and CLI behavior; each is a single sentence and takeable at a glance."
          }
        ]
      },
      "tasks/20260926-notes-query/010-contract.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "Implementation decisions and open questions — second paragraph",
            "quote": "The compatibility recommendation in the parent—array responses, explicit pagination, bounded `limit`/`offset`, case-insensitive title/description substring matching, and an `id` tie-breaker—can be used as a review starting point but requires approval before it becomes binding.",
            "why": "The single strained sentence in the section: a five-item list is embedded as an em-dash aside and the load-bearing approval caveat trails at the end; the rest of the section is 50-word single-topic paragraphs plus three small lists."
          }
        ]
      },
      "tasks/20260926-notes-query/020-api.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "A4 item",
            "quote": "A4. Service tests exercise the behavior through FastAPI and the SQLite-backed CRUD path, including boundary, tie, filter, empty-result, and invalid-input cases required by the contract.",
            "why": "Five one-requirement items; A4 enumerates its test cases inline but stays one concern, so the list holds without effort."
          }
        ]
      },
      "tasks/20260926-notes-query/020-api.md — Scope": {
        "grade": "readable",
        "findings": [
          {
            "where": "Whole paragraph",
            "quote": "It does not change client serialization or CLI parsing.",
            "why": "A 34-word paragraph of three clean ownership sentences — route and validation in, client/CLI out; nothing to unpack."
          }
        ]
      },
      "tasks/20260926-notes-query/020-api.md — Supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "Schema fact bullet",
            "quote": "The notes table has `id`, `title`, and `description`; no pagination metadata or query-specific persistence is currently present.",
            "why": "Four bullets, one current-state fact each with code-span anchors; the baseline is assembled in one pass."
          }
        ]
      },
      "tasks/20260926-notes-query/020-api.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "First prose paragraph",
            "quote": "Keep parameter validation at the public HTTP boundary and make the SQL query apply filtering, ordering, and pagination in a deterministic order.",
            "why": "Three paragraphs of ~55–60 words each stay single-topic (query construction, compatibility preservation, test strategy), and the four subsections carry the remaining content as short lists; no re-reading required."
          }
        ]
      },
      "tasks/20260926-notes-query/030-python-client.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "P2 item",
            "quote": "`list_notes()` with no arguments continues to request `/notes/` without query parameters and returns the current list-compatible result.",
            "why": "Four labeled requirements, one concern per item; the compatibility guarantee is stated in its own item rather than buried."
          }
        ]
      },
      "tasks/20260926-notes-query/030-python-client.md — Scope": {
        "grade": "readable",
        "findings": [
          {
            "where": "Whole paragraph",
            "quote": "It must consume the frozen contract rather than expose package-specific names that diverge from the public HTTP interface without a documented reason.",
            "why": "A 44-word paragraph of three sentences, each a single ownership rule; reads in one pass."
          }
        ]
      },
      "tasks/20260926-notes-query/030-python-client.md — Supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "Test-gap bullet",
            "quote": "The existing client test uses a minimal recording-compatible transport but does not assert the requested path or query parameters.",
            "why": "Three bullets, one fact each; the coverage gap that motivates P1/P3 is isolated in its own line."
          }
        ]
      },
      "tasks/20260926-notes-query/030-python-client.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "Test paragraph",
            "quote": "Keep one focused client test per mapping concern; the full service connection is verified by the CLI integration task.",
            "why": "Paragraphs are single-purpose (options, serialization tests) and the open-questions subsection cleanly separates blocked public decisions from locally resolvable choices; 342 words hold without strain."
          }
        ]
      },
      "tasks/20260926-notes-query/040-cli.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "L4 item",
            "quote": "L4. A decisive integration test invokes the CLI without a fake client, reaches an actual HTTP-served FastAPI application through the production client, and proves the approved pagination, sorting, and filtering result.",
            "why": "Five labeled requirements; L4 is the densest but still a single requirement, and the three Depends On bullets that follow are short and self-labeled."
          }
        ]
      },
      "tasks/20260926-notes-query/040-cli.md — Scope": {
        "grade": "readable",
        "findings": [
          {
            "where": "Whole paragraph",
            "quote": "This task owns CLI parsing, forwarding, rendering, and the end-to-end consumer-path evidence. It does not change HTTP semantics or duplicate client serialization.",
            "why": "Two ownership sentences; the smallest scope section in the set and fully takeable at a glance."
          }
        ]
      },
      "tasks/20260926-notes-query/040-cli.md — Supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "Environment-variable bullet",
            "quote": "The client’s environment-based constructor targets `NOTES_API_URL`, so a production-path test must configure that variable and avoid the injected fake-client seam.",
            "why": "Three bullets isolate current CLI state, the fake-client test gap, and the `NOTES_API_URL` constraint; each load-bearing fact gets its own line."
          }
        ]
      },
      "tasks/20260926-notes-query/040-cli.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "Numbered integration steps",
            "quote": "1. Starts the real FastAPI application behind an actual HTTP listener with isolated test data.",
            "why": "The decisive test is a five-step ordered list with one action per step — the clearest procedural block in the file set; the remaining paragraphs stay single-topic (~45–68 words) and the four subsections are lists, so 462 words hold without re-reading."
          }
        ]
      }
    },
    "navigation": {
      "grade": "navigable",
      "findings": [
        {
          "where": "All five files — first line of Execution plan",
          "quote": "Status: Draft",
          "why": "Plan status is a bare line inside Execution plan rather than a top-of-file metadata block, so it is not visible in a heading scan; the placement is identical in every file, so a reader learns the location once and can always find authorization status."
        },
        {
          "where": "Child files (010–040) — between Requirements checklist and Scope",
          "quote": "Depends On:",
          "why": "Dependency metadata carries no heading of its own and does not appear at section level; the inline labels and explicit file paths still make the dependency chain findable from the parent's Subtasks section."
        },
        {
          "where": "All five files — section skeleton",
          "quote": "## Requirements checklist … ## Scope … ## Supporting facts … ## Execution plan",
          "why": "Every file repeats the same heading order, and the parent's Subtasks and each child's Parent Task line cross-link the set; outcome (H1 titles), constraints (checklists), open questions (Unresolved requirement questions / Implementation decisions and open questions), and status are all reachable from headings alone."
        }
      ]
    },
    "mistakes": [
      {
        "where": "tasks/20260926-notes-query/000-main.md — Execution plan, Implementation decisions and open questions",
        "quote": "As a low-risk compatibility recommendation, evaluate keeping every response as an array, applying pagination only when explicitly requested, using a bounded `limit` plus an `offset`, searching title and description with a case-insensitive substring, and always adding `id` as the final sort tie-breaker.",
        "why": "Five discrete recommendations compressed into a single prose sentence; each is meant for independent review, but none can be scanned, challenged, or referenced on its own — a list would make each recommendation a reviewable unit."
      },
      {
        "where": "tasks/20260926-notes-query/000-main.md — Execution plan, opening paragraphs",
        "quote": "The contract is the compatibility boundary for all three consumers. … The client child will map only the approved options to query parameters. … The CLI child will add the approved command options…",
        "why": "Four consecutive ~80-word paragraphs (contract, service, client, CLI) each blend actions, constraints, and evidence with no per-child heading; the reader must hold the whole run to extract per-child ownership, which invites re-reading."
      },
      {
        "where": "tasks/20260926-notes-query/000-main.md — Execution plan, Implementation decisions and open questions",
        "quote": "- Pagination parameter model, bounds, defaults, and the no-parameter case (Q1).",
        "why": "Six bullets restate the open questions already detailed under \"Unresolved requirement questions\", so the same decision surface lives in two sections that can drift; a pointer to Q1–Q6 would avoid the duplicate."
      },
      {
        "where": "tasks/20260926-notes-query/000-main.md — Unresolved requirement questions",
        "quote": "Q1 — Pagination: should the wire contract use `offset`/`limit`, page-number/page-size, or another model? What are the minimum, default, and maximum bounds, and does an absent pagination argument retain the current unbounded array behavior?",
        "why": "Each question bullet bundles two to four distinct sub-questions (model, bounds, defaults, absent-argument behavior), so a reader must unpack compounds to know what counts as resolved; per-facet sub-bullets would make the decision surface explicit."
      },
      {
        "where": "tasks/20260926-notes-query/000-main.md — Execution plan, Requirement verification",
        "quote": "R5–R6: The CLI child’s named end-to-end test, invoked without a fake client, must traverse the CLI parser, production `NotesClient`, an actual HTTP service endpoint, and the returned query result.",
        "why": "Two requirement IDs merged into one dense bullet; an auditor verifying R5 alone cannot determine which clause discharges it, breaking the one-line-per-requirement pattern used everywhere else."
      },
      {
        "where": "tasks/20260926-notes-query/010-contract.md — Execution plan, Implementation decisions and open questions",
        "quote": "The compatibility recommendation in the parent—array responses, explicit pagination, bounded `limit`/`offset`, case-insensitive title/description substring matching, and an `id` tie-breaker—can be used as a review starting point but requires approval before it becomes binding.",
        "why": "A five-item list is embedded as an em-dash aside inside one sentence, and the load-bearing caveat (\"requires approval before it becomes binding\") trails at the end where it is easy to miss on a fast read."
      },
      {
        "where": "tasks/20260926-notes-query/000-main.md — Supporting facts, CLI bullet",
        "quote": "`apps/notes_cli/cli.py` currently prints every result from `client.list_notes()` and already has a `client=None` test seam. Existing CLI tests use a fake client, so they do not prove the production client-to-service path.",
        "why": "One bullet mixes three facts — current behavior, the test seam, and the coverage gap — and the gap is the load-bearing fact that justifies R6, yet it sits second inside a compound item rather than in its own line as the other facts do."
      }
    ],
    "summary": "The five files share one strict section skeleton (requirements checklist → scope → supporting facts → execution plan), with H1 titles stating each outcome, short labeled checklists, parent Subtasks and child Parent/Depends lines cross-linking the set; outcome, constraints, dependencies, open questions, and Draft status are all reachable from headings alone, so navigation is navigable. Most sections are short one-topic lists or 30–60-word paragraphs and grade readable — 040's five-step numbered integration procedure is the best-chunked content in the set. The one real strain point is the parent's Execution plan: 787 words whose opening ~500 are consecutive prose covering four children without per-child headings (longest paragraph 86 words), a five-part compatibility recommendation compressed into a single sentence, and a bullet restatement of Q1–Q6 that duplicates the Unresolved requirement questions section. Smaller echoes of the same compression habit — compound question bullets, an em-dash-embedded recommendation in 010, a merged R5–R6 verification bullet — cost scanning effort but not comprehension."
  }
}
