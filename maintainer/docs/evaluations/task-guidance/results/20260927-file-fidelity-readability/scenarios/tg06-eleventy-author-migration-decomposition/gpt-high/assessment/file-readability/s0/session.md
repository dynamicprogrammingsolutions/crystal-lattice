# Session — tg06-eleventy-author-migration-decomposition · file-readability-assessment-gpt-high-s0 · glm max

- Run: `20260928T204840.553283Z-task-guidance-file-readability-tg06-eleventy-author-migration-decomposition-gpt-high-s0-482d8ec6`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `9c0539a49577a3a5…`)
- Config: [glm-assessor-max](../../../../../../shared/configs/glm-assessor-max.json)
- Activity: 3 messages · 0 tool calls · 0 tool results
- Usage: unknown — saved session contains no provider usage metadata

## Transcript

**User**

Assess how easily a human reader can work with the task files below.
You are that reader: a maintainer who must find, understand, and act on
what the files say. Judge every top-level section that is present; do
not invent sections that are absent, and do not grade files or sections
that do not appear.

Grade each present top-level section `readable`, `partial`, or
`unreadable`: can a reader take in that section's content with
reasonable effort — scan it, hold it, and use it? A section is
`unreadable` when a reader must re-read dense prose or wall-like list
items to extract what matters; `partial` when parts strain the reader.

Then grade the whole file's navigation `navigable`, `partial`, or
`confusing`: can a reader find the thing they are looking for — the
outcome, the constraint, the open question, the plan status — from the
file's structure alone?

Measured structure facts are provided per section; anchor on these
numbers rather than impressions. They are facts, not rules: no shape is
banned or required. Formatting elements — tables, ordered lists, code
snippets, short paragraphs — are tools among many; what is graded is
the reader's experience, never the presence of a specific element.

Every grade carries findings: concrete `{where, quote, why}` items. A
non-top grade with empty findings is invalid. Then hunt for
presentation mistakes explicitly — prose walls, list items that mix
several facts, buried load-bearing facts, headings that do not match
their content, walls of unchecked boxes — and list each as
`{where, quote, why}` in `mistakes`.

Depth must match impact: a short section is not a defect; a dense
section is not automatically one either. Verbosity is not rewarded;
brevity that loses nothing is not penalized.

Return JSON only:

{
  "schema_version": 1,
  "scenario_id": "tg06-eleventy-author-migration-decomposition",
  "assessment": {
    "sections": {
      "SECTION TITLE": {
        "grade": "readable|partial|unreadable",
        "findings": [{"where": "...", "quote": "...", "why": "..."}]
      }
    },
    "navigation": {"grade": "navigable|partial|confusing", "findings": []},
    "mistakes": [{"where": "...", "quote": "...", "why": "..."}],
    "summary": "concise evidence-based interpretation"
  }
}

`sections` contains exactly the top-level sections listed in the
measured facts, keyed by the exact Section values of that table
(`<file path> — <section title>`), so multi-file task sets stay
addressable.

What these files are for:

# Eleventy author metadata migration decomposition

Partition a broad content/build migration by compatible working states rather than files and phases.

Category: decomposition

Measured structure facts (per file, per top-level section):

#### tasks/20260925-author-metadata-migration/000-main.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260925-author-metadata-migration/000-main.md — Requirements checklist | 125 | 0 | 0 | 6 | 26 | 0 | 0 | 0 | 1 |
| tasks/20260925-author-metadata-migration/000-main.md — Subtasks | 66 | 1 | 11 | 4 | 8 | 0 | 0 | 0 | 4 |
| tasks/20260925-author-metadata-migration/000-main.md — Unresolved requirement questions | 97 | 0 | 0 | 2 | 11 | 0 | 0 | 0 | 3 |
| tasks/20260925-author-metadata-migration/000-main.md — Decisions | 69 | 0 | 0 | 3 | 13 | 0 | 0 | 0 | 0 |
| tasks/20260925-author-metadata-migration/000-main.md — Research and supporting facts | 91 | 0 | 0 | 6 | 12 | 0 | 0 | 0 | 13 |
| tasks/20260925-author-metadata-migration/000-main.md — Execution plan | 546 | 2 | 81 | 24 | 14 | 4 | 0 | 0 | 10 |

#### tasks/20260925-author-metadata-migration/010-author-contract-and-content.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260925-author-metadata-migration/010-author-contract-and-content.md — Requirements checklist | 84 | 0 | 0 | 5 | 17 | 0 | 0 | 0 | 0 |
| tasks/20260925-author-metadata-migration/010-author-contract-and-content.md — Unresolved requirement questions | 38 | 0 | 0 | 2 | 11 | 0 | 0 | 0 | 0 |
| tasks/20260925-author-metadata-migration/010-author-contract-and-content.md — Research and supporting facts | 53 | 0 | 0 | 3 | 15 | 0 | 0 | 0 | 4 |
| tasks/20260925-author-metadata-migration/010-author-contract-and-content.md — Execution plan | 259 | 1 | 76 | 12 | 14 | 4 | 0 | 0 | 3 |

