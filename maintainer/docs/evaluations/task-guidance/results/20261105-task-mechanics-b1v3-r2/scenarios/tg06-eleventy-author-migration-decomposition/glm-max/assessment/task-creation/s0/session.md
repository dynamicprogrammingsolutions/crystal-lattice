# Session — tg06-eleventy-author-migration-decomposition · task-creation-assessment-glm-max-s0 · glm max

- Run: `20261029T191225.531130Z-task-guidance-semantic-tg06-eleventy-author-migration-decomposition-glm-max-s0-998d0fc0`
- Model: glm-5.3-flash (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-c440c4f661a7.md) — captured (original SHA-256 `178703ec345ed5ba…`)
- Config: [glm-assessor-max](../../../../../../shared/configs/glm-assessor-max.json)
- Activity: 3 messages · 0 tool calls · 0 tool results
- Usage: 0 input · 0 cached · 0 output · provider cost $0.0000000

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
  "plan_target": {
    "required_content": [
      {
        "content": "The normalized internal author representation both the legacy single-author form and the structured one-or-more-author form map into.",
        "derived_from": [
          "AUTHOR-1"
        ],
        "id": "PLAN-1"
      },
      {
        "content": "The rendering equivalence rules: how single-author behavior renders equivalently and what the approved multi-author behavior is, across pages, archives, feeds, and metadata.",
        "derived_from": [
          "AUTHOR-2"
        ],
        "id": "PLAN-2"
      },
      {
        "content": "The content and authoring-tool migration approach that moves safely to the structured form.",
        "derived_from": [
          "AUTHOR-3"
        ],
        "id": "PLAN-3"
      },
      {
        "content": "The retirement condition for the legacy form: what must be true before it is retired.",
        "derived_from": [
          "AUTHOR-4"
        ],
        "id": "PLAN-4"
      },
      {
        "content": "How the constraint that every intermediate revision builds and publishes valid output shapes the phase boundaries.",
        "derived_from": [
          "AUTHOR-5"
        ],
        "id": "PLAN-5"
      },
      {
        "content": "The phase order \u2014 normalization, rendering, content and tooling, retirement \u2014 with the compatibility constraint explicit.",
        "id": "PLAN-6"
      }
    ]
  },
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
  "response": "Planning complete. Task structure created under `tasks/20261029-post-author-migration/` \u2014 no implementation performed; only the `tasks/` directory is new in git.\n\n## What I found (verified by inspection)\n\nThe complete legacy dependency surface is small: two posts with `author: \"Name\"` front matter, the post layout (`_includes/layouts/post.njk:2`), the feed (`content/feed.xml.njk:5`), and the authoring tool `scripts/new-post.js`. Archives, home, tag pages, and sitemap render no author data at all. Both existing test files are comment-only stubs \u2014 the suite passes with zero real coverage, and `node_modules` isn't installed.\n\n## Task structure\n\n- **`000-main.md`** \u2014 parent requirements (R1\u2013R6), the material decision list, verified facts, and the requirement\u2192child verification map.\n- **`010-introduce-multi-author-model.md`** \u2014 structured form behind dual acceptance: one shared normalization point feeds templates and tooling; real-build tests pin both forms; full-output before/after comparison proves nothing changed. Compatibility state after: both forms render.\n- **`020-migrate-existing-posts.md`** \u2014 content-only migration with byte-identical production-build parity (hash comparison of every generated file) plus a legacy-key content scan; evidence recorded as the gate input. State after: all content on the new form, legacy still tolerated.\n- **`030-retire-legacy-author.md`** \u2014 explicitly gated: reviews the recorded parity/scan/tooling evidence *before* enabling strict rejection in the shared normalization point, replaces the temporary dual-acceptance test, finalizes docs.\n\nEach subtask is an independently buildable compatibility state, which is why content migration and legacy rejection are separate children rather than folded into the model work \u2014 folding them would destroy the evidence chain proving legacy still rendered identically before its removal.\n\n## Decisions needing your approval before execution (all in the parent plan)\n\n1. **D1 \u2014 data shape:** `authors` as a list of name strings vs. objects (`{name, url}`). Recommendation: plain strings.\n2. **D2 \u2014 multi-author rendering:** post page joins names with `\", \"`; feed emits one `<author>` per author; single-author output stays byte-identical.\n3. **D3 \u2014 archives:** they display no author data today; recommendation is to keep them author-agnostic (parity-only), not add display.\n4. **D4 \u2014 both forms on one post during transition:** `authors` wins, no error, until rejection is enabled.\n\n## Risks and exclusions\n\nUnknown *external* consumers of the legacy form can't be proven absent from inside this repo \u2014 the gate covers in-repo content and generated output only, and the actionable rejection error is the mitigation. Documentation changes are limited to a \"Post authors\" README section (added in 010, rewritten in 030); no new doc structure.\n\nAll plans are `Status: Draft`. Execution waits for your approval (and answers to D1\u2013D4, or confirmation of the recommendations).",
  "task_files": {
    "tasks/20261029-post-author-migration/000-main.md": "# Migrate post author metadata to structured multi-author form\n\nMove the site from a single-name `author` front matter field to a structured\nmulti-author form across templates, feed, and authoring tooling; migrate\nexisting posts safely; retire the legacy form only after generated-output and\ncontent evidence show nothing still depends on it. Planning only \u2014 no\nimplementation has been approved yet.\n\n## Requirements checklist\n\n- [ ] R1 \u2014 Posts can declare authors in the structured multi-author form and the\n      production build renders them on post pages and in the feed.\n- [ ] R2 \u2014 Every author-aware surface (post layout template, feed template,\n      `scripts/new-post.js`) consumes the new model through one shared\n      normalization point; no surface reads the legacy field directly.\n- [ ] R3 \u2014 During the transition the legacy single-name form is still accepted\n      and renders exactly as it does today; home, archive, tag pages, and\n      sitemap output are unchanged by the model introduction.\n- [ ] R4 \u2014 All existing post content is migrated to the structured form with\n      production-build output parity proven for every generated file.\n- [ ] R5 \u2014 The legacy form is rejected by the build with an actionable error,\n      and only after recorded generated-output parity plus content-scan\n      evidence show nothing in content or output still depends on it.\n- [ ] R6 \u2014 Maintained documentation describes the currently supported author\n      metadata form at each compatibility state (dual acceptance, then\n      new-form only).\n\n## Requirement questions and decisions\n\nMaterial decisions pending approval (full tradeoffs in the parent execution\nplan below; scope-local choices live in each subtask):\n\n- D1 (requirement \u2014 data shape): structured form shape \u2014 list of author name\n  strings vs list of objects (e.g. `{ name, url }`). Recommendation: list of\n  plain name strings; migration maps `author: \"X\"` to a one-element list.\n- D2 (requirement \u2014 user-visible output): multi-author rendering.\n  Recommendation: post page joins names with `\", \"`; feed emits one `<author>`\n  element per author in front matter order; single-author output stays\n  byte-identical to today.\n- D3 (requirement \u2014 scope boundary): archives and listings currently render no\n  author data at all. Recommendation: keep them author-agnostic (regression\n  parity only); do not add author display.\n- D4 (design \u2014 transition semantics): when a post carries both forms,\n  recommendation: `authors` takes precedence and legacy is ignored (no error)\n  until 030 enables rejection.\n\n## Supporting facts\n\nVerified by inspection during planning:\n\n- Legacy-form usage inventory (the complete author dependency surface):\n  - `content/posts/first.md` (`author: \"Ada Example\"`),\n    `content/posts/second.md` (`author: \"Grace Example\"`) \u2014 the only content\n    using the field.\n  - `_includes/layouts/post.njk:2` \u2014 `<p class=\"author\">{{ author }}</p>`\n    (post pages).\n  - `content/feed.xml.njk:5` \u2014 `<entry><author>{{ post.data.author\n    }}</author></entry>` (feed).\n  - `scripts/new-post.js` \u2014 `frontMatter(title, author)` emits legacy front\n    matter; no in-repo callers.\n  - `tests/author-output.test.js` \u2014 comment-only stub (no real coverage).\n- Author-agnostic surfaces with no author reference (must stay correct through\n  the migration): `_includes/postslist.njk`, `content/blog.njk`,\n  `content/index.njk`, `content/tag-pages.njk`, `content/sitemap.xml.njk`,\n  `content/posts/posts.json`.\n- Build: Eleventy 3, input `content/`, includes `_includes/`, output `_site/`\n  (gitignored). Commands: `npm run build`, `npm test` (`node --test`).\n- `node_modules` is not installed at planning time; `npm install` is required\n  before any build or test run.\n- Baseline verified: `npm test` at HEAD passes trivially (stub files contain\n  no tests) \u2014 `# pass 2 # fail 0`.\n- `docs/development/index.md` contains no author-related specification.\n\n## Subtasks\n\n- [ ] tasks/20261029-post-author-migration/010-introduce-multi-author-model.md\n- [ ] tasks/20261029-post-author-migration/020-migrate-existing-posts.md\n- [ ] tasks/20261029-post-author-migration/030-retire-legacy-author.md\n\n## Execution plan\n\nStatus: Draft\n\nApproach: three sequenced increments, each leaving the site in a coherent,\nindependently buildable compatibility state.\n\n1. **010 \u2014 Introduce the structured model behind dual acceptance.** One shared\n   normalization point feeds the post layout and feed templates; the authoring\n   tool emits the new form; legacy posts keep rendering exactly as today.\n   Real-build integration tests pin both paths, plus a full-output before/after\n   comparison proving the model introduction changed no generated file.\n2. **020 \u2014 Migrate existing post content.** Convert front matter to the\n   structured form and prove byte-identical production output for every\n   generated file (hash comparison before/after) plus a content scan showing no\n   legacy keys remain. The recorded evidence becomes the 030 gate input.\n3. **030 \u2014 Retire the legacy form (evidence-gated).** Review the recorded\n   evidence, then enable strict rejection in the shared normalization point,\n   replace temporary dual-acceptance coverage with rejection coverage, and\n   finalize documentation.\n\nCompatibility states: after 010 both forms render; after 020 all content uses\nthe new form while legacy is still tolerated; after 030 the legacy form is\nrejected. Execution order 010 \u2192 020 \u2192 030 is required: 020's evidence is only\nmeaningful against 010's dual-read model, and 030's gate consumes 020's\nevidence.\n\nVerification strategy: decisive checks run the real Eleventy production build \u2014\nfull-output parity comparisons for no-regression claims, rendered-output\nassertions for the new model, and a build-failure assertion for rejection.\nUnit tests cover only the normalization point and the authoring generator.\n\nRisks:\n\n- Computed-data wiring could interact with pagination/collections \u2014 mitigated\n  by real-build tests covering archive, tag, home, and sitemap output.\n- `scripts/new-post.js` may have external callers \u2014 no in-repo callers;\n  signature change accepted (recorded on 010).\n- Unknown external consumers of the legacy form cannot be proven absent from\n  inside this repository. The gate covers in-repo content and generated output\n  only; the actionable rejection error message is the mitigation. Residual\n  risk accepted unless the user knows of external consumers.\n\n### Implementation decisions and open questions\n\nPending approval (material; answers may adjust subtask plans):\n\n- D1 data shape: recommendation \u2014 `authors` as a list of plain name strings.\n  Extensible later to objects without re-migrating single-name content.\n- D2 rendering: recommendation \u2014 post page: names joined `\", \"`; feed: one\n  `<author>` element per author in front matter order; single-author output\n  byte-identical to today.\n- D3 archives boundary: recommendation \u2014 listings stay author-agnostic; no new\n  author display (they render no author data today).\n- D4 both-forms precedence: recommendation \u2014 `authors` wins, legacy ignored,\n  no error, until 030 enables rejection; 020's content scan guarantees no\n  dual-form posts remain in the repository anyway.\n\nResolved locally (recorded on the owning subtask): rejection enforcement point\n(shared normalization module, 030); `frontMatter` signature change (010);\nnormalization module location and Eleventy wiring mechanism (010).\n\n### Documentation\n\nAudience: content authors. Destination: a short \"Post authors\" section in\n`README.md` \u2014 added in 010 (structured form plus a visible note that the\nlegacy form is still accepted during migration), rewritten in 030 (structured\nform only). No new documentation structure; `docs/development/documentation.md`\nguidance applies to both edits.\n\n### Task checklist\n\n- [ ] tasks/20261029-post-author-migration/010-introduce-multi-author-model.md\n- [ ] tasks/20261029-post-author-migration/020-migrate-existing-posts.md\n- [ ] tasks/20261029-post-author-migration/030-retire-legacy-author.md\n\n### Requirement verification\n\n- R1 \u2192 owned by 010: integration test drives the real Eleventy build on a temp\n  fixture site carrying a multi-author post and asserts the rendered post page\n  (joined names) and feed (one `<author>` per author).\n- R2 \u2192 owned by 010: unit tests on the shared normalization module plus\n  recorded review that templates and tooling reference only the normalized\n  model; `frontMatter` unit test for the authoring tool.\n- R3 \u2192 owned by 010: integration test pinning repo-content build output\n  (`Ada Example` / `Grace Example` on post pages and feed) plus the recorded\n  before/after full-output comparison of every generated file; preserved by\n  020's parity evidence.\n- R4 \u2192 owned by 020: full-output hash comparison of the real production build\n  before/after the content edit, plus the repository content scan.\n- R5 \u2192 owned by 030: recorded gate-evidence review (parity + scan + tooling),\n  then an integration test driving the real build on a legacy-form fixture\n  post asserting failure with the actionable message, and a green real build\n  of repository content.\n- R6 \u2192 owned by 010 and 030: README updated in the same reviewed change as the\n  behavior it describes.\n",
    "tasks/20261029-post-author-migration/010-introduce-multi-author-model.md": "# Introduce structured multi-author model (dual acceptance)\n\nFirst increment of the author migration: add the structured multi-author front\nmatter form and move every author-aware surface (post layout, feed, authoring\ntool) onto a shared normalized model, while legacy single-name posts continue\nto render exactly as today. No existing content is changed in this subtask.\n\nParent Task: tasks/20261029-post-author-migration/000-main.md\n\nDepends On: none\n\n## Requirements checklist\n\n- [ ] Posts can declare authors in the structured form (shape per approved D1),\n      and the production build renders single- and multi-author posts on post\n      pages and in the feed per approved D2.\n- [ ] The post layout template and feed template render from the shared\n      normalized authors model; neither reads the legacy `author` field\n      directly (D4 precedence applies inside the normalization point).\n- [ ] `scripts/new-post.js` emits the structured form.\n- [ ] Legacy single-name posts still render byte-identically: a production\n      build at this state produces the same author output on post pages and\n      feed as before this change, and home, archive, tag, and sitemap output\n      are unchanged.\n- [ ] Automated evidence: integration tests run the real Eleventy build \u2014\n      repository content, plus a temp fixture site carrying both forms\n      including a multi-author post \u2014 and assert rendered post-page and feed\n      output; unit tests cover the normalization point and `frontMatter`.\n- [ ] README documents the structured form and states that the legacy form is\n      still accepted during migration.\n\n## Supporting details\n\n- Legacy usage inventory and build facts live in the parent task\n  (`## Supporting facts`).\n- Mechanism sketch (implementer may adjust): a shared module (suggested\n  `lib/authors.js`, outside the Eleventy input dir) exports a normalizer\n  mapping front matter to an authors list \u2014 `authors` (list of strings) wins;\n  a legacy `author` string becomes a one-element list (D4). Expose it to\n  templates via Eleventy computed data on the posts collection (suggested:\n  `content/posts/posts.11tydata.js` using `eleventyComputed`); templates then\n  render only from the normalized list.\n- The feed currently renders one `<author>` per entry; multi-author renders\n  one `<author>` element per author in front matter order (D2).\n- Integration tests should drive the real Eleventy build (Node API) with\n  distinct output directories for repo content and temp fixture sites, so the\n  production path is exercised without mutating repository content.\n- Temporary legacy-acceptance coverage added here is replaced in 030; the\n  repo-content pins (current author strings) stay valid across all phases.\n- `node_modules` is not installed; run `npm install` before building/testing.\n\n## Execution plan\n\nStatus: Draft\n\nCapture the output baseline before touching anything: build at the current\nstate and hash every file under `_site/` into a temp directory. Then implement\nthe model, templates, and tooling; rebuild and require a byte-identical\ncomparison. Add the two test layers (unit for the model and generator,\nintegration through the real build for rendering), and update the README in\nthe same change.\n\n### Implementation decisions and open questions\n\n- Resolved (local): `scripts/new-post.js` signature changes to accept the\n  authors list \u2014 no in-repo callers, fixture scale; no compatibility shim.\n- Resolved (local): normalization module location and Eleventy wiring are the\n  implementer's choice; the requirement is one shared normalization point\n  consumed by all surfaces, not per-template duplication.\n- Pending approval (material \u2014 parent D1\u2013D4): data shape, multi-author\n  rendering, archives boundary, both-forms precedence. Do not implement until\n  the parent plan is approved.\n\n### Documentation\n\n- Add a short \"Post authors\" section to `README.md` (content-author audience):\n  the structured form plus a visible note that the legacy single-name form is\n  still accepted during migration.\n- Read `docs/development/documentation.md` before adding the section, per root\n  `AGENTS.md`. Smallest change that serves the audience; no new doc structure.\n\n### Task checklist\n\n- [ ] Capture baseline: production build at current state, hash every\n      generated file into a temp (gitignored) location.\n- [ ] Add shared authors normalization module; wire it into the Eleventy data\n      cascade for posts.\n- [ ] Update `_includes/layouts/post.njk` and `content/feed.xml.njk` to render\n      from the normalized authors list.\n- [ ] Update `scripts/new-post.js` to emit the structured form.\n- [ ] Unit tests: normalization (new form, legacy form, both-forms precedence)\n      and `frontMatter` output.\n- [ ] Integration tests: real build of repo content pins current author output\n      (post pages + feed); real build of a temp fixture site with both forms\n      incl. a multi-author post asserts post-page and feed rendering.\n- [ ] README \"Post authors\" section (dual-acceptance wording).\n- [ ] `npm install`; rebuild; require the full-output comparison to be\n      byte-identical to baseline; `npm test` collects all tests and exits\n      cleanly; record results in `## Implementation Notes`.\n\n### Requirement verification\n\n- Structured form end-to-end (R1): integration test through the real Eleventy\n  build on the temp fixture site \u2014 multi-author post renders joined names on\n  the post page and one `<author>` per author in the feed. Real build, real\n  templates; no mocked renderer.\n- Single normalization point (R2): unit tests on the normalization module plus\n  a recorded review that templates and tooling reference only the normalized\n  model (no direct legacy-field reads).\n- Legacy unchanged (R3): integration test pinning repo-content build output\n  (`Ada Example` / `Grace Example` on post pages and feed) plus the recorded\n  before/after full-output comparison of every generated file.\n- Tooling emits the new form (R2): `frontMatter` unit test.\n- Documentation (R6): README section present in the same change.\n\n### Additional implementation verification\n\n- Confirm archive, tag, home, and sitemap files appear unchanged in the\n  before/after comparison \u2014 this is the concrete check that computed-data\n  wiring did not disturb pagination or collections.\n",
    "tasks/20261029-post-author-migration/020-migrate-existing-posts.md": "# Migrate existing posts to the structured form\n\nConvert all existing post front matter from the legacy single-name `author`\nfield to the structured multi-author form, proving production-build output\nparity for every generated file. The build still accepts the legacy form after\nthis subtask (retirement is 030); repository content simply no longer uses it.\n\nParent Task: tasks/20261029-post-author-migration/000-main.md\n\nDepends On: tasks/20261029-post-author-migration/010-introduce-multi-author-model.md\n\n## Requirements checklist\n\n- [ ] Every file in `content/posts/` uses only the structured authors form; no\n      legacy `author:` key remains anywhere in `content/`.\n- [ ] A production build after the migration is byte-identical to the\n      pre-migration build for every generated file (home, archive, tag pages,\n      post pages, feed, sitemap).\n- [ ] The parity comparison result and the content scan are recorded in this\n      task file as the gate evidence later consumed by 030.\n- [ ] The full test suite remains green, including the 010 integration pins\n      against the migrated content.\n\n## Supporting details\n\n- Only two posts exist: `content/posts/first.md` (Ada Example) and\n  `content/posts/second.md` (Grace Example); each becomes a one-element\n  structured list per approved D1.\n- `_site/` is gitignored; keep baseline snapshots in a temp location outside\n  version control and do not commit them.\n- This subtask changes only content files. If output parity fails, stop and\n  investigate the 010 normalization/model path \u2014 do not \"fix\" templates here.\n\n## Execution plan\n\nStatus: Draft\n\n1. Build at the current state and hash every file under `_site/` (baseline\n   snapshot in a temp directory).\n2. Rewrite the two posts' front matter to the structured form (mechanical\n   one-element lists).\n3. Rebuild and compare hashes for every generated file; any diff is a defect\n   in the model/normalization work \u2014 investigate before proceeding.\n4. Scan `content/` for the legacy `author:` key (expected: no matches).\n5. Run `npm test`; confirm the 010 integration pins still pass against the\n   migrated content.\n6. Record the parity result, scan result, and suite status in\n   `## Implementation Notes` \u2014 this is the R5 gate evidence.\n\n### Implementation decisions and open questions\n\n- None new; shape and rendering follow the decisions approved on the parent.\n\n### Documentation\n\n- None: the 010 README wording (\"legacy still accepted during migration\")\n  remains accurate after content migration; it is rewritten in 030.\n\n### Task checklist\n\n- [ ] Baseline build + hash snapshot captured before any content edit.\n- [ ] `content/posts/first.md` and `content/posts/second.md` converted.\n- [ ] Post-migration hash comparison run \u2014 all generated files identical.\n- [ ] Legacy-key content scan run \u2014 no matches in `content/`.\n- [ ] `npm test` green.\n- [ ] Gate evidence recorded in `## Implementation Notes` and referenced by\n      the parent checklist.\n\n### Requirement verification\n\n- Safe content migration (R4): the hash comparison over the real production\n  build output before/after the content edit \u2014 decisive, full-surface, no\n  mocked rendering.\n- Content fully migrated (R4): the repository content scan showing no legacy\n  `author:` keys.\n- Suite green: `npm test` collects and exits cleanly.\n",
    "tasks/20261029-post-author-migration/030-retire-legacy-author.md": "# Retire the legacy author form (evidence-gated)\n\nAfter reviewing the recorded migration evidence, make the build reject the\nlegacy single-name `author` form with an actionable error, replace the\ntemporary dual-acceptance test coverage, and update documentation so the\nstructured form is documented as the only supported author form.\n\nParent Task: tasks/20261029-post-author-migration/000-main.md\n\nDepends On: tasks/20261029-post-author-migration/010-introduce-multi-author-model.md, tasks/20261029-post-author-migration/020-migrate-existing-posts.md\n\n## Requirements checklist\n\n- [ ] Gate evidence is reviewed and recorded in this task file before\n      rejection is enabled: (a) 020 generated-output parity, (b) 020 content\n      scan showing no legacy keys, (c) 010 evidence that\n      `scripts/new-post.js` emits only the new form. If any leg is missing,\n      stop \u2014 rejection must not be enabled.\n- [ ] The production build fails with an actionable error (naming the file and\n      the fix) when a post still uses the legacy `author` form.\n- [ ] Repository content builds cleanly under the strict validation.\n- [ ] Temporary dual-acceptance coverage from 010 is replaced: the legacy-form\n      acceptance test is removed and rejection coverage added (unit +\n      real-build integration); the repo-content pins stay valid.\n- [ ] README updated: the structured form is the only supported author form;\n      dual-acceptance wording removed.\n\n## Supporting details\n\n- Rejection lives in the shared normalization point added in 010, so the\n  production build fails and every consumer of the model shares one rule.\n- Out-of-repo consumers of the legacy form (if any) are not observable here;\n  the gate covers in-repo content and generated output only. The actionable\n  rejection message is the mitigation for unknown external consumers.\n- The 010 repo-content pins (author strings on post pages and feed) remain\n  valid because 020 proved migrated content renders the same output; only the\n  temp-fixture legacy-acceptance test is replaced here.\n\n## Execution plan\n\nStatus: Draft\n\n1. Review and record the gate evidence (a\u2013c) in `## Implementation Notes`\n   before touching validation.\n2. Make the normalization strict: a legacy `author` key present on a post\n   throws with a message naming the file and pointing to the structured form,\n   so the production build fails.\n3. Unit test the strict path; integration test: a temp fixture site with a\n   legacy-form post fails the real build with the expected message, and\n   repository content still builds cleanly.\n4. Remove the 010 temp-fixture legacy-acceptance test; keep all other\n   coverage.\n5. Rewrite the README authoring section (structured form only).\n6. `npm test` and `npm run build` green on repository content; record\n   evidence.\n\n### Implementation decisions and open questions\n\n- Resolved (local): enforcement point is the shared normalization module, not\n  per-template checks \u2014 one rule, and the build fails at the source.\n- Enabling rejection after the gate is itself the approved parent outcome\n  (R5); no further approval is needed beyond the parent plan approval and the\n  recorded gate evidence.\n\n### Documentation\n\n- Rewrite the README \"Post authors\" section in the same change that enables\n  rejection: the legacy form is removed from supported behavior and the\n  migration note is deleted.\n\n### Task checklist\n\n- [ ] Gate evidence (a\u2013c) reviewed and recorded before validation changes.\n- [ ] Strict validation implemented (actionable build error).\n- [ ] Rejection tests added (unit + real-build integration asserting the\n      expected message); repo-content real build still green.\n- [ ] Temporary legacy-acceptance test removed.\n- [ ] README authoring section rewritten (structured form only).\n- [ ] `npm test` green; `npm run build` green on repository content; evidence\n      recorded.\n\n### Requirement verification\n\n- Rejection behavior (R5): integration test drives the real Eleventy build on\n  a temp fixture with a legacy-form post and asserts failure with the\n  actionable message; a real build of repository content succeeds.\n- Gate honored (R5): the recorded review of parity, scan, and tooling evidence\n  in this task file, written before the validation change.\n- Documentation current (R6): README shows the structured form as the only\n  supported form, changed in the same reviewed change as the strict\n  validation.\n"
  },
  "task_tree": {
    "all_dependencies_resolve": true,
    "all_parent_links_resolve": true,
    "coordinating_files": [
      "tasks/20261029-post-author-migration/000-main.md"
    ],
    "dependencies": [],
    "files": [
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": null,
        "path": "tasks/20261029-post-author-migration/000-main.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 6,
        "title": "Migrate post author metadata to structured multi-author form"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20261029-post-author-migration/000-main.md",
        "path": "tasks/20261029-post-author-migration/010-introduce-multi-author-model.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 6,
        "title": "Introduce structured multi-author model (dual acceptance)"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20261029-post-author-migration/000-main.md",
        "path": "tasks/20261029-post-author-migration/020-migrate-existing-posts.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 4,
        "title": "Migrate existing posts to the structured form"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20261029-post-author-migration/000-main.md",
        "path": "tasks/20261029-post-author-migration/030-retire-legacy-author.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Retire the legacy author form (evidence-gated)"
      }
    ],
    "implementation_task_count": 3,
    "parent_links": [
      {
        "child": "tasks/20261029-post-author-migration/010-introduce-multi-author-model.md",
        "parent": "tasks/20261029-post-author-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20261029-post-author-migration/020-migrate-existing-posts.md",
        "parent": "tasks/20261029-post-author-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20261029-post-author-migration/030-retire-legacy-author.md",
        "parent": "tasks/20261029-post-author-migration/000-main.md",
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
        "task_paths": ["tasks/20261029-post-author-migration/010-introduce-multi-author-model.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Shared normalization point with dual acceptance; legacy posts render byte-identically (full-output baseline comparison). Merged with D2 exactly per the target's acceptable alternative: normalization plus generated-surface adoption while a clear dual-format working state remains."
      },
      {
        "deliverable_id": "AUTHOR-D2",
        "task_paths": ["tasks/20261029-post-author-migration/010-introduce-multi-author-model.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Post layout and feed templates render from the normalized model via real-build integration tests (single- and multi-author); archives/home/tag/sitemap verified unchanged by the every-file output comparison, matching the author-agnostic archives decision (D3)."
      },
      {
        "deliverable_id": "AUTHOR-D3",
        "task_paths": ["tasks/20261029-post-author-migration/010-introduce-multi-author-model.md", "tasks/20261029-post-author-migration/020-migrate-existing-posts.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Authoring tool emits the structured form in 010 (owned by the model increment, frontMatter unit-tested, no in-repo callers); content rewrite is 020 with byte-identical production-build parity and a legacy-key scan. The split has explicit ownership and leaves valid states (new posts on the new form; existing content untouched), unlike the target's no-ownership fragmentation example."
      },
      {
        "deliverable_id": "AUTHOR-D4",
        "task_paths": ["tasks/20261029-post-author-migration/030-retire-legacy-author.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Rejection is gated on recorded parity, content-scan, and tooling evidence reviewed before strict validation is enabled; rejection coverage, doc rewrite, and clean repo build land in the same change."
      }
    ],
    "mergeable_groups": [],
    "unmatched_tasks": [],
    "overpacked_tasks": [],
    "valid_layer_boundaries": [
      "tasks/20261029-post-author-migration/010-introduce-multi-author-model.md",
      "tasks/20261029-post-author-migration/020-migrate-existing-posts.md",
      "tasks/20261029-post-author-migration/030-retire-legacy-author.md"
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
    "partition_quality_score": 95,
    "handoff_quality_score": 94,
    "summary": "The three-task set realizes all four target deliverables within the acceptable size range by combining normalization and generated-surface adoption into 010, exactly the alternative the target allows, while keeping content migration (020) and evidence-gated retirement (030) separate so the safe dual-acceptance window and the evidence chain survive; folding 020 or 030 into 010 would recreate the target's overpacking example. All five outcomes are covered: normalization plus documentation (AUTHOR-1), real-build rendering equivalence on pages/feeds with parity on author-agnostic surfaces (AUTHOR-2), tooling and content migration with byte-identical output proof (AUTHOR-3), the evidence gate before rejection (AUTHOR-4), and green build/test states after every increment (AUTHOR-5). Each task is an independently buildable compatibility state with minimal, correct dependencies; evidence is recorded where the work happens (010 and 020) and only reviewed by 030, so there is no re-ownership. The important crossing is decisively owned: real front matter through the shared normalization point into the production Eleventy build is asserted at every state (fixture and repo-content builds in 010, every-file hash parity across pages/archives/feed/sitemap in 020, rejection-failure and clean-build checks in 030), with unit tests only supplementary. Decisions D1-D4 are surfaced for approval, matching the target's open questions rather than adding scope. Minor handoff note: material decisions pending approval block execution until answered, which is appropriate but leaves the plans intentionally unapproved."
  }
}
```
