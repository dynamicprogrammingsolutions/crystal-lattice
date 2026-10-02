# Session — tg06-eleventy-author-migration-decomposition · task-creation-assessment-gpt-xhigh-s0 · glm max

- Run: `20260924T194142.737223Z-task-guidance-semantic-tg06-eleventy-author-migration-decomposition-gpt-xhigh-s0-ee2a0c41`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `544361e697d20601…`)
- Config: [glm-assessor-max](../../../../../../shared/configs/glm-assessor-max.json)
- Activity: 3 messages · 0 tool calls · 0 tool results
- Usage: unknown — saved session contains no provider usage metadata

## Transcript

**User**

Assess the task set produced for one fixed scenario. Use the reviewed
target, not raw task count, as the authority.

Judge whether the task set preserves approved outcomes and partitions work
into coherent deliverables. A technical layer is a valid separate task only
when completion leaves an independently usable, acceptable, deferable, owned,
or reviewable result. Identify subtasks that are merely phases or layer
fragments and could merge without losing independent value. Also identify
overpacked tasks that hide several independent deliverables.

The natural user request is part of the authority. Do not label behavior
explicitly requested there or listed in approved outcomes as added scope.
A coordinating parent file such as `000-main.md` is not an implementation
deliverable: exclude it from `actual_task_count`, fragmentation ratio, and
unmatched tasks unless it contains separately assigned implementation work.
For `crossing_ownership`, apply the target's exact `important_crossings`.
Separate mocked component tests and direct route/helper tests do not prove a
required production connection. Mark the crossing complete only when the task
names at least one check through that exact connection; otherwise mark it
partial or missing and explain the gap.

Do not reward verbosity, exact filenames, or matching the target's task count
mechanically. Do not penalize an acceptable alternative partition described by
the target. Treat tests, documentation, implementation, review, and deployment
as work within a deliverable unless their result is independently required.

Assess these issue dimensions separately:

- `fragmentation`: the overall mismatch between actual tasks and coherent
  deliverables;
- `phase_only_children`: implementation, testing, documentation, deployment,
  cleanup, or review children that only complete another delivery;
- `layer_split_without_independent_value`: frontend, backend, transport,
  storage, or package children that lack independent users, ownership,
  compatibility, acceptance, or a complete product outcome;
- `evidence_reownership`: a final integration, verification, or documentation
  child re-owning evidence that belongs with outcome-delivery children;
- `unsafe_dependencies`: missing, unnecessary, or wrong dependencies that
  permit a broken intermediate state or serialize independently deliverable
  work;
- `piecewise_crossing_evidence`: separate mocks, component checks, direct
  routes, or helper tests without one decisive check through the required
  production connection.

For fragmentation use `none|low|medium|high`. For every other dimension use
`none|partial|present`. `none` means the issue is absent, `partial` means a
limited or incomplete instance, and `present` means a material instance.
List concrete occurrences separately. Do not invent numeric scores; the
evaluator derives them deterministically from these statuses.

Return JSON only with this shape:

{
  "schema_version": 3,
  "scenario_id": "tg06-eleventy-author-migration-decomposition",
  "assessment": {
    "outcome_coverage": "complete|partial|poor",
    "missing_outcomes": ["OUTCOME-ID"],
    "added_obligations": ["description"],
    "semantic_deliverable_count": 0,
    "actual_task_count": 0,
    "deliverable_mappings": [
      {
        "deliverable_id": "target id",
        "task_paths": ["tasks/..."],
        "coverage": "complete|partial|missing",
        "coherence": "coherent|fragmented|overpacked",
        "reason": "short evidence"
      }
    ],
    "mergeable_groups": [
      {"task_paths": ["tasks/..."], "reason": "why these are one deliverable"}
    ],
    "unmatched_tasks": ["tasks/..."],
    "overpacked_tasks": ["tasks/..."],
    "valid_layer_boundaries": ["tasks/..."],
    "automatic_layer_fragments": ["tasks/..."],
    "dependency_issues": ["description"],
    "crossing_ownership": "complete|partial|missing",
    "fragmentation_severity": "none|low|medium|high",
    "fragmentation_ratio": 0.0,
    "quality_metrics": {
      "fragmentation": {
        "status": "none|low|medium|high",
        "occurrences": [
          {
            "task_paths": ["tasks/..."],
            "description": "concrete occurrence"
          }
        ]
      },
      "phase_only_children": {
        "status": "none|partial|present",
        "occurrences": []
      },
      "layer_split_without_independent_value": {
        "status": "none|partial|present",
        "occurrences": []
      },
      "evidence_reownership": {
        "status": "none|partial|present",
        "occurrences": []
      },
      "unsafe_dependencies": {
        "status": "none|partial|present",
        "occurrences": []
      },
      "piecewise_crossing_evidence": {
        "status": "none|partial|present",
        "occurrences": []
      }
    },
    "partition_quality_score": 0,
    "handoff_quality_score": 0,
    "summary": "concise evidence-based interpretation"
  }
}

