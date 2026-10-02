# Blog archive pagination

Split the `/blog/` archive into paginated pages (at most 20 posts per page) with
accessible previous/next links, while preserving every other build output.
Planning only — execution has not been approved and nothing has been implemented.

## Requirements checklist

- [ ] R1 — `/blog/` remains the first archive page: same URL, still the canonical
  start of the archive, with no duplicate first-page URL (e.g. no `/blog/page/1/`).
- [ ] R2 — Later archive pages are generated with stable, deterministic URLs and
  contain at most 20 posts each; the final page may contain fewer, and pages exist
  only when needed (no empty trailing page; no page 2 when there are ≤ 20 posts).
- [ ] R3 — Each archive page provides accessible previous/next navigation: static
  `<a>` links with discernible text inside a labelled navigation region; a previous
  link appears only on pages with a predecessor and a next link only on pages with
  a successor; no dead links at the boundaries.
- [ ] R4 — Home page preserved: same URL, unchanged behavior and listing.
- [ ] R5 — Tag pages preserved: unchanged URLs and behavior (each tag still lists
  all of its posts on one page; tags are not paginated).
- [ ] R6 — Feed preserved: still lists all posts in the current order at the same
  URL.
- [ ] R7 — Sitemap preserved: still lists site pages; the new archive pages appear
  as a natural consequence of it iterating all pages.
- [ ] R8 — Individual-post navigation preserved: archive, home, and tag listings
  still link to every post's individual page; post URLs and post pages are
  unchanged.
- [ ] R9 — Post order preserved: archive display remains newest-first with
  `/blog/` starting from the newest post; later pages continue with older posts in
  sequence; feed, home, and tag ordering unchanged.
- [ ] R10 — Output remains static HTML/XML with zero client-side JavaScript.

## Scope exclusions

- Tag pages and feed are not paginated.
- No previous/next navigation between individual posts is added or removed.
- No page-count indicator ("Page X of Y"), styling, or theme work beyond the
  navigation markup.

## Requirement questions and decisions

- Open material decision (pending plan approval): URL scheme for archive pages
  2+. Recommendation: `/blog/page/2/`, `/blog/page/3/`, … via the standard
  Eleventy conditional-permalink pattern; alternative: `/blog/page-2/`. No other
  requirement depends on which scheme is chosen.
- Interpretation (assumption): "individual-post navigation" means the existing
  links to individual posts from the archive, home, and tag listings. The post
  layout in this fixture has no previous/next post links, so none is added or
  removed. If the intent was to add post-level previous/next links, that is new
  scope and should be raised before execution.

## Supporting facts

Verified from the current source:

- Archive `content/blog.njk`: permalink `/blog/`, renders all of
  `collections.posts` through `_includes/postslist.njk`.
- `_includes/postslist.njk` renders `<ol class="postlist">` linking each
  `post.url`, and reverses its input for display (newest-first).
- `collections.posts` is oldest-first (Eleventy default). Home
  (`content/index.njk`) takes the last 3 via the custom `head` filter; tag pages
  (`content/tag-pages.njk`) render each tag collection; feed
  (`content/feed.xml.njk`) reverses all posts.
- Sitemap (`content/sitemap.xml.njk`) iterates `collections.all`, so generated
  archive pages will appear automatically.
- Post layout `_includes/layouts/post.njk` has no previous/next post links.
- Post permalinks derive from `content/posts/*.md` paths (e.g. `/posts/first/`);
  posts get their layout and `posts` tag from `content/posts/posts.json`.
- Eleventy 3 (`@11ty/eleventy ^3.0.0`); input `content/`, includes
  `../_includes/`, output `_site/`; `npm run build`; `npm test` runs
  `node --test tests/*.test.js`.
- `tests/archive-output.test.js` is a stub (comment only, no assertions), so
  there is no existing coverage to rely on.
- `docs/development/index.md` currently notes "No archive pagination
  specification exists."
- `node_modules/` and `_site/` are gitignored; dependencies are not currently
  installed, so execution must run `npm install` (no lockfile present) before
  building or testing.

## Execution plan

Status: Draft

### Design

- Pagination source: `content/blog.njk` becomes the paginated template with
  `pagination: { data: collections.posts, size: 20, alias: <chunk alias>,
  reverse: true }`. Paginate `collections.posts` only — never `collections.all`
  (the archive pages themselves are in `collections.all`, which would make the
  archive paginate itself). `reverse: true` reverses the data before slicing, so
  page 1 holds the 20 newest posts in newest-first order (matching today's
  `/blog/` display) and later pages continue with older posts in sequence.
- Permalink (recommended scheme, pending approval):
  `permalink: "/blog/{% if pagination.pageNumber > 0 %}page/{{ pagination.pageNumber | plus: 1 }}/{% endif %}"`
  — page 0 renders at `/blog/`, page 1 at `/blog/page/2/`, page 2 at
  `/blog/page/3/`, and so on. Eleventy derives `pagination.href.first/last/
  previous/next/all` from the same rendered permalinks, so navigation hrefs
  always agree with the generated URLs and stay stable across builds.
- Display order within a page: the shared include currently reverses whatever it
  receives, which would flip a newest-first pagination chunk. Recommended: make
  `_includes/postslist.njk` render the posts it receives in the given order, and
  have each caller pass display-ready (newest-first) input — home
  `collections.posts | head(-3) | reverse`, tag pages `collections[tag] |
  reverse`, archive the pagination chunk as-is. Rendered HTML for home and tags
  is identical to today. Alternative (minimal diff): keep the include as-is and
  pass `pagination.items | reverse` from the archive template. Either way, every
  archive page must display its chunk newest-first.
