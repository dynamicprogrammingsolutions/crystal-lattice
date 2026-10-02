# Session — tg06-eleventy-author-migration-decomposition · task-creation-assessment-gpt-max-s0 · glm max

- Run: `20260925T225259.713865Z-task-guidance-semantic-tg06-eleventy-author-migration-decomposition-gpt-max-s0-db508307`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `5c6e6f340a9f6097…`)
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
  "response": "Created a draft task structure for the author metadata migration. No templates, content, scripts, or tests were implemented or modified.\n\n- [Main task and execution plan]( /Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T221650.155557Z-task-guidance-tg06-eleventy-author-migration-decomposition-max-9f3f8621/workspace/tasks/20260926-author-metadata-migration/000-main.md )\n- [Canonical schema and transition compatibility]( /Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T221650.155557Z-task-guidance-tg06-eleventy-author-migration-decomposition-max-9f3f8621/workspace/tasks/20260926-author-metadata-migration/010-schema-compatibility.md )\n- [Templates, archives, feeds, and generated-output coverage]( /Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent/evaluation/task-guidance/gpt/runs/20260925T221650.155557Z-task-guidance-tg06-eleventy-author-migration-decomposition-max-9f3f8621/workspace/tasks/20260926-author-metadata-migration/020-rendering-output.md )\n- [Existing content and authoring tool migration]( /Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T221650.155557Z-task-guidance-tg06-eleventy-author-migration-decomposition-max-9f3f8621/workspace/tasks/20260926-author-metadata-migration/030-content-authoring.md )\n- [Evidence-gated legacy retirement]( /Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T221650.155557Z-task-guidance-tg06-eleventy-author-migration-decomposition-max-9f3f8621/workspace/tasks/20260926-author-metadata-migration/040-legacy-retirement.md )\n\nThe plan keeps all tasks in `Draft` status and records the material questions that need resolution before execution: the exact `authors` entry shape, archive byline behavior, conflicting-field validation, and whether the final state rejects or retains legacy `author` input. Verification was limited to repository inspection and task-structure checks; build and test commands were intentionally not run for this planning-only request.",
  "task_files": {
    "tasks/20260926-author-metadata-migration/000-main.md": "# Migrate post author metadata to structured multi-author data\n\nPlan the staged migration of post author front matter from the current scalar\n`author` value to an ordered structured author collection. The migration must\nkeep existing content and generated pages working while the new model is\nintroduced, then use content and production-build evidence before any legacy\nrejection is enabled.\n\n## Requirements checklist\n\n- [ ] Define and implement an approved canonical multi-author data contract,\n  including its ordering, rendering shape, and validation rules.\n- [ ] Preserve the current behavior of existing posts and generated routes\n  while both the canonical model and the legacy `author` form may be present\n  during migration.\n- [ ] Move post templates, archive/list surfaces, and feeds to consume the\n  canonical author model; support multiple authors without emitting missing,\n  duplicated, or malformed author data.\n- [ ] Migrate every existing post to the canonical model without losing author\n  names or their intended order.\n- [ ] Update the authoring tool so newly generated front matter uses the\n  canonical model and can represent the approved single- and multi-author\n  cases safely.\n- [ ] Produce generated-output and content evidence showing that no supported\n  path still depends on the legacy form before rejecting it, if rejection is\n  selected as the final compatibility state.\n- [ ] Keep maintained developer/authoring documentation aligned with the\n  supported front-matter model and the transition or final rejection state.\n\n## Scope and workstreams\n\nThe migration is split by independently owned boundaries:\n\n- The data-contract work owns the canonical representation and the one\n  compatibility normalization boundary.\n- The rendering work owns post pages, shared list/archive surfaces, feeds, and\n  generated-output assertions.\n- The content/authoring work owns existing source posts, the post-generation\n  helper, and the real production-path check connecting generated front matter\n  to Eleventy output.\n- The retirement work owns the evidence gate and the final decision to retain\n  compatibility or reject the legacy form.\n\nThis plan does not authorize implementation. The task files remain `Draft`\nuntil execution is explicitly approved.\n\n## Requirement questions and decisions\n\n- **Question \u2014 canonical entry shape:** Should `authors` be an ordered list of\n  display-name strings, or an ordered list of records such as `{ name }` with\n  room for identity/link metadata? The plan uses \u201cordered author collection\u201d\n  until this is answered and does not invent identity, URL, or attribution\n  semantics.\n- **Question \u2014 archive presentation:** The current shared `postslist.njk`\n  renders titles and links but no author. Does \u201carchives move to the new\n  model\u201d require adding archive bylines, or should existing archive markup be\n  preserved while all author-aware archive code is audited to use the\n  canonical collection? The plan currently preserves existing visible output\n  unless a byline requirement is approved.\n- **Question \u2014 final compatibility state:** Should the completed migration\n  reject legacy `author` input, or retain a read fallback indefinitely?\n  Recommendation: make rejection a final, explicit phase only after the gate\n  passes; if indefinite compatibility is preferred, document that state and\n  retain the normalizer.\n- **Question \u2014 conflicting fields:** What should happen when a source item\n  contains both the canonical field and legacy `author`, or contains an empty\n  or malformed author collection? This needs an explicit validation policy\n  before implementation so precedence is not silently invented.\n- **Decision required by the request:** No legacy rejection may be introduced\n  before both the content audit and the generated-output evidence pass.\n\n## Research and supporting facts\n\n- The site is a compact Eleventy build. `package.json` exposes `npm run build`\n  and `npm test`; the production output is `_site/`.\n- `content/posts/posts.json` applies `layouts/post.njk` and the `posts` tag to\n  all posts. The existing posts use scalar `author` front matter in\n  `content/posts/first.md` and `content/posts/second.md`.\n- `_includes/layouts/post.njk` reads `author` directly. The feed template\n  reads `post.data.author` directly.\n- `content/blog.njk`, `content/index.njk`, and `content/tag-pages.njk` all\n  reach the shared `_includes/postslist.njk`. That include currently emits\n  only title links, so archive compatibility needs an explicit audit rather\n  than an assumed author rendering change.\n- `content/sitemap.xml.njk` does not read author data, but it is part of the\n  generated-page regression surface and should remain buildable.\n- `scripts/new-post.js` currently accepts `(title, author)` and writes a scalar\n  `author` key. Its output is not currently covered by a substantive test.\n- `tests/archive-output.test.js` and `tests/author-output.test.js` are\n  placeholders describing intended generated-output coverage rather than\n  executable assertions.\n- There is no existing `tasks/` tree and no root `docs/index.md`. The\n  maintained development documentation is under `docs/development/`; the\n  documentation guidance has been read before planning this change.\n\n## Subtasks\n\n- [ ] [tasks/20260926-author-metadata-migration/010-schema-compatibility.md](tasks/20260926-author-metadata-migration/010-schema-compatibility.md)\n- [ ] [tasks/20260926-author-metadata-migration/020-rendering-output.md](tasks/20260926-author-metadata-migration/020-rendering-output.md)\n- [ ] [tasks/20260926-author-metadata-migration/030-content-authoring.md](tasks/20260926-author-metadata-migration/030-content-authoring.md)\n- [ ] [tasks/20260926-author-metadata-migration/040-legacy-retirement.md](tasks/20260926-author-metadata-migration/040-legacy-retirement.md)\n\n## Requirement ownership\n\n- The canonical data contract and transition compatibility requirements are\n  owned by `010-schema-compatibility.md`; the final compatibility state is\n  completed jointly with `040-legacy-retirement.md`.\n- The post, archive/list, feed, and generated-page requirements are owned by\n  `020-rendering-output.md`.\n- Existing-source migration and authoring-tool requirements are owned by\n  `030-content-authoring.md`, with its production-output connection verified\n  through `020-rendering-output.md`.\n- The evidence gate, conditional legacy rejection, and final documentation\n  state are owned by `040-legacy-retirement.md`, using the preceding\n  subtasks\u2019 build evidence.\n\n## Execution plan\nStatus: Draft\n\nThe migration will use a staged compatibility flow. A single page-data\nnormalizer will expose the approved canonical author collection to every\nconsumer. During the transition it may translate legacy `author` into a\nsingle-entry canonical collection, but templates and tools will not duplicate\nthat fallback logic. Existing posts will be converted before the compatibility\npath is considered for removal.\n\nThe canonical collection is an ordered interface: order in front matter must\nbe retained in post bylines, archive bylines if approved, and feed output.\nThe exact entry shape and conflict policy are open requirements questions above.\nSingleton output should preserve current visible text, markup, routes, and\nfeed meaning wherever possible; multi-author output must be deterministic and\nvalid for the selected output format.\n\nThe work proceeds in this order:\n\n1. Resolve the canonical `authors` shape, conflict behavior, and output\n   semantics, then implement the shared compatibility/normalization boundary.\n2. Update the post layout, shared archive/list path, and feed to consume only\n   normalized authors. Replace the placeholder generated-output coverage with\n   assertions for a legacy-compatible singleton, a canonical singleton, and a\n   multi-author post.\n3. Migrate all current post front matter and update `new-post.js` to emit the\n   canonical field. Connect the authoring helper to the real Eleventy path by\n   building content generated from the helper and checking the resulting post\n   and feed, rather than testing serialization in isolation only.\n4. Run the content inventory and clean production build. Review every remaining\n   runtime reference to `author`; classify intentional compatibility fixtures\n   separately from supported content and consumers.\n5. Only after the evidence gate passes, apply the approved final compatibility\n   state: either remove the fallback and reject legacy input with a clear\n   diagnostic, or retain the fallback and document it as supported. Run the\n   full build and tests again after that state change.\n\nThe parent build check must exercise the real Eleventy input, collection,\ntemplate, feed, and output directories together. A mocked `post.data` object\nor a template-only unit test is not sufficient evidence that the migration\nworks end to end.\n\n### Implementation decisions and open questions\n\n- The working field name is `authors`, pending confirmation of the exact\n  scalar-versus-record entry shape.\n- Normalization belongs at the page/collection data boundary so raw legacy\n  access does not spread across templates.\n- Archive bylines and the final rejection policy remain requirement decisions,\n  not implementation assumptions.\n- If implementation reveals an additional public-contract choice, return the\n  plan to `Draft` and record the choice before executing that part.\n\n### Documentation\n\nUpdate `docs/development/index.md` or a more focused document under\n`docs/development/` only if the authoring contract needs more room than the\nexisting index. Document the canonical front-matter example, ordering and\nrendering semantics, the transition fallback if retained, and the evidence\ncondition for any rejection. Do not document the target as current guidance\nuntil the corresponding implementation and build evidence exist.\n\n### Task checklist\n\n- [ ] Resolve the requirement questions and mark the plan `Approved` before\n  implementation.\n- [ ] Complete `010-schema-compatibility.md`.\n- [ ] Complete `020-rendering-output.md`.\n- [ ] Complete `030-content-authoring.md`.\n- [ ] Complete `040-legacy-retirement.md`.\n- [ ] Review the final build, tests, content scan, and maintained\n  documentation together.\n\n### Requirement verification\n\n- **Canonical contract and safe transition:** Verify the approved canonical and\n  legacy inputs through the shared normalizer and a real Eleventy build. The\n  decisive evidence is that both input forms reach the same canonical\n  rendering/feed boundary without raw `author` reads in consumers.\n- **Templates, archives, feeds, and generated pages:** Run the production\n  build and inspect/assert the post page, home page, blog archive, tag page,\n  feed, and sitemap. Verify existing routes and singleton output remain valid\n  and that a multi-author source produces deterministic output.\n- **Existing content migration:** Scan all post source files for legacy\n  front-matter keys, inspect the migrated names/order, then build those exact\n  sources and assert their names appear in the expected generated outputs.\n- **Authoring tool:** Invoke `scripts/new-post.js` for approved one- and\n  multi-author inputs, use its generated front matter as real post input, run\n  Eleventy, and assert the generated post/feed output. This is the decisive\n  check for the helper-to-site connection.\n- **Evidence-gated legacy retirement:** Record the content scan, runtime\n  reference audit, pre-retirement generated-output results, and post-retirement\n  build/test results. A rejection change is complete only when all four are\n  clean; otherwise the compatibility fallback remains and the unresolved state\n  is documented.\n\n### Additional implementation verification\n\n- Check YAML/JSON escaping for names containing punctuation or quotes.\n- Check empty, duplicate, and malformed author entries according to the\n  approved validation policy.\n- Check that the migration does not create `[object Object]`, `undefined`,\n  duplicate feed authors, or empty bylines in generated output.\n- Check the final diff for accidental route, title, tag, or sitemap changes.",
    "tasks/20260926-author-metadata-migration/010-schema-compatibility.md": "# Define the canonical author schema and transition compatibility\n\nEstablish the single page-data contract that represents one or more post\nauthors and temporarily bridges existing scalar `author` front matter to that\ncontract. This task owns the compatibility boundary consumed by templates and\nauthoring tools.\n\nParent Task: tasks/20260926-author-metadata-migration/000-main.md\nDepends On: None\n\n## Requirements checklist\n\n- [ ] Record the approved canonical `authors` field name, entry shape, ordering,\n  and validation rules.\n- [ ] Provide one normalization boundary that exposes canonical authors to\n  consumers during the transition.\n- [ ] Preserve a legacy singleton author during the migration without\n  requiring templates or feeds to read the raw `author` field.\n- [ ] Define and test the behavior for canonical input, legacy input,\n  conflicting fields, empty values, and malformed entries according to the\n  approved policy.\n- [ ] Keep the compatibility behavior isolated so the final retirement task can\n  remove or retain it as one explicit state change.\n\n## Requirement questions and decisions\n\n- **Question:** Confirm whether canonical entries are ordered strings or\n  records, and whether identity/URL fields are in scope.\n- **Question:** Confirm precedence or rejection when both `authors` and\n  `author` are supplied.\n- **Recommendation:** Normalize legacy `author: \"Name\"` to a one-entry\n  collection and make all downstream consumers depend only on the normalized\n  value. Do not silently merge conflicting fields without an approved rule.\n\n## Research and supporting facts\n\n- Existing source files expose only scalar `author` values.\n- The post layout and feed currently read the legacy key independently, so\n  compatibility logic is currently duplicated at the consumer level by\n  implication.\n- Eleventy configuration is the natural ownership area for a shared\n  collection/page-data boundary, but the implementation should use the\n  project\u2019s actual data-cascade capabilities rather than scattering template\n  conditionals.\n\n## Execution plan\nStatus: Draft\n\nDefine the canonical author interface before changing any consumer. The\nnormalizer should accept the approved canonical collection and, while the\ntransition is active, translate a valid legacy scalar into the same internal\nshape. It should return enough information for templates and feeds to render\nnames in source order without knowing which input form supplied them.\n\nValidation and conflict behavior must be explicit. A source item with both\nfields, an empty collection, or an invalid entry must follow the approved\npolicy and produce an actionable diagnostic if rejection is the chosen\nbehavior. The normalizer must not make the final legacy-rejection decision\nitself; that decision belongs to the evidence-gated retirement task.\n\nAdd focused coverage for normalization and an integration fixture that sends\nthe normalized value through at least one real post render. Keep the\ncompatibility fixture available for the transition tests, but mark it as\nintentional so the final source audit can distinguish it from a supported\ncontent dependency.\n\n### Implementation decisions and open questions\n\n- The exact canonical entry shape and conflict policy are blocked on the\n  parent requirement questions.\n- The normalizer\u2019s public result should be stable enough that templates,\n  feed generation, and the authoring helper share one representation.\n- Do not remove legacy support in this task; the retirement task owns that\n  compatibility-state change.\n\n### Documentation\n\nContribute the canonical front-matter example and transition semantics to the\nmaintained development documentation after the shape is approved. Avoid\nclaiming that legacy input is rejected until the final gate passes.\n\n### Task checklist\n\n- [ ] Resolve and record the schema and validation decisions.\n- [ ] Implement the shared normalization boundary during execution.\n- [ ] Add canonical, legacy, conflict, and malformed-input evidence.\n- [ ] Prove one normalized value reaches a real Eleventy-rendered page.\n- [ ] Hand off the stable interface to the rendering and content/authoring\n  subtasks.\n\n### Requirement verification\n\n- Verify canonical and legacy fixtures through the actual page-data path and a\n  real Eleventy build; do not rely only on a helper-level mock.\n- Assert that downstream output receives an ordered canonical collection and\n  contains no raw legacy fallback branch in the template/feed consumers.\n- Verify invalid or conflicting inputs according to the approved policy and\n  preserve the diagnostics needed by the final retirement audit.\n\n### Additional implementation verification\n\n- Use names with punctuation, quotes, and non-ASCII characters.\n- Verify author order survives normalization unchanged.\n- Verify a single legacy name produces exactly one canonical entry.",
    "tasks/20260926-author-metadata-migration/020-rendering-output.md": "# Move rendering surfaces to canonical authors and prove generated output\n\nUpdate the production templates and generated-output coverage so post pages,\narchive/list surfaces, feeds, and related generated pages consume the\ncanonical author model without changing existing routes or singleton meaning.\n\nParent Task: tasks/20260926-author-metadata-migration/000-main.md\nDepends On: tasks/20260926-author-metadata-migration/010-schema-compatibility.md\n\n## Requirements checklist\n\n- [ ] Make the post layout render the canonical author collection with\n  deterministic, valid singleton and multi-author output.\n- [ ] Audit `content/blog.njk`, `content/index.njk`, `content/tag-pages.njk`,\n  and `_includes/postslist.njk`; any author presentation or data access uses\n  canonical authors, while existing title/link output remains compatible\n  unless archive bylines are approved.\n- [ ] Make the feed emit the approved representation for every author and\n  preserve the existing singleton feed meaning.\n- [ ] Keep the home page, blog archive, tag pages, post routes, feed, and\n  sitemap buildable with no missing or legacy-dependent author data.\n- [ ] Replace the placeholder archive and author-output test files with\n  executable generated-output evidence.\n\n## Requirement questions and decisions\n\n- **Question:** Confirm whether archive/list pages should gain visible\n  bylines. Until confirmed, the migration audits their shared path and\n  preserves its current title/link markup.\n- **Question:** Confirm the feed representation for multiple authors (for\n  example, repeated author elements or another schema-compatible form).\n- **Recommendation:** Preserve the current singleton markup/feed meaning and\n  extend it deterministically for multiple authors without changing routes.\n\n## Research and supporting facts\n\n- `_includes/layouts/post.njk` currently prints one raw `author` value.\n- `content/feed.xml.njk` currently emits one `<author>` element from\n  `post.data.author`.\n- The three archive-like entry points share `_includes/postslist.njk`, which\n  currently renders only links and titles.\n- `content/sitemap.xml.njk` has no author dependency but should be included in\n  the build regression because a template/data failure can affect the full\n  generated site.\n- Existing output tests contain comments only and do not currently assert\n  routes, content, or feed values.\n\n## Execution plan\nStatus: Draft\n\nAfter the normalization boundary is available, update every author-aware\nconsumer to read the canonical collection. Keep presentation logic\nconsistent between the post layout and feed, and make the multi-author\nseparator or element structure an explicit part of the approved output\ncontract. Do not add archive markup solely to create a test if the archive\nbyline question is not approved; do verify that the shared list path does not\nread the legacy field.\n\nBuild representative content through the real Eleventy configuration:\ninclude a migrated singleton, a canonical multi-author post, and a\ntransition-era legacy fixture while compatibility is active. Assert the\nresulting post page, home page, blog archive, tag page, feed, and sitemap.\nReplace the current placeholder tests with checks against `_site/`, keeping\nthe build boundary intact.\n\nUse the generated-output assertions to compare the existing singleton\nmeaning, not just to check that files exist. The multi-author assertions must\ncatch missing authors, duplicate authors, object serialization, and ordering\nregressions.\n\n### Implementation decisions and open questions\n\n- Archive byline behavior and feed syntax remain blocked on parent decisions.\n- The shared include should remain the ownership point for any list-level\n  author presentation so home, archive, and tag pages cannot drift.\n- Generated output is the decisive interface; a template test with fabricated\n  `post.data` is supporting evidence only.\n\n### Documentation\n\nDocument visible byline and feed behavior in the maintained development\ndocumentation once the output contract is approved. Include route/output\ncompatibility notes only when verified by the production build.\n\n### Task checklist\n\n- [ ] Resolve archive and feed output decisions.\n- [ ] Update the post layout and feed to use canonical authors.\n- [ ] Audit/update the shared home/archive/tag list path.\n- [ ] Replace placeholder tests with generated-output assertions.\n- [ ] Run the real Eleventy build and inspect all required generated surfaces.\n- [ ] Record route and singleton-output comparison evidence for the parent gate.\n\n### Requirement verification\n\n- Run the production build with singleton and multi-author content and assert\n  post, home, blog, tag, feed, and sitemap outputs.\n- Assert the exact author names and order in the generated post/feed surfaces,\n  and assert no `undefined`, `[object Object]`, empty byline, or duplicate\n  author output is produced.\n- Verify existing route paths and singleton presentation remain compatible.\n- Use the shared list output as the decisive archive check, including the\n  approved byline behavior if that requirement is selected.\n\n### Additional implementation verification\n\n- Check HTML/XML escaping for author names containing special characters.\n- Check that a feed consumer would receive valid output for one and many\n  authors under the approved feed contract.\n- Check that unrelated titles, tags, pagination data, and sitemap URLs do not\n  change.",
    "tasks/20260926-author-metadata-migration/030-content-authoring.md": "# Migrate existing posts and update the authoring tool\n\nConvert all existing post sources to the canonical multi-author front matter\nand update `scripts/new-post.js` so new posts are authored in that model. This\ntask owns the source-content inventory and the authoring-helper-to-production\npath.\n\nParent Task: tasks/20260926-author-metadata-migration/000-main.md\nDepends On: tasks/20260926-author-metadata-migration/010-schema-compatibility.md\n\n## Requirements checklist\n\n- [ ] Migrate every existing post under the content input to the canonical\n  author field without losing names or their order.\n- [ ] Update the authoring helper API and serialization to emit the canonical\n  single- and multi-author forms safely.\n- [ ] Ensure generated front matter does not reintroduce the legacy `author`\n  key.\n- [ ] Prove that front matter emitted by the authoring helper can enter the\n  real Eleventy content pipeline and produce correct post and feed output.\n- [ ] Record a source-content inventory and clean scan that the retirement\n  task can use as evidence.\n\n## Requirement questions and decisions\n\n- **Question:** Confirm the authoring helper\u2019s final input API once the\n  canonical entry shape is approved (an array, records, or another explicit\n  collection interface).\n- **Question:** Confirm whether a one-author convenience input remains\n  supported by the helper while always serializing the canonical collection.\n- **Recommendation:** Keep the helper\u2019s output deterministic and use a real\n  YAML serializer or equivalent escaping strategy rather than interpolating\n  unescaped names into front matter.\n\n## Research and supporting facts\n\n- `content/posts/first.md` and `content/posts/second.md` are the current\n  source posts and both use scalar `author` front matter.\n- `scripts/new-post.js` exports `frontMatter(title, author)` and directly\n  interpolates both values into YAML.\n- There is no current executable test proving the helper output is valid\n  front matter or that it reaches a built page.\n- The build consumes `content/` directly, so a generated fixture can exercise\n  the helper and production Eleventy path without mocking page data.\n\n## Execution plan\nStatus: Draft\n\nInventory all post source files before editing and record each legacy value and\nits intended order. Apply the canonical field to every existing post, review\nthe diff for title/body/tag/permalink changes, and run a source scan that\ntargets front-matter keys rather than incidental prose mentions.\n\nUpdate `frontMatter` to accept the approved author collection and serialize it\nas valid, escaped front matter. Cover both the convenience single-author case\nand multiple authors if the API decision permits the convenience form. Keep\nthe function\u2019s output free of the legacy key so newly authored content cannot\nextend the transition accidentally.\n\nFor the decisive integration check, invoke the helper to create front matter\nfor a temporary or dedicated test post, place that post through the same\nEleventy input pipeline used by production, run the real build, and assert the\npost and feed output. Clean up temporary/generated fixtures according to the\ntest harness so `_site/` and the committed content set remain controlled.\n\n### Implementation decisions and open questions\n\n- The helper API depends on the canonical author entry shape from subtask 010.\n- The migration should preserve source order and values; it should not\n  normalize names by sorting or rewriting them without approval.\n- Whether a committed fixture or an isolated integration fixture is best can\n  be decided locally, provided the check crosses the real content/build\n  boundary.\n\n### Documentation\n\nUpdate the maintained development authoring guidance with the canonical\nfront-matter example, helper input contract, and one/many-author examples.\nState the transition fallback or final rejection only after the retirement\ngate establishes that state.\n\n### Task checklist\n\n- [ ] Inventory every post source and capture legacy values/order.\n- [ ] Resolve the helper API and serialization decisions.\n- [ ] Migrate all existing post front matter.\n- [ ] Update helper coverage for valid singleton and multi-author output.\n- [ ] Run the helper-to-Eleventy integration check and inspect post/feed\n  output.\n- [ ] Run the clean content scan and hand its evidence to the retirement\n  task.\n\n### Requirement verification\n\n- Scan the complete content input for legacy front-matter keys and confirm\n  every post has the canonical field with the expected names/order.\n- Invoke the authoring helper, use its emitted front matter as real Eleventy\n  input, run the production build, and assert the resulting post and feed.\n  This is the decisive check for the authoring tool.\n- Verify special characters and multiple names remain valid and intact after\n  serialization and rendering.\n\n### Additional implementation verification\n\n- Review the migration diff for accidental changes to title, body, tags,\n  permalink, or layout data.\n- Check that helper output cannot create malformed YAML from quotes, colons,\n  or newline characters.\n- Check that temporary integration content cannot be mistaken for committed\n  production content.",
    "tasks/20260926-author-metadata-migration/040-legacy-retirement.md": "# Close the transition with an evidence-gated legacy decision\n\nOwn the final compatibility state. Assemble source and generated-output\nevidence from the preceding work, then either remove the legacy fallback and\nreject `author` input or explicitly retain it as supported. No rejection is\nallowed before the gate passes.\n\nParent Task: tasks/20260926-author-metadata-migration/000-main.md\nDepends On:\n- tasks/20260926-author-metadata-migration/020-rendering-output.md\n- tasks/20260926-author-metadata-migration/030-content-authoring.md\n\n## Requirements checklist\n\n- [ ] Do not reject legacy input while any supported content, template, feed,\n  archive, or authoring path still depends on it.\n- [ ] Assemble content-scan, runtime-reference, and generated-output evidence\n  proving the canonical model is used throughout the supported site.\n- [ ] Apply the approved final state only after the evidence gate passes:\n  remove the fallback and reject legacy input with a clear diagnostic, or\n  retain the fallback and document it as supported.\n- [ ] Run the production build and executable tests again after the final state\n  is selected.\n- [ ] Leave maintained documentation consistent with the resulting\n  compatibility state.\n\n## Requirement questions and decisions\n\n- **Question:** Confirm whether this migration will end by rejecting legacy\n  `author` or by retaining a documented compatibility fallback.\n- **Recommendation:** Prefer explicit rejection after a clean gate if the\n  project wants to prevent regression, but do not make that choice silently.\n- **Decision required by the request:** The gate must include both source\n  content evidence and generated-output evidence; a repository search alone is\n  insufficient.\n\n## Research and supporting facts\n\n- Existing content currently contains the legacy key, so source migration must\n  precede any rejection.\n- The post layout and feed are current legacy consumers; archive/list surfaces\n  require an explicit audit because their shared include currently renders\n  only titles and links.\n- The existing generated-output tests are placeholders, so the gate must wait\n  for executable build assertions from the rendering and content subtasks.\n- Task files and documentation may mention the legacy field as historical or\n  transition information; the runtime/content audit must classify those\n  mentions rather than treating every textual occurrence as a product\n  dependency.\n\n## Execution plan\nStatus: Draft\n\nCollect the completed evidence from the schema, rendering, and\ncontent/authoring tasks. Before changing compatibility behavior, run a clean\ninventory over all post source files, inspect runtime references in templates,\nconfiguration, scripts, and tests, and run the real production build with the\ncanonical content. Confirm that the required post, home, archive, tag, feed,\nand sitemap outputs contain the expected values and no legacy-derived\nundefined or malformed data.\n\nTreat the gate as a checklist with an explicit recorded result:\n\n1. Every supported post source has the canonical field and no legacy\n   front-matter key.\n2. All supported consumers use normalized/canonical authors; any remaining\n   legacy reference is an intentional transition fixture, diagnostic, or\n   historical documentation.\n3. Generated-output assertions pass for singleton and multi-author content\n   across the real Eleventy build.\n4. The authoring helper emits only canonical front matter and its generated\n   content has passed through the production build.\n\nOnly after all four conditions pass may the chosen final state be applied. If\nrejection is selected, remove the compatibility fallback at the agreed\nboundary, add a focused negative assertion for legacy input, and run the\ncomplete build/tests again. If compatibility is retained, keep the fallback,\nadd no premature rejection, and document its supported scope and evidence\nrequirements for a later removal.\n\n### Implementation decisions and open questions\n\n- The final reject-versus-retain decision is still open.\n- A negative test is appropriate only if rejection is approved; it must not\n  cause the transition build to fail before the gate.\n- The final audit must distinguish intentional test fixtures from accidental\n  production dependencies.\n\n### Documentation\n\nUpdate the maintained development documentation with the final supported\nfield, authoring behavior, and compatibility state. If rejection is enabled,\ndocument the diagnostic and migration expectation; if fallback is retained,\ndocument that legacy input remains supported and why.\n\n### Task checklist\n\n- [ ] Receive and review the schema, rendering, and content/authoring evidence.\n- [ ] Run the complete content and runtime reference audit.\n- [ ] Run the clean generated-output gate across all required surfaces.\n- [ ] Resolve the final compatibility state.\n- [ ] Apply rejection only after the gate passes, if approved.\n- [ ] Re-run build/tests and update maintained documentation.\n- [ ] Hand the immutable evidence and any deferred compatibility decision to\n  the parent task.\n\n### Requirement verification\n\n- Record the exact content scan, runtime-reference classification, and\n  generated-output results before any legacy rejection.\n- If rejection is selected, run a post-gate negative check showing legacy\n  input is rejected at the approved boundary, followed by a clean production\n  build of all migrated content.\n- If fallback is retained, run the clean canonical build and verify that the\n  remaining compatibility path is intentional, isolated, and documented.\n- Verify that all required generated surfaces still build and that routes,\n  titles, tags, feed output, and sitemap output remain intact after the final\n  compatibility-state change.\n\n### Additional implementation verification\n\n- Search for raw legacy reads/writes in supported runtime paths after the final\n  state change.\n- Check diagnostics for actionable source location and field information.\n- Check that evidence and documentation do not accidentally present a\n  target-only rejection policy as current behavior before it is implemented."
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
        "title": "Migrate post author metadata to structured multi-author data"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260926-author-metadata-migration/000-main.md",
        "path": "tasks/20260926-author-metadata-migration/010-schema-compatibility.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Define the canonical author schema and transition compatibility"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260926-author-metadata-migration/000-main.md",
        "path": "tasks/20260926-author-metadata-migration/020-rendering-output.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Move rendering surfaces to canonical authors and prove generated output"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260926-author-metadata-migration/000-main.md",
        "path": "tasks/20260926-author-metadata-migration/030-content-authoring.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Migrate existing posts and update the authoring tool"
      },
      {
        "dependencies": [],
        "has_execution_plan": true,
        "parent_task": "tasks/20260926-author-metadata-migration/000-main.md",
        "path": "tasks/20260926-author-metadata-migration/040-legacy-retirement.md",
        "phase_terms": [],
        "plan_status": "Draft",
        "requirement_count": 5,
        "title": "Close the transition with an evidence-gated legacy decision"
      }
    ],
    "implementation_task_count": 4,
    "parent_links": [
      {
        "child": "tasks/20260926-author-metadata-migration/010-schema-compatibility.md",
        "parent": "tasks/20260926-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260926-author-metadata-migration/020-rendering-output.md",
        "parent": "tasks/20260926-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260926-author-metadata-migration/030-content-authoring.md",
        "parent": "tasks/20260926-author-metadata-migration/000-main.md",
        "resolves": true
      },
      {
        "child": "tasks/20260926-author-metadata-migration/040-legacy-retirement.md",
        "parent": "tasks/20260926-author-metadata-migration/000-main.md",
        "resolves": true
      }
    ],
    "phase_named_files": [],
    "task_directory_count": 1,
    "task_file_count": 5
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
    "actual_task_count": 4,
    "deliverable_mappings": [
      {
        "deliverable_id": "AUTHOR-D1",
        "task_paths": ["tasks/20260926-author-metadata-migration/010-schema-compatibility.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Owns the canonical schema, the single normalization boundary, legacy bridging, conflict/empty/malformed policy, and a real-build integration fixture; matches D1's value of safely accepting old and new content before consumers migrate."
      },
      {
        "deliverable_id": "AUTHOR-D2",
        "task_paths": ["tasks/20260926-author-metadata-migration/020-rendering-output.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Post layout, shared archive/list path, feed, and generated-output assertions kept in one delivery, avoiding the target's per-template fragmentation example while proving routes and singleton output stay compatible."
      },
      {
        "deliverable_id": "AUTHOR-D3",
        "task_paths": ["tasks/20260926-author-metadata-migration/030-content-authoring.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Content inventory/rewrite and the new-post helper are owned together with a decisive helper-to-production-build check, matching D3 and avoiding the split-without-ownership fragmentation example."
      },
      {
        "deliverable_id": "AUTHOR-D4",
        "task_paths": ["tasks/20260926-author-metadata-migration/040-legacy-retirement.md"],
        "coverage": "complete",
        "coherence": "coherent",
        "reason": "Evidence gate plus the explicit final compatibility state change (reject with diagnostic or documented retention), post-change build/tests, and documentation; matches D4's evidence-gated retirement."
      }
    ],
    "mergeable_groups": [],
    "unmatched_tasks": [],
    "overpacked_tasks": [],
    "valid_layer_boundaries": [
      "tasks/20260926-author-metadata-migration/010-schema-compatibility.md",
      "tasks/20260926-author-metadata-migration/020-rendering-output.md"
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
    "handoff_quality_score": 92,
    "summary": "The four implementation tasks map one-to-one onto the target's four compatible working states (dual-format normalization, normalized generated surfaces, content/tooling migration, evidence-gated retirement), matching the preferred partition and acceptable size range; 000-main.md is a coordinating parent and is excluded. Each child ends in an independently usable state (site accepts both forms; all public output on the canonical model; producers stop creating legacy data; gated final state change) and carries its own tests, documentation, and verification rather than horizontal test/docs/cleanup tasks. Dependencies mirror the target DAG (010 none; 020 and 030 on 010; 040 on 020+030), with 030 correctly parallel to 020. The required production crossing is named decisively: 010 sends canonical and legacy fixtures through the real page-data path and build, 020 asserts post, home, archive, tag, feed, and sitemap output from a real build including a transition-era legacy fixture, 030 pushes helper-emitted front matter through the production pipeline, and 040 re-gates all surfaces after the final state change; mocked or template-only evidence is explicitly disclaimed. No approved outcome is missing, no added obligations were identified, and all six issue dimensions are absent."
  }
}
```
