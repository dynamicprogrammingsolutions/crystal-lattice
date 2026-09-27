# Session — tg06-eleventy-author-migration-decomposition · task-creation-assessment-gpt-xhigh-s0 · glm max

- Run: `20260925T224910.336615Z-task-guidance-semantic-tg06-eleventy-author-migration-decomposition-gpt-xhigh-s0-e5624644`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `bb56a474feaf8d13…`)
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
  "response": "Created a draft, planning-only task hierarchy:\n\n- [Main migration plan](/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T221510.725090Z-task-guidance-tg06-eleventy-author-migration-decomposition-xhigh-d52b475d/workspace/tasks/20260926-author-metadata-migration/000-main.md)\n- [Source and authoring migration](/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T221510.725090Z-task-guidance-tg06-eleventy-author-migration-decomposition-xhigh-d52b475d/workspace/tasks/20260926-author-metadata-migration/010-source-and-authoring.md)\n- [Public rendering and generated output](/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T221510.725090Z-task-guidance-tg06-eleventy-author-migration-decomposition-xhigh-d52b475d/workspace/tasks/20260926-author-metadata-migration/020-public-rendering.md)\n- [Evidence-gated legacy cutover](/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T221510.725090Z-task-guidance-tg06-eleventy-author-migration-decomposition-xhigh-d52b475d/workspace/tasks/20260926-author-metadata-migration/030-legacy-cutover.md)\n\nThe plan records:\n\n- A proposed `authors` sequence of structured records.\n- Safe migration of the existing posts and the `new-post` authoring helper.\n- Transitional legacy-read compatibility.\n- Production-build verification across posts, home, blog, tags, and feeds.\n- A strict content-scan plus generated-output evidence gate before legacy rejection.\n- Documentation updates in the existing developer-facing documentation boundary.\n- Dependencies between the three subtasks.\n\nThree material questions remain explicitly unresolved before approval:\n\n1. Whether author records need only `name` or also stable identity/profile fields.\n2. Whether archive/list pages should display authors or retain their current title-only presentation.\n3. Whether post-cutover legacy input should fail the build or use another explicit unsupported-input behavior.\n\nNo implementation, dependency installation, build, or tests were run. The worktree change is limited to the new `tasks/20260926-author-metadata-migration/` structure, and all plans remain `Draft` pending those decisions and execution approval.",
  "task_files": {
    "tasks/20260926-author-metadata-migration/000-main.md": "# Migrate post author metadata to structured multi-author records\n\nPlan the migration from the single `author` front-matter string to a structured\nmulti-author representation while preserving existing content, routes, and\ngenerated pages throughout the transition.\n\n## Requirements checklist\n\n- [ ] R1. Posts use an approved structured metadata form that represents one or\n  more authors without losing each author's display name.\n- [ ] R2. Every existing post is migrated safely to the new form, preserving\n  its author data and all existing generated URLs/content.\n- [ ] R3. The post layout, shared post-list/archive paths, tag pages, and feed\n  consume the new author model and render valid output for one and multiple\n  authors.\n- [ ] R4. The post-authoring helper writes the new form for newly created posts\n  and does not create new dependencies on the legacy field.\n- [ ] R5. Legacy `author` metadata is tolerated only during the migration\n  window and is rejected or removed only after repository-content and\n  production-generated-output evidence demonstrates that no supported path\n  still depends on it.\n\n## Unresolved requirement questions\n\n- Q1. What is the canonical record shape? Recommended target: an `authors`\n  sequence of objects with a required `name` field, leaving room for a stable\n  identifier or profile URL later. Confirm whether names alone are sufficient\n  or whether identity/link fields are required now.\n- Q2. Should archive, home, and tag list entries begin displaying all author\n  names, or should they retain their current title-only presentation while\n  becoming safe consumers of the new metadata? The current shared list emits\n  titles only, so adding author text would be a user-visible presentation\n  change.\n- Q3. After the evidence gate, should legacy front matter fail the build with a\n  validation error, or should it be ignored as unsupported input? A clear\n  build-time error is recommended so an accidental regression cannot silently\n  lose author data.\n\n## Research and supporting facts\n\n- `content/posts/first.md` and `content/posts/second.md` are the only current\n  posts; both use a quoted scalar `author` value.\n- `_includes/layouts/post.njk` renders `author` directly.\n- `content/feed.xml.njk` reads `post.data.author` directly.\n- `_includes/postslist.njk` currently renders only title and URL, but it is\n  shared by `content/index.njk`, `content/blog.njk`, and\n  `content/tag-pages.njk`; those archive paths still need production-build\n  coverage during the migration.\n- `scripts/new-post.js` exports `frontMatter(title, author)` and writes the\n  legacy field, making it the authoring boundary for new content.\n- `tests/archive-output.test.js` and `tests/author-output.test.js` contain\n  comments only; they do not currently collect or assert behavior.\n- `README.md` documents the generated site at a high level. There is no\n  existing author-metadata guide or checked-in generated `_site`.\n- `package.json` provides `npm run build` and `npm test`; no lockfile or\n  `node_modules` directory is present in the inspected worktree.\n\n## Execution plan\n\nStatus: Draft\n\nThe proposed design uses a canonical `authors` sequence of author records and\nkeeps a read-only compatibility normalization for legacy `author` input during\nthe migration window. Source migration and the authoring helper stop producing\nthe legacy key. Rendering consumes one normalized sequence, so the post page\ncan render all names and the feed can emit the appropriate author elements\nwithout interpolating an object as a string. The archive/list paths retain\ntheir existing routes and presentation unless Q2 approves an author display\nchange.\n\nLegacy support is not removed as part of source conversion or template\nconversion. The final cutover is a separate dependent boundary: first scan\ncontent and implementation references, then run the real Eleventy build and\ninspect the post, archive, tag, home, and feed outputs. Only passing evidence\nmay authorize deleting the compatibility path and enabling the approved\nlegacy-input rejection behavior.\n\nOrdered work:\n\n1. Resolve Q1\u2013Q3 and record the approved schema, archive presentation, and\n   post-cutover invalid-input behavior.\n2. Define the normalized author contract, migrate the existing post files, and\n   update `scripts/new-post.js` so newly authored content uses the canonical\n   form.\n3. Update the post layout, feed, and shared archive/list consumers to use the\n   normalized multi-author data while preserving routes and valid output.\n4. Replace placeholder tests with production-path checks for migrated content,\n   single- and multi-author rendering, all archive routes, and the feed.\n5. Run the content-reference and generated-output evidence gate. If it passes,\n   remove legacy production dependencies and add the approved regression check\n   for rejected legacy input; otherwise keep compatibility and record the\n   remaining dependency.\n6. Update the maintained developer documentation with the current metadata\n   shape and authoring/migration behavior in the same change as the final\n   implementation.\n\n## Subtasks\n\n- [ ] `tasks/20260926-author-metadata-migration/010-source-and-authoring.md`\n- [ ] `tasks/20260926-author-metadata-migration/020-public-rendering.md`\n- [ ] `tasks/20260926-author-metadata-migration/030-legacy-cutover.md`\n\n### Implementation decisions and open questions\n\n- The task remains Draft until the canonical record shape, archive\n  presentation, and post-cutover legacy-input behavior are approved.\n- The compatibility reader belongs to the transition, not the final contract;\n  no child may remove it before the cutover child records both content and\n  generated-output evidence.\n- The migration must preserve existing route paths and post body content. Any\n  desired new author links or identifiers should be added only if Q1 approves\n  them.\n\n### Documentation\n\nUpdate `README.md` or the nearest existing developer-facing documentation\nsection, rather than creating an empty documentation hierarchy. Document the\ncanonical front-matter shape, how the authoring helper creates it, the\ntemporary legacy compatibility state while applicable, and the final\nunsupported-input behavior. Keep the documentation change with the\nimplementation that makes each claim true.\n\n### Task checklist\n\n- [ ] Resolve the three requirement questions before marking this plan\n  Approved.\n- [ ] Complete the source/content/authoring child.\n- [ ] Complete the public-rendering child.\n- [ ] Complete the evidence-gated cutover child.\n- [ ] Update the requirement evidence and parent status as each child closes.\n\n### Requirement verification\n\n- R1: A production build of representative single- and multi-author source\n  posts, backed by a direct authoring-helper assertion, proves that the\n  approved structured records survive parsing and render as intended.\n- R2: A repository-wide content scan plus the production build verifies that\n  every existing post has the new metadata, retains its author names, and\n  preserves existing post/archive/tag URLs and body output.\n- R3: One real `npm run build` followed by assertions over the post page,\n  `/`, `/blog/`, generated tag pages, and `/feed/feed.xml` is the decisive\n  check across the shared templates and public generation paths.\n- R4: The authoring-helper test verifies the emitted front matter, and a\n  generated post created from that output is consumed by the same Eleventy\n  build used for R3.\n- R5: The final cutover records both (a) no remaining legacy-key dependencies\n  in source content/templates/tools/tests and (b) successful generated-output\n  inspection for every affected route before any rejection is enabled.\n\n### Additional implementation verification\n\n- Check for accidental `[object Object]`, missing names, malformed feed\n  elements, duplicate author output, and unsafe escaping in generated HTML/XML.\n- Compare the route set before and after migration so metadata changes do not\n  silently alter permalink, archive, tag, or feed generation.\n- Keep the transition testable without changing production paths or adding a\n  test-only data shortcut.",
    "tasks/20260926-author-metadata-migration/010-source-and-authoring.md": "# Define and migrate the structured author source model\n\nOwn the canonical post metadata contract, migration of existing front matter,\nand the authoring helper that creates new posts.\n\nParent Task: `tasks/20260926-author-metadata-migration/000-main.md`\n\nDepends On: None\n\n## Requirements checklist\n\n- [ ] R1. The approved structured author form represents one or more authors\n  and preserves each author's display name.\n- [ ] R2. All existing post front matter is migrated without losing author\n  values, post bodies, or route-defining metadata.\n- [ ] R4. `scripts/new-post.js` emits only the approved structured form for new\n  posts.\n\n## Unresolved requirement questions\n\n- Q1. Confirm whether the canonical author records contain only a required\n  `name` or also stable identity/profile fields; do not add fields during\n  migration without approval.\n\n## Research and supporting facts\n\n- `content/posts/first.md` and `content/posts/second.md` are the complete\n  current content inventory and each has one legacy author string.\n- `scripts/new-post.js` is a small exported helper and currently accepts one\n  `author` argument, then writes `author: \"...\"`.\n- No schema validator or migration utility currently exists.\n- The source migration must leave a compatibility read path available until\n  `030-legacy-cutover.md` completes its evidence gate.\n\n## Execution plan\n\nStatus: Draft\n\nUse the approved canonical `authors` sequence as the only write format. Each\nrecord must preserve the existing display name exactly; any additional fields\nare included only if Q1 approves them. During the transition, expose one\nnormalization contract that turns a legacy scalar into a singleton sequence\nfor consumers that still need to read unmigrated content. This child does not\nremove that fallback or reject legacy input.\n\nOrdered work:\n\n1. Record the approved author record shape and validation rules in the\n   implementation and task evidence.\n2. Update the authoring helper API and its tests so generated front matter\n   contains the new key and supports one or multiple author records.\n3. Migrate every current post, checking that titles, bodies, dates/URLs, tags,\n   and author names remain unchanged.\n4. Add source-level checks that prevent the helper or migrated fixtures from\n   reintroducing the legacy write form.\n5. Update the maintained developer documentation with the new authoring\n   example, leaving any transition note clearly marked until cutover.\n\n### Implementation decisions and open questions\n\n- Q1 controls whether records contain only `name` or also identity/profile\n  fields; do not invent stable identifiers during migration.\n- Preserve exact existing name text, including spaces and punctuation.\n- Compatibility reading is deliberately deferred to the rendering and final\n  cutover boundaries; this child must not make legacy content fail early.\n\n### Documentation\n\nDocument the canonical front-matter example and the authoring-helper input in\nthe existing developer-facing documentation location selected by the parent\ntask. Do not describe legacy input as current guidance after cutover.\n\n### Task checklist\n\n- [ ] Confirm the approved structured schema.\n- [ ] Update and test the authoring helper.\n- [ ] Migrate and inspect every existing post.\n- [ ] Add source-level regression coverage.\n- [ ] Update the maintained metadata/authoring documentation.\n\n### Requirement verification\n\n- R1: The authoring-helper test asserts the exact structured front matter for\n  both one and multiple authors; the downstream production build in\n  `020-public-rendering.md` confirms Eleventy consumes it.\n- R2: A complete content inventory check verifies that each existing post has\n  the canonical key and the same author names and body content; the real\n  production build verifies the migrated files remain publishable.\n- R4: A test invokes `scripts/new-post.js`, parses the returned front matter,\n  and asserts that it writes the canonical key and never writes a new legacy\n  `author` field.\n\n### Additional implementation verification\n\n- Exercise quoting, punctuation, and multiple records in front matter so the\n  migration does not depend on names being plain ASCII or single-word values.\n- Confirm no unrelated front-matter keys are rewritten as a side effect.",
    "tasks/20260926-author-metadata-migration/020-public-rendering.md": "# Render structured authors through public site generation\n\nOwn the post layout, feed, shared archive/list consumers, and production-build\nevidence that the new model works across generated pages.\n\nParent Task: `tasks/20260926-author-metadata-migration/000-main.md`\n\nDepends On: `tasks/20260926-author-metadata-migration/010-source-and-authoring.md`\n\n## Requirements checklist\n\n- [ ] R3. Individual posts, feeds, and all archive/list generation paths\n  consume structured authors and produce valid output for single- and\n  multi-author posts while preserving existing routes.\n- [ ] The rendering transition continues to handle a legacy scalar as a\n  singleton author only until the final cutover evidence is accepted.\n\n## Unresolved requirement questions\n\n- Q2. Confirm whether archive, home, and tag list entries should display all\n  author names or retain their current title-only presentation.\n\n## Research and supporting facts\n\n- `_includes/layouts/post.njk` currently interpolates `author` directly.\n- `content/feed.xml.njk` currently interpolates `post.data.author` directly\n  inside one `<author>` element per entry.\n- `_includes/postslist.njk` is shared by the home page, `/blog/`, and tag\n  pagination. It currently renders only title and link, so its collection\n  iteration must be checked even if Q2 keeps the title-only presentation.\n- `content/tag-pages.njk` creates tag URLs from `collections`; the migration\n  must not alter this pagination or its route shape.\n- Existing tests do not execute Eleventy or inspect generated files.\n\n## Execution plan\n\nStatus: Draft\n\nNormalize each post to an author-record sequence before presentation. The post\nlayout should render every approved author according to Q2, and the feed should\nemit valid author data for every record without stringifying objects or\nsilently dropping additional authors. The shared list should be updated or\nverified as a structured-data consumer while retaining its current route and\ntitle behavior unless Q2 approves visible author names.\n\nThe compatibility normalization remains active here because old content may\nstill exist during the transition. No template should continue to depend\ndirectly on `post.data.author` after the new path is proven.\n\nOrdered work:\n\n1. Add the normalized author-record access used by the post layout and feed.\n2. Update shared list/archive consumers and confirm home, blog, and tag\n   pagination remain valid under the new post data.\n3. Add representative single- and multi-author source fixtures through normal\n   content paths, not test-only renderer shortcuts.\n4. Replace placeholder tests with a production build and assertions over the\n   generated post, home page, blog archive, tag page, and feed.\n5. Record route and output evidence for the cutover child, including checks\n   for missing, duplicated, object-stringified, or malformed author output.\n\n### Implementation decisions and open questions\n\n- Q2 determines whether archive/list items gain visible author text. If it\n  remains title-only, the shared list still must not assume a scalar author or\n  break when records are present.\n- Preserve the existing `/`, `/blog/`, `/tags/*`, post, and feed paths.\n- Keep the legacy normalization as an explicit transitional boundary so the\n  cutover child can remove and test it deliberately.\n\n### Documentation\n\nProvide the parent task with verified output examples and update the\nmaintained developer documentation if the approved presentation or feed\nsemantics are user-visible. Do not document the temporary fallback as a\npermanent contract.\n\n### Task checklist\n\n- [ ] Implement the normalized author rendering path.\n- [ ] Update all shared archive/list and feed consumers.\n- [ ] Add realistic single- and multi-author production inputs.\n- [ ] Replace placeholder tests with build-backed output assertions.\n- [ ] Record route and generated-output evidence for cutover.\n\n### Requirement verification\n\n- R3: Run `npm run build` and inspect the actual `_site` files for an\n  individual post, `/index.html`, `/blog/index.html`, a generated tag page,\n  and `/feed/feed.xml`; assert every approved author is represented and all\n  existing routes remain present.\n- Transitional compatibility: build a representative legacy scalar input\n  before cutover and verify it still renders through the normalized sequence;\n  this check is removed or inverted only by `030-legacy-cutover.md`.\n\n### Additional implementation verification\n\n- Validate HTML/XML escaping for author names containing punctuation.\n- Assert that no generated output contains `[object Object]`, an empty author\n  element, or an unexpected duplicate.\n- Keep the archive and tag checks on the real Eleventy collection/pagination\n  path so a mocked collection cannot hide template incompatibilities.",
    "tasks/20260926-author-metadata-migration/030-legacy-cutover.md": "# Gate and complete legacy author-field removal\n\nOwn the final compatibility decision: collect content and generated-output\nevidence, then remove or reject the legacy form only when the evidence gate\npasses.\n\nParent Task: `tasks/20260926-author-metadata-migration/000-main.md`\n\nDepends On:\n\n- `tasks/20260926-author-metadata-migration/010-source-and-authoring.md`\n- `tasks/20260926-author-metadata-migration/020-public-rendering.md`\n\n## Requirements checklist\n\n- [ ] R5. Legacy `author` input is removed or rejected only after both source\n  content and production-generated-output evidence show that supported paths\n  no longer depend on it.\n- [ ] The final behavior for an accidental legacy post is explicit, tested,\n  and consistent with the approved post-cutover policy.\n\n## Unresolved requirement questions\n\n- Q3. Confirm whether accidental legacy input must fail the build with a clear\n  validation error or use another explicit unsupported-input behavior.\n\n## Research and supporting facts\n\n- Legacy references currently exist in both source content and production\n  consumers: two post files, the post layout, the feed, and the authoring\n  helper.\n- The existing test files are comments only, so no current evidence can\n  authorize a cutover.\n- There is no checked-in `_site`; generated-output evidence must come from a\n  fresh real Eleventy build after the preceding migration/rendering work.\n\n## Execution plan\n\nStatus: Draft\n\nTreat legacy removal as an evidence-gated compatibility state, not as a\ncleanup step. First establish a complete source scan for legacy keys and\ndirect field reads. Then run the production build over migrated content and\ninspect every affected public output, including the feed and all archive\npaths. Only when both evidence sets pass should the compatibility reader be\nremoved and the approved build-time rejection or equivalent unsupported-input\nbehavior be enabled.\n\nOrdered work:\n\n1. Define the exact scan scope: source front matter, templates, scripts,\n   tests/fixtures, documentation claims, and generated output.\n2. Run a repository content/implementation scan and fail the gate if any\n   supported source path still requires the scalar field.\n3. Run `npm run build` from the migrated repository and assert the expected\n   route set, author output, feed validity, and absence of legacy-dependent\n   rendering symptoms.\n4. Review the two evidence sets together; if either fails, retain\n   compatibility and record the dependency instead of cutting over.\n5. If both pass, remove the legacy normalization and implement the approved\n   invalid-input behavior, then add a regression test proving accidental\n   legacy metadata cannot silently pass.\n6. Re-run the full test/build evidence after the cutover and update the\n   maintained documentation to describe only the final supported contract.\n\n### Implementation decisions and open questions\n\n- Q3 controls whether invalid legacy input produces a clear build failure or\n  another approved result. Do not silently discard the value.\n- A source scan alone is insufficient: generated output must be inspected\n  through the real Eleventy build before rejection is enabled.\n- If the gate fails, the safe outcome is a documented transition state with\n  compatibility retained; the task must not force a rejection merely to close\n  the migration.\n\n### Documentation\n\nAfter successful cutover, update the maintained developer documentation to\nremove transitional wording and state the final structured metadata and\nlegacy-input behavior. If the gate does not pass, document the remaining\ncompatibility state and the evidence gap instead.\n\n### Task checklist\n\n- [ ] Define and run the complete source/reference scan.\n- [ ] Run and inspect a fresh production build.\n- [ ] Record pass/fail evidence for every affected public route.\n- [ ] Remove compatibility only after both evidence sets pass.\n- [ ] Add and run the final legacy-input regression test.\n- [ ] Update final documentation and parent requirement status.\n\n### Requirement verification\n\n- R5: The decisive check is a recorded pair: a repository-wide scan showing no\n  remaining supported dependency on the legacy field, followed by a fresh\n  `npm run build` whose post, home, blog, tag, and feed outputs contain the\n  expected structured-author results. The legacy rejection change is applied\n  only after both checks pass.\n- Final invalid-input behavior: an integration test supplies legacy front\n  matter through the normal content/build path and asserts the approved\n  failure or handling behavior, rather than testing only a helper in\n  isolation.\n\n### Additional implementation verification\n\n- Check the final route set against the pre-migration route inventory.\n- Search generated output for stale legacy markers, missing names,\n  `[object Object]`, malformed XML, and accidental empty author elements.\n- Ensure documentation and test fixtures do not falsely claim that the legacy\n  field remains supported after the gate closes."
  },
  "task_tree": {
    "all_dependencies_resolve": true,
    "all_parent_links_resolve": true,
    "coordinating_files": [
      "tasks/20260926-author-metadata-migration/000-main.md"
    ],
    "dependencies": [
      {
        "dependency": "tasks/20260926-author-metadata-migration/010-source-and-authoring.md",
        "resolves": true,
        "task": "tasks/20260926-author-metadata-migration/020-public-rendering.md"
      },
      {
        "dependency": "tasks/20260926-author-metadata-migration/010-source-and-authoring.md",
        "resolves": true,
        "task": "tasks/20260926-author-metadata-migration/030-legacy-cutover.md"
      },
      {
        "dependency": "tasks/20260926-author-metadata-migration/020-public-rendering.md",
        "resolves": true,
        "task": "tasks/20260926-author-metadata-migration/030-legacy-cutover.md"
      }
    ],
    "files": [
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": null,
        "path": "tasks/20260926-author-metadata-migration/000-main.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Migrate post author metadata to structured multi-author records"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260926-author-metadata-migration/000-main.md",
        "path": "tasks/20260926-author-metadata-migration/010-source-and-authoring.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 3,
        "title": "Define and migrate the structured author source model"
      },
      {
        "dependencies": [
          "tasks/20260926-author-metadata-migration/010-source-and-authoring.md"
        ],
        "has_execution_plan": true,
        "parent_task": "tasks/20260926-author-metadata-migration/000-main.md",
        "path": "tasks/20260926-author-metadata-migration/020-public-rendering.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 2,
        "title": "Render structured authors through public site generation"
      },
      {
        "dependencies": [
          "tasks/20260926-author-metadata-migration/010-source-and-authoring.md",
          "tasks/20260926-author-metadata-migration/020-public-rendering.md"
        ],
        "has_execution_plan": true,
        "parent_task": "tasks/20260926-author-metadata-migration/000-main.md",
        "path": "tasks/20260926-author-metadata-migration/030-legacy-cutover.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 2,
        "title": "Gate and complete legacy author-field removal"
      }
    ],
    "implementation_task_count": 3,
    "parent_links": [
      {
        "child": "tasks/20260926-author-metadata-migration/010-source-and-authoring.md",
        "parent": "tasks/20260926-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260926-author-metadata-migration/020-public-rendering.md",
        "parent": "tasks/20260926-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260926-author-metadata-migration/030-legacy-cutover.md",
        "parent": "tasks/20260926-author-metadata-migration/000-main.md",
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
    "semantic_deliverable_count": 3,
    "actual_task_count": 3,
    "deliverable_mappings": [
      {
        "deliverable_id": "AUTHOR-D1",
        "task_paths": [
          "tasks/20260926-author-metadata-migration/010-source-and-authoring.md",
          "tasks/20260926-author-metadata-migration/020-public-rendering.md"
        ],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Normalization contract is defined with the canonical source model in 010 and applied to every public consumer in 020, so dual-format acceptance holds through the migration window; the pre-content dual-format working state is folded into 010 rather than delivered first (recorded as a dependency issue)."
      },
      {
        "deliverable_id": "AUTHOR-D2",
        "task_paths": [
          "tasks/20260926-author-metadata-migration/020-public-rendering.md"
        ],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "020 owns post layout, feed, and the shared archive/list consumers together, adds real single/multi-author content fixtures, and proves output through one real Eleventy build across post, home, blog, tag, and feed routes."
      },
      {
        "deliverable_id": "AUTHOR-D3",
        "task_paths": [
          "tasks/20260926-author-metadata-migration/010-source-and-authoring.md"
        ],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "010 owns the canonical contract, migrates the full content inventory with preservation checks, and converts scripts/new-post.js in the same ownership so producers stop writing the legacy field."
      },
      {
        "deliverable_id": "AUTHOR-D4",
        "task_paths": [
          "tasks/20260926-author-metadata-migration/030-legacy-cutover.md"
        ],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "030 is a dedicated evidence-gated retirement: content/implementation scan plus a fresh production build over every affected route before compatibility removal and approved rejection, with the gate allowed to fail safely."
      }
    ],
    "mergeable_groups": [],
    "unmatched_tasks": [],
    "overpacked_tasks": [],
    "valid_layer_boundaries": [
      "tasks/20260926-author-metadata-migration/010-source-and-authoring.md",
      "tasks/20260926-author-metadata-migration/020-public-rendering.md",
      "tasks/20260926-author-metadata-migration/030-legacy-cutover.md"
    ],
    "automatic_layer_fragments": [],
    "dependency_issues": [
      "010 migrates all content to the canonical `authors` key and forbids reintroducing the legacy write form while templates still read `post.data.author`; the transitional normalization is specified only as legacy-scalar-to-singleton, with no required legacy-compatible view for the not-yet-migrated consumers, so the intermediate revision after 010 can build while silently dropping post bylines and feed author elements (AUTHOR-5 window risk).",
      "020 depends on all of 010 (helper conversion and full content migration included) although surface adoption needs only the normalization contract; the target treats surface adoption and content/tool migration as parallel branches off normalization. Minor at this fixture size."
    ],
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
        "status": "partial",
        "occurrences": [
          {
            "task_paths": [
              "tasks/20260926-author-metadata-migration/010-source-and-authoring.md",
              "tasks/20260926-author-metadata-migration/020-public-rendering.md"
            ],
            "description": "Content migration precedes consumer migration with an under-specified bridge: 010 writes only the canonical key and its normalization is one-directional (legacy scalar to singleton), leaving the 010-to-020 intermediate revision able to publish output that loses author display, contrary to the target's normalization-first ordering and AUTHOR-5."
          },
          {
            "task_paths": [
              "tasks/20260926-author-metadata-migration/010-source-and-authoring.md",
              "tasks/20260926-author-metadata-migration/020-public-rendering.md"
            ],
            "description": "Surface adoption is serialized behind the entire source/tooling child instead of only the normalization contract, mildly serializing work the target allows to proceed in parallel off normalization."
          }
        ]
      },
      "piecewise_crossing_evidence": {
        "status": "none",
        "occurrences": []
      }
    },
    "partition_quality_score": 85,
    "handoff_quality_score": 90,
    "summary": "The set partitions the migration into three coherent, independently acceptable deliverables plus a coordinating 000-main.md (excluded as it assigns no separate implementation work). All five approved outcomes are covered with named evidence: 010 delivers the canonical model, full content migration, and the authoring helper (AUTHOR-1/3); 020 moves post layout, feed, and shared archive consumers to the normalized model with one real production build over post, home, blog, tag, and feed outputs plus a transitional legacy-input build (AUTHOR-2/5); 030 is a dedicated evidence-gated retirement requiring a source scan and a fresh production build before removal and approved rejection (AUTHOR-4/5). Tests and documentation are embedded in the children that make each claim true, no per-surface or per-test-type tasks exist, and the important crossing is proven through the real Eleventy build at pre-cutover and post-cutover states rather than mocks or isolated helper tests. The one material weakness is sequencing: the normalization/compatibility half of the target's first deliverable is defined inside the content-migration task and only applied in the rendering task, and because 010 forbids the legacy write form while templates still read the legacy key, the intermediate revision after 010 is not guaranteed to preserve author output; combining normalization with generated-surface adoption (the target's sanctioned alternative) or requiring a legacy-compatible view would close this window."
  }
}
```