#### tasks/20260925-author-metadata-migration/020-rendering-and-generated-output.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260925-author-metadata-migration/020-rendering-and-generated-output.md — Requirements checklist | 84 | 0 | 0 | 5 | 18 | 0 | 0 | 0 | 0 |
| tasks/20260925-author-metadata-migration/020-rendering-and-generated-output.md — Unresolved requirement questions | 33 | 0 | 0 | 2 | 10 | 0 | 0 | 0 | 0 |
| tasks/20260925-author-metadata-migration/020-rendering-and-generated-output.md — Research and supporting facts | 57 | 0 | 0 | 5 | 12 | 0 | 0 | 0 | 6 |
| tasks/20260925-author-metadata-migration/020-rendering-and-generated-output.md — Execution plan | 309 | 1 | 73 | 15 | 14 | 4 | 0 | 0 | 4 |

#### tasks/20260925-author-metadata-migration/030-authoring-tool.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260925-author-metadata-migration/030-authoring-tool.md — Requirements checklist | 66 | 0 | 0 | 4 | 16 | 0 | 0 | 0 | 0 |
| tasks/20260925-author-metadata-migration/030-authoring-tool.md — Unresolved requirement questions | 39 | 0 | 0 | 2 | 13 | 0 | 0 | 0 | 0 |
| tasks/20260925-author-metadata-migration/030-authoring-tool.md — Research and supporting facts | 35 | 0 | 0 | 2 | 14 | 0 | 0 | 0 | 3 |
| tasks/20260925-author-metadata-migration/030-authoring-tool.md — Execution plan | 232 | 1 | 56 | 12 | 13 | 4 | 0 | 0 | 1 |

#### tasks/20260925-author-metadata-migration/040-legacy-retirement.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260925-author-metadata-migration/040-legacy-retirement.md — Requirements checklist | 80 | 0 | 0 | 5 | 17 | 0 | 0 | 0 | 1 |
| tasks/20260925-author-metadata-migration/040-legacy-retirement.md — Research and supporting facts | 49 | 0 | 0 | 2 | 13 | 0 | 0 | 0 | 0 |
| tasks/20260925-author-metadata-migration/040-legacy-retirement.md — Execution plan | 358 | 1 | 85 | 15 | 14 | 4 | 0 | 0 | 2 |

The produced task files:

### tasks/20260925-author-metadata-migration/000-main.md

````markdown
# Migrate post author metadata

Plan the transition from the singular `author` post field to a structured,
ordered multi-author model while preserving existing content and generated
pages until the repository proves that the legacy field is no longer needed.

## Requirements checklist

- [ ] Posts use an approved structured multi-author metadata form that can represent one or more authors in a stable order.
- [ ] Existing post content is migrated safely, with no loss or unintended change to current author names.
- [ ] Post templates, archive paths, and feeds consume the new author model and continue to build successfully.
- [ ] The post-authoring helper emits the new model and no longer makes the singular field the normal authoring path.
- [ ] Legacy `author` input remains compatible during the migration transition and is rejected only after content and generated-output evidence demonstrate that no supported path depends on it.
- [ ] Maintained documentation describes the supported author metadata and transition state after implementation.

## Subtasks

The work is split by independently reviewable compatibility and ownership
boundaries:

- [ ] `tasks/20260925-author-metadata-migration/010-author-contract-and-content.md` owns the metadata contract, transition
  compatibility, and migration of source posts.
- [ ] `tasks/20260925-author-metadata-migration/020-rendering-and-generated-output.md` owns post rendering, archive
  traversal, feeds, and production-build evidence.
- [ ] `tasks/20260925-author-metadata-migration/030-authoring-tool.md` owns the post-generation helper and its contract
  documentation.
- [ ] `tasks/20260925-author-metadata-migration/040-legacy-retirement.md` owns the cross-surface evidence gate and removal
  of the legacy fallback.

## Unresolved requirement questions

- [ ] Confirm the public structured shape. Recommendation: replace `author`
  with an ordered `authors` array of objects such as `{ name: "Ada Example" }`
  so the model can grow without another front-matter migration. An ordered
  array of strings is a smaller alternative, but it is less extensible.
- [ ] Confirm whether archive listings should display author names as part of
  this migration. The current archive/list include displays titles only, so
  the minimum safe interpretation is to audit it for legacy reads and verify
  unchanged output; adding archive bylines would be a separate user-visible
  design choice.

## Decisions

- This task records a Draft plan only. No source content, templates, scripts,
  tests, or documentation are changed by creating these files.
- Compatibility is staged: accept the old field while new content and
  templates move to the new model, then remove/reject it only at the explicit
  evidence gate.
- Existing rendered names, URLs, feed location, and page coverage are
  preserved unless the user approves a separate output change.

## Research and supporting facts

- The current posts at `content/posts/first.md` and
  `content/posts/second.md` each contain a singular quoted `author` value.
