# Session — tg05-fastapi-multi-consumer-decomposition · file-readability-assessment-gpt-xhigh-s0 · glm max

- Run: `20260928T203802.690265Z-task-guidance-file-readability-tg05-fastapi-multi-consumer-decomposition-gpt-xhigh-s0-4de02b23`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `de18c51f3453f970…`)
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
| tasks/20260926-notes-query/000-main.md — Requirements checklist | 140 | 0 | 0 | 6 | 11 | 0 | 0 | 0 | 3 |
| tasks/20260926-notes-query/000-main.md — Scope and workstreams | 58 | 2 | 24 | 3 | 9 | 0 | 0 | 0 | 0 |
| tasks/20260926-notes-query/000-main.md — Requirement questions and scope decisions | 197 | 2 | 19 | 6 | 12 | 0 | 0 | 0 | 6 |
| tasks/20260926-notes-query/000-main.md — Research and supporting facts | 90 | 0 | 0 | 5 | 8 | 0 | 0 | 0 | 14 |
| tasks/20260926-notes-query/000-main.md — Subtasks | 12 | 0 | 0 | 3 | 1 | 0 | 0 | 0 | 3 |
| tasks/20260926-notes-query/000-main.md — Execution plan | 634 | 3 | 68 | 25 | 13 | 5 | 0 | 0 | 15 |

#### tasks/20260926-notes-query/010-public-api-contract-and-service.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-notes-query/010-public-api-contract-and-service.md — Requirements checklist | 85 | 0 | 0 | 6 | 10 | 0 | 0 | 0 | 1 |
| tasks/20260926-notes-query/010-public-api-contract-and-service.md — Requirement questions and scope decisions | 43 | 0 | 0 | 3 | 11 | 0 | 0 | 0 | 0 |
| tasks/20260926-notes-query/010-public-api-contract-and-service.md — Research and supporting facts | 57 | 0 | 0 | 4 | 14 | 0 | 0 | 0 | 6 |
| tasks/20260926-notes-query/010-public-api-contract-and-service.md — Execution plan | 417 | 3 | 59 | 21 | 13 | 5 | 0 | 0 | 6 |

#### tasks/20260926-notes-query/020-reusable-client.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-notes-query/020-reusable-client.md — Requirements checklist | 77 | 0 | 0 | 5 | 11 | 0 | 0 | 0 | 0 |
| tasks/20260926-notes-query/020-reusable-client.md — Requirement questions and scope decisions | 59 | 0 | 0 | 3 | 13 | 0 | 0 | 0 | 0 |
| tasks/20260926-notes-query/020-reusable-client.md — Research and supporting facts | 38 | 0 | 0 | 3 | 12 | 0 | 0 | 0 | 3 |
| tasks/20260926-notes-query/020-reusable-client.md — Execution plan | 335 | 2 | 54 | 15 | 14 | 5 | 0 | 0 | 5 |

#### tasks/20260926-notes-query/030-cli-and-production-path.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-notes-query/030-cli-and-production-path.md — Requirements checklist | 79 | 0 | 0 | 5 | 11 | 0 | 0 | 0 | 2 |
| tasks/20260926-notes-query/030-cli-and-production-path.md — Requirement questions and scope decisions | 77 | 0 | 0 | 4 | 14 | 0 | 0 | 0 | 1 |
| tasks/20260926-notes-query/030-cli-and-production-path.md — Research and supporting facts | 61 | 0 | 0 | 4 | 12 | 0 | 0 | 0 | 8 |
| tasks/20260926-notes-query/030-cli-and-production-path.md — Execution plan | 393 | 3 | 82 | 15 | 13 | 5 | 0 | 0 | 8 |

The produced task files:

### tasks/20260926-notes-query/000-main.md

````markdown
# Notes-query capability across API, client, and CLI

Plan and coordinate one supported notes-query capability across the FastAPI
service, reusable Python client, and CLI without changing existing
unparameterized behavior.

## Requirements checklist

- [ ] Define and review one stable public query contract covering bounded
  pagination, deterministic sorting, optional text filtering, valid ranges,
  defaults, and invalid-input behavior.
- [ ] Extend the public notes collection API with that contract while keeping
  an unparameterized `GET /notes/` compatible with its current bare-list,
  all-notes behavior.
- [ ] Extend `NotesClient.list_notes()` with the same capability while keeping
  a no-argument call compatible with its current list return value and request.
- [ ] Extend `notes list` with the same capability while keeping the existing
  no-option command behavior and output compatible.
- [ ] Do not begin consumer implementation against an unstable contract; the
  API contract must be reviewed and documented before the client and CLI
  depend on it.