Scores are integers from 0 through 100. `fragmentation_ratio` is actual task
files divided by the semantic coherent-deliverable count, or 0 when no
deliverable exists; it is descriptive rather than decisive.

Reviewed target:

{
  "acceptable_alternatives": [
    "Combine normalization and generated-surface adoption when a clear dual-format working state remains.",
    "Split content migration only for independently owned content collections."
  ],
  "acceptable_partition_sizes": [
    3,
    4,
    5
  ],
  "approved_outcomes": [
    {
      "id": "AUTHOR-1",
      "outcome": "Legacy single-author and structured one-or-more-author metadata normalize to one documented internal representation during migration."
    },
    {
      "id": "AUTHOR-2",
      "outcome": "Pages, archives, feeds, and metadata render equivalent single-author behavior and approved multi-author behavior from the normalized model."
    },
    {
      "id": "AUTHOR-3",
      "outcome": "Content and authoring tools migrate safely to the structured form."
    },
    {
      "id": "AUTHOR-4",
      "outcome": "Legacy form is retired only after no maintained source or generated surface depends on it."
    },
    {
      "id": "AUTHOR-5",
      "outcome": "Every intermediate revision builds and publishes valid output."
    }
  ],
  "category": "decomposition",
  "coherent_deliverables": [
    {
      "dependencies": [],
      "id": "AUTHOR-D1",
      "independent_value": "The site can safely accept old and new content before consumers or content migrate.",
      "outcomes": [
        "AUTHOR-1",
        "AUTHOR-5"
      ],
      "title": "Introduce dual-format normalization and compatibility"
    },
    {
      "dependencies": [
        "AUTHOR-D1"
      ],
      "id": "AUTHOR-D2",
      "independent_value": "All public output uses one stable internal representation while both source formats remain valid.",
      "outcomes": [
        "AUTHOR-2",
        "AUTHOR-5"
      ],
      "title": "Move generated surfaces to the normalized model"
    },
    {
      "dependencies": [
        "AUTHOR-D1"
      ],
      "id": "AUTHOR-D3",
      "independent_value": "Maintained producers and content stop creating new legacy dependencies.",
      "outcomes": [
        "AUTHOR-3",
        "AUTHOR-5"
      ],
      "title": "Migrate content and authoring tools"
    },
    {
      "dependencies": [
        "AUTHOR-D2",
        "AUTHOR-D3"
      ],
      "id": "AUTHOR-D4",
      "independent_value": "The migration completes only after direct content and generated-output evidence makes removal safe.",
      "outcomes": [
        "AUTHOR-4",
        "AUTHOR-5"
      ],
      "title": "Retire the legacy author form after evidence"
    }
  ],
  "fragmentation_examples": [
    "Parser and schema tasks separated from compatibility delivery.",
    "Page, archive, and feed templates each becoming a task.",
    "Content rewrite and authoring helper updates split without ownership.",
    "Unit tests, build tests, documentation, cleanup, and final review as horizontal tasks."
  ],
  "handoff": {
    "fresh_agent_plan": "A fresh agent reconstructs compatible working states and does not create a task per surface or test type.",
    "omit_plan": "Preserve current consumers/producers, compatibility constraints, public questions, and source pointers without the four-stage migration direction.",
    "retain_plan": "Preserve working migration states, rollback assumptions, dependencies, and direct retirement evidence."
  },
  "important_crossings": [
    "Real front matter flows through normalization and the production Eleventy build into pages, archives, and feeds at every migration state."
  ],
  "open_questions": [
    "Stable author identifier format and legacy deprecation period require approval."
  ],
  "overpacking_examples": [
    "One atomic change across content, normalization, templates, feeds, tooling, and rejection removes the safe compatibility window."
  ],
  "project": {
    "fixture_id": "tg06-eleventy-author-migration",
    "kind": "static content site and authoring tooling",
    "name": "Eleventy author metadata migration fixture",
    "revision": "26b26106d7fbb30b7b40d9ef52589d10ddbcb462",
    "upstream": "https://github.com/11ty/eleventy-base-blog"
  },
  "scenario_id": "tg06-eleventy-author-migration-decomposition",
  "schema_version": 1,
  "task_summary": "Partition a broad content/build migration by compatible working states rather than files and phases.",
  "title": "Eleventy author metadata migration decomposition"
}

Natural user request:

Migrate post author metadata from the current single-name field to a structured multi-author form without breaking existing content or generated pages during the transition. Templates, archives, feeds, and authoring tools must move to the new model, existing posts must be migrated safely, and the legacy form may be rejected only after generated-output and content evidence show that nothing still depends on it. Plan the work and create the appropriate task structure without implementing it.

