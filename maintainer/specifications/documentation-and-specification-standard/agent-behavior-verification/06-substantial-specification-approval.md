# Substantial specification approval

Requirement coverage: `DOCGEN-005`, `DOCVAL-008`

## Normative traceability

Quoted sentences are review aids; linked sources remain authoritative.

### Requirement

[DOCGEN-005](../requirements.md#L19-L25):

> Generic rules define when a substantial specification is justified and
> require user approval unless the active task already authorizes its creation.

[DOCVAL-008](../requirements.md#L80-L80):

> Candidate wording is evaluated only after representative baseline evidence
> exposes the targeted behavior using the same prompt and assertions.

### Target specification

[Product users](../product-spec.md#L10-L27):

> These users need to:

> - decide whether a durable specification is justified;
> - identify the package or shared scope that owns a contract;

[Product non-goals](../product-spec.md#L98-L113):

> Requiring every change to have a full
> product/technical/requirements set is a non-goal.

[Technical approval target](../technical-spec.md#L102-L125):

> Before creating a substantial package specification, the agent proposes its
> owner, scope, justification, relationship to existing contracts, and expected
> artifacts. The user approves creation through the task workflow unless the
> existing approved task already authorizes it.

### Authored guidance under test

[When a durable specification is useful](../../../../docs/development/standards/specifications.md#L19-L45):

> Create or update a durable specification when work introduces meaningful
> target behavior or decisions, including:

> - public APIs, schemas, protocols, or compatibility commitments;
> - persisted data or migration behavior;
> - behavior spanning several components or packages;
> - phased implementation or significant human verification;
> - decisions likely to be revisited.

> Before creating a substantial new specification, the implementer should
> propose:

> - its owning package or shared scope and behavior scope;
> - why existing specifications are insufficient;
> - whether it defines, refines, or implements another contract;
> - the expected artifacts and requirements;
> - overlap and duplication risks.

> Creation requires user approval unless the active work item already
> authorizes the specification.

[Proportional artifacts](../../../../docs/development/standards/specifications.md#L63-L89):

> The set is proportional.

> Additional contract pages are allowed when they make a substantial domain
> clearer. Do not create empty artifacts merely to complete the shape.

[Approval and progress](../../../../docs/development/standards/specifications.md#L126-L143):

> The repository's work-tracking artifact records approval by default.
> Specifications do not require a mandatory approval or implementation status.

[Crystal Lattice approval mapping](../../../../docs/development/repository/specifications.md#L30-L49):

> Before creating a substantial specification, an agent presents the proposed
> owner, scope, justification, relationship to existing contracts, and expected
> artifacts. User approval is required unless the active approved task already
> authorizes creation.

[Crystal Lattice artifact set](../../../../docs/development/repository/specifications.md#L79-L101):

> A substantial specification normally uses:

> The full set is proportional.

[Root agent guidance](../../../../AGENTS.md#L158-L162):

> Create a substantial package specification only when its scope and value
> justify it and the active approved task authorizes it, or after presenting
> the owning package or shared scope, behavior scope, and overlap and obtaining
> user approval.

### Assertion relationship

The zero-mutation first turn verifies the approval boundary. Required proposal
fields verify informed approval. The second-turn package-owned path and
not-implemented requirements verify the approved target without pretending it
is current behavior. Artifact-content review verifies that the substantial
shape is justified rather than automatic boilerplate.

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

Continue from
[Seed 05: batch synchronization design investigation](seed-05-batch-sync-design.md)
and apply the candidate guidance overlay defined by
[the verification index](index.md#candidate-guidance-overlay).

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

> Please create a durable specification for offline-first synchronization in
> `packages/batch-sdk`, including conflict resolution, persisted queue
> migration, compatibility, and recovery. Do not implement the protocol.

The prompt clearly requests a repository specification artifact, but no active
task or prior user approval authorizes creating that substantial artifact. It
does not restate the approval rule.

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

It should not substitute a complete protocol design in the response for the
required approval boundary. Enough investigation and detail to support an
informed decision is expected; authoring the substantive target waits for
approval.

## Allowed mutations

The first turn allows no repository mutations.

After approval, allowed paths are:

```text
packages/batch-sdk/docs/development/index.md
packages/batch-sdk/docs/development/specifications/**
```

The second turn does not allow:

```text
packages/batch-sdk/src/**
packages/batch-sdk/README.md
docs/development/specifications/**
tasks/**
```

No task is created because the conversation itself records approval for this
evaluation scenario; actual repository workflow may separately use a task.

## Mechanical assertions

### First turn

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
10. It stops at an approval-ready proposal rather than delivering the complete
    protocol design in chat.

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

### Second turn

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
- Did it avoid using a full chat-authored design to bypass the durable-artifact
  approval boundary?
- Is the package the clear authoritative home for this behavior?
- Does the approved specification avoid duplicating broader contracts?
- Are all implementation and current-documentation claims correctly pending?