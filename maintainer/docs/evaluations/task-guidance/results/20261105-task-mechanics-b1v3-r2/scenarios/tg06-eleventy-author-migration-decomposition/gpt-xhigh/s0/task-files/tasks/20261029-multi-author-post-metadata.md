# Migrate Post Author Metadata

Move post author metadata from the legacy scalar field to a structured form
that supports multiple authors, while preserving existing content and
generated output during the transition.

## Requirements checklist

- [ ] Represent each post's authors in a structured form that supports one or
  more authors.
- [ ] Migrate existing posts without losing or changing author names.
- [ ] Update the post layout, archive listings, feed, and post authoring helper
  to consume and produce the new form; show every post author in generated
  post and archive output and the feed.
- [ ] Keep mixed legacy and new-form content buildable during migration so
  existing content and generated pages continue to work.
- [ ] Do not reject the legacy form until source-content and generated-output
  evidence show that nothing still depends on it.

## Scope

One end-to-end task owns the schema transition, existing-content migration,
all affected consumers, and their production-path evidence. These changes
share one compatibility boundary and do not provide independently acceptable
sub-results that justify separate task files.

## Open questions and decisions

- **Design decision — front matter schema:** What exact collection and author
  object shape should posts use? Recommendation: `authors: [{ name: "..." }]`,
  with no additional fields unless required.
- **Design decision — feed representation:** How should multiple authors map
  to the existing feed's `<author>` element? Recommendation: emit one element
  per author while retaining the existing element and name representation
  for single-author posts.
- **Design decision — legacy policy:** Should the final state reject legacy
  `author` metadata after the required evidence, or retain compatibility?
  Recommendation: reject it only after both evidence checks pass; otherwise
  keep accepting it.

## Research and supporting facts

- `content/posts/first.md` and `content/posts/second.md` currently store one
  name each in the scalar `author` field.
- `_includes/layouts/post.njk` reads the scalar directly. The shared
  `_includes/postslist.njk` currently renders titles only and is used by the
  blog archive and tag pages.
- `content/feed.xml.njk` reads `post.data.author` directly into a singular
  `<author>` element.
- `scripts/new-post.js` emits scalar author front matter.
- `tests/author-output.test.js` currently contains only a comment; it does not
  assert generated output. `tests/archive-output.test.js` is present, but
  existing coverage does not establish multi-author behavior.
- `npm run build` invokes Eleventy and writes the production site to `_site`.
  The package test command is `npm test`.
- There is no `docs/index.md`; the maintained documentation entry point is
  `README.md`, and `docs/development/index.md` contains no authoring guidance.

## Execution plan

Status: Draft

### Design and compatibility

Treat author metadata as one canonical structured collection consumed by
templates, archives, and the feed. The authoring helper emits that canonical
form. During migration, accept legacy and canonical front matter through one
normalization boundary so individual templates do not duplicate compatibility
logic. Convert every existing post and verify its output before considering
legacy rejection. If rejection is approved, make it an explicit build-time
validation only after a complete content audit and production-output checks;
otherwise retain the compatibility path.

The archive currently omits author names, so include all authors in each
shared post-list entry; this covers the blog and tag archives. Preserve
single-author names and existing page/feed behavior while allowing the agreed
feed representation to encode every author. Exact front matter and feed
representations remain open decisions and must be resolved before
implementation.

### Ordered tasks

1. Resolve the author collection/object shape, feed representation, and
   whether legacy input will be rejected after evidence.
2. Add transitional normalization and update the authoring helper, post
   layout, archive listing, and feed to use the agreed structured model.
3. Migrate all current post front matter, preserving each existing name.
4. Add generated-output coverage using the real Eleventy production path for
   single- and multi-author post pages, blog and tag archives, and feed output.
   Also verify mixed legacy/new input while transitional compatibility is in
   place.
5. Audit all maintained post content and inspect asserted generated output.
   Only after both checks pass, enable legacy rejection if that policy was
   approved; otherwise keep the fallback.
6. Update the README with the supported authoring format and run the focused
   tests and production build.

### Implementation decisions and open questions

- The shared post-list template owns archive bylines because both the blog
  archive and tag pages use it.
- Transitional legacy handling belongs at one normalization boundary, not in
  each output template.
- Resolve the three design questions under “Open questions and decisions”
  before coding; changing the schema, feed contract, or legacy acceptance
  policy affects author-facing or generated-output behavior.

### Documentation

- Update `README.md` with the agreed front matter shape and authoring helper
  behavior. Do not document the target as currently supported until the
  implementation lands.

### Task checklist

- [ ] Agree the canonical author schema, feed representation, and legacy
  acceptance policy.
- [ ] Implement transitional normalization and update all author consumers.
- [ ] Migrate existing post metadata without changing names.
- [ ] Add real-build coverage for post pages, archives, feed, and mixed input.
- [ ] Audit source content and generated output before any legacy rejection.
- [ ] Document supported authoring and run tests plus the production build.

### Requirement verification

- Requirements 1–3: Run generated-output tests through Eleventy and inspect
  the built post pages, blog archive, tag pages, and feed; assert that every
  agreed author name appears in the expected output. Separately test that the
  authoring helper emits the agreed front matter.
- Requirement 4: Build representative legacy and new-form posts together
  through the production Eleventy path and assert both render correctly.
- Requirement 5: Before rejection, audit every maintained post source for the
  legacy key and run production-output assertions over migrated content. Do
  not enable rejection if either evidence check is incomplete.
