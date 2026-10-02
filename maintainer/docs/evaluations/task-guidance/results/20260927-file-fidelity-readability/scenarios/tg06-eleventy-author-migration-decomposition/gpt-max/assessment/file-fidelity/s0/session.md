# Session — tg06-eleventy-author-migration-decomposition · file-fidelity-assessment-gpt-max-s0 · glm max

- Run: `20260928T200006.049493Z-task-guidance-file-fidelity-tg06-eleventy-author-migration-decomposition-gpt-max-s0-742b5925`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `14d687ddecd42d42…`)
- Config: [glm-assessor-max](../../../../../../shared/configs/glm-assessor-max.json)
- Activity: 3 messages · 0 tool calls · 0 tool results
- Usage: unknown — saved session contains no provider usage metadata

## Transcript

**User**

Assess the task files one agent produced for a fixed scenario, together
with that agent's final conversation response. Judge whether the files
carry what a continuing agent and a human reviewer need: the decided
design, the conversation's durable context, content in the right
sections, a plan justified by planning that actually happened, and
acceptance evidence that fits the work's kind.

Grade these dimensions:

- `plan_design_completeness`: a reader of the implementation plan alone
  can reconstruct the decided design — component responsibilities,
  interfaces or data flow, compatibility and dependency states, material
  decisions, and how the requirements are verified. An ordered list of
  work steps without the design behind it is `poor`; covering some
  design elements is `partial`.
- `durable_context_preservation`: every approved outcome, material
  decision, verified fact with its source, and verification approach the
  conversation established appears in the task files — compressed, not
  dropped. Use `not checked here` only when the conversation established
  nothing durable.
- `section_appropriateness`: content sits where a continuing agent looks
  for it — outcomes and constraints in requirements, rationale and
  learned facts in supporting details, direction in the implementation
  plan, unresolved items in questions and decisions.
- `plan_justification`: the implementation plan reflects planning that
  actually happened. `justified` when the plan restates or organizes the
  conversation's planning; `not_applicable` when no plan section exists;
  `fabricated` when the plan asserts design detail the conversation
  never established.
- `task_kind_fit`: the file uses the sections the work needs and states
  acceptance evidence appropriate to the work's kind — tests for code,
  review acceptance for documentation, rollback and verification for
  operations, brief or style acceptance for content, recorded decisions
  for tracking work. `forced` when inapplicable sections are filled
  mechanically; `missing` when the work's own acceptance evidence is
  absent.

Every grade carries findings: concrete `{where, quote, why}` items
backing it. A non-top grade with empty findings is invalid. Then hunt
for mistakes explicitly — dropped facts, invented decisions or scope,
content a continuing agent would look for in the wrong place, missing
acceptance evidence — and list each as `{where, quote, why}` in
`mistakes`. Grades stay completeness judgments; the mistake hunt is
your search strategy, not a grade.

Do not reward verbosity or formatting of its own. Do not penalize
brevity that loses nothing. The target excerpt and the natural user
request define what is material.

Return JSON only:

{
  "schema_version": 1,
  "scenario_id": "tg06-eleventy-author-migration-decomposition",
  "assessment": {
    "dimensions": {
      "plan_design_completeness": {
        "grade": "complete|partial|poor",
        "findings": [{"where": "...", "quote": "...", "why": "..."}]
      },
      "durable_context_preservation": {"grade": "...", "findings": []},
      "section_appropriateness": {"grade": "...", "findings": []},
      "plan_justification": {
        "grade": "justified|not_applicable|fabricated",
        "findings": []
      },
      "task_kind_fit": {"grade": "fits|forced|missing", "findings": []}
    },
    "mistakes": [{"where": "...", "quote": "...", "why": "..."}],
    "summary": "concise evidence-based interpretation"
  }
}

Reviewed target excerpt:

# Eleventy author metadata migration decomposition

Partition a broad content/build migration by compatible working states rather than files and phases.

Category: decomposition

Approved outcomes:

- AUTHOR-1: Legacy single-author and structured one-or-more-author metadata normalize to one documented internal representation during migration.
- AUTHOR-2: Pages, archives, feeds, and metadata render equivalent single-author behavior and approved multi-author behavior from the normalized model.
- AUTHOR-3: Content and authoring tools migrate safely to the structured form.
- AUTHOR-4: Legacy form is retired only after no maintained source or generated surface depends on it.
- AUTHOR-5: Every intermediate revision builds and publishes valid output.

Open questions:

- Stable author identifier format and legacy deprecation period require approval.

Acceptable alternatives:

- Combine normalization and generated-surface adoption when a clear dual-format working state remains.
- Split content migration only for independently owned content collections.

Natural user request:

Migrate post author metadata from the current single-name field to a structured multi-author form without breaking existing content or generated pages during the transition. Templates, archives, feeds, and authoring tools must move to the new model, existing posts must be migrated safely, and the legacy form may be rejected only after generated-output and content evidence show that nothing still depends on it. Plan the work and create the appropriate task structure without implementing it.

The producer's final conversation response (the durable-context source
the files must preserve):

````markdown
Created a draft task structure for the author metadata migration. No templates, content, scripts, or tests were implemented or modified.

