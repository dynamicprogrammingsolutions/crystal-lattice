# Session — tg06-eleventy-author-migration-decomposition · task-creation-assessment-glm-max-s0 · glm max

- Run: `20260924T193857.151710Z-task-guidance-semantic-tg06-eleventy-author-migration-decomposition-glm-max-s0-a9d6e4da`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `0a1a034114436440…`)
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
  "response": "Task structure created under `tasks/20260920-post-author-migration/` \u2014 a main task plus three subtasks, one per compatibility state. Nothing was implemented; all plans are `Status: Draft` and execution waits.\n\n## What I found\n\n- Legacy model: `author: \"<name>\"` string front matter in both posts (`first.md`, `second.md`).\n- Consumers: `_includes/layouts/post.njk:2` (page) and `content/feed.xml.njk:5` (feed). `scripts/new-post.js:1` emits the legacy form.\n- Archives/tag pages/home/sitemap render no author data (`postslist.njk` is title+URL only) \u2014 verified non-consumers.\n- Both test files are comment-only stubs; no executable generated-output coverage exists, and `node_modules/` isn't installed.\n\n## Structure and approach\n\n- **`000-main.md`** \u2014 requirements, two open requirement questions, verified current-state facts, orchestration plan.\n- **`010-multi-author-model-and-compat.md`** (dual-read state): introduce `authors` + legacy normalization via computed data, move layout and feed templates to the new model, replace the test stubs with real production-build tests (temp output dir; multi-author fixtures built from temp content copies, never the real `content/`). Existing legacy content must render byte-identically.\n- **`020-content-and-tooling-migration.md`**: migrate both posts and the authoring tool; equivalence evidence via the exact-string tests; record the content audit as gate input; document the new form in the same change.\n- **`030-evidence-gate-and-legacy-rejection.md`**: three-part recorded gate (zero legacy keys, green suite, tool emits new form only) must be green *before* enabling build-time rejection, removing the legacy fallback, and adding an integration test proving a legacy fixture fails the real build.\n\nThe user-stated gate is encoded structurally: 030 depends on 010 + 020 and its first checklist item blocks rejection until evidence is recorded.\n\n## Decisions and open questions needing your input\n\n1. **Q1 \u2014 field shape (material, persisted format):** `authors: [\"Ada Example\"]` list of names (recommended) vs. list of objects like `{ name, url }`.\n2. **Q2 \u2014 archive scope:** keep archive/tag pages as verified non-consumers with unchanged output (recommended), or start displaying authors there (new visible behavior, extends 010).\n\nAlso pending your approval: field name `authors`; build-time rejection in `eleventy.config.js`; multi-author page display joined with `\", \"`; README \"Adding posts\" section as the documentation home.\n\n## Acceptance evidence (planned)\n\nGenerated-output tests through the real Eleventy build assert exact author strings across all three states (before/after equivalence), temp-copy multi-author fixtures prove new-form rendering on page and feed, and the rejection is proven by a real build failing on a legacy fixture while real content passes.\n\n## Risks / exclusions\n\nComputed-data visibility on `post.data` inside the feed is a verified-with-real-build risk with a filter fallback; `npm install` must succeed or build evidence is reported as not run; test fixtures stay out of tracked content. Excluded: no new archive author display (pending Q2), no `docs/index.md` or placeholder docs, `docs/development/index.md` left untouched.\n\nAnswer Q1/Q2 (or approve the recommendations) and I'll update the requirements and mark the plans `Approved` \u2014 execution starts only after that.",
  "task_files": {
    "tasks/20260920-post-author-migration/000-main.md": "# Migrate post author metadata to structured multi-author form\n\nMigrate post author metadata from the legacy single-name `author` front-matter\nstring to a structured multi-author form across templates, archives, feeds, and\nthe authoring tool, migrating existing posts safely and rejecting the legacy\nform only after generated-output and content evidence shows nothing still\ndepends on it.\n\nScope note: this task plans and tracks the migration. These files do not\nauthorize execution; every plan below is `Draft` and execution waits on\nexplicit approval plus resolution of the requirement questions.\n\n## Requirements checklist\n\n- [ ] Posts support a structured multi-author field as the supported content\n      model; a post can declare multiple named authors. (Field shape pending\n      requirement question Q1.)\n- [ ] Every consumer of post author metadata \u2014 post page template, feed,\n      archive/tag surfaces, and the authoring tool \u2014 reads only the new model\n      in the final state. (Archive display scope pending requirement\n      question Q2.)\n- [ ] At every executed state of the migration, the production build succeeds\n      and generated output for existing content (post pages, blog archive, tag\n      pages, feed, sitemap) remains correct; existing posts end up migrated to\n      the new form.\n- [ ] The legacy single-name `author` form is rejected by the production build\n      only after generated-output and content evidence shows that no source\n      content, template, tooling, or generated output still depends on it.\n- [ ] Maintained documentation describes the new author form and, in the same\n      reviewed change that enables it, the rejection of the legacy form.\n\n## Requirement questions\n\n- **Q1 \u2014 Field shape (material; persisted content format).** Options:\n  - **A (recommended):** `authors` is a list of author name strings, e.g.\n    `authors: [\"Ada Example\", \"Grace Example\"]`. Smallest change that satisfies\n    \"structured multi-author\"; rendering semantics stay name-text-only.\n  - **B:** `authors` is a list of objects, e.g. `authors: [{ name: \"...\", url:\n    \"...\" }]`. Leaves room for per-author metadata (links, ids) but introduces\n    fields no current template renders.\n- **Q2 \u2014 Archive display scope.** The blog archive and tag pages currently\n  render only title and URL (`_includes/postslist.njk`) and consume no author\n  data. Does \"archives must move to the new model\" mean:\n  - **A (recommended):** archives are verified as non-consumers and their\n    output stays unchanged; no new author display is added.\n  - **B:** archive/tag pages must start displaying author names from the new\n    model (new visible behavior, extends subtask 010 scope).\n\n## Subtasks\n\n- [ ] tasks/20260920-post-author-migration/010-multi-author-model-and-compat.md\n- [ ] tasks/20260920-post-author-migration/020-content-and-tooling-migration.md\n- [ ] tasks/20260920-post-author-migration/030-evidence-gate-and-legacy-rejection.md\n\n## Supporting facts\n\nCurrent state, verified by inspection (2026-09-20):\n\n- Legacy form: `author: \"<name>\"` string in post front matter.\n  `content/posts/first.md` (`Ada Example`), `content/posts/second.md`\n  (`Grace Example`). These are the only content files.\n- Consumers of author data:\n  - `_includes/layouts/post.njk:2` \u2014 `<p class=\"author\">{{ author }}</p>`.\n  - `content/feed.xml.njk:5` \u2014 simplified Atom-like document; renders\n    `{{ post.data.author }}` inside `<entry><author>`; `layout: false`,\n    permalink `/feed/feed.xml`.\n- Author non-consumers (verified): `_includes/postslist.njk` renders only\n  title + URL and is shared by `content/blog.njk` (archive),\n  `content/index.njk` (home), and `content/tag-pages.njk` (tag pages);\n  `content/sitemap.xml.njk` renders URLs only; `content/posts/posts.json` sets\n  layout/tags only.\n- Authoring tool: `scripts/new-post.js` exports `frontMatter(title, author)`\n  emitting the legacy string form. No npm script invokes it.\n- Tests: `tests/author-output.test.js` and `tests/archive-output.test.js` are\n  comment-only stubs; `npm test` (`node --test tests/*.test.js`) currently\n  passes with no executable coverage. No generated-output coverage exists yet.\n- Dependencies are not installed (`node_modules/` absent, gitignored);\n  build/test evidence requires `npm install` (devDependency\n  `@11ty/eleventy ^3.0.0`). `_site/` is gitignored output.\n- Build config: `eleventy.config.js` \u2014 input `content/`, includes\n  `../_includes`, output `_site`.\n- `docs/development/index.md` notes a missing archive pagination\n  specification \u2014 unrelated to authors; leave unchanged. There is no\n  `docs/index.md` and no existing documentation describes author metadata.\n- Fixture provenance: `UPSTREAM.md` (adapted from Eleventy Base Blog).\n\n## Execution plan\n\nStatus: Draft\n\nThree subtasks in strict order, one per compatibility state. Each ends with\nthe site building green and its evidence recorded, so every executed state is\nindependently acceptable.\n\n1. **010 \u2014 dual-read state.** Introduce the structured `authors` model with a\n   normalization path that maps legacy `author` strings into it, move the post\n   layout and feed templates to read only the new model, and replace the two\n   comment-only test stubs with real generated-output tests run through the\n   production Eleventy build. Existing content stays legacy-form and its\n   generated output must be byte-identical to the pre-change baseline.\n2. **020 \u2014 migrated-content state.** Rewrite both posts' front matter to the\n   new form and update `scripts/new-post.js` to emit it (multiple authors\n   supported). Generated output for the two posts must remain identical;\n   content audit shows zero legacy keys. Document the `authors` front-matter\n   form for content authors in the same change.\n3. **030 \u2014 rejection state.** Gate: content audit (zero legacy keys) plus\n   full green generated-output suite plus tooling emitting only the new form.\n   Only when all three hold, enable build-time rejection of legacy `author`,\n   remove the legacy normalization fallback, add an integration test proving a\n   legacy fixture fails the real build, and document the rejection in the same\n   change.\n\nSequencing rationale: the rejection gate required by the request is encoded as\nsubtask 030's dependency on 010 + 020 and its explicit pre-rejection evidence\nchecklist. Tests from 010 assert exact author strings at the generated-output\nboundary, so they stay valid across the internal migration and provide the\nbefore/after equivalence evidence for the \"nothing breaks\" constraint.\n\nPrerequisites and risks:\n\n- `npm install` must succeed before any build evidence; if it is blocked,\n  report that build evidence is not run rather than claiming it.\n- Computed-data normalization must be visible on `post.data` inside the feed\n  template; verified by the real-build feed test in 010, with a shared filter\n  as the fallback mechanism.\n- Test fixture posts (multi-author cases) must be built in temp copies of the\n  content tree, never added to the real `content/`, so the public site output\n  is not altered by tests.\n- Q1 and Q2 must be resolved before 010 executes; both change requirements,\n  not just implementation.\n\n### Implementation decisions and open questions\n\n- **Open requirement questions:** Q1 (field shape) and Q2 (archive display\n  scope) above. Neither is resolved by this plan; subtasks 010 and 020 depend\n  on Q1, 010 depends on Q2. Recommendation: Q1=A, Q2=A.\n- **Decision (pending approval with the plan):** new field is named `authors`;\n  legacy key is `author`.\n- **Decision:** rejection is enforced at build time by validating post front\n  matter in `eleventy.config.js` (exact Eleventy 3 hook chosen during 030);\n  the authoring tool additionally never emits the legacy form (from 020).\n- **Decision:** during the dual-read state, normalization maps legacy\n  `author` to the new model via Eleventy computed data in\n  `content/posts/posts.json`; a shared filter is the fallback if computed data\n  is not visible on collection items in the feed.\n- **Decision:** multi-author display on post pages joins names with `\", \"`;\n  the feed emits one `<author>` element per author in post order. Affects only\n  posts that opt into multiple authors; existing single-author output is\n  unchanged.\n\n### Documentation\n\n- Follows `docs/development/documentation.md` (read before restructuring).\n- No maintained documentation currently describes author metadata, so subtask\n  010 needs no documentation change (unless Q2 resolves to archive display).\n- Subtask 020 adds a short \"Adding posts\" section to `README.md` documenting\n  the `authors` front-matter form \u2014 placed with the site entry point that\n  content authors use; smallest structure that helps the reader (alternative\n  considered: a new `docs/` page, rejected as unnecessary structure).\n- Subtask 030 updates the same README section, in the same reviewed change\n  that enables rejection, so the \"legacy form is rejected\" claim is true when\n  published. No placeholder pages or `docs/index.md` are created.\n\n### Task checklist\n\n- [ ] Resolve Q1 and Q2 with the requester; update affected requirements.\n- [ ] Execute and complete\n      tasks/20260920-post-author-migration/010-multi-author-model-and-compat.md\n- [ ] Execute and complete\n      tasks/20260920-post-author-migration/020-content-and-tooling-migration.md\n- [ ] Verify 030's pre-rejection evidence gate is fully green before any\n      rejection change lands.\n- [ ] Execute and complete\n      tasks/20260920-post-author-migration/030-evidence-gate-and-legacy-rejection.md\n- [ ] Final review: full `npm test` + production build green; all requirement\n      checkboxes in main and subtasks supported by recorded evidence.\n\n### Requirement verification\n\n- Multi-author model supported \u2192 decisive evidence: production-build test\n  with a multi-author fixture post (temp content copy) asserting all authors\n  render on the post page and in the feed (subtask 010).\n- Consumers moved to the new model \u2192 decisive evidence: source audit shows no\n  template or tool reads the legacy key, and the full generated-output suite\n  passes after the legacy fallback is removed (subtasks 020 + 030).\n- No breakage during transition \u2192 decisive evidence: generated-output tests\n  asserting exact author strings and archive contents pass against unchanged\n  content before the model change, and pass again after each migration step\n  (subtasks 010 and 020).\n- Legacy rejected only after evidence \u2192 decisive evidence: 030's recorded\n  pre-rejection checklist (content audit zero legacy keys; green suite;\n  tool emits new form only) followed by an integration test in which a\n  legacy-form fixture fails the real build while the real content builds\n  cleanly (subtask 030). The gate order itself is a requirement; it is\n  enforced by subtask dependency plus the recorded checklist.\n- Documentation current with behavior \u2192 evidence: README section present in\n  the same changes that introduce the new form (020) and enable rejection\n  (030); verified by inspection of the merged state.\n\n### Additional implementation verification\n\n- Verify computed-data visibility on `post.data` in the feed context via the\n  real build early in 010 (material risk to the normalization approach).\n- Confirm the shared test build helper is exercised by every generated-output\n  test (maintained test infrastructure verified through real consumers).\n- Confirm `node --test` collects all test files and exits cleanly after each\n  subtask; record suite results in the executing subtask.",
    "tasks/20260920-post-author-migration/010-multi-author-model-and-compat.md": "# Introduce structured multi-author model with legacy read compatibility\n\nFirst migration state (dual-read): add the structured `authors` post field,\nnormalize legacy `author` strings into it, move the post layout and feed\ntemplates to read only the new model, and establish real generated-output test\ncoverage. Existing legacy-form content must keep generating identical output.\n\nParent Task: tasks/20260920-post-author-migration/000-main.md\n\n## Requirements checklist\n\n- [ ] Posts accept the structured `authors` field (shape per parent Q1); a\n      post listing multiple authors renders all authors on the post page and\n      in the feed.\n- [ ] Post page and feed templates render author data exclusively through the\n      new model; legacy `author` strings are normalized so the two existing\n      posts render exactly as before the change.\n- [ ] Archive, tag page, home, and sitemap generation remain unchanged during\n      this subtask (author non-consumers per parent Q2 recommendation; if Q2\n      resolves to adding archive display, that display consumes the new model\n      and is covered here instead).\n- [ ] During this state, both legacy-form and new-form content build\n      successfully through the production Eleventy pipeline.\n- [ ] Real generated-output coverage exists at the production-build boundary\n      covering: legacy-form post rendering, new-form single- and\n      multi-author rendering (page + feed), and archive listing.\n\nDo not execute until parent questions Q1 and Q2 are resolved.\n\n## Supporting facts\n\n- Consumers to move: `_includes/layouts/post.njk:2`\n  (`<p class=\"author\">{{ author }}</p>`) and `content/feed.xml.njk:5`\n  (`<author>{{ post.data.author }}</author>`; simplified Atom-like feed,\n  permalink `/feed/feed.xml`).\n- Existing content is legacy-form only: `first.md` \u2192 `Ada Example`,\n  `second.md` \u2192 `Grace Example`.\n- `tests/author-output.test.js` and `tests/archive-output.test.js` are\n  comment-only stubs; there is no executable coverage yet. `npm test` runs\n  `node --test tests/*.test.js`.\n- Dependencies (`@11ty/eleventy ^3.0.0`) are not installed; `node_modules/`\n  and `_site/` are gitignored.\n- Archives/tag pages/home share `_includes/postslist.njk` (title + URL only);\n  sitemap renders URLs only \u2014 no author reads to migrate there, only\n  verification that they stay unchanged.\n\n## Execution plan\n\nStatus: Draft\n\nApproach:\n\n1. Prerequisites: `npm install`; run `npm test` and record the trivial-green\n   baseline.\n2. Make both stub test files real before touching templates. Add a small\n   shared helper under `tests/` that runs the real Eleventy build into a temp\n   output directory (supporting an alternate input dir for fixture content\n   later). Coverage:\n   - `tests/author-output.test.js`: built `first/index.html` contains\n     `<p class=\"author\">Ada Example</p>`; `second/index.html` contains\n     `Grace Example`; built `feed/feed.xml` contains `<author>Ada\n     Example</author>` and `<author>Grace Example</author>`.\n   - `tests/archive-output.test.js`: built `blog/index.html` lists both post\n     titles.\n   Get this suite green against unchanged legacy content \u2014 that is the\n   before/after equivalence baseline.\n3. Add the model: `authors` front matter is accepted on posts (shape per Q1).\n   Add normalization in `content/posts/posts.json` via `eleventyComputed`:\n   when the post declares `authors`, use it; otherwise map legacy `author`\n   (string) to a one-element list. If the real-build feed test shows computed\n   data is not visible on collection items, fall back to a shared filter\n   module used by both templates (keep the normalization logic in one place).\n4. Move templates: `_includes/layouts/post.njk` renders the author list from\n   the new model (single author \u2192 exactly `Ada Example`, no separator\n   artifacts; multiple authors joined `\", \"`); `content/feed.xml.njk` loops\n   authors and emits one `<author>` element per author.\n5. New-form coverage without touching the public site: build a temp copy of\n   the content tree with two added fixture posts \u2014 one new-form single author\n   (must render identically to its legacy-form equivalent) and one new-form\n   multi-author post \u2014 and assert page and feed output. This exercises the\n   real pipeline; no mocks.\n6. Verify: full `npm test` green; production build (`npm run build`) green;\n   baseline tests still assert the legacy-era exact strings unchanged;\n   archive/sitemap outputs unchanged. Record results.\n\nBoundaries: all decisive evidence comes from real Eleventy build output.\nTemp-fixture builds never write into the repo `content/` or `_site/`.\n\n### Implementation decisions and open questions\n\n- Open (parent, blocking): Q1 field shape, Q2 archive display scope.\n- Local: normalization mechanism (computed data first, filter fallback);\n  multi-author page join `\", \"`; feed emits one `<author>` per author in post\n  order; test fixture posts live only in temp copies.\n\n### Documentation\n\n- No maintained documentation describes author metadata, so no documentation\n  change is required in this state unless Q2 resolves to archive display (then\n  document the archive behavior where archive behavior is documented \u2014 none\n  currently exists, so README-level notes would apply).\n- `docs/development/index.md`'s archive pagination note is unrelated; do not\n  touch it.\n\n### Task checklist\n\n- [ ] `npm install`; record baseline `npm test` result.\n- [ ] Implement shared build helper + real tests in\n      `tests/author-output.test.js` and `tests/archive-output.test.js`; green\n      against unchanged content.\n- [ ] Add `authors` model with legacy normalization (computed data; filter\n      fallback if needed).\n- [ ] Move `_includes/layouts/post.njk` and `content/feed.xml.njk` to the new\n      model.\n- [ ] Add temp-fixture build coverage for new-form single- and multi-author\n      posts (page + feed).\n- [ ] Full suite + production build green; archive/sitemap unchanged;\n      record results and update requirement checkboxes.\n\n### Requirement verification\n\n- New model supported / multi-author rendering \u2192 decisive: real-build test\n  with multi-author fixture asserting all authors on page + feed.\n- Legacy compatibility / no breakage \u2192 decisive: baseline tests asserting\n  exact strings pass against legacy content before the change and again after\n  template migration.\n- Templates read only the new model \u2192 supporting: source inspection of both\n  templates (no `author` reads) plus the passing equivalence suite.\n- Archives unchanged \u2192 decisive: archive test + unchanged sitemap output via\n  build inspection.\n\n### Additional implementation verification\n\n- Feed visibility of normalized data on collection items \u2014 resolved by the\n  feed test; if it fails, apply the filter fallback and re-verify.\n- Confirm temp-fixture builds and tests never modify tracked files.",
    "tasks/20260920-post-author-migration/020-content-and-tooling-migration.md": "# Migrate existing posts and authoring tool to the new author model\n\nSecond migration state: move all source content and the authoring tool to the\nstructured `authors` form while legacy is still accepted, with generated\noutput for the existing posts unchanged, and document the new authoring form\nfor content authors.\n\nParent Task: tasks/20260920-post-author-migration/000-main.md\nDepends On: tasks/20260920-post-author-migration/010-multi-author-model-and-compat.md\n\n## Requirements checklist\n\n- [ ] All source posts declare authors with the new `authors` form (shape per\n      parent Q1); no post front matter carries the legacy `author` key.\n- [ ] `scripts/new-post.js` emits the new form and supports multiple authors;\n      its behavior is unit-tested.\n- [ ] Generated output for the two migrated posts is unchanged after\n      migration (equivalence evidence at the production-build boundary).\n- [ ] Maintained documentation describes the `authors` front-matter form for\n      content authors, updated in the same reviewed change that migrates the\n      content.\n\n## Supporting facts\n\n- Only two posts exist: `content/posts/first.md` (`Ada Example`),\n  `content/posts/second.md` (`Grace Example`).\n- `scripts/new-post.js` exports `frontMatter(title, author)` returning\n  legacy-form front matter; nothing invokes it from `package.json` scripts.\n- After subtask 010, the generated-output suite (author + archive tests plus\n  temp-fixture coverage) exists and is green; legacy content still builds via\n  normalization.\n- The content audit performed here (zero legacy `author` keys in `content/`)\n  is a required input to subtask 030's rejection gate \u2014 record it, do not\n  just observe it.\n\n## Execution plan\n\nStatus: Draft\n\nApproach:\n\n1. Migrate `content/posts/first.md` and `content/posts/second.md` to the new\n   `authors` form (each becomes a one-element list per Q1 shape). No other\n   front-matter changes.\n2. Update `scripts/new-post.js`: `frontMatter(title, authors)` accepts an\n   ordered list of author names and emits the new form with correct YAML\n   quoting; keep it dependency-free. Unit test: single author, multiple\n   authors, and emitted front matter matches the form documented for content\n   authors.\n3. Equivalence evidence: run the full generated-output suite \u2014 the exact\n   author strings asserted by the 010 baseline tests must pass unchanged\n   after the content migration, proving no output regression.\n4. Documentation (same change): add a short \"Adding posts\" section to\n   `README.md` documenting the `authors` front-matter field with an example.\n   At this state legacy `author` is still accepted, so the section describes\n   the new form as the supported way to author posts without claiming legacy\n   is rejected.\n5. Content audit: confirm `content/` contains no legacy `author` keys\n   (search for the singular key) and record the result \u2014 this is gate\n   evidence for 030.\n6. Verify: full `npm test` green; production build green; record results.\n\n### Implementation decisions and open questions\n\n- Open (parent): Q1 field shape determines the emitted front matter in both\n  content and the tool.\n- Local: tool signature takes an ordered author-name list; documentation home\n  is a README section per the parent's documentation decision.\n\n### Documentation\n\n- README gains the \"Adding posts\" section in the same change as the content\n  migration, per `docs/development/documentation.md` (claims describe current\n  behavior; legacy is still accepted at this state, so the section must not\n  claim it is rejected).\n\n### Task checklist\n\n- [ ] Migrate both posts' front matter to the new form.\n- [ ] Update `scripts/new-post.js` for the new form (multi-author); add unit\n      tests.\n- [ ] Run generated-output suite; confirm exact-string equivalence.\n- [ ] Add README \"Adding posts\" section documenting `authors`.\n- [ ] Run content audit; record zero legacy keys as gate evidence for 030.\n- [ ] Full suite + production build green; update requirement checkboxes.\n\n### Requirement verification\n\n- Content migrated \u2192 decisive: content audit shows zero legacy `author` keys\n  in `content/posts/` (recorded).\n- Tool emits new form \u2192 decisive: unit tests covering single and multiple\n  authors against the documented form.\n- Output equivalence \u2192 decisive: exact-string generated-output tests pass\n  unchanged post-migration.\n- Documentation current \u2192 decisive: README section present in the same change\n  (inspection of the merged state).\n\n### Additional implementation verification\n\n- Confirm the audit search covers all of `content/`, not just `posts/`, so\n  the 030 gate evidence is complete.",
    "tasks/20260920-post-author-migration/030-evidence-gate-and-legacy-rejection.md": "# Evidence gate, legacy rejection, and compatibility cleanup\n\nFinal migration state: verify nothing still depends on the legacy single-name\n`author` form, then reject it at build time, remove the legacy read path, and\ndocument the rejection \u2014 in that order, with the gate evidence recorded\nbefore any rejection change lands.\n\nParent Task: tasks/20260920-post-author-migration/000-main.md\nDepends On: tasks/20260920-post-author-migration/010-multi-author-model-and-compat.md\nDepends On: tasks/20260920-post-author-migration/020-content-and-tooling-migration.md\n\n## Requirements checklist\n\n- [ ] Pre-rejection evidence is recorded and fully green before any rejection\n      change: (a) content audit shows zero legacy `author` keys in `content/`\n      (from 020), (b) the full generated-output suite passes rendering from\n      the new model, (c) the authoring tool emits only the new form.\n- [ ] Only after that evidence: the production build fails when a post's\n      front matter carries the legacy `author` key, with a clear error\n      message.\n- [ ] The legacy normalization/fallback read path is removed in the same\n      change as rejection; templates and the posts data file read only the\n      new model.\n- [ ] After rejection lands, the full generated-output suite and archive\n      tests still pass, and an integration test proves a legacy-form fixture\n      fails the real build while the real content builds cleanly.\n- [ ] Documentation states the legacy form is rejected, updated in the same\n      reviewed change that enables rejection.\n\n## Supporting facts\n\n- The rejection gate (\"legacy may be rejected only after generated-output and\n  content evidence\") is a requirement from the original request, not a\n  preference. Gate inputs: 020's recorded content audit, the 010-generated\n  generated-output suite, and the 020 tooling tests.\n- After 020, legacy support exists only as the normalization fallback added\n  in 010 (`content/posts/posts.json` computed data or the shared filter) plus\n  its acceptance in front matter.\n- Rejection and fallback removal must land together: rejecting the form while\n  keeping the fallback would leave dead code that still reads `author`.\n- `npm test` runs `node --test tests/*.test.js`; the build helper from 010\n  supports building an alternate input directory into a temp output \u2014 reused\n  for the legacy-failure integration test.\n\n## Execution plan\n\nStatus: Draft\n\nApproach:\n\n1. Gate check (blocking, recorded in this file before proceeding):\n   - Content audit: search all of `content/` for legacy `author` keys \u2014\n     expect zero. (Reuse/verify the 020 audit; re-run it here rather than\n     trusting a stale record.)\n   - Run the full generated-output suite \u2014 expect green, rendering from the\n     new model.\n   - Confirm the authoring tool emits only the new form (020 unit tests).\n   If any check fails, stop and report; do not enable rejection.\n2. Implement build-time rejection: validate post front matter in\n   `eleventy.config.js` (choose the Eleventy 3 hook during execution \u2014\n   e.g., a data preprocessor or collection/data check) so that any post\n   carrying the legacy `author` key fails the build with a clear message.\n   Export the validation predicate so it is unit-testable without bypassing\n   the wired behavior.\n3. Integration test at the real boundary: using the build helper, build a\n   temp copy of the real site plus one legacy-form fixture post and assert\n   the build fails with the rejection error; assert the real content (no\n   legacy keys) still builds cleanly.\n4. Remove the legacy normalization fallback (010's legacy branch), leaving\n   the new model as the only read path. Re-run the full suite \u2014 the\n   exact-string baseline tests must still pass, proving generated output is\n   carried by the new model alone.\n5. Documentation (same change): update the README \"Adding posts\" section to\n   state that the legacy `author` form is no longer accepted and the build\n   fails on it \u2014 true in the same reviewed change.\n6. Final verification: full `npm test` green; `npm run build` green; record\n   all results and complete the parent requirement checkboxes.\n\nBoundaries: rejection and failure-path evidence come from the real Eleventy\nbuild (temp-copy fixture), not from invoking the validator in isolation.\n\n### Implementation decisions and open questions\n\n- Local: exact Eleventy 3 hook for build-time validation (chosen during\n  execution; exported predicate keeps it unit-testable); rejection triggers\n  on presence of the legacy `author` key in post front matter regardless of\n  value.\n- No open requirement questions remain from the parent at this stage (Q1/Q2\n  resolved before 010 executed).\n\n### Documentation\n\n- README \"Adding posts\" section is updated in the same reviewed change that\n  enables rejection, per `docs/development/documentation.md` (claim becomes\n  true in the same change that publishes it).\n\n### Task checklist\n\n- [ ] Run and record the three-part gate check (audit, suite, tooling) before\n      any rejection change.\n- [ ] Implement build-time rejection in `eleventy.config.js` with exported,\n      unit-testable validation predicate.\n- [ ] Add legacy-failure integration test (temp copy + fixture post; real\n      build must fail; real content must pass).\n- [ ] Remove legacy normalization fallback; re-run full suite.\n- [ ] Update README to state legacy rejection (same change).\n- [ ] Full suite + production build green; update requirement checkboxes in\n      this file and the parent.\n\n### Requirement verification\n\n- Gate evidence before rejection \u2192 decisive: the recorded gate checklist in\n  this file, completed and green before step 2 begins.\n- Build rejects legacy form \u2192 decisive: integration test where a legacy\n  fixture fails the real build and real content passes.\n- Legacy read path removed \u2192 decisive: full generated-output suite green\n  after removal, plus source audit showing no template/data-file reads of the\n  legacy key.\n- Documentation current \u2192 decisive: README rejection statement present in the\n  same change enabling rejection (inspection of the merged state).\n\n### Additional implementation verification\n\n- Confirm the rejection error names the offending file/content so a content\n  author can fix it without reading build internals.\n- Confirm the rejection check cannot be skipped by the front-matter parser\n  treating `author` as data in an unexpected shape (e.g., list value) \u2014\n  presence of the key is what triggers rejection."
  },
  "task_tree": {
    "all_dependencies_resolve": true,
    "all_parent_links_resolve": true,
    "coordinating_files": [
      "tasks/20260920-post-author-migration/000-main.md"
    ],
    "dependencies": [],
    "files": [
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": null,
        "path": "tasks/20260920-post-author-migration/000-main.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Migrate post author metadata to structured multi-author form"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260920-post-author-migration/000-main.md",
        "path": "tasks/20260920-post-author-migration/010-multi-author-model-and-compat.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Introduce structured multi-author model with legacy read compatibility"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260920-post-author-migration/000-main.md",
        "path": "tasks/20260920-post-author-migration/020-content-and-tooling-migration.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 4,
        "title": "Migrate existing posts and authoring tool to the new author model"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260920-post-author-migration/000-main.md",
        "path": "tasks/20260920-post-author-migration/030-evidence-gate-and-legacy-rejection.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Evidence gate, legacy rejection, and compatibility cleanup"
      }
    ],
    "implementation_task_count": 3,
    "parent_links": [
      {
        "child": "tasks/20260920-post-author-migration/010-multi-author-model-and-compat.md",
        "parent": "tasks/20260920-post-author-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260920-post-author-migration/020-content-and-tooling-migration.md",
        "parent": "tasks/20260920-post-author-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260920-post-author-migration/030-evidence-gate-and-legacy-rejection.md",
        "parent": "tasks/20260920-post-author-migration/000-main.md",
        "resolves": true
      }
    ],
    "phase_named_files": [],
    "task_directory_count": 1,
    "task_file_count": 4
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
    "semantic_deliverable_count": 3,
    "actual_task_count": 3,
    "deliverable_mappings": [
      {
        "deliverable_id": "AUTHOR-D1",
        "task_paths": ["tasks/20260920-post-author-migration/010-multi-author-model-and-compat.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "010 introduces the structured authors model with legacy normalization while legacy content still builds with byte-identical output; combining normalization with generated-surface adoption is the target's explicitly acceptable alternative and the dual-format working state is preserved."
      },
      {
        "deliverable_id": "AUTHOR-D2",
        "task_paths": ["tasks/20260920-post-author-migration/010-multi-author-model-and-compat.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "In the same dual-read state the post layout and feed read only the normalized model, archives/tag/home/sitemap are verified non-consumers with unchanged output, and real-build tests prove page and feed rendering for legacy, new single-, and multi-author content."
      },
      {
        "deliverable_id": "AUTHOR-D3",
        "task_paths": ["tasks/20260920-post-author-migration/020-content-and-tooling-migration.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Content rewrite, authoring-tool migration with unit tests, generated-output equivalence re-run, README documentation, and the recorded zero-legacy-key audit land together as one producer-state change while legacy is still accepted, matching the target's single content+tooling deliverable."
      },
      {
        "deliverable_id": "AUTHOR-D4",
        "task_paths": ["tasks/20260920-post-author-migration/030-evidence-gate-and-legacy-rejection.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "The recorded three-part gate (content audit, green generated-output suite, tool emits new form only) blocks rejection, which lands together with fallback removal, a real-build legacy-failure integration test, and same-change documentation; dependencies on 010+020 encode the requested gate order."
      }
    ],
    "mergeable_groups": [],
    "unmatched_tasks": [],
    "overpacked_tasks": [],
    "valid_layer_boundaries": [],
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
    "partition_quality_score": 95,
    "handoff_quality_score": 92,
    "summary": "Three implementation tasks (000-main excluded as a coordinating parent with no separately assigned implementation work) partition the migration into exactly the coherent deliverables the target allows: 010 merges dual-format normalization and generated-surface adoption into one dual-read state under the target's sanctioned alternative, 020 is the content+tooling producer state, and 030 is evidence-gated legacy retirement — matching acceptable partition size 3 with ratio 3/3 = 1.0. Every task ends in a building, publishable revision (AUTHOR-5), each carries its own verification embedded rather than as horizontal test/doc/cleanup children, and no task is a phase-only fragment or an overpacked atomic change (content, tooling, and rejection stay separated across 020/030, preserving the compatibility window). The important crossing — real front matter through normalization and the production Eleventy build into pages, feeds, and archives at every migration state — is decisively owned by real-build tests in 010 and re-proven at each later state (equivalence suite in 020, real-build legacy-failure integration test in 030); isolated tool/validator unit tests are explicitly supplementary, not the crossing proof. Dependencies (020←010, 030←010+020) are all necessary and leave no broken intermediate; Q1/Q2 remain open with the requester, matching the target's approval-gated open questions. Minor handoff gap: rollback assumptions per state are implicit in the compatibility-state design rather than explicitly recorded."
  }
}
