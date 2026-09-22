# Introduce structured multi-author model with legacy read compatibility

First migration state (dual-read): add the structured `authors` post field,
normalize legacy `author` strings into it, move the post layout and feed
templates to read only the new model, and establish real generated-output test
coverage. Existing legacy-form content must keep generating identical output.

Parent Task: tasks/20260920-post-author-migration/000-main.md

## Requirements checklist

- [ ] Posts accept the structured `authors` field (shape per parent Q1); a
      post listing multiple authors renders all authors on the post page and
      in the feed.
- [ ] Post page and feed templates render author data exclusively through the
      new model; legacy `author` strings are normalized so the two existing
      posts render exactly as before the change.
- [ ] Archive, tag page, home, and sitemap generation remain unchanged during
      this subtask (author non-consumers per parent Q2 recommendation; if Q2
      resolves to adding archive display, that display consumes the new model
      and is covered here instead).
- [ ] During this state, both legacy-form and new-form content build
      successfully through the production Eleventy pipeline.
- [ ] Real generated-output coverage exists at the production-build boundary
      covering: legacy-form post rendering, new-form single- and
      multi-author rendering (page + feed), and archive listing.

Do not execute until parent questions Q1 and Q2 are resolved.

## Supporting facts

- Consumers to move: `_includes/layouts/post.njk:2`
  (`<p class="author">{{ author }}</p>`) and `content/feed.xml.njk:5`
  (`<author>{{ post.data.author }}</author>`; simplified Atom-like feed,
  permalink `/feed/feed.xml`).
- Existing content is legacy-form only: `first.md` → `Ada Example`,
  `second.md` → `Grace Example`.
- `tests/author-output.test.js` and `tests/archive-output.test.js` are
  comment-only stubs; there is no executable coverage yet. `npm test` runs
  `node --test tests/*.test.js`.
- Dependencies (`@11ty/eleventy ^3.0.0`) are not installed; `node_modules/`
  and `_site/` are gitignored.
- Archives/tag pages/home share `_includes/postslist.njk` (title + URL only);
  sitemap renders URLs only — no author reads to migrate there, only
  verification that they stay unchanged.

## Execution plan

Status: Draft

Approach:

1. Prerequisites: `npm install`; run `npm test` and record the trivial-green
   baseline.
2. Make both stub test files real before touching templates. Add a small
   shared helper under `tests/` that runs the real Eleventy build into a temp
   output directory (supporting an alternate input dir for fixture content
   later). Coverage:
   - `tests/author-output.test.js`: built `first/index.html` contains
     `<p class="author">Ada Example</p>`; `second/index.html` contains
     `Grace Example`; built `feed/feed.xml` contains `<author>Ada
     Example</author>` and `<author>Grace Example</author>`.
   - `tests/archive-output.test.js`: built `blog/index.html` lists both post
     titles.
   Get this suite green against unchanged legacy content — that is the
   before/after equivalence baseline.
3. Add the model: `authors` front matter is accepted on posts (shape per Q1).
   Add normalization in `content/posts/posts.json` via `eleventyComputed`:
   when the post declares `authors`, use it; otherwise map legacy `author`
   (string) to a one-element list. If the real-build feed test shows computed
   data is not visible on collection items, fall back to a shared filter
   module used by both templates (keep the normalization logic in one place).
4. Move templates: `_includes/layouts/post.njk` renders the author list from
   the new model (single author → exactly `Ada Example`, no separator
   artifacts; multiple authors joined `", "`); `content/feed.xml.njk` loops
   authors and emits one `<author>` element per author.
5. New-form coverage without touching the public site: build a temp copy of
   the content tree with two added fixture posts — one new-form single author
   (must render identically to its legacy-form equivalent) and one new-form
   multi-author post — and assert page and feed output. This exercises the
   real pipeline; no mocks.
6. Verify: full `npm test` green; production build (`npm run build`) green;
   baseline tests still assert the legacy-era exact strings unchanged;
   archive/sitemap outputs unchanged. Record results.

Boundaries: all decisive evidence comes from real Eleventy build output.
Temp-fixture builds never write into the repo `content/` or `_site/`.

### Implementation decisions and open questions

- Open (parent, blocking): Q1 field shape, Q2 archive display scope.
- Local: normalization mechanism (computed data first, filter fallback);
  multi-author page join `", "`; feed emits one `<author>` per author in post
  order; test fixture posts live only in temp copies.

### Documentation

- No maintained documentation describes author metadata, so no documentation
  change is required in this state unless Q2 resolves to archive display (then
  document the archive behavior where archive behavior is documented — none
  currently exists, so README-level notes would apply).
- `docs/development/index.md`'s archive pagination note is unrelated; do not
  touch it.

### Task checklist

- [ ] `npm install`; record baseline `npm test` result.
- [ ] Implement shared build helper + real tests in
      `tests/author-output.test.js` and `tests/archive-output.test.js`; green
      against unchanged content.
- [ ] Add `authors` model with legacy normalization (computed data; filter
      fallback if needed).
- [ ] Move `_includes/layouts/post.njk` and `content/feed.xml.njk` to the new
      model.
- [ ] Add temp-fixture build coverage for new-form single- and multi-author
      posts (page + feed).
- [ ] Full suite + production build green; archive/sitemap unchanged;
      record results and update requirement checkboxes.

### Requirement verification

- New model supported / multi-author rendering → decisive: real-build test
  with multi-author fixture asserting all authors on page + feed.
- Legacy compatibility / no breakage → decisive: baseline tests asserting
  exact strings pass against legacy content before the change and again after
  template migration.
- Templates read only the new model → supporting: source inspection of both
  templates (no `author` reads) plus the passing equivalence suite.
- Archives unchanged → decisive: archive test + unchanged sitemap output via
  build inspection.

### Additional implementation verification

- Feed visibility of normalized data on collection items — resolved by the
  feed test; if it fails, apply the filter fallback and re-verify.
- Confirm temp-fixture builds and tests never modify tracked files.