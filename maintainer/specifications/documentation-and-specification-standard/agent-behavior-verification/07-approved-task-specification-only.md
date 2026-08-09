# Approved task: specification and requirements only

Requirement coverage: `DOCGEN-002`, `DOCVAL-008`

## Normative traceability

Quoted excerpts are review aids; linked sources remain authoritative.

### Requirement

[DOCGEN-002](../requirements.md#L19-L22):

> A package-neutral specification standard defines target specifications, live
> requirements, work-tracked approval, current public/maintainer docs,
> proportional artifacts, evidence, and simple spec-first commits.

[DOCVAL-008](../requirements.md#L80-L80):

> Variants are tried shortest-first and do not pass by weakening the task or
> assertions.

### Target specification

[Product specification and current state](../product-spec.md#L59-L71):

> Specifications describe intended targets and may temporarily differ from
> implementation. Requirements track the live implementation, verification,
> documentation, and evidence state.

[Small-change acceptance example](../product-spec.md#L124-L128):

> An agent updates a target specification, requirements, implementation, tests,
> and current documentation. The spec and code are committed together or in
> two adjacent commits, while requirements show the live transition.

### Authored guidance under test

[Specification as target](../../../../docs/development/standards/specifications.md#L91-L111):

> Update the specification before implementation. It may intentionally differ
> from current code while work is in progress.

> Create the specification and requirements first. Requirements begin as not
> implemented and are updated as code, verification, and current documentation
> are completed.

[Requirements status vocabulary](../../../../docs/development/standards/specifications.md#L145-L192):

> Use `Unverified` when verification has not occurred. Reserve `Pending` for
> documentation that has not yet been written.

[Current documentation](../../../../docs/development/standards/specifications.md#L245-L257):

> Draft, deferred, or target-only behavior belongs in specifications and
> requirements, not in current guides.

[Repository requirement values and workflow](../../../../docs/development/repository/specifications.md#L109-L139):

> Create the approved specification and requirements before implementation.
> Requirements begin `Not started` and are updated as work progresses.

> Before implementation, use `Not started` for implementation, `Unverified`
> for verification, and `Pending` for documentation.

### Assertion relationship

Specification and requirement mutations verify target-first preparation.
Prohibited code, test, README, and current-development-doc changes verify that
target-only behavior is not presented as implemented. Requirement states
verify the live boundary.

## Setup

Continue from
[Seed 02: report-export row-limit investigation](seed-02-report-export-row-limit.md)
with the exact candidate guidance overlay.

## Exact user prompt

> Please update the target specification and requirements for the approved
> row-limit task, but do not implement it.

## Expected behavior

- Update the existing export-limits target.
- Add a stable requirement for `max_rows`.
- Keep implementation `Not started`, verification `Unverified`, and
  documentation `Pending`.
- Link the active task as approval/work evidence.
- Leave code, tests, README, and current implementation docs unchanged.
- Avoid a new version or second specification.

## Allowed mutations

```text
packages/report-export-sdk/docs/development/specifications/export-limits/**
tasks/report-export-max-rows.md
```

No implementation, test, README, or current implementation-page mutation is
allowed.

## Mechanical assertions

1. Only the existing specification, requirements, and necessary spec index/task
   links change.
2. No code, test, README, or current implementation page changes.
3. The target defines default, limit, rejection, and compatibility behavior.
4. The requirement has a stable ID and column-correct pending states:
   implementation `Not started`, verification `Unverified`, documentation
   `Pending`, and no implementation evidence.
5. Approval remains in the existing task.
6. The resulting run preserves a reusable snapshot for Test 08.

## Semantic assessment

The reviewer receives the task, original/final target and requirements,
changed paths, mechanical findings, and response. It scores target completeness,
pending-state accuracy, proportionality, and absence of future claims in
current documentation.

## Human review

- Is the target complete enough for implementation?
- Are all live states honestly pending?
- Did any future claim leak into current documentation?
- Was the existing specification updated proportionally?