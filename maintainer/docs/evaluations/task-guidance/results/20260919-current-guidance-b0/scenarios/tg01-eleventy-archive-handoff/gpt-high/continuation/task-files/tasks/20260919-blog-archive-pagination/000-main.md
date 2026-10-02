# Blog archive pagination

Plan the migration of the Eleventy blog archive from one unbounded page to a
stable, paginated archive while preserving the existing public output and
static-site behavior.

## Requirements checklist

- [ ] Keep `/blog/` as the first archive page and preserve the archive's
  existing post order.
- [ ] Generate stable later archive pages with no more than twenty posts per
  page.
- [ ] Add accessible previous/next navigation that exposes only the links
  valid for the current page.
- [ ] Preserve the home page, tag pages, feed, sitemap, individual-post
  routes/navigation, and post order.
- [ ] Keep the generated site usable without client-side JavaScript.

## Scope

This handoff covers archive pagination generation, archive-page navigation,
production-build regression coverage, and the small amount of developer
documentation needed to describe the supported archive URL behavior. It does
not change post content, collection semantics, the home-page post count, tag
page pagination, feed format, sitemap format, or individual-post templates
except where verification demonstrates an accidental regression.

## Subtasks

- [ ] tasks/20260919-blog-archive-pagination/010-archive-pagination-generation.md
- [ ] tasks/20260919-blog-archive-pagination/020-accessible-archive-navigation.md
- [ ] tasks/20260919-blog-archive-pagination/030-regression-coverage.md
- [ ] tasks/20260919-blog-archive-pagination/040-pagination-documentation.md

## Requirement questions and decisions

- Requirement question: what public URL pattern should later archive pages
  use? Recommendation: `/blog/page/2/`, `/blog/page/3/`, and so on, with
  `/blog/` reserved for page one. This is a user-visible URL contract and
  should be confirmed before execution.
- Preserved-contract decision: derive archive pages from the existing posts
  collection and retain the ordering currently produced by
  `_includes/postslist.njk`; pagination must not sort or reverse the
  collection a second time.
- Preserved-contract decision: use server-rendered semantic links for
  previous/next controls so navigation remains available in the static HTML
  and does not require JavaScript.

## Research and supporting facts

- `content/blog.njk` currently emits one page at `/blog/` and passes
  `collections.posts` to `_includes/postslist.njk`.
- `_includes/postslist.njk` renders an ordered list and reverses the supplied
  collection for display. The home page and tag pages reuse this include,
  while the feed reverses the collection independently.
- `content/tag-pages.njk` already uses Eleventy pagination to create one page
  per tag; its pagination behavior is separate from the archive change.
- `content/sitemap.xml.njk` iterates `collections.all`, so new archive output
  must be checked for expected sitemap inclusion without removing existing
  URLs.
- `tests/archive-output.test.js` currently contains only a comment saying that
  `/blog/index.html` should exist; it does not provide regression evidence.
- `docs/development/index.md` currently states that no archive pagination
  specification exists.
- The inspected post layout preserves title, author, and content but contains
  no explicit individual-post navigation control. Execution should verify the
  generated post routes and any existing post-navigation output before and
  after the change rather than inventing a new control.
- The fixture currently contains two dated posts, so the pagination test must
  exercise a production build with more than twenty posts in order to prove
  the page-size and later-page requirements.

## Execution plan

Status: Draft

Implement and verify the change in these boundaries:

1. Add Eleventy pagination to the archive source using the approved stable
   URL pattern. Keep page one at `/blog/`, use the same collection order as
   the current archive, and ensure every generated page receives only its
   page slice.
2. Add a shared or archive-specific semantic `<nav>` with an accessible
   label and clear previous/next link names. Render previous and next links
   conditionally at the page boundaries, using ordinary HTML links and no
   client-side behavior.
3. Replace the placeholder archive test with a production-build integration
   test. Exercise more than twenty posts and assert page sizes, deterministic
   URLs, page ordering, navigation boundaries, and absence of JavaScript
   dependency. Assert that the home page, tags, feed, sitemap, and individual
   post outputs retain their existing routes and ordering/contracts.
4. Update the owning development documentation after the URL convention is
   approved, describing `/blog/` and later archive pages as current supported
   behavior. Keep the README's static-site claim accurate; do not document
   the target behavior as current before implementation.

### Implementation decisions and open questions

- Confirm the later-page permalink pattern before changing the public archive
  contract. The recommended pattern is `/blog/page/<page-number>/`.
- Decide during implementation whether the navigation markup belongs in the
  archive template or a narrowly scoped include; whichever location is
  chosen must not add navigation to the home, tag, feed, or post outputs.
- Use the production Eleventy build as the decisive test boundary. A
  test-time fixture with more than twenty real post documents is acceptable
  only if it invokes the normal build path and does not bypass collection or
  permalink behavior.

### Documentation

- Update `docs/development/index.md` from its current “no archive pagination
  specification exists” statement to the supported archive behavior after
  implementation and verification.
- Keep documentation scoped to the developer audience and the actual
  generated URL contract. Do not create a new documentation directory or
  placeholder specification.
- If the implementation changes any maintained public guidance in `README.md`,
  update it in the same reviewed change; otherwise leave the concise README
  unchanged.

### Task checklist

- [ ] Complete the archive pagination generation subtask.
- [ ] Complete the accessible archive navigation subtask.
- [ ] Complete the production-build regression coverage subtask.
- [ ] Complete the pagination documentation subtask.
- [ ] Resolve the later-page URL requirement question before execution.
- [ ] Run the production build and the focused archive test, recording any
  blocked verification.

### Requirement verification

- Archive first page and page-size limit: production-build assertions inspect
  `/blog/` and every generated later-page HTML file with more than twenty
  posts, checking that each page has at most twenty entries and that page one
  retains its existing route and order.
- Stable later pages: the same build asserts deterministic page URLs and
  expected links for at least pages two and three when enough fixture posts
  exist.
- Accessible previous/next navigation: HTML assertions inspect semantic
  navigation, accessible labeling, link text/targets, and the absence of a
  previous link on page one or a next link on the final page.
- Preserved site outputs: production-build assertions compare or structurally
  verify home, tag, feed, sitemap, and individual-post routes and ordering;
  the test must not replace those consumers with mocks.
- Static zero-JavaScript output: generated archive and navigation pages are
  inspected for ordinary links and no client-side script requirement; the
  build remains a static Eleventy output.

### Additional implementation verification

- Check that adding archive pages does not accidentally alter
  `collections.posts` ordering for the home page, tag pages, or feed.
- Check that `collections.all` still contains the existing URLs and that the
  sitemap behavior remains valid after pagination pages are introduced.