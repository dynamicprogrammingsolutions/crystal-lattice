# Session — tg05-fastapi-multi-consumer-decomposition · file-readability-assessment-gpt-max-s0 · glm max

- Run: `20261102T105917.643712Z-task-guidance-file-readability-tg05-fastapi-multi-consumer-decomposition-gpt-max-s0-aa4944f0`
- Model: glm-5.3-flash (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-c440c4f661a7.md) — captured (original SHA-256 `8683470362c302c3…`)
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
| tasks/20261102-notes-query/000-main.md — Requirements checklist | 83 | 0 | 0 | 5 | 17 | 0 | 0 | 0 | 1 |
| tasks/20261102-notes-query/000-main.md — Questions and decisions | 92 | 0 | 0 | 2 | 67 | 0 | 0 | 0 | 0 |
| tasks/20261102-notes-query/000-main.md — Supporting details | 67 | 0 | 0 | 4 | 28 | 0 | 0 | 0 | 5 |
| tasks/20261102-notes-query/000-main.md — Subtasks | 12 | 0 | 0 | 3 | 1 | 0 | 0 | 0 | 3 |
| tasks/20261102-notes-query/000-main.md — Implementation plan | 515 | 3 | 92 | 14 | 34 | 5 | 0 | 0 | 2 |
| tasks/20261102-notes-query/000-main.md — Implementation notes | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

#### tasks/20261102-notes-query/010-public-api.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261102-notes-query/010-public-api.md — Requirements checklist | 47 | 0 | 0 | 3 | 13 | 0 | 0 | 0 | 0 |
| tasks/20261102-notes-query/010-public-api.md — Questions and decisions | 24 | 0 | 0 | 1 | 24 | 0 | 0 | 0 | 0 |
| tasks/20261102-notes-query/010-public-api.md — Supporting details | 29 | 0 | 0 | 2 | 16 | 0 | 0 | 0 | 1 |
| tasks/20261102-notes-query/010-public-api.md — Implementation plan | 199 | 2 | 52 | 8 | 30 | 5 | 0 | 0 | 0 |

#### tasks/20261102-notes-query/020-python-client.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261102-notes-query/020-python-client.md — Requirements checklist | 32 | 0 | 0 | 2 | 13 | 0 | 0 | 0 | 1 |
| tasks/20261102-notes-query/020-python-client.md — Supporting details | 28 | 0 | 0 | 2 | 16 | 0 | 0 | 0 | 2 |
| tasks/20261102-notes-query/020-python-client.md — Implementation plan | 197 | 2 | 58 | 7 | 33 | 5 | 0 | 0 | 3 |

#### tasks/20261102-notes-query/030-cli.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261102-notes-query/030-cli.md — Requirements checklist | 38 | 0 | 0 | 3 | 11 | 0 | 0 | 0 | 0 |
| tasks/20261102-notes-query/030-cli.md — Supporting details | 43 | 0 | 0 | 2 | 24 | 0 | 0 | 0 | 3 |
| tasks/20261102-notes-query/030-cli.md — Implementation plan | 235 | 2 | 82 | 8 | 35 | 5 | 0 | 0 | 4 |

The produced task files:

### tasks/20261102-notes-query/000-main.md

````markdown
# Supported Notes Query

Plan a single supported notes-query capability across the public API, reusable Python client, and CLI.

## Requirements checklist
- [ ] The public notes collection supports bounded pagination, stable sorting, and optional text filtering.
- [ ] Requests without query parameters preserve the existing public API collection response and the existing no-argument `NotesClient.list_notes()` behavior.
- [ ] The public query contract is defined and documented before client and CLI behavior depends on it.
- [ ] The reusable Python client exposes the supported query options.
- [ ] The CLI exposes the supported query options and demonstrates the production client-to-service path.

## Questions and decisions
- **Question — API contract:** Decide the parameter names, page bounds/defaults, sorting fields and direction syntax, stable tie-breaker, filter matching fields and semantics, and whether filtered/paginated results use an envelope or retain a bare array. These choices affect public compatibility. Recommendation: preserve the bare-array response when parameters are absent and use explicit documented pagination parameters with a bounded maximum; settle the parameterized response shape before consumer work.
- **Question — text matching:** Decide whether matching is case-sensitive and whether the query searches title, description, or both. Do not infer behavior while implementing.

