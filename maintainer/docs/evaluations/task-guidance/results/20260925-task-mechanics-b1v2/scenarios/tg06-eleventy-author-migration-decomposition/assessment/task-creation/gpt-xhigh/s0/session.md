# Session — tg06-eleventy-author-migration-decomposition · task-creation-assessment-gpt-xhigh-s0 · glm max

- Run: `20260925T204643.662697Z-task-guidance-semantic-tg06-eleventy-author-migration-decomposition-gpt-xhigh-s0-e408ad84`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `3a4a41b66a08c83d…`)
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
  "response": "Created a draft task structure without changing implementation, content, templates, tests, or generated output.\n\n- [Main task and execution plan](</Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T201531.700707Z-task-guidance-tg06-eleventy-author-migration-decomposition-xhigh-706f7ec3/workspace/tasks/20260925-author-metadata-migration/000-main.md>)\n- [Metadata contract, content migration, and authoring tool](</Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T201531.700707Z-task-guidance-tg06-eleventy-author-migration-decomposition-xhigh-706f7ec3/workspace/tasks/20260925-author-metadata-migration/010-metadata-content-tooling.md>)\n- [Production rendering and generated-output evidence](</Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T201531.700707Z-task-guidance-tg06-eleventy-author-migration-decomposition-xhigh-706f7ec3/workspace/tasks/20260925-author-metadata-migration/020-rendering-and-output.md>)\n- [Cutover gate and legacy rejection](</Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T201531.700707Z-task-guidance-tg06-eleventy-author-migration-decomposition-xhigh-706f7ec3/workspace/tasks/20260925-author-metadata-migration/030-cutover-and-rejection.md>)\n\nThe plan is `Draft` and execution has not started. It explicitly preserves legacy compatibility until:\n\n1. all existing posts are migrated;\n2. templates, archives, feeds, and authoring tools use the canonical model;\n3. a real Eleventy build verifies generated output; and\n4. source/content scans show no remaining production dependency.\n\nThe exact structured author schema, archive display behavior, feed representation, and rejection boundary are recorded as approval questions rather than being invented. `git diff --check` passes; no runtime tests were run because this was planning-only.",
  "task_files": {
    "tasks/20260925-author-metadata-migration/000-main.md": "# Migrate post authors to structured multi-author metadata\n\nPlan the staged migration from the post front matter `author` string to an\napproved structured multi-author representation while preserving existing\ncontent and generated-site behavior until the repository proves that the\nlegacy form is no longer needed.\n\n## Requirements checklist\n\n- [ ] Adopt an approved canonical structured multi-author field and use it as\n  the only author metadata consumed by production rendering after cutover.\n- [ ] Preserve a compatibility path for legacy `author` content during the\n  transition, so existing posts and builds continue to work while content is\n  being migrated.\n- [ ] Move post templates, archive/listing paths, feeds, and the post-authoring\n  tool to the canonical multi-author model, including deterministic rendering\n  for more than one author.\n- [ ] Migrate every existing post safely without changing its title, body,\n  route, or unrelated front matter.\n- [ ] Reject the legacy form only after generated-output evidence and source\n  content evidence demonstrate that no supported content or production path\n  still depends on it.\n- [ ] Update maintained authoring/development documentation to describe the\n  canonical field, transition boundary, and any intentional compatibility or\n  rejection behavior.\n\n## Scope and workstreams\n\nThe work is split by independently reviewable boundaries:\n\n- [Metadata contract, content migration, and authoring tool](./010-metadata-content-tooling.md)\n  owns the canonical shape, transition normalization, existing-post rewrite,\n  and generated front matter.\n- [Production rendering and generated-output evidence](./020-rendering-and-output.md)\n  owns post pages, archive/listing routes, feeds, and tests that cross the\n  real Eleventy build.\n- [Cutover gate and legacy rejection](./030-cutover-and-rejection.md) owns\n  the final dependency audit and the strict rejection change after the\n  evidence gate passes.\n\n## Subtasks\n\n- [ ] `tasks/20260925-author-metadata-migration/010-metadata-content-tooling.md`\n- [ ] `tasks/20260925-author-metadata-migration/020-rendering-and-output.md`\n- [ ] `tasks/20260925-author-metadata-migration/030-cutover-and-rejection.md`\n\nThe task does not include unrelated archive pagination, URL redesign, author\nprofiles, or changes to post body content.\n\n## Unresolved requirement questions and decisions\n\n- The repository does not specify the exact structured author schema. Confirm\n  the public front matter shape before execution. Recommendation, not yet an\n  approved decision: use an `authors` array whose entries are structured\n  records with a required display `name`, leaving room for stable identity or\n  profile fields without forcing them into this migration.\n- Confirm whether archive/list pages should newly display author names or only\n  route their existing post data through the canonical field. The migration\n  must make all author-aware archive rendering canonical; adding visible author\n  text changes archive output and therefore needs an explicit product choice.\n- Confirm the desired feed representation for multiple authors. Recommendation,\n  not yet an approved decision: preserve the existing feed element shape and\n  emit one author element per canonical author in source order.\n- Confirm the enforcement boundary for legacy rejection. Recommendation, not\n  yet an approved decision: fail the production build with an actionable\n  message when a post still contains `author`, and make the authoring tool\n  generate only the canonical field.\n\n## Research and supporting facts\n\n- Existing posts use a scalar `author` front matter value in\n  `content/posts/first.md` and `content/posts/second.md`.\n- `_includes/layouts/post.njk` renders the scalar directly, while\n  `content/feed.xml.njk` reads `post.data.author` directly.\n- `content/index.njk`, `content/blog.njk`, and `content/tag-pages.njk` all\n  share `_includes/postslist.njk`; that partial currently renders titles only,\n  so archive author behavior must be decided and then covered explicitly.\n- `scripts/new-post.js` currently emits the legacy field through\n  `frontMatter(title, author)`.\n- `tests/archive-output.test.js` and `tests/author-output.test.js` are\n  placeholders rather than decisive generated-output tests.\n- The production output directory is `_site/` and is ignored by Git. The\n  verification plan must therefore assert against a real build or a\n  deliberately captured route/output manifest rather than relying on committed\n  generated files.\n- `README.md` describes the generated site at a high level but does not\n  document post front matter or the authoring helper. `docs/development/index.md`\n  currently contains only an archive-pagination note.\n\n## Execution plan\n\nStatus: Draft\n\nThe migration will use a canonical-data boundary between front matter and\ntemplates. During the transition, that boundary accepts the legacy scalar and\nnormalizes it to the canonical multi-author value; templates, feeds, archives,\nand the authoring helper depend only on the canonical value. Existing posts are\nthen rewritten at the front matter boundary with a narrow, content-preserving\ntransform. The compatibility branch remains in place until the final audit\nproves that committed content and production consumers no longer use it.\n\nThe production-output boundary is the decisive integration point. A real\nEleventy build must continue to produce the existing route set, individual\npost output, archive/tag pages, feed, and sitemap while emitting the approved\nmulti-author result. Tests must inspect generated output and source content,\nnot only mocked template data. Only after those checks pass may the\nnormalization boundary become strict and reject legacy `author`.\n\n### Implementation decisions and open questions\n\n- Treat the exact `authors` schema, archive display choice, feed shape, and\n  rejection surface listed above as approval questions. Do not begin\n  implementation with an invented public contract.\n- Keep the compatibility conversion at one data boundary so no template or\n  feed needs to branch on old versus new front matter.\n- Make migration idempotent and narrow: alter only the author field and its\n  required serialization, preserve title/body/unrelated front matter, and\n  report files that do not match the expected shape instead of guessing.\n- Preserve author ordering from source content in post pages, archives, and\n  feeds unless the approved schema explicitly defines another ordering.\n- Treat generated route preservation and author rendering as one production\n  check. Component-level assertions alone are not sufficient evidence for the\n  migration.\n\n### Documentation\n\nAfter the behavior is implemented, update the maintained documentation owned by\nthis fixture: document the canonical post front matter and authoring helper in\n`README.md`, and add only the smallest development note needed to explain the\ntransition/rejection gate. Do not add a placeholder documentation hierarchy.\n\n### Task checklist\n\n- [ ] Approve the canonical structured author schema and the archive/feed\n  output decisions.\n- [ ] Complete `010-metadata-content-tooling.md`.\n- [ ] Complete `020-rendering-and-output.md`.\n- [ ] Complete `030-cutover-and-rejection.md` after the first two subtasks\n  provide their evidence.\n- [ ] Update the maintained documentation in the owning implementation\n  subtask.\n- [ ] Review the final requirement evidence and leave this parent task in a\n  state that clearly distinguishes completed checks from any human approval\n  still needed.\n\n### Requirement verification\n\n- Canonical field and transition compatibility: decisive evidence is the\n  metadata/content/tooling subtask's normalization and migration checks plus a\n  real build that consumes both a legacy-shaped transition fixture and the\n  migrated posts before strict rejection.\n- Templates, archives, and feeds: decisive evidence is the rendering\n  subtask's production-build test, which checks post pages, `/`, `/blog/`,\n  every generated tag page, and `/feed/feed.xml` for canonical multi-author\n  output and absence of undefined author data.\n- Safe migration of existing content: decisive evidence is a source inventory\n  and migration assertion that every existing post has the canonical field and\n  that title/body/unrelated front matter remain unchanged.\n- Conditional legacy rejection: decisive evidence is the cutover subtask's\n  ordered audit\u2014source/reference scan, generated-output assertions, and the\n  complete test/build run\u2014recorded before the strict rejection is enabled.\n- Documentation: decisive evidence is inspection of the updated maintained\n  authoring/development documentation against the final implemented contract.\n\n### Additional implementation verification\n\n- Run the repository's declared test and build commands with the normal\n  production path; do not count placeholder or mocked-only checks as proof.\n- Check for accidental output changes outside author metadata by comparing the\n  pre-migration and post-migration route sets and stable page fields.\n- Verify that malformed or mixed old/new metadata is reported clearly rather\n  than silently discarded during migration or cutover.",
    "tasks/20260925-author-metadata-migration/010-metadata-content-tooling.md": "# Define and migrate the post author metadata contract\n\nOwn the canonical structured author field, its temporary compatibility\nnormalization, safe conversion of existing posts, and the authoring helper that\ncreates new posts.\n\nParent Task: tasks/20260925-author-metadata-migration/000-main.md\n\n## Requirements checklist\n\n- [ ] Implement the approved canonical structured multi-author front matter\n  shape and a single normalization boundary for consumers.\n- [ ] Continue accepting the legacy scalar `author` during the approved\n  transition window, with deterministic conversion to the canonical value.\n- [ ] Convert every existing post to the canonical field without changing\n  title, body, route-affecting metadata, or unrelated front matter.\n- [ ] Make `scripts/new-post.js` generate the canonical field and support the\n  approved multi-author input.\n- [ ] Provide evidence that the migration is complete and repeatable before\n  the legacy form is rejected.\n\n## Unresolved requirement questions and decisions\n\n- Use the schema approved by the parent task; do not choose a public field\n  shape here. The working recommendation is `authors` as an ordered array of\n  records with a required `name`.\n- Confirm whether stable author IDs, profile URLs, or other fields are part of\n  this migration. If not approved, keep them out of the required contract.\n- Confirm whether the authoring helper's existing function signature must remain\n  source-compatible for callers during the transition or may change at the\n  same time as its emitted front matter.\n\n## Supporting facts and boundary\n\nThe only committed post sources are under `content/posts/`, and both currently\nuse `author: \"...\"`. The helper currently accepts one author argument and\nreturns serialized front matter. There is no existing validator or migration\ncommand, so the implementation must make the conversion and its failure\nreporting explicit rather than relying on a blind text replacement.\n\n## Execution plan\n\nStatus: Draft\n\nDefine one canonical normalization function or data boundary that returns an\nordered collection of author records. In transition mode it reads the legacy\nscalar only when the canonical field is absent; it reports ambiguous inputs\nsuch as both fields being present or malformed author data. The post templates\nand feed will consume only this normalized result.\n\nAdd a narrow migration path for committed Markdown sources. Before writing,\ninventory all post files and capture stable fields needed to prove safety.\nRewrite only the front matter author representation, preserve Markdown bodies\nbyte-for-byte where practical, and fail or report unexpected front matter\ninstead of guessing. Make the operation idempotent so a second run produces no\nadditional changes.\n\nUpdate the authoring helper to emit the canonical field and exercise it with\none-author and multi-author inputs. Preserve a compatibility API only if the\napproved transition contract requires it; regardless of API compatibility, new\noutput must not introduce `author`.\n\n### Implementation decisions and open questions\n\n- The migration must not remove the compatibility read until the parent\n  cutover evidence is complete.\n- The canonical field is the only value exposed to rendering consumers; do not\n  duplicate old/new branching across templates or scripts.\n- Migration errors must identify the source file and reason, and must leave\n  unrecognized files unchanged.\n- Do not treat a source-code reference to the word `author` in migration\n  diagnostics or documentation as a remaining data dependency; the cutover\n  audit must distinguish intentional references from legacy reads.\n\n### Documentation\n\nUpdate the authoring section of `README.md` with the approved front matter\nexample and helper usage. If the transition requires contributor-facing\nmigration instructions, record them in the smallest existing development\ndocumentation location after the contract is approved.\n\n### Task checklist\n\n- [ ] Record the approved canonical schema from the parent decision.\n- [ ] Add transition normalization and malformed/mixed-input coverage.\n- [ ] Add the content migration and safety/idempotence checks.\n- [ ] Update and test the authoring helper.\n- [ ] Inventory and migrate all committed posts.\n- [ ] Report the source-evidence result to the parent before cutover.\n\n### Requirement verification\n\n- Canonical model and compatibility: run the metadata tests against one\n  canonical post, one legacy post, a multi-author post, and invalid/mixed\n  inputs; then consume the normalized data through the real Eleventy build\n  before strict rejection.\n- Safe existing-post migration: inspect every file under `content/posts/`,\n  assert canonical author metadata is present, assert no legacy front matter\n  remains, and compare title/body/unrelated metadata with the pre-migration\n  inventory.\n- Authoring tool: invoke the exported helper with one and multiple authors and\n  parse its output as front matter, proving that new posts use the canonical\n  field.\n\n### Additional implementation verification\n\n- Run the migration twice and verify the second run is a no-op.\n- Check quoting, escaping, and author order for names containing YAML-sensitive\n  characters.\n- Confirm a malformed source is reported without partially rewriting other\n  posts.",
    "tasks/20260925-author-metadata-migration/020-rendering-and-output.md": "# Move production rendering to canonical authors\n\nOwn all generated author output: individual post templates, shared archive\nlisting paths, feeds, and the tests that verify the real Eleventy production\nbuild.\n\nParent Task: tasks/20260925-author-metadata-migration/000-main.md\n\nDepends On: tasks/20260925-author-metadata-migration/010-metadata-content-tooling.md\n\n## Requirements checklist\n\n- [ ] Render the canonical multi-author value in individual post pages with\n  stable ordering and no legacy-field lookup.\n- [ ] Ensure the shared listing used by the home page, blog archive, and tag\n  pages is compatible with and, where approved, displays the canonical\n  multi-author value.\n- [ ] Emit the approved representation for all authors in the feed without\n  losing authors or producing undefined values.\n- [ ] Preserve the generated route set and unrelated page content while\n  changing author metadata.\n- [ ] Replace placeholder tests with decisive generated-output coverage.\n\n## Unresolved requirement questions and decisions\n\n- Apply the parent-approved archive display decision. If archives remain title\n  only, prove that their production path still carries no legacy author read;\n  if authors are displayed, use one shared canonical rendering path and\n  specify its separator/markup.\n- Apply the parent-approved feed representation. Do not infer a new feed\n  protocol from the current fixture without approval.\n\n## Supporting facts and boundary\n\nThe post layout and feed currently read `author` directly. The home page,\n`/blog/`, and tag pages all include `_includes/postslist.njk`, which currently\nrenders only titles. The decisive boundary is a real `npm run build` followed\nby assertions against `_site/`, not isolated template rendering with mocked\npost data.\n\n## Execution plan\n\nStatus: Draft\n\nChange templates to consume only the normalized canonical authors collection.\nKeep author rendering shared where the same markup is used by post and archive\npages, and preserve source order. For the feed, emit the approved multi-author\nstructure for every entry while retaining the existing feed route and all\nunrelated elements.\n\nExpand the production-output tests so they invoke the normal build and inspect\nthe generated home page, blog archive, tag pages, individual posts, feed, and\nsitemap. Assert route preservation, expected author names/order/count, absence\nof `undefined` or empty author output, and retention of unrelated title/body\ncontent. Include a transition fixture or test setup that demonstrates the\nnormalizer still protects the build before the strict cutover.\n\n### Implementation decisions and open questions\n\n- Templates must not contain fallback logic for both fields; that belongs at\n  the normalization boundary owned by subtask 010.\n- Archive routes are in scope even if their current markup does not show\n  authors, because their shared production path must be audited for legacy\n  reads and their generated output must remain valid.\n- Preserve route names and feed URL exactly unless a separately approved\n  requirement changes them.\n\n### Documentation\n\nIf the approved archive or feed behavior is user-visible, document the\nresulting output contract in the maintained README/development documentation\nupdated by the owning subtask. Do not document target behavior before it is\nimplemented and verified.\n\n### Task checklist\n\n- [ ] Update the individual post template to use canonical authors.\n- [ ] Resolve and implement the archive/listing behavior through the shared\n  partial.\n- [ ] Update the feed to emit all canonical authors in the approved shape.\n- [ ] Replace `tests/author-output.test.js` placeholder coverage.\n- [ ] Replace `tests/archive-output.test.js` placeholder coverage.\n- [ ] Run the full production build and record route/output evidence.\n\n### Requirement verification\n\n- Individual post pages and feeds: build the site through Eleventy and inspect\n  generated files for every migrated author, stable order, and no legacy\n  lookup artifacts.\n- Archives: inspect `/index.html`, `/blog/index.html`, and each generated tag\n  page from the same build, proving the shared listing path remains valid and\n  follows the approved author behavior.\n- Compatibility: run the production path while a legacy-shaped transition\n  input is present in the dedicated fixture/setup, proving the build remains\n  safe before cutover; remove that fixture from committed content before the\n  strict gate.\n- Regression safety: compare the generated route set and non-author output\n  fields with the pre-migration baseline.\n\n### Additional implementation verification\n\n- Test one-author and multiple-author posts through the same build path.\n- Assert the feed has the expected number of author elements per entry and no\n  accidental serialization of objects such as `[object Object]`.\n- Check HTML/XML escaping for names containing reserved characters.",
    "tasks/20260925-author-metadata-migration/030-cutover-and-rejection.md": "# Prove migration completion and reject the legacy author field\n\nOwn the ordered evidence gate that permits removal of the legacy read, the\nstrict rejection behavior, and final documentation/status handoff.\n\nParent Task: tasks/20260925-author-metadata-migration/000-main.md\n\nDepends On: tasks/20260925-author-metadata-migration/010-metadata-content-tooling.md, tasks/20260925-author-metadata-migration/020-rendering-and-output.md\n\n## Requirements checklist\n\n- [ ] Produce source-content evidence that all supported posts use the\n  canonical field and none still depend on legacy `author`.\n- [ ] Produce generated-output evidence that the canonical templates, archive\n  routes, feed, and post pages work from migrated content.\n- [ ] Run the complete relevant test/build gate before enabling strict legacy\n  rejection.\n- [ ] After the evidence gate passes, reject legacy `author` with an\n  actionable failure at the approved enforcement boundary.\n- [ ] Leave documentation and task status consistent with the final supported\n  contract.\n\n## Unresolved requirement questions and decisions\n\n- Confirm whether strict rejection applies only to production content\n  validation or also to direct calls to the authoring helper. Recommendation:\n  both production input and newly authored output should be canonical, while\n  only the production input needs a hard failure for a legacy field.\n- Confirm whether intentional migration diagnostics/tests may retain the\n  literal legacy key. If allowed, the final audit must scope references by\n  dependency rather than require a misleading zero-text search.\n\n## Supporting facts and boundary\n\nThe current repository has no strict metadata validator and its author-output\ntests are placeholders. Therefore \u201cnothing depends on legacy\u201d cannot be\nclaimed from the current test suite; it requires a source scan plus a real\nbuild and output assertions from subtask 020, followed by the rejection\nbehavior itself.\n\n## Execution plan\n\nStatus: Draft\n\nRun the cutover in an explicit order:\n\n1. Confirm subtask 010 has migrated all committed post sources and has\n   transition coverage.\n2. Run subtask 020's real production build and inspect the route set and\n   generated author output.\n3. Scan production templates, configuration, scripts, tests, and content for\n   executable legacy reads or writes, classifying any intentional migration\n   documentation/fixture references separately.\n4. Record the evidence and only then switch the canonical data boundary to\n   reject a post containing the legacy field, with a file-specific error.\n5. Re-run the complete test/build gate from the strict mode and verify that a\n   deliberately legacy-shaped input fails for the intended reason without\n   weakening the migrated production path.\n\nThe rejection change is a separate final step in the implementation history,\nso reviewers can verify that it was not enabled before content and generated\noutput were clean.\n\n### Implementation decisions and open questions\n\n- No strict rejection is allowed while committed posts or production\n  templates/scripts still require the legacy field.\n- The pre-rejection evidence must be recorded in test output or an equivalent\n  reviewable check, not inferred from a successful unit test.\n- Keep migration-only diagnostics explicit and non-production; do not leave a\n  hidden compatibility fallback after strict mode.\n- If the evidence finds a remaining dependency, stop the cutover, return to\n  the relevant subtask, and leave legacy acceptance in place.\n\n### Documentation\n\nUpdate the maintained documentation to state the canonical field and the\nstrict rejection behavior after it is true. If a migration note is retained,\nmark the transition as historical/currently supported accurately; do not\ndescribe the legacy field as supported after the gate.\n\n### Task checklist\n\n- [ ] Receive source migration evidence from subtask 010.\n- [ ] Receive production-output evidence from subtask 020.\n- [ ] Complete and record the dependency scan.\n- [ ] Obtain the evidence-gate review/approval.\n- [ ] Enable strict rejection only after approval.\n- [ ] Add strict-mode regression coverage and rerun the complete build/test\n  gate.\n- [ ] Update parent requirement status and document any deferred scope.\n\n### Requirement verification\n\n- Source independence: a scoped scan of `content/`, templates, config, and\n  authoring code shows no executable legacy read/write remaining after\n  migration; any intentional test/documentation mention is classified.\n- Generated-output independence: the production build produces all expected\n  routes and canonical author output before strict mode is enabled.\n- Conditional rejection: the strict-mode test proves a legacy-only input\n  fails with an actionable message, while the migrated repository passes the\n  same complete build/test invocation.\n- Final contract: inspect the maintained documentation and task evidence\n  together so the documented supported form matches the enforced form.\n\n### Additional implementation verification\n\n- Run from a clean checkout or equivalent clean source copy to avoid stale\n  `_site` files masking missing output.\n- Verify the strict failure identifies the offending post and field.\n- Confirm no generated output or migration scratch artifact is accidentally\n  added to version control."
  },
  "task_tree": {
    "all_dependencies_resolve": true,
    "all_parent_links_resolve": true,
    "coordinating_files": [
      "tasks/20260925-author-metadata-migration/000-main.md"
    ],
    "dependencies": [],
    "files": [
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": null,
        "path": "tasks/20260925-author-metadata-migration/000-main.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 6,
        "title": "Migrate post authors to structured multi-author metadata"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260925-author-metadata-migration/000-main.md",
        "path": "tasks/20260925-author-metadata-migration/010-metadata-content-tooling.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Define and migrate the post author metadata contract"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260925-author-metadata-migration/000-main.md",
        "path": "tasks/20260925-author-metadata-migration/020-rendering-and-output.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Move production rendering to canonical authors"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260925-author-metadata-migration/000-main.md",
        "path": "tasks/20260925-author-metadata-migration/030-cutover-and-rejection.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Prove migration completion and reject the legacy author field"
      }
    ],
    "implementation_task_count": 3,
    "parent_links": [
      {
        "child": "tasks/20260925-author-metadata-migration/010-metadata-content-tooling.md",
        "parent": "tasks/20260925-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260925-author-metadata-migration/020-rendering-and-output.md",
        "parent": "tasks/20260925-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260925-author-metadata-migration/030-cutover-and-rejection.md",
        "parent": "tasks/20260925-author-metadata-migration/000-main.md",
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
    "added_obligations": [
      "Minor: the parent checklist requires updating maintained documentation (README authoring section plus a development note about the transition/rejection gate). This is reasonable for a contract-changing migration but is not an approved outcome and is not explicitly requested in the natural user request."
    ],
    "semantic_deliverable_count": 3,
    "actual_task_count": 3,
    "deliverable_mappings": [
      {
        "deliverable_id": "AUTHOR-D1",
        "task_paths": ["tasks/20260925-author-metadata-migration/010-metadata-content-tooling.md"],
        "coverage": "complete",
        "coherence": "overpacked",
        "reason": "Normalization boundary, legacy compatibility, and dual-format acceptance are fully owned by 010, but they are bundled with content migration and tooling (AUTHOR-D3), so the 'site safely accepts old and new content before content migrates' state never exists as an independently reviewable deliverable."
      },
      {
        "deliverable_id": "AUTHOR-D2",
        "task_paths": ["tasks/20260925-author-metadata-migration/020-rendering-and-output.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Post templates, shared archive listing, and feed move to the canonical model in one consumer-adoption task, verified through the real production build; it leaves an independently usable generated site on the normalized model."
      },
      {
        "deliverable_id": "AUTHOR-D3",
        "task_paths": ["tasks/20260925-author-metadata-migration/010-metadata-content-tooling.md"],
        "coverage": "complete",
        "coherence": "overpacked",
        "reason": "Content rewrite and new-post helper update are fully covered and share the same contract ownership as normalization, which is a defensible consolidation, but it merges two deliverables the target keeps separate and forces rendering adoption to wait for migration completion."
      },
      {
        "deliverable_id": "AUTHOR-D4",
        "task_paths": ["tasks/20260925-author-metadata-migration/030-cutover-and-rejection.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "The ordered evidence gate (source scan, generated-output proof, full test/build run) followed by strict rejection with rollback posture matches AUTHOR-D4 and AUTHOR-4 exactly; the rejection change is a separately reviewable final step."
      }
    ],
    "mergeable_groups": [],
    "unmatched_tasks": [],
    "overpacked_tasks": [
      "tasks/20260925-author-metadata-migration/010-metadata-content-tooling.md"
    ],
    "valid_layer_boundaries": [
      "tasks/20260925-author-metadata-migration/020-rendering-and-output.md (consumer adoption leaves an independently reviewable generated site on the canonical model)",
      "tasks/20260925-author-metadata-migration/030-cutover-and-rejection.md (the evidence-gated rejection is a deferable, separately reviewable final state gated on human approval)"
    ],
    "automatic_layer_fragments": [],
    "dependency_issues": [
      "020 depends on 010, but 010 bundles normalization (AUTHOR-D1) with content migration and tooling (AUTHOR-D3); the target makes AUTHOR-D2 depend only on AUTHOR-D1, so rendering adoption is serialized behind content migration that it does not actually require (the normalization boundary handles legacy-shaped content).",
      "After 010 completes, committed content is canonical while templates and the feed still read the legacy key until 020 lands; the plan's single normalization boundary mitigates this, but the intermediate author-rendering contract between 010 and 020 (whether the boundary keeps a compatible value exposed to current template reads) is not explicitly specified, leaving AUTHOR-5 continuity in that window assumed rather than stated."
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
        "occurrences": [
          {
            "task_paths": [],
            "description": "No instance: 010 and 020 each retain their own verification (migration/idempotence checks and the decisive real-build output test respectively); 030 only receives and re-records that evidence as part of the AUTHOR-D4 cutover gate, which is where AUTHOR-4 requires it, and adds its own strict-mode regression run."
          }
        ]
      },
      "unsafe_dependencies": {
        "status": "partial",
        "occurrences": [
          {
            "task_paths": [
              "tasks/20260925-author-metadata-migration/010-metadata-content-tooling.md",
              "tasks/20260925-author-metadata-migration/020-rendering-and-output.md"
            ],
            "description": "Bundling content migration and tooling into 010 makes 020's dependency on 010 also a dependency on migration completion, serializing consumer adoption behind producer migration even though the target treats AUTHOR-D2 and AUTHOR-D3 as independent siblings of AUTHOR-D1."
          },
          {
            "task_paths": [
              "tasks/20260925-author-metadata-migration/010-metadata-content-tooling.md",
              "tasks/20260925-author-metadata-migration/020-rendering-and-output.md"
            ],
            "description": "The intermediate revision after 010 (canonical content, legacy-reading templates/feed) is not explicitly guaranteed to keep rendering authors; the plan relies on the single normalization boundary without stating what current template reads receive in that window, so AUTHOR-5 continuity there is implied rather than checked."
          }
        ]
      },
      "piecewise_crossing_evidence": {
        "status": "none",
        "occurrences": []
      }
    },
    "partition_quality_score": 82,
    "handoff_quality_score": 88,
    "summary": "The three implementation tasks preserve every approved outcome: 010 owns normalization, compatibility, content migration, and the authoring helper (AUTHOR-1/3); 020 moves post pages, the shared archive partial, and the feed to the canonical model with a decisive real Eleventy production build that inspects generated pages, archives, tag pages, and the feed (AUTHOR-2, and the exact required crossing — real front matter through normalization into the production build — is named and owned, with placeholder tests explicitly replaced); 030 implements the ordered source/output evidence gate before strict rejection with an explicit rollback posture (AUTHOR-4), and real-build plus route-preservation checks at each state cover AUTHOR-5. There is no fragmentation: no phase-only, test-only, doc-only, or review-only children exist, tests and documentation are embedded in the owning deliverables, and the coordinating 000-main.md carries no separately assigned implementation work. The single partition deviation is that 010 consolidates the target's AUTHOR-D1 and AUTHOR-D3 into one contract-owning deliverable; this is a defensible ownership consolidation within the acceptable size range, but it removes the 'normalization accepted before content migrates' intermediate reviewable state and needlessly serializes rendering adoption behind content migration, with the intermediate author-rendering contract between 010 and 020 left implicit. Handoff quality is strong: the schema, archive display, feed shape, and rejection boundary are recorded as approval questions rather than invented, source pointers and current consumer/producer facts are preserved, working migration states and cutover ordering are retained, and the parent distinguishes completed checks from pending human approval."
  }
}
```
