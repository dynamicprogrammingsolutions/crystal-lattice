# Test 17: public package profile and local ownership

Legacy status: retained for the direct pre/post comparison. Its required full
package profile conflicts with the current rule that every illustrated file is
optional, so it is excluded from the revised suite.

## Purpose

Verify that an agent applies the Crystal Lattice public-package profile
proportionally inside the owning package, creates useful package-user and
package-maintainer routes, and does not move package documentation to root or
leak standards-maintenance context.

## Normative traceability

[DOCREP-001, DOCREP-003, DOCREP-004, and DOCREP-005](../requirements.md#L31-L38):

> Repository policy maps the generic rules to root and package paths, package
> profiles, shared domains, tasks, agent guidance, publication, and validation.

> Root `docs/` is limited to repository-wide guidance, honest cross-package
> contracts, and site entry points; package-visible and package-maintainer
> documentation is owned locally.

> Public/reusable package profiles define concise README, AGENTS, docs index,
> quickstart, user docs, development docs, and optional reference without
> forcing filler into small packages.

> Repository policy distinguishes applying the standards from maintaining them
> and keeps maintainer specifications and workflow-evaluation internals outside
> public output.

[Repository-policy boundary](../technical-spec.md#L81-L100):

> The repository policy maps generic concepts to root and package
> documentation paths and public-package profiles without restating the
> complete generic explanations.

[Crystal Lattice source structure and documentation mapping](../../../../docs/development/repository/documentation.md):

> Public/reusable packages, applications, SDKs, and services target a concise
> README, AGENTS, docs index, quickstart, user documentation, development
> documentation, package-owned specifications, and optional reference.

[Crystal Lattice ownership](../../../../docs/development/repository/documentation.md#L127-L142):

> Package user and implementation documentation belongs with its package.
> Root architecture pages are limited to genuinely cross-package structure.

[Incremental profile adoption](../../../../docs/development/repository/documentation.md#L108-L125):

> This is a profile classification, not a requirement to generate every missing
> file in one change. Other packages adopt the profile on touch or through
> separately scoped work.

## Seed

Reuse [Seed 04](seed-04-event-retry-documentation.md). Its factual
investigation already identifies the implemented retry behavior, target-only
replay behavior, current user pages, package specification, and link graph.

## Repository setup

The focused fixture contains a public SDK package with:

- a concise README;
- a package docs index and current publishing guide;
- current source and tests;
- an internal event-lifecycle specification and requirements.

It lacks a package quickstart, package AGENTS file, and development index. The
existing files contain enough verified information to create useful entry
points without reverse engineering additional behavior.

## Exact user prompt

> Please finish the documentation setup for `packages/event-sdk` so a new SDK
> user can get started and a package maintainer can find the implementation and
> specification entry points. Keep the work documentation-only.

The prompt describes user and maintainer outcomes but does not name the target
file layout or tell the agent where the documentation belongs.

## Expected behavior

The agent should keep authored documentation under `packages/event-sdk/` and:

1. retain a concise README that routes users and maintainers;
2. add a current, executable quickstart using the implemented `publish`
   behavior;
3. keep the package docs index as the user-documentation map;
4. add concise package AGENTS routing only if inherited guidance plus the
   package indexes do not provide a complete route;
5. add a development index linking current implementation entry points and the
   package-owned event-lifecycle specification;
6. avoid documenting target-only replay as supported behavior;
7. avoid root documentation, maintainer material, placeholder reference pages,
   or unrelated code changes.

## Allowed mutations

Documentation under:

```text
packages/event-sdk/
```

No source, test, root `docs/`, `maintainer/`, task, generated-output, or other
package mutation is allowed.

## Mechanical assertions

1. Every changed path is package-local documentation or package AGENTS.
2. `docs/quickstart.md` exists and contains a concrete current first-use flow.
3. `docs/index.md` routes to the quickstart, and README either links it
   directly or provides a complete first-use example plus a route to the docs
   index.
4. If `AGENTS.md` is created, it routes to source, tests, user docs,
   development docs, and a focused verification command; otherwise the package
   entry-point chain is complete without it.
5. `docs/development/index.md` routes to source/tests and the existing
   event-lifecycle specification.
6. Public pages do not claim target-only replay support or link internal target
   specifications.
7. No root, maintainer, task, generated-output, source, or test file changes.

## Semantic assessment

- Are the new pages useful rather than profile-shaped filler?
- Can a new package user reach first success without maintainer context?
- Can a package maintainer find implementation and target entry points?
- Did the agent keep package-owned material out of root documentation?

## Human review

- Is the amount of documentation proportional to this public SDK fixture?
- Would any created page be better omitted because another page already serves
  its role?
