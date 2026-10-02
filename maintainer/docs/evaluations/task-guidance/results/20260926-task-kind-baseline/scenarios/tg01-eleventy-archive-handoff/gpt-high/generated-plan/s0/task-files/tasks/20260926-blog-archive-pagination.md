# Paginate the blog archive

Add static pagination to the Eleventy blog archive so the existing `/blog/`
route remains the first page, later archive pages have stable numbered URLs,
each page contains no more than twenty posts, and visitors can move between
adjacent pages with accessible previous/next links. Existing site surfaces and
post ordering must remain unchanged.

## Requirements checklist

- [ ] Keep `/blog/` as the first archive page.
- [ ] Generate stable, deterministic later archive page URLs.
- [ ] Render no more than twenty posts on any archive page.
- [ ] Preserve the archive's current post order across page boundaries; posts
      must not be duplicated, omitted, or reordered as a result of pagination.
- [ ] Add accessible previous/next navigation to the archive pages, exposing
      only links for pages that exist and retaining correct adjacent-page
      relationships.
- [ ] Preserve the home page and tag-page output and their existing post order.
- [ ] Preserve the feed, sitemap, and individual-post URLs and navigation.
- [ ] Keep the generated site static and zero-JavaScript.

## Open requirement questions

- [ ] What canonical URL pattern should later archive pages use: for example,
      `/blog/page/2/` or `/blog/2/`? The implementation should not begin until
      this user-visible contract is confirmed. Recommendation: use
      `/blog/page/2/`, `/blog/page/3/`, and so on, because it makes the page
      namespace explicit while leaving `/blog/` as the stable first-page URL.

## Research and supporting facts

- `content/blog.njk` currently owns `/blog/` and passes all
  `collections.posts` entries to `_includes/postslist.njk`.
- `_includes/postslist.njk` reverses its input. The same partial is used by
  `content/index.njk` and `content/tag-pages.njk`, so changing its default
  ordering can silently alter the home page and tag pages.
- `content/feed.xml.njk` and `content/sitemap.xml.njk` consume the global
  collections independently of the archive template.
- Individual posts use `_includes/layouts/post.njk`; archive pagination must
  not change their URLs or post-level navigation.
- `tests/archive-output.test.js` currently contains only a note that
  `/blog/index.html` should be covered; it does not yet execute production
  output assertions.
- `docs/development/index.md` records that no archive pagination
  specification currently exists. The maintained development documentation is
  the appropriate owner for the eventual archive URL and navigation contract.

## Execution plan

Status: Draft

The archive will become an Eleventy pagination source over the same
newest-first sequence currently rendered by `/blog/`. Pagination must happen
after establishing that sequence, or use Eleventy’s reverse-aware pagination
behavior, so slicing does not put older posts on the first page. The archive
template will render the pagination items without applying a second reversal.
The shared post-list partial will either retain its current default for the
home and tag callers or receive an explicit ordering input; whichever small
template change is needed must leave those callers’ rendered order unchanged.

Each generated archive page will render a semantic navigation landmark with an
accessible label and named Previous/Next links. Links will use the resolved
stable archive URL pattern and point only to adjacent existing pages; the
first page will have no Previous link and the final page will have no Next
link. Where supported by the generated markup, previous/next relationship
metadata will agree with the visible links. No client-side code will be
introduced.

Verification will exercise the real Eleventy build and inspect generated
files. A test-only content fixture or temporary build input will provide
enough posts for three pages (41 posts), allowing the test to verify the
twenty-item limit, first/middle/last navigation states, stable paths, complete
ordered coverage, and absence of duplicate posts. The same production-output
check will assert that the home page, tag page, feed, sitemap, and
representative individual-post output remain available and unchanged in their
relevant contracts, and that generated HTML contains no JavaScript added by
the pagination feature.

### Implementation decisions and open questions

- The exact later-page URL remains an unresolved requirement question above.
  Once selected, it becomes the canonical permalink contract and must be
  covered by output tests and documentation.
- Pagination belongs to the archive template/data boundary. The shared list
  partial must not acquire archive-only links or pagination state that leaks
  into home or tag pages.
- The test should cross the production Eleventy build boundary rather than
  validate only front matter or template text. It may use temporary fixture
  content, but it must use the actual templates, configuration, collections,
  and output paths.

### Documentation

- After implementation, update `docs/development/index.md` with the confirmed
  archive URL pattern, twenty-post page limit, ordering rule, and accessible
  navigation behavior.
- Keep the task file as the execution handoff; do not describe the planned
  behavior as current user guidance before the implementation and production
  build verification are complete.

### Task checklist

- [ ] Resolve the canonical later-page URL requirement.
- [ ] Mark this plan `Approved` after the URL contract is confirmed.
- [ ] Implement archive pagination without changing shared-surface ordering.
- [ ] Add semantic accessible previous/next navigation.
- [ ] Add production-output regression coverage using a three-page fixture.
- [ ] Update the maintained development documentation.
- [ ] Run the focused test and production build checks.
- [ ] Record requirement evidence and completion notes in this task file.

### Requirement verification

- `/blog/` remains the first page, later pages are stable, and every page has
  at most twenty posts: one production Eleventy build test should enumerate
  the generated archive paths and inspect each page’s rendered post links.
- Post order is preserved without gaps or duplicates: the same build test
  should compare the concatenated archive post URLs with the pre-pagination
  newest-first sequence.
- Previous/next navigation is accessible and correctly bounded: the same
  output test should inspect the navigation landmark, link names/relationships,
  and first/middle/last page link presence.
- Home, tags, feed, sitemap, and individual posts remain preserved: focused
  assertions against the generated production output should cover each route
  family and its existing post ordering or URL contract.
- Output remains zero-JavaScript: generated HTML for archive, home, tag, and
  post pages should contain no script element or pagination runtime.

### Additional implementation verification

- Run the repository test command after the focused archive-output coverage is
  added.
- Run a clean Eleventy production build and inspect the generated archive
  directory so the test harness itself is not the only evidence of route
  generation.