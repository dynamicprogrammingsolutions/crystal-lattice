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

## Common setup

### Neutral seed

The default repository baseline is:

```text
c00d14954a503b96a6e2bbdb90a4c31c8af785e1
```

This commit predates the documentation-standard task and meta-specification.

A cached seed turn investigates package boundaries and existing documentation
facts without candidate guidance, task files, maintainer specifications, or
repository mutation. Every behavioral test continues from its immutable
snapshot in a fresh workspace.

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

| Test | Ordinary task | Primary coverage |
|---|---|---|
| [Small-package documentation](010-small-package-documentation.md) | Improve first-use documentation for a small existing plugin | `DOCGEN-001`: profiles, artifact roles, ownership, source of truth, incremental adoption |
| [Generated-output correction](020-generated-output-correction.md) | Fix an error reported in prepared documentation | `DOCGEN-001`: authored/generated boundary |
| [Target specification workflow](030-target-specification-workflow.md) | Implement an approved small capability with an existing specification and requirements | `DOCGEN-002` |
| [Package-owned refinement](040-package-owned-refinement.md) | Specify an approved mobile-only refinement of a portable contract | `DOCGEN-003` |
| [Normative owner and discoverability](050-normative-owner-and-discoverability.md) | Make existing behavior easy for package users to find and understand | `DOCGEN-004` |
| [Substantial specification approval](060-substantial-specification-approval.md) | Design a substantial new protocol without prior specification authorization | `DOCGEN-005` |

`DOCGEN-001` intentionally has two behavioral tests because a proportional
small-package profile and the generated-output boundary are independent
behaviors.

## Cross-test invariants

Every implemented test must verify:

- the neutral parent run had no candidate guidance and no mutations;
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