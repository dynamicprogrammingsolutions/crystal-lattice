# Session — tg06-eleventy-author-migration-decomposition · file-readability-assessment-gpt-xhigh-s0 · glm max

- Run: `20260928T205305.515358Z-task-guidance-file-readability-tg06-eleventy-author-migration-decomposition-gpt-xhigh-s0-515af935`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `39cef8b9cdae2ce6…`)
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
| tasks/20260926-author-metadata-migration/000-main.md — Requirements checklist | 133 | 0 | 0 | 5 | 12 | 0 | 0 | 0 | 1 |
| tasks/20260926-author-metadata-migration/000-main.md — Unresolved requirement questions | 130 | 0 | 0 | 3 | 15 | 0 | 0 | 0 | 2 |
| tasks/20260926-author-metadata-migration/000-main.md — Research and supporting facts | 126 | 0 | 0 | 8 | 13 | 0 | 0 | 0 | 21 |
| tasks/20260926-author-metadata-migration/000-main.md — Execution plan | 277 | 3 | 81 | 6 | 13 | 0 | 0 | 0 | 3 |
| tasks/20260926-author-metadata-migration/000-main.md — Subtasks | 392 | 1 | 51 | 19 | 14 | 5 | 0 | 0 | 9 |

#### tasks/20260926-author-metadata-migration/010-source-and-authoring.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-author-metadata-migration/010-source-and-authoring.md — Requirements checklist | 54 | 0 | 0 | 3 | 11 | 0 | 0 | 0 | 1 |
| tasks/20260926-author-metadata-migration/010-source-and-authoring.md — Unresolved requirement questions | 26 | 0 | 0 | 1 | 12 | 0 | 0 | 0 | 1 |
| tasks/20260926-author-metadata-migration/010-source-and-authoring.md — Research and supporting facts | 60 | 0 | 0 | 4 | 12 | 0 | 0 | 0 | 6 |
| tasks/20260926-author-metadata-migration/010-source-and-authoring.md — Execution plan | 408 | 3 | 66 | 18 | 13 | 5 | 0 | 0 | 5 |

#### tasks/20260926-author-metadata-migration/020-public-rendering.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-author-metadata-migration/020-public-rendering.md — Requirements checklist | 52 | 0 | 0 | 2 | 11 | 0 | 0 | 0 | 0 |
| tasks/20260926-author-metadata-migration/020-public-rendering.md — Unresolved requirement questions | 21 | 0 | 0 | 1 | 13 | 0 | 0 | 0 | 0 |
| tasks/20260926-author-metadata-migration/020-public-rendering.md — Research and supporting facts | 80 | 0 | 0 | 5 | 11 | 0 | 0 | 0 | 9 |
| tasks/20260926-author-metadata-migration/020-public-rendering.md — Execution plan | 444 | 4 | 65 | 18 | 14 | 5 | 0 | 0 | 11 |

#### tasks/20260926-author-metadata-migration/030-legacy-cutover.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-author-metadata-migration/030-legacy-cutover.md — Requirements checklist | 49 | 0 | 0 | 2 | 12 | 0 | 0 | 0 | 1 |
| tasks/20260926-author-metadata-migration/030-legacy-cutover.md — Unresolved requirement questions | 22 | 0 | 0 | 1 | 14 | 0 | 0 | 0 | 0 |
| tasks/20260926-author-metadata-migration/030-legacy-cutover.md — Research and supporting facts | 61 | 0 | 0 | 3 | 13 | 0 | 0 | 0 | 1 |
| tasks/20260926-author-metadata-migration/030-legacy-cutover.md — Execution plan | 508 | 3 | 70 | 20 | 14 | 5 | 0 | 0 | 3 |

The produced task files:

### tasks/20260926-author-metadata-migration/000-main.md

````markdown
# Migrate post author metadata to structured multi-author records

Plan the migration from the single `author` front-matter string to a structured
multi-author representation while preserving existing content, routes, and
generated pages throughout the transition.

## Requirements checklist

- [ ] R1. Posts use an approved structured metadata form that represents one or
  more authors without losing each author's display name.
- [ ] R2. Every existing post is migrated safely to the new form, preserving
  its author data and all existing generated URLs/content.
- [ ] R3. The post layout, shared post-list/archive paths, tag pages, and feed
  consume the new author model and render valid output for one and multiple
  authors.
- [ ] R4. The post-authoring helper writes the new form for newly created posts
  and does not create new dependencies on the legacy field.
