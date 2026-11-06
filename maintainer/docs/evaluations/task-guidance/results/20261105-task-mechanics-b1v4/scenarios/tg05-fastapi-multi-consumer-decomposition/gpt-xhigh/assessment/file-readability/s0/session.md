# Session — tg05-fastapi-multi-consumer-decomposition · file-readability-assessment-gpt-xhigh-s0 · glm max

- Run: `20261102T105434.094643Z-task-guidance-file-readability-tg05-fastapi-multi-consumer-decomposition-gpt-xhigh-s0-843e483b`
- Model: glm-5.3-flash (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-c440c4f661a7.md) — captured (original SHA-256 `73b879ff9f802f74…`)
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

#### tasks/20261102-notes-query/000-main.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261102-notes-query/000-main.md — Requirements checklist | 94 | 0 | 0 | 5 | 21 | 0 | 0 | 0 | 1 |
| tasks/20261102-notes-query/000-main.md — Questions and decisions | 174 | 0 | 0 | 5 | 51 | 0 | 0 | 0 | 20 |
| tasks/20261102-notes-query/000-main.md — Supporting details | 137 | 0 | 0 | 7 | 30 | 0 | 0 | 0 | 8 |
| tasks/20261102-notes-query/000-main.md — Subtasks | 50 | 0 | 0 | 3 | 18 | 0 | 0 | 0 | 3 |
| tasks/20261102-notes-query/000-main.md — Implementation plan | 601 | 7 | 96 | 8 | 68 | 5 | 0 | 0 | 5 |

#### tasks/20261102-notes-query/010-public-api.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261102-notes-query/010-public-api.md — Requirements checklist | 49 | 1 | 3 | 3 | 13 | 0 | 0 | 0 | 0 |
| tasks/20261102-notes-query/010-public-api.md — Supporting details | 78 | 0 | 0 | 5 | 24 | 0 | 0 | 0 | 10 |
| tasks/20261102-notes-query/010-public-api.md — Implementation plan | 394 | 6 | 73 | 7 | 42 | 5 | 0 | 0 | 1 |

#### tasks/20261102-notes-query/020-python-client.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261102-notes-query/020-python-client.md — Requirements checklist | 60 | 1 | 6 | 3 | 16 | 0 | 0 | 0 | 1 |
| tasks/20261102-notes-query/020-python-client.md — Supporting details | 48 | 0 | 0 | 3 | 21 | 0 | 0 | 0 | 6 |
| tasks/20261102-notes-query/020-python-client.md — Implementation plan | 326 | 6 | 63 | 6 | 46 | 5 | 0 | 0 | 5 |

#### tasks/20261102-notes-query/030-cli.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261102-notes-query/030-cli.md — Requirements checklist | 63 | 1 | 9 | 5 | 21 | 0 | 0 | 0 | 1 |
| tasks/20261102-notes-query/030-cli.md — Supporting details | 74 | 0 | 0 | 4 | 23 | 0 | 0 | 0 | 10 |
| tasks/20261102-notes-query/030-cli.md — Implementation plan | 416 | 6 | 87 | 6 | 64 | 5 | 0 | 0 | 5 |

The produced task files:

### tasks/20261102-notes-query/000-main.md

````markdown
# Notes Query Across API, Client, and CLI

Plan a supported notes-query capability across the public service, reusable Python client, and CLI.

## Requirements checklist

- [ ] The public notes collection supports bounded pagination, stable sorting, and optional text filtering under a defined contract.
- [ ] Requests that omit query options retain the current API response and `NotesClient.list_notes()` behavior.
- [ ] The reusable Python client and CLI expose the capability using the finalized public contract.
- [ ] The public API contract is established before client and CLI implementations rely on it.
- [ ] The CLI is verified through the production client against a running notes service, without substituting a fake client or fake service.

## Questions and decisions

