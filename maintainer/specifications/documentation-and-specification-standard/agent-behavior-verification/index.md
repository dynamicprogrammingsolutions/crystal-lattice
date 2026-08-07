# Agent-behavior verification

## Purpose

These tests verify that supported agents understand and apply the authored
documentation and specification guidance when performing ordinary repository
work.

They test agents as consumers of the guidance. They do not ask an agent to
write, summarize, or restate the standard being evaluated.

The evaluation pattern follows the validated task-guidance tests:

1. Prepare a realistic repository state.
2. Deliver the exact candidate `AGENTS.md` files and routed documentation
   through the normal agent instruction and filesystem mechanisms.
3. Give the agent a short task resembling a human request.
4. Let the agent inspect and modify the repository normally.
5. Assert on changed files, file contents, tool behavior, provenance, and the
   final response.
6. Prepare separate semantic-assessment and human-review artifacts.

User prompts do not repeat the rules under test. If a prompt explains where
documentation belongs or which artifacts to create, the evaluation cannot show
that the authored guidance caused that behavior.

## Static and behavioral verification

Some requirements combine properties of the authored standard with behavior
expected from agents.

Static verification checks the authored files directly, including:

- package-neutral pages contain no Crystal Lattice paths or package names;
- required sections and links exist;
- generic and repository-specific rules remain in their proper owners;
- generated output is not an authored source.

Behavioral verification checks whether an agent applies those rules to a real
task. A model is not asked to generate package-neutral guidance merely to prove
that the guidance itself is package-neutral.

## Traceability convention

Each test page shows:

```text
requirement
  -> target meta-specification
    -> authored guidance artifact
      -> behavioral assertion
```

Links use source line ranges for quick review. Relevant source sentences are
also copied beside the links so a reviewer can understand the test without
opening every file. Those excerpts are non-normative review aids; the linked
source remains authoritative and must be consulted when wording changes.
Changes to a linked requirement, specification, or guidance passage must update
the affected line range, copied excerpt, and behavioral assertion in the same
work.

Seed pages use the `seed-<number>-<name>.md` convention. Test pages use
two-digit numbers such as `01-<name>.md`. These names distinguish reusable
conversation/setup state from behavioral assertions without adopting the
three-digit task-file convention.

## Common setup

### Scenario-family seeds

A seed is a narrow, concrete factual investigation for a family of closely
related branch tasks. It is not a general repository survey.

The seed should:

- name the package, issue, task, or contract being investigated;
- ask only for facts needed by its branch tasks;
- be simple enough for the inexpensive subject model to complete quickly;
- avoid ownership, artifact, workflow, or approval decisions controlled by the
  candidate guidance;
- perform no mutations;
- omit candidate guidance;
- support multiple clean continuation prompts with small behavioral
  differences;
- remain reusable while candidate guidance revisions or delivery mechanisms
  change.

Current seeds:

| Seed | Narrow investigation | Current branches |
|---|---|---|
| [Seed 01](seed-01-js-single-file-tool-documentation.md) | Compare one plugin README with its code and shared Node-tool facts | Tests [01](01-small-package-documentation.md) and [02](02-generated-output-correction.md) |
| [Seed 02](seed-02-report-export-row-limit.md) | Inspect one approved row-limit task and its current spec/code/test/doc state | Test [03](03-target-specification-workflow.md) |
| [Seed 03](seed-03-mobile-composer-refinement.md) | Inspect one portable contract, mobile package, and approved UX task | Test [04](04-package-owned-refinement.md) |
| [Seed 04](seed-04-event-retry-documentation.md) | Compare implemented retry, target-only replay, user docs, and link paths | Test [05](05-normative-owner-and-discoverability.md) |
| [Seed 05](seed-05-batch-sync-design.md) | Inspect one package and related persistence/transport contracts | Test [06](06-substantial-specification-approval.md) |

Each seed page owns its exact fixture, prompt, request profile, assertions,
cache identity, provenance, and current/planned branches.