- [ ] R5. Legacy `author` metadata is tolerated only during the migration
  window and is rejected or removed only after repository-content and
  production-generated-output evidence demonstrates that no supported path
  still depends on it.

## Unresolved requirement questions

- Q1. What is the canonical record shape? Recommended target: an `authors`
  sequence of objects with a required `name` field, leaving room for a stable
  identifier or profile URL later. Confirm whether names alone are sufficient
  or whether identity/link fields are required now.
- Q2. Should archive, home, and tag list entries begin displaying all author
  names, or should they retain their current title-only presentation while
  becoming safe consumers of the new metadata? The current shared list emits
  titles only, so adding author text would be a user-visible presentation
  change.
- Q3. After the evidence gate, should legacy front matter fail the build with a
  validation error, or should it be ignored as unsupported input? A clear
  build-time error is recommended so an accidental regression cannot silently
  lose author data.

## Research and supporting facts

- `content/posts/first.md` and `content/posts/second.md` are the only current
  posts; both use a quoted scalar `author` value.
- `_includes/layouts/post.njk` renders `author` directly.
- `content/feed.xml.njk` reads `post.data.author` directly.
- `_includes/postslist.njk` currently renders only title and URL, but it is
  shared by `content/index.njk`, `content/blog.njk`, and
  `content/tag-pages.njk`; those archive paths still need production-build
  coverage during the migration.
- `scripts/new-post.js` exports `frontMatter(title, author)` and writes the
  legacy field, making it the authoring boundary for new content.
- `tests/archive-output.test.js` and `tests/author-output.test.js` contain
  comments only; they do not currently collect or assert behavior.
- `README.md` documents the generated site at a high level. There is no
  existing author-metadata guide or checked-in generated `_site`.
- `package.json` provides `npm run build` and `npm test`; no lockfile or
  `node_modules` directory is present in the inspected worktree.

## Execution plan

Status: Draft

The proposed design uses a canonical `authors` sequence of author records and
keeps a read-only compatibility normalization for legacy `author` input during
the migration window. Source migration and the authoring helper stop producing
the legacy key. Rendering consumes one normalized sequence, so the post page
can render all names and the feed can emit the appropriate author elements
without interpolating an object as a string. The archive/list paths retain
their existing routes and presentation unless Q2 approves an author display
change.

Legacy support is not removed as part of source conversion or template
conversion. The final cutover is a separate dependent boundary: first scan
content and implementation references, then run the real Eleventy build and
inspect the post, archive, tag, home, and feed outputs. Only passing evidence
may authorize deleting the compatibility path and enabling the approved
legacy-input rejection behavior.

Ordered work:

1. Resolve Q1–Q3 and record the approved schema, archive presentation, and
   post-cutover invalid-input behavior.
2. Define the normalized author contract, migrate the existing post files, and
   update `scripts/new-post.js` so newly authored content uses the canonical
   form.
3. Update the post layout, feed, and shared archive/list consumers to use the
   normalized multi-author data while preserving routes and valid output.
4. Replace placeholder tests with production-path checks for migrated content,
   single- and multi-author rendering, all archive routes, and the feed.
5. Run the content-reference and generated-output evidence gate. If it passes,
   remove legacy production dependencies and add the approved regression check
   for rejected legacy input; otherwise keep compatibility and record the
   remaining dependency.
6. Update the maintained developer documentation with the current metadata
   shape and authoring/migration behavior in the same change as the final
   implementation.

## Subtasks

- [ ] `tasks/20260926-author-metadata-migration/010-source-and-authoring.md`
- [ ] `tasks/20260926-author-metadata-migration/020-public-rendering.md`
- [ ] `tasks/20260926-author-metadata-migration/030-legacy-cutover.md`

### Implementation decisions and open questions

- The task remains Draft until the canonical record shape, archive
  presentation, and post-cutover legacy-input behavior are approved.
- The compatibility reader belongs to the transition, not the final contract;
  no child may remove it before the cutover child records both content and
  generated-output evidence.
- The migration must preserve existing route paths and post body content. Any
  desired new author links or identifiers should be added only if Q1 approves
  them.

### Documentation

Update `README.md` or the nearest existing developer-facing documentation
section, rather than creating an empty documentation hierarchy. Document the
canonical front-matter shape, how the authoring helper creates it, the
temporary legacy compatibility state while applicable, and the final
unsupported-input behavior. Keep the documentation change with the
implementation that makes each claim true.