- **Question — pagination contract:** What parameter names, default page size, maximum page size, and behavior for requests that specify sorting/filtering but omit a page size should apply? Recommendation: `limit` and `offset`, with a bounded default and hard maximum on parameterized requests; keep the exact no-query request unbounded for backward compatibility.
- **Question — sort contract:** Which note fields are sortable, which directions are supported, and what is the default? Recommendation: use `sort_by` and `order`, allow `id` and `title`, and use `id` as a deterministic tie-breaker.
- **Question — text-filter contract:** Which fields and matching semantics should the optional search cover? Recommendation: `q` performs a case-insensitive substring match over `title` and `description`.
- **Question — consumer interfaces:** Should client arguments and CLI flags mirror the HTTP names? Recommendation: client keyword arguments for `limit`, `offset`, `sort_by`, `order`, and `q`, with corresponding CLI options such as `--limit`, `--offset`, `--sort-by`, `--order`, and `--query`.
- These are public-interface decisions. Keep this plan in Draft and do not begin implementation until they are resolved and the plan is approved.

## Supporting details

- **Fact:** `GET /notes/` currently returns the complete collection as a JSON array through `crud.get_all()`.
- **Fact:** `NotesClient.list_notes()` currently makes an unparameterized `GET /notes/` request and returns decoded JSON.
- **Fact:** `notes list` currently prints each note's ID and title through the client.
- **Fact:** Existing API tests cover the unparameterized collection route; client and CLI tests use lightweight test doubles.
- **Fact:** The CLI project declares a `notes_cli.cli:main` console entry point, while the visible source is `apps/notes_cli/cli.py`. The production command's package/install path must be confirmed when designing its end-to-end check.
- **Fact:** Existing maintained documentation is in the root README and the client and CLI READMEs. `docs/development/index.md` says no notes-query specification exists.
- **Constraint:** The documentation guide favors updating the owning package documentation and avoiding placeholder pages. No task implementation or documentation changes have been made.

## Subtasks

- [ ] `tasks/20261102-notes-query/010-public-api.md` — Establish and deliver the public API contract first.
- [ ] `tasks/20261102-notes-query/020-python-client.md` — Add the reusable client interface after the API contract is delivered.
- [ ] `tasks/20261102-notes-query/030-cli.md` — Add CLI support and prove the real client-to-service path after the API and client are ready.

## Implementation plan

Status: Draft

The service owns the public query contract and applies filtering, ordering, and pagination at the collection route/database boundary. The exact parameter names, defaults, accepted sort values, and text matching behavior remain open in **Questions and decisions**; do not let the consumer interfaces invent or diverge from those semantics. Preserve the existing unparameterized route as a complete JSON-array response.

The independently reusable client maps its public method arguments to the finalized API query parameters. Its no-argument call remains the current bare collection request. The CLI maps its options to the client and retains the existing `notes list` output behavior when no options are supplied. The CLI deliverable owns one real HTTP integration check that exercises its production invocation, the production `NotesClient`, and a running notes service together.

Execution order is contract/API first, client second, CLI third. The API milestone must have a reviewed contract represented by the route behavior, OpenAPI schema, focused tests, and maintained API documentation before consumer implementation starts. This order prevents downstream packages from relying on a provisional interface. The client and CLI remain independently owned deliverables because they have separate package/application interfaces and compatibility expectations.

The change should be additive and require no schema migration: query computation should use the existing note fields and database table. The main risks are contract drift across three surfaces, unstable page boundaries from non-deterministic ordering, and an integration check that accidentally bypasses the real client or HTTP service. The API test should assert deterministic ordering and page boundaries; the CLI integration test should use a real listener and the actual configured client path. If a consumer fails, revert or disable that consumer before considering rollback of the additive API; preserve the existing no-parameter route throughout.

### Implementation decisions and open questions

The material public-contract and consumer-interface questions are listed above. Resolve them before execution; no behavior is selected by this draft plan.

### Documentation

Update the root README with the finalized public collection-query contract, `packages/notes_client/README.md` with client usage and compatibility, and `apps/notes_cli/README.md` with supported command options and invocation. Keep each description current with the behavior implemented in its owner. Do not create a separate specification page unless the contract cannot be documented clearly in the existing maintained locations.

### Task checklist

- [ ] Resolve the public contract and consumer-interface questions.
- [ ] Deliver and verify the public API before consumer work starts.
- [ ] Deliver the reusable client against the established contract.
- [ ] Deliver the CLI and its real client-to-service integration check.
- [ ] Update each owning README with supported behavior.

### Requirement verification

