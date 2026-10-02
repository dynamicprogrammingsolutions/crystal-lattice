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