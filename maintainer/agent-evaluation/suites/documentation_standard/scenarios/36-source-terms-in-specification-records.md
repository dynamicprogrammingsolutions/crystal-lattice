# Test 36: source terms in specification records

Requirement coverage: `DOCGUIDE-008`, `DOCAGENT-002`, `DOCVAL-015`,
`DSEVAL-004`

## Purpose

Verify how an agent names a task-authorized specification and its records when
the request also supplies wording that does not name the established
capability.

## Normative traceability

[DOCGUIDE-008 and DOCAGENT-002](../../../../docs/development/specifications/documentation-guidance/requirements.md)
require maintained records and portable guidance to preserve behavior without
adopting source-local labels as destination terminology.

[DOCVAL-015](../../../../docs/development/specifications/crystal-lattice-guidance-integration/requirements.md)
requires current/candidate comparison through the production runner.

[DSEVAL-004](../docs/development/requirements.md) requires exact candidate,
compilation, delivery, and producer provenance.

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

- The task may retain the source wording because it defines what the wording
  refers to.
- The specification directory, filenames, titles, requirements, and decisions
  use offline-synchronization concepts.
- A descriptive task reference is not followed by the local number, sequence
  label, or evaluative nickname.
- Requirement and decision references are complete and descriptive.
- Transport and persistence contracts are linked rather than copied.
- Requirements begin not implemented and unverified.
- Source code and current user documentation do not change.

## Allowed mutations

```text
tasks/batch-offline-sync.md
packages/batch-sdk/docs/development/index.md
packages/batch-sdk/docs/development/specifications/**
```

## Deterministic assertions

1. The selected source wording remains in the task with offline-synchronization
   context.
2. A package-owned offline-synchronization specification is created.
3. Specification paths, headings, requirements, decisions, and references do
   not adopt the selected source wording as a durable capability name.
4. Requirements remain target-only, not implemented, and unverified.
5. One `decisions.md` file is used as explicitly approved.
6. The development index links the capability.
7. No implementation or user-documentation file changes.
8. Production-runner preflight and candidate compilation provenance are valid.

## Semantic assessment

Review whether each task, specification, requirement, decision, filename,
heading, and reference uses a term established or explained for that
destination. Distinguish a task preserving defined shorthand from another
record adopting it as a capability name.

## Human review

- Which source terms, if any, became unexplained durable names?
- Are task, requirement, and decision references understandable without the
  conversation?
- Did the agent preserve the approved capability and avoid implementation?
- Did the complete guide need to be read, and was that read observed?