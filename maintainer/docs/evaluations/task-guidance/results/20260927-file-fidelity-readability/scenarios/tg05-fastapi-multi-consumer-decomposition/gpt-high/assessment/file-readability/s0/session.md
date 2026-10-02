# Session — tg05-fastapi-multi-consumer-decomposition · file-readability-assessment-gpt-high-s0 · glm max

- Run: `20260928T203515.764044Z-task-guidance-file-readability-tg05-fastapi-multi-consumer-decomposition-gpt-high-s0-def93cc5`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `7928f998efd10f02…`)
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

#### tasks/20260926-notes-query/000-main.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-notes-query/000-main.md — Requirements checklist | 177 | 0 | 0 | 7 | 10 | 0 | 0 | 0 | 5 |
| tasks/20260926-notes-query/000-main.md — Open requirement questions | 214 | 2 | 22 | 5 | 12 | 0 | 0 | 0 | 7 |
| tasks/20260926-notes-query/000-main.md — Scope and exclusions | 64 | 1 | 64 | 0 | 0 | 0 | 0 | 0 | 2 |
| tasks/20260926-notes-query/000-main.md — Supporting facts | 115 | 0 | 0 | 6 | 13 | 0 | 0 | 0 | 10 |
| tasks/20260926-notes-query/000-main.md — Execution plan | 707 | 3 | 75 | 26 | 14 | 5 | 0 | 0 | 14 |

#### tasks/20260926-notes-query/010-api-contract-and-service.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-notes-query/010-api-contract-and-service.md — Requirements checklist | 133 | 0 | 0 | 8 | 11 | 0 | 0 | 0 | 2 |
| tasks/20260926-notes-query/010-api-contract-and-service.md — Open requirement questions | 33 | 0 | 0 | 2 | 13 | 0 | 0 | 0 | 0 |
| tasks/20260926-notes-query/010-api-contract-and-service.md — Supporting facts | 66 | 0 | 0 | 3 | 14 | 0 | 0 | 0 | 6 |
| tasks/20260926-notes-query/010-api-contract-and-service.md — Execution plan | 422 | 2 | 68 | 18 | 14 | 5 | 0 | 0 | 3 |

#### tasks/20260926-notes-query/020-python-client.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-notes-query/020-python-client.md — Requirements checklist | 81 | 0 | 0 | 5 | 11 | 0 | 0 | 0 | 2 |
| tasks/20260926-notes-query/020-python-client.md — Open requirement questions | 40 | 0 | 0 | 2 | 12 | 0 | 0 | 0 | 1 |
| tasks/20260926-notes-query/020-python-client.md — Supporting facts | 66 | 0 | 0 | 4 | 13 | 0 | 0 | 0 | 3 |
| tasks/20260926-notes-query/020-python-client.md — Execution plan | 352 | 2 | 50 | 16 | 15 | 5 | 0 | 0 | 6 |

#### tasks/20260926-notes-query/030-cli-production-path.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-notes-query/030-cli-production-path.md — Requirements checklist | 105 | 0 | 0 | 6 | 11 | 0 | 0 | 0 | 4 |
| tasks/20260926-notes-query/030-cli-production-path.md — Open requirement questions | 44 | 0 | 0 | 2 | 15 | 0 | 0 | 0 | 1 |
| tasks/20260926-notes-query/030-cli-production-path.md — Supporting facts | 65 | 0 | 0 | 4 | 14 | 0 | 0 | 0 | 5 |
| tasks/20260926-notes-query/030-cli-production-path.md — Execution plan | 420 | 2 | 73 | 17 | 14 | 5 | 0 | 0 | 10 |

The produced task files:

### tasks/20260926-notes-query/000-main.md

````markdown
# Notes query capability across API, client, and CLI

Plan and coordinate one supported notes-query capability across the public
FastAPI service, reusable Python client, and notes CLI, without implementing
the capability in this planning task.

## Requirements checklist

- [ ] The public notes API supports bounded pagination, stable sorting, and
      optional text filtering through one documented query contract.
- [ ] The existing unparameterized `GET /notes/` behavior remains compatible:
      it continues to return the current collection representation, and its
      default ordering is explicitly defined and stable.
- [ ] The reusable `notes-client` package exposes the same query capability
      while preserving the current no-argument `NotesClient.list_notes()`
      behavior and return contract.
- [ ] The `notes list` CLI exposes the supported query capability while
      preserving the current no-option command behavior.
- [ ] The public API contract is settled and documented, with API-level
      regression evidence, before client or CLI consumers are implemented
      against it.
