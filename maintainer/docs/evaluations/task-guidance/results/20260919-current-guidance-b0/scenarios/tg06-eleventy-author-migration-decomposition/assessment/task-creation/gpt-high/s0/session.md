# Session — tg06-eleventy-author-migration-decomposition · task-creation-assessment-gpt-high-s0 · glm max

- Run: `20260924T192257.394136Z-task-guidance-semantic-tg06-eleventy-author-migration-decomposition-gpt-high-s0-6ebece0e`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `7af354d5cf491591…`)
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
  "response": "Created a draft parent task with five dependency-ordered subtasks. No implementation, build, or test changes were made.\n\nParent task: [000-main.md](/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T200521.904502Z-task-guidance-tg06-eleventy-author-migration-decomposition-high-13ca997e/workspace/tasks/20260919-author-metadata-migration/000-main.md)\n\nSubtasks:\n\n- [010-author-contract-and-transition.md](/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T200521.904502Z-task-guidance-tg06-eleventy-author-migration-decomposition-high-13ca997e/workspace/tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md)\n- [020-content-and-authoring-migration.md](/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T200521.904502Z-task-guidance-tg06-eleventy-author-migration-decomposition-high-13ca997e/workspace/tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md)\n- [030-rendering-and-output-migration.md](/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T200521.904502Z-task-guidance-tg06-eleventy-author-migration-decomposition-high-13ca997e/workspace/tasks/20260919-author-metadata-migration/030-rendering-and-output-migration.md)\n- [040-verification-and-legacy-removal.md](/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T200521.904502Z-task-guidance-tg06-eleventy-author-migration-decomposition-high-13ca997e/workspace/tasks/20260919-author-metadata-migration/040-verification-and-legacy-removal.md)\n- [050-documentation-and-release-handoff.md](/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T200521.904502Z-task-guidance-tg06-eleventy-author-migration-decomposition-high-13ca997e/workspace/tasks/20260919-author-metadata-migration/050-documentation-and-release-handoff.md)\n\nThe plan explicitly keeps the status as `Draft` and identifies three decisions requiring approval before execution:\n\n- The exact structured schema, with `authors: [{ name }]` recorded as the recommendation.\n- The HTML/archive and XML feed representation for multiple authors.\n- Whether the authoring tool accepts both legacy and new inputs during the transition.\n\nThe legacy-field removal is gated behind repository/content scans, production-generated post/archive/feed evidence, and a final build/test run after rejection. `git diff --check` passed; tests were intentionally not run because this was planning-only.",
  "task_files": {
    "tasks/20260919-author-metadata-migration/000-main.md": "# Structured post author metadata migration\n\nMigrate post authors from the current scalar `author` front-matter value to a\nstructured, ordered multi-author representation while preserving existing\ncontent and generated output throughout the transition. Execution is not\napproved by creating this task set.\n\n## Requirements checklist\n\n- [ ] Post metadata supports the agreed structured multi-author form, including\n      ordered authors and the single-author case.\n- [ ] Existing posts and any still-supported legacy inputs remain renderable\n      during the transition, with their author meaning preserved.\n- [ ] Post templates, shared archive/list surfaces, feeds, and authoring tools\n      consume and produce the structured form rather than depending on the\n      scalar legacy field.\n- [ ] The repository's existing posts are migrated safely without changing\n      their titles, body content, routes, tags, or intended author identity.\n- [ ] Production-generated pages and feeds preserve required author output for\n      single-author posts and correctly represent multiple authors.\n- [ ] Legacy `author` input is rejected or removed only after repository content\n      and generated-output evidence demonstrates that no supported path still\n      depends on it.\n- [ ] Maintained user/developer guidance describes the supported authoring form\n      and the completed transition.\n\n## Scope and workstreams\n\nThe migration covers post front matter and shared post defaults, the post\nlayout, the archive/list include used by the home page, blog archive, and tag\npages, the XML feed, `scripts/new-post.js`, the existing post fixtures, and\nproduction-build tests. Sitemap behavior is not an author consumer and should\nremain unchanged except for regression evidence. Generated `_site` output is\nverification evidence, not a source to edit.\n\nThe work is split so the author contract and compatibility policy are decided\nbefore content or templates change; content/tool and rendering changes can then\nproceed independently; the legacy form is removed only through the final\nevidence gate. Documentation is completed with the migration rather than\ncreating speculative standalone pages.\n\n## Unresolved requirement questions\n\n1. What is the approved structured shape and required identity field? The\n   recommended starting point is an ordered `authors` array whose entries have\n   a required `name` field, mapping `\"Ada Example\"` to\n   `authors: [{ name: \"Ada Example\" }]`. Adding IDs, URLs, or biographies\n   would expand the public contract and needs approval.\n2. What public representation is required for multiple authors in post pages,\n   archive/list output, and the feed? The implementation needs an approved\n   separator/markup policy for HTML and whether the feed emits one author\n   element per author or a structured nested form.\n3. During the transition, should the authoring tool accept both the legacy\n   scalar argument and the new collection, or should only repository content\n   be dual-read? The plan assumes a deliberately bounded compatibility window,\n   with any accepted legacy input normalized to the new model before the final\n   rejection gate.\n\n## Research and supporting facts\n\n- `content/posts/first.md` and `content/posts/second.md` use scalar\n  `author` values.\n- `content/posts/posts.json` supplies the shared post layout and `posts` tag.\n- `_includes/layouts/post.njk` renders `author` directly.\n- `content/feed.xml.njk` renders `post.data.author` directly into one feed\n  entry per post.\n- `_includes/postslist.njk` is shared by `content/index.njk`,\n  `content/blog.njk`, and `content/tag-pages.njk`; it currently renders titles\n  only, so it is an archive consumer that must be checked for the new\n  structured author display or deliberately kept author-independent.\n- `scripts/new-post.js` serializes the scalar `author` field and is the\n  authoring-tool boundary.\n- `tests/archive-output.test.js` and `tests/author-output.test.js` currently\n  contain comments describing intended coverage but no executable assertions.\n- `package.json` exposes `npm run build` through Eleventy and\n  `npm test` through Node's test runner.\n- `README.md` documents the generated site surfaces but does not document\n  post author front matter or the authoring tool.\n\n## Execution plan\n\nStatus: Draft\n\n1. Resolve the structured metadata and public rendering questions, then\n   record the compatibility window and the exact condition for rejecting\n   `author`.\n2. Add focused migration coverage and update the existing posts plus shared\n   defaults and authoring tool to use the agreed model, retaining only the\n   approved transitional read/normalization path.\n3. Update the post layout, archive/list surface, and feed to consume the\n   normalized author collection. Preserve routes, tags, post content, and\n   non-author site surfaces.\n4. Build the real site and assert generated post pages, home/blog/tag\n   archive output, and feed output for one and multiple authors. Search source\n   content, templates, tools, and generated output for remaining legacy\n   dependencies.\n5. Only when the evidence gate is green, remove or reject the legacy form.\n   Rebuild and rerun the full focused suite after that change.\n6. Update the smallest maintained documentation surface with the supported\n   front-matter/tool contract, transition status, and verification boundary.\n\n### Implementation decisions and open questions\n\n- The exact `authors` schema, HTML/feed representation, and authoring-tool\n  compatibility API remain open and require approval before execution.\n- Recommended compatibility behavior is dual-read/normalize during migration,\n  followed by explicit rejection of scalar `author` only after content and\n  generated-output scans plus production-build tests pass.\n- No URL, title, body, tag, or sitemap contract should change as part of this\n  migration.\n\n### Documentation\n\n- Update `README.md` or the owning developer documentation only after the\n  supported schema and compatibility status are implemented and verified.\n- Document the authoring-tool input and the single-/multi-author examples.\n- Do not add a placeholder documentation directory or edit generated output.\n\n### Task checklist\n\n- [ ] Complete `tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md`.\n- [ ] Complete `tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md`.\n- [ ] Complete `tasks/20260919-author-metadata-migration/030-rendering-and-output-migration.md`.\n- [ ] Complete `tasks/20260919-author-metadata-migration/040-verification-and-legacy-removal.md`.\n- [ ] Complete `tasks/20260919-author-metadata-migration/050-documentation-and-release-handoff.md`.\n- [ ] Append completion notes only after all requirements have evidence.\n\n### Requirement verification\n\n- Structured metadata and transition compatibility: contract tests plus a\n  production build containing migrated single-author content and a\n  multi-author fixture.\n- Template, archive, and feed migration: generated-output assertions at the\n  public HTML/XML boundary for post pages, home/blog/tag pages, and the feed.\n- Safe existing-content migration: source diff/content inspection plus\n  generated route, title, body, tag, and author-identity assertions.\n- Legacy rejection gate: repository-wide source/content scan and generated\n  output scan show no remaining supported dependency, followed by a build and\n  test run with the legacy form rejected.\n- Documentation: review the maintained guidance against the implemented\n  schema and tool behavior.\n\n### Additional implementation verification\n\n- Confirm XML remains well-formed after multiple author elements or the\n  approved nested representation is emitted.\n- Confirm HTML escaping and author ordering with names containing punctuation\n  or characters that require escaping.\n- Confirm archives and tag pages still render with the existing collection\n  ordering and routes.",
    "tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md": "# Define the structured author contract and transition policy\n\nChoose and document the structured author metadata contract, its public\nrendering shape, and the bounded compatibility policy that later subtasks must\nimplement.\n\nParent Task: tasks/20260919-author-metadata-migration/000-main.md\n\n## Requirements checklist\n\n- [ ] The structured multi-author shape and required fields are approved.\n- [ ] Single-author and multiple-author ordering semantics are explicit.\n- [ ] HTML post/archive rendering and XML feed representation are explicit.\n- [ ] The transition behavior for legacy `author` input is explicit,\n      including the final rejection condition.\n- [ ] The authoring-tool input contract is explicit enough for implementation\n      without inventing a public API.\n\n## Research and supporting facts\n\nThe current repository has scalar `author` values in both post files,\ndirect scalar rendering in the post layout and feed, and scalar serialization\nin `scripts/new-post.js`. The archive include does not currently render an\nauthor, so its required public behavior must be decided rather than inferred\nfrom existing output.\n\n## Execution plan\n\nStatus: Draft\n\n1. Compare the current scalar contract with the proposed structured\n   representation and define the lossless mapping for existing posts.\n2. Decide the author ordering, HTML separators/markup, feed shape, escaping\n   expectations, and authoring-tool arguments.\n3. Define the compatibility window: what reads legacy input, what writes only\n   the new field, and what repository/build evidence permits rejection.\n4. Record the accepted contract in this task and hand it to the content,\n   rendering, verification, and documentation subtasks.\n\n### Implementation decisions and open questions\n\n- Recommended schema: ordered `authors` entries with required `name`; confirm\n  before execution.\n- Confirm whether archive rows should gain a byline or remain intentionally\n  author-independent while still avoiding legacy-field access.\n- Confirm whether the feed uses repeated author elements or an approved nested\n  structure.\n\n### Documentation\n\nRecord the accepted schema and transition policy in the implementation's\nowning developer guidance during the documentation handoff; this subtask\nshould not create a speculative public guide.\n\n### Task checklist\n\n- [ ] Resolve and record the schema decision.\n- [ ] Resolve and record HTML/feed output decisions.\n- [ ] Resolve and record the compatibility and rejection gate.\n- [ ] Pass the contract to dependent subtasks.\n\n### Requirement verification\n\nReview the recorded contract against every consumer identified in the parent\ntask and confirm that it supplies enough information to test source metadata,\nHTML output, XML output, and tool serialization.\n\n### Additional implementation verification\n\nCheck that the proposed contract does not require changing URLs, titles,\ncontent, tags, collection ordering, or unrelated sitemap behavior.",
    "tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md": "# Migrate post content and authoring tools\n\nConvert existing post metadata and the new-post generator to the approved\nstructured author model while preserving a bounded transitional read path.\n\nParent Task: tasks/20260919-author-metadata-migration/000-main.md\nDepends On: tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md\n\n## Requirements checklist\n\n- [ ] Existing posts are converted to the approved structured field without\n      changing their author identity or unrelated front matter/body content.\n- [ ] Shared post defaults and any metadata normalization support the approved\n      model.\n- [ ] `scripts/new-post.js` emits the approved structured form and follows the\n      approved compatibility API.\n- [ ] Transitional legacy handling is limited to the approved window and does\n      not hide malformed new metadata.\n\n## Research and supporting facts\n\n`content/posts/first.md` and `content/posts/second.md` are the only current\npost files and each has one scalar author. `content/posts/posts.json` owns\nshared post layout/tag metadata. `scripts/new-post.js` currently accepts\n`(title, author)` and writes a scalar field.\n\n## Execution plan\n\nStatus: Draft\n\n1. Add or update focused tests for tool serialization and metadata\n   normalization according to the contract from subtask 010.\n2. Migrate the existing post front matter mechanically and inspect the diff\n   for preservation of titles, body text, tags, and author identity.\n3. Update shared defaults or configuration needed for the structured field.\n4. Update the new-post tool to emit the new model and implement only the\n   approved transition behavior.\n5. Leave final legacy rejection to subtask 040 after all consumers and\n   evidence are ready.\n\n### Implementation decisions and open questions\n\n- Do not decide a new tool signature here; use the contract approved by\n  subtask 010.\n- Do not delete legacy handling before the production-output evidence gate.\n- Do not rewrite generated `_site` files or alter post routes as part of the\n  metadata conversion.\n\n### Documentation\n\nProvide the final tool invocation/examples and migration note to subtask 050;\ndo not publish guidance until the implementation is verified.\n\n### Task checklist\n\n- [ ] Add focused tool/metadata tests.\n- [ ] Migrate all existing post metadata.\n- [ ] Update shared post metadata configuration if required.\n- [ ] Update the authoring tool.\n- [ ] Record source-preservation evidence for the migrated posts.\n\n### Requirement verification\n\nUse tool-level tests for exact serialization and a production build with the\nmigrated repository posts to verify that front matter remains consumable.\nInspect the source diff for preservation of non-author fields and body text.\n\n### Additional implementation verification\n\nExercise one single-author and one multiple-author tool input, including\nescaping-sensitive names, under the approved API.",
    "tasks/20260919-author-metadata-migration/030-rendering-and-output-migration.md": "# Migrate templates, archives, and feeds\n\nMove every generated author consumer from the scalar field to the normalized\nstructured author collection while preserving the site's existing public\nsurfaces.\n\nParent Task: tasks/20260919-author-metadata-migration/000-main.md\nDepends On: tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md\nDepends On: tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md\n\n## Requirements checklist\n\n- [ ] The post layout renders the approved single- and multi-author form.\n- [ ] The shared archive/list include and its home, blog, and tag-page\n      consumers follow the approved author behavior.\n- [ ] The feed renders the approved author representation for each post.\n- [ ] No template or feed consumer depends on the scalar legacy field after\n      the approved transition point.\n- [ ] Existing routes, collection ordering, and non-author output remain\n      stable.\n\n## Research and supporting facts\n\n`_includes/layouts/post.njk` directly prints `author`.\n`content/feed.xml.njk` directly prints `post.data.author`.\n`_includes/postslist.njk` is reused by the home page, blog archive, and tag\npages but currently prints only titles. The output contract from subtask 010\nmust determine whether it gains author markup or remains deliberately\nauthor-independent.\n\n## Execution plan\n\nStatus: Draft\n\n1. Update the post layout to iterate or otherwise consume the normalized\n   author collection using the approved escaping and ordering rules.\n2. Update the shared archive/list surface if the approved archive contract\n   exposes authors; ensure all three archive consumers receive the same\n   behavior.\n3. Update the feed to emit the approved XML representation for each author.\n4. Build the site with migrated single-author content and a multiple-author\n   fixture, then inspect generated post, archive, tag, and feed output.\n5. Keep the legacy compatibility branch available until subtask 040's final\n   source/content/output evidence permits its removal.\n\n### Implementation decisions and open questions\n\n- Rendering shape, separators, and feed structure come from subtask 010.\n- A shared normalization boundary is preferred so templates do not each\n  implement scalar-to-array compatibility logic; confirm the appropriate\n  Eleventy boundary during implementation.\n- Archive author display remains conditional on the approved public contract.\n\n### Documentation\n\nProvide verified output examples and any feed compatibility note to subtask\n050. Do not document generated output that has not been checked by a build.\n\n### Task checklist\n\n- [ ] Update the post layout.\n- [ ] Update the shared archive/list include as required.\n- [ ] Update the feed template.\n- [ ] Build and inspect all affected generated surfaces.\n- [ ] Confirm unrelated routes and collection behavior remain stable.\n\n### Requirement verification\n\nUse production-build tests and generated-output assertions for a post page,\nhome page, blog archive, tag page, and feed. Assertions must cover both\nsingle- and multiple-author cases and the approved public representation.\n\n### Additional implementation verification\n\nValidate HTML/XML escaping, author order, empty/invalid metadata behavior\nonly where the approved contract specifies it, and unchanged sitemap URLs.",
    "tasks/20260919-author-metadata-migration/040-verification-and-legacy-removal.md": "# Verify the migration and remove the legacy dependency\n\nTurn the current placeholder coverage into evidence at the production\ngenerated-output boundary, then remove or reject the scalar legacy form only\nwhen the agreed gate is satisfied.\n\nParent Task: tasks/20260919-author-metadata-migration/000-main.md\nDepends On: tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md\nDepends On: tasks/20260919-author-metadata-migration/030-rendering-and-output-migration.md\n\n## Requirements checklist\n\n- [ ] Archive and author-output tests execute real production build behavior\n      rather than only documenting intended coverage.\n- [ ] Tests cover migrated single-author content and multiple authors across\n      post pages, archives, tag pages, and feeds.\n- [ ] Source/content scans and generated-output inspection show no supported\n      dependency on scalar `author` before rejection.\n- [ ] The legacy form is rejected or removed only after the evidence gate.\n- [ ] A final build and test run passes after legacy rejection.\n\n## Research and supporting facts\n\nThe existing `tests/archive-output.test.js` and\n`tests/author-output.test.js` are comments only. `npm run build` is the\nproduction Eleventy build and `npm test` runs Node tests. The parent task\nrequires evidence that crosses the generated-output boundary, not only unit\ntests with mocked post data.\n\n## Execution plan\n\nStatus: Draft\n\n1. Replace the placeholder tests with executable tests that invoke the\n   production build or its real output path and inspect generated files.\n2. Add coverage for route preservation, author ordering/identity, archive\n   visibility, feed structure, and existing non-author output.\n3. Run repository-wide searches over source content, templates, scripts,\n   tests, and generated output to classify every remaining `author` reference\n   as approved compatibility code, documentation, or an obsolete dependency.\n4. Apply the approved legacy rejection/removal only after the search and\n   generated-output assertions are clean.\n5. Rebuild and rerun the complete focused suite after rejection; retain the\n   evidence and report any gated test that could not run.\n\n### Implementation decisions and open questions\n\n- The exact assertion strings and feed shape follow subtask 010.\n- A search result alone is not sufficient evidence; it must be combined with\n  a successful production build and generated-output assertions.\n- Do not reject legacy content merely because migrated fixtures no longer use\n  it; verify all supported content and tool paths first.\n\n### Documentation\n\nProvide the final test commands, evidence boundary, and legacy-removal date\nor release condition to subtask 050.\n\n### Task checklist\n\n- [ ] Implement real archive-output coverage.\n- [ ] Implement real author-output coverage.\n- [ ] Add source/content/generated-output dependency scans.\n- [ ] Pass the legacy rejection gate.\n- [ ] Rebuild and rerun tests after rejection.\n\n### Requirement verification\n\nThe decisive evidence is a clean production build plus generated HTML/XML\nassertions for all affected surfaces, followed by a clean post-rejection\nbuild/test run. Source and content scans corroborate that no supported path\nstill relies on scalar `author`.\n\n### Additional implementation verification\n\nCheck that tests collect and exit cleanly, do not use test-only template\nshortcuts, and do not leave generated artifacts or temporary fixtures in the\nrepository.",
    "tasks/20260919-author-metadata-migration/050-documentation-and-release-handoff.md": "# Document and hand off the completed author migration\n\nUpdate the smallest maintained documentation surface with the supported\nstructured author model, authoring workflow, compatibility status, and\nverification evidence after implementation is complete.\n\nParent Task: tasks/20260919-author-metadata-migration/000-main.md\nDepends On: tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md\nDepends On: tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md\nDepends On: tasks/20260919-author-metadata-migration/030-rendering-and-output-migration.md\nDepends On: tasks/20260919-author-metadata-migration/040-verification-and-legacy-removal.md\n\n## Requirements checklist\n\n- [ ] Maintained guidance documents the implemented structured metadata and\n      single-/multi-author examples.\n- [ ] The authoring-tool usage and compatibility/rejection status are current.\n- [ ] Documentation claims are backed by the completed production-build and\n      output evidence.\n- [ ] No placeholder or target-only guidance is presented as current behavior.\n\n## Research and supporting facts\n\n`README.md` currently describes the generated site surfaces but not post\nfront matter or `scripts/new-post.js`. `docs/development/index.md` contains\nonly an archive-pagination note, and the documentation policy requires the\nsmallest structure owned by the affected subsystem. The repository has no\nexisting author-specific guide.\n\n## Execution plan\n\nStatus: Draft\n\n1. Review the accepted contract from subtask 010 and the verified behavior\n   from subtasks 020\u2013040.\n2. Update `README.md` or the most appropriate existing developer-facing\n   location with the current front-matter/tool examples and transition status.\n3. Link the documented behavior to the actual build/test evidence without\n   claiming unsupported legacy behavior.\n4. Review the final task checklist and hand off unresolved or deferred scope.\n\n### Implementation decisions and open questions\n\n- Prefer extending `README.md` unless implementation reveals an existing\n  authoring-specific owner; do not create a new documentation hierarchy for\n  one compact contract.\n- Document only behavior that passed the final evidence gate.\n\n### Documentation\n\nThis subtask is the documentation change. Follow\n`docs/development/documentation.md` and keep the public/developer guidance\nwith the capability it describes.\n\n### Task checklist\n\n- [ ] Select the owning maintained documentation location.\n- [ ] Document structured metadata and tool usage.\n- [ ] Document transition/rejection status based on evidence.\n- [ ] Review links, examples, and claims for consistency with implementation.\n\n### Requirement verification\n\nCompare every documented example and compatibility claim with the final\nproduction build, generated-output assertions, source scan, and post-rejection\ntest run from subtask 040.\n\n### Additional implementation verification\n\nConfirm the documentation does not instruct authors to use the removed scalar\nfield and does not imply that generated `_site` output is a source of truth."
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
        "title": "Structured post author metadata migration"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260919-author-metadata-migration/000-main.md",
        "path": "tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Define the structured author contract and transition policy"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260919-author-metadata-migration/000-main.md",
        "path": "tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 4,
        "title": "Migrate post content and authoring tools"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260919-author-metadata-migration/000-main.md",
        "path": "tasks/20260919-author-metadata-migration/030-rendering-and-output-migration.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Migrate templates, archives, and feeds"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260919-author-metadata-migration/000-main.md",
        "path": "tasks/20260919-author-metadata-migration/040-verification-and-legacy-removal.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Verify the migration and remove the legacy dependency"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260919-author-metadata-migration/000-main.md",
        "path": "tasks/20260919-author-metadata-migration/050-documentation-and-release-handoff.md",
        "phase_terms": [
          "documentation"
        ],
        "plan_status": "Draft",
        "requirement_count": 4,
        "title": "Document and hand off the completed author migration"
      }
    ],
    "implementation_task_count": 5,
    "parent_links": [
      {
        "child": "tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md",
        "parent": "tasks/20260919-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md",
        "parent": "tasks/20260919-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260919-author-metadata-migration/030-rendering-and-output-migration.md",
        "parent": "tasks/20260919-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260919-author-metadata-migration/040-verification-and-legacy-removal.md",
        "parent": "tasks/20260919-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260919-author-metadata-migration/050-documentation-and-release-handoff.md",
        "parent": "tasks/20260919-author-metadata-migration/000-main.md",
        "resolves": true
      }
    ],
    "phase_named_files": [
      "tasks/20260919-author-metadata-migration/050-documentation-and-release-handoff.md"
    ],
    "task_directory_count": 1,
    "task_file_count": 6
  }
}


