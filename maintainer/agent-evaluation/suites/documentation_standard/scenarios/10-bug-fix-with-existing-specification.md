# Bug fix with an existing specification

Requirement coverage: `DOCGEN-002`

## Normative traceability

Quoted excerpts are review aids; linked sources remain authoritative.

### Requirement

[DOCGEN-002](../../../../docs/development/specifications/documentation-guidance/requirements.md):

> A package-neutral specification standard defines target specifications, live
> requirements, work-tracked approval, current public/maintainer docs,
> proportional specification files, evidence, and simple spec-first commits.

### Target specification

[Specification and current state](../../../../docs/development/specifications/documentation-guidance/product-spec.md):

> Specifications describe intended targets and may temporarily differ from
> implementation. Requirements track the live implementation, verification,
> documentation, and evidence state.

### Authored guidance under test

[Four sources of truth](../../../../../docs/development/documentation.md):

> A specification is not evidence that its target currently exists.
> Requirements bridge the target and the implemented system.

[Requirements evidence](../../../../../docs/development/documentation.md#L145-L186):

> Requirements use stable identifiers and keep implementation, verification,
> documentation, and evidence separate.

[Current documentation](../../../../../docs/development/documentation.md#L235-L242):

> Public user documentation and implementation/maintainer documentation
> describe current behavior.

### Assertion relationship

Leaving an already-correct target unchanged verifies that spec-first does not
mean rewriting every specification. Code/tests and requirement evidence verify
the live fix. Current docs change only if the supported behavior description
was inaccurate.

## Setup

Continue from
[Seed 06: existing-contract bug-fix investigation](seed-06-existing-contract-bugfix.md)
with candidate guidance added.

## Exact user prompt

> Please fix the path-normalization bug you investigated and update the
> necessary tests, tracking, and current documentation.

## Expected behavior

- Preserve the correct normative target.
- Fix the faulty implementation path.
- Add regression coverage.
- Update requirement verification/evidence.
- Correct current docs only if they were inaccurate.
- Keep approval/execution in the task.

## Allowed mutations

```text
packages/path-policy/src/path_policy.py
packages/path-policy/tests/test_path_policy.py
packages/path-policy/README.md
packages/path-policy/docs/development/specifications/path-normalization/requirements.md
tasks/path-policy-home-relative-bug.md
```

The normative specification is expected to remain unchanged unless the run
finds a concrete contradiction in the fixture.

## Mechanical assertions

1. The normative behavior is not weakened or duplicated.
2. Implementation and regression tests change and pass.
3. Requirement evidence identifies the regression test and delivery.
4. Current docs remain accurate.
5. No new specification or version is created.

## Semantic assessment

The reviewer receives the bug task, target contract, implementation/test diff,
requirements evidence, current-doc diff, and response. It scores whether the
agent distinguished a correct target from faulty implementation and kept the
fix proportional.

## Human review

- Did the agent distinguish target correctness from implementation failure?
- Is the regression evidence sufficient?
- Were documentation changes proportional to the bug?