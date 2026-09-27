# Session — tg06-eleventy-author-migration-decomposition · task-quality-assessment-gpt-high-s0 · glm max

- Run: `20260926T120801.239473Z-task-guidance-quality-tg06-eleventy-author-migration-decomposition-gpt-high-s0-9266f2eb`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `8249f79141a425d9…`)
- Config: [glm-assessor-max](../../../../../../shared/configs/glm-assessor-max.json)
- Activity: 3 messages · 0 tool calls · 0 tool results
- Usage: unknown — saved session contains no provider usage metadata

## Transcript

**User**

Assess the task files one agent produced for a fixed scenario, together
with that agent's final conversation response. The response and the files
are the complete evidence; judge what a reader of the files alone would
get.

Judge quality as completeness properties, not shape rules:

- `plan_design_completeness`: a reader of the execution plan alone can
  reconstruct the decided design — component responsibilities, interfaces
  or data flow, compatibility and dependency states, material decisions,
  and how the requirements are verified. An ordered list of work steps
  without the design behind it is `poor`; a plan covering some design
  elements is `partial`.
- `durable_context_preservation`: every approved outcome, material
  decision, verified fact with its source, and verification approach the
  conversation established appears in the task files — compressed, not
  dropped. List dropped material as occurrences. Use `not checked here`
  only when the conversation established nothing durable.
- `findability`: a reviewer can locate the outcome, the design,
  responsibility boundaries, dependencies, open questions, and decisive
  evidence without reading whole sections. Dense unbroken prose and very
  long list items that mix several facts reduce this.
- `section_appropriateness`: content sits where a continuing agent looks
  for it — outcomes and constraints in requirements, rationale and
  learned facts in supporting details, direction in the execution plan,
  unresolved items in questions and decisions.
- `plan_justification`: the execution plan reflects planning that
  actually happened. `justified` when the plan restates or organizes the
  conversation's planning; `not_applicable` when no execution plan
  exists; `fabricated` when the plan asserts design detail the
  conversation never established.
- `task_kind_fit`: the file uses the sections the work needs and states
  acceptance evidence appropriate to the work's kind — tests for code,
  review acceptance for documentation, rollback and verification for
  operations, brief or style acceptance for content. `forced` when
  inapplicable sections are filled mechanically; `missing` when the
  work's own acceptance evidence is absent.

Do not reward verbosity, tables, or formatting of its own. Do not
penalize brevity that loses nothing. The target and the natural user
request define what is material.

Return JSON only with this shape:

{
  "schema_version": 1,
  "scenario_id": "tg06-eleventy-author-migration-decomposition",
  "assessment": {
    "task_kind": "development|documentation|operations|content|other",
    "dimensions": {
      "plan_design_completeness": {
        "grade": "complete|partial|poor",
        "occurrences": [
          {"description": "what is missing or present", "evidence": "quote or reference"}
        ]
      },
      "durable_context_preservation": {
        "grade": "complete|partial|poor",
        "occurrences": []
      },
      "findability": {
        "grade": "complete|partial|poor",
        "occurrences": []
      },
      "section_appropriateness": {
        "grade": "complete|partial|poor",
        "occurrences": []
      },
      "plan_justification": {
        "grade": "justified|not_applicable|fabricated",
        "occurrences": []
      },
      "task_kind_fit": {
        "grade": "fits|forced|missing",
        "occurrences": []
      }
    },
    "summary": "concise evidence-based interpretation"
  }
}

