# Blog archive pagination

The blog archive (`/blog/`) currently renders every post on one page and becomes
hard to browse as posts grow. This task paginates the archive while preserving
the rest of the build: home page, tags, feed, sitemap, individual posts, post
order, and zero-JavaScript static output. Planning handoff only — execution has
not been requested or approved.

## Requirements checklist

- [ ] R1: `/blog/` remains the first archive page: same URL, it is page 1 of the
      paginated archive, and no duplicate `/blog/1/` page is generated.
- [ ] R2: Later archive pages are generated for the remaining posts with at most
      20 posts per page, at stable URLs derived deterministically from the page
      number.
- [ ] R3: Each archive page provides accessible previous/next navigation to the
      adjacent archive pages, rendered only when the target page exists (no
      empty nav or dead links on the first or last page).
- [ ] R4: Home page generation is preserved (unchanged template behavior and
      URL; still the three newest posts).
- [ ] R5: Tag page generation is preserved (unchanged template behavior and
      URLs, e.g. `/tags/posts/`).
- [ ] R6: Feed generation is preserved (same URL and format, still lists all
      posts newest-first).
- [ ] R7: Sitemap generation is preserved (same URL and format; whether later
      archive pages are listed follows approved decision D2).
- [ ] R8: Individual post pages and the navigation paths to them (links from
      the home page, archive pages, tag pages, and feed) are preserved; post
      URLs do not change.
- [ ] R9: Post order is preserved: listings keep displaying posts newest-first
      and archive pages hold consecutive slices of the archive's existing
      ordering — pagination must not reorder posts.
- [ ] R10: Build output remains static HTML/XML with zero client-side
      JavaScript.
- [ ] R11: The affected maintained documentation (README.md) is updated in the
      same reviewed change as the behavior (AGENTS.md documentation policy).

## Requirement questions and decisions to confirm

- **Q1 (requirement question): Which posts should page 1 show?** `/blog/` can
  hold either the 20 newest posts (later pages go back in time — recommended:
  preserves today's reading experience, where `/blog/` starts with the newest
  post and scrolls toward older ones) or the 20 oldest posts (plain collection
  order; later pages go forward, and `/blog/` would no longer show recent
  posts). The answer changes which posts appear on `/blog/` and what
  Previous/Next lead to. Recommendation: newest-first pagination. Template
  consequences for both options are in the execution plan.
- **D1 (design decision): URL scheme for later pages.** Recommended
  `/blog/2/`, `/blog/3/`, … (1-based page numbers; posts live under `/posts/`,
  so numeric archive segments cannot collide). Alternative: `/blog/page/2/`.
- **D2 (design decision): sitemap representation of later archive pages.**
  Recommended `pagination.addAllPagesToCollections: true`, so `/blog/2/` … join
  `collections.all` and the sitemap stays a complete inventory of public pages.
  Tag pagination filters `all` out, so tag pages are unaffected. Alternative:
  leave the sitemap listing only `/blog/`.
- **D3 (scope decision): seed the fixture to 25 posts** so pagination is
  observable in the production build (20 + 5 across two pages). This changes
  the output volume of home, feed, and sitemap (more entries) — the preserved
  contracts are behavior/format/URLs, not byte-identical output. Alternative:
  keep 2 posts and verify multi-page behavior through a separate test-only
  Eleventy fixture (weaker evidence for the real production path).

## Supporting details

### Repository facts

- Stack: Eleventy `^3.0.0` (`package.json`); `npm run build` = `eleventy`,
  `npm test` = `node --test tests/*.test.js`; input `content/`, includes
  `_includes/`, output `_site/` (`eleventy.config.js`). `node_modules` is not
  installed yet; `_site/` is gitignored.
- `content/blog.njk` renders `collections.posts` at `/blog/` through the shared
  `_includes/postslist.njk`, which displays `postslist | reverse`.
- In this fixture `collections.posts` is oldest→newest: `content/index.njk`
  keeps the three newest posts with `head(-3)` (`values.slice(-3)`) before the
  shared include reverses them for display, and `content/feed.xml.njk` uses
  `| reverse` for a newest-first feed. Re-confirm against the real build during
  verification rather than trusting this inference.
- Post pages live at `/posts/<slug>/` (`content/posts/first.md`,
  `content/posts/second.md`; directory data in `content/posts/posts.json` sets
  `tags: ["posts"]` and layout `layouts/post.njk`). The post layout has no
  per-post previous/next links today.