- [ ] The CLI is verified through its production client-to-service path:
      the CLI entry point uses the real `NotesClient`, which makes a real
      request to the running notes service; a fake/injected client is not the
      decisive integration evidence.
- [ ] Maintained documentation for the service, client, and CLI describes the
      resulting supported behavior in the same reviewed change as its
      implementation.

## Open requirement questions

These choices change the public contract and must be answered before the
execution plan is approved:

1. What are the pagination parameter names and semantics? A concrete
   recommendation is `limit` plus `offset`, with a positive bounded `limit`,
   `offset >= 0`, and a documented maximum; the required default limit and
   maximum still need approval.
2. Which sort fields and direction syntax are public? A concrete
   recommendation is an allowlisted note field (at least `id` and `title`),
   ascending/descending direction, and `id` as the deterministic secondary
   key for every sort. The exact parameter names and allowlist need approval.
3. What text does the filter search—title only, description only, or both—and
   what matching rules (case sensitivity and substring/token behavior) are
   required?
4. Should parameterized responses remain JSON arrays, preserving the current
   client return type, or should pagination metadata be added in an envelope?
   Keeping arrays for all modes is the compatibility-preserving
   recommendation, but it does not expose a total count or continuation
   marker.
5. What CLI option names and invalid-input behavior should be public? The
   corresponding recommendation is long options mirroring the approved API
   names, with argparse validation and a nonzero command failure for invalid
   values.

Until these are answered, the requirements above intentionally do not assert
specific parameter names, limits, sort fields, matching rules, or response
metadata.

## Scope and exclusions

In scope are the existing notes collection route, the existing
`NotesClient.list_notes()` surface, the existing `notes list` command, their
focused tests, and the maintained documentation that describes them. This
plan does not add a new notes resource, cursor protocol, authentication
scheme, bulk operation, or unrelated package restructuring. It also does not
authorize implementation until the draft contract questions are resolved and
the plan is approved.

## Supporting facts

- The service currently exposes `GET /notes/` at `src/app/api/notes.py` and
  returns `crud.get_all()` as a bare JSON collection.
- `src/app/api/crud.py` currently performs an unbounded database select with no
  explicit ordering or filtering.
- `packages/notes_client/notes_client/client.py` currently sends
  `GET /notes/` with no parameters and returns the decoded JSON unchanged.
- `apps/notes_cli/cli.py` currently accepts only `notes list`, calls
  `NotesClient.from_environment()` when no client is injected, and prints each
  note's id and title.
- Existing tests separately cover the route shape, client list return type, and
  CLI rendering. They do not cross the service, reusable client, and CLI
  production path.
- `docs/development/index.md` records that no notes-query specification exists.
  The repository has package-local READMEs but no existing public query
  contract to preserve.

## Execution plan

Status: Draft

The service owns query semantics and the compatibility contract. The client
owns the Python representation of that contract and must pass only approved
query values to the service. The CLI owns command-line mapping and user-facing
validation, while delegating retrieval to the production client. The
dependency order is therefore API contract and route evidence, then client
support, then CLI support and a real HTTP end-to-end check.

The contract gate should settle the unresolved questions above, document the
approved wire behavior in the service-owned documentation, and add route-level
tests before client or CLI implementation begins. The route should make
ordering explicit even for an unparameterized request so pagination windows do
not drift between calls; the chosen primary sort must always have a
deterministic tie-breaker. Client and CLI documentation should then mirror the
same approved names and defaults rather than defining parallel behavior.

Ordered execution:

1. Resolve the public contract questions and record the approved parameter,
   validation, response, ordering, filtering, and CLI mapping decisions in the
   API subtask.
2. Implement and test the service query path, including unparameterized
   compatibility, bounded pagination validation, stable ordering, filtering,
   and documented error responses. Complete the API task's decisive
   `TestClient`/route checks before proceeding.
3. Implement the reusable client's query arguments and request encoding,
   retaining the no-argument list behavior. Verify both request construction
   and a client-to-service integration case against the approved route.
4. Implement CLI options by forwarding approved values through
   `NotesClient.list_notes()`, retain `notes list` behavior, and add user-facing
   validation/output coverage.
5. Run the CLI through the installed/production entry point against a running
   notes service, with no injected fake client, and verify that a query option
   changes the service-backed result. Update all affected maintained READMEs
   and run the focused checks plus the repository's relevant test commands.

### Implementation decisions and open questions

- Decision: use one parent task with three subtasks because the HTTP API,
  independently packaged client, and CLI have distinct compatibility and
  acceptance boundaries.
