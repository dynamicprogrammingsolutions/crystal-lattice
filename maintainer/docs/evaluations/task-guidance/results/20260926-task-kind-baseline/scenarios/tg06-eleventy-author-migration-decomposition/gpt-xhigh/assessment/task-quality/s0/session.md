# Session — tg06-eleventy-author-migration-decomposition · task-quality-assessment-gpt-xhigh-s0 · glm max

- Run: `20260926T121011.606870Z-task-guidance-quality-tg06-eleventy-author-migration-decomposition-gpt-xhigh-s0-56344392`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `efdd0ca995e93209…`)
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
  "schema_version": 1,
  "scenario_id": "tg06-eleventy-author-migration-decomposition",
  "assessment": {
    "task_kind": "development",
    "dimensions": {
      "plan_design_completeness": {
        "grade": "partial",
        "occurrences": [
          {
            "description": "Gap: the plan never designs the working state between the source-migration child and the rendering child. After 010 migrates every post to the canonical `authors` form, the post layout and feed still read the removed `author` key until 020 lands, so that intermediate revision publishes output with missing/empty author data; no plan text acknowledges or covers this window.",
            "evidence": "010: 'Source migration and the authoring helper stop producing the legacy key' with R2 'All existing post front matter is migrated'; 020 ordered work step 1: 'Add the normalized author-record access used by the post layout and feed'; 020's own verification treats 'an empty author element' as a defect symptom."
          },
          {
            "description": "Gap: the compatibility normalization is described only in the legacy-to-canonical direction ('turns a legacy scalar into a singleton sequence for consumers that still need to read unmigrated content'), which addresses old content under new consumers — a state the plan itself eliminates by migrating all content in 010 — while the actual post-010 window needs the opposite shim (canonical records read by legacy-expecting consumers). 020's claim that 'old content may still exist during the transition' contradicts 010's full migration, so the dual-format working state the first deliverable should establish is not reconstructable.",
            "evidence": "010 execution plan normalization sentence vs 010 R2; 020 execution plan: 'The compatibility normalization remains active here because old content may still exist during the transition.'"
          },
          {
            "description": "Strength: apart from that window, the decided design is reconstructable — component responsibilities (each child opens with an ownership statement), data flow (canonical `authors` sequence -> normalization -> post/feed/archive consumers -> generated output), dependency states, Q-gated undecided items, and the evidence-gated cutover boundary.",
            "evidence": "Main plan: 'The compatibility reader belongs to the transition, not the final contract; no child may remove it before the cutover child records both content and generated-output evidence.'"
          }
        ]
      },
      "durable_context_preservation": {
        "grade": "partial",
        "occurrences": [
          {
            "description": "Drop: approved outcome AUTHOR-5 ('Every intermediate revision builds and publishes valid output') never appears as a stated requirement or checklist item; its substance survives only as scattered per-child build checks that assert publishability, not author-correct output, at the post-source-migration state.",
            "evidence": "Main file requirements checklist holds only R1–R5 (schema, migration, rendering, helper, cutover); task_tree requirement_count 5 confirms no intermediate-validity requirement."
          },
          {
            "description": "Strength: everything else the conversation established is preserved with sources — fixture facts tied to file paths, the proposed `authors` record shape, transitional legacy-read compatibility, the content-scan plus generated-output retirement gate, the existing-documentation boundary, the dependency chain, Draft status, and the three open questions (identifier fields, archive presentation, post-cutover rejection behavior).",
            "evidence": "Research sections cite content/posts/first.md, _includes/layouts/post.njk, content/feed.xml.njk, _includes/postslist.njk, scripts/new-post.js, placeholder test files, and package.json; Q1–Q3 are restated in the children that own them."
          }
        ]
      },
      "findability": {
        "grade": "complete",
        "occurrences": [
          {
            "description": "Strength: numbered R1–R5 and Q1–Q3 are cross-referenced across files (010 carries R1/R2/R4 and Q1; 020 carries R3 and Q2; 030 carries R5 and Q3), and 'Parent Task' / 'Depends On' lines sit at the top of each child, so outcome ownership, dependency boundaries, unresolved questions, and the decisive evidence ('The decisive check is a recorded pair...') are locatable without reading whole sections.",
            "evidence": "030 header block: 'Depends On: 010-source-and-authoring.md, 020-public-rendering.md'."
          },
          {
            "description": "Minor friction only: design rationale inside each 'Execution plan' is carried in dense multi-clause paragraphs, though the surrounding labeled sections keep it locatable.",
            "evidence": "Main plan paragraph beginning 'The proposed design uses a canonical `authors` sequence...'"
          }
        ]
      },
      "section_appropriateness": {
        "grade": "complete",
        "occurrences": [
          {
            "description": "Strength: current-state facts with file pointers sit in 'Research and supporting facts'; compatibility constraints sit in the requirements checklists (R5 and 020's transitional bullet); unresolved items sit in 'Unresolved requirement questions' and are echoed under decisions; sequencing and direction sit in the ordered 'Execution plan' lists; rationale sits with the decisions it governs.",
            "evidence": "030: 'A source scan alone is insufficient: generated output must be inspected through the real Eleventy build before rejection is enabled.'"
          }
        ]
      },
      "plan_justification": {
        "grade": "justified",
        "occurrences": [
          {
            "description": "The plans restate and organize exactly the planning the conversation established — proposed record shape, transitional compatibility, production-build verification across post/home/blog/tag/feed routes, the two-part evidence gate, the documentation boundary, and the dependency chain — and items requiring approval (record fields, archive presentation, post-cutover behavior) are left open rather than asserted as decided.",
            "evidence": "Final response lists the same recorded items and the same three unresolved questions; every file is marked 'Status: Draft' with Q1–Q3 gating approval."
          }
        ]
      },
      "task_kind_fit": {
        "grade": "fits",
        "occurrences": [
          {
            "description": "Acceptance evidence matches the migration's kind: a real production build with assertions over generated post, home, blog, tag, and feed output for rendering; helper tests asserting emitted front matter for the authoring tool; a repository content scan plus generated-output inspection as the retirement gate; and a regression test for rejected legacy input. No inapplicable sections are filled mechanically, and the planning-only acceptance (resolve Q1–Q3 before marking Approved) fits the requested decomposition.",
            "evidence": "030: 'The decisive check is a recorded pair: a repository-wide scan... followed by a fresh `npm run build`...'; 010: 'A test invokes `scripts/new-post.js`... asserts that it writes the canonical key and never writes a new legacy `author` field.'"
          }
        ]
      }
    },
    "summary": "A coherent planning-only decomposition: one coordinating parent plus three implementation children (source/authoring, public rendering, evidence-gated cutover) within the acceptable partition size, matching the reference dependency shape and avoiding every listed fragmentation and overpacking pattern. The files faithfully carry the conversation's decisions, fixture facts with sources, per-outcome verification, open questions, and Draft status, with strong R/Q cross-referencing for findability. The material weakness sits at the migration's core property: the every-intermediate-revision-validity outcome (AUTHOR-5) is never stated as a requirement, and the ordering that migrates all content in 010 before consumers adopt the model in 020 leaves an undesigned working state — canonical front matter read by templates still expecting the legacy scalar — where generated output would lose author data; the described normalization points legacy-to-canonical, the opposite of what that window needs."
  }
}
```