- Other consumers of posts: `content/index.njk` (three newest),
  `content/tag-pages.njk` (one page per tag at `/tags/<slug>/`, paginating
  `collections` with `filter: [all, posts]`), `content/feed.xml.njk` (all
  posts), `content/sitemap.xml.njk` (every `collections.all` page).
- `tests/archive-output.test.js` is a stub: a comment saying production-build
  coverage currently checks only that `/blog/index.html` exists. Extending it
  is the intended evidence location.
- Documentation: `README.md` describes the build outputs in one sentence;
  `docs/development/index.md` states "No archive pagination specification
  exists." That statement stays true unless a specification is created (this
  plan creates none).
- `eleventy.config.js` passes through a `public/` directory that does not
  exist; unrelated to this task.

### Eleventy pagination facts (v3)

- Relevant options: `pagination.data`, `pagination.size`, `pagination.alias`,
  `pagination.reverse`, `pagination.addAllPagesToCollections`,
  `pagination.href.previous` / `pagination.href.next`.
- `addAllPagesToCollections` defaults to `false`: only the first pagination
  page joins collections, so without it the sitemap would not list later
  archive pages.
- `pagination.reverse: true` reverses the full data set before chunking (not
  each chunk) — verify against the installed v3 behavior in the build rather
  than assuming.
- The conditional-permalink pattern
  `permalink: /blog/{% if pagination.pageNumber > 0 %}{{ pagination.pageNumber + 1 }}/{% endif %}`
  is the documented way to keep page 1 at the bare URL. The YAML value needs no
  quoting because it does not start with `{`.

### Interpretations (labeled)

- Assumption: "individual-post navigation" in the request refers to the
  existing links and routes to individual post pages. The post layout has no
  per-post prev/next links today, and the request asks to preserve — not add —
  post-level navigation.
- Clarification: "preserve" targets behavior, format, and URLs, not
  byte-identical output. Seeding more posts (D3) legitimately changes output
  volume wherever posts are enumerated.
- Post order: newest-first display is the site-wide listing convention
  (archive, home, feed). The pagination direction (Q1) decides only which slice
  is page 1, not whether order is preserved.

## Execution plan

Status: Draft

Prerequisite: an answer to Q1 and confirmation of D1–D3. Execution waits until
then.

### Approach

Behavior changes concentrate in `content/blog.njk`; `content/posts/` gains
fixture posts (D3), and `tests/archive-output.test.js` plus `README.md` gain
the evidence and documentation for the new behavior.

1. `content/blog.njk` front matter gains pagination over `collections.posts`
   with `size: 20`, alias `pagePosts`, a conditional permalink per D1, and
   `addAllPagesToCollections` per D2. The existing
   `{% set postslist = collections.posts %}` line is removed; the alias
   supplies the per-page slice.
2. Display order depends on Q1:
   - Recommended (newest posts on `/blog/`): `pagination.reverse: true`
     delivers each page's slice newest→oldest. Because the shared include
     renders `postslist | reverse`, bind the display variable once:
     `{% set postslist = pagePosts | reverse %}` — the extra reversal here plus
     the include's reversal yields the slice in newest-first display order.
     Getting this wrong is the most likely defect; tests assert exact order.
   - Alternative (oldest posts on `/blog/`): no `reverse`; the alias binds
     `postslist` directly and the include's `| reverse` keeps newest-first
     display within each page; pages advance oldest→newest.
   Either way, `_includes/postslist.njk` keeps its current output contract for
   `content/index.njk` and `content/tag-pages.njk`.
3. Below the list, render navigation only when a target exists: a
   `<nav aria-label="Blog archive pages">` with previous/next links built from
   `pagination.href.previous` / `pagination.href.next`, `rel="prev"` /
   `rel="next"`, and link text naming the action with an older/newer qualifier
   matching the Q1 direction (e.g. "Next (older posts)"). Arrows must not be
   the only signal.
4. Seed `content/posts/` to 25 posts (D3), dated/tagged like the existing
   posts, so the build produces two archive pages (20 + 5).
5. Extend `tests/archive-output.test.js`: one real production build
   (`npm run build`) per run, then assertions on `_site` output (mapping in
   Requirement verification). Derive the expected page count from the number of
   post markdown files (`ceil(N/20)`) so the test stays valid as content grows
   or shrinks — including back to a single page.
