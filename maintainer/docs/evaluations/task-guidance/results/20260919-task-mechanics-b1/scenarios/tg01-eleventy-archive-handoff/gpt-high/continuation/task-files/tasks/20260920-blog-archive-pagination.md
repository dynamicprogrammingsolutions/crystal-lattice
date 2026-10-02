# Paginate the blog archive

Plan the Eleventy archive change so the first archive page remains `/blog/`,
later pages are stable and contain no more than twenty posts, and visitors can
move between archive pages with accessible previous/next links. The change
must retain the existing site outputs and remain entirely static.

## Requirements checklist

- [ ] Keep `/blog/` as the first archive page.
- [ ] Generate deterministic, stable URLs for later archive pages, with no
      archive page containing more than twenty posts.
- [ ] Preserve the existing archive post order across page boundaries.
- [ ] Provide accessible previous/next navigation between adjacent archive
      pages, without links to unavailable pages.
- [ ] Preserve the home page, tag pages, feed, sitemap, individual-post URLs
      and navigation, and the static zero-JavaScript output.

## Requirement questions and decisions

- Open requirement question: what public URL pattern should later pages use?
  The implementation needs an explicit answer before execution because the
  pattern is a public, durable URL contract. A reasonable recommendation is
  `/blog/2/`, `/blog/3/`, and so on, while retaining `/blog/` for page one.
- Decision: use one task file rather than subtasks. The requested outcome is
  one end-to-end archive capability; tests and documentation belong with that
  capability and do not have independent acceptance boundaries.

## Research and supporting facts

- `content/blog.njk` currently owns `/blog/` and renders the complete
  `collections.posts` collection through `_includes/postslist.njk`.
- `_includes/postslist.njk` reverses the supplied collection while rendering,
  so the pagination boundary must be applied to the same display order if
  post order is to remain unchanged.
- `content/index.njk` independently renders the latest three posts, and
  `content/tag-pages.njk`, `content/feed.xml.njk`, and
  `content/sitemap.xml.njk` consume collections for other public outputs.
- `content/posts/posts.json` supplies the individual-post layout. No source
  change is authorized by this handoff, and existing post URLs/content must
  remain stable.
- `tests/archive-output.test.js` currently contains only a note that
  `/blog/index.html` is covered; it does not yet provide executable production
  build assertions.
- `docs/development/index.md` records that no archive pagination specification
  exists. The maintained documentation should be updated with the supported
  behavior when implementation is complete, rather than documenting the Draft
  plan as current behavior.
- The repository has no `tasks/` directory yet, and dependencies are not
  installed in the workspace. No build or test was run while preparing this
  plan.

## Execution plan

Status: Draft

Implement and verify pagination at the production Eleventy boundary. Resolve
the later-page URL pattern before changing the public permalink contract.
Preserve the current archive display sequence by paginating the ordered posts
that the archive actually renders, then render each page with the existing
post-list partial or an equivalent shared rendering boundary. Keep page one
at `/blog/`; make later page paths deterministic and independent of post
titles, dates, or collection mutations.

Add archive pagination controls as semantic HTML in the generated archive
pages. The controls should expose a navigation landmark with a meaningful
accessible label, use clear previous/next link names (and useful accessible
names if additional context is needed), render only links whose neighboring
page exists, and point to the canonical archive page URLs.

Extend the production-build test coverage with enough posts to cross the
twenty-post boundary. Assert the generated public files and their rendered
links, including the following cases:

- `/blog/` exists and is the first page.
- Every generated archive page contains at most twenty post entries.
- The complete archive sequence across pages matches the pre-existing post
  order, with no omissions or duplicates.
- The first, middle, and final pages expose the correct available navigation
  links and do not expose invalid previous/next destinations.
- Existing home-page, tag, feed, sitemap, and individual-post outputs retain
  their expected URLs and post ordering.
- Generated archive pages contain no client-side JavaScript dependency or
  pagination script.

Update the maintained development documentation after the implementation is
verified. Describe the supported archive URL shape, page-size limit, and
accessible navigation behavior, and keep the documentation scoped to the
archive capability.

### Implementation decisions and open questions

- The later-page URL pattern remains blocked on the requirement question
  above. Do not silently choose a different public pattern during execution.
- The page-size boundary is fixed at twenty posts maximum; the final page may
  contain fewer.
- Navigation should be emitted by the static templates/build and should not
  require JavaScript, client-side state, or runtime requests.
- If the chosen Eleventy pagination mechanism changes collection shape or
  ordering, add a small dedicated ordering transformation at the archive
  boundary rather than changing the shared collection consumers.

### Documentation

- Update `docs/development/index.md` (or the smallest more appropriate
  maintained development document if ownership changes during implementation)
  only after the behavior is implemented and verified.
- Document current supported behavior, not the Draft plan or unresolved URL
  choice.

### Task checklist

- [ ] Resolve and record the stable later-page URL pattern.
- [ ] Implement deterministic archive pagination with a maximum of twenty
      posts per page while preserving display order.
- [ ] Add semantic accessible previous/next navigation to generated archive
      pages.
- [ ] Add production-build regression coverage using more than twenty posts.
- [ ] Verify home, tags, feed, sitemap, individual posts, post order, and
      zero-JavaScript output through the production build.
- [ ] Update the maintained development documentation.
- [ ] Record implementation and completion notes after execution; this Draft
      handoff intentionally has none yet.

### Requirement verification

- `/blog/` remains the first page: verify the production build writes
  `/blog/index.html`, that its canonical URL is `/blog/`, and that its first
  twenty rendered entries are the first segment of the preserved archive
  sequence.
- Stable later pages and the twenty-post limit: verify every generated
  archive permalink is deterministic under the approved URL pattern and count
  the rendered post entries in each page, including the final partial page.
- Preserved post order: compare the concatenated post URLs from all archive
  pages with the existing archive display order; require no duplicates or
  omissions.
- Accessible previous/next navigation: inspect generated HTML on first,
  interior, and final pages for a labeled navigation landmark, valid adjacent
  links, and absence of unavailable-direction links.
- Preserved site outputs: build and assert the home page, tag pages, feed,
  sitemap, and individual-post URLs/content still generate; compare their
  post sequences where applicable.
- Static zero-JavaScript output: inspect the generated archive pages and build
  artifacts for the absence of pagination scripts or runtime dependencies.

### Additional implementation verification

- Run the repository test command after dependencies are available and run a
  production build directly as part of the integration evidence.
- Inspect the generated output directory for unexpected archive paths,
  duplicate page generation, or accidental changes to feed/sitemap entries.