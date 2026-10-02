# Session — tg06-eleventy-author-migration-decomposition · task-creation-assessment-glm-max-s0 · glm max

- Run: `20260924T192104.238276Z-task-guidance-semantic-tg06-eleventy-author-migration-decomposition-glm-max-s0-bf44a6b2`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `b16bf6b0f4306d98…`)
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
  "response": "Task structure created under `tasks/20260919-author-metadata-migration/` \u2014 planning only, nothing implemented. Execution waits for your approval.\n\n## Plan summary\n\n**Outcome.** Post author metadata moves from the scalar `author: \"Name\"` field to a canonical structured multi-author form; post pages, feed, and the authoring tool consume the new model; both existing posts migrate with unchanged URLs and author output; and the legacy form is rejected only after an evidence gate proves nothing depends on it.\n\n**Approach** (5 dependency-ordered subtasks):\n1. `010-author-model-and-compat` \u2014 install deps, capture a baseline build, add the `authors` model with a normalization layer that maps both forms to one uniform view (unit-tested).\n2. `020-templates-feed-and-archives` \u2014 post layout renders all authors (joined, `p.author` element retained), feed emits one `<author>` per author, archive/tag/home tests upgraded from existence-only to full listings; build-boundary tests run a fixture site (multi-author + legacy + new-form posts) so no test-only content pollutes production `content/`.\n3. `030-authoring-tool` \u2014 `frontMatter` emits the structured list form (unit-pinned).\n4. `040-migrate-existing-posts` \u2014 convert `first.md`/`second.md`, compare generated output against the baseline.\n5. `050-legacy-gate-and-rejection` \u2014 gate (content scan + tool check + green suite) \u2192 remove legacy acceptance \u2192 explicit build error naming offending files \u2192 README updated in the same change.\n\n**Key facts grounding the plan:** all 7 `author` touchpoints inventoried (`post.njk:2`, `feed.xml.njk:5`, both posts, `new-post.js`, both placeholder tests); archives/tags/sitemap are author-independent; `posts.json` sets no author default; existing tests assert nothing; `node_modules` is absent so execution starts with `npm install`.\n\n**Open decisions needing your approval before the affected subtask runs:**\n1. **Shape** \u2014 recommend `authors` as an ordered list of display-name strings, always a list (alternative: objects with `name`/`url` if per-author attributes are needed now).\n2. **Rejection mechanism** \u2014 recommend an explicit build-time error listing files still using legacy `author:` (rather than silently stripping it).\n3. **Feed semantics** \u2014 recommend preserving current bare-text `<author>` form, one element per author; Atom-validity rework (`<name>` wrapping) deferred out of this migration.\n\n**Acceptance evidence:** unit tests (normalization, tooling) plus production-build tests over post pages, feed, and full archive listings; baseline comparison proves single-author output equivalence during transition; final suite proves the rejection error.\n\n**Risks:** normalization must not disturb the data cascade (covered by fixture builds); feed output for multi-author posts necessarily differs from legacy; removing the legacy path early would break transition guarantees \u2014 subtask ordering enforces the gate; a fresh Eleventy 3 install must work in this worktree or the gate can't be evaluated.\n\n**Exclusions:** no per-author archive/profile pages, no Atom-validity rework, no CI setup, no changes to tags/sitemap beyond regression evidence.\n\nThe plan is stored as `Status: Draft` in `000-main.md`. Approve it (including the three decisions above, or with corrections) and I'll mark it `Approved` and begin execution with subtask 010.",
  "task_files": {
    "tasks/20260919-author-metadata-migration/000-main.md": "# Migrate post author metadata to a structured multi-author model\n\nMigrate the site's single-name `author` front-matter field to a structured\nmulti-author model across post templates, the feed, archives, and the authoring\ntool. Existing posts are migrated safely under a compatibility window, and the\nlegacy single-name form is rejected only after generated-output and content\nevidence show nothing still depends on it. Planning only: this file does not\nauthorize implementation.\n\n## Requirements checklist\n\n- [ ] R1: Posts support a single canonical structured author field representing\n      an ordered list of authors; it replaces the single-name `author` field as\n      the supported authoring model. (Exact shape per approved decision in\n      `### Implementation decisions and open questions`.)\n- [ ] R2: The post page layout renders every author of a post, for both\n      single-author and multi-author posts.\n- [ ] R3: The feed emits an author element for every author of every post,\n      preserving the currently emitted author-text semantics.\n- [ ] R4: Archives, tag pages, the home listing, and the sitemap keep\n      rendering all posts (title/link) unchanged through the migration; they\n      have no author dependence and are regression-protected.\n- [ ] R5: The authoring tool (`scripts/new-post.js`) generates the structured\n      form for new posts.\n- [ ] R6: During the transition, legacy single-name posts and structured-form\n      posts coexist: both build and render correctly, with no content loss and\n      no broken generated pages at any intermediate state.\n- [ ] R7: Existing posts (`content/posts/first.md`, `content/posts/second.md`)\n      are migrated to the structured form with their URLs and rendered author\n      output preserved.\n- [ ] R8: Evidence exists for the new model, the compatibility behavior, and\n      the migration: unit tests for normalization and the authoring tool, plus\n      production-build integration tests over post pages, feed, and archives\n      that include multi-author and legacy/new mixed cases without adding\n      test-only content to production `content/`.\n- [ ] R9: The legacy single-name form is rejected only after gate evidence \u2014\n      a content scan showing zero legacy usage and green generated-output\n      evidence \u2014 and the rejection is an explicit, documented build failure.\n- [ ] R10: Maintained documentation reflects the author model, the transition\n      state, and the final rejection state, kept in the same reviewed changes\n      as the code that makes each claim true.\n\n## Subtasks\n\n- [ ] tasks/20260919-author-metadata-migration/010-author-model-and-compat.md\n- [ ] tasks/20260919-author-metadata-migration/020-templates-feed-and-archives.md\n- [ ] tasks/20260919-author-metadata-migration/030-authoring-tool.md\n- [ ] tasks/20260919-author-metadata-migration/040-migrate-existing-posts.md\n- [ ] tasks/20260919-author-metadata-migration/050-legacy-gate-and-rejection.md\n\n## Open questions and decisions\n\nThese change scope or outcomes and must be resolved (by approval of this plan\nor explicit instruction) before the affected subtask executes.\n\n1. **Structured shape (R1, blocks 010).** Recommend: `authors` as an ordered\n   YAML list of display-name strings, e.g. `authors: [\"Ada Example\"]`, always a\n   list (no scalar shorthand for the new field; the authoring tool always emits\n   a list). Alternative: entries as objects with at least `name` (optionally\n   `url`) if per-author attributes beyond the display name are required now.\n   Choose one before 010 executes.\n2. **Rejection mechanism (R9, blocks 050).** Recommend: a build-time check in\n   the Eleventy data path that fails the build with an error listing files that\n   still define legacy `author:`, so rejection is machine-enforced and matches\n   documentation. Alternative: silently ignoring/stripping the legacy field\n   (rejected recommendation: hides authoring mistakes).\n3. **Feed Atom validity (R3, affects 020 scope).** The current feed emits bare\n   text inside `<author>` (not an Atom-valid `<name>` child). Recommend:\n   preserve current semantics (one `<author>` per author, same text form) and\n   defer any Atom-validity rework out of this migration. Confirm or expand 020\n   scope.\n\n## Supporting details\n\nVerified facts from inspection (2026-09-19):\n\n- Author touchpoints (complete):\n  - `content/posts/first.md:3` \u2014 legacy scalar `author: \"Ada Example\"`.\n  - `content/posts/second.md:3` \u2014 legacy scalar `author: \"Grace Example\"`.\n  - `_includes/layouts/post.njk:2` \u2014 renders scalar `{{ author }}` inside\n    `<p class=\"author\">`.\n  - `content/feed.xml.njk:5` \u2014 `<entry><author>{{ post.data.author }}</author></entry>`\n    per post in `collections.posts`.\n  - `scripts/new-post.js:1-3` \u2014 pure `frontMatter(title, author)` emits the\n    legacy scalar string form.\n  - `tests/author-output.test.js`, `tests/archive-output.test.js` \u2014\n    comment-only placeholders, no assertions.\n- Author-independent generated surfaces: `_includes/postslist.njk` renders\n  title + url only; `content/index.njk`, `content/blog.njk`, and\n  `content/tag-pages.njk` all include `postslist.njk`;\n  `content/sitemap.xml.njk` renders URLs only.\n- Data cascade: `content/posts/posts.json` sets only `layout` and\n  `tags: [\"posts\"]`; there is no directory-level author default.\n- Build config (`eleventy.config.js`): input `content`, includes\n  `../_includes`, output `_site`; provides a `head` filter; passthrough-copies\n  `public` (directory does not exist \u2014 pre-existing condition, not in scope).\n- Test harness: `npm test` runs `node --test tests/*.test.js`; both files\n  currently collect and exit cleanly (verified with node v20.19.5) but assert\n  nothing. Generated output (`_site/`) is gitignored.\n- Dependencies are not installed in this worktree (`node_modules` absent);\n  execution must start with `npm install` (`@11ty/eleventy ^3.0.0`).\n- Documentation surface: root `README.md` describes build outputs;\n  `docs/development/index.md` and `docs/development/documentation.md` are\n  maintainer guidance; there is no `docs/index.md`. Author-model documentation\n  belongs in the author-facing surface (`README.md`) per\n  `docs/development/documentation.md` rules.\n- `UPSTREAM.md`: fixture adapted from Eleventy Base Blog.\n\nConstraints:\n\n- No test-only posts may be added to production `content/`; multi-author and\n  mixed-form build coverage must come from a separate fixture site (see 020).\n- For single-author posts, the new pipeline must produce equivalent generated\n  output to the current build, which allows before/after comparison as\n  transition evidence.\n- New public documentation claims must land in the same reviewed change as the\n  code that makes them true (repository documentation guidance).\n\n## Execution plan\n\nStatus: Draft\n\nLayered migration: normalize both author forms behind one data view, migrate\nall consumers (post layout, feed) to that view with generated-output tests,\nmigrate the authoring tool, migrate existing content, then evaluate the\nlegacy-dependency gate and reject the legacy form. Consumers are changed\nbefore content so that migrated posts render correctly the moment they are\nconverted; the legacy path is removed last, after evidence.\n\nSequence and boundaries:\n\n1. **010 \u2014 model + compatibility.** Install dependencies, capture a baseline\n   production build of the current content (comparison artifact), then\n   introduce the canonical `authors` model with a normalization step that\n   yields a uniform authors list from either the new form or the legacy scalar.\n   Templates do not change yet. Unit tests cover normalization of both forms.\n2. **020 \u2014 consumers.** Post layout renders all authors (joined display,\n   existing `p.author` element class retained); feed emits one author element\n   per author with current text semantics; archives are regression-covered\n   (posts listed with titles/links, not just existence). Generated-output\n   tests cross the real build boundary via a fixture site that includes a\n   multi-author post, a new-form single-author post, and a legacy post, so the\n   compat path is exercised; real-content build checks cover first/second.\n3. **030 \u2014 authoring tool.** `frontMatter` emits the structured list form;\n   unit test pins the exact emitted front matter.\n4. **040 \u2014 content migration.** Convert `first.md` and `second.md` to the\n   structured form; compare generated output against the 010 baseline (same\n   URLs, same rendered author text, archive/feed/sitemap intact).\n5. **050 \u2014 gate + rejection.** Evidence gate: content scan shows zero legacy\n   `author:` usage in `content/`, authoring tool no longer emits it, all\n   build-boundary tests green. Only then remove legacy acceptance from the\n   normalization path, add the explicit build-time rejection error, re-run the\n   full suite and production build, and update `README.md` to the final\n   rejection state (removing the transitional note added earlier).\n\nRisks:\n\n- Normalization must integrate with the Eleventy data cascade without\n  shadowing unrelated post data; `posts.json` has no author keys, so risk is\n  low but the integration tests must catch regressions.\n- Feed output for multi-author posts necessarily differs from the legacy\n  single-element output; single-author output must remain text-equivalent\n  (R3/R7 comparison evidence).\n- Removing the legacy path before the gate would break transition guarantees;\n  subtask ordering (050 strictly after 030/040 evidence) enforces the gate.\n- Fresh `npm install` and an Eleventy 3 build in this worktree are\n  prerequisites; if the build cannot run, the gate cannot be evaluated and the\n  plan stops at the blocked subtask with the blocker reported.\n\n### Implementation decisions and open questions\n\n- D1 (open, needs approval): field shape \u2014 recommend `authors` list of\n  display-name strings, always a list. See top-level question 1.\n- D2 (open, needs approval): rejection mechanism \u2014 recommend explicit\n  build-time error listing offending files. See top-level question 2.\n- D3 (open, needs approval): feed keeps current bare-text `<author>` semantics,\n  one element per author; Atom-validity rework deferred. See top-level\n  question 3.\n- D4 (resolved locally): multi-author post-page display joins author names\n  with a comma inside the existing `p.author` element; element/class retained\n  so page structure and styling hooks are unchanged.\n- D5 (resolved locally): canonical form is list-only; legacy scalar is\n  accepted only by the compatibility path during the transition window and is\n  not a shorthand for the new field.\n- D6 (resolved locally): generated-output tests build a small fixture site\n  under `tests/` (own content, real templates/config) rather than adding\n  test-only posts to production `content/`; real-content builds cover the\n  actual posts.\n- D7 (resolved locally): test builds write to a gitignored/temporary output\n  directory so the working tree stays clean.\n\n### Documentation\n\n- Audience: post authors/contributors (front-matter model, authoring tool\n  behavior, legacy rejection state). Maintainers get context from this task\n  tree.\n- 010/020: `README.md` gains a short author-metadata section describing the\n  structured `authors` model with an example and the transitional note that\n  the legacy single-name form is still accepted.\n- 030: same section notes the authoring tool emits the structured form.\n- 050: the section is updated in the same change as the rejection code \u2014\n  transitional note removed, legacy `author:` documented as rejected with an\n  explicit build error, with an example of the accepted form.\n- No new documentation directories or pages; smallest structure per\n  `docs/development/documentation.md`.\n\n### Task checklist\n\n- [ ] tasks/20260919-author-metadata-migration/010-author-model-and-compat.md\n- [ ] tasks/20260919-author-metadata-migration/020-templates-feed-and-archives.md\n- [ ] tasks/20260919-author-metadata-migration/030-authoring-tool.md\n- [ ] tasks/20260919-author-metadata-migration/040-migrate-existing-posts.md\n- [ ] tasks/20260919-author-metadata-migration/050-legacy-gate-and-rejection.md\n\n### Requirement verification\n\n- R1 \u2192 unit tests for normalization (both forms) plus generated-output tests\n  showing structured posts build and render (010, 020).\n- R2 \u2192 fixture-site build test: multi-author post page contains every author\n  name; single-author post page contains its author (020).\n- R3 \u2192 fixture-site build test: feed contains one `<author>` element per\n  author per post; single-author feed text matches the pre-migration form\n  (020, 040 comparison).\n- R4 \u2192 archive/tag/home build tests assert full post lists (title + link),\n  not existence only; sitemap URLs unchanged (020, 040).\n- R5 \u2192 unit test pinning `frontMatter` output to the structured list form\n  (030).\n- R6 \u2192 fixture-site test includes a legacy post and a new-form post building\n  side by side and rendering correctly (020, 040).\n- R7 \u2192 real-content build comparison against the 010 baseline: same URLs,\n  same rendered author text, archives/feed intact (040).\n- R8 \u2192 full `node --test tests/*.test.js` run collecting all unit and\n  build-boundary tests cleanly (010\u2013040; final confirmation 050).\n- R9 \u2192 gate evidence recorded in 050 (content scan result + green suite) and\n  a test showing a legacy-form post now fails the build with the documented\n  error; `README.md` updated in the same change (050).\n- R10 \u2192 README sections present at each phase and matching the behavior of\n  that change (010/020, 030, 050).\n\n### Additional implementation verification\n\n- Final production build of the real site succeeds and `git status` shows no\n  scratch/fixture leakage into production `content/`.\n- Legacy-dependency re-check immediately before rejection: grep for\n  `author:`-style scalar usage across `content/` (scan recorded in 050).\n- Confirm `npm install` warnings/errors (if any) are reviewed; record the\n  installed Eleventy version in 010 notes.",
    "tasks/20260919-author-metadata-migration/010-author-model-and-compat.md": "# 010 \u2014 Author model and compatibility layer\n\nDefine the canonical structured multi-author author field and a normalization\nstep that yields a uniform authors list from either the new form or the legacy\nsingle-name scalar, so every downstream consumer reads one view. No consumer or\ncontent changes in this subtask.\n\nParent Task: tasks/20260919-author-metadata-migration/000-main.md\nDepends On:\n\n## Requirements checklist\n\n- [ ] R1 (slice): canonical `authors` model implemented per the approved shape\n      decision (000-main, decision D1).\n- [ ] R6 (slice): legacy scalar `author:` posts normalize to the same uniform\n      authors list as new-form posts, so mixed content builds correctly.\n- [ ] R8 (slice): unit tests cover normalization of the new form, the legacy\n      scalar, and their equivalence in output shape.\n\n## Tasks\n\n- [ ] `npm install` (dependencies absent in this worktree); record the\n      installed Eleventy version.\n- [ ] Capture a baseline production build of the current content into a\n      gitignored/temporary output directory as the comparison artifact for\n      020/040.\n- [ ] Implement the canonical `authors` model and normalization (e.g.\n      Eleventy computed data on the posts collection or an equivalent data\n      step) so every post exposes a uniform authors list; legacy `author:`\n      maps into it unchanged in behavior.\n- [ ] Add unit tests for normalization: new-form list input, legacy scalar\n      input, and shape equivalence between the two.\n\n## Verification\n\n- Unit tests for both forms pass and collect cleanly under\n  `node --test tests/*.test.js`.\n- Production build of unchanged content still succeeds and produces output\n  matching the pre-change baseline (no consumer behavior change yet).\n\n## Notes\n\n- Blocked until the D1 shape decision in 000-main is approved.\n- Do not touch templates, feed, authoring tool, or content in this subtask.",
    "tasks/20260919-author-metadata-migration/020-templates-feed-and-archives.md": "# 020 \u2014 Templates, feed, and archives on the normalized authors view\n\nMove the post page layout and the feed to render all authors through the\nnormalized view from 010, keep archive/tag/home/sitemap surfaces\nauthor-independent, and add the generated-output test boundary (fixture site\nplus real-content builds).\n\nParent Task: tasks/20260919-author-metadata-migration/000-main.md\nDepends On: tasks/20260919-author-metadata-migration/010-author-model-and-compat.md\n\n## Requirements checklist\n\n- [ ] R2 (slice): `_includes/layouts/post.njk` renders every author (joined\n      display per D4; existing `p.author` element/class retained).\n- [ ] R3 (slice): `content/feed.xml.njk` emits one `<author>` element per\n      author per post, preserving current text semantics (D3).\n- [ ] R4 (slice): archive/tag/home listing tests assert full post lists\n      (title + link), replacing the existence-only placeholder; sitemap URLs\n      unchanged.\n- [ ] R6 (slice): fixture-site build test exercises a multi-author post, a\n      new-form single-author post, and a legacy post building side by side.\n- [ ] R8 (slice): generated-output tests cross the real build boundary\n      (fixture content + real templates/config) without adding test-only\n      posts to production `content/` (D6).\n\n## Tasks\n\n- [ ] Update `_includes/layouts/post.njk` to render the normalized authors.\n- [ ] Update `content/feed.xml.njk` to emit one author element per author.\n- [ ] Replace `tests/author-output.test.js` placeholder with fixture-site\n      build tests (post pages + feed) covering multi-author, new-form, and\n      legacy posts.\n- [ ] Replace `tests/archive-output.test.js` placeholder with full listing\n      assertions for archive/tag/home (and sitemap URL stability).\n- [ ] Add real-content build checks for `first.md`/`second.md` (author text\n      unchanged on pages and feed).\n- [ ] Update `README.md` author-metadata section (structured model + example +\n      transitional legacy note) in the same change (R10 slice).\n\n## Verification\n\n- Full `node --test tests/*.test.js` run collects unit tests from 010 and the\n  new build-boundary tests cleanly.\n- Single-author generated output remains text-equivalent to the 010 baseline\n  (pages and feed); multi-author fixture output shows every author.\n\n## Notes\n\n- Test builds write to a gitignored/temporary output directory (D7).\n- The fixture site lives under `tests/` with its own content and the real\n  config/templates (D6); treat it as maintained test infrastructure.",
    "tasks/20260919-author-metadata-migration/030-authoring-tool.md": "# 030 \u2014 Authoring tool emits the structured form\n\nMove `scripts/new-post.js` to the canonical structured multi-author model so\nnew posts are authored in the supported form.\n\nParent Task: tasks/20260919-author-metadata-migration/000-main.md\nDepends On: tasks/20260919-author-metadata-migration/010-author-model-and-compat.md\n\n## Requirements checklist\n\n- [ ] R5: `frontMatter(title, authors)` emits the canonical `authors` list\n      form (shape per approved D1; always a list, per D5).\n- [ ] R8 (slice): unit test pins the exact emitted front matter.\n\n## Tasks\n\n- [ ] Update `scripts/new-post.js` to accept the authors list and emit the\n      structured front matter.\n- [ ] Add/update the unit test pinning the emitted output.\n\n## Verification\n\n- Unit test runs cleanly under `node --test tests/*.test.js`; emitted front\n  matter builds through the normalization path (covered by 010 unit tests).\n\n## Notes\n\n- API change is internal to the authoring tool; no template or content change.\n- README authoring-tool claim (if added in 020) is updated here in the same\n  change if the emitted form is documented.",
    "tasks/20260919-author-metadata-migration/040-migrate-existing-posts.md": "# 040 \u2014 Migrate existing posts to the structured form\n\nConvert the two existing posts to the canonical `authors` list form and verify\ntheir generated pages are unchanged against the 010 baseline.\n\nParent Task: tasks/20260919-author-metadata-migration/000-main.md\nDepends On:\n- tasks/20260919-author-metadata-migration/010-author-model-and-compat.md\n- tasks/20260919-author-metadata-migration/020-templates-feed-and-archives.md\n\n## Requirements checklist\n\n- [ ] R7: `content/posts/first.md` and `content/posts/second.md` use the\n      structured form; URLs and rendered author output are preserved.\n- [ ] R4 (confirmation): archive, tag, home, and sitemap outputs remain\n      correct after migration.\n- [ ] R6 (confirmation): the site contains no legacy usage after this\n      subtask; mixed-form behavior remains covered by the 020 fixture tests.\n\n## Tasks\n\n- [ ] Convert `first.md` and `second.md` to the structured form.\n- [ ] Rebuild the real site and compare against the 010 baseline: post page\n      URLs, rendered author text, feed author elements, archive/tag/home\n      listings, sitemap URLs.\n- [ ] Record the content-scan result (zero legacy `author:` usage in\n      `content/`) as gate input for 050.\n\n## Verification\n\n- Build-boundary tests over real content pass; generated output matches the\n  baseline for all author-bearing and author-independent surfaces.\n\n## Notes\n\n- Content-only change; templates and tooling already support the new form.\n- Do not remove the legacy compatibility path here \u2014 that happens in 050\n  after the gate.",
    "tasks/20260919-author-metadata-migration/050-legacy-gate-and-rejection.md": "# 050 \u2014 Legacy-dependency gate and rejection of the legacy form\n\nEvaluate the evidence gate showing nothing still depends on the legacy\nsingle-name form, then reject it with an explicit build-time error and land\nthe final documentation state.\n\nParent Task: tasks/20260919-author-metadata-migration/000-main.md\nDepends On:\n- tasks/20260919-author-metadata-migration/010-author-model-and-compat.md\n- tasks/20260919-author-metadata-migration/020-templates-feed-and-archives.md\n- tasks/20260919-author-metadata-migration/030-authoring-tool.md\n- tasks/20260919-author-metadata-migration/040-migrate-existing-posts.md\n\n## Requirements checklist\n\n- [ ] R9: gate evidence recorded (content scan: zero legacy usage in\n      `content/`; authoring tool emits only the structured form; full\n      build/test suite green) before any rejection change.\n- [ ] R9 (slice): legacy `author:` is rejected by an explicit build-time error\n      listing offending files (mechanism per approved D2).\n- [ ] R8 (final): full suite collects and exits cleanly after the rejection\n      change.\n- [ ] R10: `README.md` updated in the same reviewed change \u2014 transitional\n      note removed, legacy form documented as rejected with the error\n      behavior and an example of the accepted form.\n\n## Tasks\n\n- [ ] Record gate evidence: content scan of `content/` for legacy scalar\n      usage, 030 tool output check, full suite + production build run.\n- [ ] Remove legacy acceptance from the normalization path.\n- [ ] Add the build-time rejection check with a clear error naming offending\n      files; add a test that a legacy-form post fails the build with the\n      documented error.\n- [ ] Re-run the full suite and production build; verify no scratch or fixture\n      leakage into production `content/`.\n- [ ] Update `README.md` to the final rejection state (same change as the\n      rejection code).\n\n## Verification\n\n- Full `node --test tests/*.test.js` run passes including the new\n  legacy-rejection test.\n- Production build of the real site succeeds; `README.md` matches the\n  implemented behavior.\n\n## Notes\n\n- Do not start this subtask until D2 is approved and all dependency evidence\n  exists.\n- If the gate cannot be satisfied (e.g. a consumer or content file still\n  depends on the legacy form), stop, report the blocker, and keep the\n  compatibility path in place."
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
        "requirement_count": 10,
        "title": "Migrate post author metadata to a structured multi-author model"
      },
      {
        "dependencies": [],
        "has_execution_plan": false,
        "parent_task": "tasks/20260919-author-metadata-migration/000-main.md",
        "path": "tasks/20260919-author-metadata-migration/010-author-model-and-compat.md",
        "phase_terms": [],
        "plan_status": null,
        "requirement_count": 3,
        "title": "010 \u2014 Author model and compatibility layer"
      },
      {
        "dependencies": [],
        "has_execution_plan": false,
        "parent_task": "tasks/20260919-author-metadata-migration/000-main.md",
        "path": "tasks/20260919-author-metadata-migration/020-templates-feed-and-archives.md",
        "phase_terms": [],
        "plan_status": null,
        "requirement_count": 5,
        "title": "020 \u2014 Templates, feed, and archives on the normalized authors view"
      },
      {
        "dependencies": [],
        "has_execution_plan": false,
        "parent_task": "tasks/20260919-author-metadata-migration/000-main.md",
        "path": "tasks/20260919-author-metadata-migration/030-authoring-tool.md",
        "phase_terms": [],
        "plan_status": null,
        "requirement_count": 2,
        "title": "030 \u2014 Authoring tool emits the structured form"
      },
      {
        "dependencies": [],
        "has_execution_plan": false,
        "parent_task": "tasks/20260919-author-metadata-migration/000-main.md",
        "path": "tasks/20260919-author-metadata-migration/040-migrate-existing-posts.md",
        "phase_terms": [],
        "plan_status": null,
        "requirement_count": 3,
        "title": "040 \u2014 Migrate existing posts to the structured form"
      },
      {
        "dependencies": [],
        "has_execution_plan": false,
        "parent_task": "tasks/20260919-author-metadata-migration/000-main.md",
        "path": "tasks/20260919-author-metadata-migration/050-legacy-gate-and-rejection.md",
        "phase_terms": [],
        "plan_status": null,
        "requirement_count": 4,
        "title": "050 \u2014 Legacy-dependency gate and rejection of the legacy form"
      }
    ],
    "implementation_task_count": 5,
    "parent_links": [
      {
        "child": "tasks/20260919-author-metadata-migration/010-author-model-and-compat.md",
        "parent": "tasks/20260919-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260919-author-metadata-migration/020-templates-feed-and-archives.md",
        "parent": "tasks/20260919-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260919-author-metadata-migration/030-authoring-tool.md",
        "parent": "tasks/20260919-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260919-author-metadata-migration/040-migrate-existing-posts.md",
        "parent": "tasks/20260919-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260919-author-metadata-migration/050-legacy-gate-and-rejection.md",
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
        "task_paths": ["tasks/20260919-author-metadata-migration/010-author-model-and-compat.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Canonical authors model plus normalization of legacy scalar and new form, unit-tested, with unchanged-content build baseline; matches D1's independent value (site safely accepts old and new content before consumers migrate)."
      },
      {
        "deliverable_id": "AUTHOR-D2",
        "task_paths": ["tasks/20260919-author-metadata-migration/020-templates-feed-and-archives.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Post layout and feed move to the normalized view with archive/tag/home/sitemap regression coverage; fixture-site builds cross the real Eleventy boundary; README slice lands in the same change. Keeping page/feed/archive surfaces in one task avoids the target's per-template fragmentation example."
      },
      {
        "deliverable_id": "AUTHOR-D3",
        "task_paths": [
          "tasks/20260919-author-metadata-migration/030-authoring-tool.md",
          "tasks/20260919-author-metadata-migration/040-migrate-existing-posts.md"
        ],
        "coverage": "complete",
        "coherence": "fragmented",
        "reason": "Together they cover producer and content migration with gate-input evidence, but the tool/content split is exactly the target's fragmentation example ('content rewrite and authoring helper updates split without ownership'); both posts are one collection, so no independently owned content split applies."
      },
      {
        "deliverable_id": "AUTHOR-D4",
        "task_paths": ["tasks/20260919-author-metadata-migration/050-legacy-gate-and-rejection.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Evidence gate (content scan, tool check, green suite) precedes removal; rejection is an explicit documented build error with a failing-build test and final README state in the same change; correctly depends on all prior evidence."
      }
    ],
    "mergeable_groups": [
      {
        "task_paths": [
          "tasks/20260919-author-metadata-migration/030-authoring-tool.md",
          "tasks/20260919-author-metadata-migration/040-migrate-existing-posts.md"
        ],
        "reason": "One D3 deliverable: maintained producers and content stop creating legacy dependencies. 030 is a two-item change whose emitted form no consumer renders until 020 and no content uses until 040, so it has no independently usable or acceptable result; merging restores the target's 4-deliverable partition."
      }
    ],
    "unmatched_tasks": [],
    "overpacked_tasks": [],
    "valid_layer_boundaries": [
      "tasks/20260919-author-metadata-migration/010-author-model-and-compat.md",
      "tasks/20260919-author-metadata-migration/020-templates-feed-and-archives.md",
      "tasks/20260919-author-metadata-migration/050-legacy-gate-and-rejection.md"
    ],
    "automatic_layer_fragments": [
      "tasks/20260919-author-metadata-migration/030-authoring-tool.md"
    ],
    "dependency_issues": [
      "030 depends only on 010, so the authoring tool may emit the structured form before 020 makes templates render it: a post created in that window builds and publishes but renders without author output on the page and in the feed, a degraded intermediate state against AUTHOR-5. Merging 030 into the 040 deliverable (which already depends on 010+020) removes the window."
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
              "tasks/20260919-author-metadata-migration/030-authoring-tool.md",
              "tasks/20260919-author-metadata-migration/040-migrate-existing-posts.md"
            ],
            "description": "5 tasks cover 4 coherent deliverables (ratio 1.25); the sole defect is the authoring-tool/content split of AUTHOR-D3, which the target explicitly names as a fragmentation example. All other boundaries (normalization, consumer migration, gated retirement) match the target's deliverables, and tests/documentation are owned in-change rather than as horizontal tasks."
          }
        ]
      },
      "phase_only_children": {
        "status": "none",
        "occurrences": []
      },
      "layer_split_without_independent_value": {
        "status": "present",
        "occurrences": [
          {
            "task_paths": ["tasks/20260919-author-metadata-migration/030-authoring-tool.md"],
            "description": "Package/tooling child emits the structured front matter, but until 020 no template renders that form and until 040 no content uses it; its only acceptance is a unit test pinning emitted text. The target lists 'content rewrite and authoring helper updates split without ownership' as fragmentation, so this boundary lacks a complete product outcome or independent acceptance."
          }
        ]
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
              "tasks/20260919-author-metadata-migration/030-authoring-tool.md",
              "tasks/20260919-author-metadata-migration/020-templates-feed-and-archives.md"
            ],
            "description": "030's dependency set (010 only) omits 020, permitting tool-emitted structured posts to exist while layouts and feed still read the legacy scalar, so new posts publish without author rendering. All other edges are correct: 020 after 010, 040 after 010+020 (content converts only once consumers render the new model), 050 after all evidence-producing tasks; no unnecessary serialization of D2/D3-class work."
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
    "summary": "All five approved outcomes are covered and the set stays within the target's acceptable size range, but it uses 5 tasks for the target's 4 coherent deliverables. 010, 020, and 050 map cleanly to D1, D2, and D4 with coherent ownership (tests and documentation kept inside each change, matching the instruction to treat tests/docs as in-deliverable work). The single partition defect is the 030/040 split of D3 — precisely the target's 'content rewrite and authoring helper updates split without ownership' example: 030 is a tooling fragment with no independent product outcome, and its 010-only dependency opens a window where emitted posts render without authors. The required production crossing — real front matter through normalization and the real Eleventy build into pages, archives, and feeds at every migration state — is decisively checked via fixture-site and real-content builds (010 baseline, 020 mixed-form fixture plus archive/feed assertions, 040 baseline comparison, 050 rejection build test), so crossing ownership is complete and there is no piecewise mock substitution. No phase-only children, evidence re-ownership, or overpacked tasks; merging 030 into 040 yields the target partition."
  }
}
```
