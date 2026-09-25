# Session — tg06-eleventy-author-migration-decomposition · task-creation-assessment-gpt-high-s0 · glm max

- Run: `20260924T193958.613671Z-task-guidance-semantic-tg06-eleventy-author-migration-decomposition-gpt-high-s0-19ed98dc`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `1f4c6b34038a880e…`)
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
  "response": "Created a Draft task handoff without implementing the migration:\n\n- [Main task](</Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T222223.796015Z-task-guidance-tg06-eleventy-author-migration-decomposition-high-da1d776b/workspace/tasks/20260919-author-metadata-migration/000-main.md>)\n- [Schema and content migration](</Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T222223.796015Z-task-guidance-tg06-eleventy-author-migration-decomposition-high-da1d776b/workspace/tasks/20260919-author-metadata-migration/010-schema-and-content-migration.md>)\n- [Generated consumers](</Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T222223.796015Z-task-guidance-tg06-eleventy-author-migration-decomposition-high-da1d776b/workspace/tasks/20260919-author-metadata-migration/020-generated-consumers.md>)\n- [Authoring tool](</Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T222223.796015Z-task-guidance-tg06-eleventy-author-migration-decomposition-high-da1d776b/workspace/tasks/20260919-author-metadata-migration/030-authoring-tool.md>)\n- [Legacy cutover evidence gate](</Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T222223.796015Z-task-guidance-tg06-eleventy-author-migration-decomposition-high-da1d776b/workspace/tasks/20260919-author-metadata-migration/040-legacy-cutover-evidence.md>)\n\nThe plan keeps the legacy field supported during migration and makes rejection a separate, evidence-gated compatibility change. It requires production-build assertions for posts, home/blog/tag archives, feeds, and the sitemap, plus a repository-wide dependency audit before cutover.\n\nThe Draft records these unresolved requirement decisions:\n\n- Exact canonical structured author shape.\n- Multi-author XML feed representation.\n- Behavior when both legacy and new fields are present.\n- The final legacy rejection/error contract.\n\nNo tests or builds were run because this request was limited to planning and task-file creation.",
  "task_files": {
    "tasks/20260919-author-metadata-migration/000-main.md": "# Migrate post author metadata to structured multi-author data\n\nPlan the transition from the single `author` front-matter string to an\nordered, structured multi-author model across source content, Eleventy\ntemplates, generated artifacts, and the post-authoring helper while preserving\nexisting content and public pages during the compatibility window.\n\n## Requirements checklist\n\n- [ ] Posts have a canonical structured representation that can express the\n      ordered authors for a post, including the current single-author cases.\n- [ ] Existing posts are migrated safely without losing titles, body content,\n      routes, tags, layout behavior, or author display data.\n- [ ] Post templates, home/blog/tag archive paths, and the feed consume the\n      canonical author model; generated pages and feed output remain valid and\n      preserve existing single-author behavior while representing multiple\n      authors according to the approved public contract.\n- [ ] The post-authoring helper emits the canonical metadata and no longer\n      requires callers to author the legacy single-name field.\n- [ ] The legacy field remains supported for the transition until source\n      content and generated-output evidence demonstrate that no dependency\n      remains; any rejection/removal is a separately verified final step.\n- [ ] Tests exercise the real Eleventy production build and the authoring\n      helper at the boundaries where the migration can regress.\n- [ ] Maintained user/developer guidance describes the supported authoring\n      format and transition state after implementation.\n\n## Scope and workstreams\n\nThe migration is organized into four dependent workstreams:\n\n1. Establish the canonical data shape, a transition normalizer/compatibility\n   policy, and migrate the checked-in posts.\n2. Move the post layout, shared archive rendering, and feed generation to the\n   canonical model while preserving public routes and valid output.\n3. Update the authoring helper and its contract so newly created posts use the\n   new model.\n4. Run the integrated source/output audit and authorize legacy rejection only\n   when the evidence gate passes.\n\nThe work includes the existing Eleventy source tree, checked-in post content,\nthe `scripts/new-post.js` helper, generated-output tests, and maintained\nguidance. It excludes unrelated archive pagination and unrelated upstream\nfixture changes.\n\n## Requirement questions and decisions\n\n- The request does not specify the exact structured schema. The recommended\n  direction is an ordered `authors` list whose entries carry at least a\n  display name, with one canonical internal representation for both migrated\n  single-author and new multi-author posts. Confirm whether author entries\n  need an identifier, URL, or other fields before implementation.\n- The request does not specify how multiple authors should appear in the XML\n  feed. Decide whether the feed should emit one `<author>` element per author\n  in source order or use another approved feed contract.\n- Decide whether a post containing both legacy `author` and canonical\n  `authors` is accepted during transition, and if so how conflicts are\n  detected or resolved. Do not silently define this compatibility behavior\n  during implementation.\n- The exact point at which legacy rejection is enabled is intentionally\n  evidence-driven. The cutover subtask must keep rejection disabled until the\n  source and generated-output checks pass and record the evidence used.\n\n## Supporting facts\n\n- `content/posts/first.md` and `content/posts/second.md` currently provide a\n  scalar `author` value; `content/posts/posts.json` supplies the post layout\n  and `posts` tag.\n- `_includes/layouts/post.njk` renders the legacy value directly.\n- `content/index.njk`, `content/blog.njk`, and `content/tag-pages.njk` share\n  `_includes/postslist.njk`; the current list exposes title and URL only, so\n  archive coverage must verify that moving author data does not alter list\n  routes, ordering, or rendering.\n- `content/feed.xml.njk` reads `post.data.author` directly and is the current\n  feed dependency on the legacy field.\n- `scripts/new-post.js` accepts `(title, author)` and writes scalar\n  `author` front matter.\n- `tests/author-output.test.js` and `tests/archive-output.test.js` currently\n  contain comments but no decisive assertions. `npm test` runs\n  `node --test tests/*.test.js`, while `npm run build` is the production\n  Eleventy boundary.\n- There is no `docs/index.md`; the maintained documentation currently\n  consists of `README.md` and `docs/development/index.md` plus the repository\n  guidance in `AGENTS.md`.\n\n## Execution plan\n\nStatus: Draft\n\nFirst agree the canonical schema and public feed semantics. Then implement the\nnormalization/migration boundary, update each production consumer, and update\nthe authoring helper. Keep the compatibility path active while the integrated\nbuild renders migrated and legacy-shaped fixtures. Finally audit source\nreferences and generated output, record the passing evidence, and only then\nenable legacy rejection as a separately reviewable cutover.\n\n### Implementation decisions and open questions\n\n- The canonical model must be ordered so author display and feed output are\n  deterministic.\n- Compatibility should be centralized at the data boundary rather than\n  duplicating legacy-field checks across templates.\n- The feed contract and dual-field behavior remain open until the requester\n  confirms them; they affect public output and validation behavior.\n- A source grep alone is not sufficient for cutover: the evidence must include\n  a successful production build and inspection/assertions over generated post,\n  archive, and feed artifacts.\n\n### Documentation\n\n- Update `README.md` or the owning developer documentation with the canonical\n  front-matter example, authoring-helper usage, and the transition/rejection\n  status once implementation makes those claims true.\n- Do not document legacy rejection as current behavior before the cutover\n  evidence gate is complete.\n- Keep migration-specific test and verification notes with this task or the\n  owning subtask; do not create placeholder documentation sections.\n\n### Task checklist\n\n- [ ] Complete `tasks/20260919-author-metadata-migration/010-schema-and-content-migration.md`.\n- [ ] Complete\n      `tasks/20260919-author-metadata-migration/020-generated-consumers.md`.\n- [ ] Complete\n      `tasks/20260919-author-metadata-migration/030-authoring-tool.md`.\n- [ ] Complete\n      `tasks/20260919-author-metadata-migration/040-legacy-cutover-evidence.md`.\n- [ ] Resolve the public schema and feed/dual-field requirement questions\n      before marking execution approved.\n- [ ] Keep this plan and child statuses synchronized as execution proceeds.\n\n### Requirement verification\n\n- Canonical metadata and safe source migration: the schema/content subtask\n  must show migrated post front matter plus a real Eleventy build that\n  renders the migrated posts without route, tag, body, or title loss.\n- Generated consumers: the generated-consumers subtask must assert post,\n  home/blog/tag archive, and feed artifacts from the production build,\n  including ordered multi-author behavior and preserved single-author output.\n- Authoring tool: the authoring-tool subtask must test the helper's generated\n  front matter through the same parsing/build path used by posts.\n- Legacy transition and rejection: the cutover subtask must show no remaining\n  legacy source dependencies, successful generated-output assertions, and an\n  explicit decision/evidence record before enabling rejection.\n\n### Additional implementation verification\n\n- Run the complete test command and production build after all subtasks are\n  integrated.\n- Inspect the build output for malformed markup, empty author values, and\n  accidental route changes.\n- Confirm the repository diff contains only the approved migration,\n  verification, and documentation changes.\n",
    "tasks/20260919-author-metadata-migration/010-schema-and-content-migration.md": "# Establish the structured author model and migrate posts\n\nDefine the canonical post metadata shape, centralize transition handling for\nthe legacy scalar field, and migrate the checked-in posts without changing\ntheir public identity or content.\n\nParent Task: tasks/20260919-author-metadata-migration/000-main.md\n\n## Requirements checklist\n\n- [ ] The canonical field and entry shape are approved and documented in the\n      implementation.\n- [ ] The model preserves author order and supports current single-author\n      posts as well as multiple authors.\n- [ ] Existing post front matter is migrated without changing title, body,\n      route, tags, or layout behavior.\n- [ ] Legacy `author` input remains readable during the transition through one\n      defined compatibility boundary.\n- [ ] Ambiguous dual-field behavior is resolved and covered before execution\n      marks this subtask complete.\n\n## Requirement questions and decisions\n\n- Confirm whether the canonical field is named `authors` and whether entries\n  are objects with a required `name`, or whether a different approved shape\n  is required.\n- Confirm whether author identity/URL fields are in scope now or should remain\n  absent until a later migration.\n- Confirm the behavior when both `author` and `authors` are present.\n\n## Supporting facts\n\n- Current source files are `content/posts/first.md`,\n  `content/posts/second.md`, and the cascade file\n  `content/posts/posts.json`.\n- Current source values are plain display-name strings, so migration must\n  preserve their exact visible names.\n- No data migration utility exists in the repository; the checked-in content\n  is small enough for a reviewed, explicit source migration once the schema is\n  approved.\n\n## Execution plan\n\nStatus: Draft\n\nAdd the canonical metadata contract at the narrowest data boundary available\nin the Eleventy fixture. During the compatibility window, normalize either\nthe new field or the approved legacy input into the same ordered author\ncollection consumed by templates. Migrate both checked-in posts to the new\nfront-matter shape and add focused fixtures for one and multiple authors.\nPreserve the legacy path until the separate cutover task authorizes rejection.\n\n### Implementation decisions and open questions\n\n- Keep normalization out of individual Nunjucks templates so every consumer\n  receives the same ordering and missing-data behavior.\n- Do not invent fallback names or silently merge conflicting fields; use the\n  approved dual-field policy once the requirement question is answered.\n- The source migration is complete only when a production build proves the\n  migrated documents still resolve to the same public routes.\n\n### Documentation\n\n- Add the canonical front-matter example to the owning authoring/developer\n  documentation as part of this subtask or coordinate that update with the\n  authoring-tool subtask.\n- Record the compatibility-window status, not final legacy rejection, until\n  the cutover evidence passes.\n\n### Task checklist\n\n- [ ] Confirm and record the canonical field/entry schema.\n- [ ] Implement the centralized compatibility normalization.\n- [ ] Migrate every checked-in post and preserve its existing metadata/body.\n- [ ] Add focused one-author and multi-author source fixtures.\n- [ ] Run the production build and verify routes/tags/content.\n\n### Requirement verification\n\n- Compare the migrated post metadata and rendered post artifacts against the\n  pre-migration title, URL, body, and visible author values.\n- Build at least one multi-author fixture and verify the normalized author\n  order reaches the rendering boundary.\n- Exercise a legacy-shaped fixture while compatibility is enabled to prove\n  existing content remains readable.\n\n### Additional implementation verification\n\n- Search all source/templates/scripts for direct legacy-field reads and\n  classify each remaining occurrence as compatibility code, test fixture, or\n  unresolved dependency.\n- Verify no migration step rewrites slugs, dates, tags, or post bodies.\n",
    "tasks/20260919-author-metadata-migration/020-generated-consumers.md": "# Move generated pages and feed consumers to structured authors\n\nUpdate production templates and generated-output coverage so post pages,\nshared archive paths, and the XML feed consume the canonical author\nrepresentation without breaking existing routes or valid output.\n\nParent Task: tasks/20260919-author-metadata-migration/000-main.md\nDepends On: tasks/20260919-author-metadata-migration/010-schema-and-content-migration.md\n\n## Requirements checklist\n\n- [ ] The post layout renders the canonical author data for one and multiple\n      authors.\n- [ ] Home, blog, and tag archive paths remain on the canonical data path and\n      preserve their existing title, URL, ordering, and markup behavior.\n- [ ] The feed emits valid, deterministic author output for the approved\n      multi-author contract and preserves the current single-author case.\n- [ ] Generated-output tests inspect artifacts from a real Eleventy build,\n      rather than supplying mocked post data directly to templates.\n- [ ] No production consumer depends on the legacy scalar field after the\n      compatibility boundary is in place.\n\n## Requirement questions and decisions\n\n- Confirm the public representation of multiple authors in the XML feed\n  (recommended default: one `<author>` element per ordered author, if valid\n  for the intended feed contract).\n- Confirm whether archive lists should display author names during this\n  migration or only stop depending on the old field. The current archive list\n  displays title and URL only, so adding visible bylines would be a separate\n  user-facing change unless approved.\n\n## Supporting facts\n\n- `_includes/layouts/post.njk` currently prints `{{ author }}`.\n- `_includes/postslist.njk` is shared by `content/index.njk`,\n  `content/blog.njk`, and `content/tag-pages.njk`; it currently prints only\n  post links.\n- `content/feed.xml.njk` directly prints `post.data.author`.\n- `tests/author-output.test.js` and `tests/archive-output.test.js` are not\n  currently decisive and need real build assertions.\n\n## Execution plan\n\nStatus: Draft\n\nAdapt the post layout and feed to iterate over the normalized author\ncollection. Keep the shared archive list's current visible contract unless the\nrequester approves adding bylines, but make its generated-path coverage prove\nthat the migration does not bypass or break archive rendering. Extend the\ngenerated-output tests to build the site and inspect post, home, blog, tag,\nand feed files for both single- and multi-author cases.\n\n### Implementation decisions and open questions\n\n- Consumer templates should use normalized data, not independently support\n  both legacy and canonical field names.\n- Preserve existing archive URLs and order; author display in archives is not\n  implied by the migration request because the current list has no byline.\n- Treat XML validity and deterministic author ordering as release-blocking\n  checks.\n\n### Documentation\n\n- Document the resulting feed/author rendering contract only after the public\n  shape is approved and the generated-output assertions pass.\n- Keep the archive behavior statement aligned with whether bylines were\n  explicitly approved.\n\n### Task checklist\n\n- [ ] Update the post layout to consume normalized structured authors.\n- [ ] Update the feed template to the approved multi-author contract.\n- [ ] Verify shared archive consumers through home, blog, and tag builds.\n- [ ] Replace comment-only output tests with production-build assertions.\n- [ ] Confirm no direct legacy reads remain in production templates.\n\n### Requirement verification\n\n- Run `npm run build` with migrated single- and multi-author posts.\n- Assert the post HTML contains the expected ordered author output and keeps\n  existing post URLs.\n- Assert `/index.html`, `/blog/index.html`, and the generated tag page retain\n  expected links, order, and valid markup.\n- Assert `/feed/feed.xml` contains the approved author elements in source\n  order and remains valid XML for both author cardinalities.\n\n### Additional implementation verification\n\n- Check generated output for empty or duplicated author elements.\n- Check that the shared archive include is exercised by all three callers,\n  not only by the blog page.\n- Compare the set of generated routes before and after the migration.\n",
    "tasks/20260919-author-metadata-migration/030-authoring-tool.md": "# Update the post-authoring helper for structured authors\n\nMove the new-post helper to the canonical multi-author input and prove that\nits output is consumable by the same content/build path as hand-authored\nposts.\n\nParent Task: tasks/20260919-author-metadata-migration/000-main.md\nDepends On: tasks/20260919-author-metadata-migration/010-schema-and-content-migration.md\n\n## Requirements checklist\n\n- [ ] The helper accepts the approved structured author input, including\n      multiple ordered authors.\n- [ ] Generated front matter uses the canonical field and valid serialization\n      for the repository's parser.\n- [ ] The helper no longer requires callers to provide the legacy scalar field\n      for new posts.\n- [ ] Helper output is verified by parsing/building a representative post,\n      not only by comparing a string.\n- [ ] Transition guidance makes clear how existing legacy posts and newly\n      authored posts differ until cutover.\n\n## Requirement questions and decisions\n\n- Confirm the helper API shape: a list of author objects, a list of display\n  names normalized into objects, or another approved interface.\n- Confirm whether retaining a compatibility overload for callers of\n  `frontMatter(title, author)` is required during the transition. If retained,\n  define its warning/deprecation behavior separately from the content parser.\n\n## Supporting facts\n\n- `scripts/new-post.js` currently exports `frontMatter(title, author)` and\n  interpolates an unescaped scalar into `author:`.\n- There is no existing CLI wrapper or helper test, so the new contract should\n  be tested at the exported-function boundary and then through the Eleventy\n  build.\n\n## Execution plan\n\nStatus: Draft\n\nDefine the helper input in terms of the approved canonical model and serialize\nit safely as front matter. Add tests for one and multiple authors, including\nnames that could expose quoting or YAML serialization problems. Feed the\ngenerated front matter into a temporary or test fixture post and run the real\nbuild path so the helper cannot drift from the content parser.\n\n### Implementation decisions and open questions\n\n- Prefer structured serialization over hand-built YAML interpolation so author\n  names are quoted/escaped correctly.\n- Keep any legacy helper overload only if explicitly required; it must not\n  cause newly generated content to write the legacy field.\n- Do not make the helper reject legacy input before the integrated cutover\n  evidence has established that existing content and callers no longer need\n  it.\n\n### Documentation\n\n- Update the authoring instructions with the helper signature and a\n  canonical one-/multi-author example.\n- Explain the compatibility window and the later evidence-gated legacy\n  rejection without claiming that rejection has already happened.\n\n### Task checklist\n\n- [ ] Confirm the helper input contract.\n- [ ] Serialize canonical author front matter safely.\n- [ ] Add one- and multi-author helper tests.\n- [ ] Build a post from helper output through the production path.\n- [ ] Update the owning authoring documentation.\n\n### Requirement verification\n\n- Assert helper output parses to the approved canonical structure.\n- Build representative generated posts and verify author output matches the\n  ordered input.\n- Exercise any retained legacy call shape and verify its explicitly approved\n  transition behavior.\n\n### Additional implementation verification\n\n- Include names containing punctuation, quotes, or non-ASCII characters in\n  serialization coverage where the chosen format requires escaping.\n- Confirm helper tests do not bypass the front-matter parser or Eleventy\n  rendering boundary.\n",
    "tasks/20260919-author-metadata-migration/040-legacy-cutover-evidence.md": "# Gate removal or rejection of the legacy author field\n\nDefine and execute the final compatibility gate. Legacy input must remain\navailable until source and generated-output evidence proves that the migrated\nsite and authoring path no longer depend on it.\n\nParent Task: tasks/20260919-author-metadata-migration/000-main.md\nDepends On:\n  - tasks/20260919-author-metadata-migration/010-schema-and-content-migration.md\n  - tasks/20260919-author-metadata-migration/020-generated-consumers.md\n  - tasks/20260919-author-metadata-migration/030-authoring-tool.md\n\n## Requirements checklist\n\n- [ ] The compatibility window remains enabled while migrated and\n      legacy-shaped content are both covered.\n- [ ] A source/content audit finds no remaining required legacy field usage in\n      posts, templates, scripts, or maintained fixtures.\n- [ ] A production build proves generated posts, home/blog/tag archives, feed,\n      and sitemap still generate successfully from the canonical model.\n- [ ] Generated artifacts are inspected/asserted for preserved routes and\n      approved author output, including multi-author cases.\n- [ ] Legacy rejection/removal is enabled only after the preceding evidence\n      passes and is recorded as a deliberate cutover.\n- [ ] Post-cutover tests prove the canonical path remains supported and the\n      intended legacy failure behavior is explicit.\n\n## Requirement questions and decisions\n\n- Confirm whether the desired final state is hard rejection of legacy\n  front matter, removal of a compatibility normalizer, or both.\n- Confirm whether any external/untracked content source is in scope for the\n  dependency audit; the repository currently exposes only checked-in posts.\n- Confirm the exact error/reporting contract for a legacy field after\n  rejection. Do not introduce an undocumented failure mode.\n\n## Supporting facts\n\n- Existing generated-output test files are currently placeholders, so the\n  cutover cannot rely on prior test names as evidence.\n- `npm run build` is the production generation boundary and `npm test` is the\n  repository test boundary.\n- Direct legacy dependencies are currently visible in the post layout, feed,\n  and authoring helper; archive rendering must still be checked because it is\n  a shared production path even though it does not currently print authors.\n\n## Execution plan\n\nStatus: Draft\n\nKeep compatibility enabled while all child changes land. Run a repository-wide\ndependency audit and the complete production build/test suite with migrated\nsingle- and multi-author content. Inspect the generated artifact set and\nassert the relevant public output. Record the evidence and approval decision.\nOnly then make the legacy field rejectable/removable, update the tests and\nguidance for that final state, and rerun the same production checks to prove\nthe cutover did not regress generated pages.\n\n### Implementation decisions and open questions\n\n- The cutover is a separate compatibility state, not an incidental cleanup\n  bundled into the first source migration.\n- A passing source search is necessary but not sufficient; generated-output\n  evidence is mandatory because Eleventy data cascade and template behavior\n  can retain dependencies not obvious from migrated front matter.\n- If the evidence finds an unresolved dependency, leave compatibility enabled,\n  record the dependency, and do not reject the legacy field.\n\n### Documentation\n\n- Record the final compatibility state and migration evidence in the owning\n  developer documentation.\n- If rejection is not yet safe, document the remaining dependency and keep the\n  legacy format described as transitional rather than unsupported.\n- Do not rewrite historical generated output by hand; update its maintained\n  source and regenerate it through Eleventy.\n\n### Task checklist\n\n- [ ] Keep legacy compatibility active during integrated verification.\n- [ ] Audit content, templates, scripts, tests, and documentation for legacy\n      dependencies.\n- [ ] Run `npm test` and `npm run build` with representative content.\n- [ ] Inspect/assert generated post, archive, feed, and sitemap artifacts.\n- [ ] Record the evidence and obtain the cutover decision.\n- [ ] If approved, enable explicit legacy rejection/removal.\n- [ ] Rerun all decisive checks after cutover and update documentation.\n\n### Requirement verification\n\n- Source evidence: repository-wide search plus inspection of every remaining\n  match, with no unclassified required legacy dependency.\n- Generated evidence: successful production build and assertions over all\n  public artifact classes named in the requirements.\n- Compatibility evidence: a legacy-shaped fixture passes before cutover;\n  after cutover, the canonical fixture passes and the approved legacy failure\n  behavior is asserted.\n- Preservation evidence: generated route set, archive links/order, post\n  content, feed author order, and sitemap URLs remain valid.\n\n### Additional implementation verification\n\n- Run the complete test suite after any rejection change, not only the\n  focused author tests.\n- Check for stale generated files or documentation that still teaches the\n  rejected format.\n- Keep the evidence record in this task's completion notes so a later\n  maintainer can distinguish \u201cnot found\u201d from \u201cnot searched.\u201d\n"
  },
  "task_tree": {
    "all_dependencies_resolve": true,
    "all_parent_links_resolve": true,
    "coordinating_files": [
      "tasks/20260919-author-metadata-migration/000-main.md"
    ],
    "dependencies": [],
    "files": [
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": null,
        "path": "tasks/20260919-author-metadata-migration/000-main.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 7,
        "title": "Migrate post author metadata to structured multi-author data"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260919-author-metadata-migration/000-main.md",
        "path": "tasks/20260919-author-metadata-migration/010-schema-and-content-migration.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Establish the structured author model and migrate posts"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260919-author-metadata-migration/000-main.md",
        "path": "tasks/20260919-author-metadata-migration/020-generated-consumers.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Move generated pages and feed consumers to structured authors"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260919-author-metadata-migration/000-main.md",
        "path": "tasks/20260919-author-metadata-migration/030-authoring-tool.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Update the post-authoring helper for structured authors"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260919-author-metadata-migration/000-main.md",
        "path": "tasks/20260919-author-metadata-migration/040-legacy-cutover-evidence.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 6,
        "title": "Gate removal or rejection of the legacy author field"
      }
    ],
    "implementation_task_count": 4,
    "parent_links": [
      {
        "child": "tasks/20260919-author-metadata-migration/010-schema-and-content-migration.md",
        "parent": "tasks/20260919-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260919-author-metadata-migration/020-generated-consumers.md",
        "parent": "tasks/20260919-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260919-author-metadata-migration/030-authoring-tool.md",
        "parent": "tasks/20260919-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260919-author-metadata-migration/040-legacy-cutover-evidence.md",
        "parent": "tasks/20260919-author-metadata-migration/000-main.md",
        "resolves": true
      }
    ],
    "phase_named_files": [],
    "task_directory_count": 1,
    "task_file_count": 5
  }
}