### Candidate guidance overlay

Before a scenario request begins, its clean continuation workspace receives
the exact current candidate guidance needed by the normal routing chain:

```text
AGENTS.md
docs/development/index.md
docs/development/standards/index.md
docs/development/standards/documentation.md
docs/development/standards/specifications.md
docs/development/repository/index.md
docs/development/repository/documentation.md
docs/development/repository/specifications.md
```

Package- or shared-domain scenarios additionally receive the exact applicable
nearest `AGENTS.md`, such as:

```text
plugins/AGENTS.md
plugins/docs/AGENTS.md
```

The setup records path, content hash, and overlay source for every candidate
file. The request artifacts must prove that the intended `AGENTS.md` revision
was delivered and that routed pages were available. The user prompt contains
only the ordinary task.

Candidate guidance hashes are branch fingerprints, not seed-cache
fingerprints. This allows one factual investigation to be reused when comparing
guidance revisions, AGENTS compilation, configuration injection, plugins, or
skills.

Maintainer meta-specifications are not supplied for ordinary application of the
rules. They are relevant only to work maintaining the standards.

### Execution controls

Each scenario defines:

- allowed mutation paths;
- mutation-call budget;
- request/tool-loop limits;
- whether code changes are permitted;
- objective assertions;
- semantic-assessment input;
- human-review presentation.

Read-only repository investigation is not constrained beyond ordinary request
limits. Unexpected writes fail the scenario.

### Evidence separation

Deterministic assertions operate on repository state and explicit provenance.

An optional assessment model receives only a scenario-owned projection:

- requirement IDs;
- exact task prompt;
- candidate guidance hashes;
- relevant original and generated files;
- changed paths;
- mechanical assertion results;
- final assistant response.

It does not receive the complete event stream or unrelated repository context.

Human review receives a separate compact presentation with focused questions.
AI assessment is supporting evidence and does not satisfy human verification.

## DOCGEN test summary

| Test | Seed | Ordinary branch task | Primary coverage |
|---|---|---|---|
| [Small-package documentation](01-small-package-documentation.md) | Seed 01 | Implement the identified plugin-documentation improvements | `DOCGEN-001`: profiles, artifact roles, ownership, source of truth, incremental adoption |
| [Generated-output correction](02-generated-output-correction.md) | Seed 01 | Fix a reported typo in a branch-specific prepared page | `DOCGEN-001`: authored/generated boundary |
| [Target specification workflow](03-target-specification-workflow.md) | Seed 02 | Implement an approved small capability | `DOCGEN-002` |
| [Package-owned refinement](04-package-owned-refinement.md) | Seed 03 | Complete approved mobile-only specification work | `DOCGEN-003` |
| [Normative owner and discoverability](05-normative-owner-and-discoverability.md) | Seed 04 | Make implemented retry behavior easy for users to find | `DOCGEN-004` |
| [Substantial specification approval](06-substantial-specification-approval.md) | Seed 05 | Design a substantial protocol without prior authorization | `DOCGEN-005` |

`DOCGEN-001` intentionally has two behavioral tests because a proportional
small-package profile and the generated-output boundary are independent
behaviors.

## Cross-test invariants

Every implemented test must verify:

- its narrow parent seed had no candidate guidance and no mutations;
- the continuation used a fresh workspace;
- parent snapshot and artifacts were not modified;
- exact candidate guidance hashes were recorded;
- the final prompt equals the scenario specification;
- changed paths stay within the scenario allowlist;
- generated files and responses are retained in canonical artifacts;
- skipped gated tests are reported as not run;
- human verification remains pending until explicitly confirmed.

## Implementation ownership

This specification owns expected standard-consumer behavior. The
[agent evaluation framework specification](../../agent-evaluation-framework/index.md)
owns execution, caching, evidence, and artifact mechanics.

The implemented pytest suite belongs under `maintainer/agent-evaluation/`.
Package documentation explains how to run and inspect it without duplicating
the scenario contracts defined here.