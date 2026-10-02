# Paginate the blog archive

Plan the Eleventy archive change so that a growing blog remains browseable
while its existing public pages and static-output guarantees remain intact.

## Requirements checklist

- [ ] Keep `/blog/` as the first archive page.
- [ ] Generate deterministic, stable URLs for every later archive page, with
  no more than twenty posts on any page.
- [ ] Add accessible HTML previous/next navigation between adjacent archive
  pages, omitting a control when no page exists in that direction.
- [ ] Preserve the home page, tag pages, feed, sitemap, individual-post
  navigation, and the existing post order.
- [ ] Preserve a zero-JavaScript static output for the archive and the rest of
  the site.

## Unresolved requirement questions and decisions

- Requirement question: what URL pattern should later archive pages use?
  Recommendation: keep `/blog/` for page one and use
  `/blog/page/2/`, `/blog/page/3/`, and so on. This makes the page-number
  namespace explicit and leaves `/blog/` as a permanent canonical entry point.
  Execution should not begin until this public URL choice is confirmed.
- Decision: use one task rather than a parent task with subtasks. Pagination,
  navigation, regression coverage, and the small documentation update form
  one end-to-end archive capability with one production-build acceptance
  boundary.

## Research and supporting facts

- `content/blog.njk` currently owns `/blog/` and renders
  `collections.posts` through `_includes/postslist.njk`.
- `_includes/postslist.njk` reverses the supplied collection for display.
  The archive currently displays newer posts first, while the same include is
  also used by the home page, tag pages, and individual-post layout.
- `content/index.njk`, `content/tag-pages.njk`, `content/feed.xml.njk`, and
  `content/sitemap.xml.njk` all depend on the existing `collections.posts` or
  `collections.all` behavior. The archive implementation must not globally
  reorder or paginate those collections.
- `content/posts/posts.json` applies the post layout and `posts` tag to the
  Markdown posts. The fixture currently has only two posts, so pagination
  behavior cannot be proven without adding deterministic fixture posts or an
  equivalent repository-owned build fixture with more than twenty posts.
- `tests/archive-output.test.js` contains only a comment stating that
  `/blog/index.html` is checked; it currently provides no executable
  production-build coverage.
- The project has no archive pagination specification. `docs/development/index.md`
  currently records that absence, while `README.md` gives a short description
  of the generated site.
- The build is Eleventy 3 and the repository has no client-side JavaScript
  source. Verification should inspect generated HTML and URLs, not rely on
  browser-side behavior.

## Execution plan

Status: Draft

The archive will get its own canonical newest-first post sequence before
Eleventy pagination splits it into pages of twenty. This keeps page boundaries
correct while preserving the original `collections.posts` sequence for the
home page, tags, feed, sitemap, and post layout. The existing shared list
include should continue to receive data in the shape/order it expects, or an
archive-only rendering boundary should be introduced if that is clearer; the
implementation must not silently change the other include consumers.

The first pagination item will retain the explicit `/blog/` permalink. Later
items will use the approved stable numbered URL pattern and will link to one
another through Eleventy pagination metadata. The archive template will emit
semantic HTML navigation with a useful navigation label, text links that
identify the direction and destination, and `rel="prev"`/`rel="next"` where
applicable. First, middle, and last pages will each omit unavailable controls
instead of rendering dead or JavaScript-dependent links.

Implementation and verification will proceed in this order:

1. Confirm the later-page URL pattern, change this plan to `Approved`, and
   record the decision in the task notes before implementation.
2. Add the archive-specific ordered data and Eleventy pagination configuration,
   preserving the existing `/blog/` route and limiting each page to twenty
   posts.
3. Render the archive page list and previous/next navigation as ordinary
   server-generated HTML. Keep all navigation and page content functional with
   JavaScript disabled.
4. Expand the repository-owned fixture deterministically past the twenty-post
   boundary so the actual Eleventy build produces at least a first and later
   archive page without test-only shortcuts that bypass the production
   templates.
5. Replace the comment-only archive test with production-build assertions for
   page URLs, page sizes, ordering, no gaps or duplicates, navigation edge
   behavior, and absence of JavaScript.
6. In the same build verification, assert that the home page, tag pages, feed,
   sitemap, and individual-post navigation remain generated and retain their
   existing order/links. Confirm that the sitemap includes the generated
   archive pages without removing its existing URLs.
7. Update the maintained README summary and the development documentation
   index with the now-supported archive URL and twenty-post pagination
   contract. Do not document the target behavior as current until the build
   checks pass.

### Implementation decisions and open questions

- The exact later-page URL pattern is still a requirement question; the
  recommendation is `/blog/page/<number>/`.
- The archive-specific ordering boundary is a local implementation decision;
  preserving the shared collection and include consumers is the compatibility
  constraint.
- The test fixture must cross the twenty-post boundary through the real
  Eleventy input/build path. The implementation may choose the smallest
  repository-owned fixture expansion that keeps the sample site coherent.
- No pagination is planned for tag pages, the feed, the sitemap, the home
  page, or individual-post navigation.

### Documentation

- Update `README.md` so its supported-site summary identifies the blog archive
  as paginated and static.
- Replace the absence note in `docs/development/index.md` with the concise
  archive contract: the first-page URL, approved later-page URL pattern,
  twenty-post maximum, and server-rendered previous/next navigation.
- Keep documentation changes in the implementation change and only claim
  behavior verified by the production build.

### Task checklist

- [ ] Resolve and record the later-page URL pattern.
- [ ] Mark the plan `Approved` before execution.
- [ ] Add archive-specific ordered pagination with a twenty-post page size.
- [ ] Preserve `/blog/` as page one and generate stable later URLs.
- [ ] Add accessible server-rendered previous/next navigation.
- [ ] Add enough repository-owned posts to exercise multiple pages.
- [ ] Replace the placeholder archive test with production-build coverage.
- [ ] Add regression assertions for home, tags, feed, sitemap, post
  navigation, ordering, and zero-JavaScript output.
- [ ] Update the README and development documentation.
- [ ] Run the build and test suite and record the evidence below.

### Requirement verification

- `/blog/` remains the first archive page: inspect the production build and
  assert `/blog/index.html` exists, contains the newest page of posts, and is
  the target of the first page's relevant navigation.
- Later pages are stable and contain at most twenty posts: build the
  repository-owned fixture through more than twenty posts, assert the exact
  numbered paths, count rendered post links per page, and assert that the
  concatenated pages contain each post once in the established order.
- Previous/next navigation is accessible: assert the generated archive HTML
  contains a labeled semantic navigation element, directionally named links,
  and only the valid adjacent links on first, middle, and last pages.
- Existing site surfaces are preserved: assert the production build still
  emits the home page, tag output, feed, sitemap, and individual-post pages,
  with their expected post links/order and archive URLs represented in the
  sitemap.
- Static zero-JavaScript output is preserved: inspect the generated archive
  and preserved site pages for the absence of script-based pagination or
  required JavaScript assets, and ensure all archive navigation is expressed
  as ordinary links.

### Additional implementation verification

- Run `npm test` after the focused production-build assertions are added.
- Run `npm run build` independently and inspect the generated output tree so
  the test harness is not the only consumer of the build boundary.
- Check that generated paths do not collide with existing tag, feed, sitemap,
  or individual-post paths.