- [Main task and execution plan]( /Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T221650.155557Z-task-guidance-tg06-eleventy-author-migration-decomposition-max-9f3f8621/workspace/tasks/20260926-author-metadata-migration/000-main.md )
- [Canonical schema and transition compatibility]( /Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T221650.155557Z-task-guidance-tg06-eleventy-author-migration-decomposition-max-9f3f8621/workspace/tasks/20260926-author-metadata-migration/010-schema-compatibility.md )
- [Templates, archives, feeds, and generated-output coverage]( /Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent/evaluation/task-guidance/gpt/runs/20260925T221650.155557Z-task-guidance-tg06-eleventy-author-migration-decomposition-max-9f3f8621/workspace/tasks/20260926-author-metadata-migration/020-rendering-output.md )
- [Existing content and authoring tool migration]( /Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T221650.155557Z-task-guidance-tg06-eleventy-author-migration-decomposition-max-9f3f8621/workspace/tasks/20260926-author-metadata-migration/030-content-authoring.md )
- [Evidence-gated legacy retirement]( /Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent-evaluation/task-guidance/gpt/runs/20260925T221650.155557Z-task-guidance-tg06-eleventy-author-migration-decomposition-max-9f3f8621/workspace/tasks/20260926-author-metadata-migration/040-legacy-retirement.md )

The plan keeps all tasks in `Draft` status and records the material questions that need resolution before execution: the exact `authors` entry shape, archive byline behavior, conflicting-field validation, and whether the final state rejects or retains legacy `author` input. Verification was limited to repository inspection and task-structure checks; build and test commands were intentionally not run for this planning-only request.
````

The produced task files:

### tasks/20260926-author-metadata-migration/000-main.md

````markdown
# Migrate post author metadata to structured multi-author data

Plan the staged migration of post author front matter from the current scalar
`author` value to an ordered structured author collection. The migration must
keep existing content and generated pages working while the new model is
introduced, then use content and production-build evidence before any legacy
rejection is enabled.

## Requirements checklist

- [ ] Define and implement an approved canonical multi-author data contract,
  including its ordering, rendering shape, and validation rules.
- [ ] Preserve the current behavior of existing posts and generated routes
  while both the canonical model and the legacy `author` form may be present
  during migration.
- [ ] Move post templates, archive/list surfaces, and feeds to consume the
  canonical author model; support multiple authors without emitting missing,
  duplicated, or malformed author data.
- [ ] Migrate every existing post to the canonical model without losing author
  names or their intended order.
- [ ] Update the authoring tool so newly generated front matter uses the
  canonical model and can represent the approved single- and multi-author
  cases safely.
- [ ] Produce generated-output and content evidence showing that no supported
  path still depends on the legacy form before rejecting it, if rejection is
  selected as the final compatibility state.
- [ ] Keep maintained developer/authoring documentation aligned with the
  supported front-matter model and the transition or final rejection state.

## Scope and workstreams

The migration is split by independently owned boundaries:

- The data-contract work owns the canonical representation and the one
  compatibility normalization boundary.
- The rendering work owns post pages, shared list/archive surfaces, feeds, and
  generated-output assertions.
- The content/authoring work owns existing source posts, the post-generation
  helper, and the real production-path check connecting generated front matter
  to Eleventy output.
- The retirement work owns the evidence gate and the final decision to retain
  compatibility or reject the legacy form.

This plan does not authorize implementation. The task files remain `Draft`
until execution is explicitly approved.

## Requirement questions and decisions

- **Question — canonical entry shape:** Should `authors` be an ordered list of
  display-name strings, or an ordered list of records such as `{ name }` with
  room for identity/link metadata? The plan uses “ordered author collection”
  until this is answered and does not invent identity, URL, or attribution
  semantics.
- **Question — archive presentation:** The current shared `postslist.njk`
  renders titles and links but no author. Does “archives move to the new
  model” require adding archive bylines, or should existing archive markup be
  preserved while all author-aware archive code is audited to use the
  canonical collection? The plan currently preserves existing visible output
  unless a byline requirement is approved.
- **Question — final compatibility state:** Should the completed migration
  reject legacy `author` input, or retain a read fallback indefinitely?
  Recommendation: make rejection a final, explicit phase only after the gate
  passes; if indefinite compatibility is preferred, document that state and
  retain the normalizer.
- **Question — conflicting fields:** What should happen when a source item
  contains both the canonical field and legacy `author`, or contains an empty
  or malformed author collection? This needs an explicit validation policy
  before implementation so precedence is not silently invented.
- **Decision required by the request:** No legacy rejection may be introduced
  before both the content audit and the generated-output evidence pass.

## Research and supporting facts

- The site is a compact Eleventy build. `package.json` exposes `npm run build`
  and `npm test`; the production output is `_site/`.
- `content/posts/posts.json` applies `layouts/post.njk` and the `posts` tag to
  all posts. The existing posts use scalar `author` front matter in
  `content/posts/first.md` and `content/posts/second.md`.
- `_includes/layouts/post.njk` reads `author` directly. The feed template
  reads `post.data.author` directly.
- `content/blog.njk`, `content/index.njk`, and `content/tag-pages.njk` all
  reach the shared `_includes/postslist.njk`. That include currently emits
  only title links, so archive compatibility needs an explicit audit rather
  than an assumed author rendering change.
- `content/sitemap.xml.njk` does not read author data, but it is part of the
  generated-page regression surface and should remain buildable.
- `scripts/new-post.js` currently accepts `(title, author)` and writes a scalar
  `author` key. Its output is not currently covered by a substantive test.
- `tests/archive-output.test.js` and `tests/author-output.test.js` are
  placeholders describing intended generated-output coverage rather than
  executable assertions.
- There is no existing `tasks/` tree and no root `docs/index.md`. The
  maintained development documentation is under `docs/development/`; the
  documentation guidance has been read before planning this change.

