# Session — tg06-eleventy-author-migration-decomposition · task-creation-assessment · glm max

- Run: `20260919T223218.544286Z-task-guidance-semantic-tg06-eleventy-author-migration-decomposition-bb8302be`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `ecaac18da0be2b40…`)
- Config: [glm-assessor-max](../../../../shared/configs/glm-assessor-max.json)
- Activity: 3 messages · 0 tool calls · 0 tool results
- Usage: unknown — saved session contains no provider usage metadata

## Transcript

**User**

Assess task-guidance behavior for one fixed scenario across several producer
profiles. Use the reviewed target, not raw task count, as the authority.

Judge whether each task set preserves approved outcomes and partitions work
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
  "schema_version": 2,
  "scenario_id": "tg06-eleventy-author-migration-decomposition",
  "assessments": [
    {
      "producer": {"profile": "glm|gpt", "reasoning_effort": "..."},
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
  ]
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

Producer records:

[
  {
    "invalid_reasons": [],
    "producer": {
      "model": "glm-5.3-flash:cloud",
      "profile": "glm",
      "reasoning_effort": "max"
    },
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
    },
    "tool_metrics": {
      "list": 0,
      "mutation": 6,
      "other": 6,
      "read": 21,
      "search": 1,
      "shell": 8,
      "total": 36
    },
    "valid": true
  },
  {
    "invalid_reasons": [],
    "producer": {
      "model": "gpt-5.6-luna",
      "profile": "gpt",
      "reasoning_effort": "high"
    },
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
    },
    "tool_metrics": {
      "list": 0,
      "mutation": 1,
      "other": 1,
      "read": 0,
      "search": 0,
      "shell": 13,
      "total": 14
    },
    "valid": true
  },
  {
    "invalid_reasons": [],
    "producer": {
      "model": "gpt-5.6-luna",
      "profile": "gpt",
      "reasoning_effort": "xhigh"
    },
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
    },
    "tool_metrics": {
      "list": 0,
      "mutation": 2,
      "other": 2,
      "read": 0,
      "search": 0,
      "shell": 10,
      "total": 12
    },
    "valid": true
  },
  {
    "invalid_reasons": [],
    "producer": {
      "model": "gpt-5.6-luna",
      "profile": "gpt",
      "reasoning_effort": "max"
    },
    "response": "Created a Draft parent task with five dependency-ordered subtasks. No application, content, template, or generated-output files were changed.\n\n- [Main migration plan](</Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T201416.608120Z-task-guidance-tg06-eleventy-author-migration-decomposition-max-65fb9c4b/workspace/tasks/20260919-author-metadata-migration/000-main.md:1>)\n- [Author contract and transition boundary](</Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T201416.608120Z-task-guidance-tg06-eleventy-author-migration-decomposition-max-65fb9c4b/workspace/tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md:1>)\n- [Content and authoring-tool migration](</Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T201416.608120Z-task-guidance-tg06-eleventy-author-migration-decomposition-max-65fb9c4b/workspace/tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md:1>)\n- [Template, archive, and feed migration](</Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T201416.608120Z-task-guidance-tg06-eleventy-author-migration-decomposition-max-65fb9c4b/workspace/tasks/20260919-author-metadata-migration/030-template-archive-and-feed-migration.md:1>)\n- [Generated-output and content evidence](</Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T201416.608120Z-task-guidance-tg06-eleventy-author-migration-decomposition-max-65fb9c4b/workspace/tasks/20260919-author-metadata-migration/040-generated-output-and-content-evidence.md:1>)\n- [Conditional legacy retirement and documentation](</Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260919T201416.608120Z-task-guidance-tg06-eleventy-author-migration-decomposition-max-65fb9c4b/workspace/tasks/20260919-author-metadata-migration/050-legacy-retirement-and-documentation.md:1>)\n\nThe plan keeps these material decisions open for approval:\n\n- the exact structured `authors` shape;\n- whether archive/list pages should gain visible author bylines;\n- the feed representation for multiple authors;\n- compatibility and conflict behavior for the old authoring-tool signature and mixed metadata.\n\nThe legacy form is explicitly retained until the production build, generated-output assertions, and content/dependency inventory all pass. `git diff --check` passed; build and test execution were intentionally not run because this request was planning-only.",
    "task_files": {
      "tasks/20260919-author-metadata-migration/000-main.md": "# Migrate post author metadata to structured multi-author data\n\nPlan the migration from the current scalar `author` post field to an\napproved structured multi-author representation while preserving existing\ncontent and generated pages during the transition. This task is a planning\nhandoff only; the Draft does not authorize implementation.\n\n## Requirements checklist\n\n- [ ] Define and adopt an approved structured author collection that supports\n      one or more authors, preserves author order, and has an explicit display\n      contract.\n- [ ] Keep existing content and generated public pages working while the\n      migration is in progress by retaining an explicit compatibility path for\n      the legacy scalar form until the retirement gate is satisfied.\n- [ ] Move every author-consuming template and output surface to the approved\n      model, including the post layout, home/archive/tag listing surfaces,\n      feeds, and any additional consumers found during the inventory.\n- [ ] Move the post-authoring tool to the approved model with safe\n      serialization and validation for single- and multi-author input.\n- [ ] Migrate every existing post without changing its body, title, URL,\n      ordering, or unrelated metadata.\n- [ ] Produce production-boundary evidence for migrated content, legacy\n      compatibility, multi-author rendering, archives, feeds, and generated\n      page stability.\n- [ ] Reject the legacy form only after content and generated-output evidence\n      shows that no production content, template, authoring path, or other\n      in-repository dependency still requires it; otherwise leave the\n      compatibility path in place and record the blocker.\n\n## Scope and workstreams\n\nThe work is divided into five dependency-ordered workstreams:\n\n1. Establish the metadata contract and the single compatibility/normalization\n   boundary.\n2. Convert existing front matter and the post-authoring helper.\n3. Update post, archive/list, tag, and feed rendering to consume the\n   normalized collection while preserving routes and unrelated output.\n4. Replace placeholder output checks with production-build evidence and a\n   complete content/dependency inventory.\n5. Retire or reject the legacy form only when the evidence gate is green, and\n   update maintained developer guidance to describe the resulting contract.\n\nThe task does not include author profile pages, author URLs, identity\nresolution, taxonomy changes, archive URL changes, or unrelated template\nredesign unless the contract questions below are answered in a way that makes\none of them necessary.\n\n## Requirement questions and decisions\n\n### Unresolved requirement questions\n\n1. What is the exact target shape? The working recommendation is an\n   `authors` collection of records such as\n   `authors: [{ name: \"Ada Example\" }]`, preserving source order. A list of\n   strings or another record shape would change the authoring and rendering\n   contracts and must be chosen before execution.\n2. Should archive, home, and tag listings gain a visible multi-author byline,\n   or should they preserve their current title-only presentation while\n   consuming the new model wherever author data is actually rendered? The\n   current `postslist.njk` does not render an author, so adding a byline would\n   be a user-visible output change.\n3. Is `scripts/new-post.js` a public API whose old\n   `frontMatter(title, author)` call shape must remain accepted for a\n   deprecation window, or may that call shape be rejected once repository\n   evidence is complete? The plan assumes the old shape remains accepted\n   during transition and makes final rejection conditional.\n4. What should happen if a document contains both legacy `author` and the new\n   collection, or if either form is malformed? The migration needs an\n   explicit precedence/conflict policy before a strict rejection is enabled.\n\n### Provisional decisions for planning\n\n- Treat the new field as an ordered collection and keep one canonical\n  normalized value for all templates and output generators.\n- Preserve current URLs, route names, post body content, and non-author output\n  unless the approved display contract explicitly adds author text.\n- Keep legacy input readable during the migration phase; do not make the\n  compatibility branch fail merely because all checked-in posts have been\n  converted.\n- Make legacy retirement a separately verified final step. A failing or\n  incomplete evidence run leaves compatibility enabled and the retirement\n  requirement incomplete.\n\n## Research and supporting facts\n\n- `content/posts/first.md` and `content/posts/second.md` currently use the\n  scalar front-matter key `author`.\n- `_includes/layouts/post.njk` renders the scalar `author` directly.\n- `content/feed.xml.njk` reads `post.data.author` directly for every feed\n  entry.\n- `_includes/postslist.njk` is shared by `content/index.njk`,\n  `content/blog.njk`, and `content/tag-pages.njk`; it currently renders only\n  title and URL, so archive surfaces do not currently expose an author.\n- `scripts/new-post.js` exposes `frontMatter(title, author)` and emits the\n  scalar `author` key.\n- `eleventy.config.js` has no author normalization or validation boundary.\n- `content/posts/posts.json` supplies the post layout and `posts` tag but no\n  author data transformation.\n- `content/sitemap.xml.njk` emits URLs only; it is not an author consumer but\n  belongs in generated-page regression coverage.\n- `tests/archive-output.test.js` and `tests/author-output.test.js` currently\n  contain comments rather than executable assertions. `npm test` runs\n  `node --test tests/*.test.js`, and `npm run build` runs the Eleventy\n  production build into `_site`.\n- Existing maintained documentation contains no author-front-matter or\n  authoring-tool contract. `README.md` is a short site overview and\n  `docs/development/index.md` contains only an archive-pagination note.\n\n## Subtasks\n\n- [ ] [tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md](tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md)\n- [ ] [tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md](tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md)\n- [ ] [tasks/20260919-author-metadata-migration/030-template-archive-and-feed-migration.md](tasks/20260919-author-metadata-migration/030-template-archive-and-feed-migration.md)\n- [ ] [tasks/20260919-author-metadata-migration/040-generated-output-and-content-evidence.md](tasks/20260919-author-metadata-migration/040-generated-output-and-content-evidence.md)\n- [ ] [tasks/20260919-author-metadata-migration/050-legacy-retirement-and-documentation.md](tasks/20260919-author-metadata-migration/050-legacy-retirement-and-documentation.md)\n\n## Execution plan\n\nStatus: Draft\n\nBegin by resolving the target collection shape, rendering contract, authoring\nAPI compatibility, and mixed/malformed-input behavior. Then implement one\nnormalization boundary that can read both the approved new form and the\nlegacy scalar form during transition. All templates should consume that\nnormalized value instead of independently branching on front matter.\n\nAfter the boundary is available, migrate checked-in posts and the authoring\nhelper, then update the post layout and all shared listing/feed surfaces. Keep\nthe existing routes and content stable. Use a real Eleventy build for\nmulti-author and legacy-compatibility cases; do not rely only on unit tests\nthat bypass template rendering.\n\nThe evidence phase must inventory every remaining legacy reference and\nclassify it as a production dependency, an intentional migration test, or\nhistorical/documentation text. It must also prove the expected author output\non post pages and feeds, successful archive/home/tag generation, stable URLs,\nand successful content scanning. Only that evidence can authorize replacing\nthe transitional fallback with a rejection/validation path. If it is not\ngreen, leave the fallback enabled and carry the blocker forward.\n\n### Implementation decisions and open questions\n\n- The exact `authors` shape, archive presentation, old authoring-call\n  compatibility, and mixed-field policy remain open as listed above.\n- The normalizer should have one owner and one documented precedence policy;\n  templates must not grow divergent legacy fallbacks.\n- The feed representation for multiple authors must be chosen together with\n  the display contract, including escaping and author ordering.\n- A repository scan cannot establish compatibility for unknown external\n  callers of `scripts/new-post.js`; if that helper is externally consumed,\n  the final rejection step needs an explicit release/deprecation decision.\n\n### Documentation\n\nNo maintained user/developer documentation is changed by this planning task.\nOnce the contract is implemented, update the smallest existing owner-facing\ndocument, likely `README.md` or an existing development page, with the\napproved front-matter example, authoring-tool input, transition behavior, and\nthe verified legacy status. Do not describe the target contract as current\nguidance while this plan is still Draft.\n\n### Task checklist\n\n- [ ] Resolve the four contract questions or record approved answers in the\n      implementation notes before changing code.\n- [ ] Complete subtask 010 and establish the compatibility/normalization\n      boundary.\n- [ ] Complete subtasks 020 and 030, preserving content and generated routes.\n- [ ] Complete subtask 040 and attach generated-output and content-scan\n      evidence to the task.\n- [ ] Complete subtask 050 conditionally: reject the legacy form only if the\n      evidence gate passes; otherwise retain compatibility and record the\n      follow-up.\n- [ ] Run the final production build and test suite after the chosen\n      retirement outcome.\n\n### Requirement verification\n\n- The approved metadata contract is verified by contract-level tests and an\n  inspected example covering one author and multiple ordered authors.\n- Transition safety is verified by building a legacy-form post and a\n  new-form post through the actual Eleventy input/templates, then checking\n  post pages, archive/list routes, tag routes, feed output, sitemap output,\n  and unchanged URLs/content.\n- Template and feed migration is verified by a repository reference scan plus\n  generated-output assertions showing that all rendered author text comes\n  from the normalized collection and that no missing/legacy scalar value leaks\n  into output.\n- Content/tool migration is verified by scanning all production posts and\n  authoring-tool output, with focused tests for one author, multiple authors,\n  ordering, and safe serialization of names requiring quoting/escaping.\n- Legacy rejection is verified only after the content/dependency inventory is\n  clean and the generated-output suite passes with migrated content. A\n  failed gate is evidence for retaining compatibility, not permission to\n  reject the field.",
      "tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md": "# Establish the author metadata contract and transition boundary\n\nDefine the structured multi-author data contract and the compatibility boundary\nthat lets old and new post metadata coexist while the repository is migrated.\n\nParent Task: tasks/20260919-author-metadata-migration/000-main.md\n\n## Requirements checklist\n\n- [ ] Record the approved structured author collection, required fields,\n      cardinality, ordering, and display semantics.\n- [ ] Define one canonical normalized value for templates and output\n      generators.\n- [ ] Accept the legacy scalar `author` form during transition without\n      changing its rendered name or breaking old content.\n- [ ] Define deterministic behavior for new-only, legacy-only, both-field, and\n      malformed metadata before strict rejection is considered.\n- [ ] Keep the compatibility path isolated so the rest of the site does not\n      read the legacy field directly.\n\n## Supporting facts\n\n- The only current content examples are scalar names in\n  `content/posts/first.md` and `content/posts/second.md`.\n- There is no existing data normalization in `eleventy.config.js` or\n  `content/posts/posts.json`.\n- The post layout and feed currently read legacy data independently, which\n  makes a shared boundary necessary for consistent output.\n\n## Execution plan\n\nStatus: Draft\n\nResolve the open contract questions in the parent task before implementation.\nChoose the smallest structured representation that supports one or more\nordered authors and the approved output contract. Define the normalized\nrecord/list shape that all templates will receive, including how names are\nescaped and displayed.\n\nImplement the compatibility behavior at one owned boundary in the Eleventy\ndata/configuration path. It should translate legacy scalar input into the\nnormalized collection during transition, without requiring each template to\nknow about both forms. Add focused evidence for precedence and invalid-input\nbehavior, but defer removal of the legacy branch to subtask 050.\n\n### Implementation decisions and open questions\n\n- The target record shape and mixed-field policy are intentionally unresolved\n  until the parent task questions are answered.\n- Do not add optional identity/profile fields merely because a record shape\n  could hold them; they are outside the requested migration.\n- The compatibility boundary must be usable by both page templates and feed\n  generation, not just by the post layout.\n\n### Documentation\n\nRecord the approved contract in the parent task's implementation notes during\nexecution. Do not update current user guidance from this Draft subtask.\n\n### Task checklist\n\n- [ ] Obtain approval for the structured collection and rendering contract.\n- [ ] Define new-only, legacy-only, both-field, and malformed-input behavior.\n- [ ] Implement one normalization/compatibility owner after execution is\n      approved.\n- [ ] Add focused contract evidence consumed by subtask 040.\n- [ ] Update the parent task with the decided contract and any deviations.\n\n### Requirement verification\n\n- Contract evidence demonstrates the normalized collection for one and\n  multiple authors, including source ordering.\n- A real Eleventy build using legacy metadata demonstrates that transition\n  compatibility preserves the existing author name.\n- A mixed/malformed metadata test demonstrates the approved deterministic\n  behavior without silently selecting an undocumented value.\n- A source scan confirms that legacy branching is confined to the owned\n  compatibility boundary and its intentional tests.",
      "tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md": "# Migrate post content and the authoring tool\n\nConvert checked-in post metadata and the post-generation helper to the\napproved structured author model while preserving post content and providing\nsafe transition behavior.\n\nParent Task: tasks/20260919-author-metadata-migration/000-main.md\nDepends On: tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md\n\n## Requirements checklist\n\n- [ ] Convert every existing post to the approved structured author field\n      without changing title, body, URL, ordering, or unrelated front matter.\n- [ ] Update `scripts/new-post.js` to emit the approved representation for\n      one or more authors.\n- [ ] Define and test the authoring helper's transition behavior for the\n      legacy call shape, if it remains supported during the deprecation\n      window.\n- [ ] Serialize author names safely, including names that require quoting or\n      escaping in front matter.\n- [ ] Leave production content with no unclassified legacy scalar field before\n      the retirement evidence is evaluated.\n\n## Supporting facts\n\n- `content/posts/first.md` and `content/posts/second.md` are the complete\n  checked-in post set observed during planning and each currently has one\n  scalar author.\n- `scripts/new-post.js` currently accepts `(title, author)` and interpolates\n  both values directly into YAML, so names requiring quoting are not covered\n  by executable tests.\n- The package's test script runs Node's test runner over `tests/*.test.js`;\n  current author tests are placeholders.\n\n## Execution plan\n\nStatus: Draft\n\nAfter subtask 010's contract is approved, migrate each production post\nmechanically while checking the resulting front matter and preserving all\nnon-author content. Include a representative multi-author case in the\nproduction-boundary coverage without inventing unrelated post metadata or\nchanging routes.\n\nChange the authoring helper to accept the approved structured input and emit\nvalid, safely quoted front matter. If the old call shape is retained for the\ntransition, route it through the same normalizer and mark it as a deliberate\ncompatibility path so it can be inventoried and retired later. Add tests for\nsingle-author, multiple ordered authors, and special characters.\n\n### Implementation decisions and open questions\n\n- The exact function signature depends on the approved collection shape and\n  the unresolved external-consumer question in the parent task.\n- Whether a checked-in sample post becomes multi-author or a realistic build\n  fixture supplies that case must preserve the repository's production path;\n  test-only shortcuts that bypass Eleventy are not acceptable evidence.\n- Do not remove the old helper call shape here if subtask 010 or the parent\n  task still requires a transition window.\n\n### Documentation\n\nThe final authoring input example belongs in the maintained developer\nguidance handled by subtask 050. This subtask should only add comments or\ntest descriptions needed to explain executable behavior.\n\n### Task checklist\n\n- [ ] Confirm the approved schema and authoring API.\n- [ ] Migrate all checked-in post front matter and inspect the diff for\n      non-author changes.\n- [ ] Update the authoring helper and its transition behavior.\n- [ ] Add safe-serialization coverage for single, multiple, ordered, and\n      special-character names.\n- [ ] Produce a content inventory for subtask 040, distinguishing intentional\n      compatibility fixtures from production content.\n\n### Requirement verification\n\n- A front-matter/content diff or parser check proves every existing post has\n  the approved field and retains its title, body, URL, ordering, and other\n  metadata.\n- Authoring-helper tests prove valid output for one and multiple authors and\n  names containing YAML-sensitive characters.\n- A real generated post from the helper reaches the Eleventy build path and\n  renders correctly; a serialization-only assertion is not sufficient.\n- A production-content scan reports no unclassified legacy `author` field\n  before subtask 040's retirement gate.",
      "tasks/20260919-author-metadata-migration/030-template-archive-and-feed-migration.md": "# Migrate templates, archives, and feeds to the author collection\n\nUpdate every rendering surface that can expose post metadata to consume the\nnormalized multi-author value while preserving existing routes and unrelated\ngenerated output.\n\nParent Task: tasks/20260919-author-metadata-migration/000-main.md\nDepends On: tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md\n\n## Requirements checklist\n\n- [ ] Update the post layout to render the approved author collection,\n      including the chosen one- and multi-author display contract.\n- [ ] Audit the shared post list used by the home page, archive, and tag\n      pages; if it renders author data under the approved contract, use the\n      normalized collection rather than the legacy field.\n- [ ] Update feed generation for all authors, preserving order and valid\n      escaped output under the approved feed representation.\n- [ ] Keep sitemap generation, page URLs, archive routes, and unrelated\n      output working.\n- [ ] Leave no direct legacy-field reads in production templates outside the\n      deliberate compatibility boundary.\n\n## Supporting facts\n\n- `_includes/layouts/post.njk` directly renders `author`.\n- `content/feed.xml.njk` directly reads `post.data.author`.\n- `_includes/postslist.njk` is shared by `content/index.njk`,\n  `content/blog.njk`, and `content/tag-pages.njk`, but currently renders only\n  titles and links.\n- `content/sitemap.xml.njk` has no author dependency and should be covered as\n  a generated-page regression surface rather than changed unnecessarily.\n\n## Execution plan\n\nStatus: Draft\n\nUse the normalization boundary from subtask 010 in the post layout and feed.\nRender every approved author according to the chosen order/separator or feed\nentry contract, with proper escaping. Audit the shared list template and its\nthree callers; preserve the current title-only archive presentation unless\nthe open archive question is explicitly answered in favor of visible\nbylines, but ensure no author consumer is left on the scalar field.\n\nBuild the complete site with migrated content and inspect the post, home,\narchive, tag, feed, and sitemap outputs. Add assertions at the generated\noutput boundary rather than relying only on template text inspection.\n\n### Implementation decisions and open questions\n\n- Archive byline visibility and feed multiple-author representation remain\n  open until the parent contract is approved.\n- The feed must not collapse multiple authors into an ambiguous string unless\n  that is the explicitly approved contract.\n- No sitemap author data should be added solely to make the migration appear\n  complete; it has no current author consumer.\n\n### Documentation\n\nDocument the resulting rendered byline/feed behavior in the maintained\ndeveloper guidance only after it is verified. This subtask does not change\ncurrent documentation while the plan is Draft.\n\n### Task checklist\n\n- [ ] Confirm the post, archive/list, and feed rendering contract.\n- [ ] Update the post layout and feed to consume normalized authors.\n- [ ] Audit/update the shared list and all home/archive/tag callers as\n      required by the approved display contract.\n- [ ] Add generated-output assertions for one and multiple authors and for\n      escaped names.\n- [ ] Run a full build and pass route/output observations to subtask 040.\n\n### Requirement verification\n\n- Generated individual post pages show the approved author output for\n  single- and multi-author content without `undefined`, scalar-object\n  artifacts, or missing names.\n- Generated home, archive, and tag pages build at their existing URLs and\n  satisfy the approved archive byline contract.\n- The feed contains all authors in the approved order/structure and remains\n  valid escaped output.\n- The sitemap and unrelated page URLs remain generated, and a source scan\n  finds no direct legacy reads outside the compatibility owner.",
      "tasks/20260919-author-metadata-migration/040-generated-output-and-content-evidence.md": "# Prove generated-output and content safety before retirement\n\nReplace placeholder checks with evidence at the production Eleventy boundary\nand establish the inventory that controls whether legacy author input may be\nrejected.\n\nParent Task: tasks/20260919-author-metadata-migration/000-main.md\nDepends On: tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md\nDepends On: tasks/20260919-author-metadata-migration/030-template-archive-and-feed-migration.md\n\n## Requirements checklist\n\n- [ ] Add executable tests for the production build paths named by the\n      migration: individual posts, home/archive/tag pages, feed, and sitemap.\n- [ ] Cover migrated single-author content, at least one realistic\n      multi-author case, and legacy-form compatibility while the transition\n      branch is still enabled.\n- [ ] Verify URL/path stability and preservation of non-author post content\n      and generated page structure.\n- [ ] Scan production content, templates, configuration, and authoring tools\n      for remaining legacy dependencies and classify intentional compatibility\n      coverage separately.\n- [ ] Produce a clear green/red evidence result that subtask 050 can use\n      before changing legacy behavior.\n\n## Supporting facts\n\n- `tests/archive-output.test.js` and `tests/author-output.test.js` currently\n  contain no executable assertions.\n- `npm run build` is the repository's real Eleventy production build and\n  writes `_site`; `npm test` invokes Node's test runner.\n- Existing output consumers include the post layout, shared list, feed, and\n  sitemap, while the current archive test does not verify their content.\n\n## Execution plan\n\nStatus: Draft\n\nTurn the placeholder test files into focused production-build tests. Exercise\nthe actual content/templates and inspect generated files for author names,\nordering, escaping, absence of missing values, expected routes, and preserved\nnon-author content. Ensure the multi-author case crosses the Eleventy\nrendering boundary rather than only calling a formatter in isolation.\n\nRun a repository inventory after content and template migration. Every\nremaining `author` occurrence must be classified. Production post front\nmatter, production templates, and the new authoring path must not depend on\nthe legacy scalar; an intentional transition fixture/test is evidence of the\ncompatibility branch, not evidence that production still requires it.\n\nRecord exact commands, collection/exit results, generated paths inspected,\nand any blocker in the parent task. This evidence must be complete before\nsubtask 050 attempts retirement.\n\n### Implementation decisions and open questions\n\n- The tests must use the real build boundary and may not mock away the\n  normalizer or substitute a test-only rendering path.\n- The accepted archive and feed assertions depend on the contract approved by\n  the parent task.\n- Decide whether to keep a legacy compatibility fixture after rejection. If\n  retained, it must assert rejection rather than silently keeping a positive\n  dependency.\n\n### Documentation\n\nThe evidence report belongs in task implementation/completion notes during\nexecution. Do not publish a claim that legacy input is rejected until the\nfinal gate actually passes.\n\n### Task checklist\n\n- [ ] Add executable archive and author output coverage.\n- [ ] Add production-build coverage for single, multiple, and legacy-form\n      cases.\n- [ ] Verify post, home/archive/tag, feed, sitemap, route, and content\n      stability.\n- [ ] Run content/template/tool inventory and classify all legacy references.\n- [ ] Mark the evidence gate green only when every approved condition passes;\n      otherwise record the exact blocker and keep retirement disabled.\n\n### Requirement verification\n\n- `npm test` collects and exits successfully with meaningful assertions.\n- `npm run build` exits successfully and generated files contain the expected\n  author output on all relevant surfaces.\n- Generated-output assertions prove existing URLs and non-author content are\n  preserved while all approved authors render.\n- The inventory proves no unclassified production dependency remains on the\n  legacy scalar before retirement is considered.\n- The resulting evidence record explicitly authorizes or blocks subtask 050;\n  no inference from a passing unit test alone is sufficient.",
      "tasks/20260919-author-metadata-migration/050-legacy-retirement-and-documentation.md": "# Retire the legacy author form when the evidence gate permits\n\nConditionally reject the legacy scalar author form after generated-output and\ncontent evidence is green, then publish the verified authoring contract in\nthe smallest maintained documentation surface.\n\nParent Task: tasks/20260919-author-metadata-migration/000-main.md\nDepends On: tasks/20260919-author-metadata-migration/040-generated-output-and-content-evidence.md\n\n## Requirements checklist\n\n- [ ] Inspect subtask 040's evidence before changing legacy behavior.\n- [ ] If and only if the evidence gate is green, reject or remove the legacy\n      scalar form according to the approved policy and update its intentional\n      tests.\n- [ ] If the gate is not green, leave legacy compatibility enabled, document\n      the blocker, and do not claim that the migration is complete.\n- [ ] Update maintained developer guidance with the approved front-matter\n      structure, authoring-tool input, rendered behavior, and actual\n      transition/retirement status.\n- [ ] Run the final production build and test suite after the chosen outcome.\n\n## Supporting facts\n\n- The current repository has no authoring-guide section; `README.md` is the\n  shortest existing project-level guidance surface.\n- The legacy field currently appears in production content, the post layout,\n  the feed, and the authoring helper, so retirement is unsafe until subtasks\n  020, 030, and 040 have completed.\n- The user requirement permits rejection only after evidence demonstrates that\n  no remaining dependency requires the old form; it does not require\n  rejection when evidence is incomplete.\n\n## Execution plan\n\nStatus: Draft\n\nRead the evidence and inventory produced by subtask 040. If any production\ncontent, template, authoring path, generated output, or required regression\ncase still depends on the legacy scalar, make no rejection change. Record the\nblocking dependency and leave the transition normalizer active for a later\nfollow-up.\n\nIf every approved evidence condition is green, replace the transitional\nacceptance branch with the approved rejection/validation behavior, update\ntests to prove that legacy input now fails in the documented way, and rerun\nthe complete production build. Keep an intentional migration-history note\nonly where it does not create a live production dependency.\n\nUpdate the smallest existing maintained documentation surface after the\nbehavior is verified. The documentation must distinguish current supported\ninput from historical transition behavior and must not claim rejection if the\ngate blocked it.\n\n### Implementation decisions and open questions\n\n- The exact rejection error and whether the old authoring function signature\n  remains as a compatibility wrapper depend on the approved contract and\n  external-consumer decision.\n- Retirement is conditional, not automatic: a red or incomplete evidence\n  record requires compatibility to remain enabled.\n- Do not create a new documentation hierarchy solely for this migration; use\n  the existing owner-facing guidance unless a later scope decision identifies\n  a better owner.\n\n### Documentation\n\nUpdate `README.md` or the confirmed existing development owner document with:\n\n- the approved structured author front-matter example;\n- the authoring helper's approved input and safe serialization expectations;\n- how one and multiple authors appear on post/archive/feed surfaces;\n- whether legacy `author` is still accepted, deprecated, or rejected, based on\n  the evidence gate.\n\nReview the wording against the final build/test evidence so target-only\nbehavior is not presented as current guidance.\n\n### Task checklist\n\n- [ ] Review and record the subtask 040 evidence result.\n- [ ] Keep compatibility and record a blocker if the evidence gate is not\n      green.\n- [ ] If green, implement and test the approved legacy rejection behavior.\n- [ ] Update maintained documentation with verified current behavior.\n- [ ] Run `npm test` and `npm run build` after the final outcome.\n- [ ] Append immutable completion notes to the parent and this task when the\n      execution is complete.\n\n### Requirement verification\n\n- A green gate is traceable to the generated-output and content evidence from\n  subtask 040; no rejection is based on source search alone.\n- If rejected, a legacy-form input test proves the documented failure and the\n  migrated production build still passes.\n- If not rejected, the task records the exact unresolved dependency and\n  demonstrates that legacy content still builds during the transition.\n- The final documentation matches the verified runtime behavior.\n- Final `npm test` and `npm run build` runs collect, exit, and generate the\n  expected public paths successfully."
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
          "title": "Migrate post author metadata to structured multi-author data"
        },
        {
          "dependencies": [],
          "has_execution_plan": true,
          "parent_task": "tasks/20260919-author-metadata-migration/000-main.md",
          "path": "tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md",
          "phase_terms": [],
          "plan_status": "Draft",
          "requirement_count": 5,
          "title": "Establish the author metadata contract and transition boundary"
        },
        {
          "dependencies": [],
          "has_execution_plan": true,
          "parent_task": "tasks/20260919-author-metadata-migration/000-main.md",
          "path": "tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md",
          "phase_terms": [],
          "plan_status": "Draft",
          "requirement_count": 5,
          "title": "Migrate post content and the authoring tool"
        },
        {
          "dependencies": [],
          "has_execution_plan": true,
          "parent_task": "tasks/20260919-author-metadata-migration/000-main.md",
          "path": "tasks/20260919-author-metadata-migration/030-template-archive-and-feed-migration.md",
          "phase_terms": [],
          "plan_status": "Draft",
          "requirement_count": 5,
          "title": "Migrate templates, archives, and feeds to the author collection"
        },
        {
          "dependencies": [],
          "has_execution_plan": true,
          "parent_task": "tasks/20260919-author-metadata-migration/000-main.md",
          "path": "tasks/20260919-author-metadata-migration/040-generated-output-and-content-evidence.md",
          "phase_terms": [],
          "plan_status": "Draft",
          "requirement_count": 5,
          "title": "Prove generated-output and content safety before retirement"
        },
        {
          "dependencies": [],
          "has_execution_plan": true,
          "parent_task": "tasks/20260919-author-metadata-migration/000-main.md",
          "path": "tasks/20260919-author-metadata-migration/050-legacy-retirement-and-documentation.md",
          "phase_terms": [
            "documentation"
          ],
          "plan_status": "Draft",
          "requirement_count": 5,
          "title": "Retire the legacy author form when the evidence gate permits"
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
          "child": "tasks/20260919-author-metadata-migration/030-template-archive-and-feed-migration.md",
          "parent": "tasks/20260919-author-metadata-migration/000-main.md",
          "resolves": true
        },
        {
          "child": "tasks/20260919-author-metadata-migration/040-generated-output-and-content-evidence.md",
          "parent": "tasks/20260919-author-metadata-migration/000-main.md",
          "resolves": true
        },
        {
          "child": "tasks/20260919-author-metadata-migration/050-legacy-retirement-and-documentation.md",
          "parent": "tasks/20260919-author-metadata-migration/000-main.md",
          "resolves": true
        }
      ],
      "phase_named_files": [
        "tasks/20260919-author-metadata-migration/050-legacy-retirement-and-documentation.md"
      ],
      "task_directory_count": 1,
      "task_file_count": 6
    },
    "tool_metrics": {
      "list": 0,
      "mutation": 1,
      "other": 1,
      "read": 0,
      "search": 0,
      "shell": 13,
      "total": 14
    },
    "valid": true
  }
]


