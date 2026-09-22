# Task-creation semantic assessment

- Assessor: `glm-5.3-flash:cloud` (effort max) · run `20260919T223954.765235Z-task-guidance-semantic-tg06-eleventy-author-migration-decomposition-83cfec7b`
- Assessor config: [glm-assessor-max.json](../../../shared/configs/glm-assessor-max.json)
- Assessor system message: [glm-assessor-max-3d0be6dc03e9.md](../../../shared/system-messages/glm-assessor-max-3d0be6dc03e9.md) (original SHA-256 `8fa068030ee99793…`)
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

### glm · max (None, None) — handoff quality 92

- Plan coverage: None · Documentation boundary: None · Testing boundary: None
- Task self-contained: no · Broad rediscovery: no
- Lost facts or decisions: none
- Invented scope or decisions: none
- Missing outcomes: none

> One task per compatibility state (dual-read adoption, content/tooling migration, evidence-gated rejection) matches the target's acceptable 3-task partition via its explicitly blessed normalization+surface merge; 000-main.md is coordination only. Each completion state requires a green production build with recorded evidence, tests and documentation live inside the deliverables that own them, and the rejection gate is encoded structurally as 030's dependency plus a blocking checklist. Decisive crossing evidence is named at every state: exact-string page/feed/archive assertions from real Eleventy builds, temp-copy multi-author fixtures through the real pipeline, and a real-build legacy-rejection test. No fragmentation, phase-only, layer, evidence-reownership, dependency, or piecewise-evidence issues found.

### gpt · high (None, None) — handoff quality 82

- Plan coverage: None · Documentation boundary: None · Testing boundary: None
- Task self-contained: no · Broad rediscovery: no
- Lost facts or decisions: none
- Invented scope or decisions: none
- Missing outcomes: none

> All five outcomes are covered with correct dependencies and decisive real-build evidence (020 explicitly forbids mocked template data; 040 requires production-build artifact assertions plus a legacy fixture before cutover and a failure check after). The single defect is partition alignment: the target's content+tools deliverable is split, with the content rewrite fused into the schema/normalization task and the helper update isolated in 030, so AUTHOR-3 has no single owning task and D1's pre-migration acceptance state is hidden. The cutover task delivers the rejection itself, so no phase-only or evidence-reownership issue arises.

### gpt · xhigh (None, None) — handoff quality 80

- Plan coverage: None · Documentation boundary: None · Testing boundary: None
- Task self-contained: no · Broad rediscovery: no
- Lost facts or decisions: none
- Invented scope or decisions: none
- Missing outcomes: none

> Coverage is broad and the surface (020) and cutover (030) tasks are coherent with real-build crossing evidence and a properly gated rejection, but 010 fuses the normalization deliverable with the whole content-and-tooling migration. Because content is migrated to `authors` while templates still read legacy `author`, and rendered acceptance is explicitly deferred to 020, the 010-to-020 seam permits an intermediate revision that publishes output without author values unless an unstated backward adapter exists — a material unsafe intermediate state. Splitting 010 or requiring the back-fill would resolve it; fragmentation stays low since the remaining structure is sound.

### gpt · max (None, None) — handoff quality 82

- Plan coverage: None · Documentation boundary: None · Testing boundary: None
- Task self-contained: no · Broad rediscovery: no
- Lost facts or decisions: none
- Invented scope or decisions: none
- Missing outcomes: none

> All outcomes are covered and the state chain is sound under the documented order (boundary+helper, then templates over still-legacy content via normalization, then content migration, then gated retirement), with real-build artifact assertions across pages/archives/feed/sitemap and a production-path negative rejection check giving decisive crossing evidence. Two defects lower the partition: the content+tools deliverable is split between the helper update in 010 and the content rewrite in 030, and 030 omits its dependency on 020, so the graph alone permits a canonical-content/legacy-template state that would publish output without author values. No phase-only, layer-split, or evidence-reownership issues.