**Assistant** *(reasoning present)*

{
  "schema_version": 3,
  "scenario_id": "tg06-eleventy-author-migration-decomposition",
  "assessment": {
    "outcome_coverage": "complete",
    "missing_outcomes": [],
    "added_obligations": [],
    "semantic_deliverable_count": 4,
    "actual_task_count": 4,
    "deliverable_mappings": [
      {
        "deliverable_id": "AUTHOR-D1",
        "task_paths": [
          "tasks/20260919-author-metadata-migration/010-schema-and-content-migration.md"
        ],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "010 defines the canonical schema, centralizes dual-format normalization at one data boundary, and migrates checked-in posts with a production-build check that preserves routes, content, and visible author values, leaving the dual-format working state."
      },
      {
        "deliverable_id": "AUTHOR-D2",
        "task_paths": [
          "tasks/20260919-author-metadata-migration/020-generated-consumers.md"
        ],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "020 moves the post layout, shared archive include, and feed onto the normalized model and asserts post, home/blog/tag, and feed artifacts from real Eleventy builds for single- and multi-author cases; page/archive/feed are kept together rather than split per surface."
      },
      {
        "deliverable_id": "AUTHOR-D3",
        "task_paths": [
          "tasks/20260919-author-metadata-migration/010-schema-and-content-migration.md",
          "tasks/20260919-author-metadata-migration/030-authoring-tool.md"
        ],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Content migration is co-located with normalization in 010 and the helper migrates end-to-end (contract, serialization, tests, docs, build-through verification) in 030; both pieces are independently owned with independent value, an acceptable regrouping of the target's content+tools deliverable."
      },
      {
        "deliverable_id": "AUTHOR-D4",
        "task_paths": [
          "tasks/20260919-author-metadata-migration/040-legacy-cutover-evidence.md"
        ],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "040 owns the repository-wide legacy audit, production-build artifact evidence, the recorded cutover decision, and post-cutover re-verification, matching the target's evidence-gated retirement deliverable and the request's explicit evidence condition."
      }
    ],
    "mergeable_groups": [],
    "unmatched_tasks": [],
    "overpacked_tasks": [],
    "valid_layer_boundaries": [
      "tasks/20260919-author-metadata-migration/020-generated-consumers.md",
      "tasks/20260919-author-metadata-migration/030-authoring-tool.md"
    ],
    "automatic_layer_fragments": [],
    "dependency_issues": [],
    "crossing_ownership": "complete",
    "fragmentation_severity": "none",
    "fragmentation_ratio": 1.0,
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
        "status": "none",
        "occurrences": []
      },
      "piecewise_crossing_evidence": {
        "status": "none",
        "occurrences": []
      }
    },
    "partition_quality_score": 94,
    "handoff_quality_score": 91,
    "summary": "Four implementation tasks (000-main.md excluded as a coordinating parent) cover all five approved outcomes and map onto the target's four deliverables with one acceptable regrouping: 010 merges dual-format normalization with content migration while preserving a buildable dual-format working state, 030 owns the independently owned authoring helper end-to-end, and 020/040 match D2/D4. Task count (4) is within the acceptable range and ratio is 1.0. Every deliverable embeds its own tests, documentation, and real production-build verification, so there are no phase-only children, no layer fragments, and no overpacking; the compatibility window is preserved because templates, tooling, and rejection are separate and rejection is isolated behind 040's evidence gate. The required crossing is decisively named: 020 and 040 assert real front matter through normalization and the production Eleventy build into pages, home/blog/tag archives, and feeds at both the compatibility-enabled and post-cutover states, with mocked template data explicitly excluded and 030 routing helper output through the parser/build path. Dependencies mirror D1->{D2,D3}->D4 with no broken intermediate states (010's completion criteria require preserved author rendering); 040's explicit dependency on 010 is redundant but harmless. Open requirement questions (canonical entry shape/identifier, feed contract, dual-field policy, rejection contract) are recorded for approval, matching the target's open questions."
  }
}