### Task checklist

- [ ] Resolve the three requirement questions before marking this plan
  Approved.
- [ ] Complete the source/content/authoring child.
- [ ] Complete the public-rendering child.
- [ ] Complete the evidence-gated cutover child.
- [ ] Update the requirement evidence and parent status as each child closes.

### Requirement verification

- R1: A production build of representative single- and multi-author source
  posts, backed by a direct authoring-helper assertion, proves that the
  approved structured records survive parsing and render as intended.
- R2: A repository-wide content scan plus the production build verifies that
  every existing post has the new metadata, retains its author names, and
  preserves existing post/archive/tag URLs and body output.
- R3: One real `npm run build` followed by assertions over the post page,
  `/`, `/blog/`, generated tag pages, and `/feed/feed.xml` is the decisive
  check across the shared templates and public generation paths.
- R4: The authoring-helper test verifies the emitted front matter, and a
  generated post created from that output is consumed by the same Eleventy
  build used for R3.
- R5: The final cutover records both (a) no remaining legacy-key dependencies
  in source content/templates/tools/tests and (b) successful generated-output
  inspection for every affected route before any rejection is enabled.

### Additional implementation verification

- Check for accidental `[object Object]`, missing names, malformed feed
  elements, duplicate author output, and unsafe escaping in generated HTML/XML.
- Compare the route set before and after migration so metadata changes do not
  silently alter permalink, archive, tag, or feed generation.
- Keep the transition testable without changing production paths or adding a
  test-only data shortcut.
````

### tasks/20260926-author-metadata-migration/010-source-and-authoring.md

````markdown
# Define and migrate the structured author source model

Own the canonical post metadata contract, migration of existing front matter,
and the authoring helper that creates new posts.

Parent Task: `tasks/20260926-author-metadata-migration/000-main.md`

Depends On: None

## Requirements checklist

- [ ] R1. The approved structured author form represents one or more authors
  and preserves each author's display name.
- [ ] R2. All existing post front matter is migrated without losing author
  values, post bodies, or route-defining metadata.
- [ ] R4. `scripts/new-post.js` emits only the approved structured form for new
  posts.

## Unresolved requirement questions

- Q1. Confirm whether the canonical author records contain only a required
  `name` or also stable identity/profile fields; do not add fields during
  migration without approval.

## Research and supporting facts

- `content/posts/first.md` and `content/posts/second.md` are the complete
  current content inventory and each has one legacy author string.
- `scripts/new-post.js` is a small exported helper and currently accepts one
  `author` argument, then writes `author: "..."`.
- No schema validator or migration utility currently exists.
- The source migration must leave a compatibility read path available until
  `030-legacy-cutover.md` completes its evidence gate.

## Execution plan

Status: Draft

Use the approved canonical `authors` sequence as the only write format. Each
record must preserve the existing display name exactly; any additional fields
are included only if Q1 approves them. During the transition, expose one
normalization contract that turns a legacy scalar into a singleton sequence
for consumers that still need to read unmigrated content. This child does not
remove that fallback or reject legacy input.

Ordered work:

1. Record the approved author record shape and validation rules in the
   implementation and task evidence.
2. Update the authoring helper API and its tests so generated front matter
   contains the new key and supports one or multiple author records.
3. Migrate every current post, checking that titles, bodies, dates/URLs, tags,
   and author names remain unchanged.
4. Add source-level checks that prevent the helper or migrated fixtures from
   reintroducing the legacy write form.
5. Update the maintained developer documentation with the new authoring
   example, leaving any transition note clearly marked until cutover.

### Implementation decisions and open questions

- Q1 controls whether records contain only `name` or also identity/profile
  fields; do not invent stable identifiers during migration.
- Preserve exact existing name text, including spaces and punctuation.
- Compatibility reading is deliberately deferred to the rendering and final
  cutover boundaries; this child must not make legacy content fail early.

### Documentation

Document the canonical front-matter example and the authoring-helper input in
the existing developer-facing documentation location selected by the parent
task. Do not describe legacy input as current guidance after cutover.

### Task checklist

- [ ] Confirm the approved structured schema.
- [ ] Update and test the authoring helper.
- [ ] Migrate and inspect every existing post.
- [ ] Add source-level regression coverage.
- [ ] Update the maintained metadata/authoring documentation.

### Requirement verification

- R1: The authoring-helper test asserts the exact structured front matter for
  both one and multiple authors; the downstream production build in
  `020-public-rendering.md` confirms Eleventy consumes it.