## Subtasks

- [ ] [tasks/20260926-author-metadata-migration/010-schema-compatibility.md](tasks/20260926-author-metadata-migration/010-schema-compatibility.md)
- [ ] [tasks/20260926-author-metadata-migration/020-rendering-output.md](tasks/20260926-author-metadata-migration/020-rendering-output.md)
- [ ] [tasks/20260926-author-metadata-migration/030-content-authoring.md](tasks/20260926-author-metadata-migration/030-content-authoring.md)
- [ ] [tasks/20260926-author-metadata-migration/040-legacy-retirement.md](tasks/20260926-author-metadata-migration/040-legacy-retirement.md)

## Requirement ownership

- The canonical data contract and transition compatibility requirements are
  owned by `010-schema-compatibility.md`; the final compatibility state is
  completed jointly with `040-legacy-retirement.md`.
- The post, archive/list, feed, and generated-page requirements are owned by
  `020-rendering-output.md`.
- Existing-source migration and authoring-tool requirements are owned by
  `030-content-authoring.md`, with its production-output connection verified
  through `020-rendering-output.md`.
- The evidence gate, conditional legacy rejection, and final documentation
  state are owned by `040-legacy-retirement.md`, using the preceding
  subtasks’ build evidence.

## Execution plan
Status: Draft

The migration will use a staged compatibility flow. A single page-data
normalizer will expose the approved canonical author collection to every
consumer. During the transition it may translate legacy `author` into a
single-entry canonical collection, but templates and tools will not duplicate
that fallback logic. Existing posts will be converted before the compatibility
path is considered for removal.

The canonical collection is an ordered interface: order in front matter must
be retained in post bylines, archive bylines if approved, and feed output.
The exact entry shape and conflict policy are open requirements questions above.
Singleton output should preserve current visible text, markup, routes, and
feed meaning wherever possible; multi-author output must be deterministic and
valid for the selected output format.

The work proceeds in this order:

1. Resolve the canonical `authors` shape, conflict behavior, and output
   semantics, then implement the shared compatibility/normalization boundary.
2. Update the post layout, shared archive/list path, and feed to consume only
   normalized authors. Replace the placeholder generated-output coverage with
   assertions for a legacy-compatible singleton, a canonical singleton, and a
   multi-author post.
3. Migrate all current post front matter and update `new-post.js` to emit the
   canonical field. Connect the authoring helper to the real Eleventy path by
   building content generated from the helper and checking the resulting post
   and feed, rather than testing serialization in isolation only.
4. Run the content inventory and clean production build. Review every remaining
   runtime reference to `author`; classify intentional compatibility fixtures
   separately from supported content and consumers.
5. Only after the evidence gate passes, apply the approved final compatibility
   state: either remove the fallback and reject legacy input with a clear
   diagnostic, or retain the fallback and document it as supported. Run the
   full build and tests again after that state change.

The parent build check must exercise the real Eleventy input, collection,
template, feed, and output directories together. A mocked `post.data` object
or a template-only unit test is not sufficient evidence that the migration
works end to end.

### Implementation decisions and open questions

- The working field name is `authors`, pending confirmation of the exact
  scalar-versus-record entry shape.
- Normalization belongs at the page/collection data boundary so raw legacy
  access does not spread across templates.
- Archive bylines and the final rejection policy remain requirement decisions,
  not implementation assumptions.
- If implementation reveals an additional public-contract choice, return the
  plan to `Draft` and record the choice before executing that part.

### Documentation

Update `docs/development/index.md` or a more focused document under
`docs/development/` only if the authoring contract needs more room than the
existing index. Document the canonical front-matter example, ordering and
rendering semantics, the transition fallback if retained, and the evidence
condition for any rejection. Do not document the target as current guidance
until the corresponding implementation and build evidence exist.

### Task checklist

- [ ] Resolve the requirement questions and mark the plan `Approved` before
  implementation.
- [ ] Complete `010-schema-compatibility.md`.
- [ ] Complete `020-rendering-output.md`.
- [ ] Complete `030-content-authoring.md`.
- [ ] Complete `040-legacy-retirement.md`.
- [ ] Review the final build, tests, content scan, and maintained
  documentation together.

### Requirement verification

- **Canonical contract and safe transition:** Verify the approved canonical and
  legacy inputs through the shared normalizer and a real Eleventy build. The
  decisive evidence is that both input forms reach the same canonical
  rendering/feed boundary without raw `author` reads in consumers.
- **Templates, archives, feeds, and generated pages:** Run the production
  build and inspect/assert the post page, home page, blog archive, tag page,
  feed, and sitemap. Verify existing routes and singleton output remain valid
  and that a multi-author source produces deterministic output.
- **Existing content migration:** Scan all post source files for legacy
  front-matter keys, inspect the migrated names/order, then build those exact
  sources and assert their names appear in the expected generated outputs.
- **Authoring tool:** Invoke `scripts/new-post.js` for approved one- and
  multi-author inputs, use its generated front matter as real post input, run
  Eleventy, and assert the generated post/feed output. This is the decisive
  check for the helper-to-site connection.
- **Evidence-gated legacy retirement:** Record the content scan, runtime
  reference audit, pre-retirement generated-output results, and post-retirement
  build/test results. A rejection change is complete only when all four are
  clean; otherwise the compatibility fallback remains and the unresolved state
  is documented.

### Additional implementation verification

- Check YAML/JSON escaping for names containing punctuation or quotes.
- Check empty, duplicate, and malformed author entries according to the
  approved validation policy.
