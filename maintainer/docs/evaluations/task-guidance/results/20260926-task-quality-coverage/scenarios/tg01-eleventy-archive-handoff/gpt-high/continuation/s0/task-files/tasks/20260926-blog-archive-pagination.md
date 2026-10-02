# Paginate the blog archive

Plan the static pagination of the growing blog archive while preserving the
site's existing collection consumers and generated output.

## Requirements checklist

- [ ] Keep `/blog/` as the first archive page, without a `/blog/1/` alias.
- [ ] Generate stable later archive pages with no more than twenty posts per
      page.
- [ ] Add accessible previous/next navigation to archive pages, with correct
      boundary behavior and links that work without JavaScript.
- [ ] Preserve the home page's post selection and order.
- [ ] Preserve tag pages, the feed, the sitemap, individual-post navigation,
      and the existing newest-first post order.
- [ ] Keep the generated site static and free of JavaScript-based archive
      behavior.
- [ ] Add production-build evidence for pagination and regression coverage for
      every preserved public output.
- [ ] Update the maintained development documentation so it describes the
      implemented archive pagination rather than claiming that no pagination
      specification exists.

## Scope

The change is limited to the blog archive's page generation, archive-only
navigation markup, and the tests and developer documentation needed to explain
and verify that behavior. It does not redesign the home page, tag URLs, feed
format, sitemap format, post routes, post content, or individual-post
navigation.

## Unresolved requirement questions and design decisions

- No requirement question is currently blocking the plan.
- Design decision to confirm before execution: use `/blog/2/`, `/blog/3/`,
  and so on for later pages, while reserving `/blog/` for page one. This is the
  recommended stable URL scheme because it makes page identity explicit and
  avoids changing the existing archive URL.
- Design decision to confirm before execution: label links according to archive
  chronology and expose them in a semantic navigation landmark. The
  recommendation is visible “Previous” and “Next” links with `rel="prev"` and
  `rel="next"` where applicable, plus an `aria-label` identifying the archive
  pagination. The implementation must define the direction consistently with
  the newest-first page order and omit unavailable boundary links.

## Research and supporting facts

- `content/blog.njk` currently owns `/blog/` and renders the complete
  `collections.posts` collection.
- `_includes/postslist.njk` reverses its input while rendering, which gives the
  current newest-first order. The same include is used by the home page and tag
  pages, so archive pagination must not accidentally reverse or repartition
  those consumers.
- `content/index.njk` selects the last three collection entries before using
  the shared list include. `content/tag-pages.njk` renders each tag collection
  through that include.
- `content/feed.xml.njk` independently reverses `collections.posts`, and
  `content/sitemap.xml.njk` iterates `collections.all`. These consumers should
  continue to use the unpaginated collection.
- The current post layout is `_includes/layouts/post.njk`; the visible fixture
  does not currently contain post-navigation markup. The implementation must
  keep archive pagination isolated from post rendering and verify the existing
  individual-post output and any post-navigation links supplied by the
  production source.
- `tests/archive-output.test.js` currently contains only a comment saying that
  `/blog/index.html` exists, so the archive boundary lacks executable
  regression coverage.
- `README.md` already describes the site as producing static pages without
  client-side JavaScript. `docs/development/index.md` currently says that no
  archive pagination specification exists; that maintained statement should be
  updated after implementation. The documentation rules in
  `docs/development/documentation.md` require keeping the public claim and
  behavior change in the same reviewed change.

## Execution plan

Status: Draft

