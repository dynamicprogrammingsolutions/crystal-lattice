# Test 30: source terms in specification records

Requirement coverage: `DOCGUIDE-007`–`DOCGUIDE-008`, `DOCVAL-011`

## Purpose

Verify how an agent names a task-authorized specification and its records when
the request also supplies wording that does not name the established
capability.

## Setup

Continue from [Seed 05](seed-05-batch-sync-design.md). Each branch adds the same
approved offline-synchronization task and one source-local wording variant.
The capability remains offline synchronization, and implementation remains out
of scope.

### Task-number variant

The task says the conversation refers to the work as `Task 010`.

## Task-number exact user prompt

> Please complete Task 010 from `tasks/batch-offline-sync.md`. Keep the task,
> package development index, specification, requirements, and decisions
> consistent. Do not implement the protocol.

### Sequence-label variant

The task says the conversation refers to the first specification delivery as
`Stage A`.

## Sequence-label exact user prompt

> Please complete Stage A from `tasks/batch-offline-sync.md`. Keep the task,
> package development index, specification, requirements, and decisions
> consistent. Do not implement the protocol.

### Evaluative-wording variant

The task describes the requested specification as a `useful, portable first
version` while retaining the same approved capability and outcomes.

## Evaluative-wording exact user prompt

> Please complete the useful, portable first version approved in
> `tasks/batch-offline-sync.md`. Keep the package development index,
> specification, requirements, and decisions consistent. Do not implement the
> protocol.

## Expected behavior

- The task may retain the source wording because it states what that wording
  refers to.
- The specification directory, filenames, titles, requirements, and decisions
  use offline-synchronization concepts rather than treating the source wording
  as a capability name.
- Task, requirement, and decision references are complete and descriptive.
- Transport and persistence contracts are linked rather than copied.
- Requirements begin not implemented and unverified.
- Source code and current user documentation do not change.

## Allowed mutations

```text
tasks/batch-offline-sync.md
packages/batch-sdk/docs/development/index.md
packages/batch-sdk/docs/development/specifications/**
```

## Initial mechanical observations

The initial baseline records, but does not rely on these checks alone:

1. A package-owned offline-synchronization specification is created.
2. No source implementation changes.
3. Stable pending requirements exist.
4. Specification paths, headings, requirement rows, and decision names are
   collected for source-term inspection.
5. The complete task, specification files, diff, and response are retained.

## Semantic assessment

Review whether every task, specification, requirement, decision, filename,
heading, and reference uses a term that is established or explained for that
destination. Distinguish a task preserving its defined shorthand from another
record adopting that shorthand as a capability name.

## Human review

- Which source terms, if any, became unexplained durable names?
- Did the agent replace one source term with an equally unexplained synonym?
- Are task, requirement, and decision references understandable without the
  conversation?
- Did the agent preserve the approved capability and avoid implementation?