- Check that the migration does not create `[object Object]`, `undefined`,
  duplicate feed authors, or empty bylines in generated output.
- Check the final diff for accidental route, title, tag, or sitemap changes.
````

### tasks/20260926-author-metadata-migration/010-schema-compatibility.md

````markdown
# Define the canonical author schema and transition compatibility

Establish the single page-data contract that represents one or more post
authors and temporarily bridges existing scalar `author` front matter to that
contract. This task owns the compatibility boundary consumed by templates and
authoring tools.

Parent Task: tasks/20260926-author-metadata-migration/000-main.md
Depends On: None

## Requirements checklist

- [ ] Record the approved canonical `authors` field name, entry shape, ordering,
  and validation rules.
- [ ] Provide one normalization boundary that exposes canonical authors to
  consumers during the transition.
- [ ] Preserve a legacy singleton author during the migration without
  requiring templates or feeds to read the raw `author` field.
- [ ] Define and test the behavior for canonical input, legacy input,
  conflicting fields, empty values, and malformed entries according to the
  approved policy.
- [ ] Keep the compatibility behavior isolated so the final retirement task can
  remove or retain it as one explicit state change.

## Requirement questions and decisions

- **Question:** Confirm whether canonical entries are ordered strings or
  records, and whether identity/URL fields are in scope.
- **Question:** Confirm precedence or rejection when both `authors` and
  `author` are supplied.
- **Recommendation:** Normalize legacy `author: "Name"` to a one-entry
  collection and make all downstream consumers depend only on the normalized
  value. Do not silently merge conflicting fields without an approved rule.

## Research and supporting facts

- Existing source files expose only scalar `author` values.
- The post layout and feed currently read the legacy key independently, so
  compatibility logic is currently duplicated at the consumer level by
  implication.
- Eleventy configuration is the natural ownership area for a shared
  collection/page-data boundary, but the implementation should use the
  project’s actual data-cascade capabilities rather than scattering template
  conditionals.

## Execution plan
Status: Draft

Define the canonical author interface before changing any consumer. The
normalizer should accept the approved canonical collection and, while the
transition is active, translate a valid legacy scalar into the same internal
shape. It should return enough information for templates and feeds to render
names in source order without knowing which input form supplied them.

Validation and conflict behavior must be explicit. A source item with both
fields, an empty collection, or an invalid entry must follow the approved
policy and produce an actionable diagnostic if rejection is the chosen
behavior. The normalizer must not make the final legacy-rejection decision
itself; that decision belongs to the evidence-gated retirement task.

Add focused coverage for normalization and an integration fixture that sends
the normalized value through at least one real post render. Keep the
compatibility fixture available for the transition tests, but mark it as
intentional so the final source audit can distinguish it from a supported
content dependency.

### Implementation decisions and open questions

- The exact canonical entry shape and conflict policy are blocked on the
  parent requirement questions.
- The normalizer’s public result should be stable enough that templates,
  feed generation, and the authoring helper share one representation.
- Do not remove legacy support in this task; the retirement task owns that
  compatibility-state change.

### Documentation

Contribute the canonical front-matter example and transition semantics to the
maintained development documentation after the shape is approved. Avoid
claiming that legacy input is rejected until the final gate passes.

### Task checklist

- [ ] Resolve and record the schema and validation decisions.
- [ ] Implement the shared normalization boundary during execution.
- [ ] Add canonical, legacy, conflict, and malformed-input evidence.
- [ ] Prove one normalized value reaches a real Eleventy-rendered page.
- [ ] Hand off the stable interface to the rendering and content/authoring
  subtasks.

### Requirement verification

- Verify canonical and legacy fixtures through the actual page-data path and a
  real Eleventy build; do not rely only on a helper-level mock.
- Assert that downstream output receives an ordered canonical collection and
  contains no raw legacy fallback branch in the template/feed consumers.
- Verify invalid or conflicting inputs according to the approved policy and
  preserve the diagnostics needed by the final retirement audit.

### Additional implementation verification

- Use names with punctuation, quotes, and non-ASCII characters.
- Verify author order survives normalization unchanged.
- Verify a single legacy name produces exactly one canonical entry.
````

### tasks/20260926-author-metadata-migration/020-rendering-output.md

````markdown
# Move rendering surfaces to canonical authors and prove generated output

Update the production templates and generated-output coverage so post pages,
archive/list surfaces, feeds, and related generated pages consume the
canonical author model without changing existing routes or singleton meaning.

Parent Task: tasks/20260926-author-metadata-migration/000-main.md
Depends On: tasks/20260926-author-metadata-migration/010-schema-compatibility.md

## Requirements checklist

- [ ] Make the post layout render the canonical author collection with
  deterministic, valid singleton and multi-author output.
- [ ] Audit `content/blog.njk`, `content/index.njk`, `content/tag-pages.njk`,
  and `_includes/postslist.njk`; any author presentation or data access uses
  canonical authors, while existing title/link output remains compatible
  unless archive bylines are approved.
- [ ] Make the feed emit the approved representation for every author and
  preserve the existing singleton feed meaning.
- [ ] Keep the home page, blog archive, tag pages, post routes, feed, and
  sitemap buildable with no missing or legacy-dependent author data.
- [ ] Replace the placeholder archive and author-output test files with
  executable generated-output evidence.

## Requirement questions and decisions

- **Question:** Confirm whether archive/list pages should gain visible
  bylines. Until confirmed, the migration audits their shared path and
  preserves its current title/link markup.
