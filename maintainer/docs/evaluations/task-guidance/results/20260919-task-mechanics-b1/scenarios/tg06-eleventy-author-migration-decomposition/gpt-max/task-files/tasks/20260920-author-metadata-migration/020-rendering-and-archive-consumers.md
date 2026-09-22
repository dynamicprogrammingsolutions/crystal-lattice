# Move rendering and archive consumers to canonical authors

Update post templates, shared collection rendering, archive pages, feeds, and
related generated-output consumers so they read the canonical author
collection while preserving current routes and single-author behavior.

Parent Task: tasks/20260920-author-metadata-migration/000-main.md

Depends On: tasks/20260920-author-metadata-migration/010-author-contract-and-authoring.md

## Requirements checklist

- [ ] Render every canonical post author in the post layout in source order,
  preserving the current one-author display.
- [ ] Audit and update `_includes/postslist.njk`, the home page, blog archive,
  and tag archive templates so no author behavior depends on `author`.
- [ ] Update the feed to represent every canonical author deterministically
  and with correct XML escaping, without changing its public location.
- [ ] Verify other generated metadata consumers, including the sitemap, do
  not accidentally depend on the legacy field.
- [ ] Add production-build assertions for post pages, archive routes, feed
  author entries, and sitemap URLs.

## Research and supporting facts

- `_includes/layouts/post.njk` currently prints the scalar `author`.
- `content/index.njk`, `content/blog.njk`, and `content/tag-pages.njk` all
  include `_includes/postslist.njk`; the shared include currently prints only
  title/link values.
- `content/feed.xml.njk` directly reads `post.data.author` and has one
  `<author>` element per post.
- `content/sitemap.xml.njk` only reads `page.url`, so it should remain
  author-independent while still being covered by a route regression check.
- The current tests do not build or inspect any generated page.

## Execution plan

Status: Draft

Use the normalized canonical collection supplied by subtask 010 as the only
template input. Update the post layout to render the complete collection and
update the feed to iterate it, retaining the current single-author result and
using the approved deterministic multi-author representation. Inspect the
shared post-list and all three archive entry points: if they expose no author
metadata, preserve that public shape while proving they do not dereference
the legacy field; if author metadata is rendered as part of the approved
contract, make the include iterate canonical authors. Keep archive URLs,
tagging, ordering, and feed/sitemap locations unchanged. Build the real site
and assert output at the generated-file boundary.

### Implementation decisions and open questions

- Confirm the post-page separator for multiple display names; recommendation:
  comma plus space in source order, with no change for one name.
- Confirm the feed representation; recommendation: emit one existing-style
  author element per canonical author in source order rather than inventing a
  new feed location or author index.
- XML escaping must be handled by the template/data path for names containing
  markup-sensitive characters.
- Do not add author pages, sorting, or archive pagination as incidental scope.

### Documentation

- Document any user-visible multi-author display or feed representation in
  the same maintained authoring section updated by subtask 010.
- Record no archive-pagination claim; the existing development note is
  unrelated to this migration.

### Task checklist

- [ ] Confirm display and feed representation.
- [ ] Replace direct legacy reads in the post layout and feed.
- [ ] Audit/update the shared post list and home/blog/tag archive templates.
- [ ] Inspect sitemap and other collection consumers for stale legacy access.
- [ ] Add generated-output assertions covering one and multiple authors and
  unchanged archive/feed/sitemap routes.

### Requirement verification

- Post rendering is proven by a production build whose post HTML contains all
  canonical names in order and contains no missing/duplicated author.
- Archive compatibility is proven by successful generated home, `/blog/`, and
  tag-page files with the expected links and collection membership.
- Feed migration is proven by parsing or exact structural assertions against
  the generated feed, including every author and XML-safe names.
- Sitemap preservation is proven by checking the generated URL set before the
  final legacy rejection, with no author lookup involved.
- A scoped source scan confirms these templates contain no direct
  `author`/`post.data.author` dependency outside the explicitly transitional
  boundary.