- **API query and compatibility requirements:** Focused tests through the public FastAPI collection route and the real database verify the approved pagination bounds, sort stability, filtering semantics, and unchanged no-query array behavior. These tests do not establish the reusable package or CLI invocation path.
- **Client and CLI requirements:** Client unit tests verify parameter mapping and no-argument compatibility. The decisive cross-component check belongs to the CLI subtask: run the actual CLI command against a live service using the production `NotesClient` configuration and known notes, and verify returned output reflects the requested query. It must not inject a fake client, mock HTTP responses, or call a route directly in place of the client.
- **Contract-before-consumers requirement:** Verify the API contract is documented and represented in route/OpenAPI tests before the client and CLI implementation milestones begin. This is an execution-order gate, not a test-only claim.

### Additional implementation verification

Confirm the CLI package's registered console entry point can be invoked in the integration environment. If its current source/package layout prevents that, make only the minimal CLI packaging adjustment necessary for the production invocation and include it in the CLI deliverable.
````

### tasks/20261102-notes-query/010-public-api.md

````markdown
# Public Notes Query API

Establish and deliver the notes-query contract at the public FastAPI collection route before downstream consumers rely on it.

## Requirements checklist

- [ ] The public collection route supports the approved bounded-pagination, stable-sorting, and optional text-filtering contract.
- [ ] A request without query parameters retains the current complete JSON-array response.
- [ ] The public contract is documented and testable before client or CLI implementation begins.

Parent Task: tasks/20261102-notes-query/000-main.md

## Supporting details

- **Fact:** `src/app/api/notes.py` exposes `GET /notes/` and delegates to `crud.get_all()`.
- **Fact:** `src/app/api/crud.py` currently returns all rows from `notes.select()` without explicit ordering or query parameters.
- **Fact:** `src/app/db.py` stores notes in an existing SQLite table with `id`, `title`, and `description` columns.
- **Fact:** `src/tests/test_notes.py` checks that the unparameterized collection response is a JSON array.
- **Constraint:** Query names, bounds/defaults, sortable fields, tie-breaking, and text matching semantics are unresolved in the parent task and must be approved before implementation.

## Implementation plan

Status: Draft

The API owns the shared contract. Once the parent task's public-interface questions are resolved, encode the approved query parameters and validation in the collection route, and apply filtering, explicit deterministic ordering, and bounded selection in the database query path. Keep the existing no-parameter request as a compatibility path that returns all notes in the existing JSON-array shape. Do not add a second endpoint or alter note representation unless the approved contract requires it.

This deliverable blocks the client and CLI subtasks. Finish the public contract, route behavior, focused route/database tests, and API README update before consumer work begins. This milestone gives consumers one stable source of truth rather than allowing each package to infer API semantics.

Risks include accidental truncation of legacy requests, an unstable ordering for equal sort values, and filtering performed only after fetching all rows. Verify the public route against the database with data that exercises pagination edges, ties, and matches/non-matches. If the new behavior fails, remove or correct the query extension while retaining the original no-parameter route; no database migration should be needed.

### Implementation decisions and open questions

The parent task's unresolved public API decisions must be answered before implementation. This subtask does not choose query names, limits, sort fields, or search semantics independently.

### Documentation

Update the root `README.md` with the approved collection query parameters, their semantics and bounds, and the preserved unparameterized behavior. Ensure FastAPI's generated OpenAPI representation reflects the same contract. Do not create a standalone specification page unless the parent approves that documentation direction.

### Task checklist

- [ ] Resolve the parent task's API contract questions.
- [ ] Implement query validation and database filtering, ordering, and pagination.
- [ ] Add public-route tests for approved query behavior and legacy behavior.
- [ ] Update the root README and verify generated OpenAPI.
- [ ] Mark the API contract milestone complete before consumer implementation.

### Requirement verification

- **Query behavior and legacy compatibility:** Tests through the public collection route with the real application/database verify each approved query condition and the unchanged no-query JSON-array response. They deliberately do not verify client argument mapping, CLI options, or the live network path.
- **Contract readiness:** Inspect the maintained API documentation and generated OpenAPI alongside the passing route tests before unblocking the client and CLI subtasks.

### Additional implementation verification

Check that the selected ordering includes a deterministic tie-breaker and that page selection occurs in the database query rather than only in application memory.
````

### tasks/20261102-notes-query/020-python-client.md

````markdown
# Reusable Python Client Notes Query

Expose the finalized notes-query API through the independently reusable Python client while preserving its current no-argument behavior.

## Requirements checklist