- **Question:** Confirm the feed representation for multiple authors (for
  example, repeated author elements or another schema-compatible form).
- **Recommendation:** Preserve the current singleton markup/feed meaning and
  extend it deterministically for multiple authors without changing routes.

## Research and supporting facts

- `_includes/layouts/post.njk` currently prints one raw `author` value.
- `content/feed.xml.njk` currently emits one `<author>` element from
  `post.data.author`.
- The three archive-like entry points share `_includes/postslist.njk`, which
  currently renders only links and titles.
- `content/sitemap.xml.njk` has no author dependency but should be included in
  the build regression because a template/data failure can affect the full
  generated site.
- Existing output tests contain comments only and do not currently assert
  routes, content, or feed values.

## Execution plan
Status: Draft

After the normalization boundary is available, update every author-aware
consumer to read the canonical collection. Keep presentation logic
consistent between the post layout and feed, and make the multi-author
separator or element structure an explicit part of the approved output
contract. Do not add archive markup solely to create a test if the archive
byline question is not approved; do verify that the shared list path does not
read the legacy field.

Build representative content through the real Eleventy configuration:
include a migrated singleton, a canonical multi-author post, and a
transition-era legacy fixture while compatibility is active. Assert the
resulting post page, home page, blog archive, tag page, feed, and sitemap.
Replace the current placeholder tests with checks against `_site/`, keeping
the build boundary intact.

Use the generated-output assertions to compare the existing singleton
meaning, not just to check that files exist. The multi-author assertions must
catch missing authors, duplicate authors, object serialization, and ordering
regressions.

### Implementation decisions and open questions

- Archive byline behavior and feed syntax remain blocked on parent decisions.
- The shared include should remain the ownership point for any list-level
  author presentation so home, archive, and tag pages cannot drift.
- Generated output is the decisive interface; a template test with fabricated
  `post.data` is supporting evidence only.

### Documentation

Document visible byline and feed behavior in the maintained development
documentation once the output contract is approved. Include route/output
compatibility notes only when verified by the production build.

### Task checklist

- [ ] Resolve archive and feed output decisions.
- [ ] Update the post layout and feed to use canonical authors.
- [ ] Audit/update the shared home/archive/tag list path.
- [ ] Replace placeholder tests with generated-output assertions.
- [ ] Run the real Eleventy build and inspect all required generated surfaces.
- [ ] Record route and singleton-output comparison evidence for the parent gate.

### Requirement verification

- Run the production build with singleton and multi-author content and assert
  post, home, blog, tag, feed, and sitemap outputs.
- Assert the exact author names and order in the generated post/feed surfaces,
  and assert no `undefined`, `[object Object]`, empty byline, or duplicate
  author output is produced.
- Verify existing route paths and singleton presentation remain compatible.
- Use the shared list output as the decisive archive check, including the
  approved byline behavior if that requirement is selected.

### Additional implementation verification

- Check HTML/XML escaping for author names containing special characters.
- Check that a feed consumer would receive valid output for one and many
  authors under the approved feed contract.
- Check that unrelated titles, tags, pagination data, and sitemap URLs do not
  change.
````

### tasks/20260926-author-metadata-migration/030-content-authoring.md

````markdown
# Migrate existing posts and update the authoring tool

Convert all existing post sources to the canonical multi-author front matter
and update `scripts/new-post.js` so new posts are authored in that model. This
task owns the source-content inventory and the authoring-helper-to-production
path.

Parent Task: tasks/20260926-author-metadata-migration/000-main.md
Depends On: tasks/20260926-author-metadata-migration/010-schema-compatibility.md

## Requirements checklist

- [ ] Migrate every existing post under the content input to the canonical
  author field without losing names or their order.
- [ ] Update the authoring helper API and serialization to emit the canonical
  single- and multi-author forms safely.
- [ ] Ensure generated front matter does not reintroduce the legacy `author`
  key.
- [ ] Prove that front matter emitted by the authoring helper can enter the
  real Eleventy content pipeline and produce correct post and feed output.
- [ ] Record a source-content inventory and clean scan that the retirement
  task can use as evidence.

## Requirement questions and decisions

- **Question:** Confirm the authoring helper’s final input API once the
  canonical entry shape is approved (an array, records, or another explicit
  collection interface).
- **Question:** Confirm whether a one-author convenience input remains
  supported by the helper while always serializing the canonical collection.
- **Recommendation:** Keep the helper’s output deterministic and use a real
  YAML serializer or equivalent escaping strategy rather than interpolating
  unescaped names into front matter.

## Research and supporting facts

- `content/posts/first.md` and `content/posts/second.md` are the current
  source posts and both use scalar `author` front matter.
- `scripts/new-post.js` exports `frontMatter(title, author)` and directly
  interpolates both values into YAML.
- There is no current executable test proving the helper output is valid
  front matter or that it reaches a built page.
- The build consumes `content/` directly, so a generated fixture can exercise
  the helper and production Eleventy path without mocking page data.

## Execution plan
Status: Draft

Inventory all post source files before editing and record each legacy value and
its intended order. Apply the canonical field to every existing post, review
the diff for title/body/tag/permalink changes, and run a source scan that
targets front-matter keys rather than incidental prose mentions.

Update `frontMatter` to accept the approved author collection and serialize it
as valid, escaped front matter. Cover both the convenience single-author case
and multiple authors if the API decision permits the convenience form. Keep
the function’s output free of the legacy key so newly authored content cannot
extend the transition accidentally.

