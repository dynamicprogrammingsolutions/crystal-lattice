# Paginated blog archive

Plan the Eleventy archive change so a growing post collection remains browseable
through stable static pages while all existing site surfaces continue to use
the same post collection and ordering.

## Requirements checklist

- [ ] Keep `/blog/` as the first archive page.
- [ ] Generate deterministic later archive URLs with at most twenty posts per
      page.
- [ ] Preserve the existing newest-first post order across page boundaries,
      without dropping or duplicating posts.
- [ ] Add accessible previous/next navigation to archive pages, with only the
      links valid for the current page exposed.
- [ ] Preserve the home page, tag pages, feed, sitemap, and individual-post
      pages and navigation.
- [ ] Keep the archive output static and usable without client-side JavaScript.

## Open requirement questions and decisions

- Requirement question: confirm the public URL shape for later pages. The
  recommended convention is `/blog/2/`, `/blog/3/`, and so on, with the
  existing trailing-slash style; this is user-visible and should be confirmed
  before execution.
- Decision: scope pagination to the archive template. Do not paginate or
  reorder the global `collections.posts` collection, because the home page,
  tags, feed, sitemap, and individual posts consume it independently.
- Decision: use Eleventy’s build-time pagination and rendered links. No
  browser-side state, fetches, or JavaScript navigation is part of the
  design.
- Decision: the archive must render one canonical post list per page. The
  current template invokes the shared list include and then emits another
  archive list; retaining both would make a twenty-post page contain duplicate
  entries and would violate the page-size requirement.

## Supporting facts

- `content/blog.njk` currently owns `/blog/`, passes the complete
  `collections.posts` collection to `_includes/postslist.njk`, and separately
  loops over the reversed collection.
- `_includes/postslist.njk` reverses its `postslist` input before rendering.
  Pagination must therefore establish newest-first page boundaries before the
  include’s local ordering behavior is applied; reversing each already-sliced
  page would group the wrong posts.
- `content/index.njk`, `content/tag-pages.njk`, `content/feed.xml.njk`, and
  `content/sitemap.xml.njk` consume the collection through separate templates.
  `content/posts/posts.json` and `_includes/layouts/post.njk` own individual
  post rendering.
- The existing archive test only documents that `/blog/index.html` exists; it
  does not currently build and inspect page contents or any preservation
  surfaces.
- `README.md` describes the generated site at a high level, while
  `docs/development/index.md` explicitly notes that no archive pagination
  specification exists. `docs/development/documentation.md` was reviewed
  before planning this documentation change.

## Execution plan

Status: Draft

Implement archive-only Eleventy pagination using the confirmed later-page URL
convention. Feed the paginator an ordering that preserves the current
newest-first archive semantics, partition into pages of twenty, and retain
the `/blog/` permalink for page one. Render the page’s posts once through the
existing presentation conventions, then add a semantic navigation region with
visible Previous/Next links, appropriate `rel` values, and no invalid link on
the first or final page.

Extend the production-build test to use enough deterministic posts to exercise
the first, middle, and final page states. Assert page size, URL stability,
boundary navigation, cross-page ordering, complete non-overlapping coverage,
and absence of archive JavaScript. In the same build, assert that the home
page, tags, feed, sitemap, and individual-post output remain present and
consistent with the pre-pagination collection behavior.

Update the maintained README and development archive note after the behavior
is implemented, documenting the public archive URL pattern, twenty-post
limit, and static navigation. Do not publish the target behavior as current
documentation while this plan remains unimplemented.

### Implementation decisions and open questions

- Resolve the later-page permalink question before marking this plan
  `Approved`; `/blog/2/` is the working recommendation.
- Prefer Eleventy pagination metadata for previous/next targets so links are
  generated from the same page graph as the output. The exact Nunjucks
  property names should be verified against the installed Eleventy version
  during implementation.
- Keep collection order and all non-archive templates unchanged. If the
  shared include cannot express the required archive ordering without
  affecting home or tag output, use archive-local rendering rather than
  changing those consumers’ contracts.
- Use a realistic production build with a collection large enough to exercise
  all navigation states. Do not mock pagination metadata or test a
  JavaScript-only fallback.

### Documentation

- Update `README.md` with the supported archive pagination behavior once it is
  implemented and verified.
- Replace the stale archive note in `docs/development/index.md` with the
  current URL and page-size contract, or remove it if the maintained
  documentation no longer needs a separate archive specification.
- No documentation files are changed during this planning-only request.

### Task checklist

- [ ] Confirm the later-page URL convention and approve this execution plan.
- [ ] Implement archive-only build-time pagination with a twenty-post page
      size and stable first-page permalink.
- [ ] Preserve newest-first ordering and eliminate duplicate archive entries
      while leaving other collection consumers unchanged.
- [ ] Add semantic, visible previous/next archive navigation with correct
      first/middle/final-page behavior.
- [ ] Expand or arrange realistic build input and update production-build
      regression coverage for pagination and preserved site surfaces.
- [ ] Update maintained README/development documentation.
- [ ] Run the focused test and production build, then record evidence and any
      deviations in the task file.

### Requirement verification

- First-page and later-page URL requirements: inspect the built `_site` paths
  and assert the first archive is `/blog/` while later pages follow the
  approved stable convention.
- Page-size and ordering requirements: parse every generated archive page,
  assert no page contains more than twenty post entries, and compare the
  concatenated links against the expected newest-first collection with no
  gaps or duplicates.
- Navigation requirement: assert first, middle, and final pages expose the
  correct visible Previous/Next links and omit links that have no destination.
- Preservation requirements: build and inspect home, tag, feed, sitemap, and
  representative individual-post URLs and content; compare their post order
  or membership to the unpaginated collection contract where applicable.
- Static-output requirement: inspect generated archive HTML and the output
  asset set for absence of client-side JavaScript dependencies.