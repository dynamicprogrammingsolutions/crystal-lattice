# Blog archive pagination

Split the blog archive into multiple pages so it stays browsable as post
count grows: `/blog/` remains the first page, later pages are generated
stably with at most twenty posts each, and consecutive pages get accessible
previous/next navigation. All other outputs (home page, tags, feed, sitemap,
individual posts, post order) must be preserved, and the output stays static
with zero client-side JavaScript.

## Requirements checklist

- [ ] R1: `/blog/` remains the first archive page at its existing URL, listing posts newest-first.
- [ ] R2: Later archive pages use stable, deterministic URLs derived from the page number (`/blog/2/`, `/blog/3/`, …). `/blog/` is never duplicated (no `/blog/1/`), and page URLs do not change as post count grows.
- [ ] R3: No archive page contains more than twenty post links; every page except the last is full.
- [ ] R4: Consecutive archive pages are connected by accessible previous/next navigation built from static markup: a `<nav>` landmark with an accessible name, meaningful link text, and `rel="prev"`/`rel="next"` on the anchors. The first page has no previous link, the last page has no next link, and a single-page archive renders no pagination nav at all.
- [ ] R5: Home page preserved: latest three posts, newest first, at `/`.
- [ ] R6: Tag pages preserved: one page per tag listing every post with that tag, newest first.
- [ ] R7: Feed preserved: all posts, newest first, at `/feed/feed.xml`.
- [ ] R8: Sitemap preserved: continues to list all public site URLs, including every generated archive page.
- [ ] R9: Individual-post navigation preserved: individual posts stay at their existing URLs, and the links that lead to them from the archive, home, and tag listings are unchanged. (Interpretation pending — see open question Q1.)
- [ ] R10: Post order preserved: collection ordering is untouched, and the newest-first display convention is maintained everywhere it applies today.
- [ ] R11: Output remains fully static with zero client-side JavaScript.
- [ ] R12: Production-build test coverage updated to prove R1–R11 at the build-output boundary (required by the project testing policy for changed behavior).

## Open questions

- Q1 (requirement question): R9 "individual-post navigation" — see `### Implementation decisions and open questions` (OQ1) in the plan. Recommended reading: preserve the existing links/URLs that navigate to individual posts; adding previous/next links to individual post pages is new scope and needs explicit approval.
- Q2 (material decision): URL scheme for later archive pages — see OQ2 in the plan. Recommended: `/blog/2/`, `/blog/3/`, … Execution assumes this unless changed at approval.

## Supporting details

Facts verified from the current repository (Eleventy 3, ESM; `@11ty/eleventy ^3.0.0`):

- Config (`eleventy.config.js`): input `content`, includes `../_includes`, output `_site`; `addFilter("head", ...)` (last-N via negative count, used only by the home page); passthrough copy of `public` (directory does not exist — harmless).
- `content/blog.njk`: single page, `permalink: /blog/`, renders the entire `collections.posts` via `_includes/postslist.njk`. This is the only archive page today.
- `_includes/postslist.njk` renders `postslist | reverse`: the include owns the newest-first ordering because Eleventy collections are ordered oldest-first (date ascending). Callers: `content/blog.njk` (all posts), `content/tag-pages.njk` (`collections[tag]`), `content/index.njk` (`collections.posts | head(-3)` = newest three).
- `content/tag-pages.njk`: pagination over `collections`, size 1, alias `tag`, filter `[all, posts]`, permalink `/tags/{{ tag | slugify }}/`. Tag pages stay single-page; the request does not ask to paginate them.
- `content/feed.xml.njk`: `/feed/feed.xml`, lists all posts reversed (newest first). `content/sitemap.xml.njk`: lists every URL from `collections.all`.
- `content/posts/posts.json`: layout `layouts/post.njk`, tags `[posts]`. Two posts today: `first` (2026-01-01 → `/posts/first/`), `second` (2026-01-02 → `/posts/second/`). `_includes/layouts/post.njk` has no previous/next post links — post-to-post navigation does not exist today.
- `tests/archive-output.test.js` contains only the stub comment "Production-build coverage currently checks only that /blog/index.html exists." `npm test` runs `node --test tests/*.test.js`; `npm run build` runs `eleventy`. `node_modules/` is not installed in this workspace; `node_modules/` and `_site/` are gitignored.
- Eleventy pagination facts the plan relies on: `pagination.data: "collections.posts"` with `size` chunks the collection; `pagination.reverse: true` reverses the data before chunking, so the newest posts land on the first page and each chunk is newest-first; the current chunk is `pagination.items`; `pagination.pageNumber` is 0-based; `pagination.href.previous`/`pagination.href.next` are falsy when there is no such page; permalinks accept Nunjucks logic. `addAllPagesToCollections` defaults to `false`: only the first pagination page joins collections, so without `addAllPagesToCollections: true` the later archive pages would be missing from `collections.all` and therefore from the sitemap.
- Templates have no shared `<head>` or base layout. `<link rel="prev"/"next">` head hints are therefore not available without introducing a head; accessibility is delivered via the `<nav>` landmark, its accessible name, and `rel` attributes on the anchors. Zero-JS is preserved automatically by any static-markup approach.
- Documentation state: `docs/development/index.md` says "No archive pagination specification exists."; `README.md` describes the build outputs (home, blog archive, tag pages, feed, sitemap, individual posts, zero client-side JavaScript). Per project documentation policy, maintained docs must reflect current behavior in the same change.
- Git tree is clean; creating the task file is the only change made during planning.