For the decisive integration check, invoke the helper to create front matter
for a temporary or dedicated test post, place that post through the same
Eleventy input pipeline used by production, run the real build, and assert the
post and feed output. Clean up temporary/generated fixtures according to the
test harness so `_site/` and the committed content set remain controlled.

### Implementation decisions and open questions

- The helper API depends on the canonical author entry shape from subtask 010.
- The migration should preserve source order and values; it should not
  normalize names by sorting or rewriting them without approval.
- Whether a committed fixture or an isolated integration fixture is best can
  be decided locally, provided the check crosses the real content/build
  boundary.

### Documentation

Update the maintained development authoring guidance with the canonical
front-matter example, helper input contract, and one/many-author examples.
State the transition fallback or final rejection only after the retirement
gate establishes that state.

### Task checklist

- [ ] Inventory every post source and capture legacy values/order.
- [ ] Resolve the helper API and serialization decisions.
- [ ] Migrate all existing post front matter.
- [ ] Update helper coverage for valid singleton and multi-author output.
- [ ] Run the helper-to-Eleventy integration check and inspect post/feed
  output.
- [ ] Run the clean content scan and hand its evidence to the retirement
  task.

### Requirement verification

- Scan the complete content input for legacy front-matter keys and confirm
  every post has the canonical field with the expected names/order.
- Invoke the authoring helper, use its emitted front matter as real Eleventy
  input, run the production build, and assert the resulting post and feed.
  This is the decisive check for the authoring tool.
- Verify special characters and multiple names remain valid and intact after
  serialization and rendering.

### Additional implementation verification

- Review the migration diff for accidental changes to title, body, tags,
  permalink, or layout data.
- Check that helper output cannot create malformed YAML from quotes, colons,
  or newline characters.
- Check that temporary integration content cannot be mistaken for committed
  production content.
````

### tasks/20260926-author-metadata-migration/040-legacy-retirement.md

````markdown
# Close the transition with an evidence-gated legacy decision

Own the final compatibility state. Assemble source and generated-output
evidence from the preceding work, then either remove the legacy fallback and
reject `author` input or explicitly retain it as supported. No rejection is
allowed before the gate passes.

Parent Task: tasks/20260926-author-metadata-migration/000-main.md
Depends On:
- tasks/20260926-author-metadata-migration/020-rendering-output.md
- tasks/20260926-author-metadata-migration/030-content-authoring.md

## Requirements checklist

- [ ] Do not reject legacy input while any supported content, template, feed,
  archive, or authoring path still depends on it.
- [ ] Assemble content-scan, runtime-reference, and generated-output evidence
  proving the canonical model is used throughout the supported site.
- [ ] Apply the approved final state only after the evidence gate passes:
  remove the fallback and reject legacy input with a clear diagnostic, or
  retain the fallback and document it as supported.
- [ ] Run the production build and executable tests again after the final state
  is selected.
- [ ] Leave maintained documentation consistent with the resulting
  compatibility state.

## Requirement questions and decisions

- **Question:** Confirm whether this migration will end by rejecting legacy
  `author` or by retaining a documented compatibility fallback.
- **Recommendation:** Prefer explicit rejection after a clean gate if the
  project wants to prevent regression, but do not make that choice silently.
- **Decision required by the request:** The gate must include both source
  content evidence and generated-output evidence; a repository search alone is
  insufficient.

## Research and supporting facts

- Existing content currently contains the legacy key, so source migration must
  precede any rejection.
- The post layout and feed are current legacy consumers; archive/list surfaces
  require an explicit audit because their shared include currently renders
  only titles and links.
- The existing generated-output tests are placeholders, so the gate must wait
  for executable build assertions from the rendering and content subtasks.
- Task files and documentation may mention the legacy field as historical or
  transition information; the runtime/content audit must classify those
  mentions rather than treating every textual occurrence as a product
  dependency.

## Execution plan
Status: Draft

Collect the completed evidence from the schema, rendering, and
content/authoring tasks. Before changing compatibility behavior, run a clean
inventory over all post source files, inspect runtime references in templates,
configuration, scripts, and tests, and run the real production build with the
canonical content. Confirm that the required post, home, archive, tag, feed,
and sitemap outputs contain the expected values and no legacy-derived
undefined or malformed data.

Treat the gate as a checklist with an explicit recorded result:

1. Every supported post source has the canonical field and no legacy
   front-matter key.
2. All supported consumers use normalized/canonical authors; any remaining
   legacy reference is an intentional transition fixture, diagnostic, or
   historical documentation.
3. Generated-output assertions pass for singleton and multi-author content
   across the real Eleventy build.
4. The authoring helper emits only canonical front matter and its generated
   content has passed through the production build.

Only after all four conditions pass may the chosen final state be applied. If
rejection is selected, remove the compatibility fallback at the agreed
boundary, add a focused negative assertion for legacy input, and run the
complete build/tests again. If compatibility is retained, keep the fallback,
add no premature rejection, and document its supported scope and evidence
requirements for a later removal.

### Implementation decisions and open questions

- The final reject-versus-retain decision is still open.
- A negative test is appropriate only if rejection is approved; it must not
  cause the transition build to fail before the gate.
- The final audit must distinguish intentional test fixtures from accidental
  production dependencies.

### Documentation

Update the maintained development documentation with the final supported
field, authoring behavior, and compatibility state. If rejection is enabled,
document the diagnostic and migration expectation; if fallback is retained,
document that legacy input remains supported and why.

### Task checklist

