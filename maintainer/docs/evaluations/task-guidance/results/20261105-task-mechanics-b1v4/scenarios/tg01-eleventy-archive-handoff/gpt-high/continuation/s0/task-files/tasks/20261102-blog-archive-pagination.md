# Paginate the Blog Archive

Plan the blog archive pagination change while preserving the site's existing
static output and adjacent publishing behavior.

## Requirements checklist

- [ ] Keep `/blog/` as the first archive page.
- [ ] Generate stable later archive pages with no more than twenty posts each.
- [ ] Provide accessible previous/next navigation between archive pages.
- [ ] Preserve the home page, tag pages, feed, sitemap, and individual-post links.
- [ ] Preserve archive post ordering and static output with no client-side JavaScript.

## Questions and decisions

- What URL pattern should later archive pages use? Recommendation: numbered
  directories such as `/blog/2/`, `/blog/3/`, keeping `/blog/` unchanged.
  Confirm this user-visible URL contract before implementation.

## Supporting details

- The archive is currently a single template at `content/blog.njk`, rendered
  at `/blog/`, and displays `collections.posts`.
- `_includes/postslist.njk` reverses the supplied list and renders links to
  individual posts. The archive's current visible order therefore comes from
  that shared include.
- `content/index.njk` and `content/tag-pages.njk` also use the shared posts
  list include; `content/feed.xml.njk` separately reverses `collections.posts`.
- The sitemap iterates `collections.all`, so generated archive pages may
  become sitemap entries through the existing production path.
- The repository currently has two posts. `tests/archive-output.test.js` is
  only a placeholder and does not exercise a production build.

## Implementation plan

Status: Draft

Use Eleventy's build-time pagination for the archive, maintaining `/blog/` for
page one and using a stable, explicitly confirmed permalink pattern for later
pages. Render each archive's existing post links through the shared list
include so the visible order remains the same. Add ordinary HTML previous and
next links with clear accessible names and boundary-aware links; no browser
JavaScript is needed. Keep all other templates and collections behavior
unchanged unless the production-path check exposes a pagination interaction
that must be addressed to satisfy the preservation requirements.

The decisive evidence should cross the real Eleventy build boundary with more
than twenty posts: assert archive page count and URLs, a maximum of twenty
posts per page, continuous non-duplicated coverage in the existing order,
and correct previous/next links including first and last page boundaries.
Also assert that the home page, tags, feed, sitemap, and individual-post links
remain available and that generated archive pages contain no script-based
pagination. The current two-post repository cannot demonstrate later pages
without representative additional build input; the test should provide that
input without bypassing the production templates or build.

The main risk is changing archive URL contracts or accidentally altering
shared list behavior used by the home and tag pages. Limit changes to archive
pagination and archive navigation; if generated URLs or preserved outputs
diverge, revert the pagination/template changes and retain the current single
archive until the cause is understood.

### Implementation decisions and open questions

- The later-page permalink pattern is unresolved because it is user-visible.
  Confirm the numbered-directory recommendation before implementation.
- Use static Eleventy output and existing post link rendering; do not add
  client-side pagination or change collection order.

### Documentation

- Update `README.md` only if needed to describe the now-supported paginated
  archive; keep the statement aligned with verified production behavior.

### Task checklist

- [ ] Confirm the later-page URL pattern.
- [ ] Implement archive pagination and accessible navigation.
- [ ] Add production-build regression coverage using more than twenty posts.
- [ ] Update maintained documentation to match verified behavior.

### Requirement verification

- Archive pagination and navigation: production-build test with enough posts
  to create multiple pages; verify `/blog/`, later stable URLs, page size,
  ordering, complete coverage, and previous/next links at interior and edge
  pages. This does not assess visual styling or assistive-technology behavior
  beyond the rendered semantic links and accessible names.
- Preserved outputs and static behavior: in the same production build, verify
  the home page, tag pages, feed, sitemap, individual-post links, and absence
  of pagination scripts in archive HTML. This does not claim unrelated
  template content is unchanged byte-for-byte.

### Additional implementation verification

- Run the repository test suite and production build after the focused
  regression test passes.