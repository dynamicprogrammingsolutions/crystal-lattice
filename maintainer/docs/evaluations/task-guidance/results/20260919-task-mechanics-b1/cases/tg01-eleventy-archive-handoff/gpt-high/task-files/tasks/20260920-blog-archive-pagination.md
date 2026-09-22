# Paginated blog archive

Plan the Eleventy archive pagination needed to keep `/blog/` usable as the
post collection grows, while preserving the site's existing generated pages
and static-output contract.

## Requirements checklist

- [ ] Keep `/blog/` as the first archive page and preserve its newest-first
      post ordering.
- [ ] Generate deterministic later archive pages containing no more than
      twenty posts each.
- [ ] Add accessible previous/next navigation to archive pages, with only the
      links that have a valid adjacent page.
- [ ] Preserve the home page's post selection and order.
- [ ] Preserve tag-page output, feed entries and order, sitemap URLs, and
      individual-post output/navigation.
- [ ] Keep the generated site static and zero-JavaScript; archive paging must
      work through ordinary HTML links.
- [ ] Add production-path evidence for the archive boundaries and the
      preserved outputs.
- [ ] Update the maintained development documentation with the supported
      archive URL and pagination behavior after implementation.

## Unresolved requirement questions

- What exact URL pattern should later archive pages use? The recommended
  convention is `/blog/page/2/`, `/blog/page/3/`, and so on, because it keeps
  `/blog/` as the canonical first page and makes the page number explicit.
  This needs confirmation before the plan can become Approved; the chosen
  pattern is a public URL contract.

## Research and supporting facts

- `content/blog.njk` currently maps only `/blog/` and passes the complete
  `collections.posts` collection to `_includes/postslist.njk`.
- `_includes/postslist.njk` reverses the supplied collection for display, so
  the implementation must preserve the existing collection/order convention
  when slicing pages.
- `content/index.njk` independently selects the latest three posts through
  the `head(-3)` filter; archive pagination must not change that selection.
- Tag pages use Eleventy pagination in `content/tag-pages.njk` and should
  remain independent of the archive pagination.
- The feed iterates the full posts collection in reverse order, and the
  sitemap iterates `collections.all`; neither should be narrowed to the first
  archive page.
- The repository currently contains two posts, so boundary coverage needs a
  fixture or fixture expansion with more than twenty posts to exercise a
  second page and the page-size limit.
- `tests/archive-output.test.js` currently contains only a comment describing
  a `/blog/index.html` existence check; it is the natural owner for
  production-build archive regression coverage.
- `docs/development/index.md` currently says that no archive pagination
  specification exists. It should be updated only when the supported behavior
  is implemented and verified.
- The current source templates do not show client-side JavaScript or an
  explicit individual-post navigation include. Verification should inspect
  the generated public output and preserve any behavior supplied by the
  current production build rather than inventing a new post-navigation
  contract.

## Scope and boundaries

In scope are the archive template/configuration changes required to generate
the first and later archive pages, the semantic navigation markup, realistic
production-build tests, and the maintained development documentation.

The home page, tag pages, feed, sitemap, individual posts, post ordering, and
JavaScript policy are compatibility constraints, not targets for redesign.
No client-side pagination, infinite scrolling, feed pagination, tag
pagination, or unrelated layout changes are planned.

## Execution plan

Status: Draft

Use Eleventy pagination at the archive boundary with a page size of twenty
posts. Preserve the existing display order by establishing the same
newest-first sequence before pagination (or by applying the existing shared
list convention consistently), then render each page from its own slice.
Retain `/blog/` for the first page and use the approved stable page-number
permalink pattern for subsequent pages.

Add a small semantic navigation block to the archive output. It should use a
`nav` landmark with an accessible label and ordinary anchors for previous and
next pages. The first page must omit previous, the final page must omit next,
and a middle page must expose both. Link text and/or accessible names should
identify the destination page without relying on visual styling or
JavaScript.