- Navigation: each archive page renders, when applicable, a labelled
  `<nav>` region (e.g. `aria-label="Blog archive pages"`) containing a previous
  link to `pagination.href.previous` and a next link to `pagination.href.next`
  with discernible text (e.g. "Previous page" / "Next page"). Each link is
  guarded by `{% if %}` so the first page has no previous, the last page has no
  next, and a single-page archive renders no nav at all. Pure static HTML — no
  scripts.
- Compatibility states: with ≤ 20 posts, Eleventy generates only `/blog/` and
  the href fields are unset; home, tag, and feed templates are untouched; the
  sitemap picks up the generated archive pages automatically. Page URLs are
  positional, not post-anchored: adding a post shifts trailing posts to the next
  page while all URLs keep their meaning. That is accepted as the natural
  consequence of "stable later pages".

### Tasks

1. Paginate the archive: add pagination front matter and the conditional
   permalink to `content/blog.njk`; render each chunk newest-first; add the
   static previous/next navigation markup (including the include-ordering change
   to `_includes/postslist.njk` and its home/tag callers, or the recorded
   minimal-diff alternative).
2. Tests: replace the `tests/archive-output.test.js` stub with real production
   build coverage (no mocks, no reimplemented pagination logic). Two scenarios:
   - Synthetic overflow case: copy the site (content, includes, config) to a
     temporary directory, generate more than 20 synthetic posts, run a real
     Eleventy build, and assert page contents, order, navigation, and
     regressions (details in Requirement verification).
   - Shipped-content case (2 posts): single `/blog/` page with both posts
     newest-first, no page 2, no previous/next links.
3. Documentation: add the archive pagination spec and update the development
   docs index (see Documentation).
4. Environment: run `npm install` (no lockfile present), then `npm test` and
   `npm run build`.

### Implementation decisions and open questions

1. URL scheme for archive pages 2+ (material — public URLs): recommend
   `/blog/page/2/`, `/blog/page/3/`, …; alternative `/blog/page-2/`. To be
   confirmed or overridden at plan approval; nothing else depends on it.
2. Shared include ordering (internal, output-identical): recommend making
   `_includes/postslist.njk` render caller-provided order with the three call
   sites updated; the minimal-diff alternative re-reverses the chunk in
   `blog.njk`. Either is acceptable; the chosen one is recorded in
   Implementation Notes during execution.
3. Page URLs are positional, not post-anchored; adding posts shifts page
   contents but never the URL scheme. Accepted consequence of the request.
4. Interpretation of "individual-post navigation" (see
   Requirement questions and decisions). Flagged for confirmation at review.

### Documentation

- Add `docs/development/archive-pagination.md` — a concise specification for
  maintainers of this fixture: first-page permalink, later-page URL scheme, page
  size 20, newest-first ordering across pages, previous/next navigation behavior
  and boundary behavior, zero-JavaScript guarantee, and that tags/feed remain
  unpaginated.
- Update `docs/development/index.md` to replace "No archive pagination
  specification exists." with a reference to the new spec.
- `README.md` needs no change: its existing description stays accurate.

### Task checklist

- [ ] Paginated archive template with stable permalinks in `content/blog.njk`.
- [ ] Archive pages render their chunk newest-first (include-ordering decision
      applied to `_includes/postslist.njk` and its callers, or the alternative
      recorded).
- [ ] Accessible previous/next navigation on archive pages, guarded at the
      boundaries, zero JavaScript.
- [ ] Tests extended in `tests/archive-output.test.js`: >20-post synthetic
      production build and shipped-content single-page regression.
- [ ] `docs/development/archive-pagination.md` added and
      `docs/development/index.md` updated.
- [ ] `npm install`, `npm test`, and `npm run build` pass; working tree contains
      only intended changes.

### Requirement verification

All evidence is collected at the generated-output boundary of the real
production build; mocks and reimplementations of the pagination logic prove
nothing and are not used.

- R1, R2, R9 — synthetic >20-post build: `/blog/index.html` exists with exactly
  20 post links starting with the newest post; `/blog/page/2/index.html` exists
  with the remaining posts in sequence; no duplicate first-page URL is
  generated.
- R3 — same synthetic build: page 1 renders a next link to page 2 and no
  previous link; the last page renders a previous link to `/blog/` and no next
  link; links are text-bearing anchors inside a labelled `<nav>`; the
  shipped-content single-page build renders no navigation.
- R4, R5, R6 — build with shipped content: home (`/index.html`), the tag page
  (`/tags/posts/`), and feed (`/feed/feed.xml`) keep their current structure and
  ordering, with no pagination added.
- R7 — generated sitemap includes `/blog/`, each later archive page, the posts,
  tag page, home, and feed.
- R8 — every post page is still generated at its URL and is linked from its
  archive page (and from the home and tag listings).
- R10 — assertion that no `<script` appears in any generated HTML/XML output.

Existing coverage: `tests/archive-output.test.js` contains only a comment and no
assertions; it cannot be cited as evidence and is replaced by the above.

### Additional implementation verification

- Pagination semantics risk: confirm that Eleventy 3 `pagination.reverse`
  combined with the conditional permalink produces exactly the planned URL set
  and ordering — the synthetic-build test already asserts this through the real
  build, which is the decisive check.
- Output-diff risk: after the change, compare the generated files against a
  pre-change build of the shipped content to confirm the only differences are
  the intended archive pagination changes (home, tags, feed, and post pages
  expected byte-identical; sitemap gains the archive page URLs).