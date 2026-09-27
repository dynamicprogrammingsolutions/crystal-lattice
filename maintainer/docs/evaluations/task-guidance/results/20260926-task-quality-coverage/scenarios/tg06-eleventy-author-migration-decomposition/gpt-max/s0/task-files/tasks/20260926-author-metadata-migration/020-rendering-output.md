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