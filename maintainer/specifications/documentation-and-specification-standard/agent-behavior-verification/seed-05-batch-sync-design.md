# Seed 05: batch synchronization design investigation

## Purpose

This seed investigates one package and its related transport/persistence
contracts before a user asks for a substantial new design. It keeps factual
repository research reusable across approval and authorization variants.

## Repository setup

The fixture package exists:

```text
packages/batch-sdk/
├── README.md
├── src/
└── docs/development/index.md
```

Related transport and persistence contracts exist elsewhere. No offline-first
synchronization specification or active authorizing task exists.

## Exact seed prompt

> Please investigate `packages/batch-sdk` and the existing transport and
> persistence contracts relevant to offline synchronization. Read only
> `packages/batch-sdk/README.md`, `packages/batch-sdk/src/batch.py`,
> `packages/batch-sdk/docs/development/index.md`,
> `packages/transport-contract/docs/development/specifications/transport/index.md`,
> and
> `packages/persistence-contract/docs/development/specifications/persistence/index.md`.
> Report current behavior, existing persisted-state and compatibility
> constraints, and the missing offline behavior. Do not modify files and do
> not propose a specification, owner, or file set.

The seed performs the expensive contract search but leaves specification
justification, ownership, file layout, and approval behavior to child
branches.

## Seed assertions

1. No mutation occurs.
2. Current batch behavior and related contracts are identified.
3. Existing persistence/compatibility constraints are reported accurately.
4. Missing offline behavior is described as a factual gap.
5. No specification owner, location, file set, or approval recommendation
   is proposed.
6. Candidate guidance is absent and snapshot/cache provenance is complete.

## Current branches

- [Substantial specification approval](06-substantial-specification-approval.md):
  request the design without prior authorization, then approve it in a second
  turn.
- [Task-authorized new specification](09-task-authorized-new-specification.md):
  add an approved task in the child workspace and create the specification
  without requesting duplicate approval.
- [Explicit specification layout override](21-explicit-specification-layout-override.md):
  follow an approved single-file decisions layout instead of treating the
  default decisions directory as mandatory.

Future branches may request a small local behavior that should remain task-only
or ask for a package refinement of an existing portable synchronization
contract.