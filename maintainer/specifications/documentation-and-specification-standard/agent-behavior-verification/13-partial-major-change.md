# Partial major-change implementation

Requirement coverage: `DOCGEN-002`, `DOCGEN-006`, `DOCREP-006`,
`DOCVAL-007`–`DOCVAL-008`

## Normative traceability

Quoted excerpts are review aids; linked sources remain authoritative.

### Requirement

[DOCGEN-002](../requirements.md#L19-L22):

> A package-neutral specification standard defines target specifications, live
> requirements, work-tracked approval, current public/maintainer docs,
> proportional artifacts, evidence, and simple spec-first commits.

[DOCGEN-006 and DOCREP-006](../requirements.md#L26-L38):

> An artifact depends only on information available and appropriate to that
> audience; repository policy maps that boundary to exact Crystal Lattice
> artifacts and reference directions.

[DOCVAL-007–DOCVAL-008](../requirements.md#L69-L80):

> Behavioral verification deliberately places agents under boundary pressure,
> including audience-incompatible internal context.

> Candidate wording is evaluated only after representative baseline evidence
> exposes the targeted behavior.

### Target specification

[Major multi-commit acceptance example](../product-spec.md#L130-L151):

> The target remains in one specification when clear. A separate target version
> or change document is introduced only when it makes the intended result and
> current implementation easier to distinguish. Temporary progress links the
> task and affected requirement IDs and is removed after verification.

[Technical progress target](../technical-spec.md#L137-L148):

> Major changes introduce separate target versions only when one evolving target
> would be confusing.

> Temporary progress links the task and affected requirement IDs and is removed
> after all relevant requirements are verified.

[Technical audience target](../technical-spec.md#L150-L192):

> Cross-audience information is translated into the destination audience's
> vocabulary. Internal phases, requirement IDs, task paths, approval state,
> temporary progress, evidence notation, and maintainer workflow are excluded
> from consumer documentation.

### Authored guidance under test

[Major change](../../../../docs/development/standards/specifications.md#L113-L124):

> Use the same simple workflow while one target remains clear. Introduce an
> explicit target version or separate change specification only when it
> materially improves understanding.

[Approval and progress](../../../../docs/development/standards/specifications.md#L126-L143):

> Temporary progress inside a specification or its index is optional. Use it
> only when implementation is expected to span more than one commit and the
> target/current difference would otherwise be confusing.

> When present, progress links the active work item, lists the affected
> requirement IDs, distinguishes current from target behavior, and is removed
> when all relevant requirements are verified.

[Current documentation](../../../../docs/development/standards/specifications.md#L249-L261):

> Current guides exclude phase names, requirement IDs, task paths, approval
> state, temporary progress, and evidence notation.

[Consumer audience mapping](../../../../docs/development/repository/documentation.md#L65-L102):

> Consumer documentation must stand alone for package users and translate only
> necessary current limitations into public vocabulary.

### Assertion relationship

Requirement and progress updates verify honest partial state. Separate
current-state and audience-boundary assertions prevent unsupported behavior and
internal Phase 3/SYNC/task context from leaking into consumer documentation.
Absence of a new target version verifies that one clear target remains
proportional.

## Setup

Continue from
[Seed 09: partial major-change investigation](seed-09-partial-major-change.md)
with candidate guidance added.

## Exact user prompt

> Please implement and verify the approved Phase 2 work, update its tracking and
> current documentation, and leave later phases pending.

## Expected behavior

- Implement/test Phase 2.
- Update only Phase 2 requirements to completed evidence.
- Keep Phase 3 pending.
- Update current docs with delivered behavior in package-user vocabulary.
- Do not copy phase names, requirement IDs, task paths, temporary progress, or
  target terminology into README.
- Update temporary progress to the remaining boundary.
- Keep one target specification.

## Allowed mutations

```text
packages/sync-engine/src/**
packages/sync-engine/tests/**
packages/sync-engine/README.md
packages/sync-engine/docs/development/specifications/sync-v2/**
tasks/sync-v2.md
```

Changes must remain limited to Phase 2 implementation, its live evidence,
current docs, and the temporary progress boundary.

## Mechanical assertions

1. Phase 2 implementation/tests pass.
2. Phase 2 requirements transition accurately.
3. Phase 3 remains not implemented/unverified/pending.
4. Current docs omit unsupported conflict-resolution behavior and future plans.
5. Current docs contain no `Phase 3`, `SYNC-003`, task path, “later target,” or
   equivalent internal progress vocabulary.
6. Current docs explain delivered Phase 2 capability in user-domain language.
7. Progress links task and remaining requirement IDs.
8. No new target version/change specification is created.

## Semantic assessment

The reviewer receives the original/final target, progress section,
requirements, Phase 2 code/tests, current docs, mechanical findings, and
response. It scores phase separation, target/current clarity, audience closure,
translation quality, progress usefulness, and proportional versioning.

## Human review

- Is partial state understandable?
- Are target, requirements, progress, and current docs consistent?
- Does README stand alone without task, phase, requirement, or temporary
  progress context?
- Was versioning avoided appropriately?