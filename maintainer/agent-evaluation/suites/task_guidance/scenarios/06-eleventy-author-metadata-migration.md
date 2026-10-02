# TG-06: Eleventy author-metadata compatibility migration

## Project

- Base repository: Eleventy Base Blog
- Base revision: `26b26106d7fbb30b7b40d9ef52589d10ddbcb462`
- Kind: static content site with generated pages, feeds, and author tooling

## Purpose

Test decomposition by compatibility-preserving working states. The work
touches schema/normalization, templates, feeds, content, tooling, tests,
documentation, and cleanup, but should not become a task per layer or phase.

## Derived starting state

The fixed fixture adds:

- legacy `author: "Name"` front matter across representative posts;
- page, archive, and feed rendering of that field;
- one repository-owned content-creation helper that writes the legacy form;
- generated-output tests for author presentation.

The target structured form supports one or more authors with stable
identifiers and display names.

## Natural request

> Migrate post author metadata from the current single-name field to a
> structured multi-author form without breaking existing content or generated
> pages during the transition. Templates, archives, feeds, and authoring tools
> must move to the new model, existing posts must be migrated safely, and the
> legacy form may be rejected only after generated-output and content evidence
> show that nothing still depends on it. Plan the work and create the
> appropriate task structure without implementing it.

The prompt describes compatibility states without naming tasks or phases.

## Approved outcomes

- `AUTHOR-1`: old and new author metadata normalize to one documented internal
  representation during the compatibility window.
- `AUTHOR-2`: pages, archives, feeds, and relevant metadata render equivalent
  author behavior from the normalized representation.
- `AUTHOR-3`: repository content and authoring tools migrate to the structured
  form with validation and reversible evidence.
- `AUTHOR-4`: the legacy form is deprecated or rejected only after no
  maintained content, tool, or generated surface depends on it.
- `AUTHOR-5`: every intermediate revision builds and publishes valid output.

## Reviewed coherent partition

```text
010: Introduce dual-format normalization and compatibility
020: Move generated surfaces to the normalized author model
030: Migrate content and authoring tools
040: Retire the legacy author form after evidence
```

- `020` depends on `010`.
- `030` depends on `010` and may proceed alongside later surface work when
  compatibility remains.
- `040` depends on `020` and `030` plus complete content/build evidence.
- Each child leaves a working site and owns its tests, documentation, and
  migration evidence.

## Acceptable alternatives

- Combine normalization and generated-surface adoption when one reviewed
  change still leaves a clear dual-format working state.
- Split content migration by independently owned content collections only when
  the fixture provides such ownership.
- Three to five children are acceptable when compatibility states and rollback
  remain clear.

## Fragmentation examples

Parser, schema, template, archive, feed, content rewrite, helper update, unit
tests, build tests, documentation, deprecation, and cleanup are not
automatically separate tasks. Most belong to one of the four working migration
states.

## Overpacking example

One atomic “change every post, template, feed, helper, and validator” task
eliminates the compatibility window and creates an unsafe, hard-to-review
migration.

## Important crossing

Real front matter flows through normalization and the production Eleventy build
into pages, archives, and feeds at every migration state.

## Semantic review questions

- Does every child leave the site buildable and compatible?
- Are dependencies based on retirement safety rather than generic phases?
- Did the agent multiply surfaces and test types into separate tasks?
- Is legacy retirement gated by direct evidence?