- [ ] Prove the complete CLI-to-production-client-to-service path for a
  parameterized query without injecting the CLI's test fake client.

## Scope and workstreams

The parent task coordinates three independently acceptable boundaries:

1. The HTTP contract and service/storage query implementation.
2. The reusable Python client interface and request mapping.
3. The CLI interface and the live client-to-service proof.

Documentation and focused verification stay with the workstream that owns the
public behavior. No application, package, or documentation implementation is
authorized by this draft.

## Requirement questions and scope decisions

These are material public-contract questions and must be answered or explicitly
accepted before the plan becomes `Approved`:

- Should query parameters be added to the existing `GET /notes/` route
  (recommended for path compatibility), or should a separate route be
  introduced?
- Should parameterized responses remain bare JSON arrays (recommended because
  both the existing client and CLI consume lists), or should pagination add
  metadata and therefore introduce a new response shape?
- What are the canonical names and semantics for pagination, sorting, and
  filtering? A concrete recommendation to review is `limit` plus `offset`,
  an allow-listed sort field plus direction, and a text query applied as a
  case-insensitive substring over title and description.
- What maximum page size, default values, allowed sort fields/directions, and
  invalid-input responses are part of the contract?
- What deterministic tie-breaker is required for equal sort values? The
  current schema has no timestamp, so `id` is the available stable secondary
  key and is the recommended tie-breaker.
- Should CLI flags mirror the HTTP/client names exactly, and should
  parameterized output remain one `id: title` line per note?

The recommendations above are planning proposals, not completed requirements.
No consumer-specific interpretation should be added until they are settled.

## Research and supporting facts

- `src/app/api/notes.py` exposes `GET /notes/` and currently returns
  `crud.get_all()` directly.
- `src/app/api/crud.py` currently selects every row without filtering,
  ordering, or bounds. The table contains only `id`, `title`, and
  `description`.
- `packages/notes_client/notes_client/client.py` currently calls
  `transport.get("/notes/").json()` with no parameters, and its test asserts a
  list result.
- `apps/notes_cli/cli.py` currently iterates `list_notes()` and prints
  `id: title`. Its existing test supplies an injected fake client; it does not
  exercise `NotesClient.from_environment()` or an HTTP service.
- `docs/development/index.md` records that no notes-query specification
  exists. The root README and both package READMEs describe the current
  unparameterized behavior.

## Subtasks

- [ ] `tasks/20260926-notes-query/010-public-api-contract-and-service.md`
- [ ] `tasks/20260926-notes-query/020-reusable-client.md`
- [ ] `tasks/20260926-notes-query/030-cli-and-production-path.md`

## Execution plan

Status: Draft

The API workstream owns the canonical contract. It must settle the route,
parameter, response, validation, ordering, and filter semantics, publish the
reviewable contract, and verify the service behavior before the client task
starts. The client then maps that contract without changing the result shape.
The CLI follows the same contract and must exercise a real
`NotesClient.from_environment()` against a running service, rather than
proving only an injected fake-client seam.

Compatibility is handled at the no-argument boundary: no query options mean
the existing API list response, client list return, and CLI output remain in
force. Parameterized calls add bounded selection, deterministic order, and
filtering under the one agreed contract. The exact parameter names and
semantics remain open until the contract questions above are resolved.

Ordered execution:

1. Resolve the public-contract questions and record the accepted contract in
   the API workstream. Keep the plan in `Draft` until that review is complete.
2. Execute the API workstream, including service/storage behavior, API
   compatibility coverage, and maintained contract documentation.
3. After the API contract and its decisive integration evidence are accepted,
   execute the reusable-client workstream and verify exact request mapping and
   no-argument compatibility.
4. Execute the CLI workstream against the agreed client interface, preserve
   existing output for an unparameterized command, and run the live
   client-to-service check.
5. Update all affected maintained READMEs and development documentation,
   execute the focused tests plus the cross-boundary check, and record any
   deferred scope without silently changing the contract.

### Implementation decisions and open questions

- Contract ownership is assigned to the public API workstream.
- The existing `/notes/` collection path is the recommended compatibility
  boundary; the route choice and response shape still require approval.
- `id` is the recommended deterministic secondary ordering key because the
  current data model has no creation timestamp.
- The client and CLI are explicitly dependent on the reviewed API contract.
- The exact query vocabulary, bounds, filter semantics, and CLI mapping remain
  unresolved as listed above.

### Documentation

- The service workstream should add or update the maintained notes-query
  contract under `docs/development/` and link it from the development index,
  plus update the root service README where public API behavior is described.
- The client workstream should update `packages/notes_client/README.md` with
  the supported method arguments and no-argument compatibility.
