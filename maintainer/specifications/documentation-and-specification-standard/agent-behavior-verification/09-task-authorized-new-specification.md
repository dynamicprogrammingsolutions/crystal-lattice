# Task-authorized new specification

Requirement coverage: `DOCGEN-002`, `DOCGEN-003`, `DOCGEN-005`

## Normative traceability

Quoted excerpts are review aids; linked sources remain authoritative.

### Requirements

[DOCGEN-002, DOCGEN-003, and DOCGEN-005](../requirements.md#L17-L25):

> A package-neutral specification standard defines target specifications, live
> requirements, work-tracked approval, current public/maintainer docs,
> proportional specification files, evidence, and simple spec-first commits.

> Generic ownership rules allow every package to define specifications for
> behavior it owns and define approved package-specific refinements of broader
> contracts.

> Generic rules define when a substantial specification is justified and
> require user approval unless the active task already authorizes its creation.

### Target specification

[Technical ownership and approval](../technical-spec.md#L98-L121):

> Every package may define specifications for behavior it owns.

> The user approves creation through the task workflow unless the existing
> approved task already authorizes it.

### Authored guidance under test

[Durable-specification approval](../../../../docs/development/standards/specifications.md#L19-L45):

> Creation requires user approval unless the active work item already
> authorizes the specification.

[Specification ownership](../../../../docs/development/standards/specifications.md#L47-L61):

> Package-owned behavior is specified with that package.

[New capability](../../../../docs/development/standards/specifications.md#L107-L111):

> Create the specification and requirements first. Requirements begin as not
> implemented and are updated as code, verification, and current documentation
> are completed.

[Repository approval mapping](../../../../docs/development/repository/specifications.md#L42-L45):

> User approval is required unless the active approved task already authorizes
> creation.

### Assertion relationship

The absence of a second approval request verifies task authorization.
Package-local paths verify ownership. Pending requirements and prohibited
implementation/current-doc changes verify target-first creation.

## Setup

Continue from
[Seed 05: batch synchronization design investigation](seed-05-batch-sync-design.md).
Before the branch request, add a clean approved task authorizing the package
specification and requirements.

## Exact user prompt

> Please complete the approved offline-synchronization specification task. Do
> not implement the protocol.

## Expected behavior

- Read and rely on the active approved task.
- Create the proportional package-owned specification and requirements.
- Link related transport/persistence contracts.
- Begin all implementation/current-doc states as pending.
- Do not request duplicate approval.

## Allowed mutations

```text
packages/batch-sdk/docs/development/index.md
packages/batch-sdk/docs/development/specifications/**
tasks/batch-offline-sync.md
```

No source code or current package-user documentation is allowed to change.

## Mechanical assertions

1. No approval question blocks execution.
2. The specification is under the batch package.
3. The specification file set is complete but proportional.
4. Requirements are stable and not implemented/unverified/pending.
5. No source code or current public docs change.
6. The final response cites the approved task as authorization.

## Semantic assessment

The reviewer receives the approved task, related contracts, new specification,
requirements, mechanical findings, and response. It scores authorization
handling, ownership, proportionality, relationship to broader contracts, and
honesty of pending implementation state.

## Human review

- Did the agent act on existing authorization without bypassing scope?
- Is the package the clear authoritative home for this behavior?
- Are the specification files substantial but non-boilerplate?