- Decision: order dependencies as API -> client -> CLI; no consumer may
  implement against an unsettled wire contract.
- Decision: make the CLI/service integration check cross the real HTTP
  boundary and use the production client construction path.
- Open: pagination names, defaults, maximum, response metadata, sort syntax
  and allowlist, filter semantics, CLI names, and invalid-input behavior are
  listed in `## Open requirement questions` and require direction before
  approval.

### Documentation

- API subtask: document the approved query contract with the service-owned
  documentation and update the root API description; do not publish target
  behavior as current guidance before implementation is complete.
- Client subtask: update `packages/notes_client/README.md` with the supported
  method arguments, defaults, return shape, and compatibility behavior.
- CLI subtask: update `apps/notes_cli/README.md` with the supported options,
  examples, and failure behavior.
- Keep any new public claims in the same implementation change as the code
  and contract tests. Do not create unrelated placeholder documentation.

### Task checklist

- [ ] Resolve and approve the public query contract.
- [ ] Complete `tasks/20260926-notes-query/010-api-contract-and-service.md`.
- [ ] Complete `tasks/20260926-notes-query/020-python-client.md`.
- [ ] Complete `tasks/20260926-notes-query/030-cli-production-path.md`.
- [ ] Run the decisive checks named by each subtask and record their evidence.
- [ ] Update parent requirement status and append completion notes only after
      all approved outcomes are evidenced.

### Requirement verification

- API pagination, sorting, filtering, validation, and default compatibility:
  the route-level integration test in
  `tasks/20260926-notes-query/010-api-contract-and-service.md` must seed
  notes and exercise the public `GET /notes/` request against the real
  application/database boundary.
- Client capability and no-argument compatibility: the client subtask's
  decisive integration test must invoke `NotesClient.list_notes()` against
  the approved service route and assert both encoded query behavior and the
  unchanged no-argument list result.
- CLI capability and production path: the CLI subtask must run the actual
  `notes` entry point against a running service with the real
  `NotesClient.from_environment()` path and assert the filtered/sorted/page
  output; injected test doubles may cover formatting but cannot satisfy this
  requirement.
- Documentation and contract stability: inspect the final service, client, and
  CLI maintained documentation alongside the contract tests before marking
  the corresponding requirements complete.

### Additional implementation verification

- Verify that stable ordering is explicit in the generated SQL/query rather
  than relying on database insertion order.
- Verify limit bounds and invalid sort/filter inputs at the public boundary,
  including a result set large enough to cross a page boundary.
- Verify the CLI's no-option behavior still reaches the same client method and
  output shape as before.
````

### tasks/20260926-notes-query/010-api-contract-and-service.md

````markdown
# Define and implement the notes-query API contract

Own the public HTTP contract and service implementation for bounded
pagination, stable sorting, and optional text filtering. This subtask is the
compatibility gate for all downstream consumers.

Parent Task: tasks/20260926-notes-query/000-main.md

## Requirements checklist

- [ ] The approved query contract names pagination, sorting, and text-filter
      parameters, defaults, bounds, allowed values, and validation behavior.
- [ ] `GET /notes/` supports the approved query behavior at the public route.
- [ ] Unparameterized `GET /notes/` retains its current JSON collection shape
      and has an explicit stable default ordering.
- [ ] Pagination is bounded at the HTTP boundary and cannot request an
      unbounded or above-maximum page.
- [ ] Sorting is deterministic, including a documented tie-breaker.
- [ ] Optional text filtering follows the approved field scope and matching
      rules.
- [ ] Route-level integration tests cover the approved behavior and regressions
      through the real FastAPI application and database boundary.
- [ ] The service-owned public documentation records the approved contract
      before client and CLI consumers are implemented.

## Open requirement questions

- Confirm the parent task's unresolved pagination, sort, filter, response
  shape, and invalid-input questions before implementation.
- Confirm whether the API should expose pagination metadata or preserve a JSON
  array for parameterized calls.

## Supporting facts

- The route is `src/app/api/notes.py`; query work will likely span its route
  parameters and `src/app/api/crud.py`'s database query.
- The existing route test only asserts a 200 response and list shape for
  `GET /notes/`; it does not seed or isolate data.
- The current database schema has `id`, `title`, and `description`, which are
  the available fields for an initial sort/filter contract unless the
  approved requirements expand scope.

## Execution plan

Status: Draft

Define the wire contract first, including exact query names, defaults, maximum
page size, response shape, sorting allowlist/direction, text matching scope,
and errors. Document that contract in the service-owned documentation before
downstream implementation. Then add the smallest service query abstraction
that applies filtering, explicit primary ordering plus deterministic `id`
tie-breaking, and bounded slicing in the database query. Preserve the
unparameterized route's collection representation and make its default
ordering explicit.

