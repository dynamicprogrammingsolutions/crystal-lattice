# Blog archive pagination

Paginate the blog archive so `/blog/` stays the first archive page, later
pages hold at most twenty posts at stable URLs, and accessible
previous/next navigation links the pages together. The home page, tags,
feed, sitemap, individual posts, post order, and the static
zero-JavaScript output are preserved. Planning only — implementation
awaits plan approval.

## Requirements checklist

- [ ] `/blog/` remains the first archive page at the same URL, listing posts
      newest first as it does today.
- [ ] Later archive pages are generated for the remaining posts, each holding
      at most 20 posts, at stable deterministic URLs (a fixed scheme chosen in
      the plan; existing archive URLs stay valid as content grows).
- [ ] Archive pages expose accessible previous/next navigation: HTML links in
      a labelled `nav` landmark, rendered only when the target page exists,
      with no client-side JavaScript.
- [ ] Home page (`/`) is unchanged: same URL and behavior (latest three
      posts, newest first).
- [ ] Tag pages (`/tags/<tag>/`) are unchanged for every tag.
- [ ] Feed (`/feed/feed.xml`) is unchanged: lists all posts, newest first.
- [ ] Sitemap continues to be generated over all built pages; the new archive
      pages appear in it.
- [ ] Individual post pages, their URLs, and the archive's links to them are
      unchanged.
- [ ] The production output remains static HTML with zero client-side
      JavaScript.
- [ ] Production-build test evidence covers the paginated archive and the
      preserved surfaces (repo testing guidance: add or update evidence for
      changed behavior and regressions).
- [ ] Maintained documentation is updated in the same change: the stale
      `docs/development/index.md` line "No archive pagination specification
      exists." is replaced with a description of the implemented pagination.

## Questions and decisions

No unresolved requirement questions. The user-visible design decisions
(later-page URL scheme, navigation markup) are recorded under the plan's
"Implementation decisions and open questions" and take effect only when the
plan is approved.

## Supporting details

- Eleventy 3 (`@11ty/eleventy` `^3.0.0`); input `content/`, includes
  `_includes/`, output `_site/`. `npm run build` runs `eleventy`; `npm test`
  runs `node --test tests/*.test.js`.
- Today `content/blog.njk` renders all of `collections.posts` through
  `_includes/postslist.njk`; the include reverses its input, so the archive
  displays newest first.
- Every consumer treats `collections.posts` as ascending (oldest first) and
  reverses for display: home uses `head(-3)` (the config filter slices the
  last three), and the archive and feed reverse the collection. The archive
  must keep this newest-first order per page and across pages. (Assumption on
  Eleventy's default collection sort, inferred from the fixture's consistent
  usage; `node_modules` was not installed during planning, so no build was
  run. The planned order assertions fail loudly if the assumption is wrong.)
- New archive pages automatically join `collections.all`, so
  `content/sitemap.xml.njk` will include them without changes. No other
  generating template needs modification.
- `_includes/layouts/post.njk` has no post-to-post navigation; "preserve
  individual-post navigation" means post pages, their URLs, and the archive
  links to them stay intact.
- Only two posts exist (`content/posts/first.md` and `second.md`, dated
  2026-01-01/02), so committed content paginates to a single page.
  Multi-page behavior must be exercised with generated posts in a temporary
  copy, not by committing test posts.
- `tests/archive-output.test.js` is a stub comment; no build coverage exists
  today.
- `docs/development/index.md` currently says "No archive pagination
  specification exists." — the maintained docs location for this behavior.
  The README's build claim ("…blog archive…") stays accurate.
- `node_modules/` is not installed; execution needs `npm install` before
  building or testing.
- The fixture is adapted from Eleventy Base Blog `26b2610` (see
  `UPSTREAM.md`); reference only.
- Eleventy pagination features relied on: `pagination.data`, `size`,
  `reverse`, `items`, `href.next` / `href.previous`, `pages.length`, and a
  page-number-conditional permalink that keeps page 1 at `/blog/`. All are
  standard in Eleventy 2/3; re-check against the installed v3 docs at
  execution if behavior differs.

## Implementation plan

Status: Draft

### Design

`content/blog.njk` becomes a pagination template; every other page-generating
template stays untouched.

- Front matter paginates `collections.posts` with `size: 20` and
  `reverse: true`, so page 1 holds the twenty newest posts and each later
  page the next oldest slice. Permalink
  `/blog/{% if pagination.pageNumber > 0 %}page-{{ pagination.pageNumber + 1 }}/{% endif %}`
  keeps page 1 at `/blog/` and emits `/blog/page-2/`, `/blog/page-3/`, …
- Post order: `pagination.reverse` makes each page's `pagination.items`
  newest first. `_includes/postslist.njk` reverses its input before
  rendering, so the template passes `pagination.items | reverse` (ascending)
  to the include — keeping the include and its home/tag consumers unchanged
  while displaying newest first.
- Navigation: after the list, a
  `<nav aria-label="Blog archive pagination">` containing a page indicator
  ("Page X of Y" from `pagination.pageNumber` and `pagination.pages.length`)
  and anchors built from `pagination.href.previous` and
  `pagination.href.next`, labelled "Previous" / "Next" with `rel="prev"` /
  `rel="next"`. Anchors render only when the href exists, so a single-page
  archive emits no navigation links. Keep the `<h1>Archive</h1>` heading on
  every page.
