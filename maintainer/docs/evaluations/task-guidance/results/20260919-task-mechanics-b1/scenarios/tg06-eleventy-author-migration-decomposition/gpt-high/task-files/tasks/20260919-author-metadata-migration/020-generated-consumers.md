# Move generated pages and feed consumers to structured authors

Update production templates and generated-output coverage so post pages,
shared archive paths, and the XML feed consume the canonical author
representation without breaking existing routes or valid output.

Parent Task: tasks/20260919-author-metadata-migration/000-main.md
Depends On: tasks/20260919-author-metadata-migration/010-schema-and-content-migration.md

## Requirements checklist

- [ ] The post layout renders the canonical author data for one and multiple
      authors.
- [ ] Home, blog, and tag archive paths remain on the canonical data path and
      preserve their existing title, URL, ordering, and markup behavior.
- [ ] The feed emits valid, deterministic author output for the approved
      multi-author contract and preserves the current single-author case.
- [ ] Generated-output tests inspect artifacts from a real Eleventy build,
      rather than supplying mocked post data directly to templates.
- [ ] No production consumer depends on the legacy scalar field after the
      compatibility boundary is in place.

## Requirement questions and decisions

- Confirm the public representation of multiple authors in the XML feed
  (recommended default: one `<author>` element per ordered author, if valid
  for the intended feed contract).
- Confirm whether archive lists should display author names during this
  migration or only stop depending on the old field. The current archive list
  displays title and URL only, so adding visible bylines would be a separate
  user-facing change unless approved.

## Supporting facts

- `_includes/layouts/post.njk` currently prints `{{ author }}`.
- `_includes/postslist.njk` is shared by `content/index.njk`,
  `content/blog.njk`, and `content/tag-pages.njk`; it currently prints only
  post links.
- `content/feed.xml.njk` directly prints `post.data.author`.
- `tests/author-output.test.js` and `tests/archive-output.test.js` are not
  currently decisive and need real build assertions.

## Execution plan

Status: Draft

Adapt the post layout and feed to iterate over the normalized author
collection. Keep the shared archive list's current visible contract unless the
requester approves adding bylines, but make its generated-path coverage prove
that the migration does not bypass or break archive rendering. Extend the
generated-output tests to build the site and inspect post, home, blog, tag,
and feed files for both single- and multi-author cases.

### Implementation decisions and open questions

- Consumer templates should use normalized data, not independently support
  both legacy and canonical field names.
- Preserve existing archive URLs and order; author display in archives is not
  implied by the migration request because the current list has no byline.
- Treat XML validity and deterministic author ordering as release-blocking
  checks.

### Documentation

- Document the resulting feed/author rendering contract only after the public
  shape is approved and the generated-output assertions pass.
- Keep the archive behavior statement aligned with whether bylines were
  explicitly approved.

### Task checklist

- [ ] Update the post layout to consume normalized structured authors.
- [ ] Update the feed template to the approved multi-author contract.
- [ ] Verify shared archive consumers through home, blog, and tag builds.
- [ ] Replace comment-only output tests with production-build assertions.
- [ ] Confirm no direct legacy reads remain in production templates.

### Requirement verification

- Run `npm run build` with migrated single- and multi-author posts.
- Assert the post HTML contains the expected ordered author output and keeps
  existing post URLs.
- Assert `/index.html`, `/blog/index.html`, and the generated tag page retain
  expected links, order, and valid markup.
- Assert `/feed/feed.xml` contains the approved author elements in source
  order and remains valid XML for both author cardinalities.

### Additional implementation verification

- Check generated output for empty or duplicated author elements.
- Check that the shared archive include is exercised by all three callers,
  not only by the blog page.
- Compare the set of generated routes before and after the migration.
