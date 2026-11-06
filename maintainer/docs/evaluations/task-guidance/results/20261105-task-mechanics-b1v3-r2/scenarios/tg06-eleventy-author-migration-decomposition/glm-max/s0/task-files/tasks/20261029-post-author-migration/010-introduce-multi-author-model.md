# Introduce structured multi-author model (dual acceptance)

First increment of the author migration: add the structured multi-author front
matter form and move every author-aware surface (post layout, feed, authoring
tool) onto a shared normalized model, while legacy single-name posts continue
to render exactly as today. No existing content is changed in this subtask.

Parent Task: tasks/20261029-post-author-migration/000-main.md

Depends On: none

## Requirements checklist

- [ ] Posts can declare authors in the structured form (shape per approved D1),
      and the production build renders single- and multi-author posts on post
      pages and in the feed per approved D2.
- [ ] The post layout template and feed template render from the shared
      normalized authors model; neither reads the legacy `author` field
      directly (D4 precedence applies inside the normalization point).
- [ ] `scripts/new-post.js` emits the structured form.
- [ ] Legacy single-name posts still render byte-identically: a production
      build at this state produces the same author output on post pages and
      feed as before this change, and home, archive, tag, and sitemap output
      are unchanged.
- [ ] Automated evidence: integration tests run the real Eleventy build —
      repository content, plus a temp fixture site carrying both forms
      including a multi-author post — and assert rendered post-page and feed
      output; unit tests cover the normalization point and `frontMatter`.
- [ ] README documents the structured form and states that the legacy form is
      still accepted during migration.

## Supporting details

- Legacy usage inventory and build facts live in the parent task
  (`## Supporting facts`).
- Mechanism sketch (implementer may adjust): a shared module (suggested
  `lib/authors.js`, outside the Eleventy input dir) exports a normalizer
  mapping front matter to an authors list — `authors` (list of strings) wins;
  a legacy `author` string becomes a one-element list (D4). Expose it to
  templates via Eleventy computed data on the posts collection (suggested:
  `content/posts/posts.11tydata.js` using `eleventyComputed`); templates then
  render only from the normalized list.
- The feed currently renders one `<author>` per entry; multi-author renders
  one `<author>` element per author in front matter order (D2).
- Integration tests should drive the real Eleventy build (Node API) with
  distinct output directories for repo content and temp fixture sites, so the
  production path is exercised without mutating repository content.
- Temporary legacy-acceptance coverage added here is replaced in 030; the
  repo-content pins (current author strings) stay valid across all phases.
- `node_modules` is not installed; run `npm install` before building/testing.

## Execution plan

Status: Draft

Capture the output baseline before touching anything: build at the current
state and hash every file under `_site/` into a temp directory. Then implement
the model, templates, and tooling; rebuild and require a byte-identical
comparison. Add the two test layers (unit for the model and generator,
integration through the real build for rendering), and update the README in
the same change.

### Implementation decisions and open questions

- Resolved (local): `scripts/new-post.js` signature changes to accept the
  authors list — no in-repo callers, fixture scale; no compatibility shim.
- Resolved (local): normalization module location and Eleventy wiring are the
  implementer's choice; the requirement is one shared normalization point
  consumed by all surfaces, not per-template duplication.
- Pending approval (material — parent D1–D4): data shape, multi-author
  rendering, archives boundary, both-forms precedence. Do not implement until
  the parent plan is approved.

### Documentation

- Add a short "Post authors" section to `README.md` (content-author audience):
  the structured form plus a visible note that the legacy single-name form is
  still accepted during migration.
- Read `docs/development/documentation.md` before adding the section, per root
  `AGENTS.md`. Smallest change that serves the audience; no new doc structure.

### Task checklist

- [ ] Capture baseline: production build at current state, hash every
      generated file into a temp (gitignored) location.
- [ ] Add shared authors normalization module; wire it into the Eleventy data
      cascade for posts.
- [ ] Update `_includes/layouts/post.njk` and `content/feed.xml.njk` to render
      from the normalized authors list.
- [ ] Update `scripts/new-post.js` to emit the structured form.
- [ ] Unit tests: normalization (new form, legacy form, both-forms precedence)
      and `frontMatter` output.
- [ ] Integration tests: real build of repo content pins current author output
      (post pages + feed); real build of a temp fixture site with both forms
      incl. a multi-author post asserts post-page and feed rendering.
- [ ] README "Post authors" section (dual-acceptance wording).
- [ ] `npm install`; rebuild; require the full-output comparison to be
      byte-identical to baseline; `npm test` collects all tests and exits
      cleanly; record results in `## Implementation Notes`.

### Requirement verification

- Structured form end-to-end (R1): integration test through the real Eleventy
  build on the temp fixture site — multi-author post renders joined names on
  the post page and one `<author>` per author in the feed. Real build, real
  templates; no mocked renderer.
- Single normalization point (R2): unit tests on the normalization module plus
  a recorded review that templates and tooling reference only the normalized
  model (no direct legacy-field reads).
- Legacy unchanged (R3): integration test pinning repo-content build output
  (`Ada Example` / `Grace Example` on post pages and feed) plus the recorded
  before/after full-output comparison of every generated file.
- Tooling emits the new form (R2): `frontMatter` unit test.
- Documentation (R6): README section present in the same change.

### Additional implementation verification

- Confirm archive, tag, home, and sitemap files appear unchanged in the
  before/after comparison — this is the concrete check that computed-data
  wiring did not disturb pagination or collections.