- [ ] Receive and review the schema, rendering, and content/authoring evidence.
- [ ] Run the complete content and runtime reference audit.
- [ ] Run the clean generated-output gate across all required surfaces.
- [ ] Resolve the final compatibility state.
- [ ] Apply rejection only after the gate passes, if approved.
- [ ] Re-run build/tests and update maintained documentation.
- [ ] Hand the immutable evidence and any deferred compatibility decision to
  the parent task.

### Requirement verification

- Record the exact content scan, runtime-reference classification, and
  generated-output results before any legacy rejection.
- If rejection is selected, run a post-gate negative check showing legacy
  input is rejected at the approved boundary, followed by a clean production
  build of all migrated content.
- If fallback is retained, run the clean canonical build and verify that the
  remaining compatibility path is intentional, isolated, and documented.
- Verify that all required generated surfaces still build and that routes,
  titles, tags, feed output, and sitemap output remain intact after the final
  compatibility-state change.

### Additional implementation verification

- Search for raw legacy reads/writes in supported runtime paths after the final
  state change.
- Check diagnostics for actionable source location and field information.
- Check that evidence and documentation do not accidentally present a
  target-only rejection policy as current behavior before it is implemented.
````


**Assistant** *(reasoning present)*

```json
{
  "schema_version": 1,
  "scenario_id": "tg06-eleventy-author-migration-decomposition",
  "assessment": {
    "dimensions": {
      "plan_design_completeness": {
        "grade": "complete",
        "findings": [
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md, Execution plan",
            "quote": "A single page-data normalizer will expose the approved canonical author collection to every consumer. During the transition it may translate legacy `author` into a single-entry canonical collection, but templates and tools will not duplicate that fallback logic.",
            "why": "Names the central component, its responsibility, and the data-flow rule that consumers read only the normalized model — the decided architecture is reconstructable from the plan alone."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md, Execution plan",
            "quote": "The canonical collection is an ordered interface: order in front matter must be retained in post bylines, archive bylines if approved, and feed output.",
            "why": "States the interface contract and ordering semantics that the subtasks implement, covering the data-flow element of the design."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md, Requirement ownership",
            "quote": "The canonical data contract and transition compatibility requirements are owned by `010-schema-compatibility.md`; the final compatibility state is completed jointly with `040-legacy-retirement.md`.",
            "why": "Maps component responsibilities and dependency states across the five files, so a reader can reconstruct the whole decomposition and its dependency graph (010 <- 020/030 <- 040)."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md, Execution plan step 5",
            "quote": "Only after the evidence gate passes, apply the approved final compatibility state: either remove the fallback and reject legacy input with a clear diagnostic, or retain the fallback and document it as supported.",
            "why": "The compatibility end-state and its gating are decided as process even though the reject-vs-retain choice stays open, matching the scenario's unresolved question rather than inventing an answer."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md, Requirement verification",
            "quote": "Run the production build and inspect/assert the post page, home page, blog archive, tag page, feed, and sitemap.",
            "why": "Each requirement area has a stated verification approach (real build, generated-output assertions, content scans, helper-to-pipeline integration), so the plan shows how outcomes are proven, not just sequenced."
          }
        ]
      },
      "durable_context_preservation": {
        "grade": "complete",
        "findings": [
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md, Requirement questions and decisions",
            "quote": "Question — canonical entry shape: Should `authors` be an ordered list of display-name strings, or an ordered list of records such as `{ name }` with room for identity/link metadata?",
            "why": "The response's first material question (exact `authors` entry shape) is preserved in substance, including the refusal to invent identity/URL semantics."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md, Requirement questions and decisions",
            "quote": "Question — conflicting fields: What should happen when a source item contains both the canonical field and legacy `author`, or contains an empty or malformed author collection?",
            "why": "The conflicting-field validation question from the response is carried, together with the archive-byline and reject-vs-retain questions — all four of the response's listed material questions appear."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md, Scope and workstreams / Execution plan",
            "quote": "This plan does not authorize implementation. The task files remain `Draft` until execution is explicitly approved.",
            "why": "The response's draft-status and no-implementation outcome is preserved in every file's `Status: Draft` and the explicit authorization bar."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md, Research and supporting facts",
            "quote": "`scripts/new-post.js` currently accepts `(title, author)` and writes a scalar `author` key. Its output is not currently covered by a substantive test.",
            "why": "Inspection-derived facts carry their sources (file/symbol names, e.g. postslist.njk rendering only title links, placeholder tests), preserving the repository-inspection verification stance; no file claims an executed build, matching 'build and test commands were intentionally not run.'"
          },
          {
            "where": "tasks/20260926-author-metadata-migration/040-legacy-retirement.md, Requirements checklist",
            "quote": "Do not reject legacy input while any supported content, template, feed, archive, or authoring path still depends on it.",
            "why": "Approved outcome AUTHOR-4 is carried as a requirement with its evidence condition, and the main task mirrors it ('Produce generated-output and content evidence ... before rejecting it'), so no approved outcome is dropped."
          }
        ]
      },
      "section_appropriateness": {
        "grade": "complete",
        "findings": [
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md, Requirements checklist",
            "quote": "Migrate every existing post to the canonical model without losing author names or their intended order.",
            "why": "Outcomes and constraints sit in requirements checklists where a continuing agent looks for them; the subtask checklists decompose the same outcomes."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/020-rendering-output.md, Research and supporting facts",
            "quote": "`content/feed.xml.njk` currently emits one `<author>` element from `post.data.author`.",
            "why": "Learned facts with file-level sources live in supporting details, not mixed into the plan prose or requirement statements."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md, Requirement questions and decisions",
            "quote": "Question — archive presentation: The current shared `postslist.njk` renders titles and links but no author.",
            "why": "Unresolved items are centralized in the main task's questions section and echoed as blockers in the owning subtasks ('Archive byline behavior and feed syntax remain blocked on parent decisions'), so nothing open is buried in direction text."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md, Execution plan",
            "quote": "The work proceeds in this order: 1. Resolve the canonical `authors` shape ... 5. Only after the evidence gate passes ...",
            "why": "Direction and sequencing sit in the implementation plan, separated from facts and open questions."
          }
        ]
      },
      "plan_justification": {
        "grade": "justified",
        "findings": [
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md, Execution plan",
            "quote": "The migration will use a staged compatibility flow.",
            "why": "The plan restates and orders the decomposition the response announced (schema/compatibility -> rendering/output -> content/authoring -> evidence-gated retirement), matching the four subtask names in the response."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md, Implementation decisions and open questions",
            "quote": "The working field name is `authors`, pending confirmation of the exact scalar-versus-record entry shape.",
            "why": "The only committed naming choice traces directly to the response's own phrasing ('the exact `authors` entry shape'), so plan specifics trace to conversation-established material."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/010-schema-compatibility.md, Implementation decisions and open questions",
            "quote": "The exact canonical entry shape and conflict policy are blocked on the parent requirement questions.",
            "why": "Subtasks inherit openness instead of asserting schema detail, showing the plan organizes the conversation's planning rather than fabricating resolved design."
          }
        ]
      },
      "task_kind_fit": {
        "grade": "fits",
        "findings": [
          {
            "where": "tasks/20260926-author-metadata-migration/020-rendering-output.md, Requirements checklist",
            "quote": "Replace the placeholder archive and author-output test files with executable generated-output evidence.",
            "why": "For a code/build migration the acceptance evidence is real Eleventy build assertions against `_site/`, explicitly replacing the known placeholder tests — evidence of the right kind, not template-only mocks."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/040-legacy-retirement.md, Execution plan",
            "quote": "Treat the gate as a checklist with an explicit recorded result: 1. Every supported post source has the canonical field ...",
            "why": "The evidence gate records decisions and four concrete pass conditions, fitting the evidence-gated retirement outcome and the request's constraint that rejection wait for content plus generated-output evidence."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md, Task checklist",
            "quote": "Resolve the requirement questions and mark the plan `Approved` before implementation.",
            "why": "For the planning/decomposition kind itself, acceptance is recorded decisions plus an explicit status transition; no inapplicable section is filled mechanically (Documentation sections are conditional and content-specific)."
          }
        ]
      }
    },
    "mistakes": [
      {
        "where": "tasks/20260926-author-metadata-migration/000-main.md, Requirements checklist",
        "quote": "Keep maintained developer/authoring documentation aligned with the supported front-matter model and the transition or final rejection state.",
        "why": "Invented scope: neither the approved outcomes AUTHOR-1..5, the open questions, nor the natural user request establishes a documentation workstream, yet this requirement propagates into every subtask's Documentation section and 040's 'Leave maintained documentation consistent...' item. Plausible housekeeping, but an addition beyond the defined contract rather than carried context."
      },
      {
        "where": "tasks/20260926-author-metadata-migration/000-main.md, Requirement questions and decisions (vs scenario open questions)",
        "quote": "Question — final compatibility state: Should the completed migration reject legacy `author` input, or retain a read fallback indefinitely?",
        "why": "Partial compression of the scenario's open question 'legacy deprecation period require approval': the files collapse the deprecation-period question into a binary reject-vs-retain choice and never ask whether a defined deprecation window between gate approval and rejection is needed. The decision space's endpoints are covered, but the period dimension the excerpt names is only implicit."
      },
      {
        "where": "Producer final response, third task link",
        "quote": "/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite/tmp/agent/evaluation/task-guidance/gpt/runs/...",
        "why": "The index link for 020-rendering-output.md uses `agent/evaluation` where the other four links use `agent-evaluation`, so one of the five index links is malformed and dead for a reviewer following the response. No durable context is lost because the task files carry correct relative links among themselves."
      }
    ],
    "summary": "The five-file decomposition is faithful to the approved outcomes and to the conversation's durable context. The main task's plan reconstructs the decided design on its own: a single page-data normalizer exposing an ordered canonical author collection, consumers barred from raw `author` reads, legacy bridged as a single-entry collection during transition, and retirement executed only behind a four-condition content-plus-generated-output evidence gate, with per-requirement ownership and verification mapped to the subtasks. All four material questions the response flagged (entry shape, archive bylines, conflict validation, reject-vs-retain) are recorded as open requirement questions rather than silently decided, so plan_justification is organizing, not fabrication. Content sits in conventional sections: outcomes and the no-early-rejection constraint in requirements, inspected file-level facts with sources in supporting details, direction in the execution plan, blockers in questions/decisions. Acceptance evidence matches the code-migration kind: real Eleventy builds, generated-output assertions replacing placeholder tests, a helper-to-pipeline integration check, and a conditional negative test, plus an explicit approve-before-implement gate for the planning task itself. Residual issues are minor and none lose carried context: an unrequested documentation-alignment workstream was added as a first-class requirement, the scenario's 'legacy deprecation period' approval is folded into the reject-vs-retain question without an explicit window question, and one of the five index links in the response contains a path typo."
  }
}
```
