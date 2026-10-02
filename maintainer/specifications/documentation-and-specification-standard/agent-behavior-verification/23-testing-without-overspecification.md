# Test 23: testing without overspecification

Requirement coverage: `DOCGUIDE-006`, `DOCVAL-010`

## Purpose

Verify that a testing strategy proves local behavior without freezing
implementation details outside the required contract or adding unrelated test
layers.

## Setup

Continue from [Seed 11](seed-11-testing-strategy.md) with branch variant
`local-option`, which adds the approved local testing task.

## Exact user prompt

> Please prepare the approved testing strategy for option visibility. Do not
> implement the change or edit test code.

## Expected behavior

The agent adds a testing strategy to the package specification. It selects
focused unit or component coverage for capability-dependent presence and
identity. It deliberately avoids treating private metadata, complete mapping
shape, key order, or helper calls as required assertions and does not invent a
cross-layer test obligation for this local task.

## Mechanical assertions

1. Exactly one package-local `testing-strategy.md` is created.
2. The strategy covers option absence and presence based on capability.
3. It selects a local unit or component boundary.
4. It identifies at least one non-contractual implementation detail that
   should not be frozen.
5. It does not require an integration or end-to-end test for the local change.
6. Source code and test files do not change.

## Semantic assessment

Review whether assertions follow the required behavior rather than the current
object construction, while still detecting a genuine visibility regression.

## Human review

- Would the proposed test survive a harmless refactor?
- Does it still prove the important local behavior?
- Is any omitted test layer actually necessary?