- The CLI workstream should update `apps/notes_cli/README.md` with its flags,
  output behavior, and an example of the supported query.
- No current-behavior documentation is changed during this planning-only
  step; target-only material must remain visibly non-current until implemented.

### Task checklist

- [ ] Resolve the contract questions and obtain approval to execute.
- [ ] Complete `010-public-api-contract-and-service.md`.
- [ ] Complete `020-reusable-client.md` after the API contract gate.
- [ ] Complete `030-cli-and-production-path.md` after the client contract gate.
- [ ] Run the named API, client, and CLI evidence and update requirement
  status from that evidence.
- [ ] Record completion notes only after all approved requirements are met.

### Requirement verification

- Canonical contract, bounded service query, stable ordering, text filtering,
  and unparameterized API compatibility: owned by
  `010-public-api-contract-and-service.md`; decisive evidence is an API
  integration test through `TestClient` and the real database adapter with
  records spanning page boundaries, sort ties, filter matches, and invalid
  bounds.
- Reusable-client capability and no-argument compatibility: owned by
  `020-reusable-client.md`; evidence must verify the public method's exact
  request mapping and list return, with at least one check against the
  agreed service contract rather than only a response-shaped mock.
- CLI capability and preserved output: owned by
  `030-cli-and-production-path.md`; evidence must invoke the CLI without an
  injected client, use `NotesClient.from_environment()` over HTTP to a
  running notes service, and assert the parameterized result.
- Contract stability before consumer reliance: requires human review of the
  accepted contract and the API workstream's documented/integration-tested
  result before the client or CLI workstreams are marked executable.

### Additional implementation verification

- Run the focused tests for each subsystem and the full cross-boundary CLI
  check after implementation. No repository tests are run by this planning
  task.
````

### tasks/20260926-notes-query/010-public-api-contract-and-service.md

````markdown
# Public notes-query contract and service

Define the canonical HTTP contract first, then implement bounded pagination,
stable sorting, and optional text filtering in the FastAPI notes collection
without breaking unparameterized callers.

Parent Task: `tasks/20260926-notes-query/000-main.md`

Depends On: None

## Requirements checklist

- [ ] Establish a reviewed, documented HTTP query contract before downstream
  client or CLI implementation begins.
- [ ] Support bounded pagination on the public notes collection.
- [ ] Support deterministic sorting, including an explicit tie-breaker for
  equal primary sort values.
- [ ] Support the agreed optional text filter with documented matching scope
  and semantics.
- [ ] Preserve the current unparameterized `GET /notes/` response shape and
  all-notes behavior.
- [ ] Verify the behavior through the public API and storage boundary.

## Requirement questions and scope decisions

- Resolve the parent task's route, response-shape, parameter-name, bounds,
  filter, and invalid-input questions before implementation.
- Confirm whether the no-parameter route is deliberately unbounded for
  compatibility while explicitly paginated requests are bounded.
- Confirm the allow-listed sortable fields and the required direction syntax.

## Research and supporting facts

- The collection route is `GET /notes/` in `src/app/api/notes.py`.
- Querying currently delegates to `crud.get_all()` and returns a bare list.
- The SQL table has `id`, `title`, and `description`; it has no timestamp
  column suitable for ordering.
- Existing service tests only assert a 200 response and list type, so focused
  query and compatibility evidence is needed.

## Execution plan

Status: Draft

The service task is the source of truth for HTTP behavior. First record the
accepted contract, including examples, bounds, sorting/tie behavior, filter
scope, response shape, and validation errors. Then implement the query at the
service/storage boundary so filtering, ordering, limit, and offset are applied
before rows are returned. Keep the no-argument code path compatible with the
existing list response.

Verification should seed deterministic notes through supported service setup,
exercise the collection route through `TestClient`, and cover:

- no parameters returning the existing list shape and complete current result;
- each page respecting the agreed bound and offset semantics;
- repeated requests producing the same order, including equal primary sort
  values resolved by the agreed tie-breaker;
- title/description filter cases required by the contract;
- accepted boundary values and rejected out-of-range or invalid values.

Update the service README/development documentation only after the behavior
and contract are true. The API task is the gate that makes the downstream
client and CLI tasks executable.

### Implementation decisions and open questions

- This task owns the canonical public contract and should use the existing
  collection route unless the parent contract review chooses otherwise.
- The recommended response remains a JSON array to preserve the client and
  CLI list interfaces, but this requires approval.
- `id` is the recommended secondary key because it is the only existing
  schema field guaranteed to identify a row uniquely.
- Exact parameter vocabulary and validation rules remain open from the parent
  task.

### Documentation

