# Seed 06: existing-contract bug-fix investigation

## Purpose

This seed investigates one reproducible public bug whose intended behavior is
already defined by an existing specification. Branch tests can then verify that
the agent fixes implementation and live evidence without rewriting a target
that is already correct.

## Repository setup

The clean fixture contains:

```text
packages/path-policy/
├── README.md
├── src/path_policy.py
├── tests/test_path_policy.py
└── docs/development/specifications/path-normalization/
    ├── index.md
    ├── technical-spec.md
    └── requirements.md

tasks/path-policy-home-relative-bug.md
```

The specification requires home-relative paths to normalize against the
current user's home. One implementation path incorrectly treats them as
ordinary relative paths. The corresponding requirement is implemented but
currently unverified for this delivery path.

## Exact seed prompt

> Please investigate the home-relative path bug described in
> `tasks/path-policy-home-relative-bug.md`. Read only
> `packages/path-policy/README.md`,
> `packages/path-policy/src/path_policy.py`,
> `packages/path-policy/tests/test_path_policy.py`,
> `packages/path-policy/docs/development/specifications/path-normalization/index.md`,
> `packages/path-policy/docs/development/specifications/path-normalization/technical-spec.md`,
> and
> `packages/path-policy/docs/development/specifications/path-normalization/requirements.md`.
> Reproduce or explain the discrepancy and report the exact affected files. Do
> not modify files and do not propose a documentation or specification
> workflow.

## Seed assertions

1. No mutation occurs.
2. The response identifies the already-correct normative behavior.
3. It identifies the faulty implementation path and missing regression test.
4. It reports the live requirement and current-documentation state accurately.
5. It does not recommend rewriting or versioning the specification.
6. Candidate guidance is absent and cache/snapshot provenance is complete.

## Current branch

- [Bug fix with an existing specification](10-bug-fix-with-existing-specification.md)

Future branches may ask for a plan only, implementation without docs, or a
second delivery-path regression while reusing the same investigation.