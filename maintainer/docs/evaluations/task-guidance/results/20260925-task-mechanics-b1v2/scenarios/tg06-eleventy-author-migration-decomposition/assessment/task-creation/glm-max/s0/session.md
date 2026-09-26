# Session — tg06-eleventy-author-migration-decomposition · task-creation-assessment-glm-max-s0 · glm max

- Run: `20260925T204326.568995Z-task-guidance-semantic-tg06-eleventy-author-migration-decomposition-glm-max-s0-d076cb38`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `700e81ec1ca2e187…`)
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
  "response": "Task structure created under `tasks/20260925-author-metadata-migration/` \u2014 no code touched. Here's the plan for review.\n\n**Outcome.** Posts support a structured multi-author `authors` list; byline and feed render all authors through it; `scripts/new-post.js` and both existing posts move to the new form; the legacy `author` string is rejected at build time only after recorded evidence proves nothing depends on it.\n\n**Approach \u2014 three gated stages**, each leaving the build green and public output stable:\n\n1. **010 \u2014 Model + rendering** (`010-multi-author-model.md`): canonical normalizer that is the *only* code reading the raw `author` key; post layout and feed consume only canonical `authors`; legacy form stays accepted and byte-identical. Adds the missing real coverage: production-build integration tests (the two existing test files are comment-only stubs).\n2. **020 \u2014 Producers + evidence gate** (`020-authoring-and-content-migration.md`): migrate the authoring tool and both posts, then record the evidence bundle \u2014 repo-wide scan for legacy readers/usage plus a before/after build diff of post pages and feed.\n3. **030 \u2014 Gated rejection** (`030-legacy-rejection.md`): normalizer throws on legacy input \u2192 build failure; blocked until 020's evidence is recorded, and abandoned with a report if evidence shows a straggler.\n\n**Material decisions needing your approval** (execution waits on these):\n- **Q1 \u2014 `authors` item shape** (data + feed contract): plain name strings vs. objects with required `name`. Recommendation: objects with `name`.\n- **Q2 \u2014 scope**: no new per-author archive/profile pages; \"archives\" is continuity of existing archive output (they render no author data today \u2014 verified).\n- Minor: multi-author byline join format (recommendation: comma-joined), and no new missing-author validation.\n\n**Evidence at the public boundary**: integration tests drive the real Eleventy build and assert generated HTML/XML \u2014 byline and feed entries for multi-author and legacy posts, archive/tag/home/sitemap continuity, build-failure on legacy after rejection, plus a unit test for the tooling contract. One key constraint: multi-author rendering can't be proven with a permanent test post (it would change public output), so the test builds a temporary fixture through the same production config/templates.\n\n**Risks**: the exact Eleventy mechanism for the canonical read path (filter vs. computed data) is left to the executor to avoid a self-reference gotcha in computed data; single-author output byte-equality is the regression anchor throughout.\n\n**One flag**: since planning the work was the requested deliverable, I retained the full plan as `Status: Draft` in `000-main.md` rather than a requirements-only handoff \u2014 say the word if you'd prefer the plan stripped out. Nothing is approved for execution yet: approve Q1/Q2 and the plan, and 010 can start.",
  "task_files": {
    "tasks/20260925-author-metadata-migration/000-main.md": "# Migrate post author metadata to a structured multi-author model\n\nStaged migration of the single-name `author` front-matter field to a structured\nmulti-author model across content, templates, feed, archive outputs, and the\nauthoring tool, ending with a rejection of the legacy form that is gated on\nrecorded generated-output and content evidence.\n\n## Requirements checklist\n\n- [ ] R1 \u2014 Posts accept a structured multi-author metadata form: a single ordered\n  `authors` list where every author resolves to at least a display name (exact\n  item shape per approved decision Q1).\n- [ ] R2 \u2014 Transitional compatibility: until legacy rejection executes, the\n  legacy `author` string stays accepted and posts using it render byte-identically\n  to today; no existing content or generated page breaks at any stage boundary.\n- [ ] R3 \u2014 Author-consuming templates render through the new model: the post\n  layout byline renders every author in declared order; the feed emits one\n  author entry per author. Single-author generated output remains unchanged.\n- [ ] R4 \u2014 Non-author outputs unaffected: home, blog archive, tag pages, and\n  sitemap keep their current generated output throughout the migration.\n- [ ] R5 \u2014 The authoring tool (`scripts/new-post.js`) emits the structured form only.\n- [ ] R6 \u2014 Existing posts (`content/posts/first.md`, `content/posts/second.md`)\n  are migrated to the structured form as content changes.\n- [ ] R7 \u2014 The legacy form is rejected (production build fails on legacy `author`\n  content) only after recorded generated-output and content evidence shows no\n  remaining dependency on it; if the evidence shows a straggler, rejection does\n  not execute and the finding is reported instead.\n- [ ] R8 \u2014 Maintained documentation (README authoring note) reflects the current\n  supported model at each stage, updated in the same change as the behavior it\n  describes.\n\n## Subtasks\n\n- [ ] tasks/20260925-author-metadata-migration/010-multi-author-model.md\n- [ ] tasks/20260925-author-metadata-migration/020-authoring-and-content-migration.md\n- [ ] tasks/20260925-author-metadata-migration/030-legacy-rejection.md\n\n## Open questions (execution blockers)\n\n- Q1 (design decision \u2014 data + feed contract): item shape of `authors` \u2014\n  (a) plain name strings, or (b) objects with required `name` (optional\n  `url`/`email` deferred). Recommendation: (b); both preserve current\n  single-author output. Must be approved before 010 executes.\n- Q2 (scope confirmation): no new per-author archive pages or author profile\n  pages are included; \"archives\" is covered as continuity of existing archive\n  output. Confirm before execution.\n- Q3 (minor, user-visible, resolvable at review): multi-author byline join\n  format. Recommendation: comma-joined names (e.g. `Ada Example, Grace\n  Example`); single-author output stays byte-identical.\n\n## Supporting facts\n\n- Current model: single string `author` in post front matter\n  (`content/posts/first.md:3`, `content/posts/second.md:3`).\n- Consumers: `_includes/layouts/post.njk:2` renders top-level `author` in the\n  byline; `content/feed.xml.njk:5` renders `post.data.author` per feed entry.\n  Repo-wide search confirms no other template, script, or test reads author\n  data; home, archive, tag pages, and sitemap render none.\n- Authoring tool: `scripts/new-post.js:1-3` exports `frontMatter(title, author)`\n  emitting the legacy single-name form; nothing in the repo imports it.\n- Test state: `tests/author-output.test.js` and `tests/archive-output.test.js`\n  are placeholder files containing only comments \u2014 no assertions exist yet.\n- Build: Eleventy 3 (`eleventy.config.js`, input `content/`, includes\n  `_includes/`, output `_site/`); scripts `npm run build` and `npm test`\n  (`node --test tests/*.test.js`). `node_modules` is not installed in this\n  workspace (gitignored); execution must install before running.\n- Current single-author generated output: post page `<p class=\"author\">{name}</p>`;\n  feed `<author>{name}</author>`. This is the regression anchor for the\n  byte-identical continuity claims in R2/R3.\n- Multi-author rendering cannot be proven by adding a permanent post to\n  `content/` (that would change public output); integration tests must drive the\n  real build against a temporary content fixture reusing the production config\n  and templates (see 010).\n\n## Execution plan\n\nStatus: Draft\n\n### Design\n\nThree gated stages, each leaving the build green and generated output stable.\n\nOne canonical read path owns the author shape so every consumer moves together\nand the legacy branch has exactly one home. Components:\n\n- **Canonical author model + normalizer (new)**: a single function (config\n  filter or computed data owned by the posts collection config) that accepts the\n  structured form and, during transition, the legacy scalar, and returns the\n  ordered canonical author list exposed as `authors`. It is the only code that\n  reads raw `author`. Item shape per Q1.\n- **Consumers**: `_includes/layouts/post.njk` byline and `content/feed.xml.njk`\n  entries read only the canonical `authors`; they never read raw author front\n  matter directly. Single-author rendering remains byte-identical.\n- **Authoring tool**: `scripts/new-post.js` emits the structured form only.\n- **Content**: both posts migrate to the structured form.\n- **Rejection**: the same canonical read path throws on legacy input after the\n  evidence gate, failing the production build; covered by a test.\n\nCompatibility states: S1 (after 010) \u2014 dual-form accepted, new model live in\ntemplates; S2 (after 020) \u2014 content and tooling fully on the new form, legacy\nstill tolerated but unused; S3 (after 030) \u2014 legacy rejected with a build error\nand transitional documentation removed.\n\nVerification strategy: integration tests drive the real Eleventy production\nbuild (no mocks at the important boundary) and assert generated HTML/XML \u2014\nauthor-output test (byline and feed for multi-author and legacy posts at S1;\nrejection behavior at S3) and archive-output test (home/archive/tags/sitemap\ncontinuity). A unit test covers the tooling's emitted front matter. 020 records\nthe evidence bundle (content scan plus before/after output comparison) that\ngates 030.\n\n### Implementation decisions and open questions\n\n- D1 (decision): one canonical read path (normalizer) is the only reader of the\n  legacy `author` key, keeping the rejection surface to a single branch.\n- D2 (decision): canonical key `authors`, ordered as declared in front matter;\n  consumers must not read raw author keys.\n- D3 (decision): rejection via the normalizer raising an actionable error that\n  fails the build; no silent fallback or auto-conversion after rejection.\n- Q1 (question, blocker): `authors` item shape \u2014 strings vs objects with\n  required `name`. Recommendation: objects with required `name`, matching the\n  \"structured\" intent and leaving room for feed metadata later.\n- Q2 (question, blocker): confirm no per-author archive/profile page scope.\n- Q3 (recommendation): comma-joined multi-author byline; single author unchanged.\n- D4 (recommendation, confirm): no new presence validation for missing `authors`\n  \u2014 today a missing author renders an empty byline, and this migration's scope\n  is the legacy key, not new validation rules.\n\n### Documentation\n\n`README.md` gains a short Authoring note describing the `authors` front-matter\ncontract and the `scripts/new-post.js` output, added in 010 with a visible\ntransitional note about the still-accepted legacy field; 020 keeps it accurate\nfor tooling and content; 030 removes the transitional note and documents the\nrejection error and migration path. Audience: content authors working in this\nrepo. No new docs directories or placeholder pages.\n\n### Task checklist\n\n- [ ] 010 Multi-author model with legacy-compatible rendering \u2014\n  tasks/20260925-author-metadata-migration/010-multi-author-model.md\n- [ ] 020 Authoring-tool and content migration, legacy-dependency evidence\n  gate (depends on 010) \u2014\n  tasks/20260925-author-metadata-migration/020-authoring-and-content-migration.md\n- [ ] 030 Legacy-form rejection gated on recorded evidence (depends on 020) \u2014\n  tasks/20260925-author-metadata-migration/030-legacy-rejection.md\n\n### Requirement verification\n\n- R1, R3, R2 (S1 state): `tests/author-output.test.js` integration test through\n  the real Eleventy production build \u2014 multi-author post page byline lists all\n  authors in order, feed carries one `<author>` per author, and a legacy-form\n  post's output matches the pre-migration baseline. Decisive; traverses content\n  \u2192 build \u2192 generated HTML/XML.\n- R2, R4: `tests/archive-output.test.js` integration test \u2014 home, blog archive,\n  tag pages, and sitemap output unchanged; full `npm run build` green at each\n  stage boundary.\n- R5: unit test asserting `frontMatter()` emits the structured form; migrated\n  content building in the production build corroborates the contract.\n- R6: production build of migrated posts plus per-post byline/feed comparison\n  against the pre-migration baseline recorded in 020.\n- R7: evidence bundle recorded in 020's `## Implementation Notes` (content scan\n  results plus output diff summary); 030 is blocked without it. 030 adds a test\n  asserting the build fails on legacy-form content and a final green full build.\n- R8: README reviewed and updated within each stage's change set.\n\n### Additional implementation verification\n\nNone beyond the above. The fixture's surface is small and fully covered by the\nproduction-build tests; the 020 scan additionally confirms no Eleventy data\ncascade path (directory data, globals, layouts) injects `author`.",
    "tasks/20260925-author-metadata-migration/010-multi-author-model.md": "# 010 \u2014 Multi-author model with legacy-compatible rendering\n\nAdd the canonical structured `authors` model and its normalizer, move the\npost-layout byline and feed entries onto it, and keep the legacy `author`\nstring accepted and byte-identically rendered during the transition. Establishes\nthe integration tests for author output and archive continuity.\n\nParent Task: tasks/20260925-author-metadata-migration/000-main.md\n\nDepends On: (none \u2014 first subtask)\n\n## Requirements checklist\n\n- [ ] R1 \u2014 Canonical structured multi-author metadata is supported (item shape\n  per approved Q1).\n- [ ] R2 \u2014 Legacy `author` stays accepted; a legacy-form post renders\n  byte-identically to today.\n- [ ] R3 \u2014 Byline and feed render all authors in declared order through the\n  canonical path; single-author output unchanged.\n- [ ] R4 \u2014 Home, blog archive, tag pages, and sitemap output unchanged\n  (continuity assertions).\n- [ ] R8 (part) \u2014 README authoring note documents the new model with a visible\n  transitional note about the legacy field.\n\n## Task checklist\n\n- [ ] Implement the normalizer as the single canonical read path; only code\n  that reads raw `author`/`authors` raw keys\n- [ ] Update `_includes/layouts/post.njk` byline to render canonical `authors`\n- [ ] Update `content/feed.xml.njk` to emit one `<author>` per author\n- [ ] Rewrite `tests/author-output.test.js` as a production-build integration\n  test: real build of public content (legacy era) plus a temporary content\n  fixture reusing the production config/templates for the multi-author case\n- [ ] Strengthen `tests/archive-output.test.js` with continuity assertions\n  (home, archive, tag pages, sitemap)\n- [ ] README authoring note (new model + transitional note)\n- [ ] `npm install` if needed; `npm test` and `npm run build` green; record\n  results\n\n## Verification\n\nDecisive: production-build integration test asserting the generated post-page\nbyline and feed author entries for multi-author and legacy-form posts, plus\narchive continuity assertions on the real build. Supporting: full test run and\nfull build exit cleanly.\n\nNote: a permanent multi-author post must not be added to `content/` \u2014 that\nwould change public output. Multi-author evidence comes from the temporary\nfixture built through the same real pipeline.",
    "tasks/20260925-author-metadata-migration/020-authoring-and-content-migration.md": "# 020 \u2014 Authoring-tool and content migration, legacy-dependency evidence gate\n\nMove every producer to the new model \u2014 the authoring tool and both existing\nposts \u2014 then record the generated-output and content evidence that shows\nnothing still depends on the legacy form. This evidence is the gate that\nauthorizes 030. The legacy form remains accepted (but unused) at the end of\nthis stage.\n\nParent Task: tasks/20260925-author-metadata-migration/000-main.md\n\nDepends On: tasks/20260925-author-metadata-migration/010-multi-author-model.md\n\n## Requirements checklist\n\n- [ ] R5 \u2014 `scripts/new-post.js` emits the structured form only.\n- [ ] R6 \u2014 `content/posts/first.md` and `content/posts/second.md` migrated to\n  the structured form.\n- [ ] R7 (prerequisite) \u2014 Recorded evidence shows no remaining dependency on\n  the legacy form in content, templates, scripts, or tests.\n- [ ] R2 (still holds) \u2014 Legacy form remains accepted at the end of this stage.\n- [ ] R4 \u2014 Generated output for home, archive, tags, sitemap, and the two post\n  pages/feed is unchanged after migration.\n\n## Task checklist\n\n- [ ] Rewrite `scripts/new-post.js` `frontMatter(title, authors)` to emit the\n  structured form; add unit test for the emitted front-matter contract\n- [ ] Migrate `content/posts/first.md` and `second.md` front matter to `authors`\n- [ ] Repo-wide scan: no template, script, or test reads the raw `author` key,\n  and no content uses it (test-only legacy fixtures from 010 excluded \u2014 they\n  are intentional transitional coverage until 030)\n- [ ] Capture pre-migration baseline of the two post pages and the feed;\n  rebuild; diff per page and feed against the baseline\n- [ ] Record the evidence bundle in `## Implementation Notes` (scan summary +\n  diff result) \u2014 the gate for 030\n- [ ] Full `npm test` and `npm run build` green\n\n## Verification\n\nDecisive: build diff of the migrated posts' generated pages and feed against\nthe pre-migration baseline (byte-identical), plus the content scan. Supporting:\nunit test of the tooling's emitted front matter; full build/test run.",
    "tasks/20260925-author-metadata-migration/030-legacy-rejection.md": "# 030 \u2014 Reject the legacy single-author form (evidence-gated)\n\nRemove support for the legacy single-name `author` field so the production\nbuild fails on content using it. May execute only after 020's recorded evidence\nshows no remaining dependency on the legacy form in content, templates,\nscripts, or tests.\n\nParent Task: tasks/20260925-author-metadata-migration/000-main.md\n\nDepends On: tasks/20260925-author-metadata-migration/020-authoring-and-content-migration.md\n\n## Requirements checklist\n\n- [ ] R7 \u2014 Legacy form rejected at build time, executed only after 020's\n  recorded evidence; rejection is abandoned with a report if the evidence shows\n  a straggler.\n- [ ] R8 \u2014 README transitional note removed; rejection behavior and migration\n  path documented.\n- [ ] R2 (retired) \u2014 Post-rejection state is fully on the new model; the\n  transitional compatibility branch is gone.\n\n## Task checklist\n\n- [ ] Confirm 020's evidence is recorded and clean; if missing or showing a\n  straggler, stop and report instead of proceeding\n- [ ] Make the canonical normalizer reject the legacy `author` key with an\n  actionable error that fails the production build\n- [ ] Update 010's legacy-compat test to assert rejection (replaces the\n  transitional coverage)\n- [ ] README: remove the transitional note; document the rejection error and\n  the migration path from legacy content\n- [ ] Full build and tests green; verify all generated pages present (home,\n  archive, tag pages, feed, sitemap, both post pages)\n\n## Verification\n\nDecisive: test asserting the production build fails on legacy-form content with\nthe documented error, plus a final green full build with all generated pages\npresent through the real pipeline."
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
        "requirement_count": 8,
        "title": "Migrate post author metadata to a structured multi-author model"
      },
      {
        "dependencies": [],
        "has_execution_plan": false,
        "parent_task": "tasks/20260925-author-metadata-migration/000-main.md",
        "path": "tasks/20260925-author-metadata-migration/010-multi-author-model.md",
        "phase_terms": [],
        "plan_status": null,
        "requirement_count": 5,
        "title": "010 \u2014 Multi-author model with legacy-compatible rendering"
      },
      {
        "dependencies": [],
        "has_execution_plan": false,
        "parent_task": "tasks/20260925-author-metadata-migration/000-main.md",
        "path": "tasks/20260925-author-metadata-migration/020-authoring-and-content-migration.md",
        "phase_terms": [],
        "plan_status": null,
        "requirement_count": 5,
        "title": "020 \u2014 Authoring-tool and content migration, legacy-dependency evidence gate"
      },
      {
        "dependencies": [],
        "has_execution_plan": false,
        "parent_task": "tasks/20260925-author-metadata-migration/000-main.md",
        "path": "tasks/20260925-author-metadata-migration/030-legacy-rejection.md",
        "phase_terms": [],
        "plan_status": null,
        "requirement_count": 3,
        "title": "030 \u2014 Reject the legacy single-author form (evidence-gated)"
      }
    ],
    "implementation_task_count": 3,
    "parent_links": [
      {
        "child": "tasks/20260925-author-metadata-migration/010-multi-author-model.md",
        "parent": "tasks/20260925-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260925-author-metadata-migration/020-authoring-and-content-migration.md",
        "parent": "tasks/20260925-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260925-author-metadata-migration/030-legacy-rejection.md",
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
    "added_obligations": [],
    "semantic_deliverable_count": 3,
    "actual_task_count": 3,
    "deliverable_mappings": [
      {
        "deliverable_id": "AUTHOR-D1",
        "task_paths": [
          "tasks/20260925-author-metadata-migration/010-multi-author-model.md"
        ],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Canonical normalizer is the single reader of raw author keys, normalizing legacy scalar and structured list into one documented `authors` model (README note, R8); delivered state accepts both forms with legacy rendering byte-identical (R2)."
      },
      {
        "deliverable_id": "AUTHOR-D2",
        "task_paths": [
          "tasks/20260925-author-metadata-migration/010-multi-author-model.md"
        ],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Byline and feed moved onto the canonical path with archive/home/tag/sitemap continuity asserted through the real build; combined with D1 per the target's approved alternative, leaving a clear dual-format working state."
      },
      {
        "deliverable_id": "AUTHOR-D3",
        "task_paths": [
          "tasks/20260925-author-metadata-migration/020-authoring-and-content-migration.md"
        ],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Authoring tool emits the structured form only and both posts migrate, verified by a pre/post build diff at the public boundary; no content-collection split is warranted for two posts in one collection."
      },
      {
        "deliverable_id": "AUTHOR-D4",
        "task_paths": [
          "tasks/20260925-author-metadata-migration/030-legacy-rejection.md"
        ],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Rejection executes only after 020's recorded content scan and generated-output diff, with a straggler report path, its own build-failure test, and a final green full build; transitional compatibility branch retired."
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
    "summary": "Three implementation tasks realize the target's four deliverables via the explicitly approved combination of normalization and generated-surface adoption in 010, which ends in a genuine dual-format working state (legacy accepted, byte-identical rendering, all public output on the canonical model). 020 owns producer/content migration with its own decisive build diff, and 030 owns the evidence-gated rejection; no task is a phase fragment, no layer split exists, and tests, documentation, and evidence recording sit inside the deliverables that produce them. The important crossing is decisively owned: each stage names a check through real front matter and the production Eleventy build into pages, archives, and feeds (010 integration tests with a temporary fixture through the production config, 020 pre/post output diff, 030 build-failure test plus final green build), with no mocks at the boundary. Dependencies (010→020→030) resolve, serialize nothing independently deliverable beyond what the approved combination requires, and every stage boundary is a green, publishable state. The handoff preserves consumers/producers with source pointers, compatibility constraints (byte-identical anchor), working states S1–S3, the retirement evidence plan, and the open Q1–Q3 decisions surfaced as approval blockers; retaining the full plan as Draft deviates from the omit_plan option but matches retain_plan and is transparently flagged for the user."
  }
}
```