- Maintain the notes-query contract in `docs/development/` and link it from
  `docs/development/index.md`.
- Update the root README's public API description after implementation.
- If the contract is written before the endpoint is implemented, mark it
  visibly as `Not implemented` until the API evidence passes.

### Task checklist

- [ ] Resolve and record the accepted HTTP contract.
- [ ] Implement service/storage query behavior.
- [ ] Add API compatibility, query, validation, and ordering tests.
- [ ] Update maintained service documentation.
- [ ] Report the API evidence and unblock downstream tasks.

### Requirement verification

- Public contract and service behavior: one API integration suite through
  `TestClient`, the FastAPI route, CRUD layer, and database adapter must
  exercise the complete query behavior.
- Unparameterized compatibility: the same public-route suite must assert a
  bare list and the expected complete result when no query parameters are
  supplied.
- Stability: the public-route suite must include tied sort values and assert
  the agreed deterministic secondary order.

### Additional implementation verification

- Run the focused service tests and inspect the generated OpenAPI/query
  declarations if the framework exposes them as part of the contract.
````

### tasks/20260926-notes-query/020-reusable-client.md

````markdown
# Reusable notes client query support

Expose the agreed notes-query capability through `NotesClient` while keeping
the existing no-argument method and list return behavior compatible.

Parent Task: `tasks/20260926-notes-query/000-main.md`

Depends On: `tasks/20260926-notes-query/010-public-api-contract-and-service.md`

## Requirements checklist

- [ ] Add client arguments that map one-to-one to the reviewed HTTP query
  contract for pagination, sorting, and optional text filtering.
- [ ] Omit unspecified query options so a no-argument call preserves the
  current request and list result.
- [ ] Preserve the existing reusable-client response behavior for both
  unparameterized and parameterized calls.
- [ ] Verify request serialization and response handling against the agreed
  service contract.
- [ ] Document the supported client interface.

## Requirement questions and scope decisions

- The API workstream must settle the exact argument names and response shape
  before this task starts.
- Confirm whether client-side validation should mirror the HTTP bounds or
  leave all validation to the service; the client must not silently create a
  second contract.
- Confirm whether the public method should use explicit keyword-only query
  arguments to avoid positional ambiguity.

## Research and supporting facts

- `NotesClient.list_notes()` currently takes no arguments and calls
  `transport.get("/notes/").json()`.
- The package test transport accepts `**kwargs` but does not currently record
  them, so serialization evidence must be added.
- The package README currently promises only the unparameterized collection.

## Execution plan

Status: Draft

After the API contract gate passes, extend `list_notes()` with the canonical
query options and serialize only values the caller supplied. Keep the
no-argument branch equivalent to the current `get("/notes/")` call so existing
transports and callers continue to work. Do not add client-specific defaults,
sort semantics, or filter interpretation that differ from the HTTP contract.

Use a recording transport test for exact URL/parameter mapping and omission of
unset options. Add a contract-level check using the real service boundary
where feasible, ensuring a parameterized call returns the same list-shaped
data the service documents. Preserve a no-argument regression test. Update the
package README after the API contract is current.

### Implementation decisions and open questions

- This task consumes, rather than defines, the HTTP query vocabulary.
- The method should retain a list return unless the approved API contract
  explicitly introduces metadata.
- Keyword-only arguments are recommended for a stable Python interface, but
  the public signature remains subject to contract review.
- Validation ownership must be aligned with the API; no independent client
  semantics should be introduced.

### Documentation

- Update `packages/notes_client/README.md` with the method signature,
  supported options, list return behavior, and a query example.
- Keep no-argument usage documented as the compatibility path.

### Task checklist

- [ ] Confirm the API contract gate is complete.
- [ ] Implement client argument and query serialization.
- [ ] Add request-mapping, response, and no-argument regression tests.
- [ ] Update the client README.
- [ ] Report evidence before the CLI task starts.

### Requirement verification

- Client capability: a public `NotesClient` test must call the method with
  each supported option and assert the exact request parameters sent to the
  transport.
- Client compatibility: a no-argument public method test must assert the
  existing path, no unexpected parameters, and list return.
- API alignment: at least one test must use the accepted service contract or
  the full CLI live-path check must include a parameterized call through this
  production client implementation.

### Additional implementation verification

- Run the package's focused test suite and verify that omitted options do not
  become accidental `null` or default query parameters.
````

### tasks/20260926-notes-query/030-cli-and-production-path.md

````markdown
# Notes CLI query support and production path

Expose the shared notes-query capability through `notes list`, preserve the
existing no-option command, and prove the real CLI-to-client-to-service path.

Parent Task: `tasks/20260926-notes-query/000-main.md`

