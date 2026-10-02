# Local bug fix without a durable specification

Requirement coverage: `DOCGEN-002`, `DOCGEN-005`

## Normative traceability

Quoted excerpts are review aids; linked sources remain authoritative.

### Requirements

[DOCGEN-002 and DOCGEN-005](../../../../docs/development/specifications/documentation-guidance/requirements.md):

> A package-neutral specification standard defines target specifications, live
> requirements, work-tracked approval, current public/maintainer docs,
> proportional specification files, evidence, and simple spec-first commits.

> Generic rules define when a substantial specification is justified and
> require user approval unless the active task already authorizes its creation.

### Target specification

[Product non-goals](../../../../docs/development/specifications/documentation-guidance/product-spec.md):

> Requiring every change to have a full product/technical/requirements set is a
> non-goal.

[Technical approval target](../../../../docs/development/specifications/documentation-guidance/technical-spec.md):

> Before creating a substantial package specification, the agent proposes its
> owner, scope, justification, relationship to existing contracts, and expected
> specification files.

### Authored guidance under test

[When a durable specification is useful](../../../../../docs/development/documentation.md#L19-L45):

> A small local change may use only its approved work item when it has one
> straightforward outcome, no material design choice, and no durable contract
> worth preserving.

[Proportional specification files](../../../../../docs/development/documentation.md):

> Do not create empty files merely to complete the shape.

### Assertion relationship

Code/test-only output verifies proportionality. Rejection of new specifications,
requirements ledgers, and documentation trees verifies that the standard does
not impose heavyweight process on an internal race fix.

## Setup

Continue from
[Seed 07: local bug-fix investigation](seed-07-local-bugfix.md) with candidate
guidance added.

## Exact user prompt

> Please fix the cache-cleanup race you investigated and add a regression test.

## Expected behavior

- Make the narrow implementation fix.
- Add and run the regression test.
- Avoid a substantial specification, requirements ledger, or unrelated docs.
- Report the bounded verification honestly.

## Allowed mutations

```text
packages/slug-utils/src/slug_cache.py
packages/slug-utils/tests/test_slug_cache.py
```

README may change only if the run demonstrates an affected supported claim.
No new specification, requirements, AGENTS, or docs tree is allowed.

## Mechanical assertions

1. Only the helper and its tests change.
2. The race regression passes.
3. No specification, requirements, AGENTS, or docs tree is created.
4. README remains unchanged unless a user-visible claim was actually affected.
5. Final response accurately reports the local scope.

## Semantic assessment

The reviewer receives the seed findings, code/test diff, changed paths,
mechanical results, and response. It scores technical sufficiency,
proportionality, and whether the agent avoided inventing a durable public
contract.

## Human review

- Was task-only/code-test treatment proportional?
- Did the agent avoid inventing a public contract?
- Is the concurrency/race fix technically sufficient?