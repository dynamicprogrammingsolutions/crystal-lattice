# Structured multi-author migration

Migrate post author metadata from the legacy single-name `author` front-matter
field to a structured multi-author model across templates, feed, archives, and
authoring tooling; migrate the existing posts; and retire the legacy form only
once content and generated-output evidence show nothing still depends on it.
Planning only — no execution has been approved.

## Requirements checklist

- [ ] A structured multi-author model is the single canonical form of post
  author data, and every consumer — post layout, feed, authoring tooling —
  reads and emits only that model. (Owner: 010)
- [ ] All generated surfaces (post pages, home, archive, tag pages, feed,
  sitemap) build and render correctly under the new model, and with the
  current content their generated output is identical to the pre-migration
  baseline. (Owner: 010)
- [ ] During the transition, a post carrying only the legacy single-name
  `author` field builds and renders identically to its structured equivalent.
  (Owner: 010)
- [ ] Both existing posts are migrated to the structured model with no author
  information lost. (Owner: 010)
- [ ] Generated-output regression coverage for author rendering — single- and
  multi-author, post pages and feed — exists under `tests/` and passes
  through the production build path. (Owner: 010)
- [ ] Maintained documentation matches the supported author model at each
  phase: the structured form documented when adopted, and the legacy form no
  longer presented as supported once rejected. (Owners: 010, 020)
- [ ] The legacy `author` form is rejected only after current content evidence
  and generated-output evidence show that nothing still depends on it, and
  after rejection the migrated site still builds with output identical to the
  baseline. (Owner: 020)

## Questions and decisions

- Pending (material — persisted content data): the shape of the structured
  form. Recommendation: `authors` as a YAML list of entries with required
  `name` and optional `url`, in block style:

  ```yaml
  authors:
    - name: "Ada Example"
  ```

  A plain list of strings would give multi-author support but not structure.
  Must be confirmed before execution starts.
- Pending (material — user-visible build behavior): what rejection means for
  content that still supplies the legacy form. Recommendation: active
  rejection — the production build fails with an error naming the offending
  file; silently ignoring the field would let content regress unnoticed.
  This decides subtask 020's mechanism; confirm before approving 020.
- Planning interpretation: "templates, archives, feeds, and authoring tools
  move to the new model" means every surface that consumes author data reads
  the new model. Archives, home, tag pages, and sitemap currently render no
  author data at all, so their obligation is to keep working unchanged, not to
  gain author display. Author display in archives would be new scope beyond
  this request.

## Subtasks

- [ ] `tasks/20261102-multi-author-migration/010-structured-author-adoption.md`
  — adopt the structured model everywhere, migrate the posts, keep legacy
  reading working through one normalization point, and establish the
  generated-output evidence and tests.
- [ ] `tasks/20261102-multi-author-migration/020-legacy-author-rejection.md`
  — flip the compatibility state to reject the legacy form, gated on 010's
  evidence (`Depends On` declared in that file).

Order rationale: 010 ends in an independently acceptable, shippable state —
fully migrated with legacy still tolerated, which is exactly the transition
state the request requires. 020 is the compatibility-state flip and remains
blocked if 010's evidence shows a remaining dependency, so it can be deferred
or reported separately without reopening 010.

## Supporting details

Facts from inspection (20261102, repo-wide search):

- Complete legacy-`author` inventory: `_includes/layouts/post.njk:2` renders
  `{{ author }}`; `content/feed.xml.njk:5` renders one
  `<author>{{ post.data.author }}</author>` per post; `scripts/new-post.js`
  emits `author: "<name>"` via `frontMatter(title, author)`; content:
  `content/posts/first.md` (`Ada Example`) and `content/posts/second.md`
  (`Grace Example`).
- `_includes/postslist.njk`, `content/blog.njk`, `content/index.njk`,
  `content/tag-pages.njk`, and `content/sitemap.xml.njk` render no author
  data.
- `content/posts/posts.json` is the directory data file (shared `layout`,
  `tags: ["posts"]`); a JS directory data file (`posts.11tydata.js`) can host
  a normalization accessor via `eleventyComputed`.
- `tests/author-output.test.js` and `tests/archive-output.test.js` are
  comment-only placeholders; `npm test` (`node --test tests/*.test.js`)
  passes trivially today. There is no existing author coverage to preserve —
  only coverage to establish. Because empty test files pass, evidence must
  confirm tests actually collected and ran.
- Dependencies are not installed (no `node_modules/`, no lockfile);
  `node_modules/` and `_site/` are gitignored, so builds and baseline
  snapshots keep the working tree clean. Build evidence requires
  `npm install` first.
- Eleventy ^3.0.0 with Nunjucks templates. No `docs/index.md`;
  `docs/development/index.md` holds only an unrelated archive-pagination
  placeholder. Current author values are plain ASCII and the author-bearing
  templates contain no dates, so generated output comparison should be
  deterministic.