Depends On:

- `tasks/20260926-notes-query/010-public-api-contract-and-service.md`
- `tasks/20260926-notes-query/020-reusable-client.md`

## Requirements checklist

- [ ] Add CLI options for the reviewed pagination, sorting, and optional text
  filtering contract.
- [ ] Map CLI options to the reusable client without duplicating query
  semantics.
- [ ] Preserve the existing no-option `notes list` output and invocation
  behavior.
- [ ] Prove a parameterized query through the CLI, production
  `NotesClient.from_environment()`, live HTTP, the FastAPI service, and its
  storage boundary without injecting a fake client.
- [ ] Document the supported CLI options and output.

## Requirement questions and scope decisions

- The API and client tasks must settle the canonical option names before CLI
  flags are finalized.
- Confirm whether flags should mirror the client/API vocabulary exactly or use
  CLI-specific aliases.
- Confirm whether the existing one-line `id: title` output is sufficient for
  filtered and paginated results; it is the recommended compatibility output.
- The decisive integration check must use a running local service and the
  production client construction path, not only the current injected-client
  unit fixture.

## Research and supporting facts

- `apps/notes_cli/cli.py` currently has only a `list` subcommand and prints
  each result as `id: title`.
- `main(argv=None, client=None)` allows tests to inject a fake client, but the
  default path constructs `NotesClient.from_environment()`.
- The current CLI fixture implements only `list_notes()` with no arguments,
  so the no-option path must not require new arguments from legacy-like
  clients.
- `apps/notes_cli/README.md` currently documents only `notes list`.

## Execution plan

Status: Draft

After both upstream contract gates pass, add flags that map directly to the
agreed client arguments. When no query flags are present, invoke
`list_notes()` with no arguments and retain the existing output. When flags
are present, pass only the selected values to the client; the CLI should not
reimplement filtering, ordering, or pagination.

The decisive check will start a local notes service on an available port with
the real FastAPI application and database, configure `NOTES_API_URL`, and
invoke the CLI entry path without supplying `client`. It must seed notes that
make the selected page, stable order, and text filter observable, then assert
the printed output. This crosses the actual CLI, `NotesClient.from_environment`,
`httpx.Client`, HTTP service, query implementation, and storage. Keep the
existing injected-client tests as local rendering/regression coverage, but do
not count them as the production-path proof.

Update the CLI README only after the end-to-end check passes.

### Implementation decisions and open questions

- The CLI consumes the API/client contract and owns only argument parsing and
  presentation.
- The no-option branch should call the client with no arguments to preserve
  the current seam and output.
- The recommended output remains one `id: title` line per returned note.
- The exact flag spelling and live-server test harness remain subject to the
  upstream contract decision; the production-path boundary itself is fixed.

### Documentation

- Update `apps/notes_cli/README.md` with all supported flags, compatibility
  behavior, output, and one parameterized example.
- Document the live production-path verification command or test entry point
  for future maintainers.

### Task checklist

- [ ] Confirm both API and client dependencies are complete.
- [ ] Implement CLI flags and client mapping.
- [ ] Preserve and update injected-client unit coverage as needed.
- [ ] Add and pass the live service/client/CLI integration check with no
  injected client.
- [ ] Update the CLI README.
- [ ] Report the full-path evidence to the parent task.

### Requirement verification

- CLI interface: parser and rendering tests must verify each supported option
  is passed to the client and that the no-option command retains its output.
- Production connection: one integration test must invoke the CLI without a
  supplied client, use `NOTES_API_URL` with a running FastAPI service, and
  assert the response produced by a parameterized query. This is the decisive
  evidence for the CLI-to-client-to-service requirement.

### Additional implementation verification

