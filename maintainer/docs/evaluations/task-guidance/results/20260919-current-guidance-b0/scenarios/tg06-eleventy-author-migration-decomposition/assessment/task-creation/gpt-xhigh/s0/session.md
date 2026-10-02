# Session — tg06-eleventy-author-migration-decomposition · task-creation-assessment-gpt-xhigh-s0 · glm max

- Run: `20260924T192453.023193Z-task-guidance-semantic-tg06-eleventy-author-migration-decomposition-gpt-xhigh-s0-0d2b8b14`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `ffd0bb29ed99a86c…`)
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
  "response": "Created a draft task hierarchy; no implementation changes were made.\n\nMain task: [000-main.md](/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T200925.997826Z-task-guidance-tg06-eleventy-author-migration-decomposition-xhigh-5bd3a28b/workspace/tasks/20260919-author-metadata-migration/000-main.md)\n\nSubtasks:\n\n- [010-contract-and-inventory.md](/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T200925.997826Z-task-guidance-tg06-eleventy-author-migration-decomposition-xhigh-5bd3a28b/workspace/tasks/20260919-author-metadata-migration/010-contract-and-inventory.md)\n- [020-compatibility-and-rendering.md](/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T200925.997826Z-task-guidance-tg06-eleventy-author-migration-decomposition-xhigh-5bd3a28b/workspace/tasks/20260919-author-metadata-migration/020-compatibility-and-rendering.md)\n- [030-content-migration.md](/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T200925.997826Z-task-guidance-tg06-eleventy-author-migration-decomposition-xhigh-5bd3a28b/workspace/tasks/20260919-author-metadata-migration/030-content-migration.md)\n- [040-authoring-tool-and-guidance.md](/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T200925.997826Z-task-guidance-tg06-eleventy-author-migration-decomposition-xhigh-5bd3a28b/workspace/tasks/20260919-author-metadata-migration/040-authoring-tool-and-guidance.md)\n- [050-evidence-and-legacy-cutover.md](/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T200925.997826Z-task-guidance-tg06-eleventy-author-migration-decomposition-xhigh-5bd3a28b/workspace/tasks/20260919-author-metadata-migration/050-evidence-and-legacy-cutover.md)\n\nThe plan is intentionally `Draft` and records the material questions that must be resolved before execution:\n\n- the exact structured field and author value shape;\n- how multiple authors appear in HTML, archives, and feeds;\n- whether the authoring helper temporarily accepts the legacy argument;\n- whether author IDs, slugs, links, or author pages are in scope.\n\nThe final cutover is explicitly gated on both source-content evidence and real production-generated-output evidence. Build and tests were not run because this was a planning-only request.",
  "task_files": {
    "tasks/20260919-author-metadata-migration/000-main.md": "# Migrate post author metadata to structured multi-author data\n\nPlan the staged migration from the single `author` front-matter string to a\nstructured field that can represent multiple authors, while preserving current\ncontent and generated-site behavior until migration evidence permits removal of\nthe legacy form.\n\n## Requirements checklist\n\n- [ ] Adopt a reviewed structured post-author field that represents one or more\n  named authors and becomes the supported authoring contract.\n- [ ] Keep existing posts and generated pages working during the transition\n  through an explicit compatibility boundary.\n- [ ] Move post templates, home/archive/tag listings, feeds, and authoring tools\n  to the structured model while preserving the site\u2019s existing URL, ordering,\n  and content contracts unless a changed author rendering is explicitly\n  approved.\n- [ ] Migrate every existing post safely, without losing front matter or body\n  content.\n- [ ] Update tests and maintained developer guidance with evidence for the\n  structured model, compatibility period, migration, and cutover.\n- [ ] Reject the legacy form only after source-content evidence and\n  production-generated-output evidence show that no supported path still\n  depends on it.\n\n## Scope and workstreams\n\n- Contract and inventory: define the field shape, output rules, compatibility\n  boundary, and complete producer/consumer inventory.\n- Runtime and generated output: normalize the transition data and update post\n  layouts, listing/archive views, feeds, and related generated-output checks.\n- Content and tooling: migrate existing post front matter and make the\n  authoring helper emit the supported structure.\n- Cutover and evidence: prove content and generated output are independent of\n  the legacy field, then remove or reject legacy handling under a gated change.\n- Documentation: keep the developer-facing authoring and migration guidance\n  with the owning development documentation.\n\n## Open requirement questions and material decisions\n\n- What is the exact new field and value shape: an ordered `authors` array of\n  names, or an ordered array of author records such as `{ name }` with\n  identity/link fields?\n- How should multiple authors be rendered in HTML post pages and archive\n  listings, and how should they be serialized in the feed: one combined value,\n  repeated author elements, links, or another reviewed contract?\n- Does the authoring helper need to accept the legacy single-name argument\n  during the compatibility period, or may its public input contract change\n  immediately while only content/template reads remain dual-compatible?\n- Are stable author identifiers, slugs, profile URLs, or author archive pages\n  in scope? The current fixture has no author collection or author pages, so\n  these should not be introduced without an explicit requirement.\n\nRecommendation for review: use the smallest ordered structured value that\nsupports the required output (an `authors` list, with one entry for each\nexisting name) unless author identity or links are required. Keep any legacy\n`author` interpretation in one normalization boundary, rather than spreading\nfallback checks through templates.\n\n## Supporting facts\n\n- The post defaults in `content/posts/posts.json` provide the shared `post`\n  layout and `posts` tag; individual posts currently define `author` as a\n  quoted scalar.\n- `_includes/layouts/post.njk` renders the current scalar in the post page.\n- `_includes/postslist.njk` is shared by the home page, `/blog/` archive, and\n  tag pages, but currently renders only title and URL. The migration must\n  explicitly decide whether its author presentation changes or only its data\n  contract does.\n- `content/feed.xml.njk` reads `post.data.author`; the sitemap only emits page\n  URLs and has no author dependency.\n- `scripts/new-post.js` writes the legacy front matter and is the only\n  discovered authoring producer.\n- `tests/archive-output.test.js` and `tests/author-output.test.js` are\n  comments describing intended coverage, not executable assertions.\n- The repository has no `docs/index.md`; the applicable maintained\n  development documentation is `docs/development/index.md`, alongside the\n  repository README and guidance in `docs/development/documentation.md`.\n\n## Execution plan\n\nStatus: Draft\n\nFirst settle the author data and output contracts, then implement the\ncompatibility boundary and migrate consumers. Convert existing content with a\nreviewable, deterministic operation and make the authoring helper produce only\nthe supported representation (or an explicitly approved transition input).\nExercise the real Eleventy build and inspect generated pages and feeds. Keep\nthe legacy reader and rejection test out of the final cutover until source and\ngenerated-output scans demonstrate that no content or supported consumer still\nuses the old field. Update the maintained development guidance only for the\nbehavior that is actually implemented and verified.\n\nThe ordered work is tracked in the subtasks below. Subtask 050 is the final\ncutover gate and depends on all preceding work.\n\n### Implementation decisions and open questions\n\nThe schema, multi-author rendering/serialization rules, and authoring-helper\ntransition input policy remain open requirement questions above. The plan\nassumes a single normalization boundary and an ordered author collection, but\nexecution must not finalize the public shape until those questions are\nanswered.\n\n### Documentation\n\nUpdate the smallest relevant developer-facing documentation, likely\n`docs/development/index.md` or a focused page under `docs/development/`, with\nthe supported front-matter shape, authoring-helper contract, compatibility\nperiod, and evidence-based cutover rule. Update `README.md` only if it is the\nmaintained user/developer entry point for post authoring. Do not add a\nplaceholder documentation tree.\n\n### Task checklist\n\n- [ ] Review and resolve the author schema and output-contract questions.\n- [ ] Complete subtask\n  [tasks/20260919-author-metadata-migration/010-contract-and-inventory.md](010-contract-and-inventory.md).\n- [ ] Complete subtask\n  [tasks/20260919-author-metadata-migration/020-compatibility-and-rendering.md](020-compatibility-and-rendering.md).\n- [ ] Complete subtask\n  [tasks/20260919-author-metadata-migration/030-content-migration.md](030-content-migration.md).\n- [ ] Complete subtask\n  [tasks/20260919-author-metadata-migration/040-authoring-tool-and-guidance.md](040-authoring-tool-and-guidance.md).\n- [ ] Complete subtask\n  [tasks/20260919-author-metadata-migration/050-evidence-and-legacy-cutover.md](050-evidence-and-legacy-cutover.md).\n- [ ] Record requirement evidence and completion notes after approved execution.\n\n### Requirement verification\n\n- The structured field and authoring contract are verified by executable\n  front-matter/tool tests and a real production build containing at least\n  single-author and multi-author posts.\n- Transition safety is verified by building a representative legacy post\n  alongside structured posts and asserting the post page, home/archive/tag\n  output, feed, and preserved URL/order behavior.\n- Safe content migration is verified by source inventory, reviewed front\n  matter diffs, and a build using every migrated post.\n- Legacy rejection is verified only after a source-content scan and generated\n  output scan find no supported legacy dependency, plus a negative test proves\n  the final boundary rejects the old form.\n\n### Additional implementation verification\n\n- Run the repository\u2019s production build and test command after the cutover.\n- Assert that feed output is valid for the chosen multi-author contract and\n  that no raw legacy scalar is emitted.\n- Preserve or explicitly review escaping/quoting behavior for names containing\n  YAML- or HTML-sensitive characters.",
    "tasks/20260919-author-metadata-migration/010-contract-and-inventory.md": "# Define the author metadata contract and dependency inventory\n\nEstablish the structured multi-author schema, transition behavior, and\ncomplete list of legacy producers and consumers before changing content or\ntemplates.\n\nParent Task: tasks/20260919-author-metadata-migration/000-main.md\n\n## Requirements checklist\n\n- [ ] Specify the supported structured field, ordering, cardinality, and\n  author-value shape.\n- [ ] Specify HTML/archive and feed output for one and multiple authors.\n- [ ] Identify every repository source, test, script, template, and generated\n  artifact that produces or consumes author metadata.\n- [ ] Define the single compatibility boundary and the evidence required before\n  the legacy field can be rejected.\n\n## Open requirement questions and material decisions\n\n- Resolve whether the structured values are names or author records.\n- Resolve whether the field is required, and what missing/empty values mean.\n- Resolve whether legacy input is accepted only by the normalization boundary or\n  remains accepted by the authoring helper during transition.\n- Do not add author identity, profile links, or author archive pages unless the\n  parent task\u2019s open scope question is approved.\n\n## Supporting facts\n\nThe current dependency inventory found `author` in two post files, the post\nlayout, the feed template, the authoring helper, and the author-output coverage\nplaceholder. Shared archive/listing templates receive post objects but do not\ncurrently print author data. The sitemap has no author read.\n\n## Execution plan\n\nStatus: Draft\n\nInspect source and test references, document the exact contract, and choose one\nnormalization location that can map legacy scalar metadata to the new\nstructured value during the transition. Record output examples for a\nsingle-author post, a multi-author post, and any permitted legacy post. Define\nsource and generated-output scans that can distinguish intentional migration\ndocumentation from remaining runtime dependencies.\n\n### Implementation decisions and open questions\n\nThe task cannot be marked complete until the parent task\u2019s schema and output\nquestions are resolved. A normalization filter, data transform, or equivalent\nboundary is an implementation choice after the contract is approved.\n\n### Documentation\n\nCapture the approved field and output contract in the parent execution plan and\nthe owning developer guidance during the authoring-tool subtask.\n\n### Task checklist\n\n- [ ] Record the final field name and value shape.\n- [ ] Record single- and multi-author rendering and feed examples.\n- [ ] Record compatibility inputs and the final rejection behavior.\n- [ ] Record the complete producer/consumer inventory and evidence commands.\n\n### Requirement verification\n\n- Contract examples are reviewed against the request and current generated\n  surfaces.\n- A repository-wide search confirms the inventory includes all current\n  `author` reads and writes and identifies any newly discovered dependency.\n\n### Additional implementation verification\n\n- Check YAML quoting/escaping and HTML/feed escaping requirements for author\n  names before selecting the migration mechanism.",
    "tasks/20260919-author-metadata-migration/020-compatibility-and-rendering.md": "# Move templates and generated surfaces to structured authors\n\nUpdate the Eleventy data path and all relevant rendering surfaces so structured\nauthors are the primary model while legacy posts remain renderable during the\napproved transition.\n\nParent Task: tasks/20260919-author-metadata-migration/000-main.md\n\nDepends On: tasks/20260919-author-metadata-migration/010-contract-and-inventory.md\n\n## Requirements checklist\n\n- [ ] Make the post layout consume the structured author representation.\n- [ ] Make home, blog archive, and tag-listing paths use the structured model\n  wherever author data is displayed or passed through.\n- [ ] Make feed generation serialize all authors according to the approved feed\n  contract.\n- [ ] Preserve existing post URLs, archive/tag URLs, listing order, and\n  sitemap URLs unless an explicitly approved author-output change requires\n  otherwise.\n- [ ] Keep legacy content working through the compatibility period without\n  duplicating fallback logic across templates.\n\n## Open requirement questions and material decisions\n\n- The exact author presentation and feed serialization depend on the contract\n  approved in subtask 010.\n- Confirm whether archive listings should visibly display authors or only stop\n  depending on a legacy post-data shape; the current shared listing emits title\n  and link only.\n\n## Supporting facts\n\nThe post layout and feed are direct legacy consumers. The shared\n`_includes/postslist.njk` is used by the home page, `/blog/`, and tag pages,\nwhich makes it the relevant archive boundary even though it currently renders\nno author. `content/sitemap.xml.njk` does not read author data but should be\ncovered by URL-preservation checks because it is part of generated output.\n\n## Execution plan\n\nStatus: Draft\n\nIntroduce or use the approved normalization boundary, then update the post\nlayout, shared listing include, feed, and any collection-facing code to consume\nthe structured value. Keep the compatibility read at that boundary for the\ntransition. Add executable build-level assertions for legacy and structured\nfixtures, including one post with multiple authors, and compare URL/order\noutput across home, archive, tags, feed, and sitemap.\n\n### Implementation decisions and open questions\n\nDo not scatter `author`/`authors` conditionals through Nunjucks templates.\nChoose the narrowest shared data boundary supported by Eleventy after the\ncontract is approved. Any visible archive rendering change must be recorded as\nan approved output decision.\n\n### Documentation\n\nDocument the public generated-output behavior only after build assertions\nverify it. The authoring and data-contract documentation belongs in subtask\n040; this subtask supplies its rendering facts.\n\n### Task checklist\n\n- [ ] Add the compatibility normalization at the approved boundary.\n- [ ] Update post, listing/archive, and feed consumers.\n- [ ] Add or update build assertions for single, multiple, and legacy authors.\n- [ ] Verify URL, ordering, and sitemap preservation.\n\n### Requirement verification\n\n- A real Eleventy production build renders a legacy fixture and structured\n  single-/multi-author fixtures successfully.\n- Generated post, home, `/blog/`, tag, feed, and sitemap outputs meet the\n  approved author and URL contracts.\n- Assertions prove no duplicate or missing author output for multi-author\n  posts.\n\n### Additional implementation verification\n\n- Inspect generated HTML/XML for escaping and malformed markup.\n- Confirm the compatibility behavior is localized and removable at cutover.",
    "tasks/20260919-author-metadata-migration/030-content-migration.md": "# Migrate existing post front matter safely\n\nConvert every existing post from the legacy scalar field to the approved\nstructured multi-author field while preserving titles, body content, dates,\ntags, URLs, and other front matter.\n\nParent Task: tasks/20260919-author-metadata-migration/000-main.md\n\nDepends On: tasks/20260919-author-metadata-migration/010-contract-and-inventory.md\n\n## Requirements checklist\n\n- [ ] Migrate every existing post that currently uses the legacy author field.\n- [ ] Preserve each post\u2019s author name, order, front matter, body, and generated\n  identity during conversion.\n- [ ] Make the migration deterministic and reviewable, with no partial or\n  silently lossy conversion.\n- [ ] Produce source-content evidence that no supported post still depends on\n  the legacy field before final rejection.\n\n## Open requirement questions and material decisions\n\n- The conversion target depends on the approved structured value shape.\n- If malformed, duplicate, empty, or unusually quoted legacy values are found,\n  decide whether to repair them as part of migration or stop for review; do not\n  invent a fallback value.\n\n## Supporting facts\n\nThe current content inventory contains `content/posts/first.md` with `Ada\nExample` and `content/posts/second.md` with `Grace Example`. Both inherit\nlayout and tags from `content/posts/posts.json`. No dates or explicit URLs are\ncurrently present in these sample posts, so URL preservation must be checked\nfrom the built output rather than inferred from front matter alone.\n\n## Execution plan\n\nStatus: Draft\n\nAfter the schema is approved, convert the content with a narrowly scoped,\nreviewable operation. Compare the before/after front matter and body for every\npost, run the production build, and inspect the generated post and collection\noutputs. Keep the compatibility reader available until this evidence and the\nrepository-wide source scan are complete.\n\n### Implementation decisions and open questions\n\nPrefer a deterministic migration operation that fails on unexpected input\ninstead of guessing. The final choice of script or manual edits is an\nimplementation detail, but the resulting diff must remain easy to review.\n\n### Documentation\n\nRecord the supported front-matter example and any migration caveats in the\ndeveloper guidance selected by the parent task. Do not document a temporary\nconversion command as a supported authoring interface unless it is retained.\n\n### Task checklist\n\n- [ ] Inventory and classify every post author value.\n- [ ] Convert all valid legacy values to the approved structured form.\n- [ ] Review front matter/body diffs for preservation.\n- [ ] Build all migrated posts and record source-content evidence.\n\n### Requirement verification\n\n- A complete content scan finds no legacy author field in supported post\n  front matter after migration.\n- A diff review and production build show each migrated post retains its\n  content, metadata, URL, and author value(s).\n- Structured single- and multi-author content is accepted by the actual\n  Eleventy build.\n\n### Additional implementation verification\n\n- Check names containing punctuation, quotes, colons, or non-ASCII characters\n  if present in the inventory.\n- Verify the migration did not alter unrelated front matter or Markdown body\n  bytes.",
    "tasks/20260919-author-metadata-migration/040-authoring-tool-and-guidance.md": "# Update the authoring helper and developer guidance\n\nMove new-post creation to the structured author contract and explain the\nsupported transition behavior to maintainers.\n\nParent Task: tasks/20260919-author-metadata-migration/000-main.md\n\nDepends On: tasks/20260919-author-metadata-migration/010-contract-and-inventory.md\n\n## Requirements checklist\n\n- [ ] Make `scripts/new-post.js` produce the approved structured author\n  front matter.\n- [ ] Define and test how the helper accepts one and multiple authors.\n- [ ] Ensure generated front matter is safely quoted/serialized for supported\n  author values.\n- [ ] Document the current authoring contract and the temporary legacy policy\n  in the owning developer documentation.\n\n## Open requirement questions and material decisions\n\n- Decide whether the helper takes an array, variadic names, or author records;\n  this must match the approved schema rather than preserving an accidental\n  JavaScript API.\n- Decide whether a legacy scalar argument is accepted temporarily, normalized,\n  warned about, or rejected only at final cutover.\n\n## Supporting facts\n\nThe helper currently exports `frontMatter(title, author)` and interpolates both\nvalues directly into YAML. It has no discovered executable tests, so the\nupdated contract needs direct tests plus a build-level consumer.\n\n## Execution plan\n\nStatus: Draft\n\nChange the helper\u2019s input contract to the approved structured representation,\nserialize it safely, and add focused tests for one and multiple authors and\nspecial characters. If transition compatibility is approved for callers,\nnormalize it at the helper boundary and mark the legacy path for removal;\notherwise make the contract change explicit in the guidance. Verify output by\nfeeding generated front matter into the real site build.\n\n### Implementation decisions and open questions\n\nThe public helper API is a material interface decision. Do not preserve or\nreject legacy arguments until the parent task resolves the transition policy.\nAvoid adding a second authoring abstraction when the helper can directly emit\nthe approved front matter.\n\n### Documentation\n\nUpdate `docs/development/index.md` or a focused development page only if it\nhas a meaningful authoring audience. Include the field example, helper\ninvocation shape, transition status, and final legacy-rejection condition.\nUpdate README content only if it currently serves that audience.\n\n### Task checklist\n\n- [ ] Implement and test the approved helper input/output contract.\n- [ ] Verify safe YAML serialization for supported author values.\n- [ ] Verify generated front matter builds successfully.\n- [ ] Update maintained developer guidance with current behavior.\n\n### Requirement verification\n\n- Direct helper tests prove one- and multi-author output matches the approved\n  front-matter contract.\n- A real Eleventy build consumes helper-produced front matter successfully.\n- Documentation matches the verified supported behavior and labels any\n  transition-only behavior accurately.\n\n### Additional implementation verification\n\n- Test names that would break unquoted YAML or HTML/XML output.\n- Confirm no documentation presents the legacy field as current guidance after\n  cutover.",
    "tasks/20260919-author-metadata-migration/050-evidence-and-legacy-cutover.md": "# Prove migration completeness and remove legacy dependence\n\nClose the migration only after content and generated-output evidence prove the\nsite no longer depends on the single-name field, then make the legacy form\nunavailable with a regression test.\n\nParent Task: tasks/20260919-author-metadata-migration/000-main.md\n\nDepends On: tasks/20260919-author-metadata-migration/020-compatibility-and-rendering.md, tasks/20260919-author-metadata-migration/030-content-migration.md, tasks/20260919-author-metadata-migration/040-authoring-tool-and-guidance.md\n\n## Requirements checklist\n\n- [ ] Run the complete relevant test suite and production build against the\n  migrated content and structured fixtures.\n- [ ] Verify generated post, home, archive, tag, feed, and sitemap output has no\n  remaining legacy author dependency and preserves required site behavior.\n- [ ] Verify source content, templates, scripts, and tests have no supported\n  runtime dependency on the legacy field.\n- [ ] Remove the temporary compatibility path only after the preceding\n  evidence is recorded.\n- [ ] Make the final legacy form fail clearly and add regression coverage for\n  that rejection.\n\n## Open requirement questions and material decisions\n\n- The exact rejection error/message and whether rejection occurs at build,\n  validation, or authoring input are implementation details only after the\n  parent contract defines the final boundary.\n- If external content outside this repository is discovered, pause the\n  cutover and ask whether that source is in scope; do not claim repository\n  evidence proves external independence.\n\n## Supporting facts\n\nThe current test command is `node --test tests/*.test.js`, and the production\nbuild command is `eleventy` via `npm run build`. Existing archive and author\ntest files do not yet execute assertions, so this gate must establish real\ncoverage rather than rely on their comments.\n\n## Execution plan\n\nStatus: Draft\n\nRun source scans that exclude planning text but include all supported content,\ntemplates, scripts, and tests. Build with migrated posts plus explicit\nsingle-/multi-author fixtures, inspect every generated surface, and run the\nfull test command. Record the evidence in the parent task. Only then remove\nthe compatibility reader and add a negative test showing that a legacy\nfront-matter post is rejected at the chosen boundary. Re-run the build and\ntests after removal, and update the task checklist only from those results.\n\n### Implementation decisions and open questions\n\nThe cutover is a gated decision, not a date-based cleanup. Any remaining\nlegacy source read, generated legacy output, or unclassified content blocks\nrejection and must be resolved or explicitly brought back to the parent task\nfor scope review.\n\n### Documentation\n\nUpdate the developer guidance to state that the structured field is now\nrequired and the legacy field is rejected only when the recorded evidence\nsupports that claim. Preserve migration notes only if they help maintainers\nhandle historical content.\n\n### Task checklist\n\n- [ ] Run source-content and runtime-dependency scans.\n- [ ] Run production build and inspect all relevant generated surfaces.\n- [ ] Run `npm test` and record meaningful passing coverage.\n- [ ] Record the evidence threshold as met or identify blockers.\n- [ ] Remove compatibility handling only after the threshold is met.\n- [ ] Add and pass final legacy-rejection regression coverage.\n- [ ] Re-run build/tests and update parent requirement evidence.\n\n### Requirement verification\n\n- Source scan proves no supported post, template, script, test, or config\n  depends on the legacy field.\n- Generated-output scan/build proves all relevant pages and feeds are produced\n  from structured metadata and meet the approved output contract.\n- Full test and build runs pass after compatibility removal.\n- A negative regression test proves the legacy form is rejected at the final\n  approved boundary.\n\n### Additional implementation verification\n\n- Check generated output for accidental empty author elements, duplicate\n  authors, malformed feed XML, and URL/order regressions.\n- Confirm the final source scan does not mistake task-history wording for a\n  runtime dependency, while still covering all executable inputs."
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
        "requirement_count": 6,
        "title": "Migrate post author metadata to structured multi-author data"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260919-author-metadata-migration/000-main.md",
        "path": "tasks/20260919-author-metadata-migration/010-contract-and-inventory.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 4,
        "title": "Define the author metadata contract and dependency inventory"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260919-author-metadata-migration/000-main.md",
        "path": "tasks/20260919-author-metadata-migration/020-compatibility-and-rendering.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Move templates and generated surfaces to structured authors"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260919-author-metadata-migration/000-main.md",
        "path": "tasks/20260919-author-metadata-migration/030-content-migration.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 4,
        "title": "Migrate existing post front matter safely"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260919-author-metadata-migration/000-main.md",
        "path": "tasks/20260919-author-metadata-migration/040-authoring-tool-and-guidance.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 4,
        "title": "Update the authoring helper and developer guidance"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260919-author-metadata-migration/000-main.md",
        "path": "tasks/20260919-author-metadata-migration/050-evidence-and-legacy-cutover.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Prove migration completeness and remove legacy dependence"
      }
    ],
    "implementation_task_count": 5,
    "parent_links": [
      {
        "child": "tasks/20260919-author-metadata-migration/010-contract-and-inventory.md",
        "parent": "tasks/20260919-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260919-author-metadata-migration/020-compatibility-and-rendering.md",
        "parent": "tasks/20260919-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260919-author-metadata-migration/030-content-migration.md",
        "parent": "tasks/20260919-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260919-author-metadata-migration/040-authoring-tool-and-guidance.md",
        "parent": "tasks/20260919-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260919-author-metadata-migration/050-evidence-and-legacy-cutover.md",
        "parent": "tasks/20260919-author-metadata-migration/000-main.md",
        "resolves": true
      }
    ],
    "phase_named_files": [],
    "task_directory_count": 1,
    "task_file_count": 6
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
    "actual_task_count": 5,
    "deliverable_mappings": [
      {
        "deliverable_id": "AUTHOR-D1",
        "task_paths": [
          "tasks/20260919-author-metadata-migration/010-contract-and-inventory.md",
          "tasks/20260919-author-metadata-migration/020-compatibility-and-rendering.md"
        ],
        "coverage": "complete",
        "coherence": "fragmented",
        "reason": "Schema/contract and inventory are isolated in 010 while the normalization implementation lives inside 020; the contract phase is separated from the compatibility delivery it only enables."
      },
      {
        "deliverable_id": "AUTHOR-D2",
        "task_paths": [
          "tasks/20260919-author-metadata-migration/020-compatibility-and-rendering.md"
        ],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "020 moves post layout, listings, and feed to the structured model while keeping legacy rendering, leaving a clear dual-format working state — the combination the target explicitly permits."
      },
      {
        "deliverable_id": "AUTHOR-D3",
        "task_paths": [
          "tasks/20260919-author-metadata-migration/030-content-migration.md",
          "tasks/20260919-author-metadata-migration/040-authoring-tool-and-guidance.md"
        ],
        "coverage": "complete",
        "coherence": "fragmented",
        "reason": "AUTHOR-3 is split across a content rewrite (030) and an authoring-helper/docs update (040), matching the target's fragmentation example of content and helper updates split without a single owning deliverable."
      },
      {
        "deliverable_id": "AUTHOR-D4",
        "task_paths": [
          "tasks/20260919-author-metadata-migration/050-evidence-and-legacy-cutover.md"
        ],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "050 pairs fresh content/generated-output evidence with compatibility removal and a rejection regression test, exactly the gated retirement deliverable."
      }
    ],
    "mergeable_groups": [
      {
        "task_paths": [
          "tasks/20260919-author-metadata-migration/010-contract-and-inventory.md",
          "tasks/20260919-author-metadata-migration/020-compatibility-and-rendering.md"
        ],
        "reason": "010 produces no working state; its contract, inventory, and boundary definition only enable 020's normalization and surface adoption. Merged, they form the acceptable single dual-format normalization/adoption deliverable."
      },
      {
        "task_paths": [
          "tasks/20260919-author-metadata-migration/030-content-migration.md",
          "tasks/20260919-author-metadata-migration/040-authoring-tool-and-guidance.md"
        ],
        "reason": "Content migration and authoring-helper update are two halves of one outcome (maintained content and producers stop creating legacy dependencies); documentation is work within the deliverable, not a reason to split."
      }
    ],
    "unmatched_tasks": [],
    "overpacked_tasks": [],
    "valid_layer_boundaries": [],
    "automatic_layer_fragments": [],
    "dependency_issues": [
      "030-content-migration.md depends only on 010; converting every post to the structured field before 020's normalization/rendering lands permits an intermediate revision that builds but renders broken or empty author output, violating AUTHOR-5.",
      "040-authoring-tool-and-guidance.md depends only on 010; helper-produced structured front matter cannot be verified through a real build into correct pages until 020 lands, so its declared ordering can produce an unsupported intermediate state."
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
              "tasks/20260919-author-metadata-migration/010-contract-and-inventory.md",
              "tasks/20260919-author-metadata-migration/020-compatibility-and-rendering.md"
            ],
            "description": "Schema/contract task separated from the compatibility delivery (target fragmentation example); 5 tasks cover 4 coherent deliverables."
          },
          {
            "task_paths": [
              "tasks/20260919-author-metadata-migration/030-content-migration.md",
              "tasks/20260919-author-metadata-migration/040-authoring-tool-and-guidance.md"
            ],
            "description": "Content rewrite and authoring-helper update split into separate tasks where the target defines one 'migrate content and authoring tools' deliverable."
          }
        ]
      },
      "phase_only_children": {
        "status": "partial",
        "occurrences": [
          {
            "task_paths": [
              "tasks/20260919-author-metadata-migration/010-contract-and-inventory.md"
            ],
            "description": "Pure specification/inventory phase whose completion only completes the later deliveries; its value is realized entirely inside 020/030/040."
          }
        ]
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
        "status": "present",
        "occurrences": [
          {
            "task_paths": [
              "tasks/20260919-author-metadata-migration/030-content-migration.md",
              "tasks/20260919-author-metadata-migration/020-compatibility-and-rendering.md"
            ],
            "description": "Missing dependency 030 -> 020: structured content can replace legacy front matter before normalization/rendering consumes it, permitting broken generated output at an intermediate revision (AUTHOR-5)."
          },
          {
            "task_paths": [
              "tasks/20260919-author-metadata-migration/040-authoring-tool-and-guidance.md",
              "tasks/20260919-author-metadata-migration/020-compatibility-and-rendering.md"
            ],
            "description": "Missing dependency 040 -> 020: the helper's structured output has no correct rendering path until 020 lands, so the declared graph permits an unusable intermediate state."
          }
        ]
      },
      "piecewise_crossing_evidence": {
        "status": "none",
        "occurrences": []
      }
    },
    "partition_quality_score": 78,
    "handoff_quality_score": 82,
    "summary": "All five approved outcomes are covered and the partition largely follows compatible working states: 020 legitimately combines normalization with generated-surface adoption (an approved alternative leaving a dual-format working state), each deliverable carries its own tests/docs as internal work, and 050 correctly owns fresh evidence-gated retirement rather than re-owning per-deliverable evidence. Two splits match the target's own fragmentation examples — 010 isolates contract/schema definition from the compatibility delivery it only enables, and 030/040 split the content-and-tools outcome — giving 5 tasks for 4 coherent deliverables (ratio 1.25, low severity). The material defect is dependency safety: 030 and 040 declare only 010, so the graph permits structured content and helper output to land before 020's normalization/rendering, allowing broken intermediate revisions. The required production crossing (real front matter through normalization and the Eleventy build into pages, archives, and feeds) is named by direct build-level checks at every migration state in 020/030/040/050, so crossing ownership is complete."
  }
}
```
