# Seed 07: local bug-fix investigation

## Purpose

This seed investigates a small local defect with no durable public contract or
material design choice. It supports tests that the guidance remains
proportional and does not force a specification for every bug fix.

## Repository setup

The clean fixture contains:

```text
packages/slug-utils/
├── README.md
├── src/slug_cache.py
└── tests/test_slug_cache.py
```

The cache cleanup helper raises `FileNotFoundError` when another process removes
an expired cache entry between discovery and deletion. The package has no
durable specification because this is an internal implementation detail.

## Exact seed prompt

> Please investigate the cache-cleanup race in `packages/slug-utils`: an
> expired cache file may disappear between discovery and deletion. Reproduce or
> explain the failure, identify the affected code and tests, and report whether
> any supported user behavior is involved. Do not modify files.

## Seed assertions

1. No mutation occurs.
2. The race and affected helper are identified.
3. The missing regression test is identified.
4. The response correctly reports that no supported public contract changes.
5. It does not propose a substantial specification.
6. Candidate guidance is absent and provenance is complete.

## Current branch

- [Local bug fix without a durable specification](11-local-bugfix-without-durable-specification.md)

Future branches may vary the prompt wording or ask only for a plan while
reusing the same factual seed.