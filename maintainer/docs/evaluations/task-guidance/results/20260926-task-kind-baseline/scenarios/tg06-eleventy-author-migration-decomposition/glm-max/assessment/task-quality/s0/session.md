# Session — tg06-eleventy-author-migration-decomposition · task-quality-assessment-glm-max-s0 · glm max

- Run: `20260926T120534.911715Z-task-guidance-quality-tg06-eleventy-author-migration-decomposition-glm-max-s0-f90e3543`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `7563d834b71eb825…`)
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
  "response": "Task structure created \u2014 `tasks/20260926-author-metadata-migration/` is the only change; nothing was implemented.\n\n## Plan summary (all plans `Status: Draft`)\n\n**Outcome** \u2014 Post author metadata moves from the single-name `author` front matter field to a structured multi-author model; all consumers migrate; existing posts migrate value-preserving; the legacy form ends rejected.\n\n**Decomposition** \u2014 Three sequential stages, each an independently verifiable compatibility state, declared with dependencies (`010 \u2192 020 \u2192 030`):\n\n1. **010-structured-authors-adoption** \u2014 new model supported by post layout, feed, and `scripts/new-post.js`, with legacy still accepted and rendered byte-identically. Also builds the generated-output evidence: the existing tests are placeholder comments only (`tests/author-output.test.js` claims coverage that doesn't exist), so the evidence gate must be built, not cited.\n2. **020-content-migration** \u2014 `first.md`/`second.md` converted (\"Ada Example\", \"Grace Example\" preserved), with the 010 build-output assertions passing through the structured path as the output-unchanged proof.\n3. **030-legacy-rejection** \u2014 gate re-verified **fresh** (content scan + consumer inventory + passing build) before any removal, then legacy compatibility removed and rejected with a hard build failure plus authoring-tool rejection.\n\n**Material decisions / open questions**\n- **Q1 (blocks execution)** \u2014 structured schema shape: recommendation is `authors:` list of objects with required `name`; alternative is a list of strings. Needs your approval before execution.\n- Recommendations surfaced for approval: multi-author display joined with \", \" in the existing `<p class=\"author\">`; one `<author>` element per author in the feed; hard build failure (no warning fallback) for legacy rejection.\n\n**Acceptance evidence** \u2014 production-build assertions on real `_site` output (post pages, feed, archives) owned by 010 and maintained downstream; legacy rejection proven by a real build failing on a sandboxed legacy fixture; the 030 gate re-verified at execution start.\n\n**Documentation audience** \u2014 content authors; smallest structure (README authoring section), updated within each stage's change.\n\n**Risks** \u2014 uninstalled `node_modules` (execution needs `npm install` first); archive author *display* excluded as new scope (archives render no author today).\n\nExecution waits: approve Q1 and the plans (or adjust them), and tell me to start with 010.",
  "task_files": {
    "tasks/20260926-author-metadata-migration/000-main.md": "# Post author metadata migration to structured multi-author model\n\nMigrate post author metadata from the single-name `author` front matter field\nto a structured multi-author model across templates, archives, feeds, and the\nauthoring tool, without breaking existing content or generated pages during\nthe transition. The legacy single-name form may be rejected only after\ngenerated-output and content evidence show that nothing still depends on it.\n\nPlanning only: no implementation has been requested or performed yet.\n\n## Requirements checklist\n\n- [ ] R1 \u2014 Post author metadata supports a structured multi-author form as the\n      target representation (exact schema per the approved answer to Q1 below).\n- [ ] R2 \u2014 During the transition, existing content and generated pages keep\n      working: posts still in the legacy form build and render with unchanged\n      author output (post pages and feed).\n- [ ] R3 \u2014 All author consumers move to the new model: post page layout\n      (`_includes/layouts/post.njk`), feed (`content/feed.xml.njk`), the\n      authoring tool (`scripts/new-post.js`), and the archive surfaces\n      (`content/blog.njk`, `content/tag-pages.njk`, `_includes/postslist.njk`,\n      `content/index.njk`), which today render no author and therefore must\n      keep building correctly with multi-author data and not depend on legacy.\n- [ ] R4 \u2014 Both existing posts (`content/posts/first.md`,\n      `content/posts/second.md`) are migrated to the new model with author\n      values preserved exactly (\"Ada Example\", \"Grace Example\").\n- [ ] R5 \u2014 The legacy single-name form is rejected only after generated-output\n      and content evidence show that nothing still depends on it; that gate is\n      verified fresh immediately before rejection, not assumed from earlier\n      stages.\n- [ ] R6 \u2014 End state: the legacy form is rejected (build fails on legacy\n      content; authoring tool rejects legacy input) and no dual acceptance\n      remains.\n- [ ] R7 \u2014 Maintained documentation reflects the supported author model at\n      each stage (current behavior only; no unmarked target-only claims),\n      per the repository documentation policy.\n\n## Subtasks\n\n- [ ] tasks/20260926-author-metadata-migration/010-structured-authors-adoption.md \u2014 introduce the structured model with legacy still accepted; build the generated-output evidence later stages depend on\n- [ ] tasks/20260926-author-metadata-migration/020-content-migration.md \u2014 migrate existing post front matter; prove output unchanged\n- [ ] tasks/20260926-author-metadata-migration/030-legacy-rejection.md \u2014 evidence-gated removal and rejection of the legacy form\n\nRequirement \u2192 owning subtask:\n\n| Requirement | Owner |\n| --- | --- |\n| R1 (new model supported) | 010 |\n| R2 (transition non-breaking) | 010, preserved through 020 |\n| R3 (all consumers moved) | 010 (templates, feed, tool, archives) |\n| R4 (existing posts migrated) | 020 |\n| R5 (evidence gate before rejection) | 030, using evidence built by 010 and content evidence from 020 |\n| R6 (legacy rejected, end state) | 030 |\n| R7 (documentation current per stage) | 010, 020, 030 (each within its own stage) |\n\n## Requirement questions\n\n- Q1 (blocks execution of 010 and everything downstream) \u2014 What is the exact\n  schema of the structured multi-author form? Recommendation: an `authors`\n  list of objects with a required `name` field\n  (`authors:\\n  - name: Ada Example`), extensible later (e.g. `url`).\n  Alternative: a list of plain strings. This choice shapes content files,\n  templates, the authoring tool, and the migration of R4, so it needs\n  approval before execution starts.\n\n## Supporting facts\n\n- Current model: `author` as a single quoted string in post front matter \u2014\n  `content/posts/first.md:3` (\"Ada Example\"), `content/posts/second.md:3`\n  (\"Grace Example\"). `content/posts/posts.json` sets the post layout and\n  `tags: [\"posts\"]` for the collection.\n- A repo-wide search for `author` finds every consumer:\n  `_includes/layouts/post.njk:2` (`<p class=\"author\">{{ author }}</p>`),\n  `content/feed.xml.njk:5` (`<entry><author>{{ post.data.author }}</author>`\n  per post), `scripts/new-post.js:1-2` (emits `author: \"...\"` front matter),\n  and the two content files above. No other consumer exists.\n- Archive surfaces (`_includes/postslist.njk`, `content/blog.njk`,\n  `content/tag-pages.njk`, `content/index.njk`) render only titles and URLs,\n  so \"moving archives to the new model\" is a compatibility requirement, not a\n  display change. Adding author display to archives would be new scope and is\n  not planned (recommendation).\n- `tests/author-output.test.js` and `tests/archive-output.test.js` contain\n  placeholder comments only; the author-output comment claims generated-output\n  coverage that does not exist. There is currently no automated evidence of\n  any kind, so the R5 gate must be built as part of this migration, not cited\n  as pre-existing coverage.\n- Build and test entry points: `npm run build` (Eleventy 3, input `content/`,\n  includes `_includes/`, output `_site/`; feed `/feed/feed.xml`, archive\n  `/blog/`, tag pages `/tags/<slug>/`) and `npm test`\n  (`node --test tests/*.test.js`).\n- `node_modules` is absent in this workspace; `npm install` is required before\n  any build or test verification during execution.\n- No `tasks/` directory existed prior to this planning; it is created by this\n  handoff. Nothing outside `tasks/` has been changed by planning.\n\n## Execution plan\n\nStatus: Draft\n\nApproach \u2014 three sequential compatibility states, each independently\nverifiable, with a hard evidence gate before the last:\n\n1. Stage 1 (subtask 010): introduce the structured multi-author model and make\n   every consumer able to render it, while legacy `author` continues to work\n   unchanged. This stage also builds the generated-output evidence (tests\n   asserting real `_site` output) that stages 2 and 3 rely on.\n2. Stage 2 (subtask 020): convert both existing posts to the structured form\n   and prove, through the same production-build assertions, that generated\n   output is unchanged. Completing this stage is the content half of the R5\n   gate.\n3. Stage 3 (subtask 030): re-verify the gate fresh (content scan + consumer\n   inventory + passing build), then remove legacy compatibility and reject the\n   legacy form in the build and the authoring tool, updating tests and\n   documentation to the structured-only end state.\n\nOrdering is strict: 010 \u2192 020 \u2192 030, declared as dependencies in the subtask\nfiles. Every permitted execution order is safe because 020 requires 010's\nmodel and evidence, and 030 requires both.\n\nDesign common to the stages: normalize author data once at the data layer so\ntemplates consume a single normalized form (see 010 for the design), and keep\nthe canonical rendered form for a single author byte-identical to today's\nlegacy output. That equivalence is what makes the migration provably safe and\nthe R5 gate decidable by comparison rather than judgment.\n\nDecisive checks (one per product connection, through the real production\npath):\n\n- Author rendering on post pages and feed: production-build output assertions\n  (`npm run build`, then assert on `_site` HTML/XML), owned by 010 and\n  maintained by 020 and 030.\n- Legacy rejection: a production build fails on a legacy fixture (sandboxed\n  copy, no permanent legacy content), owned by 030.\n\nRisks:\n\n- The placeholder test comments could be mistaken for existing coverage; the\n  gate must be built from real build-output assertions.\n- Dependencies are not installed in this workspace; verification requires\n  `npm install` first.\n- Any unapproved schema choice (Q1) invalidates the plans below; execution\n  waits until Q1 is resolved.\n\n### Implementation decisions and open questions\n\n- Q1 (requirement question, unresolved \u2014 see above): structured schema shape.\n  Recommendation: `authors` list of objects with required `name`.\n- Multi-author display on a post page: join names with \", \" inside the\n  existing `<p class=\"author\">` element (recommendation; user-visible, so\n  surfaced for approval with the plan).\n- Feed representation: one `<author>` element per author, preserving the\n  current element shape (recommendation).\n- Legacy rejection mechanism: hard build failure with an actionable error,\n  and rejection in the authoring tool \u2014 not a silent fallback or warning\n  (recommendation; user-visible authoring behavior).\n- Normalization mechanism (directory computed data vs. per-template logic):\n  implementation choice made in 010; templates must not each re-implement it.\n\n### Documentation\n\n- Audience: content authors (front matter format, authoring tool usage).\n- Smallest structure: a concise authoring/front-matter section in the nearest\n  maintained doc (README.md is today's only site-level doc), updated within\n  each subtask's reviewed change \u2014 dual acceptance in 010, structured-only in\n  030. `docs/development/documentation.md` guidance applies to any new or\n  moved pages. No placeholder pages.\n\n### Task checklist\n\n- [ ] tasks/20260926-author-metadata-migration/010-structured-authors-adoption.md\n- [ ] tasks/20260926-author-metadata-migration/020-content-migration.md (Depends On 010)\n- [ ] tasks/20260926-author-metadata-migration/030-legacy-rejection.md (Depends On 010, 020)\n\n### Requirement verification\n\n- R1, R2, R3 \u2014 production build plus build-output assertions added in 010:\n  legacy posts render the current author line and feed element unchanged; a\n  structured multi-author fixture renders the approved form on the post page\n  and feed through the real build; archives still build. The authoring tool\n  is covered by a component test plus a real build of its output.\n- R4 \u2014 content scan (no legacy `author:` in `content/`) plus the same\n  build-output assertions passing after 020 now exercise the structured path,\n  proving output equivalence.\n- R5 \u2014 fresh gate evidence recorded at the start of 030: content scan, consumer\n  inventory, and a passing production build with the full test suite.\n- R6 \u2014 production build fails on a legacy fixture; authoring tool rejects\n  legacy input (integration through the real build, not a mocked validator).\n- R7 \u2014 maintained documentation reviewed and updated within each stage;\n  checked for stale claims about the legacy form.",
    "tasks/20260926-author-metadata-migration/010-structured-authors-adoption.md": "# Adopt structured multi-author model with legacy compatibility\n\nIntroduce the structured multi-author author model (schema per approved Q1 in\nthe parent task) in the post layout, feed, and authoring tool while the legacy\nsingle-name `author` field continues to work unchanged, and build the\ngenerated-output evidence that the later migration stages depend on.\n\nParent Task: tasks/20260926-author-metadata-migration/000-main.md\n\nDepends On: none (first stage)\n\n## Requirements checklist\n\n- [ ] Post front matter accepts the approved structured multi-author schema\n      alongside the legacy `author` field (dual acceptance on the same post\n      data cascade).\n- [ ] `_includes/layouts/post.njk` renders authors from the new model; posts\n      still using the legacy field render byte-identical to current output\n      (`<p class=\"author\">Ada Example</p>` for `content/posts/first.md`).\n- [ ] `content/feed.xml.njk` renders authors from the new model; legacy\n      posts' feed output is unchanged (`<author>Ada Example</author>`).\n- [ ] `scripts/new-post.js` emits the structured model, and its generated\n      front matter builds and renders correctly.\n- [ ] Blog archive, tag pages, and home page build correctly with posts in\n      either form; no author display is added to archives (out of scope).\n- [ ] Production-build generated-output tests assert author rendering for\n      both legacy and structured posts on post pages and feed, replacing the\n      placeholder comments in `tests/author-output.test.js`; the archive\n      build check is also real (`tests/archive-output.test.js`).\n- [ ] Documentation describes the supported author front matter (dual\n      acceptance) as current behavior.\n\n## Supporting facts\n\n- Legacy consumers to keep working while dual acceptance exists:\n  `_includes/layouts/post.njk:2` renders `{{ author }}`;\n  `content/feed.xml.njk:5` renders `{{ post.data.author }}` per entry.\n- `scripts/new-post.js` currently exports `frontMatter(title, author)`\n  returning `---\\ntitle: ${title}\\nauthor: \"${author}\"\\n---\\n`. It is a\n  standalone authoring tool with no other caller in the repo.\n- `content/posts/posts.json` sets `layout: layouts/post.njk` and\n  `tags: [\"posts\"]` for all posts \u2014 the natural place for directory-wide\n  computed data normalization.\n- `tests/author-output.test.js` contains only a comment; no assertions exist.\n  `npm test` runs `node --test tests/*.test.js`.\n- Current generated output to preserve (verified by reading templates and\n  content; will be captured before changes during execution):\n  post page `<p class=\"author\">Ada Example</p>`; feed\n  `<feed><entry><author>Ada Example</author></entry><entry><author>Grace Example</author></entry></feed>`.\n- `node_modules` is absent; run `npm install` before building or testing.\n\n## Execution plan\n\nStatus: Draft\n\nDesign: normalize author data once, at the data layer, so templates consume a\nsingle form and no template re-implements compatibility.\n\n- Normalization: directory-level computed data on `content/posts/` (via\n  `posts.json`, e.g. `eleventyComputed`) derives a normalized `authors` list\n  (objects per approved Q1) from either the new `authors` field or the legacy\n  `author` field. The exact mechanism is an implementation choice as long as\n  it runs in the real build path; templates read only the normalized list.\n- Canonical rendering: author names joined with \", \" in the existing\n  `<p class=\"author\">` element; a single author therefore renders the same\n  string as the legacy form did, which keeps output stable for the stage-2\n  migration proof. Feed emits one `<author>` element per author, preserving\n  the current element shape.\n- Authoring tool: `scripts/new-post.js` emits the structured form (signature\n  updated to take the structured authors input). Component test covers its\n  output; a real build of that front matter is the decisive check.\n- Evidence: production-build integration tests (`npm run build`, then\n  assertions on `_site` output) cover: legacy posts unchanged on post page\n  and feed; a structured multi-author post rendered correctly on post page\n  and feed; archive and tag pages building. The multi-author case runs\n  through a temporary post in a sandboxed copy of the content/config (no\n  permanent content changes, no test-only build shortcuts); harness details\n  are an implementation choice.\n- Documentation: smallest update describing the supported author front matter\n  (both forms during dual acceptance) as current behavior.\n\nExecution tasks:\n\n1. Run `npm install`; capture current `_site` output (build before changes)\n   as the equivalence baseline for author rendering.\n2. Implement the dual-acceptance normalization in the posts data cascade.\n3. Update `_includes/layouts/post.njk` and `content/feed.xml.njk` to the\n   normalized model.\n4. Update `scripts/new-post.js` to emit the structured form.\n5. Add build-output tests (legacy equivalence + structured rendering +\n   archive build), replacing placeholder comments.\n6. Update documentation to describe dual acceptance as current behavior.\n7. Run the production build and the full test suite; resolve fallout.\n\n### Implementation decisions and open questions\n\n- Q1 (parent schema question) must be approved before execution; the\n  recommendation is an `authors` list of objects with required `name`.\n- Multi-author display: names joined with \", \" inside the existing\n  `<p class=\"author\">` (recommendation; user-visible \u2014 surfaced for approval).\n- Feed: one `<author>` element per author, preserving the current element\n  shape (recommendation).\n- Normalization mechanism: directory computed data in `content/posts/posts.json`\n  (recommended); alternatives acceptable if they keep normalization in one\n  place in the real build path.\n\n### Documentation\n\n- Audience: content authors. Update the nearest maintained doc (README.md\n  today) with a concise authoring/front-matter section describing the\n  supported author forms. Follow `docs/development/documentation.md` before\n  creating or moving any doc page; do not create placeholder structure. If\n  README grows beyond a brief section, move authoring guidance to a dedicated\n  doc page in the same change.\n\n### Task checklist\n\n- [ ] Baseline: `npm install`, production build, capture current author output\n- [ ] Dual-acceptance normalization in the posts data cascade\n- [ ] Post layout and feed templates moved to the normalized model\n- [ ] `scripts/new-post.js` emits the structured form\n- [ ] Build-output tests: legacy equivalence, structured rendering, archives\n- [ ] Documentation updated (dual acceptance)\n- [ ] Full build + test run clean\n\n### Requirement verification\n\n- Dual acceptance, legacy equivalence, and structured rendering (parent R1,\n  R2, R3): production build plus `node --test` assertions on real `_site`\n  files \u2014 legacy post pages keep `<p class=\"author\">Ada Example</p>` /\n  `Grace Example`, feed keeps one `<author>` element per legacy post, and a\n  structured multi-author fixture renders the approved form through the real\n  build. A mock of the data cascade would not be decisive; the check is the\n  actual Eleventy output.\n- Authoring tool: component test of `frontMatter` output plus a real build of\n  front matter it generates.\n- Archives continue to build: archive-output assertions on `_site/blog/` and\n  a tag page.\n\n### Additional implementation verification\n\n- Diff `_site` output before and after this stage against the baseline from\n  task 1, confirming no drift beyond author markup for posts that opt into\n  the new model.",
    "tasks/20260926-author-metadata-migration/020-content-migration.md": "# Migrate existing post content to structured authors\n\nConvert the existing posts' front matter from the legacy single-name `author`\nfield to the structured multi-author model, preserving values exactly and\nproving through the production build that generated output is unchanged.\n\nParent Task: tasks/20260926-author-metadata-migration/000-main.md\n\nDepends On: tasks/20260926-author-metadata-migration/010-structured-authors-adoption.md\n(the structured model must exist and the build-output evidence must be in\nplace before content switches to it)\n\n## Requirements checklist\n\n- [ ] `content/posts/first.md` and `content/posts/second.md` use only the\n      structured model; the legacy `author` field is removed from them.\n- [ ] Author values are preserved exactly and in order: \"Ada Example\" and\n      \"Grace Example\".\n- [ ] Generated output after migration is unchanged versus the pre-migration\n      output: post page author lines and feed author elements stay identical\n      (proven by the production-build assertions from 010, now exercising the\n      structured path).\n- [ ] No content file retains or introduces the legacy field after migration\n      (repo-wide content scan clean).\n- [ ] Documentation contains no stale claim that existing posts still use the\n      legacy form (no behavioral change is introduced by this stage).\n\n## Supporting facts\n\n- Current front matter to migrate:\n  - `content/posts/first.md`: `author: \"Ada Example\"`\n  - `content/posts/second.md`: `author: \"Grace Example\"`\n- Conversion is mechanical and value-preserving (1:1): the legacy string\n  becomes a single structured entry carrying the same name, in file order.\n- Both posts are single-author, so their canonical rendered output must be\n  byte-identical before and after migration \u2014 this is exactly what the 010\n  equivalence assertions are designed to prove.\n- If an unexpected front matter shape is found during migration (missing\n  author, non-string value), report it instead of inventing a default; no\n  fallback behavior is specified.\n\n## Execution plan\n\nStatus: Draft\n\n- Convert both content files to the approved structured schema (Q1), removing\n  the legacy field from each.\n- Run the production build and the full test suite. The 010 build-output\n  assertions (which pin the exact legacy-era author strings) must pass after\n  migration \u2014 passing through the structured path is the output-unchanged\n  proof for this stage.\n- Run a content scan confirming no `author:` legacy field remains under\n  `content/`.\n- Documentation: no behavior change in this stage (dual acceptance is still\n  the supported behavior); verify no maintained doc claims existing posts use\n  the legacy form, and leave the rest unchanged.\n\nExecution tasks:\n\n1. Migrate `content/posts/first.md` to the structured form.\n2. Migrate `content/posts/second.md` to the structured form.\n3. Production build + full test suite (equivalence assertions pass).\n4. Content scan for residual legacy fields.\n5. Check maintained docs for stale claims.\n\n### Implementation decisions and open questions\n\n- None new. The schema is fixed by the approved answer to parent Q1. The\n  conversion is mechanical; any anomaly in existing front matter is reported,\n  not silently normalized.\n\n### Documentation\n\n- No user-facing change is made here; supported behavior (dual acceptance)\n  is unchanged. Only a stale-claims check is in scope for this stage.\n\n### Task checklist\n\n- [ ] `content/posts/first.md` migrated, value preserved\n- [ ] `content/posts/second.md` migrated, value preserved\n- [ ] Production build + tests clean (output unchanged)\n- [ ] Content scan shows no legacy `author:` field\n- [ ] Docs checked for stale legacy-content claims\n\n### Requirement verification\n\n- Values preserved and legacy removed (parent R4): front-matter inspection of\n  both files plus the content scan.\n- Output unchanged (parent R2, R4): the production-build assertions from 010\n  pin the exact author strings; they pass after migration while reading the\n  structured field \u2014 real build output, not a mocked cascade.\n- Gate contribution (parent R5): the clean content scan and passing build\n  from this stage are the content half of the 030 gate; 030 re-verifies it\n  fresh rather than assuming it.",
    "tasks/20260926-author-metadata-migration/030-legacy-rejection.md": "# Reject legacy single-author field after evidence gate\n\nAfter re-verifying that nothing still depends on the legacy single-name\n`author` field, remove the compatibility path and make the legacy form an\nerror in the build and the authoring tool, ending the migration in a\nstructured-only state.\n\nParent Task: tasks/20260926-author-metadata-migration/000-main.md\n\nDepends On:\n- tasks/20260926-author-metadata-migration/010-structured-authors-adoption.md\n- tasks/20260926-author-metadata-migration/020-content-migration.md\n\n## Requirements checklist\n\n- [ ] Gate (precondition, verified fresh at the start of execution, not\n      assumed from earlier stages): content scan shows no legacy `author`\n      field; the consumer inventory shows every author consumer (post layout,\n      feed, authoring tool) operating on the structured model and archives\n      free of legacy dependence; the latest production build and full test\n      suite pass. Execution stops if any check fails.\n- [ ] Legacy compatibility normalization (deriving structured data from\n      `author`) is removed from the data cascade and templates.\n- [ ] Content using the legacy field fails the production build with a clear,\n      actionable error; no silent fallback or warning-only behavior.\n- [ ] `scripts/new-post.js` rejects legacy single-name input and emits only\n      the structured form.\n- [ ] Existing generated output remains unchanged (the 010-era author\n      assertions still pass, now structured-only).\n- [ ] Tests updated: legacy-equivalence assertions replaced by structured-only\n      assertions plus a rejection assertion exercised through a real build.\n- [ ] Documentation updated to the structured-only end state; the legacy form\n      is documented as unsupported current behavior.\n\n## Supporting facts\n\n- The gate constraint comes from the original request: the legacy form may be\n  rejected only after generated-output and content evidence show that nothing\n  still depends on it. Both halves of that evidence exist only after 010\n  (generated-output assertions) and 020 (content migrated, scan clean).\n- After 020, no content uses `author`; after 010, templates and the tooling\n  read the normalized structured form. The remaining legacy dependence is the\n  compatibility normalization itself \u2014 which is exactly what this stage\n  removes.\n- The rejection must be proven through the real production build (a legacy\n  fixture in a sandboxed copy fails `npm run build`), not through a mocked\n  validator, per the repository testing guidance.\n- A warning-only acceptance would leave a silent dependency path and would\n  not satisfy \"rejected\"; the recommendation is a hard build failure. This is\n  user-visible authoring behavior and is surfaced for approval with the plan.\n\n## Execution plan\n\nStatus: Draft\n\n- Gate check first: rerun the content scan, the consumer inventory, and the\n  full build/test cycle. Record the evidence before touching compatibility\n  code. If the gate fails, stop and report rather than forcing the removal.\n- Remove the legacy normalization path from the posts data cascade; templates\n  keep reading the normalized structured form only.\n- Add build-time validation that fails the build with an actionable error\n  when a post carries the legacy `author` field (mechanism: an Eleventy\n  data-validation point in the real build path; exact mechanism is an\n  implementation choice).\n- Update `scripts/new-post.js` to accept only the structured form and reject\n  legacy input.\n- Update tests: structured-only rendering assertions plus the rejection test\n  (sandboxed copy with a legacy fixture; the build must fail). Archive checks\n  unchanged.\n- Update documentation: structured form only; legacy explicitly unsupported\n  as current behavior.\n- Full production build and test suite; confirm existing generated output is\n  unchanged for the migrated content.\n\nExecution tasks:\n\n1. Fresh gate verification (content scan + consumer inventory + build/tests);\n   record evidence.\n2. Remove legacy compatibility normalization.\n3. Add legacy-field build validation with an actionable error.\n4. Restrict `scripts/new-post.js` to the structured form.\n5. Update tests (structured-only + rejection through real build).\n6. Update documentation to structured-only.\n7. Full build + test run; confirm output stability.\n\n### Implementation decisions and open questions\n\n- Rejection mechanism: hard build failure for legacy content plus rejection\n  in the authoring tool (recommendation; user-visible \u2014 surfaced for\n  approval with this plan). A warning-based fallback is not planned because\n  it would keep a silent legacy path alive.\n- The rejection test uses a temporary legacy fixture in a sandboxed copy; no\n  permanent legacy content is added to `content/`.\n\n### Documentation\n\n- Update the authoring/front-matter documentation to structured-only: the\n  legacy `author` field is listed as unsupported. Audience: content authors.\n  Keep the smallest structure established in stage 1; follow\n  `docs/development/documentation.md` for any page moves.\n\n### Task checklist\n\n- [ ] Gate evidence recorded (scan + inventory + passing build/tests)\n- [ ] Legacy normalization removed from the data cascade\n- [ ] Build validation rejects the legacy field with actionable error\n- [ ] `scripts/new-post.js` rejects legacy input\n- [ ] Tests: structured-only assertions + real-build rejection test\n- [ ] Documentation updated to structured-only\n- [ ] Full build + test run clean; output unchanged for existing content\n\n### Requirement verification\n\n- Gate (parent R5): fresh evidence recorded in this stage before any removal \u2014\n  content scan clean, consumer inventory, passing production build and tests.\n- Rejection end state (parent R6): a production build fails on a sandboxed\n  legacy fixture (real build path, not a mocked validator), and the authoring\n  tool rejects legacy input.\n- Output stability (parent R2/R4): the pinned author assertions from 010 pass\n  in structured-only form after the compatibility removal.\n- Documentation (parent R7): maintained docs reviewed to describe the\n  structured-only supported behavior.\n\n### Additional implementation verification\n\n- Confirm no template, data file, or script reference to the legacy field\n  remains (repo-wide search), complementing the build-level rejection."
  },
  "task_tree": {
    "all_dependencies_resolve": true,
    "all_parent_links_resolve": true,
    "coordinating_files": [
      "tasks/20260926-author-metadata-migration/000-main.md"
    ],
    "dependencies": [],
    "files": [
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": null,
        "path": "tasks/20260926-author-metadata-migration/000-main.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 7,
        "title": "Post author metadata migration to structured multi-author model"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260926-author-metadata-migration/000-main.md",
        "path": "tasks/20260926-author-metadata-migration/010-structured-authors-adoption.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 7,
        "title": "Adopt structured multi-author model with legacy compatibility"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260926-author-metadata-migration/000-main.md",
        "path": "tasks/20260926-author-metadata-migration/020-content-migration.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Migrate existing post content to structured authors"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260926-author-metadata-migration/000-main.md",
        "path": "tasks/20260926-author-metadata-migration/030-legacy-rejection.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 7,
        "title": "Reject legacy single-author field after evidence gate"
      }
    ],
    "implementation_task_count": 3,
    "parent_links": [
      {
        "child": "tasks/20260926-author-metadata-migration/010-structured-authors-adoption.md",
        "parent": "tasks/20260926-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260926-author-metadata-migration/020-content-migration.md",
        "parent": "tasks/20260926-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260926-author-metadata-migration/030-legacy-rejection.md",
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

{
  "schema_version": 1,
  "scenario_id": "tg06-eleventy-author-migration-decomposition",
  "assessment": {
    "task_kind": "development",
    "dimensions": {
      "plan_design_completeness": {
        "grade": "complete",
        "occurrences": [
          {
            "description": "Normalization design is concrete and located: mechanism, data flow, and responsibility boundary are stated, not just a work step",
            "evidence": "010 plan: \"directory-level computed data on `content/posts/` (via `posts.json`, e.g. `eleventyComputed`) derives a normalized `authors` list ... templates read only the normalized list\""
          },
          {
            "description": "Compatibility states are defined by a decidable equivalence invariant, which is what makes the gate checkable rather than judgment-based",
            "evidence": "010 plan: \"a single author therefore renders the same string as the legacy form did, which keeps output stable for the stage-2 migration proof ... the R5 gate decidable by comparison rather than judgment\" (000-main)"
          },
          {
            "description": "Material decisions are surfaced with alternatives and approval status rather than silently baked in",
            "evidence": "000-main Q1 \"Recommendation: an `authors` list of objects with a required `name` field ... Alternative: a list of plain strings\"; 030: \"hard build failure ... A warning-based fallback is not planned because it would keep a silent legacy path alive\""
          },
          {
            "description": "Minor gap: rollback/recoverability assumptions per stage are not stated; the only recoverability element is 010's pre-change baseline capture",
            "evidence": "010 execution task 1: \"capture current `_site` output (build before changes) as the equivalence baseline\" — no statement of what reverting a failed stage means"
          },
          {
            "description": "Minor gap: the every-intermediate-revision build/publish invariant is enforced at stage boundaries rather than stated as a per-revision invariant",
            "evidence": "Stage plans end with \"Run the production build and the full test suite; resolve fallout\"; no explicit statement covering intermediate revisions within a stage"
          }
        ]
      },
      "durable_context_preservation": {
        "grade": "complete",
        "occurrences": [
          {
            "description": "Everything the response established reappears compressed in the files: placeholder-test fact, value-preservation targets, archive-scope exclusion, environment risk, and the execution-wait state",
            "evidence": "000-main supporting facts: \"tests/author-output.test.js ... contains placeholder comments only\"; \"node_modules is absent\"; R4 pins \"Ada Example\", \"Grace Example\"; R3/000-main: \"Adding author display to archives would be new scope and is not planned\"; Q1: \"blocks execution of 010 and everything downstream\""
          },
          {
            "description": "Verified facts carry their sources (file:line), and honest verification status is kept where reading is not yet proof",
            "evidence": "000-main: \"_includes/layouts/post.njk:2\", \"content/feed.xml.njk:5\", \"scripts/new-post.js:1-2\"; 010: \"verified by reading templates and content; will be captured before changes during execution\""
          }
        ]
      },
      "findability": {
        "grade": "complete",
        "occurrences": [
          {
            "description": "Outcome→owner and dependency placement lets a reviewer find responsibility and ordering without reading sections",
            "evidence": "000-main \"Requirement → owning subtask\" table (\"R4 (existing posts migrated) | 020\"); each subtask opens with \"Parent Task:\" / \"Depends On:\" lines"
          },
          {
            "description": "Open questions and decisive evidence live in dedicated, labeled sections rather than buried in prose",
            "evidence": "000-main \"## Requirement questions\" isolates Q1; \"### Decisive checks (one per product connection, through the real production path)\"; per-subtask \"### Requirement verification\""
          }
        ]
      },
      "section_appropriateness": {
        "grade": "complete",
        "occurrences": [
          {
            "description": "Constraint rationale sits in supporting facts; direction sits in execution plans; unresolved items sit in question sections",
            "evidence": "030 supporting facts: \"A warning-only acceptance would leave a silent dependency path and would not satisfy 'rejected'\"; 000-main Execution plan holds the three-state direction; Q1 held under \"Requirement questions\" and echoed under \"Implementation decisions and open questions\""
          }
        ]
      },
      "plan_justification": {
        "grade": "justified",
        "occurrences": [
          {
            "description": "Plans restate the planning the response reports (three compatibility stages, Q1, the three recommendations) and ground design detail in investigated repo facts",
            "evidence": "010 supporting facts cite `content/posts/posts.json` (layout/tags) and the exact `frontMatter(title, author)` template string; every undecided point is labeled \"recommendation\" or \"implementation choice\" instead of asserted as settled"
          }
        ]
      },
      "task_kind_fit": {
        "grade": "fits",
        "occurrences": [
          {
            "description": "Acceptance evidence is test-shaped for a code/build migration and routed through the production path; no horizontal test/doc/cleanup task files were invented",
            "evidence": "010: \"production-build integration tests (`npm run build`, then assertions on `_site` output)\"; 030: \"a production build fails on a sandboxed legacy fixture (real build path, not a mocked validator)\"; Documentation kept as a per-stage section matching R7's scope"
          }
        ]
      }
    },
    "summary": "The four-file structure (coordinator 000-main plus three staged subtasks, 010→020→030 with declared dependencies) is a compatible-working-state partition within the acceptable size range: 010 deliberately combines normalization with generated-surface adoption under an explicit dual-acceptance window (an approved alternative), content migration gets its own owned stage only because content can switch after the model and evidence exist, and retirement is evidence-gated with a fresh re-verification — avoiding both the named fragmentation patterns (no per-template or per-test-type tasks; tests and docs live inside stages) and the overpacking pattern (no single atomic change). The execution plans carry the design, not just steps: normalization mechanism and location, the byte-identical canonical-rendering invariant that makes the gate decidable, decisions with alternatives surfaced for approval (Q1 schema, display join, feed shape, hard rejection), and per-requirement evidence through the real Eleventy build with mocks explicitly rejected as non-decisive. The response's durable material — placeholder-test finding, value-preservation targets, archive-scope exclusion, environment risk, and the Q1 execution-wait state — is fully compressed into the files with file:line sources. Residual gaps are minor: rollback assumptions per stage are unstated beyond 010's baseline capture, and the every-intermediate-revision build invariant is compressed to stage boundaries. Sections are used where a continuing agent looks for them, and the acceptance evidence matches the development kind (production-build assertions, real-build rejection test, component test for the authoring tool)."
  }
}