- `_includes/layouts/post.njk` renders `author` directly.
- `content/feed.xml.njk` reads `post.data.author`; the archive and tag
  listing include currently render titles and links but do not read author
  metadata.
- `scripts/new-post.js` exports `frontMatter(title, author)` and emits the
  singular field.
- `tests/author-output.test.js` and `tests/archive-output.test.js` are
  placeholders for generated-output coverage; decisive evidence must run the
  real Eleventy build and inspect its output.
- `README.md` documents the generated site surfaces but not front matter or
  authoring conventions. `docs/development/index.md` contains no author
  specification.

## Execution plan

Status: Draft

The implementation should proceed as a staged data-contract migration. First
define and document the approved structured field and a temporary adapter that
can read legacy content. Migrate every checked-in post and update the
authoring helper to produce the new shape. Then update all production
consumers, including the post layout and feed, while auditing archive and tag
paths for indirect legacy dependencies. A real build must establish both
output preservation and correct multi-author rendering before the adapter and
singular-field acceptance are removed.

The migration boundary is deliberately evidence-driven:

1. Establish the approved schema and compatibility behavior.
2. Add focused source-content checks and migrate all existing posts.
3. Update production templates and the authoring helper, with generated-output
   assertions for posts, archives, feeds, and relevant metadata.
4. Run a repository-wide dependency search plus a clean production build and
   inspect representative generated files for old and new forms.
5. Only after those checks pass, remove the legacy fallback/rejection path and
   add a regression that fails if singular `author` metadata returns.

### Implementation decisions and open questions

- The recommended model is `authors` as an ordered array of `{ name }`
  records. The final field name, record shape, and any additional required
  fields remain blocked on the unresolved schema question above.
- The compatibility adapter must define behavior for legacy single-name
  content, new single-author content, and multiple authors. It must preserve
  author order and must not silently discard names.
- Feed representation for multiple authors must be decided with the schema:
  each author should have a deterministic XML representation, while the
  existing feed URL and entry coverage remain stable.
- No fallback behavior for malformed or empty author data is approved by this
  plan; decide validation and failure behavior when the schema is approved.

### Documentation

- Update the maintained package/development documentation in the same change
  as the implementation, most likely `README.md` or a focused authoring
  document if the approved contract warrants one.
- Document the new front-matter form, ordering semantics, the authoring helper
  input, and the fact that the singular field is transitional only until the
  retirement gate is complete.
- Do not describe the new model as current guidance until implementation and
  generated-output evidence make it true.

### Task checklist

- [ ] Resolve the structured-author schema and archive-display question.
- [ ] Complete `tasks/20260925-author-metadata-migration/010-author-contract-and-content.md`.
- [ ] Complete `tasks/20260925-author-metadata-migration/020-rendering-and-generated-output.md`.
- [ ] Complete `tasks/20260925-author-metadata-migration/030-authoring-tool.md`.
- [ ] Complete `tasks/20260925-author-metadata-migration/040-legacy-retirement.md`.
- [ ] Keep this plan Draft until the user approves execution.
- [ ] After approval, mark the plan Approved before changing implementation files.

### Requirement verification

- Structured metadata and safe source migration: inspect every post front
  matter and run the focused content/schema checks from subtask 010.
- Templates, archives, and feeds: run `npm run build` through the real
  Eleventy pipeline, then assert representative post, archive/tag, and feed
  output from the generated `_site` as specified by subtask 020.
- Authoring tool: test the exported helper with one and multiple authors and
  assert that its emitted front matter uses only the approved new model, as
  specified by subtask 030.
- Legacy rejection: combine repository-wide source/content search, migrated
  content inspection, clean generated-output inspection, and the regression
  guard from subtask 040. Do not mark this requirement complete from isolated
  template tests or mocked data.
- Documentation: review the maintained documentation against the implemented
  contract and transition state after the behavioral checks pass.
````

### tasks/20260925-author-metadata-migration/010-author-contract-and-content.md

````markdown
# Define the author contract and migrate content

Establish the approved structured author metadata, provide transition
compatibility for existing singular-authored posts, and migrate all checked-in
post front matter without changing author identity or order.

Parent Task: tasks/20260925-author-metadata-migration/000-main.md

## Requirements checklist

- [ ] The approved structured multi-author field and record shape are defined.
- [ ] Legacy singular author data can be read during the transition and maps deterministically to one structured author.
- [ ] Every existing post is migrated with the original author name preserved.
- [ ] The migration supports one or more authors in explicit order and does not silently drop values.
- [ ] Focused checks detect missing, malformed, or accidentally regressed source metadata according to the approved contract.

## Unresolved requirement questions

- [ ] Confirm whether the structured value is an array of author records
  (recommended) or an array of strings, and which record fields are required.
- [ ] Confirm validation behavior for empty or malformed author entries.

## Research and supporting facts

- Both checked-in posts currently use `author: "Name"` and are the complete
  known source-content inventory at planning time.
