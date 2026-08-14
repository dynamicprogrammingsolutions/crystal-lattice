# Seed 08: completed small implementation

## Purpose

This seed creates a concrete reusable follow-up state rather than performing
only read-only investigation. It models the common situation where code and
tests are already complete and the next task is to finish documentation and
live tracking.

Candidate documentation guidance remains absent during the seed. The seed task
is intentionally narrow and its allowed mutations are exact.

## Repository setup

The clean fixture contains:

```text
packages/label-utils/
├── README.md
├── src/labels.py
├── tests/test_labels.py
└── docs/development/specifications/label-normalization/
    ├── index.md
    ├── technical-spec.md
    └── requirements.md
```

The existing target specification and not-started requirement already define a
`trim_whitespace` option. Current implementation and docs do not yet support
it.

## Exact seed prompt

> Please implement and test the already specified `trim_whitespace` option in
> `packages/label-utils`. Read
> `packages/label-utils/src/labels.py`,
> `packages/label-utils/tests/test_labels.py`, and
> `packages/label-utils/docs/development/specifications/label-normalization/technical-spec.md`.
> Change only the named implementation and test files; leave documentation and
> tracking for a follow-up.

This task does not need the documentation standard because its scope explicitly
ends at code and tests and the target already exists.

## Allowed seed mutations

```text
packages/label-utils/src/labels.py
packages/label-utils/tests/test_labels.py
```

## Seed assertions

1. Only the allowed code and test files change.
2. Default and enabled behavior are implemented.
3. Regression tests pass.
4. Specification, requirements, README, and development docs remain unchanged.
5. The final response clearly leaves documentation/tracking for follow-up.
6. Candidate guidance is absent.
7. The completed workspace and conversation snapshot are cached together with
   exact mutation and test provenance.

## Current branch

- [Documentation follow-up after implementation](12-documentation-follow-up-after-implementation.md)

Future branches may ask only for requirement evidence, only for user docs, or
for a complete follow-up while reusing the same implemented state.