- [ ] The reusable client exposes the approved pagination, sorting, and text-filtering options using the finalized API contract.
- [ ] Calling `NotesClient.list_notes()` without options continues to issue the existing unparameterized request and return decoded JSON.
- [ ] Client documentation describes supported query usage without claiming behavior beyond the public API contract.

Parent Task: tasks/20261102-notes-query/000-main.md
Depends On: tasks/20261102-notes-query/010-public-api.md

## Supporting details

- **Fact:** `packages/notes_client/notes_client/client.py` implements `list_notes()` as `GET /notes/` followed by `.json()`.
- **Fact:** The client package currently depends on `httpx`; its tests use a small transport double.
- **Constraint:** This deliverable depends on the API contract and behavior in `tasks/20261102-notes-query/010-public-api.md`. It must not define independent names or semantics.

## Implementation plan

Status: Draft

After the API task establishes the contract, extend the client's public `list_notes()` interface to accept the approved query options and forward them using the corresponding HTTP parameters. Preserve the existing no-argument call as a bare `GET /notes/` request so existing consumers retain the same route, response decoding, and full-collection behavior. Keep parameter translation in the client rather than duplicating server-side filtering or sorting.

This task follows the API milestone and blocks the CLI task. Focused client tests should verify correct parameter forwarding and that no arguments do not introduce a query payload. Those tests are local package evidence only; the CLI task owns the decisive integration check through a real HTTP service and the production client configuration.

The main risk is interface drift or changing the no-argument call while adding optional parameters. If the new method surface proves incompatible, retain the no-argument signature behavior and revise only the additive options to match the approved API contract.

### Implementation decisions and open questions

Use the approved parameter and matching semantics from `tasks/20261102-notes-query/010-public-api.md`. Any unresolved consumer naming question in the parent task must be answered before implementation.

### Documentation

Update `packages/notes_client/README.md` with the approved method arguments, an example of a filtered/paginated/sorted call, and a clear statement that the no-argument call preserves the existing full collection behavior.

### Task checklist

- [ ] Confirm the API milestone is complete and its contract is stable.
- [ ] Add the client query arguments and parameter forwarding.
- [ ] Test parameter forwarding and no-argument compatibility.
- [ ] Update the client README.
- [ ] Provide the completed client for CLI integration.

### Requirement verification

- **Client capability and compatibility:** Client tests use the package's transport boundary to verify the exact approved parameters are sent and that a no-argument call remains unparameterized. They deliberately do not claim to prove the live service or CLI path; that evidence is owned by `tasks/20261102-notes-query/030-cli.md`.

### Additional implementation verification

Check public method defaults and annotations against the approved API behavior so omitted arguments do not silently change the legacy request.
````

### tasks/20261102-notes-query/030-cli.md

````markdown
# Notes Query CLI

Expose notes querying through the CLI and verify the production CLI-to-client-to-service path.

## Requirements checklist

- [ ] The CLI exposes the approved pagination, sorting, and text-filtering options through the reusable client.
- [ ] Running `notes list` without options retains its current output behavior.
- [ ] An integration check exercises the actual CLI invocation, production client configuration, and running notes service together without fakes at those boundaries.

Parent Task: tasks/20261102-notes-query/000-main.md
Depends On:
- tasks/20261102-notes-query/010-public-api.md
- tasks/20261102-notes-query/020-python-client.md

## Supporting details

- **Fact:** `apps/notes_cli/cli.py` currently offers `list` and delegates output to `NotesClient.list_notes()`.
- **Fact:** `apps/notes_cli/tests/test_cli.py` tests `list_command()` with an injected client fixture, so it does not prove the production client-to-service path.
- **Fact:** `apps/notes_cli/pyproject.toml` registers `notes_cli.cli:main`, while the visible source file is `apps/notes_cli/cli.py`; verify the console-entry-point packaging path as part of the real invocation.
- **Constraint:** CLI option names and semantics must match the decisions recorded in `tasks/20261102-notes-query/000-main.md` and the API contract delivered by `tasks/20261102-notes-query/010-public-api.md`.

## Implementation plan

Status: Draft

After the API and reusable client milestones are complete, extend `notes list` with options matching the approved CLI interface and pass them to the production client. Keep the existing no-option command and ID/title output. Do not implement filtering, sorting, or pagination in the CLI itself.