Subject material:

{
  "response": "Created a Draft task plan with a parent task and three dependent subtasks. No application, content, test, or documentation implementation was performed.\n\n- [Main migration plan](<.../workspace/tasks/20260920-author-metadata-migration/000-main.md>)\n- [010 \u2014 Source contract and content migration](<.../workspace/tasks/20260920-author-metadata-migration/010-source-contract-and-content-migration.md>)\n- [020 \u2014 Rendering, archives, and feeds](<.../workspace/tasks/20260920-author-metadata-migration/020-rendering-and-output-surfaces.md>)\n- [030 \u2014 Evidence-gated legacy rejection](<.../workspace/tasks/20260920-author-metadata-migration/030-cutover-evidence-and-legacy-rejection.md>)\n\nThe plan explicitly preserves legacy compatibility during transition and postpones rejection until both source/content inventory and real generated-output evidence confirm that the old form is no longer depended on. It also records the unresolved public-contract decisions around the canonical schema, multi-author formatting, feed serialization, and rejection boundary.",
  "task_files": {
    "tasks/20260920-author-metadata-migration/000-main.md": "# Migrate post author metadata to a structured multi-author form\n\nPlan the staged migration from the post front matter `author` string to a\nstructured multi-author contract across source content, authoring tools,\ntemplates, archives, feeds, and the legacy-field cutover.\n\n## Requirements checklist\n\n- [ ] Define and adopt one canonical structured multi-author representation for\n  post metadata.\n- [ ] Keep existing legacy-author content buildable and renderable during the\n  migration transition, without breaking existing generated pages or feeds.\n- [ ] Move post templates, archive/list paths, and feed generation to consume\n  the canonical author representation.\n- [ ] Update the post authoring helper to emit the canonical representation and\n  support the approved multi-author input.\n- [ ] Migrate every existing post safely, preserving its current author data and\n  preventing dropped, duplicated, or reordered authors.\n- [ ] Reject the legacy single-name form only after content inventory and\n  generated-output evidence show that no supported source or output path still\n  depends on it.\n- [ ] Record the current authoring contract and the completed cutover in the\n  maintained documentation, without documenting target behavior as current\n  before implementation is complete.\n\n## Unresolved requirement questions and decisions\n\n- **Requirement question \u2014 canonical schema:** What is the exact field name and\n  element shape? For example, should the field be an array of display-name\n  strings or an array of author objects with stable identifiers and names?\n  This changes front matter, the authoring helper API, and every renderer.\n- **Requirement question \u2014 rendered form:** How should one and multiple authors\n  appear on post pages, archive/list views, and the feed? The migration should\n  preserve the current one-name presentation where applicable, but the\n  separator, ordering, and feed serialization for multiple authors need\n  approval.\n- **Requirement question \u2014 compatibility boundary:** During transition, should\n  legacy `author` be normalized in Eleventy data, accepted only by the\n  authoring tool, or accepted by both? The final rejection point and its error\n  message should be explicit before implementation.\n- **Decision:** Use separate source migration, output migration, and\n  evidence-gated rejection boundaries. No rejection should be enabled merely\n  because the new field exists.\n- **Decision:** Do not add author identity pages, profile URLs, or a new\n  persistent author registry unless the schema decision explicitly requires\n  them.\n\n## Scope and workstreams\n\nThe work is decomposed into three dependent subtasks:\n\n1. Establish the source contract, authoring-tool behavior, and migrated post\n   content.\n2. Convert every production output surface that consumes or exposes author\n   metadata.\n3. Prove that the legacy form is unused, then enable its rejection and record\n   the final supported contract.\n\nThis planning task does not modify application code, content, generated\noutput, tests, or maintained documentation.\n\n## Research and supporting facts\n\n- The two existing post sources,\n  `content/posts/first.md` and `content/posts/second.md`, use quoted scalar\n  `author` values.\n- `scripts/new-post.js` emits the legacy `author` front matter and accepts one\n  author argument.\n- `_includes/layouts/post.njk` renders `author` directly.\n- `content/feed.xml.njk` reads `post.data.author` directly.\n- The home page, blog archive, and tag pages all use\n  `_includes/postslist.njk`; that shared list currently renders only title and\n  URL, so its author behavior must be reviewed as the archive integration\n  point even though it has no direct legacy-field reference today.\n- `content/posts/posts.json` supplies the shared post layout and `posts` tag;\n  there is no separate author data collection or author registry.\n- `tests/author-output.test.js` and `tests/archive-output.test.js` contain\n  comments describing intended coverage but no assertions, so they are not\n  evidence for the migration or the cutover gate.\n- The repository has no authoring or front matter guide beyond the general\n  `README.md`; documentation should remain small and owned by the site\n  package.\n\n## Subtasks\n\n- [ ] [tasks/20260920-author-metadata-migration/010-source-contract-and-content-migration.md](tasks/20260920-author-metadata-migration/010-source-contract-and-content-migration.md)\n- [ ] [tasks/20260920-author-metadata-migration/020-rendering-and-output-surfaces.md](tasks/20260920-author-metadata-migration/020-rendering-and-output-surfaces.md)\n- [ ] [tasks/20260920-author-metadata-migration/030-cutover-evidence-and-legacy-rejection.md](tasks/20260920-author-metadata-migration/030-cutover-evidence-and-legacy-rejection.md)\n\n## Execution plan\n\nStatus: Draft\n\nExecute the subtasks in numeric order after the unresolved schema,\npresentation, and compatibility questions are approved. Keep the old input\nreadable until the final evidence gate; the new field must be exercised through\nthe actual Eleventy build rather than through isolated template mocks.\n\nThe first workstream establishes the canonical source representation,\nnormalizes legacy input for the transition if that is the approved boundary,\nupdates `scripts/new-post.js`, and migrates every existing post. The second\nworkstream updates the post layout, shared archive/list path, and feed to use\nthe canonical data while preserving the established output for the existing\nsingle-author posts. It also adds coverage for multiple authors and for all\narchive entry points. The last workstream inventories source references,\nbuilds the site, inspects generated post/archive/feed output, and only then\nenables a clear failure for remaining legacy input.\n\n### Implementation decisions and open questions\n\n- The staged compatibility decision is approved for planning: migration and\n  rendering must be independently verifiable before legacy rejection.\n- The exact field/schema, multi-author display/serialization, and enforcement\n  boundary remain open requirement questions. Resolve them before changing the\n  requirements checklist or marking execution approved.\n- The final rejection must be exercised through the real authoring/build path;\n  a test that bypasses front matter parsing or supplies already-normalized\n  data is not decisive.\n\n### Documentation\n\nUpdate `README.md` or the smallest more appropriate package-owned guide with\nthe canonical front matter example, authoring-tool input, transition status,\nand final rejection behavior. Do not describe legacy rejection as current\nuntil the evidence gate passes. No new documentation directory or placeholder\npage is needed.\n\n### Task checklist\n\n- [ ] Resolve the canonical schema, presentation, and compatibility-boundary\n  questions.\n- [ ] Approve this plan and mark it `Approved` before execution.\n- [ ] Complete\n  `010-source-contract-and-content-migration.md`.\n- [ ] Complete `020-rendering-and-output-surfaces.md` against the production\n  build.\n- [ ] Complete `030-cutover-evidence-and-legacy-rejection.md`.\n- [ ] Update maintained authoring documentation after the supported behavior is\n  true.\n- [ ] Record implementation and completion notes with evidence in this task\n  file and its subtasks.\n\n### Requirement verification\n\n- **Canonical representation and authoring tool:** Verify the approved field\n  shape in every migrated post, invoke the real `scripts/new-post.js` export\n  with one and multiple authors, and parse the resulting front matter through\n  the normal Eleventy input path.\n- **Transition compatibility:** Build with a representative legacy fixture\n  before the final cutover and assert that the post page and feed still\n  contain the same author information and valid output.\n- **Output migration:** Run the production build and inspect a post page, home\n  page, blog archive, tag archive, and feed. Assert that each author-bearing\n  surface is derived from canonical data and that multiple authors are\n  complete, ordered, and serialized according to the approved contract.\n- **Existing-content migration:** Inventory all post front matter, compare the\n  pre-migration author values with the canonical values, and build the full\n  site to catch malformed metadata.\n- **Legacy rejection gate:** Require both a repository/content scan with no\n  supported legacy inputs and generated-output checks showing no legacy data\n  path remains before asserting that legacy input fails. Keep a focused\n  negative test for the final rejection.\n- **Documentation:** Review the maintained guide against the behavior proven\n  by the final build and tests.",
    "tasks/20260920-author-metadata-migration/010-source-contract-and-content-migration.md": "# Establish the structured author contract and migrate source content\n\nDefine the canonical post metadata shape, move the authoring helper to that\nshape, and migrate existing post front matter while preserving all author\ninformation during the compatibility window.\n\nParent Task: tasks/20260920-author-metadata-migration/000-main.md\n\nDepends On: None\n\n## Requirements checklist\n\n- [ ] The approved structured multi-author schema is documented as the\n  canonical post input contract.\n- [ ] `scripts/new-post.js` accepts the approved multi-author input and emits\n  valid canonical front matter for one and multiple authors.\n- [ ] Every existing post is migrated without losing, duplicating, or\n  reordering author data.\n- [ ] Legacy source data remains normalizable or otherwise supported at the\n  approved transition boundary until the cutover subtask supplies its evidence.\n\n## Unresolved requirement questions and decisions\n\n- The parent task's canonical field name, element shape, and authoring-helper\n  API must be resolved before execution; this subtask must not invent them.\n- The transition behavior for a legacy scalar is a parent-level compatibility\n  decision. If normalization is selected, define whether it produces a\n  one-element canonical list and where that normalization occurs.\n\n## Research and supporting facts\n\n- `content/posts/first.md` contains the author value `Ada Example`.\n- `content/posts/second.md` contains the author value `Grace Example`.\n- `scripts/new-post.js` currently has the signature\n  `frontMatter(title, author)` and writes `author: \"...\"`.\n- `content/posts/posts.json` does not define or transform author metadata, so\n  the source contract cannot currently be delegated to a collection data\n  file.\n\n## Execution plan\n\nStatus: Draft\n\nAfter the parent questions are approved, define the canonical representation\nand the compatibility normalization boundary. Update the authoring helper to\nproduce that representation for one and multiple authors, including safe\nquoting/escaping for names. Migrate the two existing post files and any\nadditional post files discovered by the content inventory. Preserve author\norder and compare the old scalar values with the migrated one-author values.\n\nAdd focused source-level evidence for the helper output and content inventory,\nbut leave final acceptance of rendered pages and the legacy rejection to the\ndependent subtasks. If the chosen transition strategy needs Eleventy data\nnormalization or validation, keep that logic at the agreed source/build\nboundary and document its lifetime so it can be removed or disabled at\ncutover.\n\n### Implementation decisions and open questions\n\n- Keep the migration lossless: existing one-author values become exactly one\n  canonical author entry, with no implicit author identity or link creation.\n- Resolve any escaping or malformed-input behavior as part of the approved\n  front matter contract; do not silently invent fallback authors.\n- The compatibility adapter, if used, must be exercised with an actual legacy\n  post and must remain available until subtask 030 closes the evidence gate.\n\n### Documentation\n\nProvide the canonical front matter and authoring-helper examples to the\nparent's package documentation plan. Do not publish the legacy rejection rule\nfrom this subtask while the output and content evidence is incomplete.\n\n### Task checklist\n\n- [ ] Confirm the approved canonical schema and helper API.\n- [ ] Define and implement the transition normalization/validation boundary.\n- [ ] Update the authoring helper for one and multiple authors.\n- [ ] Inventory and migrate all existing post front matter.\n- [ ] Add focused source/content evidence and pass it through the normal\n  parsing boundary.\n- [ ] Update this subtask with implementation and completion notes after\n  execution.\n\n### Requirement verification\n\n- **Canonical source contract:** Parse generated helper output and each\n  migrated post through the actual Eleventy input path; assert the canonical\n  field and exact author list.\n- **Authoring tool:** Exercise one-author and multiple-author calls,\n  including names requiring front matter quoting/escaping, and assert valid\n  output without relying on a hand-constructed fixture.\n- **Lossless migration:** Compare the complete pre-migration author inventory\n  with the canonical post inventory, including count and order.\n- **Transition support:** Build or parse a real legacy-form fixture at the\n  selected compatibility boundary and verify it normalizes to the same data\n  as its migrated equivalent.",
    "tasks/20260920-author-metadata-migration/020-rendering-and-output-surfaces.md": "# Move author rendering across pages, archives, and feeds\n\nConvert the production templates and all archive/list entry points to consume\nthe structured author collection, while preserving generated output for\nexisting one-author posts and defining deterministic multi-author output.\n\nParent Task: tasks/20260920-author-metadata-migration/000-main.md\n\nDepends On: tasks/20260920-author-metadata-migration/010-source-contract-and-content-migration.md\n\n## Requirements checklist\n\n- [ ] The post layout renders authors from the canonical structured field.\n- [ ] The shared archive/list path and its home, blog, and tag-page consumers no\n  longer depend on the legacy field when author data is rendered or exposed.\n- [ ] The feed renders the canonical author data according to the approved\n  feed representation.\n- [ ] Legacy-form input remains renderable during the approved transition\n  window, if the parent compatibility decision requires it.\n- [ ] One-author output remains compatible with the current generated pages,\n  while multiple authors are complete and deterministic.\n\n## Unresolved requirement questions and decisions\n\n- The parent task must approve the visible multi-author formatting and the\n  feed serialization before this subtask can define exact assertions.\n- The current archive list renders only titles and URLs. Confirm whether the\n  migration should add an author byline there or only ensure that any existing\n  or newly exposed archive author data uses the canonical field.\n- Decide whether the feed emits one author element per author or one\n  serialized element, and preserve the existing feed contract for a\n  one-author post unless the approved migration explicitly changes it.\n\n## Research and supporting facts\n\n- `_includes/layouts/post.njk` currently prints `{{ author }}`.\n- `content/feed.xml.njk` currently prints `post.data.author` inside each\n  entry.\n- `content/index.njk`, `content/blog.njk`, and `content/tag-pages.njk` all\n  include `_includes/postslist.njk`.\n- `_includes/postslist.njk` currently prints only `post.data.title` and\n  `post.url`; it is the shared integration point for all three archive paths.\n- `tests/author-output.test.js` and `tests/archive-output.test.js` do not\n  currently run a build or assert generated output.\n\n## Execution plan\n\nStatus: Draft\n\nUsing the canonical field from subtask 010, update the post layout, shared\narchive/list rendering, and feed template. Keep compatibility handling at the\napproved boundary so templates do not each implement divergent legacy\nfallbacks. If archive bylines are part of the approved output, render them\nthrough one shared author formatter and exercise home, blog, and tag pages.\nIf archives intentionally remain title-only, verify they do not read the\nlegacy field and add coverage that the shared path remains safe with canonical\ndata.\n\nReplace the placeholder tests with production-build assertions. Build the\nsite using the normal Eleventy command, then inspect representative generated\npost, home, blog, tag, and feed files. Include a multi-author fixture or\nmigrated post so the tests prove list completeness, ordering, escaping, and\nfeed validity rather than only checking that files exist.\n\n### Implementation decisions and open questions\n\n- Centralize any presentation logic needed by several templates so post,\n  archive, and feed output cannot drift.\n- Do not remove transition support from templates until subtask 030 has\n  completed its source and generated-output evidence gate.\n- Resolve archive byline behavior and feed element shape before fixing exact\n  output assertions.\n\n### Documentation\n\nSupply the final visible/output examples and feed behavior to the parent\ndocumentation update. Do not document unverified generated output as a\nsupported contract.\n\n### Task checklist\n\n- [ ] Confirm archive presentation and feed serialization.\n- [ ] Update the post layout to consume canonical authors.\n- [ ] Update the shared archive/list integration and all archive consumers as\n  required by the approved output contract.\n- [ ] Update the feed to consume canonical authors.\n- [ ] Replace placeholder author/archive tests with production-build checks.\n- [ ] Verify legacy-form rendering during the transition.\n- [ ] Update this subtask with implementation and completion notes after\n  execution.\n\n### Requirement verification\n\n- **Post rendering:** Run the real build and assert the generated post page\n  contains the approved one- and multiple-author representation.\n- **Archive paths:** Inspect generated home, blog archive, and tag archive\n  pages and assert the shared list path is compatible with canonical author\n  data and has no legacy-field dependency.\n- **Feed:** Inspect the generated feed XML and assert every author is present,\n  ordered, escaped, and serialized according to the approved contract.\n- **Transition:** Build with a real legacy-form post before cutover and\n  compare its author output with the equivalent canonical post.\n- **Regression:** Confirm existing titles, URLs, post bodies, and one-author\n  author output remain intact in the generated files.",
    "tasks/20260920-author-metadata-migration/030-cutover-evidence-and-legacy-rejection.md": "# Prove migration completeness and reject the legacy author form\n\nOwn the final compatibility gate: establish that source content and generated\noutputs no longer depend on the single-name field, then enable and verify\nlegacy-form rejection.\n\nParent Task: tasks/20260920-author-metadata-migration/000-main.md\n\nDepends On:\ntasks/20260920-author-metadata-migration/010-source-contract-and-content-migration.md\ntasks/20260920-author-metadata-migration/020-rendering-and-output-surfaces.md\n\n## Requirements checklist\n\n- [ ] A complete content/source inventory shows no supported post still relies\n  on the legacy single-name field.\n- [ ] A clean production build and generated-output inspection show that post\n  pages, home/blog/tag archives, and feeds do not depend on the legacy field.\n- [ ] Transition compatibility is retained until both evidence conditions pass.\n- [ ] After the evidence gate passes, the approved boundary rejects legacy\n  input with a clear actionable error.\n- [ ] The final documentation describes only the now-supported canonical form\n  and the verified rejection behavior.\n\n## Unresolved requirement questions and decisions\n\n- The exact enforcement boundary remains the parent-level requirement\n  question: authoring helper, front matter validation, Eleventy build, or a\n  combination. The chosen boundary must cover all supported authoring paths.\n- Decide whether a legacy-field negative test remains permanently as regression\n  coverage after rejection; the recommended approach is yes, because it\n  protects the compatibility contract.\n\n## Research and supporting facts\n\n- The repository currently has two post files and both use `author`; the\n  content inventory must be rerun after migration rather than assuming this\n  remains the complete set.\n- Existing generated-output tests are placeholders, so current test names\n  cannot serve as the evidence gate.\n- The build output directory is `_site`, and the normal build command is\n  `npm run build`.\n- The legacy field is currently consumed directly by the post layout and feed;\n  any remaining reference or fallback must be classified as intentional\n  transition code before rejection.\n\n## Execution plan\n\nStatus: Draft\n\nFirst run a repository/content inventory that distinguishes migrated source,\nintentional compatibility code, tests, documentation, and generated output.\nThen run the production build with representative migrated and\nmultiple-author content and inspect all author-bearing output surfaces from\nsubtask 020. Repeat with a real legacy fixture while compatibility is still\nenabled. Record the commands and decisive assertions in the implementation\nnotes so the cutover is auditable.\n\nOnly when the inventory and generated-output checks are both clean, enable the\napproved legacy rejection at the agreed boundary. Add a negative test that\npasses legacy input through the actual supported path and asserts the clear\nfailure. Remove obsolete compatibility branches only after that test and the\nfull production build pass; retain intentional historical migration evidence\nas documentation or test data without allowing it as supported input.\n\n### Implementation decisions and open questions\n\n- The rejection gate is a hard dependency, not a cleanup step: no legacy\n  rejection may ship on source inspection alone.\n- Generated-output evidence must cross the Eleventy build boundary and include\n  the public page/archive/feed paths, not just inspect template source.\n- Resolve the enforcement boundary before execution and do not broaden it to\n  reject unrelated unknown metadata.\n\n### Documentation\n\nUpdate the package-owned authoring guidance only after the gate passes. State\nthe canonical field, accepted multi-author shape, authoring-helper usage, and\nthe legacy-field rejection with an example of the supported replacement. If\nthe project retains migration notes, label them as historical rather than\nsupported input instructions.\n\n### Task checklist\n\n- [ ] Confirm the enforcement boundary and permanent negative-test policy.\n- [ ] Inventory source/content and classify every remaining legacy reference.\n- [ ] Run clean production-build and generated-output evidence.\n- [ ] Verify transition compatibility before rejection.\n- [ ] Enable legacy rejection only after both evidence conditions pass.\n- [ ] Run the negative legacy-input test through the real supported path.\n- [ ] Run the full test suite and final production build.\n- [ ] Update maintained documentation and record immutable completion notes.\n\n### Requirement verification\n\n- **Content evidence:** Search all supported post sources and authoring\n  inputs, then parse the complete inventory through the normal build path.\n  The only remaining legacy references may be explicitly classified\n  migration fixtures or historical documentation.\n- **Generated-output evidence:** Build from migrated content and inspect\n  generated post, home, blog, tag, and feed files for complete canonical\n  author output and absence of legacy-dependent rendering.\n- **Transition ordering:** Demonstrate that the legacy fixture succeeds before\n  the gate and fails only after the clean inventory/build evidence is\n  recorded.\n- **Rejection:** Invoke the actual supported input/build path with a legacy\n  `author` field and assert a deterministic, actionable failure.\n- **Final regression:** Run `npm test` and `npm run build`, then verify the\n  generated pages and feed remain complete after compatibility code is\n  removed or disabled."
  },
  "task_tree": {
    "all_dependencies_resolve": true,
    "all_parent_links_resolve": true,
    "coordinating_files": [
      "tasks/20260920-author-metadata-migration/000-main.md"
    ],
    "dependencies": [],
    "files": [
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": null,
        "path": "tasks/20260920-author-metadata-migration/000-main.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 7,
        "title": "Migrate post author metadata to a structured multi-author form"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260920-author-metadata-migration/000-main.md",
        "path": "tasks/20260920-author-metadata-migration/010-source-contract-and-content-migration.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 4,
        "title": "Establish the structured author contract and migrate source content"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260920-author-metadata-migration/000-main.md",
        "path": "tasks/20260920-author-metadata-migration/020-rendering-and-output-surfaces.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Move author rendering across pages, archives, and feeds"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260920-author-metadata-migration/000-main.md",
        "path": "tasks/20260920-author-metadata-migration/030-cutover-evidence-and-legacy-rejection.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Prove migration completeness and reject the legacy author form"
      }
    ],
    "implementation_task_count": 3,
    "parent_links": [
      {
        "child": "tasks/20260920-author-metadata-migration/010-source-contract-and-content-migration.md",
        "parent": "tasks/20260920-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260920-author-metadata-migration/020-rendering-and-output-surfaces.md",
        "parent": "tasks/20260920-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260920-author-metadata-migration/030-cutover-evidence-and-legacy-rejection.md",
        "parent": "tasks/20260920-author-metadata-migration/000-main.md",
        "resolves": true
      }
    ],
    "phase_named_files": [],
    "task_directory_count": 1,
    "task_file_count": 4
  }
}