6. Update `README.md` (see Documentation).
7. `npm install`, run `npm test`, iterate until clean; inspect generated
   `_site/blog/` pages for the nav landmark and URL shapes.

### Risks

- Double-reverse confusion between `pagination.reverse` and the shared
  include's `| reverse`; mitigated by explicit order assertions.
- The shared include is consumed by three templates; its contract must not
  change. Home and tag pages are re-verified after any include-adjacent change.
- `addAllPagesToCollections` (D2) is the only lever that puts later archive
  pages into `collections.all`/the sitemap; forgetting it silently shrinks the
  sitemap.
- With ≤ 20 posts the build must degrade to today's single page (no `/blog/2/`,
  no nav). The generic page-count assertion covers the invariant, but after D3
  the fixture no longer exercises that case in the production build; accepted
  as a tradeoff of D3 (the alternative test-only fixture was rejected for
  weaker evidence on the real path).

### Implementation decisions and open questions

- Q1 pagination direction — unanswered, blocks execution; recommendation:
  `pagination.reverse: true` so `/blog/` shows the 20 newest posts and reading
  onward from `/blog/` continues down the existing newest→oldest order.
- D1 URLs: `/blog/{{ pagination.pageNumber + 1 }}/` (recommend); no existing
  URL changes.
- D2 sitemap: `addAllPagesToCollections: true` (recommend) to keep the sitemap
  a complete page inventory.
- D3 fixture growth to 25 posts (recommend): cheapest decisive evidence at the
  real production boundary.
- Resolved locally (reversible, in-plan): alias name `pagePosts`, nav wrapper
  markup, test style (single build plus assertions in the existing test file),
  and no new specification or documentation pages.

### Documentation

- Audience: readers of the package's front documentation (`README.md`).
- Update the existing README sentence to state that the blog archive is
  paginated (20 posts per page) with previous/next navigation — only after the
  behavior exists, in the same reviewed change, keeping claims true.
- No new documentation or specification pages: smallest structure that helps
  the reader; `docs/development/index.md` remains accurate.

### Task checklist

- [ ] 1. `npm install`; run `npm run build` and `npm test` to establish the
      baseline; record today's `/blog/` output shape.
- [ ] 2. Update `content/blog.njk` per the approach (front matter, display
      order per Q1, accessible previous/next navigation).
- [ ] 3. Seed `content/posts/` to 25 posts (D3).
- [ ] 4. Extend `tests/archive-output.test.js` per Requirement verification.
- [ ] 5. Update `README.md` per Documentation.
- [ ] 6. Run `npm test` (real production build plus assertions) until clean;
      spot-check generated `_site/blog/` pages.

### Requirement verification

Evidence boundary: files generated by a real `npm run build` into `_site/`,
asserted from `tests/archive-output.test.js` (integration through the real
Eleventy build; no template copies or mocks).

| Requirement | Evidence |
| --- | --- |
| R1 | `_site/blog/index.html` exists; no `_site/blog/1/` is generated. |
| R2 | Every archive page contains ≤ 20 `/posts/` links; `_site/blog/2/index.html` exists when N > 20 and holds the remaining posts; page count equals `ceil(N/20)` (N = number of post markdown files). |
| R3 | Archive pages with a target page contain a `<nav aria-label="Blog archive pages">` whose prev/next links point to adjacent archive pages and carry `rel` attributes; pages without a target render no nav. Automated checks prove structure only — screen-reader/keyboard confirmation is not planned (residual). |
| R4 | `_site/index.html` lists exactly the three newest posts through the unchanged home template. |
| R5 | `_site/tags/posts/index.html` lists all N posts, newest first. |
| R6 | `_site/feed/feed.xml` lists all N posts, newest first, unchanged format. |
| R7 | `_site/sitemap.xml` unchanged format; lists `/blog/` and — with D2 approved — `/blog/2/` alongside home, tag, and post URLs. |
| R8 | `_site/posts/<slug>/index.html` exists for every post; post URLs unchanged across listings, feed, and sitemap. |
| R9 | Order assertions: archive pages hold consecutive slices in the established order with newest-first display (per Q1 direction); home, tags, and feed keep newest-first order. |
| R10 | No `<script` in any generated HTML. |
| R11 | README diff reviewed in the same change as the behavior. |

### Additional implementation verification

- Rebuild determinism: run the build twice and confirm identical archive file
  sets and URLs, supporting "stable later pages" beyond single-run assertions.