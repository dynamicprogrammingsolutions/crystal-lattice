# Blog archive pagination

Split the blog archive so `/blog/` stays the first archive page while stable
later pages carry at most twenty posts each, with accessible previous/next
navigation. Preserve the home page, tags, feed, sitemap, individual post
pages, post order, and static zero-JavaScript output. Planning only:
execution has not been approved.

## Requirements checklist

- [ ] 1. `/blog/` remains the first archive page at the same URL and continues
      to show posts newest-first, now limited to at most 20 posts.
- [ ] 2. Later archive pages are statically generated at stable, deterministic
      URLs, each containing at most 20 posts and continuing the same
      newest-first sequence. Stable means deterministic chunking from an
      explicit total order (date descending, deterministic tiebreak for equal
      dates): identical inputs produce identical pages.
- [ ] 3. Every archive page offers accessible previous/next navigation to the
      adjacent archive pages: a labeled `<nav>` with descriptive links, a link
      rendered only where an adjacent page exists, keyboard operable by
      default, no JavaScript.
- [ ] 4. Home page, tag pages, feed, and individual post pages keep their
      current URLs and output.
- [ ] 5. The sitemap remains valid and continues to enumerate the built public
      pages, including the generated archive pages.
- [ ] 6. Build output remains static files with zero client-side JavaScript.
- [ ] 7. Maintained documentation (README plus the development docs) reflects
      the paginated archive in the same change.

## Open questions

- Q1 (user-visible URLs, requirement-relevant): scheme for the later archive
  pages. Recommendation: one-based numbering, `/blog/2/`, `/blog/3/`, … via
  the documented conditional permalink. Eleventy's default pagination URLs
  would place the second page at `/blog/1/` (0-indexed), which reads as page
  "1" while being the second page. The choice changes shipped URLs and needs
  approval before implementation.
- Q2 (sitemap scope, clarification): generated archive pages will appear in
  the sitemap automatically because `content/sitemap.xml.njk` enumerates
  `collections.all`. Recommendation: keep that behavior (they are public
  indexable pages). Excluding them would require an extra filter and is not
  planned unless requested.

## Supporting details

- Eleventy ^3.0.0 (`package.json`); `eleventy.config.js` sets input
  `content/`, includes `../_includes`, output `_site/`; `npm run build` runs
  `eleventy`; `npm test` runs `node --test tests/*.test.js`. Dependencies are
  not installed in this workspace (`node_modules/` absent, gitignored).
- Current archive: `content/blog.njk` has `permalink: /blog/` and renders all
  of `collections.posts` through `_includes/postslist.njk`, which renders
  `postslist | reverse` (newest-first display; collections are
  date-ascending).
- Content: two posts (`content/posts/first.md` dated 2026-01-01, `second.md`
  dated 2026-01-02) tagged `posts` via `content/posts/posts.json`, layout
  `_includes/layouts/post.njk` (no per-post prev/next links exist today, so
  "individual-post navigation" means their current rendering stays as is).
  Post URLs are `/posts/first/`, `/posts/second/`, so `/blog/<n>/` cannot
  collide with post URLs.
- Other surfaces: `content/index.njk` shows the 3 newest posts (`head(-3)`);
  `content/tag-pages.njk` paginates over `collections` with
  `filter: [all, posts]`; `content/feed.xml.njk` lists all posts;
  `content/sitemap.xml.njk` enumerates `collections.all`.
