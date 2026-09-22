# Paginate the blog archive

The `/blog/` archive currently lists every post on a single page, which
becomes hard to browse as the post count grows. Introduce Eleventy pagination
so `/blog/` stays the first archive page, later pages hold at most 20 posts
at stable URLs, and archive pages are linked with accessible previous/next
navigation — while preserving the home page, tag pages, feed, sitemap,
individual-post navigation, post order, and the static zero-JavaScript
output. Plan and task structure only; execution is not authorized yet.

## Requirements checklist

- [ ] `/blog/` remains the first archive page at its current URL, with no
      duplicate first page (no `/blog/1/`).
- [ ] Archive pages contain at most 20 posts. Additional pages are generated
      only while posts exceed the page size, at stable numbered URLs
      (`/blog/2/`, `/blog/3/`, …); no empty trailing pages.
- [ ] Archive pages expose previous/next navigation that is accessible: the
      links sit in a `<nav>` landmark with an accessible name, link text
      describes the destination, and each link is rendered only when its
      target page exists (no previous link on page 1, no next link on the
      last page; no disabled placeholder links).
- [ ] Post order is preserved: page 1 holds the newest posts and each later
      page continues with progressively older posts; within-page listing
      order stays newest-first, matching the current archive.
- [ ] Home page behavior is unchanged (newest three posts, shared posts-list
      markup).
