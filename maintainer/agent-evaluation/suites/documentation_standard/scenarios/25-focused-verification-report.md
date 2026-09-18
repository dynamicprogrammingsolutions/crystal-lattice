# Test 25: focused verification report

Requirement coverage: `DOCGUIDE-006`, `DOCVAL-010`

## Purpose

Verify that a completion update foregrounds decisive behavior evidence and
remaining work rather than routine quality-check counts.

## Setup

Continue from
[Seed 08](seed-08-completed-small-implementation.md), whose implementation and
focused test pass while README and requirement tracking remain stale.

## Exact user prompt

> Please give me a concise completion update for the label-trimming change. Do
> not modify files.

## Expected behavior

The response explains the delivered trimming behavior, names the focused test
that proves it, and identifies the stale current documentation or requirements.
Formatting, lint, compilation, and broad counts are absent or clearly
secondary.

## Mechanical assertions

1. No files change.
2. The response names the trimming behavior.
3. It names the focused passing test or pytest evidence.
4. It identifies remaining documentation or requirement tracking.
5. Acceptance evidence appears before any routine mechanical checks.
6. The response remains concise.

## Semantic assessment

Review whether a human can quickly tell what works, why that claim is credible,
and what still prevents complete delivery.

## Human review

- Is the decisive evidence easy to find?
- Is important remaining work visible?
- Was any routine check given more prominence than the feature evidence?