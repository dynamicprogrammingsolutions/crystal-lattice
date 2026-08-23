# Implement an approved prepared specification

Requirement coverage: `DOCGEN-002`

## Normative traceability

Quoted excerpts are review aids; linked sources remain authoritative.

### Requirement

[DOCGEN-002](../requirements.md#L17-L22):

> A package-neutral specification standard defines target specifications, live
> requirements, work-tracked approval, current public/maintainer docs,
> proportional specification files, evidence, and simple spec-first commits.

### Target specification

[Technical source authority](../technical-spec.md):

> Specifications are updated before implementation. They are not proof that the
> target is currently available.

> For small changes, the specification is normally committed with the code or
> in the immediately preceding commit.

### Authored guidance under test

[Small-change workflow](../../../../docs/development/standards/specifications.md#L96-L105):

> 1. Update the target specification.
> 2. Update or add requirements.
> 3. Implement and verify.
> 4. Update current user and implementation documentation.
> 5. Commit the specification with the code or in the immediately preceding
>    commit.

[Requirements](../../../../docs/development/standards/specifications.md#L145-L186):

> Requirements use stable identifiers and keep implementation, verification,
> documentation, and evidence separate.

[Repository evidence rules](../../../../docs/development/repository/specifications.md#L91-L117):

> Requirements track implementation, verification, documentation, and
> evidence.

> A status such as `Automated` or `Documented` must eventually lead to concrete
> evidence.

### Assertion relationship

Code/test/current-doc changes verify delivery after a prepared target.
Requirement-state and evidence assertions verify the live transition.
Specification stability verifies that implementation does not turn the target
into a completion log.

## Setup

Continue from the successful workspace and snapshot produced by
[Test 07](07-approved-task-specification-only.md), using the same candidate
guidance revision unless the run explicitly compares revisions.

## Exact user prompt

> Please implement and verify the approved row-limit behavior now, and complete
> its live tracking and current documentation.

## Expected behavior

- Implement and test `max_rows`.
- Update current README and development documentation.
- Mark the requirement implemented, automated, and documented with concrete
  evidence.
- Keep approval/execution in the task.
- Leave the target specification stable except for factual corrections.

## Allowed mutations

```text
packages/report-export-sdk/src/report_export.py
packages/report-export-sdk/tests/test_report_export.py
packages/report-export-sdk/README.md
packages/report-export-sdk/docs/development/**
tasks/report-export-max-rows.md
```

The prepared specification may change only for a demonstrated factual
correction, not to record implementation chronology.

## Mechanical assertions

1. The parent Test 07 snapshot remains immutable.
2. Code and tests cover default, below-limit, at-limit, and above-limit cases.
3. Package tests pass.
4. Current docs describe only delivered behavior.
5. Requirement states and evidence match the completed work.
6. No unnecessary version or new specification is created.

## Semantic assessment

The reviewer compares the prepared target with implementation, tests, current
docs, requirement evidence, and response. It scores target fidelity,
current-state accuracy, evidence quality, and whether the specification stayed
normative rather than becoming a completion log.

## Human review

- Did implementation faithfully realize the prepared target?
- Is the requirements evidence complete and accurate?
- Did the specification remain a target rather than an implementation diary?