# Blog archive pagination (Eleventy)

Split the blog archive across build-time pages with at most twenty posts each,
keeping `/blog/` as the first page and adding accessible previous/next
navigation, without regressing any existing page, feed, sitemap, or the
zero-JavaScript static output. Plan only — execution must not start until the
Draft plan below is approved.

## Requirements checklist

- [ ] R1 — `/blog/` remains the first archive page at the same URL; it is not
      replaced by or redirected to `/blog/page-1/`.
- [ ] R2 — The archive is split at build time into pages with at most twenty
      posts each; later pages have stable, deterministic URLs derived from the
      page number under `/blog/`, exist only when they contain posts, and are
      regenerated automatically as the post count grows.
- [ ] R3 — Every multi-page archive has accessible previous/next navigation: a
      nav landmark with an accessible name, visible Previous/Next links to the
      adjacent pages only where those pages exist, and no broken links. A
      single-page archive renders no pagination controls.
- [ ] R4 — All existing behavior is preserved:
  - Home page (`/`) unchanged.
  - Tag pages (`/tags/<tag>/`) unchanged, including their own pagination data.
  - Feed (`/feed/feed.xml`) unchanged: same entries, same order.
  - Sitemap (`/sitemap.xml`) still enumerates every generated page; new
    archive pages appearing in it is an accepted consequence, not a regression.
  - Individual post pages keep their URLs and inbound links; every post is
    linked from exactly one archive page, with no duplicates or gaps across
    archive pages.
  - Post order is preserved: newest-first within the archive listing, and
    page 1 continues to show the most recent posts with later pages continuing
    oldest-ward in strict newest-to-oldest order.
  - Output remains static with zero client-side JavaScript.
- [ ] R5 — The change ships with updated test evidence for the new pagination
      behavior and the preserved surfaces, and with the maintained docs kept
      truthful, all in the same reviewed change.

## Decisions awaiting approval

These are material (public URLs and user-visible output). The Draft plan below
assumes the recommended options; approval of the plan approves these too, or
state corrections and the plan returns to Draft.

1. **Later-page URL scheme.** Recommended: `/blog/page-2/`, `/blog/page-3/`, …
   (page number = `pagination.pageNumber + 1`, first page has no suffix).
   Alternative: `/blog/2/`. Rationale: `page-` reads clearly, avoids ambiguity
   with post URLs, and matches common Eleventy pagination examples.
2. **Current-page orientation in the nav.** Recommended: include a plain text
   `Page X of Y` marker between the links (non-link, announced within the
   landmark). Alternative: links only. Rationale: cheap orientation for
   screen-reader and visual users; small user-visible addition.
3. **No separate specification page.** Recommended: update `README.md` and the
   now-stale line in `docs/development/index.md`; do not add a spec page.
   Alternative: author `docs/development/archive-pagination.md`. The behavior
   is current once implemented, so the smaller structure suffices.

## Research and supporting details

**Fact — current fixture behavior (2 posts, `First` 2026-01-01 and `Second`
2026-01-02):**

- `content/blog.njk` renders the archive at `/blog/` by setting
  `postslist = collections.posts` and including `_includes/postslist.njk`,
  which iterates `postslist | reverse`. Eleventy collections sort
  oldest-first, so the archive shows all posts newest-first.
- `content/index.njk` (home) shows the three newest posts via the `head(-3)`
  filter (`head(-3)` = `slice(-3)`), reusing the same include.
- `content/tag-pages.njk` paginates over `collections` (`size: 1`, alias
  `tag`, filter `[all, posts]`) to build `/tags/<slug>/`; independent of the
  archive.
- `content/feed.xml.njk` loops `collections.posts | reverse` (newest-first)
  over all posts; `content/sitemap.xml.njk` loops `collections.all`.
- `content/posts/posts.json` gives posts the `posts` tag and the
  `layouts/post.njk` layout; post URLs are `/posts/<slug>/`.
- No template or layout contains `<script>`; the zero-JS claim is currently
  true.

**Fact — Eleventy ^3.0.0 pagination supports this change directly:**
`pagination.data: collections.posts` with `size: 20`, `alias`, and
`reverse: true`; `pagination.href.previous` / `pagination.href.next` are
undefined at the boundaries; and v3 documents skipping the first page via the
`permalink: { build: "…" }` conditional form, so page 0 stays at `/blog/`.
Hrefs derive from generated permalinks, which is what keeps later-page URLs
stable. If the `permalink.build` form misbehaves in this fixture, the fallback
is the inline conditional string in front matter
(`permalink: /blog{% if pagination.pageNumber > 0 %}/page-{{ pagination.pageNumber + 1 }}{% endif %}/`);
the executor must confirm the actual emitted URLs by build output either way.

**Fact — page 1 must stay newest-first.** Paginating ascending
`collections.posts` directly would put the oldest posts on `/blog/`, changing
what visitors see first. `pagination.reverse: true` fixes this; then page
slices are newest-to-oldest, and because `_includes/postslist.njk` hard-codes
`| reverse`, `content/blog.njk` must set `postslist = posts | reverse` so the
include still renders newest-first. The include itself must not change (home
and tags depend on its current behavior).