- `tests/archive-output.test.js` contains only a comment ("Production-build
  coverage currently checks only that /blog/index.html exists.") — there are
  no actual assertions today, so real coverage must be written, not extended
  in place.
- `docs/development/index.md` states "No archive pagination specification
  exists."; there is no `docs/index.md`.
- Verified against the Eleventy 3 docs (11ty.dev/docs/pagination):
  - `pagination.reverse: true` reverses the whole data set before chunking, so
    page 1 holds the newest items of a date-ascending collection.
  - Default pagination URLs append a 0-indexed number for later pages
    (`_site/paged/index.html` and `_site/paged/1/index.html` in the docs
    example); a conditional permalink
    (`{% if pagination.pageNumber > 0 %}…{% endif %}`) keeps page 1 at its
    original URL while numbering later pages; in Nunjucks
    `{{ pagination.pageNumber + 1 }}` works (the Liquid caveat does not
    apply).
  - `pagination.href.previous` / `pagination.href.next` give adjacent page
    URLs (absent when there is no adjacent page); `pagination.items` is the
    current chunk (an array when size > 1); `pagination.pages` lists all
    chunks in order.

## Execution plan

Status: Draft

Approach:

1. Install dependencies (`npm install`) and confirm the production build
   succeeds on the unchanged site.
2. Convert `content/blog.njk` into a pagination template: pagination over the
   posts collection, `size: 20`, an alias for the current chunk (not `page`,
   which is reserved), and a conditional permalink so page 1 keeps `/blog/`
   and later pages become `/blog/2/`, `/blog/3/`, … (Q1).
3. Ordering (D2): paginate over an explicitly sorted copied collection added
   in `eleventy.config.js` via `addCollection` — posts sorted date
   descending with `inputPath` as the tiebreak for equal dates, paginated
   with `reverse: false`. Page 1 then holds the 20 newest posts and page
   boundaries are deterministic even for same-date posts. Alternative with
   confirmed semantics: `pagination.reverse: true` directly over
   `collections.posts`, accepting the default tiebreak; acceptable only if
   the same-date determinism test passes.
4. Keep `_includes/postslist.njk` unchanged (shared with home and tag pages).
   Because the include renders `postslist | reverse`, the archive sets
   `postslist` to the current chunk pre-reversed so the display stays
   newest-first; add a comment explaining the paired reversals and confirm
   the order from build output rather than reasoning alone.
5. Add the navigation to `content/blog.njk` after the post list: a
   `<nav aria-label="…">` containing "Newer posts" / "Older posts" links
   bound to `pagination.href.previous` / `pagination.href.next`, each
   rendered only when the href exists (no dead links), plus a "Page X of Y"
   indicator (D3). No scripts.
6. Change nothing else: `content/index.njk`, `content/tag-pages.njk`,
   `content/feed.xml.njk`, `content/sitemap.xml.njk`,
   `_includes/postslist.njk`, `_includes/layouts/post.njk`, and
   `content/posts/*` stay untouched. The new archive pages flow into
   `collections.all` — and therefore the sitemap — automatically.
7. Write the verification below, update README and the development docs in
   the same change, then keep this task file current while executing.

Boundaries:

- Only the blog archive pagination and its navigation; tag pagination, feed,
  sitemap and post templates, and post content are out of scope.
- No client-side JavaScript; no new build tooling beyond the config change
  needed for ordering.

### Implementation decisions and open questions

- D1 (Q1, needs approval): later-page URL scheme — recommendation
  `/blog/{N}/` one-based (`/blog/2/` is the second page), implemented with
  the documented conditional permalink. Tradeoff: the Eleventy default needs
  no permalink logic but numbers pages 0-indexed (`/blog/1/` second);
  `/blog/page-2/` is equally valid if preferred. No other URL conflicts
  exist in this site.
- D2 (local, reversible): ordering mechanism — explicit derived collection
  (recommended, pins the same-date tiebreak) vs `pagination.reverse: true`
  over the default collection. Both put the newest posts on page 1.
- D3 (local, reversible): "Page X of Y" indicator — recommended, because
  landing on `/blog/3/` with only prev/next links gives little orientation;
  executor may include or omit without changing requirements.
- D4 (local, reversible): navigation labels — "Newer posts" / "Older posts"
  recommended; more meaningful than "Previous"/"Next" without page context.
- Pending resolution of Q1/Q2 the plan stays in `Draft`; implementation
  waits for approval.

### Documentation

- `README.md`: extend the existing build-output sentence with the paginated
  archive (at most 20 posts per page, previous/next links, no JavaScript) so
  the public claim ships in the same change as the behavior.
- `docs/development`: replace the "No archive pagination specification
  exists." line in `docs/development/index.md` with a short specification of
  the archive pagination contract (page size, URL scheme, ordering,
  navigation markup, zero-JS). Recommendation: a small dedicated page (e.g.
  `docs/development/archive-pagination.md`) linked from the index; inlining
  it in the index is acceptable if fewer files are preferred. Audience:
  maintainers. Describes shipped behavior only.

### Task checklist

- [ ] Install dependencies and verify `npm run build` succeeds on the
      unchanged site.
- [ ] Resolve Q1 (later-page URL scheme) and D2 (ordering mechanism).
- [ ] Implement pagination in `content/blog.njk` (plus the derived collection
      in `eleventy.config.js` if D2 resolves that way).
- [ ] Implement the accessible previous/next navigation markup.
- [ ] Build and inspect `_site/` output (archive pages, sitemap, feed) as a
      sanity check.
- [ ] Replace the placeholder in `tests/archive-output.test.js` with the
      integration coverage described under Requirement verification.
- [ ] Update `README.md` and the development docs in the same change.
- [ ] Record requirement evidence and progress here (Implementation Notes
      while executing; Completion Notes at the end).

### Requirement verification

- R1, R2 (archive pages, order, size, stability): integration test at the
  real build boundary — run the same production build command against a
  temporary copy of the site seeded with generated posts (distinct dates,
  plus same-date posts to pin the tiebreak), then assert on emitted files:
  `/blog/index.html` holds the 20 newest posts newest-first; later pages at
  the approved URLs hold the next chunks in order, each ≤ 20 posts; two
  builds of identical input emit byte-identical archive pages. Also assert
  the production two-post content still builds to a single `/blog/` page
  holding both posts with no navigation (feature dormant at current size).
- R3 (navigation): assertions on the emitted archive HTML: labeled `<nav>`;
  "Newer posts"/"Older posts" links with correct hrefs; a link exists only
  where an adjacent page exists (page 1 lacks "Newer posts", last page lacks
  "Older posts"); no `<script>` elements. Structural accessibility of real
  links is the evidence boundary; no screen-reader audit is planned.
- R4 (preserved surfaces): build before and after the change from identical
  input (temp site copies) and byte-compare the emitted home, tag, feed, and
  post files; alternatively pin their content with explicit assertions.
  Byte-identical output is the strongest evidence and cheap here.
- R5 (sitemap): assert the emitted sitemap contains every archive page URL
  and still contains all other public URLs.
- R6 (zero-JS): scan all emitted HTML for `<script` (and inline event
  handler attributes if cheap); expect none.
- R7 (documentation): reviewed during execution; final confirmation is the
  reviewer's read of the shipped docs.

### Additional implementation verification

- Pagination edge sizes in the test data: exactly 20 posts (single page, no
  navigation) and 21 posts (two pages; second page holds one post).
- Run the full `npm test` suite and confirm it collects the new tests and
  exits cleanly.