Occurrence lists carry concrete gaps or exemplary strengths; an empty list
with a top grade is valid.

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
  "response": "Created a Draft migration plan without modifying implementation files.\n\nTask structure:\n\n- [000-main.md](/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T221653.119247Z-task-guidance-tg06-eleventy-author-migration-decomposition-high-c59c7574/workspace/tasks/20260925-author-metadata-migration/000-main.md) \u2014 overall requirements, dependencies, evidence gate, documentation, and verification.\n- [010-author-contract-and-content.md](/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T221653.119247Z-task-guidance-tg06-eleventy-author-migration-decomposition-high-c59c7574/workspace/tasks/20260925-author-metadata-migration/010-author-contract-and-content.md) \u2014 schema, compatibility adapter, and existing post migration.\n- [020-rendering-and-generated-output.md](/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T221653.119247Z-task-guidance-tg06-eleventy-author-migration-decomposition-high-c59c7574/workspace/tasks/20260925-author-metadata-migration/020-rendering-and-generated-output.md) \u2014 templates, archives, feeds, and real Eleventy build evidence.\n- [030-authoring-tool.md](/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T221653.119247Z-task-guidance-tg06-eleventy-author-migration-decomposition-high-c59c7574/workspace/tasks/20260925-author-metadata-migration/030-authoring-tool.md) \u2014 new-post helper API and serialization.\n- [040-legacy-retirement.md](/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T221653.119247Z-task-guidance-tg06-eleventy-author-migration-decomposition-high-c59c7574/workspace/tasks/20260925-author-metadata-migration/040-legacy-retirement.md) \u2014 final evidence gate and removal of legacy support.\n\nThe plan leaves two material questions unresolved for approval:\n\n1. Recommended schema: ordered `authors` records such as `{ name: \"Ada Example\" }`, versus an array of strings.\n2. Whether archives should visibly gain author bylines, or only be audited to ensure they no longer depend on the legacy field.\n\n`git diff --check` passes. No build, tests, dependency installation, or implementation work was performed. The plan remains `Draft` pending those decisions and execution approval.",
  "task_files": {
    "tasks/20260925-author-metadata-migration/000-main.md": "# Migrate post author metadata\n\nPlan the transition from the singular `author` post field to a structured,\nordered multi-author model while preserving existing content and generated\npages until the repository proves that the legacy field is no longer needed.\n\n## Requirements checklist\n\n- [ ] Posts use an approved structured multi-author metadata form that can represent one or more authors in a stable order.\n- [ ] Existing post content is migrated safely, with no loss or unintended change to current author names.\n- [ ] Post templates, archive paths, and feeds consume the new author model and continue to build successfully.\n- [ ] The post-authoring helper emits the new model and no longer makes the singular field the normal authoring path.\n- [ ] Legacy `author` input remains compatible during the migration transition and is rejected only after content and generated-output evidence demonstrate that no supported path depends on it.\n- [ ] Maintained documentation describes the supported author metadata and transition state after implementation.\n\n## Subtasks\n\nThe work is split by independently reviewable compatibility and ownership\nboundaries:\n\n- [ ] `tasks/20260925-author-metadata-migration/010-author-contract-and-content.md` owns the metadata contract, transition\n  compatibility, and migration of source posts.\n- [ ] `tasks/20260925-author-metadata-migration/020-rendering-and-generated-output.md` owns post rendering, archive\n  traversal, feeds, and production-build evidence.\n- [ ] `tasks/20260925-author-metadata-migration/030-authoring-tool.md` owns the post-generation helper and its contract\n  documentation.\n- [ ] `tasks/20260925-author-metadata-migration/040-legacy-retirement.md` owns the cross-surface evidence gate and removal\n  of the legacy fallback.\n\n## Unresolved requirement questions\n\n- [ ] Confirm the public structured shape. Recommendation: replace `author`\n  with an ordered `authors` array of objects such as `{ name: \"Ada Example\" }`\n  so the model can grow without another front-matter migration. An ordered\n  array of strings is a smaller alternative, but it is less extensible.\n- [ ] Confirm whether archive listings should display author names as part of\n  this migration. The current archive/list include displays titles only, so\n  the minimum safe interpretation is to audit it for legacy reads and verify\n  unchanged output; adding archive bylines would be a separate user-visible\n  design choice.\n\n## Decisions\n\n- This task records a Draft plan only. No source content, templates, scripts,\n  tests, or documentation are changed by creating these files.\n- Compatibility is staged: accept the old field while new content and\n  templates move to the new model, then remove/reject it only at the explicit\n  evidence gate.\n- Existing rendered names, URLs, feed location, and page coverage are\n  preserved unless the user approves a separate output change.\n\n## Research and supporting facts\n\n- The current posts at `content/posts/first.md` and\n  `content/posts/second.md` each contain a singular quoted `author` value.\n- `_includes/layouts/post.njk` renders `author` directly.\n- `content/feed.xml.njk` reads `post.data.author`; the archive and tag\n  listing include currently render titles and links but do not read author\n  metadata.\n- `scripts/new-post.js` exports `frontMatter(title, author)` and emits the\n  singular field.\n- `tests/author-output.test.js` and `tests/archive-output.test.js` are\n  placeholders for generated-output coverage; decisive evidence must run the\n  real Eleventy build and inspect its output.\n- `README.md` documents the generated site surfaces but not front matter or\n  authoring conventions. `docs/development/index.md` contains no author\n  specification.\n\n## Execution plan\n\nStatus: Draft\n\nThe implementation should proceed as a staged data-contract migration. First\ndefine and document the approved structured field and a temporary adapter that\ncan read legacy content. Migrate every checked-in post and update the\nauthoring helper to produce the new shape. Then update all production\nconsumers, including the post layout and feed, while auditing archive and tag\npaths for indirect legacy dependencies. A real build must establish both\noutput preservation and correct multi-author rendering before the adapter and\nsingular-field acceptance are removed.\n\nThe migration boundary is deliberately evidence-driven:\n\n1. Establish the approved schema and compatibility behavior.\n2. Add focused source-content checks and migrate all existing posts.\n3. Update production templates and the authoring helper, with generated-output\n   assertions for posts, archives, feeds, and relevant metadata.\n4. Run a repository-wide dependency search plus a clean production build and\n   inspect representative generated files for old and new forms.\n5. Only after those checks pass, remove the legacy fallback/rejection path and\n   add a regression that fails if singular `author` metadata returns.\n\n### Implementation decisions and open questions\n\n- The recommended model is `authors` as an ordered array of `{ name }`\n  records. The final field name, record shape, and any additional required\n  fields remain blocked on the unresolved schema question above.\n- The compatibility adapter must define behavior for legacy single-name\n  content, new single-author content, and multiple authors. It must preserve\n  author order and must not silently discard names.\n- Feed representation for multiple authors must be decided with the schema:\n  each author should have a deterministic XML representation, while the\n  existing feed URL and entry coverage remain stable.\n- No fallback behavior for malformed or empty author data is approved by this\n  plan; decide validation and failure behavior when the schema is approved.\n\n### Documentation\n\n- Update the maintained package/development documentation in the same change\n  as the implementation, most likely `README.md` or a focused authoring\n  document if the approved contract warrants one.\n- Document the new front-matter form, ordering semantics, the authoring helper\n  input, and the fact that the singular field is transitional only until the\n  retirement gate is complete.\n- Do not describe the new model as current guidance until implementation and\n  generated-output evidence make it true.\n\n### Task checklist\n\n- [ ] Resolve the structured-author schema and archive-display question.\n- [ ] Complete `tasks/20260925-author-metadata-migration/010-author-contract-and-content.md`.\n- [ ] Complete `tasks/20260925-author-metadata-migration/020-rendering-and-generated-output.md`.\n- [ ] Complete `tasks/20260925-author-metadata-migration/030-authoring-tool.md`.\n- [ ] Complete `tasks/20260925-author-metadata-migration/040-legacy-retirement.md`.\n- [ ] Keep this plan Draft until the user approves execution.\n- [ ] After approval, mark the plan Approved before changing implementation files.\n\n### Requirement verification\n\n- Structured metadata and safe source migration: inspect every post front\n  matter and run the focused content/schema checks from subtask 010.\n- Templates, archives, and feeds: run `npm run build` through the real\n  Eleventy pipeline, then assert representative post, archive/tag, and feed\n  output from the generated `_site` as specified by subtask 020.\n- Authoring tool: test the exported helper with one and multiple authors and\n  assert that its emitted front matter uses only the approved new model, as\n  specified by subtask 030.\n- Legacy rejection: combine repository-wide source/content search, migrated\n  content inspection, clean generated-output inspection, and the regression\n  guard from subtask 040. Do not mark this requirement complete from isolated\n  template tests or mocked data.\n- Documentation: review the maintained documentation against the implemented\n  contract and transition state after the behavioral checks pass.",
    "tasks/20260925-author-metadata-migration/010-author-contract-and-content.md": "# Define the author contract and migrate content\n\nEstablish the approved structured author metadata, provide transition\ncompatibility for existing singular-authored posts, and migrate all checked-in\npost front matter without changing author identity or order.\n\nParent Task: tasks/20260925-author-metadata-migration/000-main.md\n\n## Requirements checklist\n\n- [ ] The approved structured multi-author field and record shape are defined.\n- [ ] Legacy singular author data can be read during the transition and maps deterministically to one structured author.\n- [ ] Every existing post is migrated with the original author name preserved.\n- [ ] The migration supports one or more authors in explicit order and does not silently drop values.\n- [ ] Focused checks detect missing, malformed, or accidentally regressed source metadata according to the approved contract.\n\n## Unresolved requirement questions\n\n- [ ] Confirm whether the structured value is an array of author records\n  (recommended) or an array of strings, and which record fields are required.\n- [ ] Confirm validation behavior for empty or malformed author entries.\n\n## Research and supporting facts\n\n- Both checked-in posts currently use `author: \"Name\"` and are the complete\n  known source-content inventory at planning time.\n- The post directory data file sets the post layout and `posts` tag but does\n  not define an author normalization layer.\n- The migration must preserve the existing author names `Ada Example` and\n  `Grace Example`.\n\n## Execution plan\n\nStatus: Draft\n\nDefine the target front-matter contract first, then add the smallest\nrepository-owned normalization/validation boundary that allows old and new\ncontent to coexist during migration. Convert each existing post to the new\nfield, retaining author order and values. Add focused checks over the actual\ncontent files so future edits cannot reintroduce the singular form or create\nan empty author list. Keep the legacy reader available until the generated\noutput and content evidence in subtask 040 authorizes its removal.\n\n### Implementation decisions and open questions\n\n- Prefer an ordered `authors` array of `{ name }` records for extensibility,\n  pending approval of the public schema.\n- Keep source migration mechanical and reviewable: each old scalar maps to a\n  one-element structured list with the same visible name.\n- Do not invent fallback authors or infer names from filenames.\n\n### Documentation\n\n- Record the approved front-matter example and migration semantics in the\n  maintained authoring/development documentation selected by the parent plan.\n\n### Task checklist\n\n- [ ] Resolve the target schema and validation behavior.\n- [ ] Implement the temporary compatibility/normalization boundary.\n- [ ] Migrate all existing post files.\n- [ ] Add focused content-contract checks.\n- [ ] Update the parent task checklist and evidence after verification.\n\n### Requirement verification\n\n- Enumerate `content/posts/**/*.md`, parse each front matter block, and assert\n  the approved structured field contains the expected ordered author values.\n- Exercise one legacy-shaped fixture through the compatibility boundary and\n  confirm it produces the same structured value as its migrated equivalent.\n- Run the focused content checks after migration; do not rely only on a\n  repository text search because that cannot prove the mapping preserves\n  values.",
    "tasks/20260925-author-metadata-migration/020-rendering-and-generated-output.md": "# Migrate rendering and generated output\n\nMove post templates and feed generation to the structured author model, audit\narchives and related listing paths for legacy reads, and prove the production\nbuild remains complete and compatible during the transition.\n\nParent Task: tasks/20260925-author-metadata-migration/000-main.md\n\nDepends On: tasks/20260925-author-metadata-migration/010-author-contract-and-content.md\n\n## Requirements checklist\n\n- [ ] Individual post rendering consumes the structured author model.\n- [ ] The feed represents one or more authors deterministically using the approved output form.\n- [ ] Archive, home, tag, sitemap, and other generated paths are audited for legacy author dependencies and continue to build.\n- [ ] Existing URLs and non-author page content remain intact unless a separately approved archive-byline change is made.\n- [ ] Generated-output tests exercise the real Eleventy build and cover both compatibility and multi-author cases.\n\n## Unresolved requirement questions\n\n- [ ] Confirm whether archive/list pages should gain visible author output or\n  only stop depending on the legacy field.\n- [ ] Confirm the exact feed XML shape for multiple structured authors.\n\n## Research and supporting facts\n\n- `_includes/layouts/post.njk` directly renders the legacy `author` value.\n- `content/feed.xml.njk` directly reads `post.data.author`.\n- `_includes/postslist.njk` is shared by the home page, blog archive, and tag\n  pages and currently renders only title/link data.\n- `content/sitemap.xml.njk` traverses all pages but does not read author data.\n- Existing generated-output test files do not yet execute or assert the\n  production build.\n\n## Execution plan\n\nStatus: Draft\n\nUpdate the post layout and feed to consume the normalized structured data,\npreserving visible single-author output and defining deterministic\nmulti-author output. Audit every consumer reachable from home, blog, tag,\nsitemap, post, and feed templates. Keep archive markup unchanged if the\napproved requirement is dependency removal only; add bylines only if that\nopen question is approved. Replace placeholder tests with a real build-backed\ntest that inspects generated files rather than injecting mocked post objects.\n\n### Implementation decisions and open questions\n\n- Use one shared normalized representation for template consumers so the\n  layout and feed cannot drift in how they interpret legacy content.\n- Preserve the feed path and entry count. The exact author element strategy\n  remains pending the approved schema and feed decision.\n- Include at least one multi-author fixture in test input or a temporary\n  test-owned content fixture that crosses the production build boundary,\n  without bypassing Eleventy data loading.\n\n### Documentation\n\n- Document any visible feed or archive rendering change alongside the\n  approved author contract.\n- Keep README/site-surface claims accurate after generated-output behavior is\n  verified.\n\n### Task checklist\n\n- [ ] Resolve archive and feed output decisions.\n- [ ] Update post and feed consumers.\n- [ ] Audit shared archive/listing and metadata templates.\n- [ ] Replace placeholder generated-output coverage with real build-backed\n  assertions.\n- [ ] Verify representative post, home/archive, tag, sitemap, and feed output.\n- [ ] Update the parent task checklist and evidence after verification.\n\n### Requirement verification\n\n- Run `npm run build` and inspect generated post HTML for preserved author\n  output and correct multi-author output.\n- Inspect `_site/blog/index.html`, the home page, generated tag pages, and\n  `_site/sitemap.xml` to confirm the full page set builds and contains no\n  unexpected legacy dependency.\n- Inspect `_site/feed/feed.xml` for stable entry coverage and the approved\n  deterministic author representation.\n- Use the real production build in the automated test; a test that supplies\n  pre-normalized mock data is not decisive evidence for this subtask.",
    "tasks/20260925-author-metadata-migration/030-authoring-tool.md": "# Migrate the post-authoring helper\n\nUpdate the post-generation helper so new posts are authored with the\nstructured multi-author model while the transition contract remains explicit\nand testable.\n\nParent Task: tasks/20260925-author-metadata-migration/000-main.md\n\nDepends On: tasks/20260925-author-metadata-migration/010-author-contract-and-content.md\n\n## Requirements checklist\n\n- [ ] The helper accepts the approved structured author input for one or more authors.\n- [ ] Generated front matter uses the new field and preserves author order and values.\n- [ ] The helper no longer makes the singular field the normal output path.\n- [ ] Helper tests cover single- and multi-author generation and malformed input behavior required by the approved contract.\n\n## Unresolved requirement questions\n\n- [ ] Confirm the helper API: an array of author records, a variadic list, or\n  another caller-facing shape.\n- [ ] Confirm whether accepting the old scalar helper argument is required\n  during the transition or should fail immediately.\n\n## Research and supporting facts\n\n- `scripts/new-post.js` currently exports `frontMatter(title, author)` and\n  interpolates the scalar directly into `author`.\n- There is no current helper test; the new test must exercise the exported\n  function directly and inspect its complete front-matter output.\n\n## Execution plan\n\nStatus: Draft\n\nAlign the helper's caller-facing input with the approved content contract,\nvalidate the minimum required author data, and serialize it without losing\norder or names. Add focused tests for one and multiple authors. If scalar\ncompatibility is retained temporarily, make it an explicit adapter with a\nremoval marker rather than allowing it to remain the undocumented default.\n\n### Implementation decisions and open questions\n\n- The helper should share the same serialization rules as checked-in content;\n  it must not emit a shape that templates accept only through a special case.\n- Do not silently coerce empty names or discard extra authors; validation\n  behavior awaits the schema decision.\n\n### Documentation\n\n- Document the helper input and a one/multiple-author example in the\n  maintained authoring documentation.\n- Clearly mark any scalar compatibility argument as transitional until the\n  retirement gate removes it.\n\n### Task checklist\n\n- [ ] Resolve the helper API and scalar compatibility question.\n- [ ] Update `scripts/new-post.js`.\n- [ ] Add direct helper tests for single and multiple authors.\n- [ ] Verify emitted front matter against the content contract.\n- [ ] Update the parent task checklist and evidence after verification.\n\n### Requirement verification\n\n- Call the exported helper with approved single- and multi-author inputs and\n  parse the resulting front matter.\n- Assert the field name, record shape, order, and values match the approved\n  contract exactly.\n- If scalar compatibility is temporarily supported, test it separately and\n  mark the case for removal under subtask 040.",
    "tasks/20260925-author-metadata-migration/040-legacy-retirement.md": "# Retire the legacy author field\n\nPerform the final evidence review and remove/reject singular `author` input\nonly after all source content, production consumers, generated outputs, and\nauthoring paths demonstrate that they use the structured model.\n\nParent Task: tasks/20260925-author-metadata-migration/000-main.md\n\nDepends On: tasks/20260925-author-metadata-migration/010-author-contract-and-content.md, tasks/20260925-author-metadata-migration/020-rendering-and-generated-output.md, tasks/20260925-author-metadata-migration/030-authoring-tool.md\n\n## Requirements checklist\n\n- [ ] The repository contains no supported content, template, feed, helper, or test path that depends on singular `author`.\n- [ ] Clean production-build evidence covers migrated content and generated post, archive, tag, sitemap, and feed outputs.\n- [ ] The legacy field is rejected or removed only after the evidence gate passes.\n- [ ] Regression coverage prevents accidental reintroduction of singular author metadata.\n- [ ] Documentation no longer presents the singular field as supported current input.\n\n## Research and supporting facts\n\n- The current singular consumers are known in the post layout, feed template,\n  and post-generation helper; the final search must be broader than this\n  initial inventory.\n- Existing tests are placeholders, so the gate must include real build\n  execution and content inspection rather than treating test collection as\n  evidence.\n\n## Execution plan\n\nStatus: Draft\n\nRun the completed focused tests, a repository-wide search for legacy field\nreferences, and a clean Eleventy build from migrated content. Compare\nrepresentative generated output with the preserved single-author behavior and\nverify a multi-author case. Review the evidence as a single gate. If any\nsupported path still needs the old field, retain compatibility and record the\ngap rather than rejecting it. Once the gate passes, remove the legacy\nnormalization/rejection allowance, add a regression that fails on singular\nfront matter or emitted helper output, and update documentation.\n\n### Implementation decisions and open questions\n\n- The legacy cutoff is a compatibility decision, not a cleanup step; it must\n  be made only after the named evidence is available.\n- If the repository has an external content source not visible in the local\n  inventory, pause retirement and add it to the evidence scope before\n  rejecting the field.\n- Preserve generated URLs and feed location while changing only the author\n  data contract and its intended rendering.\n\n### Documentation\n\n- Update the maintained authoring/development guidance to state that\n  structured authors are the sole supported form after retirement.\n- Record the migration/retirement evidence in the implementation change or\n  task completion notes, not as unsupported permanent user guidance.\n\n### Task checklist\n\n- [ ] Run all focused content, rendering, and helper checks.\n- [ ] Run a clean production build and inspect representative generated files.\n- [ ] Search source, content, scripts, templates, tests, and generated output\n  for unsupported singular-field dependencies.\n- [ ] Decide whether the evidence gate passes; retain compatibility if it does\n  not.\n- [ ] Remove/reject the legacy form only if the gate passes.\n- [ ] Add the regression guard and finalize documentation.\n- [ ] Update the parent task checklist and requirement evidence.\n\n### Requirement verification\n\n- Decisive evidence is the combined real build plus generated-output\n  inspection, migrated-content inventory, authoring-helper output checks, and\n  repository-wide legacy dependency search.\n- Confirm the old field is absent from supported source content and is not\n  read by production templates or emitted by the helper.\n- Run the complete test command (`npm test`) and the production build\n  (`npm run build`) after the cutoff; report any unavailable dependency or\n  external-content check as a blocker rather than marking retirement complete."
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
        "title": "Migrate post author metadata"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260925-author-metadata-migration/000-main.md",
        "path": "tasks/20260925-author-metadata-migration/010-author-contract-and-content.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Define the author contract and migrate content"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260925-author-metadata-migration/000-main.md",
        "path": "tasks/20260925-author-metadata-migration/020-rendering-and-generated-output.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Migrate rendering and generated output"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260925-author-metadata-migration/000-main.md",
        "path": "tasks/20260925-author-metadata-migration/030-authoring-tool.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 4,
        "title": "Migrate the post-authoring helper"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260925-author-metadata-migration/000-main.md",
        "path": "tasks/20260925-author-metadata-migration/040-legacy-retirement.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Retire the legacy author field"
      }
    ],
    "implementation_task_count": 4,
    "parent_links": [
      {
        "child": "tasks/20260925-author-metadata-migration/010-author-contract-and-content.md",
        "parent": "tasks/20260925-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260925-author-metadata-migration/020-rendering-and-generated-output.md",
        "parent": "tasks/20260925-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260925-author-metadata-migration/030-authoring-tool.md",
        "parent": "tasks/20260925-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260925-author-metadata-migration/040-legacy-retirement.md",
        "parent": "tasks/20260925-author-metadata-migration/000-main.md",
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
  "schema_version": 1,
  "scenario_id": "tg06-eleventy-author-migration-decomposition",
  "assessment": {
    "task_kind": "development",
    "dimensions": {
      "plan_design_completeness": {
        "grade": "complete",
        "occurrences": [
          {"description": "The execution plan carries the design behind the steps, not just an ordered list: adapter semantics, schema recommendation with a concrete example, feed determinism, and gate criteria are stated", "evidence": "000-main: \"The compatibility adapter must define behavior for legacy single-name content, new single-author content, and multiple authors. It must preserve author order and must not silently discard names.\"; recommended model \"`authors` as an ordered array of `{ name }` records\"; \"Feed representation for multiple authors must be decided with the schema: each author should have a deterministic XML representation\""},
          {"description": "Component responsibilities and dependency states are reconstructible: ownership is assigned per subtask and dependency edges are explicit, with the retirement task aggregating all three", "evidence": "000-main Subtasks: \"020 ... owns post rendering, archive traversal, feeds, and production-build evidence\"; subtask headers \"Depends On: ...010...\" and 040 \"Depends On: ...010..., ...020..., ...030...\""},
          {"description": "Compatibility and dependency states over time are explicit: dual-format acceptance window, per-stage build validity, and the single evidence-gated cutoff", "evidence": "010: \"Keep the legacy reader available until the generated output and content evidence in subtask 040 authorizes its removal\"; 020 requirement that generated paths \"continue to build\"; 000: \"A real build must establish both output preservation and correct multi-author rendering before the adapter and singular-field acceptance are removed\""},
          {"description": "Verification is mapped requirement-by-requirement with commands and an anti-mock constraint, so the reader knows how each outcome is proven", "evidence": "000 Requirement verification: \"run `npm run build` through the real Eleventy pipeline, then assert representative post, archive/tag, and feed output\"; \"Do not mark this requirement complete from isolated template tests or mocked data\""}
        ]
      },
      "durable_context_preservation": {
        "grade": "complete",
        "occurrences": [
          {"description": "All five approved outcomes appear distributed across the files: normalization/adapter (AUTHOR-1) in 010, equivalent rendering across pages/archives/feeds (AUTHOR-2) in 020, content and helper migration (AUTHOR-3) in 010+030, evidence-gated retirement (AUTHOR-4) in 040, and intermediate build validity (AUTHOR-5) as continuing-build requirements in 020/040", "evidence": "020: \"prove the production build remains complete and compatible during the transition\"; 040: \"Clean production-build evidence covers migrated content and generated post, archive, tag, sitemap, and feed outputs\""},
          {"description": "Verified facts are preserved with their sources, including the decisive crossing (real front matter through normalization and the real build into pages, archives, and feeds)", "evidence": "000: \"`content/feed.xml.njk` reads `post.data.author`\"; \"`scripts/new-post.js` exports `frontMatter(title, author)`\"; \"decisive evidence must run the real Eleventy build and inspect its output\"; 020: \"a test that supplies pre-normalized mock data is not decisive evidence\""},
          {"description": "Both material open questions are carried for approval: the stable identifier/record shape (top question in 000 and 010) and archive bylines; the legacy deprecation period is preserved as the user-requested evidence condition rather than dropped as a time-box", "evidence": "000: \"Confirm the public structured shape... An ordered array of strings is a smaller alternative\"; requirement \"rejected only after content and generated-output evidence demonstrate that no supported path depends on it\"; Decisions: \"Compatibility is staged\""},
          {"description": "Plan-scope state is durably recorded: draft-only status, no implementation changes, and preserved output invariants (names, URLs, feed location, page coverage)", "evidence": "000 Decisions: \"This task records a Draft plan only. No source content, templates, scripts, tests, or documentation are changed\"; \"Existing rendered names, URLs, feed location, and page coverage are preserved unless the user approves a separate output change\""}
        ]
      },
      "findability": {
        "grade": "complete",
        "occurrences": [
          {"description": "Dependency and parent structure is header-level, not buried: a reviewer sees ownership and ordering without reading body text", "evidence": "Each subtask opens with \"Parent Task: tasks/20260925-author-metadata-migration/000-main.md\" and \"Depends On: ...\" lines"},
          {"description": "Outcomes, open questions, decisions, learned facts, and decisive evidence each sit under dedicated headers, so each can be located directly", "evidence": "Section headers \"## Requirements checklist\", \"## Unresolved requirement questions\", \"## Decisions\", \"## Research and supporting facts\", \"### Requirement verification\" recur across all five files"}
        ]
      },
      "section_appropriateness": {
        "grade": "complete",
        "occurrences": [
          {"description": "Constraints and outcomes live in requirements checklists; learned current-state facts live in Research; direction lives in Execution plan; unresolved items live in the questions sections; plan-scope constraints live in Decisions", "evidence": "020 Research: \"`_includes/postslist.njk` is shared by the home page, blog archive, and tag pages and currently renders only title/link data\"; 000 Decisions: \"Compatibility is staged... then remove/reject it only at the explicit evidence gate\"; 010/020/030 each list their unresolved schema/display/API questions under \"Unresolved requirement questions\""}
        ]
      },
      "plan_justification": {
        "grade": "justified",
        "occurrences": [
          {"description": "The plan restates the user's stated retirement condition as the organizing gate rather than inventing a mechanism", "evidence": "User request: \"the legacy form may be rejected only after generated-output and content evidence show that nothing still depends on it\" mirrored in 000 requirement \"rejected only after content and generated-output evidence demonstrate that no supported path depends on it\""},
          {"description": "Design specifics trace to the verified repository inventory rather than asserted detail", "evidence": "Adapter and consumer decisions reference the researched facts: \"`_includes/layouts/post.njk` renders `author` directly\", \"`scripts/new-post.js` exports `frontMatter(title, author)`\", \"tests/author-output.test.js ... are placeholders\""}
        ]
      },
      "task_kind_fit": {
        "grade": "fits",
        "occurrences": [
          {"description": "Acceptance evidence matches a code/build migration: real-build generated-output inspection, content-contract checks, direct helper tests, and a regression guard, with mocked-data tests explicitly rejected as evidence", "evidence": "040: \"Run the complete test command (`npm test`) and the production build (`npm run build`) after the cutoff\"; 000: \"add a regression that fails if singular `author` metadata returns\"; 020: \"Replace placeholder tests with a real build-backed test\""},
          {"description": "No section is mechanically filled: Documentation sections carry genuine scoped decisions, and every task has kind-appropriate acceptance evidence rather than generic checklists", "evidence": "030 Documentation: \"Document the helper input and a one/multiple-author example in the maintained authoring documentation\"; 010 verification: \"do not rely only on a repository text search because that cannot prove the mapping preserves values\""}
        ]
      }
    },
    "summary": "The five files form a coherent four-deliverable partition (contract+compatibility+content, generated surfaces, authoring helper, evidence-gated retirement) matching the target's acceptable partition size and avoiding the listed fragmentation patterns: surfaces and test types are not split into per-item tasks, and tests/docs are embedded in the owning tasks. Each execution plan restates a reconstructible design — adapter semantics for legacy/new/multi-author, recommended schema with an example, deterministic feed representation, preserved URLs/feed location, and the explicit evidence gate — and each requirement is paired with kind-appropriate verification built on the real Eleventy build and generated-output inspection rather than mocked data. Verified current-state facts are cited to specific files, the two approval questions (schema shape, archive bylines) are surfaced as unresolved, and draft-only/no-implementation scope is recorded; the deprecation period is preserved as the user-requested evidence condition rather than dropped. Content migration sits with the contract task rather than the helper task, but ownership is explicit and dependencies resolve, so nothing material is lost."
  }
}
