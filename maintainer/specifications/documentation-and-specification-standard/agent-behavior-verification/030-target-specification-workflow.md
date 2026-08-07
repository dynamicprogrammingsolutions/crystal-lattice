# Target specification workflow

Requirement coverage: `DOCGEN-002`

## Behavior under test

For approved implementation work with an existing specification, an agent
should:

- update the target specification before implementation;
- implement and test the change;
- update live requirements independently across implementation,
  verification, documentation, and evidence;
- keep approval and execution in the work-tracking artifact;
- update user and implementation documentation to current behavior;
- avoid treating the specification as proof that implementation exists;
- keep an ordinary small spec-first change in the same commit-sized work
  rather than inventing version machinery.

## Repository setup

Use the common neutral seed and candidate guidance overlay.

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
- proportionality of artifacts;
- compatibility and failure-behavior clarity;
- evidence quality.

## Human review

The human presentation asks:

- Does the specification remain a target rather than an implementation log?
- Are requirement statuses justified by concrete evidence?
- Do current docs match the delivered code?
- Was the existing task used as the approval/execution record?
- Was the simple change kept simple?