- R2: A complete content inventory check verifies that each existing post has
  the canonical key and the same author names and body content; the real
  production build verifies the migrated files remain publishable.
- R4: A test invokes `scripts/new-post.js`, parses the returned front matter,
  and asserts that it writes the canonical key and never writes a new legacy
  `author` field.

### Additional implementation verification

- Exercise quoting, punctuation, and multiple records in front matter so the
  migration does not depend on names being plain ASCII or single-word values.
- Confirm no unrelated front-matter keys are rewritten as a side effect.
````

### tasks/20260926-author-metadata-migration/020-public-rendering.md

````markdown
# Render structured authors through public site generation

Own the post layout, feed, shared archive/list consumers, and production-build
evidence that the new model works across generated pages.

Parent Task: `tasks/20260926-author-metadata-migration/000-main.md`

Depends On: `tasks/20260926-author-metadata-migration/010-source-and-authoring.md`

## Requirements checklist

- [ ] R3. Individual posts, feeds, and all archive/list generation paths
  consume structured authors and produce valid output for single- and
  multi-author posts while preserving existing routes.
- [ ] The rendering transition continues to handle a legacy scalar as a
  singleton author only until the final cutover evidence is accepted.

## Unresolved requirement questions

- Q2. Confirm whether archive, home, and tag list entries should display all
  author names or retain their current title-only presentation.

## Research and supporting facts

- `_includes/layouts/post.njk` currently interpolates `author` directly.
- `content/feed.xml.njk` currently interpolates `post.data.author` directly
  inside one `<author>` element per entry.
- `_includes/postslist.njk` is shared by the home page, `/blog/`, and tag
  pagination. It currently renders only title and link, so its collection
  iteration must be checked even if Q2 keeps the title-only presentation.
- `content/tag-pages.njk` creates tag URLs from `collections`; the migration
  must not alter this pagination or its route shape.
- Existing tests do not execute Eleventy or inspect generated files.

## Execution plan

Status: Draft

Normalize each post to an author-record sequence before presentation. The post
layout should render every approved author according to Q2, and the feed should
emit valid author data for every record without stringifying objects or
silently dropping additional authors. The shared list should be updated or
verified as a structured-data consumer while retaining its current route and
title behavior unless Q2 approves visible author names.

The compatibility normalization remains active here because old content may
still exist during the transition. No template should continue to depend
directly on `post.data.author` after the new path is proven.

Ordered work:

1. Add the normalized author-record access used by the post layout and feed.
2. Update shared list/archive consumers and confirm home, blog, and tag
   pagination remain valid under the new post data.
3. Add representative single- and multi-author source fixtures through normal
   content paths, not test-only renderer shortcuts.
4. Replace placeholder tests with a production build and assertions over the
   generated post, home page, blog archive, tag page, and feed.
5. Record route and output evidence for the cutover child, including checks
   for missing, duplicated, object-stringified, or malformed author output.

### Implementation decisions and open questions

- Q2 determines whether archive/list items gain visible author text. If it
  remains title-only, the shared list still must not assume a scalar author or
  break when records are present.
- Preserve the existing `/`, `/blog/`, `/tags/*`, post, and feed paths.
- Keep the legacy normalization as an explicit transitional boundary so the
  cutover child can remove and test it deliberately.

### Documentation

Provide the parent task with verified output examples and update the
maintained developer documentation if the approved presentation or feed
semantics are user-visible. Do not document the temporary fallback as a
permanent contract.

### Task checklist

- [ ] Implement the normalized author rendering path.
- [ ] Update all shared archive/list and feed consumers.
- [ ] Add realistic single- and multi-author production inputs.
- [ ] Replace placeholder tests with build-backed output assertions.
- [ ] Record route and generated-output evidence for cutover.

### Requirement verification

- R3: Run `npm run build` and inspect the actual `_site` files for an
  individual post, `/index.html`, `/blog/index.html`, a generated tag page,
  and `/feed/feed.xml`; assert every approved author is represented and all
  existing routes remain present.
- Transitional compatibility: build a representative legacy scalar input
  before cutover and verify it still renders through the normalized sequence;
  this check is removed or inverted only by `030-legacy-cutover.md`.

### Additional implementation verification

- Validate HTML/XML escaping for author names containing punctuation.
- Assert that no generated output contains `[object Object]`, an empty author
  element, or an unexpected duplicate.