## Supporting details
- The current FastAPI collection route returns `crud.get_all()` directly, with no query parameters.
- `NotesClient.list_notes()` currently issues `GET /notes/` and returns decoded JSON.
- The CLI currently offers `notes list` and prints each note's ID and title through `NotesClient`.
- The API, client package, and CLI have independently maintained readmes and test suites. The public HTTP contract, reusable package interface, and CLI interface are separate compatibility boundaries.

## Subtasks
- [ ] `tasks/20261102-notes-query/010-public-api.md`
- [ ] `tasks/20261102-notes-query/020-python-client.md`
- [ ] `tasks/20261102-notes-query/030-cli.md`

## Implementation plan
Status: Draft

The public HTTP API owns query semantics and its compatibility boundary. It must settle and document the query contract before consumers adopt it; the existing no-parameter collection request remains a bare list. The client owns a reusable Python interface that maps its supported options onto that contract while retaining no-argument behavior. The CLI owns argument parsing and presentation, delegating the query to the real client rather than reproducing query logic.

Execution order follows the contract dependency: first define and implement the API contract, then implement the client mapping, then expose those options in the CLI. Keep focused API and client evidence with their respective deliverables. For the CLI, the decisive integration check must invoke the actual CLI command with the production `NotesClient` against the actual FastAPI application and verify that query arguments affect the notes returned; tests that mock the client or route separately do not prove this connection.

The main risk is a mismatched or prematurely relied-upon query contract across the three boundaries. Mitigate it by resolving the open contract questions before consumer implementation and keeping contract documentation and API tests aligned. The no-parameter API/client behavior is a required regression check. If the parameterized contract proves incompatible with the established API, stop before consumer rollout and revise the proposed contract for review; do not silently change the compatibility boundary. Changes remain additive and can be reverted by removing the query implementation and consumer options while retaining the original unparameterized path.

### Implementation decisions and open questions
- Resolve the API and text-matching questions above before execution; no parameter names, defaults, bounds, ordering fields, matching rules, or parameterized response shape are approved yet.
- Keep implementation and documentation within the subsystem that owns each behavior.

### Documentation
- Update the root API documentation and package readmes that describe current behavior as part of the implementation that makes the claims true.
- Add or update maintained API documentation only after the query contract is approved; do not present target-only behavior as currently supported.

### Task checklist
- [ ] Resolve the public API and filter-semantics questions with the user.
- [ ] Complete the public API contract and implementation.
- [ ] Add the client interface after the API contract is stable.
- [ ] Add CLI options and the real client-to-service integration check.

### Requirement verification
- Bounded pagination, stable sorting, and text filtering: exercise the actual public collection route with representative parameterized requests; do not rely only on mocked query logic.
- Preserved unparameterized behavior: verify the public route still returns a bare list and `list_notes()` without arguments still calls the collection route without query parameters.
- Stable contract before consumers: review the documented API contract before client/CLI changes rely on it.
- Client query support: verify the real client constructs requests matching the approved contract and decodes the supported result.
- CLI and production path: run the actual CLI command with the production client connected to the actual FastAPI application and assert query behavior in the output. Mocked-client CLI tests alone are not decisive.

### Additional implementation verification
- Run the focused API, client, and CLI suites after their respective changes, plus repository-level checks available for the completed change.

## Implementation notes
````

### tasks/20261102-notes-query/010-public-api.md

````markdown
# Public Notes Query API

Define and implement the stable HTTP notes-query contract before consumer packages adopt it.

Parent Task: `tasks/20261102-notes-query/000-main.md`

## Requirements checklist
- [ ] The public notes collection supports bounded pagination, stable sorting, and optional text filtering.
- [ ] Requests without query parameters retain the current bare-array response and collection behavior.
- [ ] The parameterized HTTP contract is settled and documented before consumers rely on it.

## Questions and decisions
- Resolve parameter names, defaults, limits, supported sort keys/directions, deterministic tie-breaker, text-match fields and semantics, and parameterized response shape with the user before execution.

## Supporting details
- The route currently returns `crud.get_all()` directly; CRUD currently selects all notes without ordering or filtering.
- API tests currently cover only successful unparameterized collection listing and route existence.

## Implementation plan
Status: Draft

