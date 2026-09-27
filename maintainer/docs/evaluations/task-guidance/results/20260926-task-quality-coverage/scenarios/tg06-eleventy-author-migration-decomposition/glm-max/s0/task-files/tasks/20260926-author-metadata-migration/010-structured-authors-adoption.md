# Adopt structured multi-author model with legacy compatibility

Introduce the structured multi-author author model (schema per approved Q1 in
the parent task) in the post layout, feed, and authoring tool while the legacy
single-name `author` field continues to work unchanged, and build the
generated-output evidence that the later migration stages depend on.

Parent Task: tasks/20260926-author-metadata-migration/000-main.md

Depends On: none (first stage)

## Requirements checklist

- [ ] Post front matter accepts the approved structured multi-author schema
      alongside the legacy `author` field (dual acceptance on the same post
      data cascade).
- [ ] `_includes/layouts/post.njk` renders authors from the new model; posts
      still using the legacy field render byte-identical to current output
      (`<p class="author">Ada Example</p>` for `content/posts/first.md`).
- [ ] `content/feed.xml.njk` renders authors from the new model; legacy
      posts' feed output is unchanged (`<author>Ada Example</author>`).
- [ ] `scripts/new-post.js` emits the structured model, and its generated
      front matter builds and renders correctly.
- [ ] Blog archive, tag pages, and home page build correctly with posts in
      either form; no author display is added to archives (out of scope).
- [ ] Production-build generated-output tests assert author rendering for
      both legacy and structured posts on post pages and feed, replacing the
      placeholder comments in `tests/author-output.test.js`; the archive
      build check is also real (`tests/archive-output.test.js`).
- [ ] Documentation describes the supported author front matter (dual
      acceptance) as current behavior.

## Supporting facts

- Legacy consumers to keep working while dual acceptance exists:
  `_includes/layouts/post.njk:2` renders `{{ author }}`;
  `content/feed.xml.njk:5` renders `{{ post.data.author }}` per entry.
- `scripts/new-post.js` currently exports `frontMatter(title, author)`
  returning `---\ntitle: ${title}\nauthor: "${author}"\n---\n`. It is a
  standalone authoring tool with no other caller in the repo.
- `content/posts/posts.json` sets `layout: layouts/post.njk` and
  `tags: ["posts"]` for all posts — the natural place for directory-wide
  computed data normalization.
- `tests/author-output.test.js` contains only a comment; no assertions exist.
  `npm test` runs `node --test tests/*.test.js`.
- Current generated output to preserve (verified by reading templates and
  content; will be captured before changes during execution):
  post page `<p class="author">Ada Example</p>`; feed
  `<feed><entry><author>Ada Example</author></entry><entry><author>Grace Example</author></entry></feed>`.
- `node_modules` is absent; run `npm install` before building or testing.

## Execution plan

Status: Draft

Design: normalize author data once, at the data layer, so templates consume a
single form and no template re-implements compatibility.

- Normalization: directory-level computed data on `content/posts/` (via
  `posts.json`, e.g. `eleventyComputed`) derives a normalized `authors` list
  (objects per approved Q1) from either the new `authors` field or the legacy
  `author` field. The exact mechanism is an implementation choice as long as
  it runs in the real build path; templates read only the normalized list.
- Canonical rendering: author names joined with ", " in the existing
  `<p class="author">` element; a single author therefore renders the same
  string as the legacy form did, which keeps output stable for the stage-2
  migration proof. Feed emits one `<author>` element per author, preserving
  the current element shape.
- Authoring tool: `scripts/new-post.js` emits the structured form (signature
  updated to take the structured authors input). Component test covers its
  output; a real build of that front matter is the decisive check.
- Evidence: production-build integration tests (`npm run build`, then
  assertions on `_site` output) cover: legacy posts unchanged on post page
  and feed; a structured multi-author post rendered correctly on post page
  and feed; archive and tag pages building. The multi-author case runs
  through a temporary post in a sandboxed copy of the content/config (no
  permanent content changes, no test-only build shortcuts); harness details
  are an implementation choice.
- Documentation: smallest update describing the supported author front matter
  (both forms during dual acceptance) as current behavior.

Execution tasks:

1. Run `npm install`; capture current `_site` output (build before changes)
   as the equivalence baseline for author rendering.
2. Implement the dual-acceptance normalization in the posts data cascade.
3. Update `_includes/layouts/post.njk` and `content/feed.xml.njk` to the
   normalized model.
4. Update `scripts/new-post.js` to emit the structured form.
5. Add build-output tests (legacy equivalence + structured rendering +
   archive build), replacing placeholder comments.
6. Update documentation to describe dual acceptance as current behavior.
7. Run the production build and the full test suite; resolve fallout.

### Implementation decisions and open questions

- Q1 (parent schema question) must be approved before execution; the
  recommendation is an `authors` list of objects with required `name`.
- Multi-author display: names joined with ", " inside the existing
  `<p class="author">` (recommendation; user-visible — surfaced for approval).
- Feed: one `<author>` element per author, preserving the current element
  shape (recommendation).
- Normalization mechanism: directory computed data in `content/posts/posts.json`
  (recommended); alternatives acceptable if they keep normalization in one
  place in the real build path.

### Documentation

- Audience: content authors. Update the nearest maintained doc (README.md
  today) with a concise authoring/front-matter section describing the
  supported author forms. Follow `docs/development/documentation.md` before
  creating or moving any doc page; do not create placeholder structure. If
  README grows beyond a brief section, move authoring guidance to a dedicated
  doc page in the same change.

### Task checklist

- [ ] Baseline: `npm install`, production build, capture current author output
- [ ] Dual-acceptance normalization in the posts data cascade
- [ ] Post layout and feed templates moved to the normalized model
- [ ] `scripts/new-post.js` emits the structured form
- [ ] Build-output tests: legacy equivalence, structured rendering, archives
- [ ] Documentation updated (dual acceptance)
- [ ] Full build + test run clean

### Requirement verification

- Dual acceptance, legacy equivalence, and structured rendering (parent R1,
  R2, R3): production build plus `node --test` assertions on real `_site`
  files — legacy post pages keep `<p class="author">Ada Example</p>` /
  `Grace Example`, feed keeps one `<author>` element per legacy post, and a
  structured multi-author fixture renders the approved form through the real
  build. A mock of the data cascade would not be decisive; the check is the
  actual Eleventy output.
- Authoring tool: component test of `frontMatter` output plus a real build of
  front matter it generates.
- Archives continue to build: archive-output assertions on `_site/blog/` and
  a tag page.

### Additional implementation verification

- Diff `_site` output before and after this stage against the baseline from
  task 1, confirming no drift beyond author markup for posts that opt into
  the new model.