**Assistant** *(reasoning present)*

{
  "schema_version": 2,
  "scenario_id": "tg06-eleventy-author-migration-decomposition",
  "assessments": [
    {
      "producer": {"profile": "glm", "reasoning_effort": "max"},
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
          "reason": "010 lands the canonical authors model with normalization of both forms plus unit tests and a baseline production build; the site accepts old and new content before any consumer or content changes, exactly D1's dual-format working state."
        },
        {
          "deliverable_id": "AUTHOR-D2",
          "task_paths": ["tasks/20260919-author-metadata-migration/020-templates-feed-and-archives.md"],
          "coverage": "complete",
          "coherence": "coherent",
          "reason": "Post layout, feed, and archive regression move together in one consumer-migration task with fixture-site build tests through the real config/templates; no per-template splitting."
        },
        {
          "deliverable_id": "AUTHOR-D3",
          "task_paths": [
            "tasks/20260919-author-metadata-migration/030-authoring-tool.md",
            "tasks/20260919-author-metadata-migration/040-migrate-existing-posts.md"
          ],
          "coverage": "complete",
          "coherence": "fragmented",
          "reason": "Authoring-tool change and content conversion are split into two children; the target bundles producer and content migration in one deliverable and names this split as a fragmentation pattern."
        },
        {
          "deliverable_id": "AUTHOR-D4",
          "task_paths": ["tasks/20260919-author-metadata-migration/050-legacy-gate-and-rejection.md"],
          "coverage": "complete",
          "coherence": "coherent",
          "reason": "Gate evidence, legacy rejection with an explicit build error and negative test, and final-state documentation land in one gated retirement change."
        }
      ],
      "mergeable_groups": [
        {
          "task_paths": [
            "tasks/20260919-author-metadata-migration/030-authoring-tool.md",
            "tasks/20260919-author-metadata-migration/040-migrate-existing-posts.md"
          ],
          "reason": "Both children together complete AUTHOR-D3 (producers and content stop creating new legacy dependencies); each carries only half the outcome, so merging loses no independent value."
        }
      ],
      "unmatched_tasks": [],
      "overpacked_tasks": [],
      "valid_layer_boundaries": [],
      "automatic_layer_fragments": ["tasks/20260919-author-metadata-migration/030-authoring-tool.md"],
      "dependency_issues": [
        "040 declares a dependency on 020 although AUTHOR-D3 depends only on AUTHOR-D1; the edge serializes the content half of producer migration behind consumer migration. It is conservative (it protects single-author output equivalence per AUTHOR-5) but serializes independently deliverable work under the target graph."
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
              "description": "AUTHOR-D3 is split into an authoring-tool task and a content-conversion task, the producer/tooling vs content split the target's fragmentation examples name."
            }
          ]
        },
        "phase_only_children": {"status": "none", "occurrences": []},
        "layer_split_without_independent_value": {
          "status": "partial",
          "occurrences": [
            {
              "task_paths": ["tasks/20260919-author-metadata-migration/030-authoring-tool.md"],
              "description": "The authoring-tool child is separately owned and unit-pinned, but it divides producer migration so that neither 030 nor 040 carries the AUTHOR-D3 outcome alone; the target bundles tooling with content migration."
            }
          ]
        },
        "evidence_reownership": {"status": "none", "occurrences": []},
        "unsafe_dependencies": {
          "status": "partial",
          "occurrences": [
            {
              "task_paths": ["tasks/20260919-author-metadata-migration/040-migrate-existing-posts.md"],
              "description": "040→020 edge serializes content migration behind consumer migration even though AUTHOR-D3 needs only AUTHOR-D1's normalization; conservative for AUTHOR-5 but an unnecessary serialization of independently deliverable work."
            }
          ]
        },
        "piecewise_crossing_evidence": {"status": "none", "occurrences": []}
      },
      "partition_quality_score": 84,
      "handoff_quality_score": 86,
      "summary": "The partition follows the target's state-based model closely: normalization+compatibility (010), one combined consumer-migration task covering layout, feed, and archives (020), and a gated retirement with evidence, rejection, and final documentation (050) map 1:1 to AUTHOR-D1/D2/D4, with tests and documentation embedded inside deliverables rather than horizontal. The only boundary defect is splitting AUTHOR-D3 into a tool task (030) and a content task (040), a split the target explicitly names as fragmentation; merging them loses nothing. The 040→020 dependency conservatively serializes content migration behind rendering migration. Outcome coverage is complete, and the important crossing is owned by named real-build checks (mixed-content fixture builds through real templates/config, real-content baseline comparison, post-rejection build), so crossing ownership is complete. Open decisions on field shape, rejection mechanism, and feed semantics are surfaced for approval, matching the target's open questions, though the legacy deprecation-period question is not explicitly raised."
    },
    {
      "producer": {"profile": "gpt", "reasoning_effort": "high"},
      "outcome_coverage": "complete",
      "missing_outcomes": [],
      "added_obligations": [],
      "semantic_deliverable_count": 4,
      "actual_task_count": 5,
      "deliverable_mappings": [
        {
          "deliverable_id": "AUTHOR-D1",
          "task_paths": [
            "tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md",
            "tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md"
          ],
          "coverage": "complete",
          "coherence": "fragmented",
          "reason": "The contract/transition decision (010) stands alone as a decision phase while the normalization implementation is fused with content/tool migration in 020; the accept-old-and-new-before-migration working state is never delivered as its own checkpoint."
        },
        {
          "deliverable_id": "AUTHOR-D2",
          "task_paths": ["tasks/20260919-author-metadata-migration/030-rendering-and-output-migration.md"],
          "coverage": "complete",
          "coherence": "coherent",
          "reason": "Post layout, shared archive include, and feed move together in one rendering task with real-build inspection; archives are kept author-independent per the open contract question."
        },
        {
          "deliverable_id": "AUTHOR-D3",
          "task_paths": ["tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md"],
          "coverage": "complete",
          "coherence": "overpacked",
          "reason": "Content conversion and the authoring-tool change share a task with the normalization delivery (AUTHOR-D1), fusing two target deliverables into one atomic change and collapsing the compatibility checkpoint."
        },
        {
          "deliverable_id": "AUTHOR-D4",
          "task_paths": ["tasks/20260919-author-metadata-migration/040-verification-and-legacy-removal.md"],
          "coverage": "complete",
          "coherence": "fragmented",
          "reason": "The gated retirement is embedded in a verification task that also builds the migration-wide executable test suite, smearing the retirement delivery across displaced evidence work."
        }
      ],
      "mergeable_groups": [
        {
          "task_paths": [
            "tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md",
            "tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md"
          ],
          "reason": "The contract/transition decision is the decision core of the normalization delivery; AUTHOR-D1 is one working state, so the standalone decision phase merges into the normalization task."
        },
        {
          "task_paths": [
            "tasks/20260919-author-metadata-migration/040-verification-and-legacy-removal.md",
            "tasks/20260919-author-metadata-migration/050-documentation-and-release-handoff.md"
          ],
          "reason": "Final maintained documentation of the retired state belongs inside the gated retirement change (AUTHOR-D4) rather than a separate documentation child."
        }
      ],
      "unmatched_tasks": ["tasks/20260919-author-metadata-migration/050-documentation-and-release-handoff.md"],
      "overpacked_tasks": [
        "tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md"
      ],
      "valid_layer_boundaries": [],
      "automatic_layer_fragments": [],
      "dependency_issues": [
        "030 depends on 020 although AUTHOR-D2 needs only AUTHOR-D1's normalization; because 020 fuses normalization with content/tool migration, rendering migration is serialized behind content migration.",
        "The plan migrates content and tooling (020) before templates (030) and never states that normalization preserves the legacy author view for converted posts, so the 020→030 window can publish pages and feeds without author output, against AUTHOR-5."
      ],
      "crossing_ownership": "complete",
      "fragmentation_severity": "medium",
      "fragmentation_ratio": 1.25,
      "quality_metrics": {
        "fragmentation": {
          "status": "medium",
          "occurrences": [
            {
              "task_paths": ["tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md"],
              "description": "Standalone contract/transition decision phase ahead of the normalization delivery; AUTHOR-D1's decision core is detached from its implementation."
            },
            {
              "task_paths": ["tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md"],
              "description": "Normalization delivery (AUTHOR-D1) is fused with content/tool migration (AUTHOR-D3), removing the accept-before-migrate checkpoint the target treats as an independent deliverable."
            },
            {
              "task_paths": ["tasks/20260919-author-metadata-migration/040-verification-and-legacy-removal.md"],
              "description": "Horizontal verification child concentrates the executable build-boundary tests that belong with the 020/030 deliveries they prove."
            },
            {
              "task_paths": ["tasks/20260919-author-metadata-migration/050-documentation-and-release-handoff.md"],
              "description": "Documentation-only child completing the migration delivery instead of landing final-state documentation inside the retirement change."
            }
          ]
        },
        "phase_only_children": {
          "status": "present",
          "occurrences": [
            {
              "task_paths": ["tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md"],
              "description": "Decision child that only records the contract consumed by later deliveries; no implementation result of its own."
            },
            {
              "task_paths": ["tasks/20260919-author-metadata-migration/050-documentation-and-release-handoff.md"],
              "description": "Documentation child that only completes the migration delivery; its guidance work belongs inside the retirement change."
            }
          ]
        },
        "layer_split_without_independent_value": {"status": "none", "occurrences": []},
        "evidence_reownership": {
          "status": "present",
          "occurrences": [
            {
              "task_paths": ["tasks/20260919-author-metadata-migration/040-verification-and-legacy-removal.md"],
              "description": "Executable production-boundary tests for post pages, archives, tag pages, and feeds are written in a final verification task rather than shipping with the rendering (030) and content (020) deliveries they verify; 030 plans build-and-inspect verification only."
            },
            {
              "task_paths": ["tasks/20260919-author-metadata-migration/050-documentation-and-release-handoff.md"],
              "description": "Documentation child re-owns the evidence trail, comparing its claims against 040's build/test evidence instead of evidence shipping with the deliveries themselves."
            }
          ]
        },
        "unsafe_dependencies": {
          "status": "present",
          "occurrences": [
            {
              "task_paths": ["tasks/20260919-author-metadata-migration/030-rendering-and-output-migration.md"],
              "description": "030→020 edge serializes independently deliverable rendering migration behind content/tool migration; the edge exists only because 020 fuses normalization with AUTHOR-D3 work."
            },
            {
              "task_paths": [
                "tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md",
                "tasks/20260919-author-metadata-migration/030-rendering-and-output-migration.md"
              ],
              "description": "Content/tool migration precedes template migration with no stated mechanism keeping the legacy author view rendered for converted posts, permitting a window where pages and feeds lose author output (AUTHOR-5)."
            }
          ]
        },
        "piecewise_crossing_evidence": {"status": "none", "occurrences": []}
      },
      "partition_quality_score": 62,
      "handoff_quality_score": 70,
      "summary": "Outcome coverage is complete and the important crossing is owned by named production-build checks (030's real build and inspection, 040's executable generated-output assertions including legacy-compatibility fixtures while the transition branch is enabled, and a post-rejection rebuild). The partition, however, shifts the target's boundaries materially: the normalization delivery is fused with content/tool migration in 020 (losing the accept-before-migrate checkpoint and forcing 030 to depend on 020), a standalone contract phase (010) and a documentation-only child (050) hang off the tree, and 040 builds the migration-wide executable test suite that belongs with the deliveries it verifies — the exact horizontal-test, documentation, and evidence patterns the target flags. The content-before-templates ordering is safe only if normalization preserves the legacy author view, which the tasks never state. The retirement gate itself is properly evidence-based and the three contract decisions are surfaced for approval."
    },
    {
      "producer": {"profile": "gpt", "reasoning_effort": "xhigh"},
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
          "reason": "Normalization is implemented in 020 combined with generated-surface adoption — a combination the target explicitly accepts — but the schema/output contract and producer-consumer inventory stand alone in 010 as a detached decision phase."
        },
        {
          "deliverable_id": "AUTHOR-D2",
          "task_paths": ["tasks/20260919-author-metadata-migration/020-compatibility-and-rendering.md"],
          "coverage": "complete",
          "coherence": "coherent",
          "reason": "Post layout, shared listing include, and feed adopt the normalized model together with build-level assertions for single-, multi-, and legacy-author fixtures plus URL/order/sitemap preservation."
        },
        {
          "deliverable_id": "AUTHOR-D3",
          "task_paths": [
            "tasks/20260919-author-metadata-migration/030-content-migration.md",
            "tasks/20260919-author-metadata-migration/040-authoring-tool-and-guidance.md"
          ],
          "coverage": "complete",
          "coherence": "fragmented",
          "reason": "Content conversion (030) and authoring-helper migration (040) are separate children; the target bundles producers and content in one deliverable and names this split as a fragmentation pattern."
        },
        {
          "deliverable_id": "AUTHOR-D4",
          "task_paths": ["tasks/20260919-author-metadata-migration/050-evidence-and-legacy-cutover.md"],
          "coverage": "complete",
          "coherence": "coherent",
          "reason": "Evidence scans, gated compatibility removal, negative rejection regression, and final-state guidance updates form one gated cutover task."
        }
      ],
      "mergeable_groups": [
        {
          "task_paths": [
            "tasks/20260919-author-metadata-migration/010-contract-and-inventory.md",
            "tasks/20260919-author-metadata-migration/020-compatibility-and-rendering.md"
          ],
          "reason": "The contract/inventory decision is the decision core of the normalization delivery; AUTHOR-D1 is one working state, so the standalone decision phase merges into 020."
        },
        {
          "task_paths": [
            "tasks/20260919-author-metadata-migration/030-content-migration.md",
            "tasks/20260919-author-metadata-migration/040-authoring-tool-and-guidance.md"
          ],
          "reason": "Content migration and authoring-helper migration together complete AUTHOR-D3; neither child carries the producer-migration outcome alone, so merging loses no independent value."
        }
      ],
      "unmatched_tasks": [],
      "overpacked_tasks": [],
      "valid_layer_boundaries": [],
      "automatic_layer_fragments": ["tasks/20260919-author-metadata-migration/040-authoring-tool-and-guidance.md"],
      "dependency_issues": [
        "030 (content conversion) depends only on the 010 contract, not on 020 where the normalization/compatibility boundary is implemented; the declared graph permits migrating content before any normalization exists, which would publish converted posts through scalar-reading templates with no author output (AUTHOR-5)."
      ],
      "crossing_ownership": "complete",
      "fragmentation_severity": "low",
      "fragmentation_ratio": 1.25,
      "quality_metrics": {
        "fragmentation": {
          "status": "low",
          "occurrences": [
            {
              "task_paths": ["tasks/20260919-author-metadata-migration/010-contract-and-inventory.md"],
              "description": "Standalone contract-and-inventory decision phase ahead of the normalization delivery."
            },
            {
              "task_paths": [
                "tasks/20260919-author-metadata-migration/030-content-migration.md",
                "tasks/20260919-author-metadata-migration/040-authoring-tool-and-guidance.md"
              ],
              "description": "AUTHOR-D3 is split into content-conversion and authoring-helper children, the split the target's fragmentation examples name."
            }
          ]
        },
        "phase_only_children": {
          "status": "partial",
          "occurrences": [
            {
              "task_paths": ["tasks/20260919-author-metadata-migration/010-contract-and-inventory.md"],
              "description": "Contract/inventory child produces decisions and scan definitions consumed by later deliveries; it only completes the normalization delivery's decision core."
            }
          ]
        },
        "layer_split_without_independent_value": {
          "status": "partial",
          "occurrences": [
            {
              "task_paths": ["tasks/20260919-author-metadata-migration/040-authoring-tool-and-guidance.md"],
              "description": "The authoring-helper child is separately owned and testable, but it divides producer migration so neither 030 nor 040 completes AUTHOR-D3 alone; the target bundles tooling with content migration."
            }
          ]
        },
        "evidence_reownership": {"status": "none", "occurrences": []},
        "unsafe_dependencies": {
          "status": "present",
          "occurrences": [
            {
              "task_paths": ["tasks/20260919-author-metadata-migration/030-content-migration.md"],
              "description": "Missing dependency: 030 needs the normalization boundary implemented in 020 but declares only 010; executing 030 before 020 migrates content with no normalization in place — a broken intermediate state the graph permits."
            }
          ]
        },
        "piecewise_crossing_evidence": {"status": "none", "occurrences": []}
      },
      "partition_quality_score": 74,
      "handoff_quality_score": 78,
      "summary": "This set uses the target's sanctioned combination well: 020 fuses normalization with generated-surface adoption while keeping legacy fixtures building, so AUTHOR-D1 and AUTHOR-D2 are covered without an overpacked task, and evidence stays with the deliveries (build assertions in 020, content evidence in 030, helper tests plus real-build checks in 040). Two boundary defects remain: a standalone contract/inventory phase (010) ahead of the normalization delivery, and the content/tooling split (030/040) the target names as fragmentation. The declared graph also permits content conversion (030) to run before the normalization boundary (020) exists, since 030 depends only on the 010 contract — a missing dependency permitting a broken intermediate state. Outcome coverage is complete, the retirement is properly evidence-gated with a negative rejection regression, and the crossing is owned by named real-build checks at every migration state."
    },
    {
      "producer": {"profile": "gpt", "reasoning_effort": "max"},
      "outcome_coverage": "complete",
      "missing_outcomes": [],
      "added_obligations": [],
      "semantic_deliverable_count": 4,
      "actual_task_count": 5,
      "deliverable_mappings": [
        {
          "deliverable_id": "AUTHOR-D1",
          "task_paths": ["tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md"],
          "coverage": "complete",
          "coherence": "coherent",
          "reason": "010 resolves the contract and implements the normalization/compatibility boundary in the Eleventy data path, proving with a real legacy build that the dual-format working state renders unchanged."
        },
        {
          "deliverable_id": "AUTHOR-D3",
          "task_paths": ["tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md"],
          "coverage": "complete",
          "coherent": false,
          "coherence": "coherent",
          "reason": "Content conversion and the authoring-helper migration land together with serialization tests and a real-build check for helper output, matching AUTHOR-D3's producer-and-content deliverable."
        },
        {
          "deliverable_id": "AUTHOR-D2",
          "task_paths": ["tasks/20260919-author-metadata-migration/030-template-archive-and-feed-migration.md"],
          "coverage": "complete",
          "coherence": "coherent",
          "reason": "Post layout, shared list audit, and feed move in one rendering task with generated-output assertions; sitemap and routes are regression-covered rather than changed."
        },
        {
          "deliverable_id": "AUTHOR-D4",
          "task_paths": ["tasks/20260919-author-metadata-migration/050-legacy-retirement-and-documentation.md"],
          "coverage": "complete",
          "coherence": "coherent",
          "reason": "Conditional retirement behind the 040 evidence gate, rejection tests, final builds, and maintained documentation land as one gated retirement deliverable."
        }
      ],
      "mergeable_groups": [
        {
          "task_paths": ["tasks/20260919-author-metadata-migration/040-generated-output-and-content-evidence.md"],
          "reason": "Its executable output tests belong with the 020/030 deliveries they verify, and its legacy-dependency inventory belongs with the 050 retirement gate; the standalone evidence task splits otherwise-embedded work."
        }
      ],
      "unmatched_tasks": ["tasks/20260919-author-metadata-migration/040-generated-output-and-content-evidence.md"],
      "overpacked_tasks": [],
      "valid_layer_boundaries": [],
      "automatic_layer_fragments": [],
      "dependency_issues": [
        "010 leaves 020 (content/tool migration) and 030 (template migration) unordered; the intermediate window's validity rests on the normalization boundary also serving the unchanged scalar-reading layout for new-form posts, which the tasks do not state explicitly (AUTHOR-5 risk)."
      ],
      "crossing_ownership": "complete",
      "fragmentation_severity": "low",
      "fragmentation_ratio": 1.25,
      "quality_metrics": {
        "fragmentation": {
          "status": "low",
          "occurrences": [
            {
              "task_paths": ["tasks/20260919-author-metadata-migration/040-generated-output-and-content-evidence.md"],
              "description": "Standalone evidence task concentrates the executable build-boundary tests for posts, archives, feeds, and sitemap — the horizontal build-test pattern the target flags."
            }
          ]
        },
        "phase_only_children": {
          "status": "partial",
          "occurrences": [
            {
              "task_paths": ["tasks/20260919-author-metadata-migration/040-generated-output-and-content-evidence.md"],
              "description": "Testing child whose executable tests complete the 020/030 deliveries they verify; its legacy-dependency inventory portion is legitimately AUTHOR-D4 gate input."
            }
          ]
        },
        "layer_split_without_independent_value": {"status": "none", "occurrences": []},
        "evidence_reownership": {
          "status": "present",
          "occurrences": [
            {
              "task_paths": ["tasks/20260919-author-metadata-migration/040-generated-output-and-content-evidence.md"],
              "description": "Executable production-boundary tests for post pages, home/archive/tag pages, feed, and sitemap are written in a final evidence child instead of shipping with the 020/030 deliveries they prove; 030 only inspects output manually and passes observations forward."
            }
          ]
        },
        "unsafe_dependencies": {
          "status": "partial",
          "occurrences": [
            {
              "task_paths": [
                "tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md",
                "tasks/20260919-author-metadata-migration/030-template-archive-and-feed-migration.md"
              ],
              "description": "020 and 030 are unordered siblings after 010; nothing requires rendering adoption before or with content conversion, so the window between them is guarded only by an unstated normalization behavior."
            }
          ]
        },
        "piecewise_crossing_evidence": {"status": "none", "occurrences": []}
      },
      "partition_quality_score": 79,
      "handoff_quality_score": 82,
      "summary": "Four of five tasks map 1:1 onto the target's deliverables with no phase children among them: normalization+compatibility with a real legacy build (010), combined content+tool migration (020), one combined rendering task (030), and a conditional, evidence-gated retirement with final documentation (050). The single structural defect is 040, a horizontal evidence task that writes the executable build-boundary tests the 020/030 deliveries should carry — the exact pattern the target flags — while its dependency inventory is legitimately AUTHOR-D4 gate input. The graph leaves content and template migration unordered after 010, leaving an intermediate-output window guarded only by an unstated normalization behavior. Coverage is complete, the crossing is owned by named real-build checks at every state (legacy build in 010, helper output through the real build in 020, generated-output assertions in 030/040, post-rejection rebuild in 050), and the conditional retirement plus the external-consumer deprecation question align with the target's open questions."
    }
  ]
}
