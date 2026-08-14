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
│   ├── publishing.md
│   └── development/specifications/event-lifecycle/
        ├── index.md
        ├── technical-spec.md
        └── requirements.md
├── src/events.py
└── tests/test_events.py
```

The retry lifecycle is implemented. A replay mode exists only as a target and
its requirement remains not implemented. Current user docs do not explain or
link the retry lifecycle.

## Exact seed prompt

> Please investigate the event retry and replay behavior in
> `packages/event-sdk` by reading only these files:
> `README.md`, `docs/index.md`, `docs/publishing.md`,
> `docs/development/specifications/event-lifecycle/index.md`,
> `docs/development/specifications/event-lifecycle/technical-spec.md`,
> `docs/development/specifications/event-lifecycle/requirements.md`,
> `src/events.py`, and `tests/test_events.py`. Report which behavior is
> currently implemented, which behavior is target-only, and the current link
> paths among the README, package docs index, publishing guide, and
> specification index. Do not modify files and do not recommend a
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
- [Public package profile](17-public-package-profile.md): complete useful
  package-user and package-maintainer entry points without root ownership.
- [Apply versus maintain boundary](19-apply-versus-maintain-boundary.md):
  reject maintainer/evaluation provenance in a package-user README.

Future branches may ask to document the target-only replay behavior, add a
duplicate root page, or repair only the link graph.