- The post directory data file sets the post layout and `posts` tag but does
  not define an author normalization layer.
- The migration must preserve the existing author names `Ada Example` and
  `Grace Example`.

## Execution plan

Status: Draft

Define the target front-matter contract first, then add the smallest
repository-owned normalization/validation boundary that allows old and new
content to coexist during migration. Convert each existing post to the new
field, retaining author order and values. Add focused checks over the actual
content files so future edits cannot reintroduce the singular form or create
an empty author list. Keep the legacy reader available until the generated
output and content evidence in subtask 040 authorizes its removal.

### Implementation decisions and open questions

- Prefer an ordered `authors` array of `{ name }` records for extensibility,
  pending approval of the public schema.
- Keep source migration mechanical and reviewable: each old scalar maps to a
  one-element structured list with the same visible name.
- Do not invent fallback authors or infer names from filenames.

### Documentation

- Record the approved front-matter example and migration semantics in the
  maintained authoring/development documentation selected by the parent plan.

### Task checklist

- [ ] Resolve the target schema and validation behavior.
- [ ] Implement the temporary compatibility/normalization boundary.
- [ ] Migrate all existing post files.
- [ ] Add focused content-contract checks.
- [ ] Update the parent task checklist and evidence after verification.

### Requirement verification

- Enumerate `content/posts/**/*.md`, parse each front matter block, and assert
  the approved structured field contains the expected ordered author values.
- Exercise one legacy-shaped fixture through the compatibility boundary and
  confirm it produces the same structured value as its migrated equivalent.
- Run the focused content checks after migration; do not rely only on a
  repository text search because that cannot prove the mapping preserves
  values.
````

### tasks/20260925-author-metadata-migration/020-rendering-and-generated-output.md

````markdown
# Migrate rendering and generated output

Move post templates and feed generation to the structured author model, audit
archives and related listing paths for legacy reads, and prove the production
build remains complete and compatible during the transition.

Parent Task: tasks/20260925-author-metadata-migration/000-main.md

Depends On: tasks/20260925-author-metadata-migration/010-author-contract-and-content.md

## Requirements checklist

- [ ] Individual post rendering consumes the structured author model.
- [ ] The feed represents one or more authors deterministically using the approved output form.
- [ ] Archive, home, tag, sitemap, and other generated paths are audited for legacy author dependencies and continue to build.
- [ ] Existing URLs and non-author page content remain intact unless a separately approved archive-byline change is made.
- [ ] Generated-output tests exercise the real Eleventy build and cover both compatibility and multi-author cases.

## Unresolved requirement questions

- [ ] Confirm whether archive/list pages should gain visible author output or
  only stop depending on the legacy field.
- [ ] Confirm the exact feed XML shape for multiple structured authors.

## Research and supporting facts

- `_includes/layouts/post.njk` directly renders the legacy `author` value.
- `content/feed.xml.njk` directly reads `post.data.author`.
- `_includes/postslist.njk` is shared by the home page, blog archive, and tag
  pages and currently renders only title/link data.
- `content/sitemap.xml.njk` traverses all pages but does not read author data.
- Existing generated-output test files do not yet execute or assert the
  production build.

## Execution plan

Status: Draft

Update the post layout and feed to consume the normalized structured data,
preserving visible single-author output and defining deterministic
multi-author output. Audit every consumer reachable from home, blog, tag,
sitemap, post, and feed templates. Keep archive markup unchanged if the
approved requirement is dependency removal only; add bylines only if that
open question is approved. Replace placeholder tests with a real build-backed
test that inspects generated files rather than injecting mocked post objects.

### Implementation decisions and open questions

- Use one shared normalized representation for template consumers so the
  layout and feed cannot drift in how they interpret legacy content.
- Preserve the feed path and entry count. The exact author element strategy
  remains pending the approved schema and feed decision.
- Include at least one multi-author fixture in test input or a temporary
  test-owned content fixture that crosses the production build boundary,
  without bypassing Eleventy data loading.

### Documentation

- Document any visible feed or archive rendering change alongside the
  approved author contract.
- Keep README/site-surface claims accurate after generated-output behavior is
  verified.

### Task checklist

- [ ] Resolve archive and feed output decisions.
- [ ] Update post and feed consumers.
- [ ] Audit shared archive/listing and metadata templates.
- [ ] Replace placeholder generated-output coverage with real build-backed
  assertions.
- [ ] Verify representative post, home/archive, tag, sitemap, and feed output.
- [ ] Update the parent task checklist and evidence after verification.

### Requirement verification

- Run `npm run build` and inspect generated post HTML for preserved author
  output and correct multi-author output.
- Inspect `_site/blog/index.html`, the home page, generated tag pages, and
  `_site/sitemap.xml` to confirm the full page set builds and contains no
  unexpected legacy dependency.
- Inspect `_site/feed/feed.xml` for stable entry coverage and the approved
  deterministic author representation.