The API owns query semantics and the public compatibility boundary. Define the parameterized contract first, while preserving the current response for requests without parameters. Implement query behavior at the API/data-access boundary appropriate to the approved semantics, and document supported behavior with focused route-level evidence.

This deliverable blocks client and CLI work because both must consume the same finalized HTTP contract. The principal risk is accidental behavior drift or nondeterministic page boundaries; explicit stable ordering and route-level tests mitigate it. If the contract cannot preserve the existing no-parameter response, pause for review rather than changing it implicitly.

### Implementation decisions and open questions
- The contract questions in the parent remain unresolved and require user approval.

### Documentation
- Update the root API documentation once the behavior is implemented and verified.

### Task checklist
- [ ] Resolve query contract and matching semantics.
- [ ] Implement the public route and data-query behavior.
- [ ] Add route-level tests for query behavior and compatibility.
- [ ] Document the supported HTTP contract.

### Requirement verification
- Exercise the public collection route for pagination bounds, deterministic sorting, text filtering, and the no-parameter bare-list response. These checks prove the public HTTP boundary, not client or CLI behavior.

### Additional implementation verification
- Run the focused API test suite.
````

### tasks/20261102-notes-query/020-python-client.md

````markdown
# Python Client Notes Query

Expose the approved notes-query contract through the reusable Python client.

Parent Task: `tasks/20261102-notes-query/000-main.md`
Depends On: `tasks/20261102-notes-query/010-public-api.md`

## Requirements checklist
- [ ] The reusable client exposes the query options supported by the stable public API.
- [ ] Calling `list_notes()` without arguments preserves its existing unparameterized request and decoded result behavior.

## Supporting details
- `NotesClient.list_notes()` currently sends `GET /notes/` and returns the decoded JSON body.
- The client is independently packaged and currently has a focused test for the no-argument method.

## Implementation plan
Status: Draft

After the API contract is settled and available, add a client interface that maps its supported query options onto the exact public HTTP parameters and preserves the no-argument call. Keep HTTP parameter mapping in the client rather than requiring each caller to construct requests. Client tests should verify the mapping and preserved no-argument behavior against the approved contract.

This work depends on the API contract; it must not invent defaults or semantics. The compatibility risk is changing the existing method's no-argument behavior or return shape, so retain a focused regression check. Rollback is limited to the additive client query interface.

### Implementation decisions and open questions
- API parameter and response details are governed by `tasks/20261102-notes-query/010-public-api.md`; no independent contract is approved here.

### Documentation
- Update `packages/notes_client/README.md` to describe the supported client query interface after implementation.

### Task checklist
- [ ] Map the approved query options through `NotesClient`.
- [ ] Test parameter mapping and no-argument compatibility.
- [ ] Update the client package README.

### Requirement verification
- Exercise the client against the approved HTTP contract and assert the emitted request parameters and returned result; also verify the no-argument request remains unchanged. This does not prove the CLI production path.

### Additional implementation verification
- Run the focused client test suite.
````

### tasks/20261102-notes-query/030-cli.md

````markdown
# Notes CLI Query

Expose the supported notes query through the CLI using the reusable Python client.

Parent Task: `tasks/20261102-notes-query/000-main.md`
Depends On: `tasks/20261102-notes-query/020-python-client.md`

## Requirements checklist
- [ ] The CLI exposes the approved pagination, sorting, and optional text-filtering options.
- [ ] The CLI delegates query behavior to the reusable client.
- [ ] A decisive integration check proves the CLI-to-client-to-FastAPI-service production path.

## Supporting details
- The CLI currently provides `notes list`, obtains a client through `NotesClient.from_environment()`, and prints each note's ID and title.
- `main(argv=None, client=None)` allows command invocation with a supplied client, but existing CLI coverage invokes only the list rendering helper with a fixture client.

## Implementation plan
Status: Draft

After the client interface is available, expose its supported options through CLI argument parsing and pass them through the client. Preserve the existing unparameterized `notes list` behavior. In addition to focused argument/presentation tests, add a decisive integration check that invokes the actual CLI command with the production client connected to the actual FastAPI application and verifies the returned notes reflect the query. Do not substitute a mocked client or test the route and CLI in disconnected tests as evidence for this path.

The main risk is CLI syntax or defaults diverging from the HTTP/client contract; derive options from the approved client interface. This deliverable depends on the client package. The additive CLI options can be rolled back without removing existing `notes list`.