**Assistant** *(reasoning present)*

{
  "schema_version": 3,
  "scenario_id": "tg06-eleventy-author-migration-decomposition",
  "assessment": {
    "outcome_coverage": "complete",
    "missing_outcomes": [],
    "added_obligations": [
      "050 requires maintained user/developer documentation of the author model plus a release-handoff checklist review; neither the natural request nor AUTHOR-1..5 asks for a standalone documentation deliverable."
    ],
    "semantic_deliverable_count": 4,
    "actual_task_count": 5,
    "deliverable_mappings": [
      {
        "deliverable_id": "AUTHOR-D1",
        "task_paths": [
          "tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md",
          "tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md",
          "tasks/20260919-author-metadata-migration/030-rendering-and-output-migration.md"
        ],
        "coverage": "partial",
        "coherence": "fragmented",
        "reason": "Dual-format normalization never forms its own working-state boundary: the contract/policy is a decision record in 010, normalization support is embedded in 020, and 030 only 'prefers' a shared normalization boundary. No task completion leaves the site safely accepting old and new content as an isolated result."
      },
      {
        "deliverable_id": "AUTHOR-D2",
        "task_paths": [
          "tasks/20260919-author-metadata-migration/030-rendering-and-output-migration.md"
        ],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "030 moves post layout, shared archive/list include, and feed to the normalized model with production-build generated-output assertions for single and multiple authors; page/archive/feed stay together instead of becoming per-template tasks."
      },
      {
        "deliverable_id": "AUTHOR-D3",
        "task_paths": [
          "tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md"
        ],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "020 migrates existing posts, shared defaults, and the new-post tool under one owner with source-preservation evidence, avoiding the content-vs-helper split the target flags; it also absorbs part of D1's normalization work."
      },
      {
        "deliverable_id": "AUTHOR-D4",
        "task_paths": [
          "tasks/20260919-author-metadata-migration/040-verification-and-legacy-removal.md"
        ],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "040 gates scalar-author rejection on repository scans plus generated-output evidence and requires a post-rejection build/test run, matching the evidence-gated retirement deliverable; it additionally hosts the whole migration test suite (see evidence_reownership)."
      }
    ],
    "mergeable_groups": [
      {
        "task_paths": [
          "tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md",
          "tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md"
        ],
        "reason": "010 only records schema/rendering/transition decisions that acquire value when 020 implements them; recording the contract inside the first implementation delivery (or the parent plan) loses no independent product."
      },
      {
        "task_paths": [
          "tasks/20260919-author-metadata-migration/050-documentation-and-release-handoff.md"
        ],
        "reason": "Documentation and handoff are work within the deliveries they describe: schema/tool guidance belongs with 010/020 and evidence-backed status with 040; no approved outcome requires a standalone docs deliverable."
      }
    ],
    "unmatched_tasks": [
      "tasks/20260919-author-metadata-migration/050-documentation-and-release-handoff.md"
    ],
    "overpacked_tasks": [],
    "valid_layer_boundaries": [
      "tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md",
      "tasks/20260919-author-metadata-migration/030-rendering-and-output-migration.md",
      "tasks/20260919-author-metadata-migration/040-verification-and-legacy-removal.md"
    ],
    "automatic_layer_fragments": [],
    "dependency_issues": [
      "030 depends on 020, although the target treats generated-surface migration and content/tool migration as independent siblings that each depend only on normalization (D2 and D3 over D1). Because normalization is embedded in 020 rather than standalone, rendering must wait for content migration, serializing independently deliverable work; harm is low since 030 also wants migrated content for its builds.",
      "040 applies decisions recorded in 010 without declaring that dependency; it is satisfied only transitively via 020/030."
    ],
    "crossing_ownership": "complete",
    "fragmentation_severity": "low",
    "fragmentation_ratio": 1.25,
    "quality_metrics": {
      "fragmentation": {
        "status": "low",
        "occurrences": [
          {
            "task_paths": [
              "tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md"
            ],
            "description": "Standalone contract/policy decision task separated from the compatibility delivery it enables — the target's 'schema tasks separated from compatibility delivery' pattern."
          },
          {
            "task_paths": [
              "tasks/20260919-author-metadata-migration/050-documentation-and-release-handoff.md"
            ],
            "description": "Documentation/handoff as a final horizontal child outside the deliveries it documents, though no approved outcome requires an independent documentation result."
          }
        ]
      },
      "phase_only_children": {
        "status": "partial",
        "occurrences": [
          {
            "task_paths": [
              "tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md"
            ],
            "description": "Decision-recording child whose checklist completes only when 020/030 implement the recorded contract; it produces no buildable or user-visible result of its own."
          },
          {
            "task_paths": [
              "tasks/20260919-author-metadata-migration/050-documentation-and-release-handoff.md"
            ],
            "description": "Documentation child that only completes the already-delivered migration; its content re-exports 010's contract, 020's tool examples, and 040's evidence rather than delivering a required outcome."
          }
        ]
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
              "tasks/20260919-author-metadata-migration/030-rendering-and-output-migration.md",
              "tasks/20260919-author-metadata-migration/040-verification-and-legacy-removal.md"
            ],
            "description": "040, the final verification child, implements the entire executable generated-output suite (author/archive output across post pages, home/blog/tag archives, and feeds) that evidences the surface-migration delivery, while 030 also claims production-build assertions — decisive AUTHOR-2 evidence is split between a delivery child and a horizontal verification child."
          }
        ]
      },
      "unsafe_dependencies": {
        "status": "partial",
        "occurrences": [
          {
            "task_paths": [
              "tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md",
              "tasks/20260919-author-metadata-migration/030-rendering-and-output-migration.md"
            ],
            "description": "030→020 dependency serializes content/tool migration ahead of generated-surface migration; the target's dependency model makes them parallel over D1. No broken intermediate state is permitted (020 and 030 each verify a production build), so the instance is limited."
          }
        ]
      },
      "piecewise_crossing_evidence": {
        "status": "none",
        "occurrences": []
      }
    },
    "partition_quality_score": 0,
    "handoff_quality_score": 0,
    "summary": "The set preserves all five approved outcomes and its core maps cleanly onto the target: 020 is content+tools (D3), 030 is generated surfaces (D2), and 040 is evidence-gated legacy retirement (D4), with per-template, per-test-type, and content-vs-helper fragmentation avoided and removal correctly gated on scans plus generated-output evidence. Two bookend tasks are phase-like: 010 records contract/transition decisions that only 020/030 realize, and 050 hoists documentation/handoff that no approved outcome requires independently, so both are mergeable. Dual-format normalization (D1) never becomes its own working-state boundary — it is smeared across a decision task, embedded support in 020, and a 'preferred' boundary in 030 — and 030's dependency on 020 serializes work the target treats as parallel. The decisive crossing (real front matter through normalization and the production Eleventy build into pages, archives, and feeds) is named in 020, 030, and 040, including a post-rejection rebuild, so crossing ownership is complete; 040's centralization of the executable output suite partially re-owns evidence that belongs with the surface-migration child."
  }
}