- Keep the archive and tag checks on the real Eleventy collection/pagination
  path so a mocked collection cannot hide template incompatibilities.
````

### tasks/20260926-author-metadata-migration/030-legacy-cutover.md

````markdown
# Gate and complete legacy author-field removal

Own the final compatibility decision: collect content and generated-output
evidence, then remove or reject the legacy form only when the evidence gate
passes.

Parent Task: `tasks/20260926-author-metadata-migration/000-main.md`

Depends On:

- `tasks/20260926-author-metadata-migration/010-source-and-authoring.md`
- `tasks/20260926-author-metadata-migration/020-public-rendering.md`

## Requirements checklist

- [ ] R5. Legacy `author` input is removed or rejected only after both source
  content and production-generated-output evidence show that supported paths
  no longer depend on it.
- [ ] The final behavior for an accidental legacy post is explicit, tested,
  and consistent with the approved post-cutover policy.

## Unresolved requirement questions

- Q3. Confirm whether accidental legacy input must fail the build with a clear
  validation error or use another explicit unsupported-input behavior.

## Research and supporting facts

- Legacy references currently exist in both source content and production
  consumers: two post files, the post layout, the feed, and the authoring
  helper.
- The existing test files are comments only, so no current evidence can
  authorize a cutover.
- There is no checked-in `_site`; generated-output evidence must come from a
  fresh real Eleventy build after the preceding migration/rendering work.

## Execution plan

Status: Draft

Treat legacy removal as an evidence-gated compatibility state, not as a
cleanup step. First establish a complete source scan for legacy keys and
direct field reads. Then run the production build over migrated content and
inspect every affected public output, including the feed and all archive
paths. Only when both evidence sets pass should the compatibility reader be
removed and the approved build-time rejection or equivalent unsupported-input
behavior be enabled.

Ordered work:

1. Define the exact scan scope: source front matter, templates, scripts,
   tests/fixtures, documentation claims, and generated output.
2. Run a repository content/implementation scan and fail the gate if any
   supported source path still requires the scalar field.
3. Run `npm run build` from the migrated repository and assert the expected
   route set, author output, feed validity, and absence of legacy-dependent
   rendering symptoms.
4. Review the two evidence sets together; if either fails, retain
   compatibility and record the dependency instead of cutting over.
5. If both pass, remove the legacy normalization and implement the approved
   invalid-input behavior, then add a regression test proving accidental
   legacy metadata cannot silently pass.
6. Re-run the full test/build evidence after the cutover and update the
   maintained documentation to describe only the final supported contract.

### Implementation decisions and open questions

- Q3 controls whether invalid legacy input produces a clear build failure or
  another approved result. Do not silently discard the value.
- A source scan alone is insufficient: generated output must be inspected
  through the real Eleventy build before rejection is enabled.
- If the gate fails, the safe outcome is a documented transition state with
  compatibility retained; the task must not force a rejection merely to close
  the migration.

### Documentation

After successful cutover, update the maintained developer documentation to
remove transitional wording and state the final structured metadata and
legacy-input behavior. If the gate does not pass, document the remaining
compatibility state and the evidence gap instead.

### Task checklist

- [ ] Define and run the complete source/reference scan.
- [ ] Run and inspect a fresh production build.
- [ ] Record pass/fail evidence for every affected public route.
- [ ] Remove compatibility only after both evidence sets pass.
- [ ] Add and run the final legacy-input regression test.
- [ ] Update final documentation and parent requirement status.

### Requirement verification

- R5: The decisive check is a recorded pair: a repository-wide scan showing no
  remaining supported dependency on the legacy field, followed by a fresh
  `npm run build` whose post, home, blog, tag, and feed outputs contain the
  expected structured-author results. The legacy rejection change is applied
  only after both checks pass.
- Final invalid-input behavior: an integration test supplies legacy front
  matter through the normal content/build path and asserts the approved
  failure or handling behavior, rather than testing only a helper in
  isolation.

### Additional implementation verification

- Check the final route set against the pre-migration route inventory.
- Search generated output for stale legacy markers, missing names,
  `[object Object]`, malformed XML, and accidental empty author elements.
