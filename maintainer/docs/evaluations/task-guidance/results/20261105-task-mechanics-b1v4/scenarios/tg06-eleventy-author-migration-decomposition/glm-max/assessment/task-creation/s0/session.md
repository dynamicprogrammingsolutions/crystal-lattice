# Session — tg06-eleventy-author-migration-decomposition · task-creation-assessment-glm-max-s0 · glm max

- Run: `20261102T045311.940993Z-task-guidance-semantic-tg06-eleventy-author-migration-decomposition-glm-max-s0-637dc9fd`
- Model: glm-5.3-flash (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-c440c4f661a7.md) — captured (original SHA-256 `e423fe275b893475…`)
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
  "response": "Task structure created \u2014 planning only, nothing implemented. The only change in the tree is the new `tasks/20261102-multi-author-migration/` directory.\n\n## What was created\n\n**`tasks/20261102-multi-author-migration/000-main.md`** \u2014 parent task: 7 requirements, the two pending material decisions, and the inspected facts (complete legacy-`author` inventory: `post.njk:2`, `feed.xml.njk:5`, `scripts/new-post.js`, and the two posts; archives/home/tags/sitemap render no author data today; both test files are empty placeholders that pass trivially).\n\n**`010-structured-author-adoption.md`** (Draft) \u2014 the end-to-end adoption: one normalization accessor (recommended: `posts.11tydata.js` with `eleventyComputed`), templates and feed consume only `authors`, the script emits the structured form, both posts migrated, baseline-first generated-output comparison at every milestone, and real generated-output tests (including multi-author and legacy-equivalence fixtures built through the real pipeline). Ends in an independently shippable state: fully migrated, legacy still tolerated.\n\n**`020-legacy-author-rejection.md`** (Draft, `Depends On` 010) \u2014 the compatibility-state flip, gated: re-confirm content scan + build evidence *before* touching code, then remove the fallback, add the approved rejection, swap the equivalence test for a rejection test, and verify output is still baseline-identical. If the comparison fails, the flip reverts and the surfaced dependency is reported \u2014 the gate does its job.\n\n## Two decisions need your confirmation before execution (both recorded in 000-main)\n\n1. **Data shape** (persisted content data): recommended `authors:` as a YAML list of `{ name, url? }` entries in block style. A plain string list is the simpler alternative.\n2. **What \"rejected\" means** (user-visible build behavior): recommended a loud build failure naming the offending file; the alternative is silently ignoring the field.\n\nOne planning interpretation to be aware of: since archives currently render no author data, I scoped their obligation to \"keep working unchanged\" \u2014 author display in archives would be new scope.\n\nKey risks carried in the plans: accessor/template divergence (mitigated by the single-accessor rule and equivalence test), test artifacts dirtying the tree (gitignored/teardown paths), and the empty-placeholder test failure mode (final run must show tests actually collected). Rollback throughout is a simple revert \u2014 everything touched is git-tracked.\n\nBoth plans are `Status: Draft` \u2014 execution waits for your approval, and not before the two decisions above are settled.",
  "task_files": {
    "tasks/20261102-multi-author-migration/000-main.md": "# Structured multi-author migration\n\nMigrate post author metadata from the legacy single-name `author` front-matter\nfield to a structured multi-author model across templates, feed, archives, and\nauthoring tooling; migrate the existing posts; and retire the legacy form only\nonce content and generated-output evidence show nothing still depends on it.\nPlanning only \u2014 no execution has been approved.\n\n## Requirements checklist\n\n- [ ] A structured multi-author model is the single canonical form of post\n  author data, and every consumer \u2014 post layout, feed, authoring tooling \u2014\n  reads and emits only that model. (Owner: 010)\n- [ ] All generated surfaces (post pages, home, archive, tag pages, feed,\n  sitemap) build and render correctly under the new model, and with the\n  current content their generated output is identical to the pre-migration\n  baseline. (Owner: 010)\n- [ ] During the transition, a post carrying only the legacy single-name\n  `author` field builds and renders identically to its structured equivalent.\n  (Owner: 010)\n- [ ] Both existing posts are migrated to the structured model with no author\n  information lost. (Owner: 010)\n- [ ] Generated-output regression coverage for author rendering \u2014 single- and\n  multi-author, post pages and feed \u2014 exists under `tests/` and passes\n  through the production build path. (Owner: 010)\n- [ ] Maintained documentation matches the supported author model at each\n  phase: the structured form documented when adopted, and the legacy form no\n  longer presented as supported once rejected. (Owners: 010, 020)\n- [ ] The legacy `author` form is rejected only after current content evidence\n  and generated-output evidence show that nothing still depends on it, and\n  after rejection the migrated site still builds with output identical to the\n  baseline. (Owner: 020)\n\n## Questions and decisions\n\n- Pending (material \u2014 persisted content data): the shape of the structured\n  form. Recommendation: `authors` as a YAML list of entries with required\n  `name` and optional `url`, in block style:\n\n  ```yaml\n  authors:\n    - name: \"Ada Example\"\n  ```\n\n  A plain list of strings would give multi-author support but not structure.\n  Must be confirmed before execution starts.\n- Pending (material \u2014 user-visible build behavior): what rejection means for\n  content that still supplies the legacy form. Recommendation: active\n  rejection \u2014 the production build fails with an error naming the offending\n  file; silently ignoring the field would let content regress unnoticed.\n  This decides subtask 020's mechanism; confirm before approving 020.\n- Planning interpretation: \"templates, archives, feeds, and authoring tools\n  move to the new model\" means every surface that consumes author data reads\n  the new model. Archives, home, tag pages, and sitemap currently render no\n  author data at all, so their obligation is to keep working unchanged, not to\n  gain author display. Author display in archives would be new scope beyond\n  this request.\n\n## Subtasks\n\n- [ ] `tasks/20261102-multi-author-migration/010-structured-author-adoption.md`\n  \u2014 adopt the structured model everywhere, migrate the posts, keep legacy\n  reading working through one normalization point, and establish the\n  generated-output evidence and tests.\n- [ ] `tasks/20261102-multi-author-migration/020-legacy-author-rejection.md`\n  \u2014 flip the compatibility state to reject the legacy form, gated on 010's\n  evidence (`Depends On` declared in that file).\n\nOrder rationale: 010 ends in an independently acceptable, shippable state \u2014\nfully migrated with legacy still tolerated, which is exactly the transition\nstate the request requires. 020 is the compatibility-state flip and remains\nblocked if 010's evidence shows a remaining dependency, so it can be deferred\nor reported separately without reopening 010.\n\n## Supporting details\n\nFacts from inspection (20261102, repo-wide search):\n\n- Complete legacy-`author` inventory: `_includes/layouts/post.njk:2` renders\n  `{{ author }}`; `content/feed.xml.njk:5` renders one\n  `<author>{{ post.data.author }}</author>` per post; `scripts/new-post.js`\n  emits `author: \"<name>\"` via `frontMatter(title, author)`; content:\n  `content/posts/first.md` (`Ada Example`) and `content/posts/second.md`\n  (`Grace Example`).\n- `_includes/postslist.njk`, `content/blog.njk`, `content/index.njk`,\n  `content/tag-pages.njk`, and `content/sitemap.xml.njk` render no author\n  data.\n- `content/posts/posts.json` is the directory data file (shared `layout`,\n  `tags: [\"posts\"]`); a JS directory data file (`posts.11tydata.js`) can host\n  a normalization accessor via `eleventyComputed`.\n- `tests/author-output.test.js` and `tests/archive-output.test.js` are\n  comment-only placeholders; `npm test` (`node --test tests/*.test.js`)\n  passes trivially today. There is no existing author coverage to preserve \u2014\n  only coverage to establish. Because empty test files pass, evidence must\n  confirm tests actually collected and ran.\n- Dependencies are not installed (no `node_modules/`, no lockfile);\n  `node_modules/` and `_site/` are gitignored, so builds and baseline\n  snapshots keep the working tree clean. Build evidence requires\n  `npm install` first.\n- Eleventy ^3.0.0 with Nunjucks templates. No `docs/index.md`;\n  `docs/development/index.md` holds only an unrelated archive-pagination\n  placeholder. Current author values are plain ASCII and the author-bearing\n  templates contain no dates, so generated output comparison should be\n  deterministic.\n",
    "tasks/20261102-multi-author-migration/010-structured-author-adoption.md": "# Structured author adoption\n\nParent Task: tasks/20261102-multi-author-migration/000-main.md\n\nIntroduce the structured `authors` model as the single canonical form of post\nauthor data, switch every consumer to it, migrate the two existing posts, keep\nlegacy-form posts working through one normalization point, and establish the\ngenerated-output evidence and tests that the later rejection step (020) is\ngated on.\n\n## Requirements checklist\n\n- [ ] `_includes/layouts/post.njk` and `content/feed.xml.njk` render only from\n  the structured `authors` model, and `scripts/new-post.js` emits only the\n  structured form; the transition normalization accessor is the only code\n  aware of the legacy `author` field.\n- [ ] A post carrying only the legacy `author` string builds and renders with\n  output identical to the same post expressed in structured form; the\n  legacy\u2192structured mapping lives in exactly one shared place.\n- [ ] The production build over the current two posts produces output\n  identical to the pre-migration baseline across every generated page.\n- [ ] Both existing posts use only the structured form and no legacy\n  `author:` remains anywhere under `content/`.\n- [ ] A multi-author post renders every author in the post-page byline and\n  one `<author>` element per author in the feed, verified through a\n  production build of a temporary fixture.\n- [ ] `tests/` contains generated-output coverage for author rendering \u2014\n  real-content single-author pages and feed, fixture multi-author, fixture\n  legacy equivalence \u2014 and `npm test` collects and passes it.\n- [ ] Maintained documentation states the supported author front-matter model.\n\n## Implementation plan\n\nStatus: Draft\n\n### Design\n\nData flow: front matter (`authors`, or legacy `author` while tolerated) \u2192\nEleventy data cascade \u2192 one normalization accessor guarantees page data always\nexposes `authors` as the structured list \u2192 `post.njk` renders the byline from\nit, `feed.xml.njk` emits one `<author>` per entry. The accessor never changes\nrendered output; templates never see the legacy field.\n\nNormalization accessor (recommended): convert `content/posts/posts.json` to\n`content/posts/posts.11tydata.js`, keeping the existing `layout` and `tags`\nand adding `eleventyComputed.authors` that returns the structured value when\npresent and otherwise derives `[{ name: <legacy string> }]`. The accessor\nhandles both keys explicitly rather than relying on Eleventy's data-precedence\nsemantics. Accepted fallback: keep `posts.json` and add an `authors` Nunjucks\nfilter in `eleventy.config.js` that every template calls \u2014 functionally fine,\nbut it spreads the compat rule across call sites.\n\nRendering: the post byline joins author names; a single author must produce\nexactly the current text (e.g. `Ada Example`). Multi-author join is new\ndisplay behavior \u2014 recommend `\", \"` (deterministic, scales past two authors).\nThe feed emits `<author>{{ a.name }}</author>` per entry, which for\nsingle-author posts reproduces the current element exactly.\n\nAuthoring tool: `frontMatter(title, authors)` takes the structured list and\nemits block-style `authors:` YAML matching the content convention, so script\noutput and hand-written front matter agree.\n\nVerification strategy: the decisive evidence is the production build compared\nagainst a pre-change baseline. Permanent regression coverage lives in tests\nthat invoke the real build into disposable output directories.\n\n### Order and rationale\n\n1. `npm install`; run the production build; record the baseline `_site` output\n   (gitignored path or temp dir outside the repo) plus the exact\n   author-bearing expectations (byline text per post page, feed `<author>`\n   contents, full page set). Stop-safe point: nothing changed yet.\n2. Add the accessor; switch `post.njk` and `feed.xml.njk` to consume\n   `authors`. Content is still legacy, so the accessor supplies everything.\n   Build; full comparison against the baseline must be identical.\n3. Migrate `first.md` and `second.md` to the structured form. Build; compare \u2014\n   identical. Content evidence now exists: zero legacy `author:` under\n   `content/`.\n4. Update `scripts/new-post.js` to the structured interface.\n5. Tests. Rework `tests/author-output.test.js` to run the production build on\n   the real content and assert (a) both post pages' byline text and (b) the\n   feed's `<author>` contents. For multi-author and legacy-equivalence cases,\n   build a temporary fixture site through the real pipeline: a fixture input\n   dir with its own minimal `eleventy.config.js` pointing `includes` at the\n   repo `_includes` (absolute path), with `content/feed.xml.njk` copied into\n   the fixture at test runtime from the live file so the template cannot\n   drift. Builds go to disposable output dirs; fixture dirs are removed in\n   teardown. Extend `tests/archive-output.test.js` minimally to assert the\n   archive lists both migrated posts (archives unaffected).\n6. Documentation: add a short front-matter note stating the supported\n   `authors` model (recommended: `README.md` \u2014 the site currently documents\n   only build outputs, and no front-matter doc exists to update).\n7. Final production build + full baseline comparison + `npm test`; confirm\n   clean exits and record the evidence 020 is gated on in Implementation\n   notes.\n\nMilestones 1\u20133 are safe stopping points; the state after milestone 3 \u2014 fully\nmigrated, legacy still tolerated, evidence recorded \u2014 is independently\nacceptable and is what unblocks 020.\n\n### Risks and way back\n\n- Divergent normalization (template and accessor disagreeing about the model):\n  mitigated by the single-accessor rule and the legacy-equivalence test.\n- Eleventy computed-data precedence surprises: the accessor handles both keys\n  explicitly, so correctness does not depend on precedence; the fixture test\n  catches regressions.\n- Baseline drift from nondeterminism: author-bearing templates contain no\n  dates or random values; any diff outside author-bearing surfaces is a defect\n  to explain, not noise to accept.\n- Test leftovers: fixture/temp artifacts must be created under gitignored or\n  teardown-removed paths so a failed run cannot dirty the tree.\n- Blast radius: two templates, one script, two posts, tests, docs \u2014 all\n  git-tracked. Rollback is reverting the change; no persisted or external\n  state exists beyond the repository.\n\n### Implementation decisions and open questions\n\n- Adopted locally (reversible): block-style YAML for `authors` in content;\n  `\", \"` byline join for multi-author display; `frontMatter(title, authors)`\n  signature; accessor via `posts.11tydata.js`. These affect only new\n  multi-author output or the in-repo-unused script interface; existing\n  rendered output is pinned by the baseline comparison.\n- Blocked on the main task's pending decision: final data shape (adds or\n  changes `url` handling). Execution must not start before it is confirmed;\n  this plan is Draft until then. The rejection mechanism is 020's concern.\n- Open questions: none local.\n\n### Documentation\n\n- Audience: content authors and maintainers of this fixture. Requirement: the\n  supported `authors` front-matter model is documented where authoring is\n  documented \u2014 recommended: a short \"Post front matter\" note in `README.md`,\n  per `docs/development/documentation.md` (smallest structure that helps the\n  reader; claim lands in the same reviewed change as the code). In this phase\n  the legacy form is still tolerated; docs describe the structured form as the\n  supported model and may note the transition tolerance.\n\n### Task checklist\n\n- [ ] Install dependencies; production build; record baseline output and\n  author-bearing expectations.\n- [ ] Add the single normalization accessor for legacy\u2192structured authors.\n- [ ] Switch `_includes/layouts/post.njk` and `content/feed.xml.njk` to\n  consume `authors`; build and confirm output identical to baseline.\n- [ ] Migrate `content/posts/first.md` and `content/posts/second.md`; build\n  and confirm identical; confirm zero legacy `author:` under `content/`.\n- [ ] Update `scripts/new-post.js` to emit the structured form.\n- [ ] Implement generated-output tests (real-content single-author, fixture\n  multi-author, fixture legacy equivalence) and minimal archive coverage.\n- [ ] Document the supported author model.\n- [ ] Final build + full comparison + `npm test`; record the evidence 020 is\n  gated on.\n\n### Requirement verification\n\n- Structured model is canonical (req 1): code inspection \u2014 the only remaining\n  `author` reference is the accessor; decisive check is the baseline\n  comparison below through the production build.\n- Transition tolerance (req 2): fixture build through the real pipeline \u2014\n  legacy-only post output equals the structured equivalent (byline and feed\n  element compared).\n- Existing output unchanged (req 3): full `_site` comparison against the\n  pre-change baseline after the template switch, after content migration, and\n  at the final build \u2014 the named decisive check for this subtask.\n- Content migrated, nothing lost (req 4): repo scan showing zero legacy\n  `author:` under `content/`, plus the identical-output comparison proving no\n  rendered loss.\n- Multi-author rendering (req 5): production build of the two-author fixture;\n  assert both names in the byline and two `<author>` elements in the feed.\n- Regression coverage (req 6): `npm test` collects the new tests and exits\n  cleanly; tests exercise the real build, not mocks.\n- Documentation (req 7): the documented section reviewed against the\n  implemented model.\n\nDeliberately not covered: zero-author posts (behavior unspecified \u2014 no\nrequirement invented); URL/sitemap/feed structure beyond the author element\n(no change planned); fixture templates other than the runtime-copied feed and\nthe repo `_includes` layout (real templates are covered by the real-content\nassertions).\n\n### Additional implementation verification\n\n- Confirm the final `npm test` run actually collected the new tests (count or\n  per-file output), guarding the real failure mode of this repo today: empty\n  placeholder test files that pass without testing anything.\n",
    "tasks/20261102-multi-author-migration/020-legacy-author-rejection.md": "# Legacy author rejection\n\nParent Task: tasks/20261102-multi-author-migration/000-main.md\n\nDepends On: tasks/20261102-multi-author-migration/010-structured-author-adoption.md\n\nFlip the compatibility state after 010's evidence is re-confirmed: stop\naccepting the legacy `author` form, remove the transition normalization, and\nverify both the rejection and that the migrated site's output is unchanged.\n\n## Requirements checklist\n\n- [ ] The gate is honored: the flip is executed only after re-confirming\n  (a) content evidence \u2014 zero legacy `author:` occurrences under `content/` \u2014\n  and (b) generated-output evidence \u2014 010's build comparison against the\n  baseline still holds; the evidence is recorded before the flip.\n- [ ] The transition normalization is removed: no template, script, data\n  file, or test maps or reads the legacy `author` field anywhere.\n- [ ] Legacy-form input is rejected per the approved mechanism (main task\n  recommendation: production build fails with an error naming the offending\n  file), verified by building a temporary legacy-form fixture and asserting\n  the approved observable outcome.\n- [ ] The migrated production content still builds and every existing page's\n  output remains identical to the baseline recorded in 010.\n- [ ] Documentation no longer presents the legacy form as supported and\n  states the rejection behavior where it is user-visible.\n\n## Implementation plan\n\nStatus: Draft\n\nDesign: replace the accessor's legacy fallback (010's `eleventyComputed.authors`\nderivation, or the equivalent filter) with the approved rejection behavior, in\none coherent change together with the test and documentation updates. After\nthis subtask, page data contains only structured `authors`, and supplying\nlegacy `author:` produces the approved outcome instead of silent tolerance.\n\nOrder and rationale:\n\n1. Re-confirm the gate (read-only checkpoint; record dated evidence in\n   Implementation notes): content scan \u2014 zero legacy `author:` under\n   `content/`; `npm test` on the migrated site passes; spot-check 010's\n   baseline comparison expectations still describe current output. If anything\n   still depends on the legacy form, stop and report \u2014 do not reject.\n2. Flip: remove the normalization fallback, implement the approved rejection,\n   retire 010's legacy-equivalence fixture test (it would fail by design) and\n   replace it with the rejection test, update documentation \u2014 all in one\n   change so no intermediate state claims the wrong contract.\n3. Verify: production build over migrated content compared against 010's\n   baseline must be identical; production build of a legacy-form fixture must\n   produce the approved outcome (nonzero exit and error naming the file, or\n   the alternative if that is what was approved); `npm test` collects and\n   passes everything. If the comparison fails, revert the flip and report the\n   dependency that surfaced \u2014 the gate did its job.\n\nStop-safe: step 1 is read-only. Steps 2\u20133 are a single reversible change;\nreverting restores 010's tolerated state.\n\nRisks: a consumer outside the repository or added later regresses (assumption:\nthe repository is the complete scope \u2014 no external consumers identified during\nplanning); removing the accessor subtly changes data shape (mitigated by the\nfull-output comparison). Way back: revert the single change; legacy tolerance\nreturns.\n\n### Implementation decisions and open questions\n\n- The rejection mechanism is the main task's pending material decision; this\n  subtask executes whichever mechanism is approved (recommendation recorded\n  there: loud build error naming the file).\n- Adopted locally: the rejection test runs through the production build on a\n  temporary fixture \u2014 the real path, not a unit-level shim.\n- Open questions: none local.\n\n### Documentation\n\n- Same change as the flip: wherever 010 documented the author model, state\n  that the legacy single-name form is no longer accepted and describe what\n  happens when it is supplied. Audience unchanged: content authors and\n  maintainers of this fixture.\n\n### Task checklist\n\n- [ ] Re-confirm gate evidence (content scan, test run, baseline comparison\n  currency) and record it before the flip.\n- [ ] Remove the normalization fallback; implement the approved rejection.\n- [ ] Replace 010's legacy-equivalence test with the rejection-evidence test.\n- [ ] Build migrated content; confirm output identical to baseline.\n- [ ] Build the legacy fixture; confirm the approved observable outcome.\n- [ ] Update documentation; `npm test` collects and passes everything.\n\n### Requirement verification\n\n- Gate honored: dated Implementation-notes record of the step-1 evidence,\n  written before the flip \u2014 decisive for ordering.\n- Normalization removed: repo scan \u2014 no code path reads or maps the legacy\n  field.\n- Rejection works: production build of the legacy fixture produces the\n  approved observable outcome.\n- No regression: full-output comparison identical to 010's baseline;\n  `npm test` exits cleanly with all tests collected.\n\nDeliberately not covered: multi-author rendering (owned and evidenced by 010;\nunchanged here); tooling outside this repository (assumed none).\n\n### Additional implementation verification\n\n- After the flip, run one full production build of the pristine repository\n  state (no fixture input) and confirm the generated page set is exactly the\n  baseline set \u2014 guards against the rejection change accidentally excluding\n  or reordering pages.\n"
  },
  "task_tree": {
    "all_dependencies_resolve": true,
    "all_parent_links_resolve": true,
    "coordinating_files": [
      "tasks/20261102-multi-author-migration/000-main.md"
    ],
    "dependencies": [],
    "files": [
      {
        "dependencies": [],
        "has_execution_plan": false,
        "parent_task": null,
        "path": "tasks/20261102-multi-author-migration/000-main.md",
        "phase_terms": [],
        "plan_status": null,
        "requirement_count": 7,
        "title": "Structured multi-author migration"
      },
      {
        "dependencies": [],
        "has_execution_plan": false,
        "parent_task": "tasks/20261102-multi-author-migration/000-main.md",
        "path": "tasks/20261102-multi-author-migration/010-structured-author-adoption.md",
        "phase_terms": [],
        "plan_status": null,
        "requirement_count": 7,
        "title": "Structured author adoption"
      },
      {
        "dependencies": [],
        "has_execution_plan": false,
        "parent_task": "tasks/20261102-multi-author-migration/000-main.md",
        "path": "tasks/20261102-multi-author-migration/020-legacy-author-rejection.md",
        "phase_terms": [],
        "plan_status": null,
        "requirement_count": 5,
        "title": "Legacy author rejection"
      }
    ],
    "implementation_task_count": 2,
    "parent_links": [
      {
        "child": "tasks/20261102-multi-author-migration/010-structured-author-adoption.md",
        "parent": "tasks/20261102-multi-author-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20261102-multi-author-migration/020-legacy-author-rejection.md",
        "parent": "tasks/20261102-multi-author-migration/000-main.md",
        "resolves": true
      }
    ],
    "phase_named_files": [],
    "task_directory_count": 1,
    "task_file_count": 3
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
    "semantic_deliverable_count": 2,
    "actual_task_count": 2,
    "deliverable_mappings": [
      {
        "deliverable_id": "AUTHOR-D1",
        "task_paths": ["tasks/20261102-multi-author-migration/010-structured-author-adoption.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "One normalization accessor (posts.11tydata.js eleventyComputed) is the only legacy-aware code; model is documented; dual-format acceptance is proven by the legacy-equivalence production-pipeline test."
      },
      {
        "deliverable_id": "AUTHOR-D2",
        "task_paths": ["tasks/20261102-multi-author-migration/010-structured-author-adoption.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "post.njk and feed.xml.njk consume only `authors`; single-author equivalence and multi-author byline/feed rendering are each verified through real production builds with full baseline comparison; archives confirmed author-free and build-checked."
      },
      {
        "deliverable_id": "AUTHOR-D3",
        "task_paths": ["tasks/20261102-multi-author-migration/010-structured-author-adoption.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Both posts migrated with a zero-legacy content scan plus identical-output proof, and new-post.js emits the structured form; folding the single-collection content and one-script tooling into the combined working state loses no independently owned or deferrable result, matching the target's sanctioned combination."
      },
      {
        "deliverable_id": "AUTHOR-D4",
        "task_paths": ["tasks/20261102-multi-author-migration/020-legacy-author-rejection.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Retirement is a separate, deferred deliverable gated on re-confirmed content and generated-output evidence recorded before the flip, with rejection verified via a production build of a legacy fixture and baseline identity re-checked afterward."
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
    "partition_quality_score": 90,
    "handoff_quality_score": 92,
    "summary": "Two implementation tasks (000-main is coordinating and excluded) realize the target's four deliverables through its sanctioned alternative: 010 combines normalization, generated-surface adoption, and the single-collection content/tooling migration into one working state that ends fully migrated with legacy still tolerated — exactly the transition state the request requires — so the safe compatibility window the target's overpacking example warns about is preserved by keeping rejection separate. 020 delivers AUTHOR-4 as an independently deferrable, evidence-gated flip (Depends On 010, matching D4's dependency on D2+D3). All five outcomes are covered: documented single representation (AUTHOR-1), equivalence plus multi-author rendering across pages/feed with archives verified unaffected (AUTHOR-2), safe content and tooling migration (AUTHOR-3), gated retirement (AUTHOR-4), and per-milestone build-and-compare validity with stop-safe points (AUTHOR-5). The required production crossing is decisively checked at every migration state via real-content production builds with full baseline comparison and production-pipeline fixture builds, not mocks or helper-only tests, and the plan explicitly guards the empty-placeholder-test failure mode. No fragmentation, phase-only children, layer splits, evidence re-ownership, dependency defects, or piecewise evidence in any dimension; the only deviation from the target's 3-5 size range is the further merge of the small content/tooling migration, which costs no independent value."
  }
}
```