- No changes to `eleventy.config.js`, `_includes/postslist.njk`,
  `content/index.njk`, `content/tag-pages.njk`, `content/feed.xml.njk`,
  `content/sitemap.xml.njk`, `content/posts/`, or the post layout.

Testing: replace the `tests/archive-output.test.js` stub with an integration
test that runs the real production build in a temporary copy of the repo
(spawn the repo-installed Eleventy CLI, e.g.
`node <repo>/node_modules/@11ty/eleventy/cmd.cjs`, with cwd set to the temp
copy; remove the copy in teardown). Two builds per run:

- Committed content (2 posts): `/blog/` lists both posts newest first with
  no previous/next links and no `page-2` output.
- Copy plus 23 generated posts (25 total, with titles/dates chosen so order
  is unambiguous): asserts page sizes (20 then 5), newest-first order on
  each page and across the page boundary, `/blog/` linking next to
  `/blog/page-2/` with no previous link (the inverse on page 2), the
  labelled nav, home still showing the latest three, the `posts` tag page
  listing all 25, the feed listing all 25 newest first, the sitemap
  including `/blog/`, `/blog/page-2/`, and post URLs, post pages still
  present, and no `<script` in any generated HTML.

### Risks and way back

- Blast radius is one template plus its test and one docs page; the
  `/blog/` URL and every other surface are preserved. Rollback is reverting
  `content/blog.njk` — static output only, no persisted data, and no URLs
  outside the new `/blog/page-N/` pages are affected.
- The reversal chain (`collections.posts` → `pagination.reverse` →
  `pagination.items | reverse` → include) is the main correctness risk; the
  order and count assertions make a mistake fail the build instead of
  shipping.
- If `collections.posts` were not ascending, page 1 would hold the oldest
  posts; the same assertions catch it. Sitemap growth by the new pages is
  intended (they join `collections.all`).

### Order logic

Template change first (a single file), then tests that pin its behavior,
then documentation describing the verified behavior — code and its public
claims land in the same reviewed change. A green `npm test` is the safe
stopping milestone; docs come last so they describe observed output.

### Implementation steps

1. Rewrite `content/blog.njk` with the pagination front matter, per-page
   list, and navigation markup from the design.
2. Rewrite `tests/archive-output.test.js` with the two-build integration
   coverage described above.
3. `npm install` (first run), then `npm test`; fix template or test failures
   until green. Run `npm run build` once and spot-check `_site/blog/`.
4. Update `docs/development/index.md` (replace the stale line with the
   archive pagination section) and confirm the README claim still holds.

### Implementation decisions and open questions

- Later-page URL scheme: `/blog/page-<N>/` for N ≥ 2, page 1 at `/blog/`.
  User-visible decision, presented here for approval.
- Pagination uses `pagination.reverse: true` and feeds
  `pagination.items | reverse` to the shared include, so
  `_includes/postslist.njk`, home, and tag pages keep their current
  contracts unchanged.
- Navigation copy and markup: labelled `nav`, "Previous" / "Next" link text
  with `rel` attributes, a "Page X of Y" indicator, and links rendered only
  when the target page exists.
- Every archive page keeps the single `<h1>Archive</h1>` heading.
- Documentation extends `docs/development/index.md` in place rather than
  adding a new file (smallest structure that serves the reader).
- Tests build a temporary copy of the repo with generated posts instead of
  committing test posts, keeping the production path real.
- Open questions: none.

### Documentation

`docs/development/index.md` gains an "Archive pagination" section replacing
its stale placeholder line — developer-facing text describing implemented
behavior only (URLs, 20-post pages, newest-first order, navigation,
invariants). Audience: developers maintaining the site. The README needs no
change; its "blog archive" claim remains true. No other maintained docs
describe archive structure.

### Task checklist

- [ ] Rewrite `content/blog.njk` as a pagination template (20 per page,
      `reverse: true`, conditional permalink, labelled prev/next nav).
- [ ] Rewrite `tests/archive-output.test.js` as the two-build integration
      test (single-page and 25-post cases).
- [ ] `npm install` (if needed), `npm test`, and `npm run build` green.
- [ ] Update `docs/development/index.md` with the implemented archive
      pagination section; verify README accuracy.

### Requirement verification

- `/blog/` first page, post order, ≤ 20 posts per page, stable later URLs →
  the 25-post build's assertions on `_site/blog/index.html` and
  `_site/blog/page-2/index.html` (URL set, per-page link counts, cross-page
  order). Deliberately not covered: archives beyond two pages.
- Accessible prev/next navigation, zero JS → per-page nav markup
  assertions, absence of links when no target page exists, and a
  `<script` scan across generated HTML. Deliberately not covered:
  screen-reader experience.
- Home / tags / feed / sitemap / post pages preserved → the 25-post build's
  assertions on each generated surface (behavioral content checks, not
  byte-identity; the underlying templates are untouched).
- Test-evidence requirement → `npm test` collects and exits cleanly with the
  new suite.
- Documentation requirement → the `docs/development/index.md` section matches
  the implemented behavior; human review of the change remains outstanding.

### Additional implementation verification

None planned beyond the above; a third-page (45-post) build would only
repeat chunking logic already exercised at the 20/5 boundary.
