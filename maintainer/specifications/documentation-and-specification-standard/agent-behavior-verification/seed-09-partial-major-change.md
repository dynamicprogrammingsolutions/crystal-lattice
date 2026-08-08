# Seed 09: partial major-change investigation

## Purpose

This seed investigates an approved multi-commit capability whose target,
requirements, implementation, current docs, and temporary progress intentionally
differ while work is incomplete.

## Repository setup

The fixture contains:

```text
packages/sync-engine/
├── README.md
├── src/
├── tests/
└── docs/development/specifications/sync-v2/
    ├── index.md
    ├── product-spec.md
    ├── technical-spec.md
    └── requirements.md

tasks/sync-v2.md
```

Phase 1 is implemented and documented. Phase 2 is approved but not implemented.
The specification index has a temporary progress section linking the task and
affected requirement IDs. Phase 3 remains future work.

## Exact seed prompt

> Please investigate the current state of the approved `sync-v2` work in
> `tasks/sync-v2.md`. Compare the target specification, temporary progress,
> requirements, implementation, tests, and current user documentation. Report
> what is complete, what Phase 2 requires, and what remains later. Do not modify
> files and do not propose a new specification version.

## Seed assertions

1. No mutation occurs.
2. Phase 1, Phase 2, and later target behavior are distinguished accurately.
3. Requirement states and evidence are reported correctly.
4. Current docs are identified as covering only implemented behavior.
5. Temporary progress links are identified.
6. No new target version or change specification is proposed.
7. Candidate guidance is absent and provenance is complete.

## Current branch

- [Partial major-change implementation](13-partial-major-change.md)

Future branches may complete the final phase and verify removal of temporary
progress using the same initial investigation or a continuation from Test 13.