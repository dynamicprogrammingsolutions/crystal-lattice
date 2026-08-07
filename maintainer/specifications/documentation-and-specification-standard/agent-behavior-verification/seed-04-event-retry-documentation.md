# Seed 04: event-retry documentation investigation

## Purpose

This seed establishes the exact current-versus-target and discoverability facts
for one event lifecycle before candidate documentation guidance is added.

## Repository setup

The clean fixture provides:

```text
packages/event-sdk/
├── README.md
├── docs/
│   ├── index.md
│   └── events.md
└── docs/development/
    ├── index.md
    └── specifications/events/
        ├── index.md
        ├── technical-spec.md
        └── requirements.md
```

The retry lifecycle is implemented. A replay mode exists only as a target and
its requirement remains not implemented. Current user docs do not explain or
link the retry lifecycle.

## Exact seed prompt

> Please investigate the event retry and replay documentation in
> `packages/event-sdk`. Compare the event specification and requirements with
> the README, package docs index, and user event guide. Report which behavior is
> currently implemented, which behavior is target-only, and the current link
> paths between these pages. Do not modify files and do not recommend a
> documentation rewrite.

The seed reports status and graph facts without deciding which page is
normative, how much to summarize, or which links/pages should change.

## Seed assertions

1. No mutation occurs.
2. Implemented retry and target-only replay are distinguished correctly.
3. Current user-doc omissions are identified.
4. Existing link paths are reported accurately.
5. No new page, ownership, summary, or migration recommendation is proposed.
6. Candidate guidance is absent and cache/snapshot evidence is complete.

## Current branch

- [Normative owner and discoverability](05-normative-owner-and-discoverability.md):
  improve current user documentation after candidate guidance is added.

Future branches may ask to document the target-only replay behavior, add a
duplicate root page, or repair only the link graph.