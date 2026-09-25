# Session — tg06-eleventy-author-migration-decomposition · task-creation-assessment-gpt-max-s0 · glm max

- Run: `20260924T192635.014145Z-task-guidance-semantic-tg06-eleventy-author-migration-decomposition-gpt-max-s0-7ad526f9`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `b957b0ef2385376f…`)
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
        "task_paths": ["tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Contract definition and the single normalization/compatibility boundary are kept together with legacy acceptance and its own real-build check; no parser/schema split from the compatibility delivery."
      },
      {
        "deliverable_id": "AUTHOR-D2",
        "task_paths": ["tasks/20260919-author-metadata-migration/030-template-archive-and-feed-migration.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Post layout, shared archive/list template, and feed move to the normalized model in one task; routes and sitemap preservation are owned here rather than split per surface."
      },
      {
        "deliverable_id": "AUTHOR-D3",
        "task_paths": ["tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Content conversion and the authoring helper stay in one owned task with safe serialization, matching the target's acceptable alternative rather than splitting content from tooling."
      },
      {
        "deliverable_id": "AUTHOR-D4",
        "task_paths": ["tasks/20260919-author-metadata-migration/040-generated-output-and-content-evidence.md", "tasks/20260919-author-metadata-migration/050-legacy-retirement-and-documentation.md"],
        "coverage": "complete",
        "coherence": "fragmented",
        "reason": "Evidence gathering (040) is a separate horizontal task before conditional retirement plus documentation (050); the target folds direct evidence inside the retirement deliverable 'retire after evidence'."
      }
    ],
    "mergeable_groups": [
      {
        "task_paths": ["tasks/20260919-author-metadata-migration/040-generated-output-and-content-evidence.md", "tasks/20260919-author-metadata-migration/050-legacy-retirement-and-documentation.md"],
        "reason": "040's inventory and green/red gate exist only to authorize 050's conditional rejection; the target's D4 bundles evidence with retirement. Per-surface build assertions in 040 can return to 010/020/030, which already produce their own verification, leaving one coherent retirement deliverable and exactly the target's four-task partition."
      }
    ],
    "unmatched_tasks": ["tasks/20260919-author-metadata-migration/040-generated-output-and-content-evidence.md"],
    "overpacked_tasks": [],
    "valid_layer_boundaries": [
      "tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md",
      "tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md",
      "tasks/20260919-author-metadata-migration/030-template-archive-and-feed-migration.md",
      "tasks/20260919-author-metadata-migration/050-legacy-retirement-and-documentation.md"
    ],
    "automatic_layer_fragments": [],
    "dependency_issues": [],
    "crossing_ownership": "complete",
    "fragmentation_severity": "low",
    "fragmentation_ratio": 1.25,
    "quality_metrics": {
      "fragmentation": {
        "status": "low",
        "occurrences": [
          {
            "task_paths": ["tasks/20260919-author-metadata-migration/040-generated-output-and-content-evidence.md", "tasks/20260919-author-metadata-migration/050-legacy-retirement-and-documentation.md"],
            "description": "The retirement deliverable is split into a horizontal build-test/review task (040) and the retirement task (050), producing 5 tasks for 4 coherent working states (ratio 1.25). The count still falls inside the acceptable 3-5 band, and the other four deliverables are each single coherent tasks with no per-surface or per-test-type splits."
          }
        ]
      },
      "phase_only_children": {
        "status": "present",
        "occurrences": [
          {
            "task_paths": ["tasks/20260919-author-metadata-migration/040-generated-output-and-content-evidence.md"],
            "description": "040 is a verification child whose green/red evidence record only completes the retirement delivery (050); beyond 020+030 it changes no user-facing state, and 030/020 already hand their route/output observations and content inventory to it."
          }
        ]
      },
      "layer_split_without_independent_value": {
        "status": "none",
        "occurrences": []
      },
      "evidence_reownership": {
        "status": "present",
        "occurrences": [
          {
            "task_paths": ["tasks/20260919-author-metadata-migration/040-generated-output-and-content-evidence.md"],
            "description": "040 re-owns generated-output verification that belongs with outcome-delivery children: 030's checklist already adds generated-output assertions and passes route/output observations to 040, 020 produces the content inventory for 040, and 010's legacy-build and contract evidence is consumed by 040, centralizing AUTHOR-2/AUTHOR-5 verification in a final integration child."
          }
        ]
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
    "partition_quality_score": 82,
    "handoff_quality_score": 85,
    "summary": "The partition realizes the target's four working-state deliverables almost exactly: 010 is D1 (contract plus one normalization/compatibility boundary, not a parser/schema split), 030 is D2 (post layout, shared archive/list, and feed moved together rather than one task per surface), 020 is D3 (content and authoring helper kept under one owner), and 050 is D4 (conditional retirement plus documentation as within-deliverable work). All five approved outcomes are covered with no added scope; mixed-form and malformed-input policy, archive bylines, and the deprecation window are held as open questions instead of silently adding scope. Dependencies match the target DAG (D1 feeds the independent D2/D3 pair, retirement follows both) with no broken intermediate state, since normalization keeps every intermediate revision building. The single deviation is 040, a horizontal evidence task that re-owns production-build verification and the retirement inventory the target folds into D4 and into the outcome children themselves; merging it into 050 (returning its per-surface assertions to their owning deliverables) yields exactly the target's four-task partition, which is within the acceptable size band. The required crossing is owned: 010, 030, and 040 each name real Eleventy production-build checks through normalization into posts, archives, and feeds, with 040 explicitly forbidding mock-away of the normalizer, and the legacy, migrated, and multi-author states are each covered, so crossing ownership is complete. Fragmentation is low (ratio 1.25), driven solely by the evidence-gate fragment."
  }
}
```