**Assistant** *(reasoning present)*

```json
{
  "schema_version": 3,
  "scenario_id": "tg06-eleventy-author-migration-decomposition",
  "assessment": {
    "outcome_coverage": "complete",
    "missing_outcomes": [],
    "added_obligations": [],
    "semantic_deliverable_count": 4,
    "actual_task_count": 3,
    "deliverable_mappings": [
      {
        "deliverable_id": "AUTHOR-D1",
        "task_paths": [
          "tasks/20260920-author-metadata-migration/010-source-contract-and-content-migration.md"
        ],
        "coverage": "partial",
        "coherence": "coherent",
        "reason": "Canonical contract, normalization boundary, and legacy acceptance-until-cutover are delivered, but collapsed into the same task as content migration; the pre-migration dual-format checkpoint (site accepts old and new content before consumers or content migrate) is never a separate delivery, and no task owns output validity at the 010 boundary."
      },
      {
        "deliverable_id": "AUTHOR-D2",
        "task_paths": [
          "tasks/20260920-author-metadata-migration/020-rendering-and-output-surfaces.md"
        ],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Post layout, shared archive/list path with its home/blog/tag consumers, and feed all move to the canonical model in one delivery, with one-author compatibility preserved and multi-author output made deterministic; verified through the real build."
      },
      {
        "deliverable_id": "AUTHOR-D3",
        "task_paths": [
          "tasks/20260920-author-metadata-migration/010-source-contract-and-content-migration.md"
        ],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Authoring helper update and lossless migration of every existing post are owned together with the source contract, matching D3's producer-plus-content scope with the compatibility window retained until 030."
      },
      {
        "deliverable_id": "AUTHOR-D4",
        "task_paths": [
          "tasks/20260920-author-metadata-migration/030-cutover-evidence-and-legacy-rejection.md"
        ],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Content inventory plus production-build generated-output evidence precede enabling rejection, with transition compatibility retained until both conditions pass; matches D4's hard evidence gate rather than treating removal as cleanup."
      }
    ],
    "mergeable_groups": [],
    "unmatched_tasks": [],
    "overpacked_tasks": [],
    "valid_layer_boundaries": [
      "tasks/20260920-author-metadata-migration/020-rendering-and-output-surfaces.md"
    ],
    "automatic_layer_fragments": [],
    "dependency_issues": [
      "Declared dependencies are correct and complete (020 depends on 010; 030 depends on 010 and 020, matching D2/D3/D4 ordering). The one gap is timing: 010 migrates all content to the canonical field while every template and the feed still read the legacy field, and no task owns keeping generated output valid between 010 and 020; the D1-style compatibility delivery before content migrates is absorbed rather than separately established."
    ],
    "crossing_ownership": "complete",
    "fragmentation_severity": "none",
    "fragmentation_ratio": 0.75,
    "quality_metrics": {
      "fragmentation": {
        "status": "none",
        "occurrences": []
      },
      "phase_only_children": {
        "status": "none",
        "occurrences": []
      },
      "layer_split_without_independent_value": {
        "status": "none",
        "occurrences": []
      },
      "evidence_reownership": {
        "status": "none",
        "occurrences": []
      },
      "unsafe_dependencies": {
        "status": "partial",
        "occurrences": [
          {
            "task_paths": [
              "tasks/20260920-author-metadata-migration/010-source-contract-and-content-migration.md",
              "tasks/20260920-author-metadata-migration/020-rendering-and-output-surfaces.md"
            ],
            "description": "After 010 completes, migrated canonical content flows to consumers that still render the legacy scalar field; 010's verification only parses through the Eleventy input path and explicitly defers rendered-page acceptance to 020, so the intermediate revision's published output validity is unowned, and the pre-migration dual-format checkpoint the target defines for D1 is not a separately delivered state."
          }
        ]
      },
      "piecewise_crossing_evidence": {
        "status": "none",
        "occurrences": []
      }
    },
    "partition_quality_score": 88,
    "handoff_quality_score": 90,
    "summary": "The three implementation tasks map cleanly onto the target's four deliverables: 010 carries both the source-side contract/normalization (D1) and the content/tooling migration (D3), 020 carries all generated surfaces (D2) bundled rather than split per template, and 030 carries the evidence-gated legacy rejection (D4). All five approved outcomes have owning tasks with verification plans; tests, documentation, and review sit inside their deliverables rather than as horizontal phase tasks, so there are no mergeable fragments and nothing overpacked. The required crossing is decisively owned: 020 and 030 both run the normal Eleventy build and inspect generated post, home/blog/tag, and feed output with real migrated, multi-author, and legacy front matter, explicitly rejecting mock-based or placeholder evidence. The single material weakness is sequencing: 010 lands canonical content while every consumer still reads the legacy field, no task keeps that intermediate revision's output valid, and the target's described acceptable merge pairs normalization with surface adoption rather than with content migration, so D1's independent pre-migration value is only partially preserved. Handoff is strong: unresolved schema, presentation, and compatibility-boundary questions, current consumers/producers with source pointers, and the evidence-gate ordering are preserved without leaking the target's four-stage direction or inducing per-surface/per-test task creation."
  }
}
```