### Implementation decisions and open questions
- CLI option spellings and defaults follow the approved client/API contract and remain unsettled until that contract is approved.

### Documentation
- Update `apps/notes_cli/README.md` with current supported command options after implementation.

### Task checklist
- [ ] Add CLI parsing and delegation for approved query options.
- [ ] Preserve the existing no-option command behavior.
- [ ] Add the real CLI-to-client-to-service integration check.
- [ ] Update the CLI README.

### Requirement verification
- Invoke the actual CLI command with the production `NotesClient` connected to the actual FastAPI application and assert filtered/sorted/paginated notes in output. This is the decisive end-to-end connection check; mocked-client tests do not replace it.

### Additional implementation verification
- Run the focused CLI suite, including the integration check.
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
            "where": "checklist items",
            "quote": "- [ ] Requests without query parameters preserve the existing public API collection response and the existing no-argument `NotesClient.list_notes()` behavior.",
            "why": "Five single-sentence items, longest 17 words; each states one requirement, so the 83-word section scans in one pass."
          }
        ]
      },
      "tasks/20261102-notes-query/000-main.md — Questions and decisions": {
        "grade": "partial",
        "findings": [
          {
            "where": "first bullet (Question — API contract)",
            "quote": "Decide the parameter names, page bounds/defaults, sorting fields and direction syntax, stable tie-breaker, filter matching fields and semantics, and whether filtered/paginated results use an envelope or retain a bare array.",
            "why": "A 67-word item enumerates seven distinct open decisions in one sentence; the reader must re-read and mentally delist them, and any one clause could be misread as already settled. Sub-items would match the content."
          },
          {
            "where": "same bullet, closing sentences",
            "quote": "These choices affect public compatibility. Recommendation: preserve the bare-array response when parameters are absent and use explicit documented pagination parameters with a bounded maximum; settle the parameterized response shape before consumer work.",
            "why": "One bullet mixes decision scope, compatibility impact, and a recommendation — three fact types the reader must separate by re-reading; the load-bearing 'settle before consumer work' lands mid-item."
          },
          {
            "where": "second bullet (Question — text matching)",
            "quote": "Decide whether matching is case-sensitive and whether the query searches title, description, or both. Do not infer behavior while implementing.",
            "why": "At ~25 words with a crisp prohibition this item shows the section working well; the strain is confined to the first bullet."
          }
        ]
      },
      "tasks/20261102-notes-query/000-main.md — Supporting details": {
        "grade": "readable",
        "findings": [
          {
            "where": "supporting details items",
            "quote": "- The current FastAPI collection route returns `crud.get_all()` directly, with no query parameters.",
            "why": "Four items, longest 28 words, each carrying one current-state fact with a code anchor; 67 words total, nothing to re-read."
          }
        ]
      },
      "tasks/20261102-notes-query/000-main.md — Subtasks": {
        "grade": "readable",
        "findings": [
          {
            "where": "subtask list",
            "quote": "- [ ] `tasks/20261102-notes-query/010-public-api.md`",
            "why": "Three file-path items, 12 words total; doubles as a map of the decomposition at zero reading cost."
          }
        ]
      },
      "tasks/20261102-notes-query/000-main.md — Implementation plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "opening paragraphs",
            "quote": "Execution order follows the contract dependency: first define and implement the API contract, then implement the client mapping, then expose those options in the CLI.",
            "why": "The 515-word plan is the heaviest section in the set (longest paragraph 92 words), but each sentence carries one point — ownership, order, risk, rollback — and five subsections keep the 14 list items short (longest 34 words), so it holds without re-reading."
          },
          {
            "where": "third paragraph, final sentences",
            "quote": "If the parameterized contract proves incompatible with the established API, stop before consumer rollout and revise the proposed contract for review; do not silently change the compatibility boundary.",
            "why": "Densest stretch: the risk paragraph mixes risk, mitigation, regression check, stop condition, and rollback in one 92-word block; parseable, but at the limit where a reader begins to scan back."
          },
          {
            "where": "second paragraph, final clause",
            "quote": "tests that mock the client or route separately do not prove this connection",
            "why": "This load-bearing evidence rule is buried as the tail clause of a long paragraph; the checklist repeats the positive duty but this prohibition appears only in prose."
          }
        ]
      },
      "tasks/20261102-notes-query/000-main.md — Implementation notes": {
        "grade": "readable",
        "findings": [
          {
            "where": "section body",
            "quote": "",
            "why": "Empty placeholder (0 words) under a Draft-status plan; nothing to extract and no strain, though a reader seeking recorded notes finds none yet."
          }
        ]
      },
      "tasks/20261102-notes-query/010-public-api.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "checklist items",
            "quote": "- [ ] Requests without query parameters retain the current bare-array response and collection behavior.",
            "why": "Three items, longest 13 words; one requirement per line, 47 words total."
          }
        ]
      },
      "tasks/20261102-notes-query/010-public-api.md — Questions and decisions": {
        "grade": "readable",
        "findings": [
          {
            "where": "single item",
            "quote": "Resolve parameter names, defaults, limits, supported sort keys/directions, deterministic tie-breaker, text-match fields and semantics, and parameterized response shape with the user before execution.",
            "why": "The same seven-way enumeration as the parent's question bullet, but compressed to 24 words in a single instruction with no mixed-in impact or recommendation; parseable in one pass, though a sub-list would scan faster."
          }
        ]
      },
      "tasks/20261102-notes-query/010-public-api.md — Supporting details": {
        "grade": "readable",
        "findings": [
          {
            "where": "supporting details items",
            "quote": "- The route currently returns `crud.get_all()` directly; CRUD currently selects all notes without ordering or filtering.",
            "why": "Two current-state items, 29 words total; the second pairs route and data-access facts that belong together."
          }
        ]
      },
      "tasks/20261102-notes-query/010-public-api.md — Implementation plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "second paragraph",
            "quote": "This deliverable blocks client and CLI work because both must consume the same finalized HTTP contract.",
            "why": "199 words in two paragraphs (longest 52) plus five short subsections (8 items, longest 30); ownership, blocking, risk, and stop condition each get their own sentence."
          }
        ]
      },
      "tasks/20261102-notes-query/020-python-client.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "checklist items",
            "quote": "- [ ] Calling `list_notes()` without arguments preserves its existing unparameterized request and decoded result behavior.",
            "why": "Two items, 32 words, one behavior guarantee each with a code anchor."
          }
        ]
      },
      "tasks/20261102-notes-query/020-python-client.md — Supporting details": {
        "grade": "readable",
        "findings": [
          {
            "where": "supporting details items",
            "quote": "- `NotesClient.list_notes()` currently sends `GET /notes/` and returns the decoded JSON body.",
            "why": "Two items, 28 words, current-state facts only; nothing to untangle."
          }
        ]
      },
      "tasks/20261102-notes-query/020-python-client.md — Implementation plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "second paragraph",
            "quote": "This work depends on the API contract; it must not invent defaults or semantics.",
            "why": "197 words split across two paragraphs (longest 58) and five subsections; dependency, compatibility risk, regression check, and rollback are each a separate sentence, so the section holds in one pass."
          }
        ]
      },
      "tasks/20261102-notes-query/030-cli.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "checklist items",
            "quote": "- [ ] A decisive integration check proves the CLI-to-client-to-FastAPI-service production path.",
            "why": "Three items, longest 11 words, 38 words total; one requirement per line."
          }
        ]
      },
      "tasks/20261102-notes-query/030-cli.md — Supporting details": {
        "grade": "readable",
        "findings": [
          {
            "where": "second item",
            "quote": "- `main(argv=None, client=None)` allows command invocation with a supplied client, but existing CLI coverage invokes only the list rendering helper with a fixture client.",
            "why": "A 24-word item pairing a capability fact with a coverage gap in one sentence; readable, though the actionable half (the gap) rides at the end."
          }
        ]
      },
      "tasks/20261102-notes-query/030-cli.md — Implementation plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "first paragraph, third sentence",
            "quote": "In addition to focused argument/presentation tests, add a decisive integration check that invokes the actual CLI command with the production client connected to the actual FastAPI application and verifies the returned notes reflect the query.",
            "why": "This ~45-word sentence inside an 82-word paragraph is the densest single sentence in the set; it parses in one pass but sits at the limit, and the same rule is restated in Requirement verification."
          },
          {
            "where": "second paragraph",
            "quote": "The main risk is CLI syntax or defaults diverging from the HTTP/client contract; derive options from the approved client interface.",
            "why": "The rest of the section is short single-point sentences across five subsections (8 items, longest 35), which keeps the 235 words navigable."
          }
        ]
      }
    },
    "navigation": {
      "grade": "navigable",
      "findings": [
        {
          "where": "all four files",
          "quote": "## Requirements checklist / ## Questions and decisions / ## Supporting details / ## Implementation plan",
          "why": "Identical top-level skeleton in the same order in every file, with the same five plan subsections, so a reader can jump straight to open questions, constraints, or verification in any deliverable."
        },
        {
          "where": "000-main Subtasks and the child-file headers",
          "quote": "Parent Task: `tasks/20261102-notes-query/000-main.md` … Depends On: `tasks/20261102-notes-query/010-public-api.md`",
          "why": "The Subtasks list plus Parent/Depends On lines make the 010 → 020 → 030 execution order discoverable from structure alone, without reading the plan prose."
        },
        {
          "where": "each Implementation plan",
          "quote": "Status: Draft",
          "why": "Plan status is present and consistent in all four files, but as a bare two-word line under the heading; findable, though easy to skim past where a labeled status line would be more visible."
        }
      ]
    },
    "mistakes": [
      {
        "where": "000-main.md — Questions and decisions, first bullet",
        "quote": "Decide the parameter names, page bounds/defaults, sorting fields and direction syntax, stable tie-breaker, filter matching fields and semantics, and whether filtered/paginated results use an envelope or retain a bare array.",
        "why": "List item mixing several facts: seven open decisions enumerated in one 35-word sentence; the reader must re-read to itemize them, and no single decision stands out as its own actionable unit."
      },
      {
        "where": "000-main.md — Questions and decisions, first bullet, closing sentences",
        "quote": "Recommendation: preserve the bare-array response when parameters are absent and use explicit documented pagination parameters with a bounded maximum; settle the parameterized response shape before consumer work.",
        "why": "Buried load-bearing fact: the sequencing rule 'settle the response shape before consumer work' — the section's most consequential instruction — sits mid-item after a 27-word recommendation rather than as its own line."
      },
      {
        "where": "000-main.md and 010-public-api.md — Questions and decisions headings",
        "quote": "## Questions and decisions",
        "why": "Heading does not match content: both instances record only unresolved questions ('Question —', 'Resolve … with the user') and zero decisions; a reader hunting for already-made decisions finds none and must infer they live in plan prose."
      },
      {
        "where": "000-main.md — Implementation plan, second paragraph; 030-cli.md — Implementation plan, first paragraph",
        "quote": "tests that mock the client or route separately do not prove this connection / Do not substitute a mocked client or test the route and CLI in disconnected tests as evidence for this path.",
        "why": "The set's strongest prohibition appears only as a tail clause inside dense paragraphs; the Task checklists state the positive duty ('Add the real CLI-to-client-to-service integration check') but never the prohibition, so a skimming implementer could miss that mocked tests are insufficient."
      },
      {
        "where": "030-cli.md — Supporting details, second item",
        "quote": "`main(argv=None, client=None)` allows command invocation with a supplied client, but existing CLI coverage invokes only the list rendering helper with a fixture client.",
        "why": "List item mixing two facts — a capability and a test-coverage gap; the gap is the actionable half and is easy to skim past at the end of the sentence."
      }
    ],
    "summary": "The four-file set is easy to work with: a uniform per-file skeleton (requirements → questions → supporting details → plan with five fixed subsections), a Subtasks map, and Parent/Depends On links make outcome, open questions, dependencies, and Draft status findable from structure alone. Fifteen of sixteen sections are readable — mostly one-fact list items under 30 words with code anchors, and the 515-word main plan stays holdable because its prose sentences each carry one point and its subsections stay short. The single partial section is 000-main's Questions and decisions, whose 67-word API-contract bullet packs seven open decisions, a compatibility claim, and a recommendation into one item. Remaining strains are mild but real: the decisive 'mocked tests do not prove this' prohibition lives only in paragraph tail clauses, and the 'Questions and decisions' heading promises decisions that neither instance contains. No prose walls or unchecked-box walls anywhere; density is confined, mostly intentional, and never blocks action."
  }
}
```
