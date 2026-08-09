# Seed 02: report-export row-limit investigation

## Purpose

This seed investigates one approved, small implementation task before candidate
specification guidance is added. It provides concrete code/spec/test/doc facts
for multiple workflow branches without deciding the workflow itself.

## Repository setup

The test-owned clean fixture contains:

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

The approved task requests an optional `max_rows` limit with a default of
1,000. Existing specification, requirements, implementation, tests, and
current docs describe unlimited exports.

The fixture is committed or otherwise fingerprinted as clean before the seed
request.

## Exact seed prompt

> Please investigate the approved row-limit change in
> `tasks/report-export-max-rows.md`. Compare the task with the existing export
> specification, requirements, implementation, tests, README, and development
> documentation. Report the current behavior, the exact files involved, and
> any factual inconsistencies. Do not modify files and do not decide the order
> or documentation workflow for implementing the change.

The seed supplies facts. It does not decide whether to update the
specification first, how requirements should transition, where approval is
tracked, or whether a new target version is needed.

## Request profile

Use the common read-only profile with zero allowed mutations and no candidate
guidance, tasks guidance, skills, MCP, or web context beyond the explicitly
named fixture task.

## Seed assertions

1. No repository mutation occurs.
2. The response identifies the active task and all owning package artifacts.
3. It accurately reports unlimited current behavior.
4. It distinguishes the existing target specification, requirements ledger,
   code/tests, and current docs as facts without assigning an update order.
5. It does not recommend a new specification version or status convention.
6. Candidate guidance is absent and snapshot/cache provenance is complete.

## Current branches

- [Target specification workflow](03-target-specification-workflow.md):
  implement the approved task after adding the candidate guidance.
- [Approved task: specification and requirements only](07-approved-task-specification-only.md):
  prepare the target and pending live state without implementation.
- [Implement an approved prepared specification](08-approved-specification-implementation.md):
  continue from Test 07 and complete implementation, verification, current
  docs, and live evidence.
- [Premature current documentation](15-premature-current-documentation.md):
  ask the agent to publish approved target behavior in the README while
  implementation remains pending.

Future branches may add plan-only variants while reusing this same factual
seed.