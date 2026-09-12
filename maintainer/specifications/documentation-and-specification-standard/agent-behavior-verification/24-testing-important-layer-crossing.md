# Test 24: testing an important layer crossing

Requirement coverage: `DOCGUIDE-006`, `DOCVAL-010`

## Purpose

Verify that a testing strategy does not replace an important production
crossing with isolated unit tests.

## Setup

Continue from [Seed 11](seed-11-testing-strategy.md) with branch variant
`cross-layer`, which adds the approved option-delivery testing task.

## Exact user prompt

> Please prepare the approved testing strategy for option delivery. Do not
> implement the change or edit test code.

## Expected behavior

The strategy maps local behavior to unit or component tests and includes at
least one integration path through the plugin result, public endpoint, and
production frontend adapter. It does not require native or hosted coverage
without a separate risk that needs those environments.

## Mechanical assertions

1. Exactly one cross-package `testing-strategy.md` is created.
2. Plugin behavior, the public endpoint, and the production frontend adapter
   are all represented.
3. At least one selected integration test crosses the real delivery boundary.
4. The strategy is not satisfied by mocks or isolated unit tests alone.
5. Native, hosted, and manual checks are either omitted or given a concrete
   risk-based reason.
6. Source code and test files do not change.

## Semantic assessment

Review whether every selected layer detects a distinct important failure and
whether the strategy avoids both a unit-only gap and an indiscriminate
end-to-end test list.

## Human review

- Does the integration test reach the production boundary being claimed?
- Are lower-level tests used where they are sufficient?
- Are expensive layers omitted for a defensible reason?