## Execution plan

Status: Draft

### Design

One capability: paginated archive pages plus navigation, with ordering moved
out of the shared list include so every caller states its own order.

**Component responsibilities after the change**

- `_includes/postslist.njk` becomes a pure renderer: it outputs `<ol class="postlist">` items in the order given and no longer reverses. Ordering responsibility moves to callers:
  - `content/index.njk`: `{% set postslist = collections.posts | head(-3) | reverse %}` (unchanged display: newest three first).
  - `content/tag-pages.njk`: `{% set postslist = collections[tag] | reverse %}` (unchanged display: newest first).
  - `content/blog.njk`: `{% set postslist = pagination.items %}` — the pagination chunk arrives newest-first because of `pagination.reverse: true`.
- `content/blog.njk` becomes the paginated archive (only place pagination is added):

  ```njk
  ---
  pagination:
    data: collections.posts
    size: 20
    reverse: true
    addAllPagesToCollections: true
  permalink: "/blog{% if pagination.pageNumber > 0 %}/{{ pagination.pageNumber + 1 }}{% endif %}/"
  ---
  <h1>Archive</h1>
  {% set postslist = pagination.items %}
  {% include "postslist.njk" %}
  {% if pagination.href.previous or pagination.href.next %}
  <nav class="pagination" aria-label="Blog archive pages">
  {% if pagination.href.previous %}<a rel="prev" href="{{ pagination.href.previous }}">Newer posts</a>{% endif %}
  {% if pagination.href.next %}<a rel="next" href="{{ pagination.href.next }}">Older posts</a>{% endif %}
  </nav>
  {% endif %}
  ```

- With ≤ 20 posts (today: 2 posts), pagination yields exactly one page and the output is identical to today's `/blog/` (list only, no nav). As posts grow, page 0 keeps the 20 newest posts; each later page holds the next block of 20, newest-first within the page.
- Feed, sitemap, tag pages, home page, post layout, and post content are not modified. The sitemap is fed by `collections.all`, so `addAllPagesToCollections: true` is what keeps it complete once later pages exist.

**Compatibility and dependency states**

- Existing URLs (`/`, `/blog/`, `/posts/*`, `/tags/*`, `/feed/feed.xml`) do not change. New URLs (`/blog/2/` …) appear only when more than twenty posts exist.
- The sitemap gains the later archive URLs automatically through `collections.all`; no sitemap template change is required.
- No new dependencies; no JavaScript introduced; output stays plain HTML files in `_site/`.

**Material decisions (need approval together with the plan)**

- OQ1 (Q1): R9 interpreted as "preserve links/URLs that navigate to individual posts" (all that exists today). Adding previous/next post-to-post links to `_includes/layouts/post.njk` would be new user-visible scope — not planned; requires explicit approval.
- OQ2 (Q2): later-page URL scheme `/blog/2/`, `/blog/3/`, … (human page number; page 1 stays `/blog/`). Alternative considered and rejected: `/blog/page/2/` (longer; no collision risk exists because posts live under `/posts/`). Public URLs are user-visible, so approval covers this scheme.

**Verification strategy**

Two production builds inside temporary copies of the fixture (never the repo tree, keeping the workspace clean; builds use the real Eleventy CLI so the production path is exercised):

1. Multi-post build: fixture copy + 25 synthetic posts (distinct dates/titles; some with an extra tag) built with the real CLI in the temp copy, asserting pagination boundaries, URL scheme, navigation, and all preserved outputs.
2. Fixture-content build: exact fixture content (2 posts) built in a second temp copy, asserting the single-page archive is unchanged (no `/blog/2/`, no nav) and current outputs are intact.

Assertions are listed under `### Requirement verification`. The test harness (temp-copy + real CLI) lives in the existing `tests/archive-output.test.js`; the stub comment is replaced.

### Implementation decisions and open questions