Keep the archive data source separate from consumers that need the complete
collection. Confirm that the home page, tag pages, feed, sitemap, and
individual-post rendering still receive their existing inputs and retain
their order and URLs.

Extend the production-build test to create enough representative posts to
cross the twenty-post boundary, then inspect generated files for:

- the first-page route and later stable routes;
- at most twenty post links per archive page, with no duplicates or gaps
  across the archive;
- newest-first ordering;
- correct previous/next presence at first, middle, and final pages;
- accessible navigation markup and ordinary HTML links;
- unchanged home, tag, feed, sitemap, and representative post behavior;
- no JavaScript dependency in the generated output.

Prefer test data that exercises the real Eleventy content/build path. If
temporary test content is necessary, build it with the same production
templates and configuration rather than testing a copied pagination helper in
isolation.

### Implementation decisions and open questions

- **Open requirement question:** confirm the public later-page URL pattern.
  Recommendation: `/blog/page/<n>/`, starting at `n = 2`.
- **Implementation decision after URL approval:** keep the first page at the
  existing `/blog/` permalink; do not introduce `/blog/page/1/` as a second
  public entry point unless compatibility evidence requires it.
- **Implementation decision:** pagination navigation is server-generated
  markup with links, not client-side state or scripts.
- **Implementation decision:** page-size and navigation tests must cross the
  twenty-post boundary through the production build.
- **Risk:** changing the collection before the shared list reverses it could
  invert page order or split posts incorrectly. The test must assert the
  complete cross-page sequence, not only individual page counts.
- **Risk:** applying archive pagination to a shared collection could
  accidentally truncate home, tag, feed, or sitemap data. Keep the archive
  page data local and assert those consumers independently.

### Documentation

After implementation and verification, update `docs/development/index.md` to
replace the current “no archive pagination specification exists” statement
with the supported archive contract: `/blog/` is the first page, later pages
use the approved stable URL pattern, each page contains at most twenty posts,
and navigation is available through accessible static links. Do not document
the target behavior as current before the build and tests prove it.

### Task checklist

- [ ] Resolve and record the stable later-page URL pattern.
- [ ] Implement archive-only pagination with a maximum of twenty posts per
      page while retaining `/blog/`.
- [ ] Add accessible static previous/next navigation with correct boundary
      behavior.
- [ ] Add or adapt realistic production-build fixture data beyond twenty
      posts.
- [ ] Expand archive-output coverage for page generation, ordering, links,
      boundaries, and zero-JavaScript output.
- [ ] Add regression assertions for the home page, tags, feed, sitemap, and
      individual-post output/navigation.
- [ ] Update `docs/development/index.md`.
- [ ] Run the production build and the relevant test suite; record results and
      any environment limitations.

### Requirement verification

- **First page and stable later pages:** production-build inspection finds
  `/blog/index.html` plus the approved later-page files, and the URL sequence
  is deterministic for the same post set.
- **Maximum page size and post order:** generated archive pages contain no
  more than twenty post entries, and concatenating pages in order produces
  the same newest-first sequence as the unpaginated archive.
- **Accessible previous/next navigation:** generated first, middle, and final
  pages contain the expected `nav` landmark and only valid adjacent-page
  anchors, with destination-identifying accessible names.
- **Preserved consumers:** generated home, tag, feed, sitemap, and
  individual-post artifacts retain their expected URLs, membership, ordering,
  and navigation/content relationships.
- **Static zero-JavaScript output:** archive navigation is represented by
  server-rendered HTML anchors, and the production output contains no
  pagination script or client-side pagination dependency.

### Additional implementation verification

- Run the configured `npm test` suite after the focused archive test is
  updated.
- Run the production `npm run build` and inspect the generated file set,
  including page-count and route-boundary behavior.
- Check that generated output does not leave stale later-page files when the
  post count changes, if the build/test harness makes that state observable.