This is the last dependent deliverable because its decisive check must cross all production layers. Start a real notes service on a local HTTP listener with known notes, configure `NOTES_API_URL`, then invoke the registered CLI command without injecting a client. Select query options whose expected result distinguishes the requested filtering, ordering, and page boundary, and assert the command output. If the installed console entry point cannot currently be invoked because of the source/package layout, make only the minimal packaging adjustment required to exercise that supported production command.

The key risk is a test that appears end-to-end but substitutes a fake client, mocks HTTP, or calls the route directly. Such a test does not satisfy the requirement. Another risk is losing the existing simple command behavior while adding options. If integration fails, isolate whether the issue is packaging, client parameter forwarding, or service behavior; keep the prior no-option CLI and API paths intact while correcting the failing layer.

### Implementation decisions and open questions

Follow the parent task's approved CLI option naming decision and the finalized API/client contract. Do not resolve those public-interface choices independently in this subtask.

### Documentation

Update `apps/notes_cli/README.md` with the approved command options, a real invocation example, and the existing behavior when options are omitted. Keep the example consistent with the tested production entry point.

### Task checklist

- [ ] Confirm the API and client dependencies are complete.
- [ ] Add CLI options and pass them through the reusable client.
- [ ] Preserve and test the no-option `notes list` output.
- [ ] Add a real-listener integration check for CLI, production client, and service.
- [ ] Verify the registered console entry point and update the CLI README.

### Requirement verification

- **CLI capability, compatibility, and production path:** Run the actual CLI command against a running notes service over HTTP, with `NOTES_API_URL` configured and known service data. Do not inject a client or mock the transport/service. Assert output that proves the approved filter, sort, and pagination options reached the service and affected the returned notes. Also verify that omitting options preserves the current output behavior.

### Additional implementation verification

Confirm the integration check invokes the supported console entry point rather than only calling the output helper, and that it starts/stops its service cleanly without relying on a developer's manually running service.
````


**Assistant** *(reasoning present)*

