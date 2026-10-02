# Session — tg06-eleventy-author-migration-decomposition · task-creation-assessment-gpt-high-s0 · glm max

- Run: `20260925T204439.150147Z-task-guidance-semantic-tg06-eleventy-author-migration-decomposition-gpt-high-s0-d47e7682`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `53f4a54517bde943…`)
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
  "response": "Created a planning-only task structure for the author metadata migration:\n\n- [Main task]( /Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T201718.821229Z-task-guidance-tg06-eleventy-author-migration-decomposition-high-c5987d54/workspace/tasks/20260925-author-metadata-migration/000-main.md:1)\n- [Data contract and authoring]( /Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T201718.821229Z-task-guidance-tg06-eleventy-author-migration-decomposition-high-c5987d54/workspace/tasks/20260925-author-metadata-migration/010-data-contract-and-authoring.md:1)\n- [Public rendering surfaces]( /Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent/evaluation/task-guidance/gpt/runs/20260925T201718.821229Z-task-guidance-tg06-eleventy-author-migration-decomposition-high-c5987d54/workspace/tasks/20260925-author-metadata-migration/020-public-rendering-surfaces.md:1)\n- [Transition gate and documentation]( /Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T201718.821229Z-task-guidance-tg06-eleventy-author-migration-decomposition-high-c5987d54/workspace/tasks/20260925-author-metadata-migration/030-transition-gate-and-documentation.md:1)\n\nThe plan is `Draft` and execution has not started. It covers:\n\n- canonical structured author metadata;\n- authoring-tool output and existing-post migration;\n- post, home, archive, tag, and feed rendering;\n- generated-output and source-content evidence;\n- delayed legacy-field rejection/removal;\n- maintained developer documentation.\n\nThe plan records four material questions that need approval before implementation: the exact structured shape, archive presentation, transition normalization behavior, and the final legacy-field failure policy. No source files, content, templates, tests, or generated output were changed.",
  "task_files": {
    "tasks/20260925-author-metadata-migration/000-main.md": "# Migrate post author metadata to structured multi-author data\n\nPlan the migration from the single `author` front-matter string to a\nstructured representation that can express multiple authors while preserving\nexisting posts and generated output throughout the transition.\n\n## Requirements checklist\n\n- [ ] Establish and document one canonical structured multi-author metadata\n  contract for posts, including the representation of one author and multiple\n  authors.\n- [ ] Keep existing content and generated pages working during the transition\n  while the legacy single-name form still exists.\n- [ ] Move post pages, archive/list views, tag/home post lists, feeds, and any\n  shared templates that expose author data to the structured model.\n- [ ] Update the post-authoring tool to emit the canonical structured form and\n  define how its inputs represent one or more authors.\n- [ ] Migrate every existing post safely without losing author identity,\n  ordering, or other front matter.\n- [ ] Retire or reject the legacy form only after generated-output checks and\n  source-content evidence demonstrate that no supported path still depends on\n  it.\n- [ ] Update maintained developer/authoring documentation to describe the\n  supported form and the transition or rejection behavior.\n\n## Scope and workstreams\n\nThe work is split by independently reviewable ownership boundaries:\n\n- [ ] [tasks/20260925-author-metadata-migration/010-data-contract-and-authoring.md](010-data-contract-and-authoring.md)\n  owns the metadata contract, authoring tool, compatibility normalization, and\n  migration of the existing post corpus.\n- [ ] [tasks/20260925-author-metadata-migration/020-public-rendering-surfaces.md](020-public-rendering-surfaces.md)\n  owns post, archive/list, tag/home, and feed rendering of the structured\n  authors.\n- [ ] [tasks/20260925-author-metadata-migration/030-transition-gate-and-documentation.md](030-transition-gate-and-documentation.md)\n  owns the final evidence gate, legacy-form retirement/rejection, and\n  maintained authoring documentation.\n\n## Unresolved requirement questions\n\n- What is the exact structured value shape: an array of names, or an array of\n  author records with fields such as name, URL, or identifier? This changes the\n  authoring contract and generated markup, so it must be approved before\n  implementation.\n- In archive, home, and tag list views, should author names be displayed, and\n  if so, should they be plain text or links? The current shared list renders\n  titles only, while the request requires archive surfaces to move to the new\n  model.\n- During the transition, should legacy `author` be normalized as a temporary\n  fallback when `authors` is absent, or should migrated content be the only\n  supported input while a separate compatibility check reports stragglers?\n- Once the evidence gate passes, should an old `author` field fail the build\n  with a clear validation error, or should it remain accepted but deprecated?\n\n## Decisions\n\n- This is planning only; no implementation, content migration, generated\n  output, or test changes are authorized by this handoff.\n- The production Eleventy build is the decisive integration boundary. Unit\n  checks that inject already-normalized data cannot alone prove the migration.\n- The legacy form remains available to the compatibility path until the\n  generated-output and source-content evidence required by the user has\n  passed.\n- Existing author identity and ordering are preserved as migration invariants;\n  no author merge, deduplication, or identity enrichment is assumed.\n- Tests and documentation stay with the workstream that owns the behavior they\n  prove or describe; there is no standalone test-only or documentation-only\n  child.\n\n## Research and supporting facts\n\n- The production input directory is `content`, with shared templates under\n  `_includes`; Eleventy writes generated pages to `_site`.\n- Post metadata is inherited from `content/posts/posts.json`, and the current\n  post layout reads `author` directly.\n- The current feed reads `post.data.author` directly. The shared\n  `_includes/postslist.njk` is used by the home page, `/blog/`, and generated\n  tag pages, but currently renders titles only.\n- Existing content consists of `content/posts/first.md` and\n  `content/posts/second.md`, each with a quoted single-name `author` field.\n- `scripts/new-post.js` emits the legacy field and accepts one author argument.\n- The repository exposes `npm run build` and `npm test`; the current author\n  test file is a placeholder comment rather than an executable assertion.\n- Maintained development documentation currently consists of\n  `docs/development/index.md`; there is no `docs/index.md` and no existing\n  task directory.\n\n## Execution plan\n\nStatus: Draft\n\nThe migration should establish one canonical author data boundary before\nchanging presentation. Content and the authoring tool will converge on the\nsame structured value; a temporary normalization/compatibility layer will\nallow old content to render while migration evidence is collected. Templates\nwill consume normalized structured authors rather than branching independently\non legacy and new fields. The final workstream will scan source content and\nthe repository\u2019s author consumers, build the site through Eleventy, inspect\nthe relevant generated pages and feed, and only then remove or reject the\nlegacy field according to the approved policy.\n\nExecution order:\n\n1. Resolve the four requirement questions above and record the chosen schema,\n   archive presentation, compatibility behavior, and post-gate failure mode.\n2. Execute `010-data-contract-and-authoring.md`: implement the canonical\n   metadata contract, update the authoring tool, and migrate all existing\n   posts while preserving their content.\n3. Execute `020-public-rendering-surfaces.md`: update the shared post/list\n   templates and feed, then add output assertions that exercise the actual\n   Eleventy build.\n4. Execute `030-transition-gate-and-documentation.md`: run the complete\n   build and tests, inspect generated post/archive/tag/feed output, scan source\n   content and author consumers for legacy dependencies, and retire or reject\n   the old form only after those checks pass.\n5. Update the task checklists and requirement evidence as each boundary is\n   completed. Record any approved plan change before implementing it.\n\n### Implementation decisions and open questions\n\nThe unresolved questions above are material because they alter the metadata\nshape or public output and must be answered before the plan can become\nApproved. The recommended direction is a minimally structured ordered list\nwhose entries retain the author name, with additional fields added only if the\nrepository has a real consumer for them. The compatibility layer should be\ntemporary and explicit, and the post-gate behavior should produce a clear\nbuild-time error if rejection is chosen. These are recommendations, not\napproved requirements.\n\n### Documentation\n\nUpdate `docs/development/index.md`, or add one focused page under\n`docs/development/` only if the approved contract needs more room, to cover\nthe canonical front matter, authoring-tool input, migration compatibility, and\nthe condition under which the legacy field is rejected. Keep target-only\ntransition text visibly marked until implementation makes it current.\n\n### Task checklist\n\n- [ ] Resolve the material schema, archive presentation, compatibility, and\n  post-gate behavior questions.\n- [ ] Complete the data-contract and authoring workstream.\n- [ ] Complete the public-rendering workstream.\n- [ ] Complete the transition evidence, legacy retirement, and documentation\n  workstream.\n- [ ] Reconcile all requirement evidence and append immutable completion notes\n  after implementation is actually complete.\n\n### Requirement verification\n\n- Structured contract and authoring tool: decisive evidence is the updated\n  authoring-tool output plus migrated post front matter consumed by the real\n  Eleventy build.\n- Existing-content safety: decisive evidence is a clean build of every\n  migrated post with assertions that each original author and post remains in\n  the expected generated output.\n- Public surfaces: decisive evidence is one production build inspected by\n  executable assertions for a post page, `/blog/`, a generated tag page, and\n  `/feed/feed.xml`, covering every author in the approved order.\n- Legacy retirement: decisive evidence is the source-content and consumer scan\n  plus the same production build succeeding after the approved rejection or\n  removal is enabled. No mock-only check satisfies this gate.\n- Documentation: decisive evidence is review of the maintained development\n  documentation against the implemented contract and final transition state.\n\n### Additional implementation verification\n\n- Check that HTML/XML escaping remains correct for author names containing\n  characters meaningful to markup.\n- Check that zero, one, and multiple-author cases follow the approved\n  validation and rendering policy.\n- Check that the authoring tool\u2019s output is parseable front matter and that\n  unrelated title/content fields remain unchanged during migration.",
    "tasks/20260925-author-metadata-migration/010-data-contract-and-authoring.md": "# Establish structured author data and migrate authoring inputs\n\nDefine the canonical post metadata shape, make new-post authoring emit it,\npreserve a temporary compatibility path for existing legacy content, and\nmigrate the current post corpus without content loss.\n\n## Requirements checklist\n\n- [ ] Define the approved structured value for one or more authors, including\n  ordering and validation behavior.\n- [ ] Update `scripts/new-post.js` so newly created posts use the canonical\n  structured form and can represent the approved one- and multi-author cases.\n- [ ] Provide an explicit transition normalization path for legacy single-name\n  metadata until the final evidence gate.\n- [ ] Migrate every existing post to the canonical form while preserving\n  titles, body content, author identity, and author order.\n\nParent Task: tasks/20260925-author-metadata-migration/000-main.md\n\n## Unresolved requirement questions\n\n- Is the canonical value an ordered list of strings or an ordered list of\n  records? Do records require fields beyond `name`?\n- What should the authoring function accept for multiple authors: a list,\n  repeated arguments, or another input form?\n- What validation applies to an empty list, empty name, duplicate name, or\n  legacy `author` plus new `authors` supplied together?\n\n## Decisions\n\n- The migration must preserve source content; rewriting bodies or unrelated\n  front matter is out of scope.\n- Compatibility is temporary and must have a clearly identifiable removal or\n  rejection point in the final transition workstream.\n- The contract is shared with templates and cannot be finalized independently\n  of the approved public rendering semantics.\n\n## Research and supporting facts\n\n- `scripts/new-post.js` currently exposes `frontMatter(title, author)` and\n  writes `author: \"<name>\"`.\n- `content/posts/first.md` and `content/posts/second.md` are the complete\n  current corpus and each has one legacy author.\n- Eleventy reads post front matter directly; the existing repository has no\n  author schema module or validation helper.\n\n## Execution plan\n\nStatus: Draft\n\nAdd the approved structured metadata contract at the narrowest shared input\nboundary, then update the post generator and source files to use it. Keep\nlegacy normalization available while the public templates are being migrated.\nAvoid inventing author identity fields that have no current consumer. Make the\nconversion mechanical and reviewable so a diff can prove that bodies and\nunrelated metadata did not change.\n\n1. Record the approved shape and validation rules in this task and the\n   maintained development documentation.\n2. Implement the normalization/validation boundary used by production\n   rendering, including the temporary legacy fallback and its diagnostics.\n3. Update `scripts/new-post.js` and its focused tests for one and multiple\n   authors.\n4. Convert every existing post to the canonical field and inspect the diff\n   for preservation of title, body, and author order.\n5. Run the production build as a handoff check for the rendering workstream;\n   do not remove the legacy path yet.\n\n### Implementation decisions and open questions\n\nThe exact data shape and authoring API remain blocked on the parent task\u2019s\nmaterial questions. Once approved, resolve local formatting and helper-module\nchoices here, but do not change the public contract or rejection timing\nwithout updating the parent plan.\n\n### Documentation\n\nDocument the canonical front matter and `new-post.js` input in the maintained\ndevelopment authoring guidance. During the transition, label compatibility\nbehavior as transitional rather than presenting the legacy field as current\nauthoring guidance.\n\n### Task checklist\n\n- [ ] Resolve and record the canonical schema and validation policy.\n- [ ] Implement the shared normalization/validation boundary.\n- [ ] Update and test the authoring tool.\n- [ ] Migrate all existing posts and review the preservation diff.\n- [ ] Run a production-build handoff check without retiring legacy support.\n\n### Requirement verification\n\n- Canonical authoring output: call the real exported authoring function for\n  one and multiple authors, parse its front matter, and verify the canonical\n  structure and ordering.\n- Safe corpus migration: compare the migrated post bodies, titles, and\n  non-author front matter with their pre-migration values, then run the real\n  Eleventy build over all posts.\n- Compatibility: build a fixture or retained legacy post through the actual\n  Eleventy data path and verify it normalizes to the same structured shape;\n  this evidence must not remove the fallback.\n\n### Additional implementation verification\n\n- Verify malformed structured values produce the approved diagnostic rather\n  than silently dropping authors.\n- Verify the conversion does not alter line endings or content outside the\n  author metadata unless the repository\u2019s formatter requires it.",
    "tasks/20260925-author-metadata-migration/020-public-rendering-surfaces.md": "# Render structured authors across public surfaces\n\nMove all author-consuming templates and generated surfaces to the canonical\nmulti-author model while preserving the approved transition compatibility.\n\n## Requirements checklist\n\n- [ ] Render every author on individual post pages using the approved order\n  and presentation.\n- [ ] Move the shared archive/list path used by the home page, `/blog/`, and\n  tag pages to the structured model, with the approved author visibility and\n  link behavior.\n- [ ] Render every author in the feed using valid escaped XML and the approved\n  feed representation.\n- [ ] Ensure no template reads the legacy single-name field directly.\n\nParent Task: tasks/20260925-author-metadata-migration/000-main.md\nDepends On: tasks/20260925-author-metadata-migration/010-data-contract-and-authoring.md\n\n## Unresolved requirement questions\n\n- What exact author presentation is required in archive/list views, which\n  currently render only post titles?\n- Should post-page authors and feed authors expose only names, or approved\n  identity fields as links/attributes?\n- Is one feed `<author>` element containing multiple names acceptable, or does\n  the feed contract require one author element per author?\n\n## Decisions\n\n- The shared `_includes/postslist.njk` is the ownership point for the\n  home/archive/tag list behavior; duplicating author logic in each page is\n  out of scope.\n- The production build must be exercised with real migrated content; tests\n  that pass synthetic normalized data directly to a template are supporting\n  checks only.\n- Output escaping and stable author order are compatibility requirements for\n  generated HTML and XML.\n\n## Research and supporting facts\n\n- `_includes/layouts/post.njk` currently prints `author` directly.\n- `_includes/postslist.njk` is included by `content/index.njk`,\n  `content/blog.njk`, and `content/tag-pages.njk`, but currently prints only\n  title links.\n- `content/feed.xml.njk` currently reads `post.data.author` directly and\n  emits one `<author>` element per post.\n- `content/posts/posts.json` supplies the post layout and `posts` tag; no\n  author-specific collection or archive template exists.\n\n## Execution plan\n\nStatus: Draft\n\nConsume the normalized structured author data from the shared templates.\nImplement the approved display semantics once in the post layout/list include\nand once in the feed template, preserving the current URLs and page\ncollection behavior. Add executable generated-output assertions rather than\nonly template-string checks.\n\n1. Confirm the approved HTML and feed representation against the data\n   contract from subtask 010.\n2. Update the post layout and shared list include, then verify all callers:\n   home, blog archive, and tag pages.\n3. Update the feed template to represent all authors and escape names\n   correctly.\n4. Extend author-output and archive-output coverage to run a production build\n   and assert the public output for one- and multiple-author posts.\n5. Inspect generated output for absence of literal legacy-field rendering and\n   preservation of existing URLs.\n\n### Implementation decisions and open questions\n\nThe archive display and feed cardinality questions are material public-output\ndecisions and stay open until approved. Local choices such as loop structure\nand whitespace can be resolved during implementation. Any change to URLs,\nfeed location, or author identity semantics returns the parent plan to Draft.\n\n### Documentation\n\nRecord the public author rendering semantics in the development guidance if\nthey are relevant to people creating or reviewing posts. Do not document\ngenerated markup details that are not part of the approved contract.\n\n### Task checklist\n\n- [ ] Resolve public post, archive/list, and feed presentation.\n- [ ] Update the post layout and shared list include.\n- [ ] Update the feed template.\n- [ ] Add generated-output assertions for all relevant surfaces.\n- [ ] Verify URLs and escaping remain stable.\n\n### Requirement verification\n\n- Post and list rendering: run the real Eleventy build with representative\n  one- and multiple-author posts, then assert the generated post, home,\n  `/blog/`, and tag HTML contains all approved authors in order.\n- Feed rendering: inspect generated `/feed/feed.xml` and assert every author\n  appears in the approved XML structure with escaped markup.\n- Legacy template dependency: scan author-consuming templates and inspect the\n  generated output after the build; no direct legacy read or literal legacy\n  value may remain.\n\n### Additional implementation verification\n\n- Confirm a name containing `&`, `<`, or `>` is escaped correctly in both HTML\n  and XML contexts.\n- Confirm shared list behavior remains valid when a post has multiple\n  authors, including whitespace and separator behavior.",
    "tasks/20260925-author-metadata-migration/030-transition-gate-and-documentation.md": "# Close the compatibility transition and document the supported contract\n\nUse source-content and generated-output evidence to decide when the legacy\nsingle-name field can be retired or rejected, then update maintained\nauthoring guidance to match the completed migration.\n\n## Requirements checklist\n\n- [ ] Run the complete production build and relevant test suite against the\n  migrated corpus and structured authoring path.\n- [ ] Produce source-content evidence that no post still depends on the\n  legacy single-name field.\n- [ ] Produce consumer evidence that templates, feed generation, authoring\n  tools, and tests no longer depend on the legacy form.\n- [ ] Retire or reject the legacy form only after both generated-output and\n  content/consumer evidence pass.\n- [ ] Make the post-gate behavior explicit and diagnosable if a legacy field is\n  encountered.\n- [ ] Update maintained developer/authoring documentation to describe the\n  canonical form and final compatibility state.\n\nParent Task: tasks/20260925-author-metadata-migration/000-main.md\nDepends On: tasks/20260925-author-metadata-migration/010-data-contract-and-authoring.md\nDepends On: tasks/20260925-author-metadata-migration/020-public-rendering-surfaces.md\n\n## Unresolved requirement questions\n\n- Is the approved end state strict rejection of `author`, or continued\n  acceptance with a deprecation warning? The user permits rejection after\n  evidence but does not require it.\n- If strict rejection is chosen, should failure happen during front matter\n  normalization, Eleventy build evaluation, or a dedicated content check?\n- Which generated artifacts are the minimum evidence set for archive, tag,\n  post, and feed coverage if the build output contains additional pages?\n\n## Decisions\n\n- No legacy rejection may be enabled before the evidence gate passes.\n- Evidence must cross the production path: source content and consumers are\n  scanned, then Eleventy builds the site and generated artifacts are checked.\n- A passing mock or template unit test cannot substitute for generated-output\n  evidence.\n- Documentation must describe current supported behavior after completion; any\n  pre-completion target text must be visibly marked as not implemented.\n\n## Research and supporting facts\n\n- The current build writes to `_site`; `npm run build` is the repository\u2019s\n  production build command.\n- The repository\u2019s test command is `npm test`, but the author-output test is\n  currently only a placeholder comment and must become executable evidence.\n- Existing author consumers are discoverable in the post layout, feed\n  template, shared post list, authoring script, post front matter, and tests.\n- `docs/development/index.md` is the existing maintained development\n  documentation location.\n\n## Execution plan\n\nStatus: Draft\n\nTreat compatibility closure as a gated release step. First establish a\nbaseline inventory of legacy references, then run the completed structured\npath and inspect generated output. Only when migrated source content and all\nsupported consumers are clear should the implementation remove or reject the\nlegacy form. The final documentation update must be made in the same reviewed\nchange as the behavior it describes.\n\n1. Resolve the approved post-gate policy and failure location.\n2. Run `npm test` and `npm run build` with the migrated corpus, ensuring the\n   tests collect and exit successfully.\n3. Inspect generated post, home, blog archive, tag, feed, and metadata output\n   for author completeness, ordering, escaping, and absence of legacy values.\n4. Search source content, templates, scripts, configuration, and tests for\n   legacy `author` dependencies; classify any remaining occurrence as an\n   intentional compatibility check, documentation history, or a defect.\n5. After the generated-output and content/consumer evidence passes, remove the\n   fallback or enable the approved clear rejection behavior.\n6. Re-run the build, tests, and legacy scan after closure, then update\n   `docs/development/index.md` with the current supported contract and\n   transition state.\n\n### Implementation decisions and open questions\n\nThe strict-rejection versus deprecation choice and its failure boundary are\nmaterial and require approval. The recommended end state is explicit\nbuild-time rejection with a message naming the replacement field, because it\nprevents silent reintroduction of the legacy form; retain deprecation instead\nif compatibility with external unpublished content is a requirement. This\nrecommendation does not authorize either behavior.\n\n### Documentation\n\nUpdate `docs/development/index.md` with the canonical metadata example,\nauthoring-tool usage, supported one/multiple-author cases, migration\ncompatibility status, and the final legacy-field policy. Keep the guidance\nshort and developer-facing; do not create a placeholder documentation tree.\n\n### Task checklist\n\n- [ ] Resolve the final legacy policy and failure boundary.\n- [ ] Run baseline and post-migration production/test evidence.\n- [ ] Complete source-content and consumer scans.\n- [ ] Retire or reject the legacy form after the evidence gate.\n- [ ] Re-run all decisive checks after closure.\n- [ ] Update maintained documentation and reconcile parent requirement status.\n\n### Requirement verification\n\n- Generated-output evidence: `npm run build` followed by assertions over the\n  generated post, archive, tag, and feed artifacts proves the public path.\n- Content evidence: a repository scan proves every existing post uses the\n  canonical field and identifies every remaining legacy token.\n- Consumer evidence: a scan plus executable tests proves no template, authoring\n  tool, or maintained test still reads or emits the legacy field except for\n  explicitly approved rejection/compatibility coverage.\n- Rejection timing: the final diff and test order show that legacy rejection\n  was enabled only after the preceding build and scans passed; a legacy fixture\n  then demonstrates the approved diagnostic.\n- Documentation: inspect the final development guidance against the shipped\n  behavior and schema.\n\n### Additional implementation verification\n\n- Run a clean build after removing or rejecting compatibility to catch hidden\n  data-path assumptions.\n- Verify that generated output does not contain stale files from a prior\n  build when evaluating the evidence gate; clean or otherwise control the\n  output directory as part of the documented check.\n- Confirm the final error path points authors to the canonical structured\n  field without accepting both fields ambiguously."
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
        "requirement_count": 7,
        "title": "Migrate post author metadata to structured multi-author data"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260925-author-metadata-migration/000-main.md",
        "path": "tasks/20260925-author-metadata-migration/010-data-contract-and-authoring.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 4,
        "title": "Establish structured author data and migrate authoring inputs"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260925-author-metadata-migration/000-main.md",
        "path": "tasks/20260925-author-metadata-migration/020-public-rendering-surfaces.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 4,
        "title": "Render structured authors across public surfaces"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260925-author-metadata-migration/000-main.md",
        "path": "tasks/20260925-author-metadata-migration/030-transition-gate-and-documentation.md",
        "phase_terms": [
          "documentation"
        ],
        "plan_status": "Draft",
        "requirement_count": 6,
        "title": "Close the compatibility transition and document the supported contract"
      }
    ],
    "implementation_task_count": 3,
    "parent_links": [
      {
        "child": "tasks/20260925-author-metadata-migration/010-data-contract-and-authoring.md",
        "parent": "tasks/20260925-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260925-author-metadata-migration/020-public-rendering-surfaces.md",
        "parent": "tasks/20260925-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260925-author-metadata-migration/030-transition-gate-and-documentation.md",
        "parent": "tasks/20260925-author-metadata-migration/000-main.md",
        "resolves": true
      }
    ],
    "phase_named_files": [
      "tasks/20260925-author-metadata-migration/030-transition-gate-and-documentation.md"
    ],
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
        "task_paths": ["tasks/20260925-author-metadata-migration/010-data-contract-and-authoring.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "010 defines the canonical documented contract, implements the normalization/validation boundary with a temporary legacy fallback, and proves real front matter through the actual Eleventy data path; it merges D1 with D3 into one owned data-boundary state while legacy remains accepted until the gate."
      },
      {
        "deliverable_id": "AUTHOR-D2",
        "task_paths": ["tasks/20260925-author-metadata-migration/020-public-rendering-surfaces.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "020 owns post layout, the shared postslist include used by home/blog/tag, and the feed as one rendering deliverable, with production-build assertions over generated HTML and feed XML; not one task per template."
      },
      {
        "deliverable_id": "AUTHOR-D3",
        "task_paths": ["tasks/20260925-author-metadata-migration/010-data-contract-and-authoring.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "new-post.js is updated to emit the canonical form and the full two-post corpus is migrated with preservation diffs in the same boundary task; merging content/tooling migration with normalization is a coherent alternative consistent with the acceptable 3-task size."
      },
      {
        "deliverable_id": "AUTHOR-D4",
        "task_paths": ["tasks/20260925-author-metadata-migration/030-transition-gate-and-documentation.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "030 owns the evidence gate: content and consumer scans, production build with generated-artifact assertions, then retirement/rejection only after evidence, with the final documentation updated in the same reviewed change."
      }
    ],
    "mergeable_groups": [],
    "unmatched_tasks": [],
    "overpacked_tasks": [],
    "valid_layer_boundaries": [
      "tasks/20260925-author-metadata-migration/020-public-rendering-surfaces.md"
    ],
    "automatic_layer_fragments": [],
    "dependency_issues": [
      "010 completes the entire corpus migration to the canonical field while post.njk, feed.xml.njk, and postslist still read the legacy `author` value (they move only in 020). Between 010 and 020 the production build succeeds but generated pages and feed drop author rendering, which conflicts with the dual-format working state and AUTHOR-5; 010's normalization is only legacy→structured and does not synthesize a legacy-compatible view for not-yet-migrated templates.",
      "Otherwise the dependency graph matches the target: 020 correctly depends on 010 for the approved contract, and 030 depends on both 010 and 020 before the retirement gate; no missing or wrongly serialized dependencies beyond the window above."
    ],
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
        "status": "partial",
        "occurrences": [
          {
            "task_paths": [
              "tasks/20260925-author-metadata-migration/010-data-contract-and-authoring.md",
              "tasks/20260925-author-metadata-migration/020-public-rendering-surfaces.md"
            ],
            "description": "010 migrates all existing posts off the legacy field while every author-consuming template still reads `author` directly until 020, leaving an intermediate revision whose generated output loses author data; the plan should retain a legacy-compatible view (or defer corpus migration behind the normalization boundary) so each intermediate revision still publishes equivalent output."
          }
        ]
      },
      "piecewise_crossing_evidence": {
        "status": "none",
        "occurrences": []
      }
    },
    "partition_quality_score": 88,
    "handoff_quality_score": 90,
    "summary": "The set is a high-quality 3-task partition (000-main excluded as a coordinating file with no separately assigned implementation). Task 010 coherently merges target deliverables D1 and D3 — canonical contract, normalization fallback, authoring-tool update, and full corpus migration — leaving legacy acceptance until the gate, which fits the acceptable 3–5 size range; 020 and 030 map one-to-one to D2 and D4. All five outcomes are covered: normalization is documented (AUTHOR-1), pages/archives/tag lists/feed move to the normalized model (AUTHOR-2), content and tools migrate (AUTHOR-3), retirement is gated on content and consumer scans plus generated-output evidence (AUTHOR-4), and each boundary runs the production build (AUTHOR-5). The important crossing is owned decisively: 020 and 030 assert real front matter through the production Eleventy build into post, home, /blog/, tag, and feed artifacts, with synthetic-data tests explicitly demoted to supporting checks. No test-only, documentation-only, per-template, or per-layer children exist; tests and documentation stay inside the owning deliverables. The single material weakness is the 010→020 window where migrated content and legacy-reading templates mismatch, briefly breaking author rendering in generated output contrary to the dual-format working-state requirement; a legacy-compatible view during the transition would close it. Unresolved schema, archive-presentation, compatibility, and post-gate questions are correctly surfaced for approval rather than assumed, matching the target's open questions."
  }
}
```
