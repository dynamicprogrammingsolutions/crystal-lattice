# Session — tg06-eleventy-author-migration-decomposition · task-creation-assessment-gpt-max-s0 · glm max

- Run: `20260924T194334.626494Z-task-guidance-semantic-tg06-eleventy-author-migration-decomposition-gpt-max-s0-1bc8b960`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `58d1505291b4c33f…`)
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
  "response": "Created a Draft main task with four capability-owned subtasks. No source, template, content, or test implementation was changed.\n\n- Main plan: [000-main.md](/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T223114.817321Z-task-guidance-tg06-eleventy-author-migration-decomposition-max-e885e3d1/workspace/tasks/20260920-author-metadata-migration/000-main.md)\n- Contract and authoring tool: [010-author-contract-and-authoring.md](/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T223114.817321Z-task-guidance-tg06-eleventy-author-migration-decomposition-max-e885e3d1/workspace/tasks/20260920-author-metadata-migration/010-author-contract-and-authoring.md)\n- Templates, archives, and feeds: [020-rendering-and-archive-consumers.md](/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T223114.817321Z-task-guidance-tg06-eleventy-author-migration-decomposition-max-e885e3d1/workspace/tasks/20260920-author-metadata-migration/020-rendering-and-archive-consumers.md)\n- Existing content migration: [030-source-content-migration.md](/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T223114.817321Z-task-guidance-tg06-eleventy-author-migration-decomposition-max-e885e3d1/workspace/tasks/20260920-author-metadata-migration/030-source-content-migration.md)\n- Generated-output evidence and legacy retirement: [040-output-evidence-and-legacy-retirement.md](/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T223114.817321Z-task-guidance-tg06-eleventy-author-migration-decomposition-max-e885e3d1/workspace/tasks/20260920-author-metadata-migration/040-output-evidence-and-legacy-retirement.md)\n\nThe plan preserves the legacy adapter until source scans and real Eleventy output checks pass, then adds a canonical-only rejection check. It records the remaining design questions around whether `authors` contains strings or `{name}` records, dual-field conflict handling, feed representation, and the rejection diagnostic.\n\nI verified the task structure, required headings, parent/dependency links, and that the worktree contains only the new `tasks/` tree. Build and test commands were not run because this is planning-only and dependencies are not installed.",
  "task_files": {
    "tasks/20260920-author-metadata-migration/000-main.md": "# Migrate post author metadata\n\nPlan the migration from the single `author` front-matter value to a canonical\nordered multi-author value while keeping legacy content and generated output\nworking until repository evidence permits the legacy form to be rejected.\n\n## Requirements checklist\n\n- [ ] R1. Define and adopt one canonical structured author collection that\n  supports one or more authors, preserves source order, and exposes each\n  author's display identity to every production consumer.\n- [ ] R2. Preserve existing content and generated pages during the transition:\n  legacy `author` content must continue to normalize to the canonical model\n  until the retirement gate passes, without changing post bodies, routes,\n  tags, archive membership, feed location, or sitemap coverage.\n- [ ] R3. Move the authoring helper to the canonical model and make its\n  single- and multi-author behavior explicit, while preserving safe input\n  compatibility during the transition.\n- [ ] R4. Migrate every repository post from the legacy field without losing,\n  duplicating, or reordering author names, and leave auditable source evidence\n  that the migration is complete.\n- [ ] R5. Move post layouts, home/blog/tag archive consumers, shared post-list\n  rendering, feeds, and any other author consumers to the canonical model.\n  Generated pages must continue to build and all authors must be represented\n  deterministically.\n- [ ] R6. Reject the legacy field only after both source/consumer evidence and\n  production generated-output evidence show that nothing in the repository\n  still depends on it; the rejection must have a clear diagnostic and a\n  regression check.\n- [ ] R7. Update maintained authoring documentation and regression evidence\n  with the supported canonical form and the completed transition state.\n\n## Scope and workstreams\n\nThe scope is the repository\u2019s Eleventy source, content, authoring helper,\nproduction templates, build-time validation, tests, and the maintained\ndocumentation that explains how posts are authored. Existing URLs, post body\ncontent, tags, archive membership, feed location, and sitemap behavior are\ncompatibility constraints.\n\nThe work is intentionally divided by independently reviewable capability:\n\n- establish the data contract and authoring boundary;\n- migrate all rendering and collection consumers;\n- migrate source content and prove its inventory is clean; and\n- perform the generated-output/content gate before enforcing canonical-only\n  input.\n\nAuthor profile pages, stable author IDs, roles, avatars, author sorting, and\nnew public routes are out of scope unless the canonical-shape decision below\nrequires one of them.\n\n## Subtasks\n\n- [ ] tasks/20260920-author-metadata-migration/010-author-contract-and-authoring.md\n- [ ] tasks/20260920-author-metadata-migration/020-rendering-and-archive-consumers.md\n- [ ] tasks/20260920-author-metadata-migration/030-source-content-migration.md\n- [ ] tasks/20260920-author-metadata-migration/040-output-evidence-and-legacy-retirement.md\n\n## Unresolved requirement questions and decisions\n\n- Requirement question: does \u201cstructured\u201d mean an ordered list of display\n  strings (`authors: [\"Ada Example\"]`) or an ordered list of records with a\n  required `name` (`authors: [{ name: \"Ada Example\" }]`)? Recommendation:\n  use records with a required `name` and no additional fields in this\n  migration, so each author has an explicit structured boundary without\n  inventing profile behavior.\n- Requirement question: if both `author` and `authors` are present during the\n  compatibility window, should the build fail as ambiguous input or should\n  one field win? Recommendation: fail with a targeted diagnostic; silently\n  choosing one would hide a content migration error.\n- Design decision: install compatibility normalization before changing\n  consumers or source content; migrate content and collect output evidence;\n  only then enable canonical-only rejection. This ordering is required by the\n  requested transition guarantee.\n- Recommendation requiring confirmation at execution time: preserve the\n  existing one-author display text, join multiple post-page names in source\n  order with a deterministic separator, and emit one feed author element per\n  canonical author. This avoids a URL or feed-location redesign while making\n  multiple authors lossless.\n\n## Research and supporting facts\n\n- `content/posts/first.md` and `content/posts/second.md` are the only current\n  posts and each has a scalar quoted `author`.\n- `_includes/layouts/post.njk` renders `author` directly.\n- `content/feed.xml.njk` reads `post.data.author` directly and currently emits\n  one author element per post.\n- `content/index.njk`, `content/blog.njk`, and `content/tag-pages.njk` all\n  use `_includes/postslist.njk`; that include currently renders titles and\n  links but no author data. These archive paths still need an explicit\n  canonical-model audit and route/output checks.\n- `content/posts/posts.json` supplies the shared post layout and `posts` tag;\n  `content/sitemap.xml.njk` enumerates all page URLs but has no author lookup.\n- `scripts/new-post.js` exports `frontMatter(title, author)` and serializes\n  the legacy field.\n- `tests/author-output.test.js` and `tests/archive-output.test.js` currently\n  contain comments only, so there is no executable author or archive\n  regression evidence to preserve.\n- `package.json` exposes `npm run build` and `npm test`; dependencies are not\n  installed in this planning checkout, so neither command is evidence for\n  this Draft plan.\n- There is no `docs/index.md`; `docs/development/index.md` only records that\n  no archive pagination specification exists. The smallest likely maintained\n  documentation change is a focused authoring section in `README.md`, unless\n  the approved contract needs a dedicated development page.\n\n## Execution plan\n\nStatus: Draft\n\nFirst agree the canonical author element shape and collision behavior. Add a\nsingle normalization/validation boundary that can represent canonical input\nand temporarily adapt the legacy scalar. Update the authoring helper and\nrendering consumers against that boundary before editing source posts. Then\nconvert every existing post, run a scoped source/consumer inventory, and\nexercise a real Eleventy build that checks post pages, archive routes, feed\nentries, and sitemap coverage. The final subtask removes the compatibility\npath and enables a canonical-only rejection only after those checks pass.\n\nEach child owns its focused tests and documentation updates; the final child\nowns the cross-capability retirement gate rather than being a generic test\nor cleanup task.\n\n### Implementation decisions and open questions\n\n- The canonical field name is planned as `authors`; its element shape remains\n  the requirement question above and must be settled before execution.\n- Normalization should live at the Eleventy data boundary so layouts and\n  collection templates do not each implement different legacy fallbacks.\n- The legacy adapter must be observable in tests and removable without\n  changing canonical rendering.\n- The final rejection is planned as a build-time validation failure with a\n  field-specific message; confirm this is the desired authoring-tool failure\n  mode before implementation.\n\n### Documentation\n\n- Update the maintained authoring guidance with the canonical front-matter\n  example, single/multi-author rules, ordering behavior, and the fact that\n  legacy `author` is no longer accepted after the retirement gate.\n- Keep migration-only rationale and evidence in these task files rather than\n  publishing a target-only claim as current documentation before execution.\n- Do not create an empty documentation hierarchy or unrelated archive\n  pagination material.\n\n### Task checklist\n\n- [ ] Confirm the canonical element shape, collision behavior, and rejection\n  diagnostic before execution.\n- [ ] Complete tasks/20260920-author-metadata-migration/010-author-contract-and-authoring.md.\n- [ ] Complete tasks/20260920-author-metadata-migration/020-rendering-and-archive-consumers.md.\n- [ ] Complete tasks/20260920-author-metadata-migration/030-source-content-migration.md.\n- [ ] Complete tasks/20260920-author-metadata-migration/040-output-evidence-and-legacy-retirement.md.\n- [ ] Review the final generated-output, source-inventory, and negative\n  legacy-input evidence together before marking R6 complete.\n\n### Requirement verification\n\n- R1 is complete only when the canonical contract is exercised through the\n  authoring/data boundary and a real rendered post with one and multiple\n  authors.\n- R2 is complete only when a pre-migration/compatibility build accepts the\n  legacy fixture and preserves routes, post content, archive membership, feed\n  location, and sitemap coverage.\n- R3 is complete when the authoring helper\u2019s generated front matter is parsed\n  by the production data path for both one and multiple authors, including\n  relevant escaping/validation cases.\n- R4 is complete when a scoped source scan finds no legacy post field and a\n  reviewed content diff proves names and order were preserved.\n- R5 is complete when the production build and output assertions cover the\n  post layout, home/blog/tag archive routes, feed author entries, and sitemap\n  URLs without a legacy lookup.\n- R6 is complete only after the source/consumer scan and canonical-content\n  build pass, followed by a real negative build/input check proving that a\n  legacy field now fails with the intended diagnostic.\n- R7 is complete when the maintained authoring documentation matches the\n  enforced behavior and `npm test` plus `npm run build` exit successfully\n  with dependencies available.",
    "tasks/20260920-author-metadata-migration/010-author-contract-and-authoring.md": "# Define the author contract and migrate authoring input\n\nEstablish the canonical `authors` data contract and the temporary\ncompatibility boundary, then make the post-authoring helper emit canonical\nfront matter without prematurely breaking existing callers or content.\n\nParent Task: tasks/20260920-author-metadata-migration/000-main.md\n\nDepends On: None\n\n## Requirements checklist\n\n- [ ] Define an ordered, non-empty canonical author collection and the\n  required display identity for each entry.\n- [ ] Normalize a legacy scalar `author` to one canonical author during the\n  transition, while making the legacy/canonical collision behavior explicit.\n- [ ] Make `scripts/new-post.js` produce canonical `authors` front matter for\n  one or multiple authors and preserve safe compatibility for existing\n  single-author callers until the retirement gate.\n- [ ] Add focused evidence for normalization, serialization, ordering, and\n  invalid/ambiguous input.\n- [ ] Document the canonical authoring example in the maintained documentation\n  owned by this capability.\n\n## Research and supporting facts\n\n- `scripts/new-post.js` currently exports a two-argument\n  `frontMatter(title, author)` helper and writes `author: \"...\"`.\n- No Eleventy data normalization or front-matter validation exists in\n  `eleventy.config.js`.\n- The current post layout receives front-matter fields directly, so changing\n  the source field without a shared boundary would create inconsistent\n  transition behavior across templates.\n- There are no executable tests for the helper or the legacy transition.\n\n## Execution plan\n\nStatus: Draft\n\nAfter the canonical element shape is approved, introduce one normalization\nand validation boundary in the Eleventy data path. It should expose only the\ncanonical collection to downstream templates, adapt a legacy scalar while the\nmigration is in progress, and identify both-field or malformed input with a\ntargeted error. Update the exported helper so its canonical output is stable\nand YAML-safe for one and multiple authors; if its old scalar call shape is\nretained temporarily, it must still write `authors`, not recreate `author`.\nAdd tests that exercise the helper and the production data boundary rather\nthan mocking the fields. Keep the compatibility branch available until the\nretirement subtask proves it can be removed.\n\n### Implementation decisions and open questions\n\n- Resolve whether an item is a string or a record with required `name`;\n  the parent recommendation is the record form.\n- Resolve whether both fields fail immediately; the parent recommendation is\n  to fail rather than apply precedence.\n- Preserve author order exactly as supplied. Do not sort, deduplicate, or\n  infer author identity from display text.\n- Treat empty author collections and blank names as invalid input, with the\n  exact diagnostic tested at the boundary.\n\n### Documentation\n\n- Extend `README.md` (or the smallest approved owning document) with the\n  canonical front-matter example and the one/multiple-author input rule.\n- Describe the compatibility behavior as transitional only; do not claim\n  legacy rejection until the retirement child completes it.\n\n### Task checklist\n\n- [ ] Confirm canonical item shape and validation/collision semantics.\n- [ ] Add the shared compatibility normalization and validation boundary.\n- [ ] Update `scripts/new-post.js` to serialize canonical one/multiple-author\n  metadata safely.\n- [ ] Add production-boundary tests for canonical input, legacy adaptation,\n  malformed input, and ambiguous dual input.\n- [ ] Update the maintained authoring guidance.\n\n### Requirement verification\n\n- The canonical contract is proven by parsing helper output through the same\n  data path used by Eleventy pages, with one and multiple ordered entries.\n- Transition safety is proven by a representative legacy front matter input\n  producing the same normalized one-author value without a template-specific\n  fallback.\n- Authoring compatibility is proven by tests of the exported helper\u2019s\n  canonical output and any retained scalar call form.\n- Validation is proven by production-path failures for blank/empty and\n  ambiguous metadata, not by a mock that bypasses Eleventy data loading.",
    "tasks/20260920-author-metadata-migration/020-rendering-and-archive-consumers.md": "# Move rendering and archive consumers to canonical authors\n\nUpdate post templates, shared collection rendering, archive pages, feeds, and\nrelated generated-output consumers so they read the canonical author\ncollection while preserving current routes and single-author behavior.\n\nParent Task: tasks/20260920-author-metadata-migration/000-main.md\n\nDepends On: tasks/20260920-author-metadata-migration/010-author-contract-and-authoring.md\n\n## Requirements checklist\n\n- [ ] Render every canonical post author in the post layout in source order,\n  preserving the current one-author display.\n- [ ] Audit and update `_includes/postslist.njk`, the home page, blog archive,\n  and tag archive templates so no author behavior depends on `author`.\n- [ ] Update the feed to represent every canonical author deterministically\n  and with correct XML escaping, without changing its public location.\n- [ ] Verify other generated metadata consumers, including the sitemap, do\n  not accidentally depend on the legacy field.\n- [ ] Add production-build assertions for post pages, archive routes, feed\n  author entries, and sitemap URLs.\n\n## Research and supporting facts\n\n- `_includes/layouts/post.njk` currently prints the scalar `author`.\n- `content/index.njk`, `content/blog.njk`, and `content/tag-pages.njk` all\n  include `_includes/postslist.njk`; the shared include currently prints only\n  title/link values.\n- `content/feed.xml.njk` directly reads `post.data.author` and has one\n  `<author>` element per post.\n- `content/sitemap.xml.njk` only reads `page.url`, so it should remain\n  author-independent while still being covered by a route regression check.\n- The current tests do not build or inspect any generated page.\n\n## Execution plan\n\nStatus: Draft\n\nUse the normalized canonical collection supplied by subtask 010 as the only\ntemplate input. Update the post layout to render the complete collection and\nupdate the feed to iterate it, retaining the current single-author result and\nusing the approved deterministic multi-author representation. Inspect the\nshared post-list and all three archive entry points: if they expose no author\nmetadata, preserve that public shape while proving they do not dereference\nthe legacy field; if author metadata is rendered as part of the approved\ncontract, make the include iterate canonical authors. Keep archive URLs,\ntagging, ordering, and feed/sitemap locations unchanged. Build the real site\nand assert output at the generated-file boundary.\n\n### Implementation decisions and open questions\n\n- Confirm the post-page separator for multiple display names; recommendation:\n  comma plus space in source order, with no change for one name.\n- Confirm the feed representation; recommendation: emit one existing-style\n  author element per canonical author in source order rather than inventing a\n  new feed location or author index.\n- XML escaping must be handled by the template/data path for names containing\n  markup-sensitive characters.\n- Do not add author pages, sorting, or archive pagination as incidental scope.\n\n### Documentation\n\n- Document any user-visible multi-author display or feed representation in\n  the same maintained authoring section updated by subtask 010.\n- Record no archive-pagination claim; the existing development note is\n  unrelated to this migration.\n\n### Task checklist\n\n- [ ] Confirm display and feed representation.\n- [ ] Replace direct legacy reads in the post layout and feed.\n- [ ] Audit/update the shared post list and home/blog/tag archive templates.\n- [ ] Inspect sitemap and other collection consumers for stale legacy access.\n- [ ] Add generated-output assertions covering one and multiple authors and\n  unchanged archive/feed/sitemap routes.\n\n### Requirement verification\n\n- Post rendering is proven by a production build whose post HTML contains all\n  canonical names in order and contains no missing/duplicated author.\n- Archive compatibility is proven by successful generated home, `/blog/`, and\n  tag-page files with the expected links and collection membership.\n- Feed migration is proven by parsing or exact structural assertions against\n  the generated feed, including every author and XML-safe names.\n- Sitemap preservation is proven by checking the generated URL set before the\n  final legacy rejection, with no author lookup involved.\n- A scoped source scan confirms these templates contain no direct\n  `author`/`post.data.author` dependency outside the explicitly transitional\n  boundary.",
    "tasks/20260920-author-metadata-migration/030-source-content-migration.md": "# Migrate existing post source content\n\nConvert every repository post to the canonical multi-author front matter\nafter the compatibility boundary exists, preserving content identity and\nleaving auditable evidence that no source post still requires the legacy\nfield.\n\nParent Task: tasks/20260920-author-metadata-migration/000-main.md\n\nDepends On: tasks/20260920-author-metadata-migration/010-author-contract-and-authoring.md\n\n## Requirements checklist\n\n- [ ] Inventory all post-like source files and front-matter locations before\n  editing them.\n- [ ] Convert every legacy `author` value to one canonical author entry,\n  preserving each name, source order, title, body, tags, and route inputs.\n- [ ] Verify the migrated content through the real Eleventy build while the\n  compatibility path is still available.\n- [ ] Produce a scoped source audit showing no legacy post field remains and\n  distinguishing intentional migration documentation/tests from production\n  content.\n\n## Research and supporting facts\n\n- The known source inventory is `content/posts/first.md` and\n  `content/posts/second.md`; both use the scalar field.\n- `content/posts/posts.json` applies the common post layout and `posts` tag,\n  so source migration must preserve collection membership.\n- No explicit permalink appears in either post; route stability therefore\n  depends on preserving filenames and Eleventy defaults.\n- The repository has no migration utility or content validation test today.\n\n## Execution plan\n\nStatus: Draft\n\nRun a repository-scoped inventory over Markdown, JSON data, templates, helper\ncode, and tests before changing source. After subtask 010 establishes\nnormalization, convert the known posts (and any inventory discoveries) to the\napproved canonical form. Review the source diff for exact author names and\norder, unchanged bodies, titles, and collection metadata. Build the site\nbefore legacy rejection so the transitional adapter proves that the migrated\ncanonical content and any remaining compatibility fixtures coexist. Finish\nwith a source scan whose scope is explicit and whose result is consumable by\nthe retirement gate.\n\nFor the small current inventory, a reviewed one-off content edit is\npreferable to adding a permanent migration script; if the inventory grows,\nuse a repeatable transformation with a dry-run/diff check and do not leave\ngenerated artifacts in source control.\n\n### Implementation decisions and open questions\n\n- Confirm whether any content outside `content/posts/` is an approved post\n  source before declaring the inventory complete.\n- Do not normalize names by trimming, sorting, deduplicating, or changing\n  spelling unless the source review explicitly identifies an error.\n- Keep any temporary inventory/migration report outside the repository or\n  remove it before handoff; the durable evidence is the source scan and\n  tested build.\n\n### Documentation\n\n- The canonical content example belongs in the authoring documentation\n  maintained by subtask 010; do not add a second source-format guide here.\n- Record the final migrated file inventory in task evidence, not as a\n  generated documentation artifact.\n\n### Task checklist\n\n- [ ] Inventory all candidate post/front-matter sources.\n- [ ] Convert every legacy post field to the approved canonical form.\n- [ ] Review the diff for author identity/order and unchanged post metadata.\n- [ ] Build the migrated site while compatibility remains enabled.\n- [ ] Run and preserve the scoped no-legacy-source audit for subtask 040.\n\n### Requirement verification\n\n- Inventory completeness is proven by a scoped search covering all supported\n  content extensions and front-matter locations.\n- Data preservation is proven by source diff review plus comparison of\n  title/body/tag/route inputs, not by checking only the new author field.\n- Canonical content is proven by a real Eleventy build that renders every\n  migrated post and retains its collection membership.\n- Legacy retirement input is proven only when the source audit has no\n  production `author` field and the consumer scan separately has no stale\n  legacy lookup.",
    "tasks/20260920-author-metadata-migration/040-output-evidence-and-legacy-retirement.md": "# Prove generated output and retire the legacy author field\n\nRun the cross-capability transition gate, then enforce canonical-only author\nmetadata only after source, consumer, and generated-output evidence proves\nthat the legacy field is no longer required.\n\nParent Task: tasks/20260920-author-metadata-migration/000-main.md\n\nDepends On:\n\n- tasks/20260920-author-metadata-migration/010-author-contract-and-authoring.md\n- tasks/20260920-author-metadata-migration/020-rendering-and-archive-consumers.md\n- tasks/20260920-author-metadata-migration/030-source-content-migration.md\n\n## Requirements checklist\n\n- [ ] Collect a complete pre-rejection source and consumer audit with no\n  production dependency on the legacy `author` field.\n- [ ] Prove through a real production build that migrated post pages, home\n  page, blog archive, tag pages, feed, and sitemap all remain generated and\n  contain the expected author/routes/content evidence.\n- [ ] Only after those checks pass, remove the legacy normalization branch and\n  enforce a canonical-only input rule with a targeted diagnostic.\n- [ ] Add a negative regression check showing legacy input is rejected after\n  the gate, while canonical one/multiple-author input remains accepted.\n- [ ] Run the full available test/build commands and record blocked commands\n  or environment limitations instead of treating them as passing.\n\n## Research and supporting facts\n\n- The repository currently has no executable generated-output assertions;\n  both relevant test files are comment-only placeholders.\n- `npm run build` invokes Eleventy and writes `_site`; `npm test` runs the\n  Node test files. `node_modules` is absent in the planning checkout.\n- `.gitignore` excludes `node_modules/` and `_site/`, so generated verification\n  can remain a local build artifact.\n- Current legacy consumers are known in the post layout, feed, and authoring\n  helper, but the final audit must catch references introduced during the\n  migration as well.\n\n## Execution plan\n\nStatus: Draft\n\nAdd or complete the generated-output test harness so it invokes the real\nEleventy build and inspects `_site`, rather than supplying mocked post data.\nBefore retirement, run a scoped inventory over production content, templates,\nconfiguration, scripts, and tests; allow only the explicitly documented\ncompatibility boundary to mention or read the legacy field. Build the\ncanonical content and assert post author rendering, archive links/routes, all\nfeed authors, feed location, and sitemap URLs. Review the source and output\nresults together as the retirement gate.\n\nOnce the gate is green, remove the legacy adapter, turn on canonical-only\nvalidation, and add a production-path negative fixture/check for a legacy\nfront-matter field. Re-run the canonical build and all tests after that\nchange. The negative check must demonstrate the intended failure without\nweakening the normal build path or leaving a legacy fixture in the production\ncontent tree.\n\n### Implementation decisions and open questions\n\n- Confirm the rejection mode; recommendation: fail the build early with the\n  field name and migration action in the diagnostic.\n- Keep the compatibility branch until the positive output evidence is\n  complete; do not use a passing static scan alone as the retirement gate.\n- Define the audit scope so historical task text or a deliberate negative\n  fixture does not masquerade as a production dependency, while no live\n  template/content/script lookup is excluded.\n- If dependencies remain unavailable, leave the plan/task incomplete and\n  report the exact blocked production commands; do not mark R6 complete from\n  static inspection.\n\n### Documentation\n\n- Update the maintained authoring guidance only after canonical-only\n  validation is enabled, so it describes current supported behavior.\n- Record the source scan, generated-output checks, and negative rejection\n  result in completion notes when execution is approved; do not claim this\n  evidence in the Draft plan.\n\n### Task checklist\n\n- [ ] Implement/complete real generated-output assertions.\n- [ ] Run the pre-rejection source and consumer audit.\n- [ ] Build and inspect all required canonical outputs.\n- [ ] Review the combined evidence and explicitly authorize the retirement\n  step.\n- [ ] Remove legacy normalization and enable canonical-only rejection.\n- [ ] Add/run the negative legacy-input regression check.\n- [ ] Re-run `npm test` and `npm run build`, then record evidence and any\n  deferred verification.\n\n### Requirement verification\n\n- The retirement gate is decisive only when the scoped source/consumer audit,\n  canonical content build, and generated-output assertions all pass together.\n- Generated pages are verified at the public boundary: post HTML contains\n  every author, home/blog/tag routes and links remain present, feed output\n  contains every author at `/feed/feed.xml`, and sitemap URLs remain intact.\n- Legacy rejection is verified by running the actual production validation\n  path against representative legacy input and asserting the targeted\n  failure, followed by a successful canonical build.\n- Overall completion is verified by clean exits from `npm test` and\n  `npm run build` with the required dependencies installed; unavailable\n  commands remain an explicit verification gap."
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
        "title": "Migrate post author metadata"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260920-author-metadata-migration/000-main.md",
        "path": "tasks/20260920-author-metadata-migration/010-author-contract-and-authoring.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Define the author contract and migrate authoring input"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260920-author-metadata-migration/000-main.md",
        "path": "tasks/20260920-author-metadata-migration/020-rendering-and-archive-consumers.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Move rendering and archive consumers to canonical authors"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260920-author-metadata-migration/000-main.md",
        "path": "tasks/20260920-author-metadata-migration/030-source-content-migration.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 4,
        "title": "Migrate existing post source content"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260920-author-metadata-migration/000-main.md",
        "path": "tasks/20260920-author-metadata-migration/040-output-evidence-and-legacy-retirement.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Prove generated output and retire the legacy author field"
      }
    ],
    "implementation_task_count": 4,
    "parent_links": [
      {
        "child": "tasks/20260920-author-metadata-migration/010-author-contract-and-authoring.md",
        "parent": "tasks/20260920-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260920-author-metadata-migration/020-rendering-and-archive-consumers.md",
        "parent": "tasks/20260920-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260920-author-metadata-migration/030-source-content-migration.md",
        "parent": "tasks/20260920-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260920-author-metadata-migration/040-output-evidence-and-legacy-retirement.md",
        "parent": "tasks/20260920-author-metadata-migration/000-main.md",
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
        "task_paths": ["tasks/20260920-author-metadata-migration/010-author-contract-and-authoring.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "010 delivers the canonical contract, the normalization/validation boundary with legacy adaptation, production-path tests, and authoring docs, leaving the dual-format acceptance state of AUTHOR-D1/AUTHOR-1; it also absorbs the authoring-helper half of AUTHOR-D3."
      },
      {
        "deliverable_id": "AUTHOR-D2",
        "task_paths": ["tasks/20260920-author-metadata-migration/020-rendering-and-archive-consumers.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "020 moves post layout, shared post list, home/blog/tag archives, feed, and the sitemap audit to the canonical model with real-build output assertions, matching AUTHOR-D2/AUTHOR-2 while preserving routes and feed location."
      },
      {
        "deliverable_id": "AUTHOR-D3",
        "task_paths": ["tasks/20260920-author-metadata-migration/010-author-contract-and-authoring.md", "tasks/20260920-author-metadata-migration/030-source-content-migration.md"],
        "coverage": "complete",
        "coherence": "fragmented",
        "reason": "Both halves of AUTHOR-D3 are present but split across non-adjacent tasks: the authoring-helper migration sits inside 010 with the normalization contract, while content conversion is 030; each half is explicitly owned and leaves a working state, so value is preserved but the target deliverable boundary is not."
      },
      {
        "deliverable_id": "AUTHOR-D4",
        "task_paths": ["tasks/20260920-author-metadata-migration/040-output-evidence-and-legacy-retirement.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "040 combines the source/consumer audit, canonical generated-output build evidence, adapter removal, canonical-only rejection with a targeted diagnostic and negative regression, and full test/build runs — the evidence-gated retirement of AUTHOR-D4/AUTHOR-4."
      }
    ],
    "mergeable_groups": [],
    "unmatched_tasks": [],
    "overpacked_tasks": [],
    "valid_layer_boundaries": [],
    "automatic_layer_fragments": [],
    "dependency_issues": [],
    "crossing_ownership": "complete",
    "fragmentation_severity": "low",
    "fragmentation_ratio": 1.0,
    "quality_metrics": {
      "fragmentation": {
        "status": "low",
        "occurrences": [
          {
            "task_paths": [
              "tasks/20260920-author-metadata-migration/010-author-contract-and-authoring.md",
              "tasks/20260920-author-metadata-migration/030-source-content-migration.md"
            ],
            "description": "Target deliverable AUTHOR-D3 (content + authoring tools) is re-cut: the authoring-helper migration is fused into 010 alongside the normalization/compatibility boundary, and content migration is a separate 030. Ownership and working states survive on both sides, so this is a benign boundary deviation rather than a phase split, but the partition does not preserve the target's D1/D3 line."
          }
        ]
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
        "status": "partial",
        "occurrences": [
          {
            "task_paths": [
              "tasks/20260920-author-metadata-migration/020-rendering-and-archive-consumers.md",
              "tasks/20260920-author-metadata-migration/040-output-evidence-and-legacy-retirement.md"
            ],
            "description": "020 already owns production-build assertions for post pages, archive routes, feed authors, and sitemap URLs, but 040's checklist also says 'Implement/complete real generated-output assertions' and its plan says to add or complete the generated-output harness — leaving harness ownership ambiguous and pulling part of the surface evidence into the final gate child. The gate-level re-verification itself is legitimate AUTHOR-D4 work."
          }
        ]
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
    "partition_quality_score": 87,
    "handoff_quality_score": 86,
    "summary": "Four implementation tasks behind a coordinating parent cover all five approved outcomes with the compatibility window intact: 010 establishes the canonical contract, normalization boundary, and authoring-helper migration; 020 moves every generated consumer (post layout, shared list, archives, feed, sitemap audit) in one task; 030 converts content with inventory and diff evidence; 040 runs the combined source/consumer/generated-output gate before removing the adapter and enabling canonical-only rejection with a negative check. Declared dependencies (010→none, 020→010, 030→010, 040→010+020+030) match the target's D1→{D2,D3}→D4 graph, no phase-only, per-surface, or per-test-type tasks exist, and each task names decisive checks through the required production connection (real front matter → normalization → real Eleventy build → pages, archives, feed), so the crossing is complete. The only fragmentation is the benign re-cut of AUTHOR-D3 (helper half in 010, content half in 030, both owned), and evidence_reownership is partial because 040 ambiguously re-owns the output-assertion harness 020 already claims. Watch-item: the graph permits executing 030 before 020; the narrative order (consumers before content) avoids degraded author rendering, but an explicit canonical→legacy compatibility view or ordering note would harden intermediate states."
  }
}