```json
{
  "schema_version": 1,
  "scenario_id": "tg05-fastapi-multi-consumer-decomposition",
  "assessment": {
    "sections": {
      "tasks/20261102-notes-query/000-main.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "5 unchecked checklist items",
            "quote": "- [ ] The CLI is verified through the production client against a running notes service, without substituting a fake client or fake service.",
            "why": "Each item is a single 13–21 word sentence carrying one requirement, so the outcome list scans in one pass; even the longest item reads as a single claim."
          }
        ]
      },
      "tasks/20261102-notes-query/000-main.md — Questions and decisions": {
        "grade": "readable",
        "findings": [
          {
            "where": "pagination bullet",
            "quote": "**Question — pagination contract:** What parameter names, default page size, maximum page size, and behavior for requests that specify sorting/filtering but omit a page size should apply? Recommendation: `limit` and `offset`, ...",
            "why": "Bold topic lead-ins plus 20 code spans let a reader scan all five open decisions; the 51-word item splits cleanly at 'Recommendation:' so question and proposed answer stay distinguishable."
          },
          {
            "where": "final bullet",
            "quote": "- These are public-interface decisions. Keep this plan in Draft and do not begin implementation until they are resolved and the plan is approved.",
            "why": "This item drops the Question/Recommendation pattern and is a directive rather than a question; it does not block comprehension but slightly muddies what the section contains (also listed in mistakes)."
          }
        ]
      },
      "tasks/20261102-notes-query/000-main.md — Supporting details": {
        "grade": "readable",
        "findings": [
          {
            "where": "seven bold-prefixed bullets",
            "quote": "- **Fact:** The CLI project declares a `notes_cli.cli:main` console entry point, while the visible source is `apps/notes_cli/cli.py`.",
            "why": "One fact per bullet, each ≤30 words with a Fact/Constraint type label, makes the evidence list attributable and skimmable."
          }
        ]
      },
      "tasks/20261102-notes-query/000-main.md — Subtasks": {
        "grade": "readable",
        "findings": [
          {
            "where": "3 checklist items",
            "quote": "- [ ] `tasks/20261102-notes-query/010-public-api.md` — Establish and deliver the public API contract first.",
            "why": "Each item is one file link plus one ordering clause; the three-step execution order is visible at a glance."
          }
        ]
      },
      "tasks/20261102-notes-query/000-main.md — Implementation plan": {
        "grade": "partial",
        "findings": [
          {
            "where": "fourth prose paragraph",
            "quote": "The change should be additive and require no schema migration: ... The main risks are contract drift across three surfaces, unstable page boundaries from non-deterministic ordering, and an integration check that accidentally bypasses the real client or HTTP service. The API test should assert deterministic ordering and page boundaries; ... If a consumer fails, revert or disable that consumer before considering rollback of the additive API; preserve the existing no-parameter route throughout.",
            "why": "The 96-word paragraph stacks four concerns — additivity, risk inventory, per-component test assertions, and rollback policy — forcing a re-read to separate them."
          },
          {
            "where": "Task checklist subsection vs. Requirements checklist and Subtasks",
            "quote": "- [ ] Deliver and verify the public API before consumer work starts.",
            "why": "This near-duplicates the Requirements checklist item 'The public API contract is established before client and CLI implementations rely on it.' and the Subtasks entries, so the file carries three overlapping lists and the reader must reconcile which is authoritative."
          },
          {
            "where": "Implementation decisions and open questions subsection",
            "quote": "The material public-contract and consumer-interface questions are listed above. Resolve them before execution; no behavior is selected by this draft plan.",
            "why": "The heading promises decisions and questions but the body is only a pointer upward; a reader searching this subsection for the decisions finds none."
          }
        ]
      },
      "tasks/20261102-notes-query/010-public-api.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "3 checklist items",
            "quote": "- [ ] The public contract is documented and testable before client or CLI implementation begins.",
            "why": "Outcome, backward compatibility, and sequencing are split across three short one-line items; nothing requires re-reading."
          }
        ]
      },
      "tasks/20261102-notes-query/010-public-api.md — Supporting details": {
        "grade": "readable",
        "findings": [
          {
            "where": "Constraint bullet",
            "quote": "- **Constraint:** Query names, bounds/defaults, sortable fields, tie-breaking, and text matching semantics are unresolved in the parent task and must be approved before implementation.",
            "why": "Five bullets, each a single Fact or Constraint ≤24 words with a bold type label; the blocking dependency is stated once, clearly."
          }
        ]
      },
      "tasks/20261102-notes-query/010-public-api.md — Implementation plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "third prose paragraph",
            "quote": "Risks include accidental truncation of legacy requests, an unstable ordering for equal sort values, and filtering performed only after fetching all rows.",
            "why": "Paragraphs hold one theme each (contract encoding, blocking gate, risks/verification/rollback); the 73-word close separates risk, test data, and rollback sentence-by-sentence, so it holds on first reading."
          },
          {
            "where": "Requirement verification subsection",
            "quote": "They deliberately do not verify client argument mapping, CLI options, or the live network path.",
            "why": "The verification bullets state both what is proven and what is explicitly out of scope, which is easy to scan and prevents over-claiming."
          }
        ]
      },
      "tasks/20261102-notes-query/020-python-client.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "compatibility item",
            "quote": "- [ ] Calling `NotesClient.list_notes()` without options continues to issue the existing unparameterized request and return decoded JSON.",
            "why": "Three short items separate new capability, compatibility guarantee, and documentation scope; the code span anchors the compatibility claim to a concrete symbol."
          }
        ]
      },
      "tasks/20261102-notes-query/020-python-client.md — Supporting details": {
        "grade": "readable",
        "findings": [
          {
            "where": "Constraint bullet",
            "quote": "- **Constraint:** This deliverable depends on the API contract and behavior in `tasks/20261102-notes-query/010-public-api.md`. It must not define independent names or semantics.",
            "why": "Three bullets of one fact each, ≤21 words; the dependency and its prohibition are stated in two clean sentences."
          }
        ]
      },
      "tasks/20261102-notes-query/020-python-client.md — Implementation plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "first prose paragraph",
            "quote": "Keep parameter translation in the client rather than duplicating server-side filtering or sorting.",
            "why": "The three paragraphs are single-theme (argument mapping, sequencing/tests, risk/rollback) with roughly one directive per sentence; the 63-word maximum stays parseable in one pass."
          },
          {
            "where": "second prose paragraph",
            "quote": "Those tests are local package evidence only; the CLI task owns the decisive integration check through a real HTTP service and the production client configuration.",
            "why": "Cross-task evidence ownership is embedded mid-paragraph in prose rather than structured, but it is stated plainly enough to catch on first read."
          }
        ]
      },
      "tasks/20261102-notes-query/030-cli.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "integration item",
            "quote": "- [ ] An integration check exercises the actual CLI invocation, production client configuration, and running notes service together without fakes at those boundaries.",
            "why": "Five one-sentence items each carry one requirement; the longest (21 words) enumerates three boundaries but stays a single scannable claim."
          }
        ]
      },
      "tasks/20261102-notes-query/030-cli.md — Supporting details": {
        "grade": "readable",
        "findings": [
          {
            "where": "packaging fact bullet",
            "quote": "- **Fact:** `apps/notes_cli/pyproject.toml` registers `notes_cli.cli:main`, while the visible source file is `apps/notes_cli/cli.py`; verify the console-entry-point packaging path as part of the real invocation.",
            "why": "Four bold-labeled bullets remain short (≤23 words) and findable, though this Fact bullet also smuggles in a directive (see mistakes); it still parses in one pass."
          }
        ]
      },
      "tasks/20261102-notes-query/030-cli.md — Implementation plan": {
        "grade": "partial",
        "findings": [
          {
            "where": "second prose paragraph",
            "quote": "Start a real notes service on a local HTTP listener with known notes, configure `NOTES_API_URL`, then invoke the registered CLI command without injecting a client. Select query options whose expected result distinguishes the requested filtering, ordering, and page boundary, and assert the command output.",
            "why": "This is the core integration procedure of the whole task set, delivered as sequential prose: the reader must reconstruct the implicit step order by re-reading instead of scanning a list, and the paragraph ends with a packaging contingency folded in (87 words)."
          },
          {
            "where": "Requirement verification subsection, first bullet",
            "quote": "**CLI capability, compatibility, and production path:** Run the actual CLI command against a running notes service over HTTP, with `NOTES_API_URL` configured and known service data. Do not inject a client or mock the transport/service. Assert output that proves the approved filter, sort, and pagination options reached the service and affected the returned notes. Also verify that omitting options preserves the current output behavior.",
            "why": "The decisive acceptance criterion is a 64-word wall item bundling four instructions (run, prohibit, assert, regression-check); extracting the full requirement takes multiple passes."
          },
          {
            "where": "third prose paragraph",
            "quote": "The key risk is a test that appears end-to-end but substitutes a fake client, mocks HTTP, or calls the route directly. Such a test does not satisfy the requirement.",
            "why": "Risk, failure isolation, and rollback are packed into one 87-word paragraph, so the reader must untangle three topics that recur verbatim in other sections."
          }
        ]
      }
    },
    "navigation": {
      "grade": "navigable",
      "findings": [
        {
          "where": "dependency metadata in subtask files",
          "quote": "Depends On:\n- tasks/20261102-notes-query/010-public-api.md\n- tasks/20261102-notes-query/020-python-client.md",
          "why": "Explicit Parent Task / Depends On lines plus the parent's numbered Subtasks make execution order and file relationships findable from structure alone, without reading plan prose."
        },
        {
          "where": "plan status markers",
          "quote": "Status: Draft",
          "why": "Open questions have a dedicated titled section in the parent, every plan opens with an explicit status line, and unchecked boxes signal state, so outcome, open questions, and status are each locatable immediately."
        },
        {
          "where": "constraint locations across files",
          "quote": "without substituting a fake client or fake service",
          "why": "The binding no-fakes constraint has no single home: near-identical wording recurs in the 000-main checklist, two plan paragraphs, its Requirement verification, and three places in 030-cli, so confirming the full constraint requires reading several sections rather than one."
        }
      ]
    },
    "mistakes": [
      {
        "where": "tasks/20261102-notes-query/000-main.md — Questions and decisions, final bullet",
        "quote": "- These are public-interface decisions. Keep this plan in Draft and do not begin implementation until they are resolved and the plan is approved.",
        "why": "A load-bearing process directive hides as the tail item of a question list, breaking the section's Question/Recommendation pattern; a reader scanning for questions will mis-file the draft/approval gate."
      },
      {
        "where": "tasks/20261102-notes-query/000-main.md — Implementation plan, fourth paragraph",
        "quote": "The main risks are contract drift across three surfaces, unstable page boundaries from non-deterministic ordering, and an integration check that accidentally bypasses the real client or HTTP service. The API test should assert deterministic ordering and page boundaries; the CLI integration test should use a real listener and the actual configured client path. If a consumer fails, revert or disable that consumer before considering rollback of the additive API; preserve the existing no-parameter route throughout.",
        "why": "Prose wall: 96 words mixing risk inventory, per-component test assertions, and rollback policy in one paragraph; each concern deserves its own line to be actionable."
      },
      {
        "where": "all four files — Implementation plan → Task checklist vs. top-level Requirements checklist/Subtasks",
        "quote": "- [ ] Deliver and verify the public API before consumer work starts.",
        "why": "Every file carries two to three overlapping checklists (Requirements checklist, Subtasks, and an in-plan Task checklist) restating the same milestones in different words; the reader must diff them to find which is authoritative, and future edits can silently diverge."
      },
      {
        "where": "tasks/20261102-notes-query/000-main.md — Implementation plan → Implementation decisions and open questions (same pattern in 010 and 030)",
        "quote": "The material public-contract and consumer-interface questions are listed above.",
        "why": "Heading promises decisions and open questions but the body is only an upward pointer; the actual questions live solely in the parent's Questions and decisions section, so the heading does not match its content."
      },
      {
        "where": "no-fakes rule, stated in 000-main checklist, 000-main plan, 000-main Requirement verification, and 030-cli checklist/plan/verification",
        "quote": "It must not inject a fake client, mock HTTP responses, or call a route directly in place of the client.",
        "why": "The single most important prohibition is restated at least six times with varying wording across two files, burying the load-bearing rule through repetition and creating drift risk when one instance is edited."
      },
      {
        "where": "tasks/20261102-notes-query/030-cli.md — Supporting details, third Fact bullet",
        "quote": "- **Fact:** `apps/notes_cli/pyproject.toml` registers `notes_cli.cli:main`, while the visible source file is `apps/notes_cli/cli.py`; verify the console-entry-point packaging path as part of the real invocation.",
        "why": "A directive ('verify ...') is mixed into a bullet labeled Fact, conflating observed state with required action; the same mixed fact-plus-instruction also appears in 000-main's Supporting details."
      },
      {
        "where": "tasks/20261102-notes-query/030-cli.md — Implementation plan, second paragraph",
        "quote": "Start a real notes service on a local HTTP listener with known notes, configure `NOTES_API_URL`, then invoke the registered CLI command without injecting a client.",
        "why": "Step-by-step procedure is written as running prose; the implicit sequence (start service → configure → invoke → assert) must be extracted by re-reading instead of scanned as an ordered list."
      },
      {
        "where": "010/020/030 — dependency metadata placement",
        "quote": "Parent Task: tasks/20261102-notes-query/000-main.md",
        "why": "Parent/Depends On metadata sits directly under the '## Requirements checklist' heading (visible as stray short paragraphs in the measured facts), so routing information is filed under a heading that does not describe it."
      },
      {
        "where": "tasks/20261102-notes-query/000-main.md — Implementation plan, first paragraph",
        "quote": "The exact parameter names, defaults, accepted sort values, and text matching behavior remain open in **Questions and decisions**; do not let the consumer interfaces invent or diverge from those semantics.",
        "why": "An execution gate is buried mid-paragraph in dense prose and duplicates both the closing directive of Questions and decisions and 010's Constraint bullet — three phrasings of one gate."
      }
    ],
    "summary": "The task set is consistently templated and easy to traverse: short bold-prefixed bullets carry facts and questions, dependencies and status are explicit, and every file's outcome list sits at the top, so navigation is genuinely structure-driven (navigable). 15 of 14 sections... more precisely, 13 of 14 sections grade readable: checklists, Supporting details, Questions and decisions, and Subtasks are all one-concern-per-line with code spans anchoring symbols. The strain concentrates exactly where the measurements point — the two densest Implementation plan sections. 000-main's plan (601 words, 96-word paragraph) stacks risks, test assertions, and rollback policy in single paragraphs, and 030-cli's plan buries the task set's core integration procedure as sequential prose and packs its decisive acceptance criterion into a 64-word wall item. Set-wide, three overlapping checklists per file and the six-fold restatement of the no-fakes rule mean readers can find every answer but must reconcile duplicates to be certain they hold the authoritative one."
  }
}
```
