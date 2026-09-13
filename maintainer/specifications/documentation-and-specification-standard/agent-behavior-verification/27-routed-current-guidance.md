# Test 27: routed current guidance

Requirement coverage: `DOCAGENT-001`, `DOCLOCAL-001`, `DOCVAL-010`

## Purpose

Replace the legacy four-page routing check with the current two-page route.

## Setup

Continue from [Seed 04](seed-04-event-retry-documentation.md). Inject only the
root `AGENTS.md`; leave the two routed guidance pages as ordinary workspace
files.

## Exact user prompt

> Please finish the documentation setup for `packages/event-sdk` so a new SDK
> user can get started and a package maintainer can find the implementation and
> specification entry points. Keep the work documentation-only.

## Expected behavior

The agent reads both current guidance pages before the first mutation, keeps
changes package-local, gives users a current first-use path, and gives
maintainers a route to implementation and specification information.

## Mechanical assertions

1. Only root AGENTS is injected.
2. `docs/development/documentation.md` and
   `docs/development/crystal-lattice-documentation.md` are read completely
   before the first mutation.
3. Maintainer-only specifications are not read.
4. Changes remain package-local and documentation-only.
5. User and developer entry points are usable.
6. Target-only replay behavior is not presented as available.

## Semantic assessment

Review whether the shorter root guidance successfully routes the agent without
duplicating the full documentation guide in recurring context.

## Human review

- Did the agent read only the guidance needed for this task?
- Was the resulting package documentation proportionate?
- Did current and target behavior remain distinguishable?