Use Eleventy pagination for the archive source while keeping the existing
`collections.posts` collection intact for the home page, tags, feed, sitemap,
and individual posts. The archive should paginate an explicitly newest-first
sequence (or use Eleventy's equivalent reverse-pagination option) so page
boundaries are calculated before rendering and each page displays at most
twenty posts. Page one should retain the existing `/blog/` permalink; later
page permalinks should be deterministic numbered paths under `/blog/`.

Keep the shared list include's behavior for the home page and tag pages
unchanged. If the archive needs a directly ordered page-item loop, give the
archive its own small rendering boundary rather than changing the shared
include in a way that could double-reverse page items. Render pagination links
only in the archive template or an archive-owned include, using semantic
navigation, visible link text, an accessible label, and `rel` metadata. Do not
introduce client-side code, runtime routing, or a JavaScript dependency.

Replace the placeholder archive test with an integration test that builds the
site through the real Eleventy production path and inspects generated public
files. The test should use a temporary copy or equivalent isolated fixture
containing enough posts to exercise a full first page, a full later page, and
the final partial page; it must still use the production templates,
configuration, collection definitions, and build command rather than mocking
pagination data. The same test suite should retain a small baseline that makes
the existing home, tags, feed, sitemap, and individual-post assertions easy to
diagnose.

### Implementation decisions and open questions

- Recommended archive URL contract: `/blog/` for page one and
  `/blog/<page-number>/` for page numbers starting at two.
- Keep the source collection unpaginated. Archive pagination is a view over
  that collection, not a replacement for the collection used by other
  outputs.
- Preserve newest-first ordering both within each archive page and across
  page boundaries. A post must occur on exactly one archive page.
- Use a semantic `<nav>` landmark with an accessible label and visible
  Previous/Next links. Omit Previous on the first page and Next on the last
  page; do not render dead or placeholder links.
- No current source file exposes individual-post navigation markup. Treat
  post-route/content preservation and archive-nav isolation as the automated
  checks available in this fixture, and require a human check if a broader
  post-navigation contract is supplied outside the visible source.

### Documentation

- Update `docs/development/index.md` with the supported archive URL pattern,
  twenty-post page limit, page-one `/blog/` behavior, and the no-JavaScript
  navigation contract.
- Do not update `README.md` unless implementation changes its existing
  static-site claim; pagination should remain compatible with that claim.
- Keep this task file as the planning and execution handoff. Do not present the
  target pagination behavior as current user guidance until implementation and
  verification are complete.

### Task checklist

- [ ] Confirm the numbered later-page URL and Previous/Next wording/direction.
- [ ] Add archive pagination metadata and stable conditional permalinks.
- [ ] Preserve the unpaginated collection consumers and shared-list behavior.
- [ ] Add archive-only accessible navigation with correct first/last-page
      boundaries.
- [ ] Replace the placeholder test with a real production-build integration
      test and a sufficiently large isolated post fixture.
- [ ] Add regression assertions for home, tags, feed, sitemap,
      individual-post output/navigation, post order, and absence of
      JavaScript.
- [ ] Update the maintained development documentation.
- [ ] Run the build and test suite, then inspect generated archive URLs and
      navigation at the public-file boundary.

### Requirement verification

- “`/blog/` remains the first page” and “later pages are stable”:
  production-build test asserts `/blog/index.html` exists, `/blog/1/` does
  not, numbered later pages exist for the fixture, and their links resolve to
  the expected generated files.
- “At most twenty posts per page” and “post order is preserved”:
  production-build test parses every archive page, counts rendered post links,
  asserts the count is no greater than twenty, asserts newest-first order within
  each page, and asserts the concatenated pages contain each post once in the
  original archive order.
- “Accessible previous/next navigation”:
  production-build test checks the rendered archive navigation landmark,
  accessible label, visible Previous/Next links, `rel` values, destination
  paths, and omission of the unavailable link at the first and last page.
  Human review should also confirm the labels are understandable when read
  without surrounding visual context.
- “Preserve home, tags, feed, sitemap, and individual-post navigation”:
  the same real build asserts the existing home selection/order, tag output and
  URLs, feed entry order, sitemap URLs, post routes/content, and any existing
  post-navigation links remain unchanged; archive pagination markup must not
  appear on individual post pages.
- “Static zero-JavaScript output”:
  the generated public HTML/XML is searched for script elements or injected
  runtime navigation code, and the archive links are verified as ordinary
  generated anchors.
- “Documentation is current”:
  inspect `docs/development/index.md` after the implementation and confirm its
  URL, limit, accessibility, and static-output claims match the generated
  files and passing integration test.

### Additional implementation verification

- Run `npm test` and the production `npm run build` from a clean working tree
  state appropriate to the repository.
- Inspect the generated output for trailing-slash URL consistency and ensure
  no empty archive page is emitted when the post count is an exact multiple of
  twenty.
- Confirm the temporary large-post fixture is isolated and cleaned up so test
  data cannot become public content or leave unrelated repository changes.