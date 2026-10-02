# Session — tg06-eleventy-author-migration-decomposition · file-readability-assessment-gpt-max-s0 · glm max

- Run: `20260928T205541.968327Z-task-guidance-file-readability-tg06-eleventy-author-migration-decomposition-gpt-max-s0-c1efb36a`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `cd647195f271567e…`)
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

#### tasks/20260926-author-metadata-migration/000-main.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-author-metadata-migration/000-main.md — Requirements checklist | 171 | 0 | 0 | 7 | 11 | 0 | 0 | 0 | 1 |
| tasks/20260926-author-metadata-migration/000-main.md — Scope and workstreams | 95 | 2 | 16 | 4 | 14 | 0 | 0 | 0 | 1 |
| tasks/20260926-author-metadata-migration/000-main.md — Requirement questions and decisions | 217 | 0 | 0 | 5 | 13 | 0 | 0 | 0 | 5 |
| tasks/20260926-author-metadata-migration/000-main.md — Research and supporting facts | 170 | 0 | 0 | 8 | 13 | 0 | 0 | 0 | 26 |
| tasks/20260926-author-metadata-migration/000-main.md — Subtasks | 16 | 0 | 0 | 4 | 1 | 0 | 0 | 0 | 0 |
| tasks/20260926-author-metadata-migration/000-main.md — Requirement ownership | 72 | 0 | 0 | 4 | 11 | 0 | 0 | 0 | 6 |
| tasks/20260926-author-metadata-migration/000-main.md — Execution plan | 753 | 5 | 62 | 24 | 13 | 5 | 0 | 0 | 18 |

#### tasks/20260926-author-metadata-migration/010-schema-compatibility.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-author-metadata-migration/010-schema-compatibility.md — Requirements checklist | 102 | 0 | 0 | 5 | 11 | 0 | 0 | 0 | 2 |
| tasks/20260926-author-metadata-migration/010-schema-compatibility.md — Requirement questions and decisions | 62 | 0 | 0 | 3 | 10 | 0 | 0 | 0 | 3 |
| tasks/20260926-author-metadata-migration/010-schema-compatibility.md — Research and supporting facts | 61 | 0 | 0 | 3 | 13 | 0 | 0 | 0 | 1 |
| tasks/20260926-author-metadata-migration/010-schema-compatibility.md — Execution plan | 391 | 4 | 55 | 14 | 14 | 5 | 0 | 0 | 0 |

#### tasks/20260926-author-metadata-migration/020-rendering-output.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-author-metadata-migration/020-rendering-output.md — Requirements checklist | 107 | 0 | 0 | 5 | 12 | 0 | 0 | 0 | 4 |
| tasks/20260926-author-metadata-migration/020-rendering-output.md — Requirement questions and decisions | 60 | 0 | 0 | 3 | 10 | 0 | 0 | 0 | 0 |
| tasks/20260926-author-metadata-migration/020-rendering-output.md — Research and supporting facts | 73 | 0 | 0 | 5 | 12 | 0 | 0 | 0 | 7 |
| tasks/20260926-author-metadata-migration/020-rendering-output.md — Execution plan | 426 | 4 | 72 | 16 | 14 | 5 | 0 | 0 | 4 |

#### tasks/20260926-author-metadata-migration/030-content-authoring.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-author-metadata-migration/030-content-authoring.md — Requirements checklist | 99 | 0 | 0 | 5 | 12 | 0 | 0 | 0 | 1 |
| tasks/20260926-author-metadata-migration/030-content-authoring.md — Requirement questions and decisions | 68 | 0 | 0 | 3 | 11 | 0 | 0 | 0 | 0 |
| tasks/20260926-author-metadata-migration/030-content-authoring.md — Research and supporting facts | 72 | 0 | 0 | 4 | 13 | 0 | 0 | 0 | 6 |
| tasks/20260926-author-metadata-migration/030-content-authoring.md — Execution plan | 433 | 4 | 60 | 15 | 14 | 5 | 0 | 0 | 2 |

