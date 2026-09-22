# Migrate post author metadata to a structured multi-author form

Plan the staged migration from the post front matter `author` string to a
structured multi-author contract across source content, authoring tools,
templates, archives, feeds, and the legacy-field cutover.

## Requirements checklist

- [ ] Define and adopt one canonical structured multi-author representation for
  post metadata.
- [ ] Keep existing legacy-author content buildable and renderable during the
  migration transition, without breaking existing generated pages or feeds.
- [ ] Move post templates, archive/list paths, and feed generation to consume
  the canonical author representation.
- [ ] Update the post authoring helper to emit the canonical representation and
  support the approved multi-author input.
- [ ] Migrate every existing post safely, preserving its current author data and
  preventing dropped, duplicated, or reordered authors.
- [ ] Reject the legacy single-name form only after content inventory and
  generated-output evidence show that no supported source or output path still
  depends on it.
- [ ] Record the current authoring contract and the completed cutover in the
  maintained documentation, without documenting target behavior as current
  before implementation is complete.

## Unresolved requirement questions and decisions

- **Requirement question — canonical schema:** What is the exact field name and
  element shape? For example, should the field be an array of display-name
  strings or an array of author objects with stable identifiers and names?
  This changes front matter, the authoring helper API, and every renderer.
- **Requirement question — rendered form:** How should one and multiple authors
  appear on post pages, archive/list views, and the feed? The migration should
  preserve the current one-name presentation where applicable, but the
  separator, ordering, and feed serialization for multiple authors need
  approval.
- **Requirement question — compatibility boundary:** During transition, should
  legacy `author` be normalized in Eleventy data, accepted only by the
  authoring tool, or accepted by both? The final rejection point and its error
  message should be explicit before implementation.
- **Decision:** Use separate source migration, output migration, and
  evidence-gated rejection boundaries. No rejection should be enabled merely
  because the new field exists.
- **Decision:** Do not add author identity pages, profile URLs, or a new
  persistent author registry unless the schema decision explicitly requires
  them.

## Scope and workstreams

The work is decomposed into three dependent subtasks:

1. Establish the source contract, authoring-tool behavior, and migrated post
   content.
2. Convert every production output surface that consumes or exposes author
   metadata.
3. Prove that the legacy form is unused, then enable its rejection and record
   the final supported contract.

This planning task does not modify application code, content, generated
output, tests, or maintained documentation.

## Research and supporting facts

- The two existing post sources,
  `content/posts/first.md` and `content/posts/second.md`, use quoted scalar
  `author` values.
- `scripts/new-post.js` emits the legacy `author` front matter and accepts one
  author argument.
- `_includes/layouts/post.njk` renders `author` directly.
- `content/feed.xml.njk` reads `post.data.author` directly.
- The home page, blog archive, and tag pages all use
  `_includes/postslist.njk`; that shared list currently renders only title and
  URL, so its author behavior must be reviewed as the archive integration
  point even though it has no direct legacy-field reference today.
- `content/posts/posts.json` supplies the shared post layout and `posts` tag;
  there is no separate author data collection or author registry.
- `tests/author-output.test.js` and `tests/archive-output.test.js` contain
  comments describing intended coverage but no assertions, so they are not
  evidence for the migration or the cutover gate.
- The repository has no authoring or front matter guide beyond the general
  `README.md`; documentation should remain small and owned by the site
  package.

## Subtasks

- [ ] [tasks/20260920-author-metadata-migration/010-source-contract-and-content-migration.md](tasks/20260920-author-metadata-migration/010-source-contract-and-content-migration.md)
- [ ] [tasks/20260920-author-metadata-migration/020-rendering-and-output-surfaces.md](tasks/20260920-author-metadata-migration/020-rendering-and-output-surfaces.md)
- [ ] [tasks/20260920-author-metadata-migration/030-cutover-evidence-and-legacy-rejection.md](tasks/20260920-author-metadata-migration/030-cutover-evidence-and-legacy-rejection.md)

## Execution plan

Status: Draft

Execute the subtasks in numeric order after the unresolved schema,
presentation, and compatibility questions are approved. Keep the old input
readable until the final evidence gate; the new field must be exercised through
the actual Eleventy build rather than through isolated template mocks.

The first workstream establishes the canonical source representation,
normalizes legacy input for the transition if that is the approved boundary,
updates `scripts/new-post.js`, and migrates every existing post. The second
workstream updates the post layout, shared archive/list path, and feed to use
the canonical data while preserving the established output for the existing
single-author posts. It also adds coverage for multiple authors and for all
archive entry points. The last workstream inventories source references,
builds the site, inspects generated post/archive/feed output, and only then
enables a clear failure for remaining legacy input.

### Implementation decisions and open questions

- The staged compatibility decision is approved for planning: migration and
  rendering must be independently verifiable before legacy rejection.
- The exact field/schema, multi-author display/serialization, and enforcement
  boundary remain open requirement questions. Resolve them before changing the
  requirements checklist or marking execution approved.
- The final rejection must be exercised through the real authoring/build path;
  a test that bypasses front matter parsing or supplies already-normalized
  data is not decisive.

### Documentation

Update `README.md` or the smallest more appropriate package-owned guide with
the canonical front matter example, authoring-tool input, transition status,
and final rejection behavior. Do not describe legacy rejection as current
until the evidence gate passes. No new documentation directory or placeholder
page is needed.

### Task checklist

- [ ] Resolve the canonical schema, presentation, and compatibility-boundary
  questions.
- [ ] Approve this plan and mark it `Approved` before execution.
- [ ] Complete
  `010-source-contract-and-content-migration.md`.
- [ ] Complete `020-rendering-and-output-surfaces.md` against the production
  build.
- [ ] Complete `030-cutover-evidence-and-legacy-rejection.md`.
- [ ] Update maintained authoring documentation after the supported behavior is
  true.
- [ ] Record implementation and completion notes with evidence in this task
  file and its subtasks.

### Requirement verification

- **Canonical representation and authoring tool:** Verify the approved field
  shape in every migrated post, invoke the real `scripts/new-post.js` export
  with one and multiple authors, and parse the resulting front matter through
  the normal Eleventy input path.
- **Transition compatibility:** Build with a representative legacy fixture
  before the final cutover and assert that the post page and feed still
  contain the same author information and valid output.
- **Output migration:** Run the production build and inspect a post page, home
  page, blog archive, tag archive, and feed. Assert that each author-bearing
  surface is derived from canonical data and that multiple authors are
  complete, ordered, and serialized according to the approved contract.
- **Existing-content migration:** Inventory all post front matter, compare the
  pre-migration author values with the canonical values, and build the full
  site to catch malformed metadata.
- **Legacy rejection gate:** Require both a repository/content scan with no
  supported legacy inputs and generated-output checks showing no legacy data
  path remains before asserting that legacy input fails. Keep a focused
  negative test for the final rejection.
- **Documentation:** Review the maintained guide against the behavior proven
  by the final build and tests.