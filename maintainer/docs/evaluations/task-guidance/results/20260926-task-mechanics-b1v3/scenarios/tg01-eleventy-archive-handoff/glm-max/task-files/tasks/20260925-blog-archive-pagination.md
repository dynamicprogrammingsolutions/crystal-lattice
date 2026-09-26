# Blog archive pagination

Split the blog archive into stable static pages of at most twenty posts with
accessible previous/next navigation, preserving all existing site behavior and
the zero-JavaScript static output. Planning only — implementation is not
authorized yet.

## Requirements checklist

- [ ] R1 `/blog/` remains the first archive page at the same URL.
- [ ] R2 When more than twenty posts exist, later archive pages are generated
      as static pages with stable page-number-based URLs (exact scheme pending
      decision D1); no archive pages exist beyond what the post count requires.
- [ ] R3 Every archive page contains at most twenty posts.
- [ ] R4 Archive pages provide accessible previous/next navigation: a labeled
      `<nav>` landmark with previous/next links, omitting the absent direction
      on the first and last pages.
- [ ] R5 Home page behavior is preserved (three newest posts, newest first).
- [ ] R6 Tag page behavior is preserved (archive pages must not appear in or
      alter tag pages).
- [ ] R7 Feed output is preserved (all posts, newest first).
- [ ] R8 Sitemap behavior is preserved and lists the new archive pages.
- [ ] R9 Individual post pages and their URLs are unchanged.
- [ ] R10 Post order semantics are preserved: newest-first within every archive
      page, and pages continue newest-to-oldest across page boundaries.
- [ ] R11 Output remains static HTML with zero client-side JavaScript.
- [ ] R12 Tests provide build-level evidence for R1–R11 (per AGENTS.md testing
      guidance).
- [ ] R13 README documents the paginated archive in the same reviewed change
      (per AGENTS.md documentation guidance).

## Scope

In scope: pagination of the blog archive (`content/blog.njk`), accessible
prev/next navigation, tests, README update.

Out of scope: tag page pagination, per-post previous/next links, adding an
HTML `<head>`/`<title>` to templates, styling beyond minimal markup, changes to
feed/sitemap/home/tag templates.

## Open questions and decisions

- D1 (material, user-visible): URL scheme for later archive pages.
  Recommendation: `/blog/page/2/`, `/blog/page/3/`, … (clearly navigational,
  conventional). Alternative: `/blog/2/` (matches upstream Eleventy Base Blog
  style). Both are static and page-number-based (stable). Awaiting approval.
- D2 (material, minor): include a visible "Page X of Y" indicator inside the
  nav. Recommendation: yes, for orientation. Awaiting approval.

No unresolved requirement-level questions otherwise; the request fully
determines the outcomes above.

## Supporting facts

- Facts below were read from the current workspace (fixture adapted from
  Eleventy Base Blog at `26b26106d7fbb30b7b40d9ef52589d10ddbcb462`).
- `content/blog.njk` has `permalink: /blog/` and renders `collections.posts`
  through `_includes/postslist.njk`, which loops `postslist | reverse`.
  Eleventy sorts collections ascending by date, so the archive currently
  displays all posts newest-first on one page.
- `content/index.njk` shows `collections.posts | head(-3)` — the three newest —
  through the same include.
- `content/posts/posts.json` tags every post `posts`; `first.md` (2026-01-01)
  and `second.md` (2026-01-02) carry no other tags, so no tag pages are
  generated today (`tag-pages.njk` filters out `all` and `posts`).
- `content/feed.xml.njk` lists `collections.posts | reverse`;
  `content/sitemap.xml.njk` lists every `collections.all` URL. Archive pages
  2+ will only reach the sitemap if the pagination sets
  `pagination.addAllPagesToCollections: true`; without it only the first
  pagination page joins collections.
- Blog pages carry no tags, so paginated archive pages join only
  `collections.all` — they cannot contaminate `collections.posts` (feed/home)
  or tag pages, as long as no tags are added to `blog.njk`.
- Templates emit HTML fragments (no `<head>`), so accessible navigation is a
  visible `<nav aria-label="...">` with `rel="prev"`/`rel="next"` anchors; a
  `<link rel>` head element approach is not applicable.
- `tests/archive-output.test.js` currently contains only a comment and no
  assertions; it must be replaced with real coverage.
- `node_modules` is not installed in this workspace; the executor must run
  `npm install` (`@11ty/eleventy ^3.0.0`) before build/test verification.
- Eleventy pagination (v2/v3) supports `size`, `reverse` (reverses the data set
  before chunking), `addAllPagesToCollections`, template syntax in `permalink`,
  and exposes `pagination.pageNumber` (0-indexed), `pagination.hrefs`,
  `pagination.href.next`, `pagination.href.previous` for navigation targets.
  Build tests will confirm the installed version behaves as assumed.

## Execution plan

Status: Draft

### Design

`content/blog.njk` becomes the pagination template while keeping `/blog/` as
page one:

```njk
---
pagination:
  data: collections.posts
  size: 20
  reverse: true
  addAllPagesToCollections: true
permalink: /blog/{% if pagination.pageNumber > 0 %}page/{{ pagination.pageNumber + 1 }}/{% endif %}
---
<h1>Archive</h1>
{% set postslist = pagination.items | reverse %}
{% include "postslist.njk" %}
{%- if pagination.hrefs.length > 1 %}
<nav class="archive-pagination" aria-label="Blog archive pages">
  {%- if pagination.href.previous %}
  <a rel="prev" href="{{ pagination.href.previous }}">Previous</a>
  {%- endif %}
  <span>Page {{ pagination.pageNumber + 1 }} of {{ pagination.hrefs.length }}</span>
  {%- if pagination.href.next %}
  <a rel="next" href="{{ pagination.href.next }}">Next</a>
  {%- endif %}
</nav>
{%- endif %}
```