Use route integration tests with seeded records that include equal primary
sort values, mixed matching/nonmatching text, and enough records to cross
page boundaries. Cover default behavior, each approved query dimension,
combined dimensions, invalid bounds/values, and compatibility. These tests
are the decisive evidence that the public service boundary is ready for
consumers.

### Implementation decisions and open questions

- The API task owns all wire-level decisions; client and CLI tasks must not
  infer or redefine them.
- Stable sort behavior must be expressed in the production query and tested
  with ties.
- No response envelope or metadata is to be introduced unless the approved
  contract explicitly requires it, because the current client expects a list.
- The exact public choices remain open in the parent task until approved.

### Documentation

- Update the service-facing maintained documentation, likely the root
  `README.md` or a focused service-owned page only if the approved contract
  needs more detail.
- If a focused specification is created, update the existing development
  documentation index rather than leaving an undiscoverable page.
- Mark target behavior as current only after the implementation and route
  evidence are complete.

### Task checklist

- [ ] Resolve and record the HTTP query contract.
- [ ] Add/update route and query implementation.
- [ ] Add route integration coverage for all approved dimensions and
      unparameterized compatibility.
- [ ] Publish/update service documentation with verified behavior.
- [ ] Run the decisive service test command and record the result.
- [ ] Hand the settled contract to the client subtask.

### Requirement verification

- Contract and route behavior: a focused integration suite must issue real
  HTTP requests to the FastAPI app, seed through the supported API or
  controlled test fixture, and assert page bounds, deterministic ordering,
  filter results, response shape, and validation responses.
- Compatibility: the existing no-parameter route request must still return a
  JSON list with the approved stable default ordering.
- Contract readiness: the API tests and maintained documentation must be
  complete before `020-python-client.md` begins implementation.

### Additional implementation verification

- Inspect generated SQL/query composition to ensure filtering and ordering
  happen before pagination.
- Check behavior at zero, one, maximum, and maximum-plus-one page sizes, plus
  negative offsets or equivalent invalid pagination inputs as applicable.
````

### tasks/20260926-notes-query/020-python-client.md

````markdown
# Expose the notes-query contract through the reusable Python client

Add the approved notes-query capability to the independently maintained
`notes-client` package while preserving its current no-argument behavior.

Parent Task: tasks/20260926-notes-query/000-main.md
Depends On: tasks/20260926-notes-query/010-api-contract-and-service.md

## Requirements checklist

- [ ] `NotesClient.list_notes()` exposes the approved pagination, sorting, and
      optional text-filter inputs.
- [ ] The client encodes only approved values and parameter names for the
      service contract.
- [ ] A no-argument `list_notes()` call continues to request the unparameterized
      collection and return the current decoded list behavior.
- [ ] Client documentation describes the supported arguments, defaults,
      response/return shape, and compatibility behavior.
- [ ] Tests cover request encoding, no-argument compatibility, and the client
      against the settled service contract.

## Open requirement questions

- Use the exact API parameter names, defaults, validation, and response shape
  approved by `010-api-contract-and-service.md`; do not resolve a second
  client-specific contract.
- Confirm whether invalid client arguments fail locally, are sent for server
  validation, or follow another approved policy.

## Supporting facts

- The client implementation is `packages/notes_client/notes_client/client.py`.
- It currently calls `self.transport.get("/notes/").json()` and returns the
  decoded value directly.
- Its current test transport records no requests and only proves that the
  result is a list, so it cannot establish query encoding or service
  compatibility by itself.
- The package has its own README and `pyproject.toml`, making its method
  signature and return behavior an independently maintained package boundary.

## Execution plan

Status: Draft

After the API task settles the wire contract, extend `list_notes()` with the
approved optional arguments and construct a query parameter mapping that
omits unset values. Preserve the existing no-argument request and decoded
return path. Apply the approved client-side validation policy without
duplicating server semantics that belong to the HTTP contract.

Retain a focused transport-level test for exact request encoding, then add a
client-to-service integration test that uses the production `NotesClient`
method against the real FastAPI route. The integration evidence must exercise
at least one combined pagination/sort/filter request and the no-argument
compatibility path.

### Implementation decisions and open questions

- The API subtask is the source of truth for query names and response shape.
- Optional values should not appear in the request when omitted, preserving
  the current unparameterized request exactly.
- Whether local argument validation is required remains subordinate to the
  approved contract and error policy.