**Fact — sitemap scope grows as a consequence.** Paginated archive pages join
`collections.all`, so `/sitemap.xml` will list `/blog/page-2/` etc.
automatically. This is accepted (see R4); no sitemap template change is
planned.

**Assumption (rationale: no such feature exists today) — "individual-post
navigation" means individual posts stay navigable: their URLs are unchanged
and each remains linked from the archive listing. There is no post-to-post
prev/next UI in this fixture (`_includes/layouts/post.njk` renders title,
author, content only), so there is nothing else to preserve. If the requester
meant adding post-to-post navigation, that is out of scope until approved.**

**Fact — test infrastructure:** `tests/archive-output.test.js` currently
contains only a comment stating that production-build coverage checks that
`/blog/index.html` exists; it defines no tests, so `npm test` passes trivially
today. Existing coverage for preserved behaviors (feed, sitemap, home, tags):
none. `node_modules/` is not installed; `npm install` is a prerequisite.
`npm test` runs `node --test tests/*.test.js`.

**Fact — stability semantics:** "stable later pages" means deterministic,
content-independent URLs (`/blog/page-N/`, N ≥ 2) generated at build time.
Which posts sit on page 2 will shift as new posts are added; that is inherent
to newest-first pagination and acceptable.

**Fact — testing >20 posts requires synthetic content.** The fixture has 2
posts. To prove the twenty-per-page bound and multi-page behavior without
mutating repository content, tests should build a temporary copy of the
project (generated Markdown posts added there), symlink the repo's
`node_modules` into the copy, and run the real production build
(`eleventy` CLI) inside it. The repository's own `content/` and `_site/` stay
untouched; temporary directories are cleaned up even on failure.

## Execution plan

Status: Draft

Approach:

1. **Baseline.** Run `npm install` (first run; `devDependencies` are not
   installed), then `npm run build` and `npm test`. Record the current output
   (single `/blog/index.html` with links `Second`, `First`; feed newest-first;
   sitemap page list) as the comparison baseline for R4.
2. **Paginate the archive** in `content/blog.njk`:

   ```njk
   ---
   pagination:
     data: collections.posts
     size: 20
     alias: posts
     reverse: true
   permalink:
     build: /blog/{% if pagination.pageNumber > 0 %}page-{{ pagination.pageNumber + 1 }}/{% endif %}
   ---
   <h1>Archive</h1>
   {% set postslist = posts | reverse %}
   {% include "postslist.njk" %}
   {% include "archive-pagination.njk" %}
   ```

   Notes: `alias: posts` shadows no global in this template (the tag `posts`
   is unrelated to variable scope); `| reverse` compensates for the include's
   own reverse so each page renders newest-first; `collections.posts` itself
   is untouched.
3. **Add `_includes/archive-pagination.njk`** (new file):

   ```njk
   {% if pagination.pages.length > 1 %}
   <nav class="archive-pagination" aria-label="Blog archive pages">
     {% if pagination.href.previous %}<a href="{{ pagination.href.previous }}" rel="prev">Previous</a>{% endif %}
     <span>Page {{ pagination.pageNumber + 1 }} of {{ pagination.pages.length }}</span>
     {% if pagination.href.next %}<a href="{{ pagination.href.next }}" rel="next">Next</a>{% endif %}
   </nav>
   {% endif %}
   ```

   Accessibility: `<nav>` landmark scoped by `aria-label` so it is
   distinguishable from other navs; links have visible text and only render
   when the target page exists, so no disabled-state theater and no broken
   links; the page marker is plain text, not a link to the current page.
   `rel="prev"/"next"` anchors are low-risk machine hints. The single-page
   gate keeps `/blog/` free of an empty landmark.
4. **Tests** in `tests/archive-output.test.js` (replace the placeholder; keep
   the file name — this is the archive-output capability). Use production
   builds over a temporary project copy with generated posts (see supporting
   details), asserting at the file boundary:
   - 45-post build: `/blog/index.html` with exactly 20 post links (newest 20,
     newest first); `/blog/page-2/` (20 links) and `/blog/page-3/` (5 links)
     exist; no `/blog/page-1/`; page count = ceil(45/20); union of page links
     equals the set of post URLs with no duplicates; prev/next presence is
     next-only / both / prev-only for pages 1/2/3 and every link target
     resolves to a generated file; nav landmark and accessible name present;
     page marker matches `Page N of 3`.
   - 20-post build: single page, no pagination nav at all.
   - 21-post build: exactly two pages.
   - Preserved surfaces (45-post build): home shows the three newest posts;
     `/tags/posts/` lists all posts newest-first; feed contains every post
     newest-first (and equals the pre-change baseline order); sitemap includes
     `/`, `/blog/`, `/blog/page-2/`, `/blog/page-3/`, and every post URL;
     every post URL file exists; no `<script` in any generated `.html`.
   - 2-post (repo) build: unchanged single-page archive.
   Assertions may use simple string/regex parsing of the generated HTML; no
   new runtime dependencies.