- Run the CLI-focused tests plus the live integration test in an environment
  where the service process and package import paths match supported usage.
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
            "where": "First checklist item",
            "quote": "Define and review one stable public query contract covering bounded pagination, deterministic sorting, optional text filtering, valid ranges, defaults, and invalid-input behavior.",
            "why": "One checkbox carries six contract facets, so the box cannot be checked incrementally; the reader must hold all six to know what 'done' means. At 140 words across 6 items the section still scans in one pass."
          }
        ]
      },
      "tasks/20260926-notes-query/000-main.md — Scope and workstreams": {
        "grade": "readable",
        "findings": [
          {
            "where": "Whole section",
            "quote": "The parent task coordinates three independently acceptable boundaries",
            "why": "Two short paragraphs plus a 3-item numbered list deliver the entire decomposition in one pass; 58 words with nothing to re-read."
          }
        ]
      },
      "tasks/20260926-notes-query/000-main.md — Requirement questions and scope decisions": {
        "grade": "readable",
        "findings": [
          {
            "where": "Third question item",
            "quote": "What are the canonical names and semantics for pagination, sorting, and filtering? A concrete recommendation to review is `limit` plus `offset`, an allow-listed sort field plus direction, and a text query applied as a case-insensitive substring over title and description.",
            "why": "Question and recommendation are interleaved within single items, so the reader must split 'open' from 'proposed' per item rather than per list."
          },
          {
            "where": "Closing paragraph",
            "quote": "The recommendations above are planning proposals, not completed requirements.",
            "why": "The rule that separates open questions from proposals arrives only after all six items, so it must be applied retroactively while re-reading the list."
          }
        ]
      },
      "tasks/20260926-notes-query/000-main.md — Research and supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "Fourth bullet",
            "quote": "Its existing test supplies an injected fake client; it does not exercise `NotesClient.from_environment()` or an HTTP service.",
            "why": "Five bullets at 90 words, each pairing one code fact with its immediate implication; scannable with no prose walls."
          }
        ]
      },
      "tasks/20260926-notes-query/000-main.md — Subtasks": {
        "grade": "readable",
        "findings": [
          {
            "where": "Whole section",
            "quote": "`tasks/20260926-notes-query/010-public-api-contract-and-service.md`",
            "why": "Three one-line file references; nothing to extract or reconcile."
          }
        ]
      },
      "tasks/20260926-notes-query/000-main.md — Execution plan": {
        "grade": "partial",
        "findings": [
          {
            "where": "Requirement verification, first bullet",
            "quote": "Canonical contract, bounded service query, stable ordering, text filtering, and unparameterized API compatibility: owned by `010-public-api-contract-and-service.md`; decisive evidence is an API integration test through `TestClient` and the real database adapter with records spanning page boundaries, sort ties, filter matches, and invalid bounds.",
            "why": "Wall-like item fusing five requirement areas, the owning file, and the evidence design into one compound sentence; extracting any single fact requires re-reading it."
          },
          {
            "where": "Multiple subsections (Requirements checklist item 5, Ordered execution 1, Task checklist 1/3, Requirement verification bullet 4)",
            "quote": "Contract stability before consumer reliance: requires human review of the accepted contract and the API workstream's documented/integration-tested result before the client or CLI workstreams are marked executable.",
            "why": "The single load-bearing sequencing fact (API contract gate before consumers) is restated in at least five differently-worded places in this 634-word section, so the reader must reconcile variants to find the authoritative statement."
          },
          {
            "where": "Task checklist",
            "quote": "Complete `020-reusable-client.md` after the API contract gate.",
            "why": "Duplicates the Subtasks list item for the same deliverable, adding to a wall of roughly 15 unchecked boxes in this file that track the same three files in two places."
          },
          {
            "where": "Ordered execution, item 5",
            "quote": "Update all affected maintained READMEs and development documentation, execute the focused tests plus the cross-boundary check, and record any deferred scope without silently changing the contract.",
            "why": "One step bundles three unrelated actions (documentation, test execution, scope recording), forcing the reader to unpack a compound instruction."
          }
        ]
      },
      "tasks/20260926-notes-query/010-public-api-contract-and-service.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "Whole section",
            "quote": "Preserve the current unparameterized `GET /notes/` response shape and all-notes behavior.",
            "why": "Six single-purpose items at 85 words; each box maps to one verifiable behavior, no compound boxes."
          }
        ]
      },
      "tasks/20260926-notes-query/010-public-api-contract-and-service.md — Requirement questions and scope decisions": {
        "grade": "readable",
        "findings": [
          {
            "where": "Second item",
            "quote": "Confirm whether the no-parameter route is deliberately unbounded for compatibility while explicitly paginated requests are bounded.",
            "why": "Three items, each one open decision at 43 words total; nothing to reconcile or re-read."
          }
        ]
      },
      "tasks/20260926-notes-query/010-public-api-contract-and-service.md — Research and supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "Fourth bullet",
            "quote": "Existing service tests only assert a 200 response and list type, so focused query and compatibility evidence is needed.",
            "why": "Each of four short bullets states a fact and its immediate consequence; the section is taken in at a glance."
          }
        ]
      },
      "tasks/20260926-notes-query/010-public-api-contract-and-service.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "Paragraph before the subsections",
            "quote": "Update the service README/development documentation only after the behavior and contract are true. The API task is the gate that makes the downstream client and CLI tasks executable.",
            "why": "The sequencing-critical gate fact is the last sentence of a paragraph that opens with documentation timing; it is findable but easy to skim past."
          },
          {
            "where": "Verification bullet list",
            "quote": "repeated requests producing the same order, including equal primary sort values resolved by the agreed tie-breaker;",
            "why": "Verification cases are split one-per-bullet, which keeps this 417-word section scannable despite three lead paragraphs."
          }
        ]
      },
      "tasks/20260926-notes-query/020-reusable-client.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "Whole section",
            "quote": "Add client arguments that map one-to-one to the reviewed HTTP query contract for pagination, sorting, and optional text filtering.",
            "why": "Five items at 77 words, one responsibility per box; no compound requirements."
          }
        ]
      },
      "tasks/20260926-notes-query/020-reusable-client.md — Requirement questions and scope decisions": {
        "grade": "readable",
        "findings": [
          {
            "where": "First item",
            "quote": "The API workstream must settle the exact argument names and response shape before this task starts.",
            "why": "A fixed dependency constraint sits under a 'questions' heading, so the reader must sort decided items from open ones within a 3-item list."
          }
        ]
      },
      "tasks/20260926-notes-query/020-reusable-client.md — Research and supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "Second bullet",
            "quote": "The package test transport accepts `**kwargs` but does not currently record them, so serialization evidence must be added.",
            "why": "Three short bullets, each linking a current state to its consequence; 38 words, nothing to re-read."
          }
        ]
      },
      "tasks/20260926-notes-query/020-reusable-client.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "Second paragraph",
            "quote": "Use a recording transport test for exact URL/parameter mapping and omission of unset options.",
            "why": "Two lead paragraphs where each sentence is a single instruction; the plan and its evidence split cleanly, so 335 words hold without strain."
          },
          {
            "where": "Implementation decisions, third bullet",
            "quote": "Keyword-only arguments are recommended for a stable Python interface, but the public signature remains subject to contract review.",
            "why": "Recommendation and open status are balanced in one clause, but the 'recommended / subject to review' pattern is used consistently across files, so it parses on first read."
          }
        ]
      },
      "tasks/20260926-notes-query/030-cli-and-production-path.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "Fourth item",
            "quote": "Prove a parameterized query through the CLI, production `NotesClient.from_environment()`, live HTTP, the FastAPI service, and its storage boundary without injecting a fake client.",
            "why": "The longest box enumerates one requirement (the proof path) rather than several unrelated facts; five items at 79 words remain scannable."
          }
        ]
      },
      "tasks/20260926-notes-query/030-cli-and-production-path.md — Requirement questions and scope decisions": {
        "grade": "readable",
        "findings": [
          {
            "where": "Fourth item",
            "quote": "The decisive integration check must use a running local service and the production client construction path, not only the current injected-client unit fixture.",
            "why": "A binding constraint sits among four items under a 'questions' heading; the reader must separate fixed decisions from genuinely open ones."
          },
          {
            "where": "Third item",
            "quote": "Confirm whether the existing one-line `id: title` output is sufficient for filtered and paginated results; it is the recommended compatibility output.",
            "why": "Question and recommendation packed into one item, mixing the open decision with the proposed answer."
          }
        ]
      },
      "tasks/20260926-notes-query/030-cli-and-production-path.md — Research and supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "Second bullet",
            "quote": "`main(argv=None, client=None)` allows tests to inject a fake client, but the default path constructs `NotesClient.from_environment()`.",
            "why": "Four code-level facts, one per bullet with the seam consequence attached; 61 words, easily held."
          }
        ]
      },
      "tasks/20260926-notes-query/030-cli-and-production-path.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "Third paragraph",
            "quote": "The decisive check will start a local notes service on an available port with the real FastAPI application and database, configure `NOTES_API_URL`, and invoke the CLI entry path without supplying `client`.",
            "why": "The 82-word decisive-evidence paragraph compresses harness setup, seeding, the crossed components, and a scope restriction into one block; each sentence is single-topic, but the block rewards a second read more than anything else in these files."
          },
          {
            "where": "Third paragraph, last sentence",
            "quote": "Keep the existing injected-client tests as local rendering/regression coverage, but do not count them as the production-path proof.",
            "why": "A load-bearing scope restriction (what does not count as proof) is embedded at the end of the densest paragraph rather than surfaced alongside the evidence definition."
          }
        ]
      }
    },
    "navigation": {
      "grade": "navigable",
      "findings": [
        {
          "where": "All four files",
          "quote": "Depends On: `tasks/20260926-notes-query/010-public-api-contract-and-service.md`",
          "why": "Identical section scaffolding (checklist, questions, research facts, execution plan with the same five subsections) plus Parent Task / Depends On lines at each file top means any fact type sits at a predictable position, and the 010-then-020-then-030 order is recoverable from structure alone."
        },
        {
          "where": "Execution plan, first line in each file",
          "quote": "Status: Draft",
          "why": "Plan status is one line into the fifth section rather than at the file top; a reader looking for state must scan past four sections first, though the heading makes the search short."
        },
        {
          "where": "000-main.md across sections",
          "quote": "Keep the plan in `Draft` until that review is complete.",
          "why": "The contract-gate constraint is highly findable only because it appears in five places; a reader landing on any one copy gets a different wording, so confirming the exact rule requires cross-checking."
        }
      ]
    },
    "mistakes": [
      {
        "where": "000-main.md, Execution plan, Requirement verification",
        "quote": "Canonical contract, bounded service query, stable ordering, text filtering, and unparameterized API compatibility: owned by `010-public-api-contract-and-service.md`; decisive evidence is an API integration test through `TestClient` and the real database adapter with records spanning page boundaries, sort ties, filter matches, and invalid bounds.",
        "why": "Compound bullets mix three fact types (requirement areas, ownership, evidence design) per item; these are the densest list items in the file set and the main reason this section strains."
      },
      {
        "where": "000-main.md, Task checklist vs. Subtasks",
        "quote": "Complete `010-public-api-contract-and-service.md`.",
        "why": "The Task checklist repeats the Subtasks file list as unchecked boxes, contributing to ~15 unchecked boxes in one file that track the same three deliverables twice."
      },
      {
        "where": "000-main.md, five locations (Requirements checklist item 5, Ordered execution 1, Task checklist 1/3, Requirement verification bullet 4)",
        "quote": "Do not begin consumer implementation against an unstable contract; the API contract must be reviewed and documented before the client and CLI depend on it.",
        "why": "The one load-bearing sequencing constraint is restated five times in different words; variants must be reconciled instead of pointing to a single authoritative statement."
      },
      {
        "where": "000-main.md, Ordered execution item 5",
        "quote": "Update all affected maintained READMEs and development documentation, execute the focused tests plus the cross-boundary check, and record any deferred scope without silently changing the contract.",
        "why": "One list item bundles three distinct actions (docs, tests, scope recording) that belong on separate lines for a checklist-style read."
      },
      {
        "where": "020-reusable-client.md and 030-cli-and-production-path.md, Requirement questions and scope decisions",
        "quote": "The API workstream must settle the exact argument names and response shape before this task starts. / The decisive integration check must use a running local service and the production client construction path, not only the current injected-client unit fixture.",
        "why": "Fixed dependencies and binding constraints are listed under a heading that promises open questions, so heading and content do not match and decided-vs-open status is blurred."
      },
      {
        "where": "000-main.md, Requirements checklist item 1",
        "quote": "covering bounded pagination, deterministic sorting, optional text filtering, valid ranges, defaults, and invalid-input behavior",
        "why": "One checkbox gates six sub-requirements, so the item cannot be progressed or checked incrementally."
      },
      {
        "where": "030-cli-and-production-path.md, Execution plan, third paragraph",
        "quote": "Keep the existing injected-client tests as local rendering/regression coverage, but do not count them as the production-path proof.",
        "why": "A buried load-bearing fact: the sentence deciding what does not count as the production-path proof is the last sentence of the densest paragraph in the file set."
      },
      {
        "where": "010-public-api-contract-and-service.md, Execution plan, lead paragraph",
        "quote": "Update the service README/development documentation only after the behavior and contract are true. The API task is the gate that makes the downstream client and CLI tasks executable.",
        "why": "Two unrelated facts (documentation timing and the gate role) share one paragraph, and the load-bearing gate statement is the trailing sentence, easy to skim past."
      }
    ],
    "summary": "These are consistently scaffolded planning files: every file repeats checklist, questions, research facts, and an execution plan with the same five subsections, which makes navigation genuinely easy — the outcome (Draft status with an API-contract gate), the open questions, and the dependencies are all recoverable from headings and the Depends On lines alone. The short sections are genuinely light: checklists run 77–140 words, research facts 38–90 words, and scope/questions sections stay at or under ~200 words with one-topic items. The single real strain point is the 000-main.md Execution plan at 634 words: its Requirement verification bullets fuse requirement lists, file ownership, and evidence design into single compound sentences, its Task checklist duplicates the Subtasks list, and the one sequencing constraint that governs the whole decomposition (API contract reviewed before client or CLI work begins) is restated five times in different words, forcing reconciliation rather than lookup. The child files' Execution plans (335–417 words) stay readable, with the 030 file's 82-word decisive-evidence paragraph the only other spot that rewards a second read. Net: 17 of 18 sections readable, 000-main.md's Execution plan partial; navigation navigable."
  }
}
```