- D1 — Pagination source: `pagination.data: "collections.posts"`, `size: 20` ("at most twenty"), `reverse: true` so the newest posts fill page 1, matching today's newest-first archive. Rejected alternative: without `reverse`, `/blog/` would hold the oldest posts.
- D2 — Permalink uses Nunjucks logic so page 0 renders `/blog/` and page N (0-based ≥ 1) renders `/blog/N+1/`. Guarantees unique permalinks and no `/blog/1/`.
- D3 — Ordering contract: `postslist.njk` renders in given order; callers own ordering (home: `head(-3) | reverse`; tags: `| reverse`; archive: `pagination.items`, newest-first chunk). Without this, the include's `| reverse` would flip each 20-item chunk to oldest-first within the page. Display output is unchanged for home and tags.
- D4 — `addAllPagesToCollections: true` so every archive page enters `collections.all` and the sitemap stays complete (Eleventy default adds only the first pagination page to collections).
- D5 — Navigation markup: `<nav aria-label="Blog archive pages">` wrapping conditional "Newer posts"/"Older posts" anchors with `rel="prev"`/`rel="next"`; the whole nav is suppressed when the archive is a single page. No head-level `<link rel="prev"/"next">` because templates have no `<head>`; introducing one is out of scope.
- D6 — Tests drive the real Eleventy CLI in temporary fixture copies, reusing the root `node_modules` bin after `npm install` (fall back to installing inside the copy if bin reuse fails). No test-only build shortcuts or stub templates.
- OQ1 — Interpretation of "individual-post navigation" (see Q1 above). Execution assumes preserve-only; expansion needs approval.
- OQ2 — URL scheme (see Q2 above). Execution assumes `/blog/2/` style.
- Excluded from scope: paginating tag pages, a "Page X of Y" indicator, `<link rel="prev"/"next">` head elements, feed truncation, and any content changes to posts.

### Documentation

- `docs/development/index.md` (audience: maintainers): replace "No archive pagination specification exists." with a short factual description of the shipped behavior — `/blog/` first page, `/blog/N/` later pages, at most twenty posts each, static prev/next navigation. Smallest structure; no new pages or directories.
- `README.md` (audience: package readers): extend the outputs description with one sentence stating the blog archive paginates in blocks of up to twenty posts. Both doc updates ship in the same change as the behavior, per project documentation policy.

### Task checklist

- [ ] T1: Make `_includes/postslist.njk` a pure renderer; update `content/index.njk` and `content/tag-pages.njk` to order their lists explicitly (newest first). Verify display output for home and tags is unchanged.
- [ ] T2: Convert `content/blog.njk` to the paginated archive per the design snippet (size 20, reverse, addAllPagesToCollections, conditional permalink, accessible prev/next nav).
- [ ] T3: Replace the stub in `tests/archive-output.test.js` with the temp-copy production-build harness and the assertion set mapped in `### Requirement verification`.
- [ ] T4: Update `docs/development/index.md` and `README.md` as described above.
- [ ] T5: Install devDependencies if needed, run `npm test` (and optionally `npm run build` as an in-repo smoke build), and update the requirements checklist with evidence.

### Requirement verification

- R1, R2, R3 — Multi-post build (25 posts): `_site/blog/index.html` exists and lists exactly the twenty newest posts in newest-first order; `_site/blog/2/index.html` exists and lists the remaining five; `_site/blog/3/` and `_site/blog/1/` do not exist.
- R4 — Multi-post build: `/blog/` has `rel="next"` → `/blog/2/` and no `rel="prev"`; `/blog/2/` has `rel="prev"` → `/blog/` and no `rel="next"`; both pages have a `<nav>` with an accessible name and the rel attributes on anchors. Fixture-content build: `/blog/` renders no pagination nav and `/blog/2/` does not exist.
- R5 — Multi-post build: `_site/index.html` contains exactly the three newest posts, newest first.
- R6 — Multi-post build: `/tags/posts/` lists every post with that tag, newest first; `/tags/extra/` lists only the posts carrying the extra tag (tag completeness and filtering unchanged).
- R7 — Multi-post build: `_site/feed/feed.xml` lists all posts (fixture + synthetic), newest first.
- R8 — Multi-post build: `_site/sitemap.xml` contains `/blog/` and every generated later archive page (plus the pre-existing URLs), proving `collections.all` completeness regardless of mechanism.
- R9 — Both builds: `_site/posts/first/index.html` and `_site/posts/second/index.html` exist, and the archive/home/tag listings still link to individual-post URLs.
- R10 — Both builds: ordering assertions above (archive, home, tags, feed all newest-first; individual posts unchanged).
- R11 — Multi-post build: walk `_site` — no `.js` files emitted and no `<script` tags in any output.
- R12 — `node --test tests/*.test.js` collects the file and exits cleanly; the stub comment is gone.

### Additional implementation verification

- Run `npm run build` in the real repo once and inspect `/blog/` output as a smoke test ( `_site/` is gitignored); confirm Eleventy emits no pagination/permalink warnings (e.g., duplicate permalinks).
- Routine quality checks: full `npm test` suite green; no unintended file changes in git status.