5. **Documentation** (see the Documentation section below): one sentence in
   `README.md` and the stale absence line in `docs/development/index.md`.
6. **Finish.** `npm run build && npm test` exit 0; `git status` contains only
   the intended template, include, test, and doc changes.

Boundaries:

- Do not modify `_includes/postslist.njk`, `content/index.njk`,
  `content/tag-pages.njk`, `content/feed.xml.njk`,
  `content/sitemap.xml.njk`, `_includes/layouts/post.njk`, post content, or
  `eleventy.config.js`. Only `content/blog.njk`, the new nav include,
  `tests/archive-output.test.js`, `README.md`, and
  `docs/development/index.md` change.
- Do not add JavaScript, client-side behavior, redirects, or new
  dependencies.
- Do not add a specification page unless approved (decision 3).
- Nothing here authorizes execution before the plan is marked Approved.

Dependencies:

- `npm install` must succeed (network access to install `@11ty/eleventy`
  ^3.0.0); Node version compatible with Eleventy 3.
- Confirm the v3 `permalink.build` conditional form works as documented
  (fallback listed in supporting details) — verify via emitted URLs in the
  first build.

Risks:

- Permalink syntax variant produces `/blog/page-1/` instead of `/blog/` →
  detect immediately in the baseline build of step 4 and apply the fallback.
- Pagination data/alias collision or template-scope mistakes → would show up
  as empty or wrong-order listings in the build assertions.
- Test-generated content accidentally committed → mitigated by building in a
  temp copy only.

### Implementation decisions and open questions

- Decision 1 (URL scheme `/blog/page-N/`), Decision 2 (Page X of Y marker),
  and Decision 3 (no spec page) are listed above and assumed by this Draft.
- Interpretation of "individual-post navigation" is recorded as an assumption
  in supporting details; no post-to-post navigation will be added unless the
  requester asks.
- No open requirement questions remain; all requested surfaces map to R1–R5.

### Documentation

- `README.md`: extend the archive sentence so it stays true, e.g.
  "…a paginated blog archive (first page at `/blog/`, up to twenty posts per
  page, with accessible previous/next links)…". Ship in the same change.
- `docs/development/index.md`: the line "No archive pagination specification
  exists." becomes false once implemented; replace it with a brief statement
  of the implemented pagination contract or a pointer to the code/tests.
- No other maintained documentation exists or is affected; generated output
  needs no source-side changes beyond the templates themselves.

### Task checklist

- [ ] Install dependencies (`npm install`) and record baseline `npm run
      build` / `npm test` results.
- [ ] Convert `content/blog.njk` to the paginated template (R1, R2).
- [ ] Add `_includes/archive-pagination.njk` and include it (R3).
- [ ] Build against 2-, 20-, 21-, and 45-post fixtures to confirm page
      boundaries, URLs, ordering, and nav presence.
- [ ] Replace the placeholder in `tests/archive-output.test.js` with the
      build-output assertions (R5).
- [ ] Update `README.md` and `docs/development/index.md` (R5).
- [ ] Run final `npm run build && npm test`; confirm clean, intended-only
      working tree; update this checklist as items complete.

### Requirement verification

Existing coverage: none (the test file is an empty placeholder), so all
evidence is new. Boundary for all checks: the production build's static
output files — no component-level mocks, since pagination is a build-time
Eleventy behavior.

- R1 + R2 + R3 → 45-post production build in a temp copy: `/blog/` exists with
  ≤20 links; `/blog/page-2/`–`/blog/page-3/` exist with ≤20 links; no
  `/blog/page-1/`; deterministic page-N naming; nav landmark with accessible
  name; prev/next presence pattern per page; all link targets exist. Plus the
  20- and 21-post builds for the exact boundary (single page vs. two pages)
  and the 2-post build (no controls rendered).
- R4 → same builds: home = three newest; `/tags/posts/` unchanged shape;
  feed entry list and order identical to the recorded pre-change baseline;
  sitemap still enumerates all pages (including the new archive pages, per
  the accepted consequence); each post URL file exists; the multiset of
  archive links across pages equals the set of post URLs exactly once each;
  no `<script` anywhere in `_site/**/*.html`.
- R5 → `npm test` exits 0 with the new assertions collected and run (not a
  zero-test pass); README and `docs/development/index.md` diffs present in
  the same change set.

### Additional implementation verification

- Baseline diff of generated `feed.xml`, `sitemap.xml`, `index.html`, and
  `/tags/posts/` between the pre-change build and the post-change 2-post
  build, to prove "unchanged" precisely rather than plausibly.
- Confirm the empty-pagination-edge (exactly 20 posts) emits no
  `archive-pagination` markup, and that no stray `/blog/page-<n>/` exists
  beyond the expected count.