- Use the real production build in the automated test; a test that supplies
  pre-normalized mock data is not decisive evidence for this subtask.
````

### tasks/20260925-author-metadata-migration/030-authoring-tool.md

````markdown
# Migrate the post-authoring helper

Update the post-generation helper so new posts are authored with the
structured multi-author model while the transition contract remains explicit
and testable.

Parent Task: tasks/20260925-author-metadata-migration/000-main.md

Depends On: tasks/20260925-author-metadata-migration/010-author-contract-and-content.md

## Requirements checklist

- [ ] The helper accepts the approved structured author input for one or more authors.
- [ ] Generated front matter uses the new field and preserves author order and values.
- [ ] The helper no longer makes the singular field the normal output path.
- [ ] Helper tests cover single- and multi-author generation and malformed input behavior required by the approved contract.

## Unresolved requirement questions

- [ ] Confirm the helper API: an array of author records, a variadic list, or
  another caller-facing shape.
- [ ] Confirm whether accepting the old scalar helper argument is required
  during the transition or should fail immediately.

## Research and supporting facts

- `scripts/new-post.js` currently exports `frontMatter(title, author)` and
  interpolates the scalar directly into `author`.
- There is no current helper test; the new test must exercise the exported
  function directly and inspect its complete front-matter output.

## Execution plan

Status: Draft

Align the helper's caller-facing input with the approved content contract,
validate the minimum required author data, and serialize it without losing
order or names. Add focused tests for one and multiple authors. If scalar
compatibility is retained temporarily, make it an explicit adapter with a
removal marker rather than allowing it to remain the undocumented default.

### Implementation decisions and open questions

- The helper should share the same serialization rules as checked-in content;
  it must not emit a shape that templates accept only through a special case.
- Do not silently coerce empty names or discard extra authors; validation
  behavior awaits the schema decision.

### Documentation

- Document the helper input and a one/multiple-author example in the
  maintained authoring documentation.
- Clearly mark any scalar compatibility argument as transitional until the
  retirement gate removes it.

### Task checklist

- [ ] Resolve the helper API and scalar compatibility question.
- [ ] Update `scripts/new-post.js`.
- [ ] Add direct helper tests for single and multiple authors.
- [ ] Verify emitted front matter against the content contract.
- [ ] Update the parent task checklist and evidence after verification.

### Requirement verification

- Call the exported helper with approved single- and multi-author inputs and
  parse the resulting front matter.
- Assert the field name, record shape, order, and values match the approved
  contract exactly.
- If scalar compatibility is temporarily supported, test it separately and
  mark the case for removal under subtask 040.
````

### tasks/20260925-author-metadata-migration/040-legacy-retirement.md

````markdown
# Retire the legacy author field

Perform the final evidence review and remove/reject singular `author` input
only after all source content, production consumers, generated outputs, and
authoring paths demonstrate that they use the structured model.

Parent Task: tasks/20260925-author-metadata-migration/000-main.md

Depends On: tasks/20260925-author-metadata-migration/010-author-contract-and-content.md, tasks/20260925-author-metadata-migration/020-rendering-and-generated-output.md, tasks/20260925-author-metadata-migration/030-authoring-tool.md

## Requirements checklist

- [ ] The repository contains no supported content, template, feed, helper, or test path that depends on singular `author`.
- [ ] Clean production-build evidence covers migrated content and generated post, archive, tag, sitemap, and feed outputs.
- [ ] The legacy field is rejected or removed only after the evidence gate passes.
- [ ] Regression coverage prevents accidental reintroduction of singular author metadata.
- [ ] Documentation no longer presents the singular field as supported current input.

## Research and supporting facts

- The current singular consumers are known in the post layout, feed template,
  and post-generation helper; the final search must be broader than this
  initial inventory.
- Existing tests are placeholders, so the gate must include real build
  execution and content inspection rather than treating test collection as
  evidence.

## Execution plan

Status: Draft

Run the completed focused tests, a repository-wide search for legacy field
references, and a clean Eleventy build from migrated content. Compare
representative generated output with the preserved single-author behavior and
verify a multi-author case. Review the evidence as a single gate. If any
supported path still needs the old field, retain compatibility and record the
gap rather than rejecting it. Once the gate passes, remove the legacy
normalization/rejection allowance, add a regression that fails on singular
front matter or emitted helper output, and update documentation.

### Implementation decisions and open questions

- The legacy cutoff is a compatibility decision, not a cleanup step; it must
  be made only after the named evidence is available.
- If the repository has an external content source not visible in the local
  inventory, pause retirement and add it to the evidence scope before
  rejecting the field.
- Preserve generated URLs and feed location while changing only the author
  data contract and its intended rendering.

### Documentation

- Update the maintained authoring/development guidance to state that
  structured authors are the sole supported form after retirement.
- Record the migration/retirement evidence in the implementation change or
  task completion notes, not as unsupported permanent user guidance.

### Task checklist

