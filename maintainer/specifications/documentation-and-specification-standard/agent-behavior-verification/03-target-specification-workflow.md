# Target specification workflow

Requirement coverage: `DOCGEN-002`

## Normative traceability

Quoted sentences are review aids; linked sources remain authoritative.

### Requirement

[DOCGEN-002](../requirements.md#L17-L22):

> A package-neutral specification standard defines target specifications, live
> requirements, work-tracked approval, current public/maintainer docs,
> proportional specification files, evidence, and simple spec-first commits.

### Target specification

[Product specification and current state](../product-spec.md#L50-L62):

> Specifications describe intended targets and may temporarily differ from
> implementation. Requirements track the live implementation, verification,
> documentation, and evidence state.

> Task files are the default approval and execution record. Public user
> documentation and implementation/maintainer documentation describe current
> behavior and must remain consistent with committed code.

> Simple specification changes are normally committed with their
> implementation or in the immediately preceding commit.

[Small-change acceptance example](../product-spec.md#L110-L114):

> An agent updates a target specification, requirements, implementation, tests,
> and current documentation. The spec and code are committed together or in
> two adjacent commits, while requirements show the live transition.

[Technical source authority](../technical-spec.md):

> | Specification | Intended target behavior and design |
> | Requirements | Live implementation, verification, documentation, and
> evidence state |
> | Task | Approval, execution scope, plan, findings, and completion |

> Specifications are updated before implementation. They are not proof that
> the target is currently available.

### Authored guidance under test

[Four sources of truth](../../../../docs/development/standards/specifications.md):

> Specification: intended target behavior and design.

> Requirements: live implementation, verification, documentation, and evidence
> state.

> Work item: approval, execution scope, plan, findings, and completion.

> A specification is not evidence that its target currently exists.

[Proportional specification files](../../../../docs/development/standards/specifications.md):

> The set is proportional.

> Requirements normalize target outcomes and track live state.

> Do not create empty files merely to complete the shape.

[Specification as target](../../../../docs/development/standards/specifications.md#L91-L117):

> Update the specification before implementation. It may intentionally differ
> from current code while work is in progress.

> 1. Update the target specification.
> 2. Update or add requirements.
> 3. Implement and verify.
> 4. Update current user and implementation documentation.
> 5. Commit the specification with the code or in the immediately preceding
>    commit.

[Approval and requirements](../../../../docs/development/standards/specifications.md#L126-L152):

> The repository's work item records approval by default.
> Specifications do not require a mandatory approval or implementation status.

> Requirements use stable identifiers and keep implementation, verification,
> documentation, and evidence separate.

[Relationship to work tracking](../../../../docs/development/standards/specifications.md#L192-L202):

> Specifications own target behavior and design. Requirements own live state
> and evidence. Work items own approval, execution plans, dependencies,
> findings, and completion.

[Current documentation](../../../../docs/development/standards/specifications.md#L235-L242):

> Public user documentation and implementation/maintainer documentation
> describe current behavior.

> Draft, deferred, or target-only behavior belongs in specifications and
> requirements, not in current guides.

[Crystal Lattice source mapping](../../../../docs/development/repository/specifications.md):

> Approval and execution: `tasks/` task and execution plan.

> Specifications are targets. Requirements track what is implemented,
> verified, and documented. Public and implementation documentation describe
> current committed behavior.

[Crystal Lattice workflow](../../../../docs/development/repository/specifications.md#L119-L144):

> Update the specification first. Implement, test, and update requirements and
> current docs. Commit the spec with the implementation or in the immediately
> preceding commit.

[Root agent guidance](../../../../AGENTS.md#L135-L146):

> Specifications describe intended targets and may temporarily differ from
> implementation. Requirements track live implementation, verification,
> documentation, and evidence. Task files track approval and execution.

> Use stable requirement IDs for important acceptance behavior and record
> concrete implementation, verification, documentation, task, and delivery
> evidence.

### Assertion relationship

Mutation order verifies spec-first work. Final files and tests verify
implementation and current documentation. Requirement-column assertions verify
live state and evidence. The existing task verifies the approval owner. The
absence of a new version/change spec verifies proportional, simple delivery.

## Behavior under test

For approved implementation work with an existing specification, an agent
should:

- update the target specification before implementation;
- implement and test the change;
- update live requirements independently across implementation,
  verification, documentation, and evidence;
- keep approval and execution in the work item;
- update user and implementation documentation to current behavior;
- avoid treating the specification as proof that implementation exists;
- keep an ordinary small spec-first change in the same commit-sized work
  rather than inventing version machinery.

## Repository setup

Continue from
[Seed 02: report-export row-limit investigation](seed-02-report-export-row-limit.md)
and apply the candidate guidance overlay defined by
[the verification index](index.md#candidate-guidance-overlay).

A test-owned package fixture provides:

```text
packages/report-export-sdk/
├── README.md
├── src/report_export.py
├── tests/test_report_export.py
└── docs/development/
    ├── index.md
    └── specifications/export-limits/
        ├── index.md
        ├── product-spec.md
        ├── technical-spec.md
        └── requirements.md

tasks/report-export-max-rows.md
```

The approved task requires an optional `max_rows` limit with a default of
1,000. The target specification does not yet contain the behavior, the
requirements ledger has no corresponding requirement, and implementation/docs
reflect the old unlimited behavior.

The fixture package is intentionally small and deterministic so technical
implementation does not dominate the guidance evaluation.

## Exact user prompt

> Please implement the approved report-export row limit described in
> `tasks/report-export-max-rows.md`.

The task file contains the feature acceptance requirements. The prompt does not
describe the specification workflow.

## Expected behavior

The agent should:

1. Read the task, owning package entry points, existing specification, and
   requirements.
2. Update the target specification and add a stable requirement ID.
3. Implement the limit and regression tests.
4. Update package user and development documentation to describe the now
   implemented behavior.
5. Mark implementation, automated verification, and documentation accurately
   in the requirements ledger with concrete evidence.
6. Keep approval/execution notes in the task rather than adding mandatory
   approval status to the specification.

## Allowed mutations

Allowed paths are limited to:

```text
packages/report-export-sdk/README.md
packages/report-export-sdk/src/report_export.py
packages/report-export-sdk/tests/test_report_export.py
packages/report-export-sdk/docs/development/index.md
packages/report-export-sdk/docs/development/specifications/export-limits/**
tasks/report-export-max-rows.md
```

No separate specification version, change specification, or unrelated package
documentation is expected.

## Mechanical assertions

The scenario verifies:

1. The first specification mutation precedes the first implementation
   mutation in tool telemetry.
2. The target specification defines `max_rows`, the default, rejection
   behavior, and compatibility.
3. A stable requirement ID tracks the new behavior.
4. The requirement row separately records implementation, verification,
   documentation, and evidence.
5. Evidence links the implementation, test, current docs, active task, and
   delivered change.
6. Tests cover default, below-limit, at-limit, and above-limit behavior.
7. Package tests pass.
8. README/current development docs describe current implemented behavior.
9. The specification does not claim that its text proves implementation.
10. Approval remains represented by the existing task.
11. No unnecessary target version or second specification is created.
12. The final response accurately summarizes spec, code, tests, docs, and
    requirement-state changes.

## Semantic assessment

The reviewer receives the task, original and final specification/requirements,
primary code/test/doc diffs, mechanical findings, and response.

It scores:

- target versus current-state separation;
- requirement-ledger accuracy;
- specification-first sequencing;
- proportionality of specification files;
- compatibility and failure-behavior clarity;
- evidence quality.

## Human review

The human presentation asks:

- Does the specification remain a target rather than an implementation log?
- Are requirement statuses justified by concrete evidence?
- Do current docs match the delivered code?
- Was the existing task used as the approval/execution record?
- Was the simple change kept simple?