### Documentation

- Update `packages/notes_client/README.md` with the final method signature or
  invocation examples, query semantics, defaults, return shape, and no-arg
  compatibility.
- Keep package documentation aligned with the service contract; do not
  introduce client-only aliases without an approved compatibility reason.

### Task checklist

- [ ] Consume the settled API contract.
- [ ] Extend `NotesClient.list_notes()` and query encoding.
- [ ] Update transport-level and service integration tests.
- [ ] Update the package README.
- [ ] Run the package tests and decisive client-to-service check.
- [ ] Hand the client invocation contract to the CLI subtask.

### Requirement verification

- Query encoding: a transport-level test must assert the exact path and
  parameter mapping for every approved option and omission of unset values.
- Client compatibility: a no-argument call must still issue the existing
  unparameterized request and return a list.
- Public connection: an integration test must call the real `NotesClient`
  implementation against the implemented FastAPI route and assert the
  filtered, sorted, bounded result; a mocked response alone is not decisive.

### Additional implementation verification

- Confirm the client does not accidentally send `None`, client-only names, or
  an incompatible envelope assumption.
- If the API response shape is an array, preserve the existing direct JSON
  return; if the approved contract uses metadata, document and test the
  resulting intentional compatibility change explicitly.
````

### tasks/20260926-notes-query/030-cli-production-path.md

````markdown
# Expose notes queries in the CLI and prove the production path

Add the approved notes-query controls to `notes list`, preserve its existing
no-option behavior, and verify the actual CLI -> reusable client -> running
service path.

Parent Task: tasks/20260926-notes-query/000-main.md
Depends On: tasks/20260926-notes-query/010-api-contract-and-service.md,
tasks/20260926-notes-query/020-python-client.md

## Requirements checklist

- [ ] `notes list` exposes CLI options corresponding to the approved query
      capability.
- [ ] The no-option `notes list` command retains its current output purpose
      and uses the reusable client's unparameterized behavior.
- [ ] CLI values are forwarded through `NotesClient.list_notes()` rather than
      reimplementing service querying.
- [ ] Invalid CLI values produce the approved user-facing nonzero failure.
- [ ] CLI documentation contains the supported options and examples.
- [ ] A decisive integration check runs the production CLI entry point with
      `NotesClient.from_environment()` against a running notes service, with no
      injected fake client, and proves that query options affect the
      service-backed output.

## Open requirement questions

- Confirm the final CLI option names, defaults, help text, and invalid-input
  behavior after the API contract is approved.
- Confirm whether CLI output remains one `id: title` line per note when the API
  response includes pagination metadata; this follows the approved response
  shape.

## Supporting facts

- The CLI implementation is `apps/notes_cli/cli.py`.
- It currently has only a required `list` subcommand and calls
  `list_command(selected)` after choosing an injected client or
  `NotesClient.from_environment()`.
- Existing CLI tests inject a fake client and assert only that output is
  nonempty; they do not prove the production client or service path.
- The CLI package has a separate README and console-script entry point
  (`notes = "notes_cli.cli:main"`).

## Execution plan

Status: Draft

After the API and client contracts are settled, add CLI arguments that map
one-to-one to the approved query inputs. Keep `list_command` focused on
formatting and have `main` pass parsed values to the production client
method. Preserve the existing no-option invocation and output format unless
the approved response shape requires an explicitly reviewed change.

Keep unit coverage for parsing and rendering with the injected fixture, but
make the decisive check stronger: start the real notes service on a local
address, invoke the actual `notes` console entry point with environment-based
configuration and query options, and assert output from records selected by
the service. Run a no-option invocation in the same path to prove the
compatibility behavior. The check must not pass by supplying the CLI's
optional `client` argument.

### Implementation decisions and open questions

- The CLI delegates all retrieval semantics to `NotesClient`; it must not
  duplicate filtering, sorting, or pagination.
- The end-to-end check must use the production environment/client selection
  path and a real HTTP request to the service.
- Exact option names, response-driven output handling, and invalid-input
  policy remain open until the API contract and client method are approved.

### Documentation

- Update `apps/notes_cli/README.md` with the final command syntax, options,
  examples, defaults, output behavior, and invalid-input behavior.
- Keep the existing basic `notes list` example to document compatibility.

### Task checklist

- [ ] Consume the settled API and client contracts.
- [ ] Add CLI parsing and forwarding for approved query options.
- [ ] Extend unit coverage for parsing, formatting, and no-option behavior.
- [ ] Add/run the real entry-point-to-running-service integration check.
- [ ] Update the CLI README.
- [ ] Record the exact command and service setup used as decisive evidence.

