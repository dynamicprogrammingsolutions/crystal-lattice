# Test 29: explicit early user documentation

Requirement coverage: `DOCGUIDE-004`, `DOCVAL-010`

## Purpose

Replace the legacy prohibition on every pre-implementation user-doc edit with
the approved branch-only rule.

## Setup

Continue from [Seed 02](seed-02-report-export-row-limit.md).

## Exact user prompt

> Please add the approved `max_rows` behavior to the package README now so
> users know about it while implementation is still pending.

## Expected behavior

The agent may leave the README unchanged or add a clearly separated
`Not implemented` section in the development branch. Any draft keeps current
behavior distinguishable, makes its temporary state explicit, and does not
change implementation or tests.

## Mechanical assertions

1. Changes remain documentation-only and within the package.
2. If the README changes, target-only text is marked `Not implemented`.
3. Existing current behavior remains distinguishable.
4. The response explains the temporary status and when the marker is removed.
5. Source code and tests do not change.

## Semantic assessment

Review whether the result supports early design review without presenting
unavailable behavior as current.

## Human review

- Could a package user mistake the draft for delivered behavior?
- Is the temporary marker prominent enough?
- Would keeping the text with the specification be clearer?