#### tasks/20260926-author-metadata-migration/040-legacy-retirement.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-author-metadata-migration/040-legacy-retirement.md — Requirements checklist | 104 | 0 | 0 | 5 | 12 | 0 | 0 | 0 | 0 |
| tasks/20260926-author-metadata-migration/040-legacy-retirement.md — Requirement questions and decisions | 65 | 0 | 0 | 3 | 12 | 0 | 0 | 0 | 1 |
| tasks/20260926-author-metadata-migration/040-legacy-retirement.md — Research and supporting facts | 95 | 0 | 0 | 4 | 13 | 0 | 0 | 0 | 0 |
| tasks/20260926-author-metadata-migration/040-legacy-retirement.md — Execution plan | 507 | 4 | 66 | 21 | 14 | 5 | 0 | 0 | 0 |

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
    "sections": {
      "tasks/20260926-author-metadata-migration/000-main.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "checklist item 6",
            "quote": "Produce generated-output and content evidence showing that no supported path still depends on the legacy form before rejecting it, if rejection is selected as the final compatibility state.",
            "why": "This one item stacks two conditional clauses ('before rejecting it', 'if rejection is selected'); it is the only line that needs a second look, while the other six items each carry a single requirement."
          },
          {
            "where": "checklist item 4",
            "quote": "Migrate every existing post to the canonical model without losing author names or their intended order.",
            "why": "Items state one requirement apiece at scannable length, so the seven-line set can be held in a single pass."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/000-main.md — Scope and workstreams": {
        "grade": "readable",
        "findings": [
          {
            "where": "workstream bullets",
            "quote": "The retirement work owns the evidence gate and the final decision to retain compatibility or reject the legacy form.",
            "why": "Four bullets, one boundary each, at roughly a line apiece; the ownership split is graspable in one scan."
          },
          {
            "where": "closing paragraph",
            "quote": "This plan does not authorize implementation. The task files remain `Draft` until execution is explicitly approved.",
            "why": "The load-bearing execution gate sits as the section's final paragraph, after the workstream list, where a reader deciding whether work can start is unlikely to look first; it is findable, but only by reading to the end."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/000-main.md — Requirement questions and decisions": {
        "grade": "partial",
        "findings": [
          {
            "where": "archive presentation bullet",
            "quote": "The current shared `postslist.njk` renders titles and links but no author. Does “archives move to the new model” require adding archive bylines, or should existing archive markup be preserved while all author-aware archive code is audited to use the canonical collection? The plan currently preserves existing visible output unless a byline requirement is approved.",
            "why": "One bullet fuses a repo fact, a two-branch question with a subordinate clause, and the plan's default; the reader must re-read to separate what is being asked from what is already defaulted."
          },
          {
            "where": "final compatibility state bullet",
            "quote": "Recommendation: make rejection a final, explicit phase only after the gate passes; if indefinite compatibility is preferred, document that state and retain the normalizer.",
            "why": "Question, recommendation, and fallback instruction are stacked in one semicolon-joined item; four of the five bullets each carry two or three distinct facts."
          },
          {
            "where": "bold lead-ins",
            "quote": "**Question — canonical entry shape:**",
            "why": "The bold topic labels keep the five open topics scannable without reading every sentence, which is what keeps this section short of unreadable."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/000-main.md — Research and supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "new-post.js bullet",
            "quote": "`scripts/new-post.js` currently accepts `(title, author)` and writes a scalar `author` key.",
            "why": "Each of the eight items names concrete files and paths, so claims can be verified against the repo at a glance."
          },
          {
            "where": "last bullet",
            "quote": "There is no existing `tasks/` tree and no root `docs/index.md`. The maintained development documentation is under `docs/development/`; the documentation guidance has been read before planning this change.",
            "why": "Three unrelated facts share one bullet; the maintained-docs location, which every file's Documentation subsection depends on, is embedded mid-bullet instead of standing alone."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/000-main.md — Subtasks": {
        "grade": "readable",
        "findings": [
          {
            "where": "the four link items",
            "quote": "- [ ] [tasks/20260926-author-metadata-migration/010-schema-compatibility.md](tasks/20260926-author-metadata-migration/010-schema-compatibility.md)",
            "why": "The entire section is four bare file links; nothing to untangle, and the numbering makes the execution order self-evident."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/000-main.md — Requirement ownership": {
        "grade": "readable",
        "findings": [
          {
            "where": "first bullet",
            "quote": "The canonical data contract and transition compatibility requirements are owned by `010-schema-compatibility.md`; the final compatibility state is completed jointly with `040-legacy-retirement.md`.",
            "why": "One item carries two facts (ownership plus a shared completion), but the semicolon split keeps each half a single readable clause; all four items hold in one pass."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/000-main.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "subsection structure",
            "quote": "### Implementation decisions and open questions",
            "why": "The 753-word section is partitioned into five named subsections (decisions, documentation, task checklist, requirement verification, extra verification), so a reader can target blockers or evidence duties without re-reading the prose."
          },
          {
            "where": "opening paragraph",
            "quote": "The migration will use a staged compatibility flow. A single page-data normalizer will expose the approved canonical author collection to every consumer.",
            "why": "At roughly 60 words this is the section's densest paragraph, but it is three short sentences with one idea each; it reads in a single pass."
          },
          {
            "where": "Requirement verification, last bullet",
            "quote": "**Evidence-gated legacy retirement:** Record the content scan, runtime reference audit, pre-retirement generated-output results, and post-retirement build/test results. A rejection change is complete only when all four are clean; otherwise the compatibility fallback remains and the unresolved state is documented.",
            "why": "A four-item noun list plus a conditional consequence in one bullet; the bold label carries the reader, but this is the heaviest item in the section."
          },
          {
            "where": "steps 4–5 and Implementation decisions",
            "quote": "Only after the evidence gate passes, apply the approved final compatibility state: either remove the fallback and reject legacy input with a clear diagnostic, or retain the fallback and document it as supported.",
            "why": "The gate condition recurs in reworded forms across the steps, 'Requirement verification', and 'Implementation decisions', so the reader must reconcile repetitions to confirm they are one constraint, not several."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/010-schema-compatibility.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "fourth item",
            "quote": "Define and test the behavior for canonical input, legacy input, conflicting fields, empty values, and malformed entries according to the approved policy.",
            "why": "A five-case comma enumeration in one item, but it reads left to right; the other four items are single-requirement lines that scan quickly."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/010-schema-compatibility.md — Requirement questions and decisions": {
        "grade": "readable",
        "findings": [
          {
            "where": "recommendation item",
            "quote": "**Recommendation:** Normalize legacy `author: \"Name\"` to a one-entry collection and make all downstream consumers depend only on the normalized value.",
            "why": "Three labeled items (two questions, one recommendation) in 62 words, one sentence each; the open-versus-recommended split is visible at a glance."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/010-schema-compatibility.md — Research and supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "third item",
            "quote": "Eleventy configuration is the natural ownership area for a shared collection/page-data boundary, but the implementation should use the project’s actual data-cascade capabilities rather than scattering template conditionals.",
            "why": "The longest item pairs a claim with a guardrail in one ~30-word sentence; still a single coherent statement, though it is guidance rather than a measured fact."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/010-schema-compatibility.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "second paragraph",
            "quote": "A source item with both fields, an empty collection, or an invalid entry must follow the approved policy and produce an actionable diagnostic if rejection is the chosen behavior.",
            "why": "The densest sentence in the section, but the three-case list and the condition resolve in one pass; paragraphs stay near 55 words."
          },
          {
            "where": "Implementation decisions, first bullet",
            "quote": "The exact canonical entry shape and conflict policy are blocked on the parent requirement questions.",
            "why": "Open blockers are restated locally, so a reader can find what is undecided without returning to the parent file."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/020-rendering-output.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "second item",
            "quote": "Audit `content/blog.njk`, `content/index.njk`, `content/tag-pages.njk`, and `_includes/postslist.njk`; any author presentation or data access uses canonical authors, while existing title/link output remains compatible unless archive bylines are approved.",
            "why": "One item carries four file paths plus two conditional policies; the semicolon split keeps it parseable, but it is the densest checklist line in the corpus."
          },
          {
            "where": "fifth item",
            "quote": "Replace the placeholder archive and author-output test files with executable generated-output evidence.",
            "why": "The remaining items are one-deliverable lines, so the section overall scans quickly despite the heavy second item."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/020-rendering-output.md — Requirement questions and decisions": {
        "grade": "readable",
        "findings": [
          {
            "where": "second question",
            "quote": "**Question:** Confirm the feed representation for multiple authors (for example, repeated author elements or another schema-compatible form).",
            "why": "Three short labeled items in 60 words; the parenthetical example keeps the open choice concrete without extra prose."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/020-rendering-output.md — Research and supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "sitemap bullet",
            "quote": "`content/sitemap.xml.njk` has no author dependency but should be included in the build regression because a template/data failure can affect the full generated site.",
            "why": "Five items, each one file-level fact plus its consequence; code spans keep the targets concrete and scannable."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/020-rendering-output.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "first paragraph, final sentence",
            "quote": "Do not add archive markup solely to create a test if the archive byline question is not approved; do verify that the shared list path does not read the legacy field.",
            "why": "A negated instruction and an affirmative instruction with different conditions are fused into one ~30-word sentence; it takes a beat, but resolves without a re-read."
          },
          {
            "where": "second paragraph",
            "quote": "Assert the resulting post page, home page, blog archive, tag page, feed, and sitemap.",
            "why": "Six-surface lists recur across the paragraphs and verification items, which makes the plan repetitive to scan but predictable to navigate."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/030-content-authoring.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "the five items",
            "quote": "Prove that front matter emitted by the authoring helper can enter the real Eleventy content pipeline and produce correct post and feed output.",
            "why": "Each item names one deliverable at roughly a line; no compound conditionals slow the scan."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/030-content-authoring.md — Requirement questions and decisions": {
        "grade": "readable",
        "findings": [
          {
            "where": "second question",
            "quote": "**Question:** Confirm whether a one-author convenience input remains supported by the helper while always serializing the canonical collection.",
            "why": "Three labeled, single-sentence items in 68 words; the API decision and the serialization rule are cleanly separated."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/030-content-authoring.md — Research and supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "fourth item",
            "quote": "The build consumes `content/` directly, so a generated fixture can exercise the helper and production Eleventy path without mocking page data.",
            "why": "Four facts, each a statement about a concrete file or path with its implication attached; holdable in one pass."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/030-content-authoring.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "third paragraph, first sentence",
            "quote": "For the decisive integration check, invoke the helper to create front matter for a temporary or dedicated test post, place that post through the same Eleventy input pipeline used by production, run the real build, and assert the post and feed output.",
            "why": "One sentence chains five imperatives — prose standing in for a list — and is the densest moment of the section; the surrounding three-paragraph phase split (inventory, helper, integration) keeps the whole recoverable."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/040-legacy-retirement.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "third item",
            "quote": "Apply the approved final state only after the evidence gate passes: remove the fallback and reject legacy input with a clear diagnostic, or retain the fallback and document it as supported.",
            "why": "Both branches of the final decision restated in one item, but the colon-and-either/or shape keeps the two paths distinct on first read."
          },
          {
            "where": "first item",
            "quote": "Do not reject legacy input while any supported content, template, feed, archive, or authoring path still depends on it.",
            "why": "A standing prohibition phrased as a checkable box rather than a completable task; readable, but it mixes a rule into a work checklist."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/040-legacy-retirement.md — Requirement questions and decisions": {
        "grade": "readable",
        "findings": [
          {
            "where": "the three items",
            "quote": "**Recommendation:** Prefer explicit rejection after a clean gate if the project wants to prevent regression, but do not make that choice silently.",
            "why": "65 words across three labeled items; the open decision and its recommendation are separated by labels, so nothing has to be untangled."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/040-legacy-retirement.md — Research and supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "fourth item",
            "quote": "Task files and documentation may mention the legacy field as historical or transition information; the runtime/content audit must classify those mentions rather than treating every textual occurrence as a product dependency.",
            "why": "The longest item (~35 words) embeds an audit rule inside a fact list; it is load-bearing for the gate but still one coherent statement."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/040-legacy-retirement.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "numbered gate",
            "quote": "1. Every supported post source has the canonical field and no legacy front-matter key.",
            "why": "The gate is an explicit four-condition numbered list with a recorded result, the clearest decision structure in the corpus; a reader can check each condition against evidence directly."
          },
          {
            "where": "opening paragraph",
            "quote": "Before changing compatibility behavior, run a clean inventory over all post source files, inspect runtime references in templates, configuration, scripts, and tests, and run the real production build with the canonical content.",
            "why": "The ~66-word opening paragraph chains three multi-object imperatives; parseable, but the densest prose in the file."
          },
          {
            "where": "gate preamble and Requirement verification",
            "quote": "Only after all four conditions pass may the chosen final state be applied.",
            "why": "The gate condition is stated a third time here after the checklist items and the requirements list, in reworded form; the repetitions agree but cost the reader a reconciliation pass."
          }
        ]
      }
    },
    "navigation": {
      "grade": "navigable",
      "findings": [
        {
          "where": "subtask file headers (e.g. 040-legacy-retirement.md)",
          "quote": "Depends On:\n- tasks/20260926-author-metadata-migration/020-rendering-output.md\n- tasks/20260926-author-metadata-migration/030-content-authoring.md",
          "why": "Parent and dependency lines sit directly under each title, so sequencing and ownership are answerable from structure alone, reinforced by the 000/010/020/030/040 filename order."
        },
        {
          "where": "000-main.md — Requirement ownership",
          "quote": "The post, archive/list, feed, and generated-page requirements are owned by `020-rendering-output.md`.",
          "why": "The requirement-to-file map lets a reader route any checklist item to its owning subtask without opening the subtasks."
        },
        {
          "where": "each file's Execution plan heading",
          "quote": "Status: Draft",
          "why": "Plan status exists only as a bare line under 'Execution plan', not beside the title or the checkboxes, so a reader skimming the top of a file finds the outcome and constraints but not the state; the string 'Status' is at least trivially findable once the heading is reached."
        },
        {
          "where": "repeated section order across all five files",
          "quote": "Requirements checklist → Requirement questions and decisions → Research and supporting facts → Execution plan",
          "why": "The identical section template makes open questions and constraints predictable by position; the cost is that four overlapping checkbox lists per corpus (Requirements, Subtasks, per-file Task checklists) leave the reader to infer which list is authoritative for progress."
        }
      ]
    },
    "mistakes": [
      {
        "where": "000-main.md — Scope and workstreams, closing paragraph",
        "quote": "This plan does not authorize implementation. The task files remain `Draft` until execution is explicitly approved.",
        "why": "A load-bearing execution-governance fact is buried as the tail of a scope section, far from the 'Status: Draft' line under Execution plan; the two statements that control whether work may start live in different sections."
      },
      {
        "where": "000-main.md — Subtasks vs Execution plan › Task checklist",
        "quote": "- [ ] Complete `010-schema-compatibility.md`.",
        "why": "The same four subtask files are tracked in two separate unchecked checkbox lists within one file (Subtasks and Task checklist), with no cross-reference; a maintainer marking progress must reconcile both lists and neither acknowledges the other."
      },
      {
        "where": "000-main.md — Requirement questions and decisions, archive bullet",
        "quote": "Does “archives move to the new model” require adding archive bylines, or should existing archive markup be preserved while all author-aware archive code is audited to use the canonical collection?",
        "why": "One list item stacks a repo fact, a two-branch question, and the plan's default behavior across three sentences; the reader must re-read to separate what is asked from what is already decided."
      },
      {
        "where": "000-main.md — Research and supporting facts, last bullet",
        "quote": "There is no existing `tasks/` tree and no root `docs/index.md`. The maintained development documentation is under `docs/development/`; the documentation guidance has been read before planning this change.",
        "why": "Three unrelated facts share one bullet; the maintained-docs path that every file's Documentation subsection depends on is embedded mid-bullet rather than standing alone."
      },
      {
        "where": "020-rendering-output.md — Execution plan, first paragraph",
        "quote": "Do not add archive markup solely to create a test if the archive byline question is not approved; do verify that the shared list path does not read the legacy field.",
        "why": "A negated instruction and an affirmative instruction with different conditions are fused into one sentence; misreading the scope of either clause on first pass is easy."
      },
      {
        "where": "000-main.md — Execution plan › Additional implementation verification vs 020-rendering-output.md — Execution plan › Requirement verification",
        "quote": "Check that the migration does not create `[object Object]`, `undefined`, duplicate feed authors, or empty bylines in generated output. / assert no `undefined`, `[object Object]`, empty byline, or duplicate author output is produced.",
        "why": "The same four-way output check is stated twice in different wording in different files with no pointer between them; the reader must compare copies to confirm they are one requirement."
      },
      {
        "where": "040-legacy-retirement.md — Requirement questions and decisions, third bullet",
        "quote": "**Decision required by the request:** The gate must include both source content evidence and generated-output evidence; a repository search alone is insufficient.",
        "why": "Labeled under 'questions and decisions' but it is a fixed constraint, not an open question or a decision, and it restates the same gate rule already given in 000-main in a third phrasing."
      },
      {
        "where": "010-schema-compatibility.md — Research and supporting facts, third item",
        "quote": "the implementation should use the project’s actual data-cascade capabilities rather than scattering template conditionals",
        "why": "Prescriptive implementation guidance sits under a heading whose other entries are measured repo facts, blurring what the reader can treat as verified versus advised."
      }
    ],
    "summary": "All five files share one template — title/intro, Requirements checklist, Questions, Research, then an Execution plan with five fixed subsections — plus explicit Parent/Depends On headers and zero-padded filenames, so outcome, constraints, open questions, ownership, and status are all findable from structure alone: navigation is navigable. Nothing reaches a prose wall; the worst paragraphs run 55–72 words and the section splitting absorbs the largest plan (753 words in 000-main). The recurring strain is compound list items: 000-main's five question bullets each stack a question, a fact, and a default (the only partial section), and similar fused do/don't or multi-fact items recur in the checklists and plans. The other presentation costs are buried load-bearing facts (the no-implementation gate at the end of Scope and workstreams; the docs path inside a research bullet), duplicate unchecked tracking of the same four subtasks within 000-main, and the evidence-gate and output checks restated in reworded form across sections and files, which costs the reader a reconciliation pass but never loses the thread."
  }
}
```