### Requirement verification

- CLI mapping: unit coverage must assert parsed values reach the client method
  and that no-option invocation retains existing output behavior.
- Production path: invoke the actual `notes` console script or equivalent
  installed entry point with `NOTES_API_URL` targeting a running service;
  seed known records through the service boundary, request a combined query,
  and assert the selected stable order and page in stdout.
- Compatibility: the same real path must run `notes list` without query
  options and verify the existing line-oriented output.
- Invalid input: invoke the public command with each approved invalid class
  and assert the documented nonzero/error behavior.

### Additional implementation verification

- Ensure CLI options are not silently ignored when their values are falsey or
  zero-like but valid under the approved contract.
- Ensure the integration command uses the package/runtime configuration that a
  user would use, rather than a test-only client injection or direct route
  call.
````


**Assistant** *(reasoning present)*

```json
{
  "schema_version": 1,
  "scenario_id": "tg05-fastapi-multi-consumer-decomposition",
  "assessment": {
    "sections": {
      "tasks/20260926-notes-query/000-main.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "checklist item 6 (CLI production path)",
            "quote": "The CLI is verified through its production client-to-service path: the CLI entry point uses the real `NotesClient`, which makes a real request to the running notes service; a fake/injected client is not the decisive integration evidence.",
            "why": "The densest of the seven boxes: a single item carries the requirement, the mechanism, and an evidence exclusion, so the reader must unpack three clauses to tick it. The other six items stay at one commitment each, and the whole list scans in one pass."
          }
        ]
      },
      "tasks/20260926-notes-query/000-main.md — Open requirement questions": {
        "grade": "readable",
        "findings": [
          {
            "where": "numbered item 1",
            "quote": "A concrete recommendation is `limit` plus `offset`, with a positive bounded `limit`, `offset >= 0`, and a documented maximum; the required default limit and maximum still need approval.",
            "why": "Each item pairs the open decision with its provisional recommendation and the residual open part, so question, proposal, and remaining gap are all in one place with no cross-referencing. Items run long but stay single-topic."
          }
        ]
      },
      "tasks/20260926-notes-query/000-main.md — Scope and exclusions": {
        "grade": "readable",
        "findings": [
          {
            "where": "the single 64-word paragraph",
            "quote": "This plan does not add a new notes resource, cursor protocol, authentication scheme, bulk operation, or unrelated package restructuring.",
            "why": "Three sentences carry in-scope, exclusions, and the implementation gate; at 64 words the paragraph holds in one read, though all three moves are compressed into one block instead of being separated."
          }
        ]
      },
      "tasks/20260926-notes-query/000-main.md — Supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "bullet 2",
            "quote": "`src/app/api/crud.py` currently performs an unbounded database select with no explicit ordering or filtering.",
            "why": "Every bullet anchors exactly one file path to exactly one current-behavior fact, which makes this the fastest section in the file set to scan and cite."
          }
        ]
      },
      "tasks/20260926-notes-query/000-main.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "opening paragraph 1",
            "quote": "The service owns query semantics and the compatibility contract. The client owns the Python representation of that contract and must pass only approved query values to the service.",
            "why": "Three ownership claims plus the dependency order live in 75 words of prose rather than a list; one-idea-per-sentence keeps it parseable, but the ownership map cannot be skimmed as items."
          },
          {
            "where": "Ordered execution, step 5",
            "quote": "Update all affected maintained READMEs and run the focused checks plus the repository's relevant test commands.",
            "why": "One numbered step bundles the end-to-end CLI run, documentation updates, and test commands, so progress on this step cannot be tracked partially."
          },
          {
            "where": "subsection structure",
            "quote": "### Requirement verification",
            "why": "Five named subsections of 3-6 short items decompose the 707-word section; no subsection exceeds a screen of reading, which is what keeps the largest section workable."
          }
        ]
      },
      "tasks/20260926-notes-query/010-api-contract-and-service.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "checklist item 5",
            "quote": "Sorting is deterministic, including a documented tie-breaker.",
            "why": "Eight boxes of one short assertion each; this is the easiest section in the file set to scan and check off."
          }
        ]
      },
      "tasks/20260926-notes-query/010-api-contract-and-service.md — Open requirement questions": {
        "grade": "readable",
        "findings": [
          {
            "where": "bullet 2",
            "quote": "Confirm whether the API should expose pagination metadata or preserve a JSON array for parameterized calls.",
            "why": "Two items of one sentence each; the reader sees the entire open-decision surface for this subtask at a glance."
          }
        ]
      },
      "tasks/20260926-notes-query/010-api-contract-and-service.md — Supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "bullet 3",
            "quote": "The current database schema has `id`, `title`, and `description`, which are the available fields for an initial sort/filter contract unless the approved requirements expand scope.",
            "why": "The load-bearing field allowlist rides at the tail of the sentence behind a hedge; it is findable on a full read but easy to drop on a facts-only scan."
          }
        ]
      },
      "tasks/20260926-notes-query/010-api-contract-and-service.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "first paragraph, sentence 1",
            "quote": "Define the wire contract first, including exact query names, defaults, maximum page size, response shape, sorting allowlist/direction, text matching scope, and errors.",
            "why": "Seven contract dimensions are packed into one subordinate clause of prose; the reader extracting the decision list must re-parse the sentence rather than scan items, though it is short enough to hold in one read."
          },
          {
            "where": "second paragraph",
            "quote": "seeded records that include equal primary sort values, mixed matching/nonmatching text, and enough records to cross page boundaries",
            "why": "The 68-word paragraph compresses the test-seed design and coverage matrix into flowing prose; it is the densest stretch of an otherwise list-led plan."
          }
        ]
      },
      "tasks/20260926-notes-query/020-python-client.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "checklist item 3",
            "quote": "A no-argument `list_notes()` call continues to request the unparameterized collection and return the current decoded list behavior.",
            "why": "Five boxes with one behavior commitment each; the compatibility requirement is stated once and unambiguously."
          }
        ]
      },
      "tasks/20260926-notes-query/020-python-client.md — Open requirement questions": {
        "grade": "readable",
        "findings": [
          {
            "where": "bullet 1",
            "quote": "Use the exact API parameter names, defaults, validation, and response shape approved by `010-api-contract-and-service.md`; do not resolve a second client-specific contract.",
            "why": "The item itself is clear and short, but it is a settled directive styled as an open question (see mistakes); a reader scanning this section for undecided points misclassifies it."
          }
        ]
      },
      "tasks/20260926-notes-query/020-python-client.md — Supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "bullet 3",
            "quote": "Its current test transport records no requests and only proves that the result is a list, so it cannot establish query encoding or service compatibility by itself.",
            "why": "Four short bullets, each stating one current-state fact including the evidence gap; the whole section holds in a single read."
          }
        ]
      },
      "tasks/20260926-notes-query/020-python-client.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "first paragraph, sentence 3",
            "quote": "Apply the approved client-side validation policy without duplicating server semantics that belong to the HTTP contract.",
            "why": "Both paragraphs stay near 50 words with one instruction per sentence and the five subsections hold 3-4 items each; the lightest execution plan of the four files."
          }
        ]
      },
      "tasks/20260926-notes-query/030-cli-production-path.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "checklist item 6",
            "quote": "A decisive integration check runs the production CLI entry point with `NotesClient.from_environment()` against a running notes service, with no injected fake client, and proves that query options affect the service-backed output.",
            "why": "The longest checklist item in the file set (~45 words) folds the check definition and its exclusion into one box; still a single topic, but it takes sustained attention to tick."
          }
        ]
      },
      "tasks/20260926-notes-query/030-cli-production-path.md — Open requirement questions": {
        "grade": "readable",
        "findings": [
          {
            "where": "bullet 2",
            "quote": "Confirm whether CLI output remains one `id: title` line per note when the API response includes pagination metadata; this follows the approved response shape.",
            "why": "Both items name the undecided choice and the upstream decision it waits on; one sentence each, no re-reading needed."
          }
        ]
      },
      "tasks/20260926-notes-query/030-cli-production-path.md — Supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "bullet 3",
            "quote": "Existing CLI tests inject a fake client and assert only that output is nonempty; they do not prove the production client or service path.",
            "why": "One gap statement per line with the file path or entry point inline; each fact can be lifted directly into the plan."
          }
        ]
      },
      "tasks/20260926-notes-query/030-cli-production-path.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "second paragraph, final sentence",
            "quote": "The check must not pass by supplying the CLI's optional `client` argument.",
            "why": "A load-bearing exclusion sits as the last sentence of a 73-word prose paragraph; it is restated in the checklist, but on a prose-only read it is the easiest decisive rule to miss."
          },
          {
            "where": "Requirement verification, Production path bullet",
            "quote": "invoke the actual `notes` console script or equivalent installed entry point with `NOTES_API_URL` targeting a running service; seed known records through the service boundary, request a combined query, and assert the selected stable order and page in stdout.",
            "why": "A four-stage procedure is chained with semicolons inside one bullet; the reader can follow it, but it is the densest instruction in the file."
          }
        ]
      }
    },
    "navigation": {
      "grade": "navigable",
      "findings": [
        {
          "where": "all four files",
          "quote": "## Requirements checklist / ## Open requirement questions / ## Supporting facts / ## Execution plan",
          "why": "Every file repeats the same four-part skeleton with the same five plan subsections, so the outcome (title plus checklist), constraints (checklist and scope), open decisions (own heading in every file), and plan status (Status: Draft) are reachable from headings alone."
        },
        {
          "where": "000-main.md — Task checklist and subtask headers",
          "quote": "Complete `tasks/20260926-notes-query/010-api-contract-and-service.md`.",
          "why": "The parent tracks subtask progress by exact file path and each subtask restates Parent/Depends On at the top, so the API -> client -> CLI chain is visible without reading any plan prose."
        }
      ]
    },
    "mistakes": [
      {
        "where": "tasks/20260926-notes-query/020-python-client.md — Open requirement questions, bullet 1 (pattern also in 010 and 030 'Confirm...' items)",
        "quote": "Use the exact API parameter names, defaults, validation, and response shape approved by `010-api-contract-and-service.md`; do not resolve a second client-specific contract.",
        "why": "Heading/content mismatch: this is a settled binding constraint, not an open question. A reader scanning for undecided points treats policy as open, and a reader hunting for constraints will not look under this heading."
      },
      {
        "where": "tasks/20260926-notes-query/000-main.md — Scope and exclusions, final sentence",
        "quote": "It also does not authorize implementation until the draft contract questions are resolved and the plan is approved.",
        "why": "Buried load-bearing fact: the no-implementation-before-approval gate is the last clause of a 64-word prose paragraph rather than a checklist line or the plan's status line, so a checklist-first scan can miss it entirely."
      },
      {
        "where": "tasks/20260926-notes-query/000-main.md — Execution plan, Ordered execution step 5",
        "quote": "Run the CLI through the installed/production entry point against a running notes service, with no injected fake client, and verify that a query option changes the service-backed result. Update all affected maintained READMEs and run the focused checks plus the repository's relevant test commands.",
        "why": "One numbered step mixes three distinct actions (end-to-end run, documentation updates, test commands); a reader cannot see or record partial progress within the step."
      },
      {
        "where": "tasks/20260926-notes-query/010-api-contract-and-service.md — Execution plan, first paragraph",
        "quote": "including exact query names, defaults, maximum page size, response shape, sorting allowlist/direction, text matching scope, and errors.",
        "why": "Prose-buried enumeration: the seven dimensions of the contract to be decided are packed into a subordinate clause, so extracting them as a checklist requires re-parsing prose; the same pattern recurs in 000-main's second plan paragraph and 030's integration procedure."
      },
      {
        "where": "010/020/030 — 'Implementation decisions and open questions' subsections",
        "quote": "- The exact public choices remain open in the parent task until approved.",
        "why": "Inconsistent classification within an identical heading: the parent file labels its items 'Decision:'/'Open:', while the subtasks mix decisions and open items as unlabeled bullets, forcing the reader to infer each item's status from phrasing."
      },
      {
        "where": "tasks/20260926-notes-query/000-main.md — Requirements checklist, item 6",
        "quote": "the CLI entry point uses the real `NotesClient`, which makes a real request to the running notes service; a fake/injected client is not the decisive integration evidence.",
        "why": "List item mixing several facts: requirement, mechanism, and evidence exclusion share one checkbox, making this the only box in the set that must be read twice to verify."
      }
    ],
    "summary": "The four files share one rigid skeleton — requirements checklist, open questions, supporting facts, then an execution plan subdivided into five named subsections — and nearly every claim is anchored to a concrete file path, so a maintainer can reach the outcome, the constraints, the open decisions, and the Draft status from headings alone; navigation is navigable. Every section is readable: the heaviest section (000-main's 707-word plan) is decomposed into short subsections, list items run 10-15 words per line, and no paragraph exceeds 75 words, so nothing forces re-reading. The residual friction is localization-level rather than structural: decisive evidence rules folded into single checklist items (000-main item 6, 030 item 6), contract dimensions and integration procedures enumerated inside prose sentences (010, 030, 000-main), the no-implementation gate hidden as the last clause of the scope paragraph, and settled directives presented under 'Open requirement questions' (most clearly in 020), plus a decision/open labeling style that the subtasks drop relative to the parent."
  }
}
```