Why each choice:

- `reverse: true` reverses `collections.posts` (ascending, oldest first) into
  newest-first *before* chunking, so page 1 at `/blog/` holds the twenty
  newest posts and each later page continues toward older posts — preserving
  the current single-page ordering semantics across page boundaries. Page
  URLs depend only on the page number, so they are stable as posts are added
  (content shifts between pages, URLs do not change meaning).
- `pagination.items | reverse` feeds the chunk to the shared include in
  ascending order so the include's existing `| reverse` displays each page
  newest-first; the shared include stays unchanged for home and tag pages.
- `addAllPagesToCollections: true` keeps the sitemap complete (all archive
  pages appear). Blog pages stay untagged, so tag pages and the feed are
  structurally unaffected.
- The nav renders only when there is more than one page; guards on
  `pagination.href.previous` / `pagination.href.next` naturally omit the
  absent direction on the first/last pages. Anchors are plain links — no
  JavaScript, keyboard reachable, with a labeled landmark and `rel` hints.
  If the installed Eleventy version lacks any assumed pagination field, the
  booleans `pagination.page.first`/`pagination.page.last` are the documented
  fallback for the guards; tests will catch any mismatch.

### Implementation decisions and open questions

- D1 (open, material): later-page URL scheme — recommendation
  `/blog/page/N/`; alternative `/blog/N/` (upstream base blog style). User
  decided when plan is approved.
- D2 (open, material, minor): "Page X of Y" indicator — recommendation
  include. User decided when plan is approved.
- Resolved local choices (reversible, no approval needed): nav placed after
  the list inside `blog.njk`; link text "Previous"/"Next"; `aria-label`
  "Blog archive pages"; keep `<h1>Archive</h1>` on every page; no changes to
  the shared include.

### Documentation

Update `README.md` in the same change: one sentence stating the blog archive
is paginated from `/blog/` with at most twenty posts per page and
previous/next links, still with zero client-side JavaScript. Audience: anyone
reading the package README. No new documentation files or directories; the
"smallest structure" rule applies. `docs/development/index.md` stays unchanged
("No archive pagination specification exists." remains true — this is
implemented behavior documented in the README, not a spec).

### Task checklist

- [ ] 1. Add pagination frontmatter and chunk wiring to `content/blog.njk`
      (per design; scheme per approved D1).
- [ ] 2. Add the accessible prev/next `<nav>` markup to `content/blog.njk`
      (per design; indicator per approved D2).
- [ ] 3. Replace `tests/archive-output.test.js` with integration coverage:
      a temp-dir test harness that runs the real Eleventy build over the
      production templates (`content/*.njk`, real `_includes`) with a
      generated fixture of 45 posts (dated/titled incrementally, one post
      carrying an extra tag to exercise a tag page), plus a real-content
      (2 posts) case; assertions per the requirement verification below,
      including a no-`<script` check over generated HTML.
- [ ] 4. `npm install` (workspace currently has no `node_modules`), then
      `npm test` (all tests collect and exit cleanly) and an `npm run build`
      smoke check on the real content.
- [ ] 5. Update `README.md` (per Documentation section).
- [ ] 6. Update this task file: requirement evidence, implementation notes,
      completion notes.

### Requirement verification

Evidence boundary: files written by the real production build pipeline
(production templates + real `_includes`, executed by Eleventy) — no mocked
rendering. `npm test` collects cleanly; each run counts only when it exits 0.

- R1, R2, R3, R10 → 45-post build: `_site/blog/index.html` exists; page 1
  lists 20 `<li>` items, newest 20 posts newest-first; `/blog/page/2/index.html`
  and `/blog/page/3/index.html` exist with 20 and 5 items; concatenated page
  order equals the full post set newest-first; a follow-up build with one more
  post still uses the `/blog/page/N/` scheme (URL stability).
- R4: parse each archive page: page 1 has next link to `/blog/page/2/` and no
  previous; page 2 has both; page 3 has previous only; `<nav>` carries
  `aria-label`; `rel="prev"`/`rel="next"` present; every nav href resolves to
  a generated file.
- R5: `_site/index.html` lists exactly the three newest posts, newest first.
- R6: tag page for the extra tag lists exactly its tagged posts and no archive
  pages; no tag page exists for `posts`/`all`.
- R7: `_site/feed/feed.xml` contains every post URL, newest first.
- R8: `_site/sitemap.xml` contains `/blog/`, every `/blog/page/N/`, and every
  post URL.
- R9: `_site/posts/first/index.html` and `second` exist with unchanged content.
- R11: no `<script` occurrence in any generated HTML file.
- R12: existence and green run of the suite above.
- R13: README sentence reviewed in the same change as the code.
- Real-content case (2 posts): `/blog/` exists as a single page with no
  pagination nav (≤20 posts ⇒ one page; guards the small-content edge).

### Additional implementation verification

- Manual `npm run build` on real content and spot-check `_site/blog/` output
  (fragment structure, nav absent with 2 posts) — distinct risk: production
  build health beyond the test fixture.
- Watch for the pagination edge where an empty `collections.posts` would
  generate no pages; real content always has posts, so it is out of scope, but
  note the behavior if observed during verification.

## Risks

- Offline/broken `npm install` would block build and tests; report as blocked
  rather than substituting mocked evidence.
- Assumed pagination fields (`hrefs`, `href.previous/next`) or
  Nunjucks-in-`permalink` behavior could differ in the installed version;
  tests provide the decisive check and a documented fallback exists.
- Sitemap will grow to include archive pages 2+ — expected consequence of the
  preserved "list all pages" behavior, called out so it is not mistaken for a
  regression.

## Completion Notes

(to be added after execution)