- Ensure documentation and test fixtures do not falsely claim that the legacy
  field remains supported after the gate closes.
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
            "where": "R1–R4 items",
            "quote": "R1. Posts use an approved structured metadata form that represents one or more authors without losing each author's display name.",
            "why": "Numbered, single-claim items of roughly equal length make the five requirements scannable and individually referenceable."
          },
          {
            "where": "R5 item",
            "quote": "Legacy `author` metadata is tolerated only during the migration window and is rejected or removed only after repository-content and production-generated-output evidence demonstrates that no supported path still depends on it.",
            "why": "The one load-bearing requirement compresses a time window, a two-source evidence condition, and the removal rule into a single sentence; it costs the reader more parsing than the rest of the checklist combined, though one careful read resolves it."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/000-main.md — Unresolved requirement questions": {
        "grade": "readable",
        "findings": [
          {
            "where": "Q1 item",
            "quote": "What is the canonical record shape? Recommended target: an `authors` sequence of objects with a required `name` field, leaving room for a stable identifier or profile URL later. Confirm whether names alone are sufficient or whether identity/link fields are required now.",
            "why": "One item bundles the question, a recommendation, and a re-ask of the same question; the reader must separate the recommendation from the actual open decision before acting on it."
          },
          {
            "where": "Q2 item",
            "quote": "Should archive, home, and tag list entries begin displaying all author names, or should they retain their current title-only presentation while becoming safe consumers of the new metadata?",
            "why": "A two-branch either/or plus a presentation-safety clause rides in one item; at this length it still lands in a single read."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/000-main.md — Research and supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "feed fact bullet",
            "quote": "`content/feed.xml.njk` reads `post.data.author` directly.",
            "why": "One fact per bullet with precise code-spanned file references makes the eight-item inventory skimmable and directly actionable."
          },
          {
            "where": "postslist fact bullet",
            "quote": "`_includes/postslist.njk` currently renders only title and URL, but it is shared by `content/index.njk`, `content/blog.njk`, and `content/tag-pages.njk`; those archive paths still need production-build coverage during the migration.",
            "why": "A single bullet carries a current-state fact, a three-way sharing relationship, and a forward-looking work obligation; the trailing obligation is easy to miss when scanning for facts."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/000-main.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "opening design paragraph",
            "quote": "Rendering consumes one normalized sequence, so the post page can render all names and the feed can emit the appropriate author elements without interpolating an object as a string.",
            "why": "The ~81-word design paragraph chains six distinct decisions (canonical shape, compat normalization, legacy write-stop, rendering, feed behavior, archive presentation); sentence boundaries keep it recoverable, but it is the densest prose in the file and rewards a second pass."
          },
          {
            "where": "ordered work, step 5",
            "quote": "If it passes, remove legacy production dependencies and add the approved regression check for rejected legacy input; otherwise keep compatibility and record the remaining dependency.",
            "why": "A plan step that also carries a full if/then/else policy; the conditional is load-bearing for the whole migration and sits inline in a list item rather than in the decisions block."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/000-main.md — Subtasks": {
        "grade": "readable",
        "findings": [
          {
            "where": "heading vs content",
            "quote": "## Subtasks … ### Requirement verification",
            "why": "The heading promises a child-task list (three path items) but the section's ~390 words are governance content — decisions, documentation rules, parent checklist, R1–R5 verification; the five labeled subsections keep it navigable despite the mismatch."
          },
          {
            "where": "Requirement verification, R2 bullet",
            "quote": "R2: A repository-wide content scan plus the production build verifies that every existing post has the new metadata, retains its author names, and preserves existing post/archive/tag URLs and body output.",
            "why": "The verification bullets are the densest items in the file — single sentences asserting three to four properties each; each needs deliberate unpacking rather than skimming."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/010-source-and-authoring.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "R-numbering",
            "quote": "R2. All existing post front matter is migrated without losing author values, post bodies, or route-defining metadata. … R4. `scripts/new-post.js` emits only the approved structured form for new posts.",
            "why": "The checklist jumps R2 → R4 because R3 belongs to the rendering child; without a scope note the skip can read as an omission until the reader cross-references the parent."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/010-source-and-authoring.md — Unresolved requirement questions": {
        "grade": "readable",
        "findings": [
          {
            "where": "Q1 item",
            "quote": "Q1. Confirm whether the canonical author records contain only a required `name` or also stable identity/profile fields; do not add fields during migration without approval.",
            "why": "A single open question stated together with its guardrail; the brevity loses nothing because the parent file holds the fuller context."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/010-source-and-authoring.md — Research and supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "last bullet",
            "quote": "The source migration must leave a compatibility read path available until `030-legacy-cutover.md` completes its evidence gate.",
            "why": "A forward-looking boundary rule is filed in a section of current-state facts; a reader triaging 'what is true now' versus 'what is required later' gets the two mixed."
          },
          {
            "where": "gap bullet",
            "quote": "No schema validator or migration utility currently exists.",
            "why": "One-line, one-fact statements with a clear consequence make the short inventory immediately usable."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/010-source-and-authoring.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "design paragraph",
            "quote": "During the transition, expose one normalization contract that turns a legacy scalar into a singleton sequence for consumers that still need to read unmigrated content.",
            "why": "The opening paragraph states the contract and the child's non-goals in four bounded sentences; no re-reading needed."
          },
          {
            "where": "five subsections after Ordered work",
            "quote": "### Implementation decisions and open questions … ### Additional implementation verification",
            "why": "The 408-word plan is partitioned into a design paragraph, a five-step list, and five short labeled blocks, so no part approaches wall density."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/020-public-rendering.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "second checkbox item",
            "quote": "The rendering transition continues to handle a legacy scalar as a singleton author only until the final cutover evidence is accepted.",
            "why": "An unnumbered constraint sits in the requirements checklist alongside R3; having no R ID, it is invisible to the R-numbered verification mapping later in the file."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/020-public-rendering.md — Unresolved requirement questions": {
        "grade": "readable",
        "findings": [
          {
            "where": "Q2 item",
            "quote": "Q2. Confirm whether archive, home, and tag list entries should display all author names or retain their current title-only presentation.",
            "why": "A one-line scoped restatement of the parent's Q2; brevity that loses nothing at this level of the hierarchy."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/020-public-rendering.md — Research and supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "postslist fact bullet",
            "quote": "It currently renders only title and link, so its collection iteration must be checked even if Q2 keeps the title-only presentation.",
            "why": "The bullet mixes a current-state fact with a conditional obligation in its trailing clause; still one read, but the actionable part trails the evidence."
          },
          {
            "where": "test-fact bullet",
            "quote": "Existing tests do not execute Eleventy or inspect generated files.",
            "why": "Short single-fact bullets with code-spanned referents keep the five-item inventory skimmable."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/020-public-rendering.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "design paragraph",
            "quote": "The shared list should be updated or verified as a structured-data consumer while retaining its current route and title behavior unless Q2 approves visible author names.",
            "why": "Q2-dependent behavior is distributed across two sentences of one paragraph (layout and shared list); the reader must track the same conditional in both places."
          },
          {
            "where": "transitional paragraph",
            "quote": "The compatibility normalization remains active here because old content may still exist during the transition.",
            "why": "The second paragraph cleanly isolates the transition boundary from the design paragraph, so the plan's two concerns stay separable at a glance."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/030-legacy-cutover.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "second checkbox item",
            "quote": "The final behavior for an accidental legacy post is explicit, tested, and consistent with the approved post-cutover policy.",
            "why": "A second unnumbered checklist commitment with no R ID; 'Requirement verification' maps only R5, so this commitment lacks a traceable handle."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/030-legacy-cutover.md — Unresolved requirement questions": {
        "grade": "readable",
        "findings": [
          {
            "where": "Q3 item",
            "quote": "Q3. Confirm whether accidental legacy input must fail the build with a clear validation error or use another explicit unsupported-input behavior.",
            "why": "A single crisp decision point with both options named; nothing to untangle."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/030-legacy-cutover.md — Research and supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "test-fact bullet",
            "quote": "The existing test files are comments only, so no current evidence can authorize a cutover.",
            "why": "Each of the three bullets pairs a fact with its direct consequence in one clause; dense but single-purpose and instantly usable as gate criteria."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/030-legacy-cutover.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "design paragraph, final sentence",
            "quote": "Only when both evidence sets pass should the compatibility reader be removed and the approved build-time rejection or equivalent unsupported-input behavior be enabled.",
            "why": "The file's densest single line: gate condition plus two sequenced actions in one sentence; a single careful read resolves it, but it is the closest any section comes to strain."
          },
          {
            "where": "Ordered work (six steps) plus five subsections",
            "quote": "4. Review the two evidence sets together; if either fails, retain compatibility and record the dependency instead of cutting over.",
            "why": "The 508-word plan stays navigable because the numbered steps carry one decision each and the failure path is stated explicitly inline."
          }
        ]
      }
    },
    "navigation": {
      "grade": "navigable",
      "findings": [
        {
          "where": "all four files, Execution plan headers",
          "quote": "Status: Draft",
          "why": "Plan status is declared in the same position in every file, so a reader can check state at a glance without hunting."
        },
        {
          "where": "000-main.md — Subtasks and each child's header",
          "quote": "Parent Task: `tasks/20260926-author-metadata-migration/000-main.md` … Depends On: `tasks/20260926-author-metadata-migration/010-source-and-authoring.md`",
          "why": "The parent lists children by exact path and every child echoes its parent and dependencies, so the decomposition graph is traceable from structure alone."
        },
        {
          "where": "cross-file references",
          "quote": "Resolve Q1–Q3 and record the approved schema, archive presentation, and post-cutover invalid-input behavior.",
          "why": "Stable R1–R5 and Q1–Q3 identifiers plus dedicated 'Requirements checklist' and 'Unresolved requirement questions' sections let a reader jump from any reference to the authoritative statement."
        },
        {
          "where": "000-main.md — Subtasks vs child files — Execution plan",
          "quote": "### Implementation decisions and open questions",
          "why": "The same governance blocks sit under '## Subtasks' in the parent but under '## Execution plan' in the children; a reader who learns the children's layout will not find the parent's decisions or R1–R5 verification in the analogous place."
        }
      ]
    },
    "mistakes": [
      {
        "where": "000-main.md — '## Subtasks' heading",
        "quote": "## Subtasks … ### Requirement verification",
        "why": "Heading does not match its content: the child-task list is three items, while ~90% of the section is parent-level governance (decisions, documentation rules, task checklist, R1–R5 verification, extra checks); a reader scanning headings for requirement verification or open decisions will not look under 'Subtasks'."
      },
      {
        "where": "010-source-and-authoring.md — Research and supporting facts, last bullet",
        "quote": "The source migration must leave a compatibility read path available until `030-legacy-cutover.md` completes its evidence gate.",
        "why": "A load-bearing boundary rule is buried in a current-state evidence section; readers auditing 'what is true now' versus 'what is required later' get the two kinds of statements mixed in one list."
      },
      {
        "where": "000-main.md and 020-public-rendering.md — Research and supporting facts, postslist bullets",
        "quote": "…those archive paths still need production-build coverage during the migration.",
        "why": "Research-fact bullets carry forward-looking work obligations in trailing clauses, so a reader scanning the facts sections for evidence also absorbs hidden work assignments."
      },
      {
        "where": "020-public-rendering.md and 030-legacy-cutover.md — Requirements checklist, second items",
        "quote": "The final behavior for an accidental legacy post is explicit, tested, and consistent with the approved post-cutover policy.",
        "why": "Constraint-style items without R numbers are styled as requirement checkboxes, breaking the R-number traceability that 'Requirement verification' sections and cross-file references depend on."
      },
      {
        "where": "000-main.md — Unresolved requirement questions, Q1",
        "quote": "What is the canonical record shape? Recommended target: an `authors` sequence of objects with a required `name` field, leaving room for a stable identifier or profile URL later. Confirm whether names alone are sufficient…",
        "why": "One list item mixes the question, a recommendation, and a re-ask of the same question; the actual decision point must be disentangled from the recommendation before it can be resolved or answered."
      },
      {
        "where": "000-main.md Execution plan, 010 Execution plan and facts, 010 decisions, 020 Execution plan",
        "quote": "read-only compatibility normalization … normalization contract … Compatibility reading is deliberately deferred … the compatibility reader",
        "why": "The same transitional mechanism is named at least five different ways across the file set; a reader must first infer these are one thing before they can follow the cutover rule that every file restates."
      }
    ],
    "summary": "The four files share one strict template — requirements checklist, unresolved questions, research facts, execution plan, then governance blocks — so every top-level section is short, single-purpose, and scannable; the longest prose unit is an ~81-word design paragraph and list items stay in the low tens of words. All 17 present sections grade readable: density is localized (multi-clause verification bullets, the 030 gate sentence, the 000 design paragraph) but always within single-read range given the sentence boundaries and labeled subsections. Navigation is navigable because plan status ('Status: Draft'), open questions (Q1–Q3), requirements (R1–R5), and the parent/child dependency graph each have fixed, findable homes with stable identifiers. The residual frictions are presentational: the parent files its governance content under a 'Subtasks' heading and under a different parent section than the children use, constraints and obligations are embedded in 'facts' bullets and unnumbered checklist items, one question item bundles ask plus recommendation, and the compatibility mechanism travels under five near-synonymous names."
  }
}
```
