# Reviewed target — tg06-eleventy-author-migration-decomposition

**Eleventy author metadata migration decomposition** — Partition a broad content/build migration by compatible working states rather than files and phases.

Category: decomposition · Project: `Eleventy author metadata migration fixture` · Acceptable partition sizes: 3, 4, 5

**Approved outcomes**

- AUTHOR-1: Legacy single-author and structured one-or-more-author metadata normalize to one documented internal representation during migration.
- AUTHOR-2: Pages, archives, feeds, and metadata render equivalent single-author behavior and approved multi-author behavior from the normalized model.
- AUTHOR-3: Content and authoring tools migrate safely to the structured form.
- AUTHOR-4: Legacy form is retired only after no maintained source or generated surface depends on it.
- AUTHOR-5: Every intermediate revision builds and publishes valid output.

**Coherent deliverables**

- **AUTHOR-D1** — Introduce dual-format normalization and compatibility
  The site can safely accept old and new content before consumers or content migrate.
  - Outcomes: AUTHOR-1, AUTHOR-5
- **AUTHOR-D2** — Move generated surfaces to the normalized model (depends on AUTHOR-D1)
  All public output uses one stable internal representation while both source formats remain valid.
  - Outcomes: AUTHOR-2, AUTHOR-5
- **AUTHOR-D3** — Migrate content and authoring tools (depends on AUTHOR-D1)
  Maintained producers and content stop creating new legacy dependencies.
  - Outcomes: AUTHOR-3, AUTHOR-5
- **AUTHOR-D4** — Retire the legacy author form after evidence (depends on AUTHOR-D2, AUTHOR-D3)
  The migration completes only after direct content and generated-output evidence makes removal safe.
  - Outcomes: AUTHOR-4, AUTHOR-5

**Important crossings**

- Real front matter flows through normalization and the production Eleventy build into pages, archives, and feeds at every migration state.

**Acceptable alternatives**

- Combine normalization and generated-surface adoption when a clear dual-format working state remains.
- Split content migration only for independently owned content collections.

**Fragmentation examples**

- Parser and schema tasks separated from compatibility delivery.
- Page, archive, and feed templates each becoming a task.
- Content rewrite and authoring helper updates split without ownership.
- Unit tests, build tests, documentation, cleanup, and final review as horizontal tasks.

**Overpacking examples**

- One atomic change across content, normalization, templates, feeds, tooling, and rejection removes the safe compatibility window.

**Open questions**

- Stable author identifier format and legacy deprecation period require approval.

**Handoff expectations**

- retain plan: Preserve working migration states, rollback assumptions, dependencies, and direct retirement evidence.
- omit plan: Preserve current consumers/producers, compatibility constraints, public questions, and source pointers without the four-stage migration direction.
- fresh agent plan: A fresh agent reconstructs compatible working states and does not create a task per surface or test type.
