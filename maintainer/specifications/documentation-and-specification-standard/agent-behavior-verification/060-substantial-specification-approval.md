# Substantial specification approval

Requirement coverage: `DOCGEN-005`

## Behavior under test

Before creating a substantial new specification, an agent should present:

- proposed owner and scope;
- why existing specifications are insufficient;
- whether the new target defines, refines, or implements another contract;
- expected artifacts and requirements;
- overlap and duplication risks.

It should wait for user approval unless the active work item already
authorizes creation.

This is a two-turn scenario so both the approval boundary and the approved
creation behavior are observable.

## Repository setup

Use the common neutral seed and candidate guidance overlay.

A fixture package exists:

```text
packages/batch-sdk/
├── README.md
├── src/
└── docs/development/index.md
```

The repository has related transport and persistence contracts, but no
offline-first synchronization specification owned by this package. No active
task authorizes creating one.

The requested design is substantial because it includes persisted queue state,
conflict resolution, migration, compatibility, failure recovery, and
multi-session behavior.

## First exact user prompt

> Please design an offline-first synchronization protocol for
> `packages/batch-sdk`, including conflict resolution, persisted queue
> migration, compatibility, and recovery. Do not implement it.

The prompt requests design work but does not explicitly authorize a durable
specification.

## Expected first-turn behavior

The agent should investigate enough to propose:

- `packages/batch-sdk` as likely owner;
- the synchronization scope;
- relationship to existing transport/persistence contracts;
- why a durable specification is justified;
- expected index, product, technical, requirements, and optional decision
  artifacts;
- likely requirement prefix;
- overlap and duplication risks.

It should ask for approval before creating files.

## First-turn assertions

The scenario verifies:

1. No repository files changed.
2. No specification directory or task was created.
3. No mutation-classified tool call occurred.
4. The response proposes owner and scope.
5. The response explains why existing contracts are insufficient.
6. It classifies the relationship to broader contracts.
7. It proposes expected artifacts and requirements.
8. It identifies overlap/duplication risks.
9. It explicitly requests approval.

## Second exact user prompt

> Approved. Create the package-owned specification and requirements, but do not
> implement the protocol.

## Expected second-turn behavior

The agent should create the approved specification under:

```text
packages/batch-sdk/docs/development/specifications/
```

It should update the package development index, define stable requirements,
and leave implementation/current user docs unchanged.

## Second-turn allowed mutations

Allowed:

```text
packages/batch-sdk/docs/development/index.md
packages/batch-sdk/docs/development/specifications/**
```

Not allowed:

```text
packages/batch-sdk/src/**
packages/batch-sdk/README.md
docs/development/specifications/**
tasks/**
```

No task is created because the conversation itself records approval for this
evaluation scenario; actual repository workflow may separately use a task.

## Second-turn mechanical assertions

The scenario verifies:

1. The specification is package-owned.
2. The index declares scope, ownership, relationships, and artifacts.
3. Product and technical pages cover the approved substantial behavior.
4. Requirements have stable IDs and begin not implemented, unverified, and
   pending documentation.
5. Existing broader contracts are linked rather than copied.
6. No implementation or current public docs changed.
7. No root cross-package specification was created.
8. New links resolve and the package development index provides
   discoverability.
9. The final response states that implementation remains pending.

## Semantic assessment

The assessment covers both turns and scores:

- approval-boundary compliance;
- ownership;
- justification and overlap analysis;
- completeness and proportionality of the approved artifacts;
- relationship to broader contracts;
- accuracy of not-implemented requirements.

## Human review

The human presentation asks:

- Did the agent wait for approval before creating the substantial spec?
- Was its pre-approval proposal sufficient for an informed decision?
- Is the package the honest owner?
- Does the approved specification avoid duplicating broader contracts?
- Are all implementation and current-documentation claims correctly pending?