- [ ] Tag page behavior is unchanged (one page per collection other than
      `all` and `posts`, listing that tag's posts).
- [ ] Feed behavior is unchanged (all posts, no pagination pages in the feed).
- [ ] Sitemap continues to list the site's pages and now includes the
      additional archive pages.
- [ ] Individual post URLs and the current per-post navigation state are
      unchanged.
- [ ] Output remains static HTML with zero client-side JavaScript.
- [ ] Maintained documentation is updated in the same change: `README.md`
      describes the paginated archive, and the development docs no longer
      state that no archive pagination specification exists.
- [ ] `tests/archive-output.test.js` provides production-build evidence for
      pagination, navigation, and the preserved surfaces, and the suite
      passes.

## Decisions affecting scope or outcomes

- **D1 — Later-page URL scheme (open, needs approval).** Numbered pages:
  `/blog/2/`, `/blog/3/`, … with page 1 kept at `/blog/`. This is the
  Eleventy-standard scheme and directly satisfies "stable later pages".
  Alternative considered: date-range URLs; rejected as nonstandard and
  harder to keep stable.
- **D2 — Meaning of "stable" (open, needs approval).** Page-numbered URLs are
  deterministic and the set of URLs only grows; the posts on each page shift
  as new posts publish (page 1 always shows the newest 20). The alternative —
  date-anchored pages whose contents never shift — is disproportionate for
  this site.
- **D3 — Page size.** Exactly 20, satisfying "at most twenty"; the last page
  may be smaller.

No other requirement questions are open.

## Supporting details

### Current state (verified by inspection)

- Eleventy 3 (`@11ty/eleventy` ^3.0.0, ESM project). Scripts: `npm run build`
  → `eleventy`, `npm test` → `node --test tests/*.test.js`. `node_modules`
  is not installed in this workspace; execution must install dependencies
  first.
- `eleventy.config.js` — input `content/`, includes `../_includes`, output
  `_site/`; provides the `head` filter. `_site/` and `node_modules/` are
  gitignored; no `public/` directory exists (its passthrough copy is a
  no-op).
- `content/blog.njk` — permalinks to `/blog/` and includes
  `_includes/postslist.njk` with `collections.posts`.
- `_includes/postslist.njk` renders `postslist | reverse`, so archives
  display newest-first (`collections.posts` is oldest-first; consistent with
  the feed's `| reverse` and the home page's `head(-3)` for "newest three").
- `content/index.njk` — home page passes `collections.posts | head(-3)` (the
  three newest) to the shared include.
- `content/tag-pages.njk` — pagination over `collections` (size 1, filter
  `[all, posts]`), permalinks `/tags/{{ tag | slugify }}/`, same include.
  With current content the only collections are `all` and `posts`, so no tag
  pages are generated today.
- `content/feed.xml.njk` — `/feed/feed.xml` lists `collections.posts`
  reversed; `layout: false`.
- `content/sitemap.xml.njk` — `/sitemap.xml` lists every page URL from
  `collections.all`, so paginated archive pages are picked up automatically
  if they join that collection.
- `content/posts/` — two posts (`First` 2026-01-01, `Second` 2026-01-02) with
  folder data (`tags: ["posts"]`, layout `layouts/post.njk`); URLs
  `/posts/first/`, `/posts/second/`. `_includes/layouts/post.njk` renders
  title/author/content only — no per-post previous/next navigation exists
  today, so "preserve individual-post navigation" means leaving it as-is.
- `tests/archive-output.test.js` is a comment-only stub with no tests; the
  suite currently passes trivially.
- `docs/development/index.md` states "No archive pagination specification
  exists." — the intended anchor for the specification this change adds.
- Fixture adapted from Eleventy Base Blog (see `UPSTREAM.md`).

### Eleventy pagination capabilities (confirmed against v3 docs)

- `pagination.reverse: true` reverses the data set before chunking, so page 1
  receives the newest posts when paginating `collections.posts`.
- Per-page data includes `pagination.pageNumber` (0-indexed),
  `pagination.href.next` / `pagination.href.previous` (absent on boundary
  pages), `pagination.hrefs`, and `pagination.pages`.
- A conditional permalink keeps page 1 at the base URL while numbering later
  pages, e.g. `/blog{% if pagination.pageNumber > 0 %}/{{ pagination.pageNumber + 1 }}{% endif %}/`.
- Modifier order is `before` → `reverse` → `filter`; `before` is available if
  custom ordering is ever needed.
- By default only the first page of a paginated template joins collections;
  `addAllPagesToCollections: true` on the archive template ensures every
  archive page joins `collections.all` (and thus the sitemap). The template
  stays untagged, so `collections.posts` and the feed remain post-only.

### Constraints from repository guidance

- Documentation must be updated in the same change that makes new public
  claims true; read `docs/development/documentation.md` before creating the
  specification page.
- Tests must cross the real production-build boundary; no test-only
  shortcuts that hide product defects.
- No JavaScript, no new runtime dependencies.

## Execution plan

Status: Draft

### Approach

Convert `content/blog.njk` into Eleventy's paginated archive template:

- Add pagination front matter: `data: collections.posts`, `size: 20`,
  `reverse: true` (page 1 = newest posts, later pages progressively older),
  and `addAllPagesToCollections: true` so all archive pages appear in
  `collections.all`/sitemap.
- Permalink: `/blog{% if pagination.pageNumber > 0 %}/{{ pagination.pageNumber + 1 }}{% endif %}/`
  → `/blog/`, `/blog/2/`, `/blog/3/`, …
- Keep the shared include for consistent markup: pass the page chunk so its
  internal `| reverse` renders each page newest-first (e.g.
  `{% set postslist = pagination.items | reverse %}`).
- Render previous/next navigation only when the corresponding href exists,
  inside a `<nav aria-label="…">` landmark, with descriptive visible link
  text.

`_includes/postslist.njk`, `content/index.njk`, `content/tag-pages.njk`,
`content/feed.xml.njk`, `content/sitemap.xml.njk`, and the post layout stay
unchanged.

### Implementation decisions and open questions

- D1 (later-page URL scheme) and D2 (meaning of "stable") above remain open
  for approval; D3 resolves to page size 20.
- Implementation-local decisions (reversible, resolved by this plan): reuse
  `postslist.njk` rather than a bespoke archive list; apply navigation only
  to archive pages (tag pages stay unpaginated and unchanged); exact link
  wording (e.g. "Previous page" / "Next page") is an implementation detail as
  long as it is visible and describes the destination; no `/blog/1/` page is
  generated.

### Documentation

- `README.md`: extend the build description to cover the paginated archive
  (at most 20 posts per page, previous/next navigation).
- `docs/development/archive-pagination.md`: new specification describing the
  implemented behavior — URL scheme, page size, ordering, navigation rules,
  and preserved surfaces — written as current-behavior documentation as part
  of the implementing change. Read `docs/development/documentation.md` before
  creating it.
- `docs/development/index.md`: replace "No archive pagination specification
  exists." with a link to the new specification.

Audience: developers maintaining the fixture; the README line also serves
site readers.

### Task checklist

- [ ] Implement pagination, permalink scheme, and accessible navigation in
      `content/blog.njk`, reusing `postslist.njk` for listing markup.
- [ ] Extend `tests/archive-output.test.js` with a build harness and
      assertions as described under Testing.
- [ ] Update `README.md`, add `docs/development/archive-pagination.md`, and
      update `docs/development/index.md`.
- [ ] Install dependencies, run `npm test` (suite collects the new tests and
      exits clean) and `npm run build`; spot-check `_site/` output.
- [ ] Keep task statuses current during execution; add
      `## Implementation Notes` while executing and immutable
      `## Completion Notes` after completion.

### Testing

Extend `tests/archive-output.test.js` with an integration harness that builds
through the production path: create a temporary directory, copy
`eleventy.config.js`, `_includes/`, and the `content/` templates, synthesize
a 45-post content set (dates ascending; a couple of posts carry an extra tag
to exercise tag pages), build via Eleventy's programmatic API with output in
the temp directory, then assert on the generated files:

- 45 posts → `/blog/` (20 items), `/blog/2/` (20), `/blog/3/` (5); no
  `/blog/1/`; page 1 starts with the newest post; within-page order is
  newest-first.
- Navigation: page 1 has next only; page 2 has both; page 3 has previous
  only; links point at the adjacent pages; the nav landmark has an
  accessible name; link text is non-empty and direction-describing.
- Preserved surfaces: home lists the newest 3; the extra tag's page lists its
  posts; feed contains all 45 posts (no pagination pages); sitemap includes
  `/blog/`, `/blog/2/`, `/blog/3/`, and the home page; post URLs unchanged.
- Zero-JavaScript: no `<script` in any built HTML file.

A second scenario reuses the harness with the repo's real two posts to prove
the unchanged single-page case: only `/blog/`, no `/blog/2/`, no previous/next
navigation.

Rejected alternative: permanently seeding ~25 test posts into
`content/posts/` — it would exercise the same build path but pollutes the
shipped content and shifts every preserved surface's data. The temp-dir
harness exercises the identical templates and config without that cost.

### Requirement verification

- First page and URL scheme → assertions that `/blog/index.html` exists,
  `/blog/1/` does not, and later pages are `/blog/2/`, `/blog/3/` in the
  harness build; the two-post scenario proves no extra pages are generated.
- Page size and composition → per-page item counts (20/20/5) plus membership
  and within-page order assertions (newest-first; page 1 = newest 20).
- Accessible navigation → markup assertions: `<nav>` with accessible name,
  descriptive link text, hrefs to adjacent pages, links absent on boundary
  pages. Structural build-output assertions are the practical evidence at
  this fixture's boundaries; no screen-reader/axe run is planned because
  there is no browser test infrastructure.
- Preserved surfaces → output assertions for the home page (newest 3), tag
  page, feed entries, sitemap URLs, and unchanged post URLs.
- Zero-JavaScript → assertion that built HTML contains no `<script`.
- Documentation → files updated in the same change and reviewed against the
  built behavior (manual review; no automated check).
- Test evidence → `npm test` collects and passes the new suites (exit 0), and
  `node --test` output shows the new tests are collected (count > 0).

### Additional implementation verification

- Run `npm run build` on the repo's real content and review `_site/` against
  the expected six outputs (`/index.html`, `/blog/index.html`, two post
  pages, `/feed/feed.xml`, `/sitemap.xml`) to confirm nothing regressed for
  the shipped content.
- Confirm `pagination.href.previous`/`href.next` values match the actual
  generated file paths (guards against an off-by-one in the conditional
  permalink).

### Risks and exclusions

- The programmatic API signature must be confirmed against the installed
  Eleventy 3 package during execution; fallback is the CLI with
  `--input`/`--output`/`--config` overrides pointed at the temp directory.
- `reverse: true` semantics are confirmed from the docs, but tests assert
  built output, so any mismatch surfaces as a failing assertion rather than a
  silent regression.
- Dependency installation requires registry access (`node_modules` is not
  present).
- Out of scope: per-post previous/next navigation, tag-page pagination, any
  JavaScript, and new dependencies.