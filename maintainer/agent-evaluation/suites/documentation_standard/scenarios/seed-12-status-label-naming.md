# Seed 12: status-label naming investigation

## Purpose

Establish an existing status API, one pending status-label requirement, current
tests, and current developer documentation before source-local terminology is
introduced by a branch task.

## Repository setup

The fixture contains:

```text
packages/status-labels/
├── README.md
├── src/status_labels.py
├── tests/test_status_labels.py
└── docs/development/
    ├── status-labels.md
    └── specifications/status-labels/
        ├── index.md
        ├── technical-spec.md
        └── requirements.md
```

`is_terminal(status)` is implemented and verified. The specification also
requires a public callable that maps `in_progress` to `In progress` and `done`
to `Done`, and raises `KeyError` for values without a defined label. It
deliberately defines behavior rather than a Python function name.
`STATUS-002` is not implemented.

## Exact seed prompt

> Please investigate the pending status-label behavior in
> `packages/status-labels`. Read
> `packages/status-labels/README.md`,
> `packages/status-labels/src/status_labels.py`,
> `packages/status-labels/tests/test_status_labels.py`,
> `packages/status-labels/docs/development/status-labels.md`,
> `packages/status-labels/docs/development/specifications/status-labels/index.md`,
> `packages/status-labels/docs/development/specifications/status-labels/technical-spec.md`,
> and
> `packages/status-labels/docs/development/specifications/status-labels/requirements.md`.
> Report the implemented API, pending behavior, missing test coverage, and
> documentation that would change when the pending requirement is implemented.
> Do not modify files, choose a function name, or propose task wording.

## Expected seed result

- The implemented `is_terminal` behavior is identified.
- The pending display-label behavior, defined mappings, and unknown-value
  error are identified without inventing a public function name.
- Missing implementation, tests, requirement evidence, and developer
  documentation are reported.
- No task terminology or implementation approach is proposed.
- No files change.

## Fixture

Use fixture `status-labels`, revision `v3`, branch variant `base`.

## Current branch

- [Test 37: source terms in code and tests](37-source-terms-in-code-and-tests.md)