- [ ] Run all focused content, rendering, and helper checks.
- [ ] Run a clean production build and inspect representative generated files.
- [ ] Search source, content, scripts, templates, tests, and generated output
  for unsupported singular-field dependencies.
- [ ] Decide whether the evidence gate passes; retain compatibility if it does
  not.
- [ ] Remove/reject the legacy form only if the gate passes.
- [ ] Add the regression guard and finalize documentation.
- [ ] Update the parent task checklist and requirement evidence.

### Requirement verification

- Decisive evidence is the combined real build plus generated-output
  inspection, migrated-content inventory, authoring-helper output checks, and
  repository-wide legacy dependency search.
- Confirm the old field is absent from supported source content and is not
  read by production templates or emitted by the helper.
- Run the complete test command (`npm test`) and the production build
  (`npm run build`) after the cutoff; report any unavailable dependency or
  external-content check as a blocker rather than marking retirement complete.
````


**Assistant** *(reasoning present)*

{
  "schema_version": 1,
  "scenario_id": "tg06-eleventy-author-migration-decomposition",
  "assessment": {
    "sections": {
      "tasks/20260925-author-metadata-migration/000-main.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "Requirements checklist, item 5 of 6",
            "quote": "Legacy `author` input remains compatible during the migration transition and is rejected only after content and generated-output evidence demonstrate that no supported path depends on it.",
            "why": "Six parallel single-requirement items; the longest (26 words per the measured facts) is this one, which embeds the removal condition inside the checkbox but still scans in one pass."
          }
        ]
      },
      "tasks/20260925-author-metadata-migration/000-main.md — Subtasks": {
        "grade": "readable",
        "findings": [
          {
            "where": "Subtasks, intro plus four items",
            "quote": "The work is split by independently reviewable compatibility and ownership boundaries:",
            "why": "An 11-word paragraph states the split criterion, then each item binds exactly one subtask file to its ownership scope, so the decomposition index is extractable at a glance."
          }
        ]
      },
      "tasks/20260925-author-metadata-migration/000-main.md — Unresolved requirement questions": {
        "grade": "readable",
        "findings": [
          {
            "where": "Both bullets",
            "quote": "Confirm the public structured shape. Recommendation: replace `author` with an ordered `authors` array of objects such as `{ name: \"Ada Example\" }` so the model can grow without another front-matter migration.",
            "why": "Only two items (97 words total) and each opens with the imperative question before its supporting argument, so the open decisions are extractable; the embedded recommendations cost a parsing beat and are flagged in mistakes."
          }
        ]
      },
      "tasks/20260925-author-metadata-migration/000-main.md — Decisions": {
        "grade": "readable",
        "findings": [
          {
            "where": "Decisions, item 2 of 3",
            "quote": "Compatibility is staged: accept the old field while new content and templates move to the new model, then remove/reject it only at the explicit evidence gate.",
            "why": "Three short policy statements, one decision each; the load-bearing staged-compatibility rule is stated once and cleanly rather than buried."
          }
        ]
      },
      "tasks/20260925-author-metadata-migration/000-main.md — Research and supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "Research facts, bullet 3 of 6",
            "quote": "`content/feed.xml.njk` reads `post.data.author`; the archive and tag listing include currently render titles and links but do not read author metadata.",
            "why": "Six file-anchored bullets with 13 code spans make each claim checkable against the repo; this one joins two facts with a semicolon, a minor mix that stays under ~20 words."
          }
        ]
      },
      "tasks/20260925-author-metadata-migration/000-main.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "Execution plan, section shape",
            "quote": "The migration boundary is deliberately evidence-driven:",
            "why": "The set's largest section (546 words) stays workable because the 81-word strategy paragraph is followed by a numbered five-step boundary and four labeled subsections (24 items total), so no undifferentiated block must be held at once; strain concentrates in the Requirement verification bullets flagged in mistakes."
          }
        ]
      },
      "tasks/20260925-author-metadata-migration/010-author-contract-and-content.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "Requirements checklist, item 5 of 5",
            "quote": "Focused checks detect missing, malformed, or accidentally regressed source metadata according to the approved contract.",
            "why": "Five parallel items, longest 17 words per measurement, each stating one verifiable requirement without mixing scopes."
          }
        ]
      },
      "tasks/20260925-author-metadata-migration/010-author-contract-and-content.md — Unresolved requirement questions": {
        "grade": "readable",
        "findings": [
          {
            "where": "Unresolved questions, bullet 1 of 2",
            "quote": "Confirm whether the structured value is an array of author records (recommended) or an array of strings, and which record fields are required.",
            "why": "Two items, 38 words total; the only embedded judgment is the parenthetical '(recommended)', visible without re-reading."
          }
        ]
      },
      "tasks/20260925-author-metadata-migration/010-author-contract-and-content.md — Research and supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "Research facts, bullet 3 of 3",
            "quote": "The migration must preserve the existing author names `Ada Example` and `Grace Example`.",
            "why": "Three short bullets (53 words total), each a single fact or constraint the migration must honor."
          }
        ]
      },
      "tasks/20260925-author-metadata-migration/010-author-contract-and-content.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "Execution plan, opening paragraph",
            "quote": "Convert each existing post to the new field, retaining author order and values.",
            "why": "The 76-word paragraph gives one purpose per sentence, then 12 items sit under four labeled subsections; the whole 259-word section reads in a single pass."
          }
        ]
      },
      "tasks/20260925-author-metadata-migration/020-rendering-and-generated-output.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "Requirements checklist, item 3 of 5",
            "quote": "Archive, home, tag, sitemap, and other generated paths are audited for legacy author dependencies and continue to build.",
            "why": "Five items, longest 18 words; the one enumerating five surfaces still asserts a single requirement pair (audited, still building) rather than stacking several facts."
          }
        ]
      },
      "tasks/20260925-author-metadata-migration/020-rendering-and-generated-output.md — Unresolved requirement questions": {
        "grade": "readable",
        "findings": [
          {
            "where": "Unresolved questions, bullet 1 of 2",
            "quote": "Confirm whether archive/list pages should gain visible author output or only stop depending on the legacy field.",
            "why": "Two crisp either/or questions, 33 words total, with nothing embedded beyond the question itself."
          }
        ]
      },
      "tasks/20260925-author-metadata-migration/020-rendering-and-generated-output.md — Research and supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "Research facts, bullet 3 of 5",
            "quote": "`_includes/postslist.njk` is shared by the home page, blog archive, and tag pages and currently renders only title/link data.",
            "why": "Five template-anchored bullets (57 words) each carry one current-state fact a reviewer can verify directly."
          }
        ]
      },
      "tasks/20260925-author-metadata-migration/020-rendering-and-generated-output.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "Execution plan, opening paragraph",
            "quote": "Keep archive markup unchanged if the approved requirement is dependency removal only; add bylines only if that open question is approved.",
            "why": "The 73-word paragraph carries one directive per sentence and ties its conditional branch back to the named open question; 15 items sit under four labeled subsections."
          }
        ]
      },
      "tasks/20260925-author-metadata-migration/030-authoring-tool.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "Requirements checklist, item 1 of 4",
            "quote": "The helper accepts the approved structured author input for one or more authors.",
            "why": "Four items, longest 16 words, each covering one boundary of the helper change (input, emitted front matter, default path, tests)."
          }
        ]
      },
      "tasks/20260925-author-metadata-migration/030-authoring-tool.md — Unresolved requirement questions": {
        "grade": "readable",
        "findings": [
          {
            "where": "Unresolved questions, bullet 1 of 2",
            "quote": "Confirm the helper API: an array of author records, a variadic list, or another caller-facing shape.",
            "why": "Two short questions with the candidate options enumerated inline; 39 words total."
          }
        ]
      },
      "tasks/20260925-author-metadata-migration/030-authoring-tool.md — Research and supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "Research facts, bullet 1 of 2",
            "quote": "`scripts/new-post.js` currently exports `frontMatter(title, author)` and interpolates the scalar directly into `author`.",
            "why": "Two bullets pairing a current-state fact with its consequence for testing; 35 words total."
          }
        ]
      },
      "tasks/20260925-author-metadata-migration/030-authoring-tool.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "Execution plan, opening paragraph",
            "quote": "If scalar compatibility is retained temporarily, make it an explicit adapter with a removal marker rather than allowing it to remain the undocumented default.",
            "why": "The lightest plan in the set (232 words, 56-word paragraph, 12 items); the compatibility conditional is one self-contained sentence."
          }
        ]
      },
      "tasks/20260925-author-metadata-migration/040-legacy-retirement.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "Requirements checklist, item 1 of 5",
            "quote": "The repository contains no supported content, template, feed, helper, or test path that depends on singular `author`.",
            "why": "Five items, longest 17 words; the surface-enumerating item still states one testable condition rather than several facts."
          }
        ]
      },
      "tasks/20260925-author-metadata-migration/040-legacy-retirement.md — Research and supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "Research facts, bullet 2 of 2",
            "quote": "Existing tests are placeholders, so the gate must include real build execution and content inspection rather than treating test collection as evidence.",
            "why": "Two fact-plus-consequence bullets (49 words); the load-bearing placeholder caveat sits in the section built for it rather than buried in the plan."
          }
        ]
      },
      "tasks/20260925-author-metadata-migration/040-legacy-retirement.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "Execution plan, opening paragraph",
            "quote": "Once the gate passes, remove the legacy normalization/rejection allowance, add a regression that fails on singular front matter or emitted helper output, and update documentation.",
            "why": "The densest subtask plan (358 words with an 85-word paragraph) still reads as one gate procedure, and its seven-item checklist restates the sequence as discrete actions; the prose staging of the failure branch is flagged in mistakes."
          }
        ]
      }
    },
    "navigation": {
      "grade": "navigable",
      "findings": [
        {
          "where": "All subtask files, header lines",
          "quote": "Parent Task: tasks/20260925-author-metadata-migration/000-main.md",
          "why": "Every subtask file opens with its goal paragraph, parent link, and an explicit Depends On line, so the 010→020→030→040 order is recoverable from the first lines without reading the bodies."
        },
        {
          "where": "Every file, first line under '## Execution plan'",
          "quote": "Status: Draft",
          "why": "Plan status is the first line of the Execution plan section in all five files, so current state is findable from the heading alone."
        },
        {
          "where": "000-main, Subtasks section",
          "quote": "owns post rendering, archive traversal, feeds, and production-build evidence",
          "why": "The main file's Subtasks section indexes all four subtask files with their ownership scopes, giving the set a single entry point."
        },
        {
          "where": "Cross-references throughout (e.g., 000-main Requirement verification; 010 Execution plan)",
          "quote": "as specified by subtask 020",
          "why": "References use bare subtask numbers rather than paths; the mapping requires one inference from the numeric filename prefixes shown in the Subtasks index."
        },
        {
          "where": "000-main, subsection under Execution plan",
          "quote": "Implementation decisions and open questions",
          "why": "Open decisions live in two places per file (top-level 'Unresolved requirement questions' and this subsection), though the subsection mostly cross-references the former ('remain blocked on the unresolved schema question above') instead of duplicating it."
        }
      ]
    },
    "mistakes": [
      {
        "where": "000-main, Unresolved requirement questions, bullet 1",
        "quote": "Confirm the public structured shape. Recommendation: replace `author` with an ordered `authors` array of objects such as `{ name: \"Ada Example\" }` so the model can grow without another front-matter migration. An ordered array of strings is a smaller alternative, but it is less extensible.",
        "why": "One checkbox stacks the open question, the recommended answer, and the rejected alternative; the reader must untangle which part is still undecided versus already steered."
      },
      {
        "where": "000-main, Unresolved requirement questions, bullet 2",
        "quote": "The current archive/list include displays titles only, so the minimum safe interpretation is to audit it for legacy reads and verify unchanged output; adding archive bylines would be a separate user-visible design choice.",
        "why": "Question, current-state fact, chosen default, and scope boundary share one list item; the actual open decision is one clause among four statements."
      },
      {
        "where": "000-main, Execution plan, Requirement verification",
        "quote": "Legacy rejection: combine repository-wide source/content search, migrated content inspection, clean generated-output inspection, and the regression guard from subtask 040.",
        "why": "Four distinct evidence duties are compressed into a single comma-chained bullet; turning it into separate actions requires re-reading the list."
      },
      {
        "where": "000-main, Execution plan, opening paragraph",
        "quote": "First define and document the approved structured field and a temporary adapter that can read legacy content. Migrate every checked-in post and update the authoring helper to produce the new shape.",
        "why": "This 81-word paragraph narrates the same five stages that the numbered list directly beneath it enumerates, so the plan is presented twice back-to-back and the section grows to 546 words."
      },
      {
        "where": "040, Execution plan, opening paragraph",
        "quote": "If any supported path still needs the old field, retain compatibility and record the gap rather than rejecting it.",
        "why": "The load-bearing failure branch of the evidence gate is a mid-paragraph sentence inside an 85-word prose procedure instead of a list step, so a skimming reader can miss that the gate has a retain-compatibility outcome."
      },
      {
        "where": "040, Requirement verification, bullet 1",
        "quote": "Decisive evidence is the combined real build plus generated-output inspection, migrated-content inventory, authoring-helper output checks, and repository-wide legacy dependency search.",
        "why": "Same comma-chain bundling as the parent file: four evidence classes in one sentence that the reader must decompose to act on."
      },
      {
        "where": "020, Requirements checklist, item 4",
        "quote": "Existing URLs and non-author page content remain intact unless a separately approved archive-byline change is made.",
        "why": "A checkbox item carries a hidden conditional ('unless...') that couples this requirement to the unresolved archive question; the exception is easy to skim past in a checklist."
      }
    ],
    "summary": "A consistently templated five-file set: every file opens with a goal paragraph plus Parent Task/Depends On links, the shared skeleton (Requirements checklist, Unresolved requirement questions, Research and supporting facts, Execution plan with a Status line) matches its content, and outcome, constraints, open questions, and plan status are all findable from headings alone — navigation is navigable. All 21 sections read in one pass; the heaviest (000-main's 546-word Execution plan) is segmented into a short strategy paragraph, a numbered five-step boundary, and four labeled subsections, and its all-unchecked boxes are semantically correct for a Draft plan. Residual strain is localized, not structural: the two unresolved-question bullets in 000-main bundle question, recommendation, and discarded alternative; the Requirement verification blocks in 000-main and 040 compress four evidence classes into single comma-chained bullets; and the 81–85-word procedural paragraphs in those two files stage order-sensitive steps — including 040's retain-compatibility failure branch — in prose rather than as list steps."
  }
}
