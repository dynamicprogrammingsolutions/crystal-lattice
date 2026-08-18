# Documentation follow-up after implementation

Requirement coverage: `DOCGEN-002`, `DOCGEN-004`

## Normative traceability

Quoted excerpts are review aids; linked sources remain authoritative.

### Requirements

[DOCGEN-002 and DOCGEN-004](../requirements.md#L17-L24):

> A package-neutral specification standard defines target specifications, live
> requirements, work-tracked approval, current public/maintainer docs,
> proportional artifacts, evidence, and simple spec-first commits.

> Generic rules define one authoritative source, controlled summaries,
> current-versus-target separation, complete indexes, and two-link
> discoverability without requiring placeholder pages.

### Target specification

[Product specification and current state](../product-spec.md#L50-L58):

> Requirements track the live implementation, verification, documentation, and
> evidence state.

> Public user documentation and implementation/maintainer documentation
> describe current behavior and must remain consistent with committed code.

### Authored guidance under test

[Relationship to work tracking](../../../../docs/development/standards/specifications.md#L192-L202):

> Requirements own live state and evidence.

[Current documentation](../../../../docs/development/standards/specifications.md#L249-L261):

> Public user documentation and implementation/maintainer documentation
> describe current behavior.

[Discoverability](../../../../docs/development/standards/documentation.md#L153-L176):

> Every authored page should be reachable in at most two documentation links
> from the nearest repository, package, or shared-domain entry point.

### Assertion relationship

The seed proves implementation/tests already exist. Branch mutations to
requirements and current docs verify follow-up completion without replaying
implementation. Link assertions verify discoverability.

## Setup

Continue from
[Seed 08: completed small implementation](seed-08-completed-small-implementation.md),
preserving its exact code/test mutations and adding candidate guidance only to
the follow-up.

## Exact user prompt

> Please finish the documentation and tracking for what we just implemented.

## Expected behavior

- Update the requirement to implemented/automated/documented with evidence.
- Update current README and relevant development docs.
- Link the behavior from the appropriate entry point.
- Leave the already-correct target, code, and tests unchanged.

## Allowed mutations

```text
packages/label-utils/README.md
packages/label-utils/docs/development/index.md
packages/label-utils/docs/development/specifications/label-normalization/requirements.md
```

The parent implementation, tests, and target specification must remain
unchanged.

## Mechanical assertions

1. Parent seed code/tests remain unchanged.
2. Requirements accurately cite implementation and test evidence.
3. Current docs explain the delivered option and defaults.
4. Links resolve and satisfy the package entry-point chain.
5. No new specification or placeholder page is created.

## Semantic assessment

The reviewer receives the completed seed state, follow-up prompt, requirement
and documentation diffs, link findings, and response. It scores continuity
understanding, current-state accuracy, evidence completeness, and avoidance of
redundant implementation work.

## Human review

- Did the agent understand the follow-up context?
- Are current docs and live tracking now complete?
- Did it avoid redundant implementation work?