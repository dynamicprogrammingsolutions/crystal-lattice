# Local bug fix without a durable specification

Requirement coverage: `DOCGEN-002`, `DOCGEN-005`

## Normative traceability

Quoted excerpts are review aids; linked sources remain authoritative.

### Requirements

[DOCGEN-002 and DOCGEN-005](../requirements.md#L17-L25):

> A package-neutral specification standard defines target specifications, live
> requirements, work-tracked approval, current public/maintainer docs,
> proportional artifacts, evidence, and simple spec-first commits.

> Generic rules define when a substantial specification is justified and
> require user approval unless the active task already authorizes its creation.

### Target specification

[Product non-goals](../product-spec.md#L84-L99):

> Requiring every change to have a full product/technical/requirements set is a
> non-goal.

[Technical approval target](../technical-spec.md#L118-L121):

> Before creating a substantial package specification, the agent proposes its
> owner, scope, justification, relationship to existing contracts, and expected
> artifacts.

### Authored guidance under test

[When a durable specification is useful](../../../../docs/development/standards/specifications.md#L19-L45):

> A small local change may use only its approved work item when it has one
> straightforward outcome, no material design choice, and no durable contract
> worth preserving.

[Proportional artifacts](../../../../docs/development/standards/specifications.md#L63-L89):

> Do not create empty artifacts merely to complete the shape.

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