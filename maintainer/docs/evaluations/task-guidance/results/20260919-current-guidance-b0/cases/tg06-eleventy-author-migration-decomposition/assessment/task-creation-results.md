# Task-creation semantic assessment

- Assessor: `glm-5.3-flash:cloud` (effort max) · run `20260919T223218.544286Z-task-guidance-semantic-tg06-eleventy-author-migration-decomposition-bb8302be`
- Assessor config: [glm-assessor-max.json](../../../shared/configs/glm-assessor-max.json)
- Assessor system message: [glm-assessor-max-3d0be6dc03e9.md](../../../shared/system-messages/glm-assessor-max-3d0be6dc03e9.md) (original SHA-256 `ecaac18da0be2b40…`)
- Rubric: fragmentation uses none/low/medium/high mapped to 100/67/33/0; every other dimension uses none/partial/present mapped to 100/50/0. An assessment's overall success is the equal-weight average of the six dimension scores.

## Reviewed target

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

- fresh agent plan: A fresh agent reconstructs compatible working states and does not create a task per surface or test type.
- omit plan: Preserve current consumers/producers, compatibility constraints, public questions, and source pointers without the four-stage migration direction.
- retain plan: Preserve working migration states, rollback assumptions, dependencies, and direct retirement evidence.

## Judgments

### glm · max (None, None) — handoff quality 86

- Plan coverage: None · Documentation boundary: None · Testing boundary: None
- Task self-contained: no · Broad rediscovery: no
- Lost facts or decisions: none
- Invented scope or decisions: none
- Missing outcomes: none

> The partition follows the target's state-based model closely: normalization+compatibility (010), one combined consumer-migration task covering layout, feed, and archives (020), and a gated retirement with evidence, rejection, and final documentation (050) map 1:1 to AUTHOR-D1/D2/D4, with tests and documentation embedded inside deliverables rather than horizontal. The only boundary defect is splitting AUTHOR-D3 into a tool task (030) and a content task (040), a split the target explicitly names as fragmentation; merging them loses nothing. The 040→020 dependency conservatively serializes content migration behind rendering migration. Outcome coverage is complete, and the important crossing is owned by named real-build checks (mixed-content fixture builds through real templates/config, real-content baseline comparison, post-rejection build), so crossing ownership is complete. Open decisions on field shape, rejection mechanism, and feed semantics are surfaced for approval, matching the target's open questions, though the legacy deprecation-period question is not explicitly raised.

### gpt · high (None, None) — handoff quality 70

- Plan coverage: None · Documentation boundary: None · Testing boundary: None
- Task self-contained: no · Broad rediscovery: no
- Lost facts or decisions: none
- Invented scope or decisions: none
- Missing outcomes: none

> Outcome coverage is complete and the important crossing is owned by named production-build checks (030's real build and inspection, 040's executable generated-output assertions including legacy-compatibility fixtures while the transition branch is enabled, and a post-rejection rebuild). The partition, however, shifts the target's boundaries materially: the normalization delivery is fused with content/tool migration in 020 (losing the accept-before-migrate checkpoint and forcing 030 to depend on 020), a standalone contract phase (010) and a documentation-only child (050) hang off the tree, and 040 builds the migration-wide executable test suite that belongs with the deliveries it verifies — the exact horizontal-test, documentation, and evidence patterns the target flags. The content-before-templates ordering is safe only if normalization preserves the legacy author view, which the tasks never state. The retirement gate itself is properly evidence-based and the three contract decisions are surfaced for approval.

### gpt · xhigh (None, None) — handoff quality 78

- Plan coverage: None · Documentation boundary: None · Testing boundary: None
- Task self-contained: no · Broad rediscovery: no
- Lost facts or decisions: none
- Invented scope or decisions: none
- Missing outcomes: none

> This set uses the target's sanctioned combination well: 020 fuses normalization with generated-surface adoption while keeping legacy fixtures building, so AUTHOR-D1 and AUTHOR-D2 are covered without an overpacked task, and evidence stays with the deliveries (build assertions in 020, content evidence in 030, helper tests plus real-build checks in 040). Two boundary defects remain: a standalone contract/inventory phase (010) ahead of the normalization delivery, and the content/tooling split (030/040) the target names as fragmentation. The declared graph also permits content conversion (030) to run before the normalization boundary (020) exists, since 030 depends only on the 010 contract — a missing dependency permitting a broken intermediate state. Outcome coverage is complete, the retirement is properly evidence-gated with a negative rejection regression, and the crossing is owned by named real-build checks at every migration state.

### gpt · max (None, None) — handoff quality 82

- Plan coverage: None · Documentation boundary: None · Testing boundary: None
- Task self-contained: no · Broad rediscovery: no
- Lost facts or decisions: none
- Invented scope or decisions: none
- Missing outcomes: none

> Four of five tasks map 1:1 onto the target's deliverables with no phase children among them: normalization+compatibility with a real legacy build (010), combined content+tool migration (020), one combined rendering task (030), and a conditional, evidence-gated retirement with final documentation (050). The single structural defect is 040, a horizontal evidence task that writes the executable build-boundary tests the 020/030 deliveries should carry — the exact pattern the target flags — while its dependency inventory is legitimately AUTHOR-D4 gate input. The graph leaves content and template migration unordered after 010, leaving an intermediate-output window guarded only by an unstated normalization behavior. Coverage is complete, the crossing is owned by named real-build checks at every state (legacy build in 010, helper output through the real build in 020, generated-output assertions in 030/040, post-rejection rebuild in 050), and the conditional retirement plus the external-consumer deprecation question align with the target's open questions.
