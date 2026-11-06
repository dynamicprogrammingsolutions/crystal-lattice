# Migrate post author metadata to structured multi-author form

Move the site from a single-name `author` front matter field to a structured
multi-author form across templates, feed, and authoring tooling; migrate
existing posts safely; retire the legacy form only after generated-output and
content evidence show nothing still depends on it. Planning only — no
implementation has been approved yet.

## Requirements checklist

- [ ] R1 — Posts can declare authors in the structured multi-author form and the
      production build renders them on post pages and in the feed.
- [ ] R2 — Every author-aware surface (post layout template, feed template,
      `scripts/new-post.js`) consumes the new model through one shared
      normalization point; no surface reads the legacy field directly.
- [ ] R3 — During the transition the legacy single-name form is still accepted
      and renders exactly as it does today; home, archive, tag pages, and
      sitemap output are unchanged by the model introduction.
- [ ] R4 — All existing post content is migrated to the structured form with
      production-build output parity proven for every generated file.
- [ ] R5 — The legacy form is rejected by the build with an actionable error,
      and only after recorded generated-output parity plus content-scan
      evidence show nothing in content or output still depends on it.
- [ ] R6 — Maintained documentation describes the currently supported author
      metadata form at each compatibility state (dual acceptance, then
      new-form only).

## Requirement questions and decisions

Material decisions pending approval (full tradeoffs in the parent execution
plan below; scope-local choices live in each subtask):

- D1 (requirement — data shape): structured form shape — list of author name
  strings vs list of objects (e.g. `{ name, url }`). Recommendation: list of
  plain name strings; migration maps `author: "X"` to a one-element list.
- D2 (requirement — user-visible output): multi-author rendering.
  Recommendation: post page joins names with `", "`; feed emits one `<author>`
  element per author in front matter order; single-author output stays
  byte-identical to today.
- D3 (requirement — scope boundary): archives and listings currently render no
  author data at all. Recommendation: keep them author-agnostic (regression
  parity only); do not add author display.
- D4 (design — transition semantics): when a post carries both forms,
  recommendation: `authors` takes precedence and legacy is ignored (no error)
  until 030 enables rejection.

## Supporting facts

Verified by inspection during planning:

- Legacy-form usage inventory (the complete author dependency surface):
  - `content/posts/first.md` (`author: "Ada Example"`),
    `content/posts/second.md` (`author: "Grace Example"`) — the only content
    using the field.
  - `_includes/layouts/post.njk:2` — `<p class="author">{{ author }}</p>`
    (post pages).
  - `content/feed.xml.njk:5` — `<entry><author>{{ post.data.author
    }}</author></entry>` (feed).
  - `scripts/new-post.js` — `frontMatter(title, author)` emits legacy front
    matter; no in-repo callers.
  - `tests/author-output.test.js` — comment-only stub (no real coverage).
- Author-agnostic surfaces with no author reference (must stay correct through
  the migration): `_includes/postslist.njk`, `content/blog.njk`,
  `content/index.njk`, `content/tag-pages.njk`, `content/sitemap.xml.njk`,
  `content/posts/posts.json`.
- Build: Eleventy 3, input `content/`, includes `_includes/`, output `_site/`
  (gitignored). Commands: `npm run build`, `npm test` (`node --test`).
- `node_modules` is not installed at planning time; `npm install` is required
  before any build or test run.
- Baseline verified: `npm test` at HEAD passes trivially (stub files contain
  no tests) — `# pass 2 # fail 0`.
- `docs/development/index.md` contains no author-related specification.

## Subtasks

- [ ] tasks/20261029-post-author-migration/010-introduce-multi-author-model.md
- [ ] tasks/20261029-post-author-migration/020-migrate-existing-posts.md
- [ ] tasks/20261029-post-author-migration/030-retire-legacy-author.md

## Execution plan

Status: Draft

Approach: three sequenced increments, each leaving the site in a coherent,
independently buildable compatibility state.

1. **010 — Introduce the structured model behind dual acceptance.** One shared
   normalization point feeds the post layout and feed templates; the authoring
   tool emits the new form; legacy posts keep rendering exactly as today.
   Real-build integration tests pin both paths, plus a full-output before/after
   comparison proving the model introduction changed no generated file.
2. **020 — Migrate existing post content.** Convert front matter to the
   structured form and prove byte-identical production output for every
   generated file (hash comparison before/after) plus a content scan showing no
   legacy keys remain. The recorded evidence becomes the 030 gate input.
3. **030 — Retire the legacy form (evidence-gated).** Review the recorded
   evidence, then enable strict rejection in the shared normalization point,
   replace temporary dual-acceptance coverage with rejection coverage, and
   finalize documentation.

Compatibility states: after 010 both forms render; after 020 all content uses
the new form while legacy is still tolerated; after 030 the legacy form is
rejected. Execution order 010 → 020 → 030 is required: 020's evidence is only
meaningful against 010's dual-read model, and 030's gate consumes 020's
evidence.

Verification strategy: decisive checks run the real Eleventy production build —
full-output parity comparisons for no-regression claims, rendered-output
assertions for the new model, and a build-failure assertion for rejection.
Unit tests cover only the normalization point and the authoring generator.

Risks:

- Computed-data wiring could interact with pagination/collections — mitigated
  by real-build tests covering archive, tag, home, and sitemap output.
- `scripts/new-post.js` may have external callers — no in-repo callers;
  signature change accepted (recorded on 010).
- Unknown external consumers of the legacy form cannot be proven absent from
  inside this repository. The gate covers in-repo content and generated output
  only; the actionable rejection error message is the mitigation. Residual
  risk accepted unless the user knows of external consumers.

### Implementation decisions and open questions

Pending approval (material; answers may adjust subtask plans):

- D1 data shape: recommendation — `authors` as a list of plain name strings.
  Extensible later to objects without re-migrating single-name content.
- D2 rendering: recommendation — post page: names joined `", "`; feed: one
  `<author>` element per author in front matter order; single-author output
  byte-identical to today.
- D3 archives boundary: recommendation — listings stay author-agnostic; no new
  author display (they render no author data today).
- D4 both-forms precedence: recommendation — `authors` wins, legacy ignored,
  no error, until 030 enables rejection; 020's content scan guarantees no
  dual-form posts remain in the repository anyway.

Resolved locally (recorded on the owning subtask): rejection enforcement point
(shared normalization module, 030); `frontMatter` signature change (010);
normalization module location and Eleventy wiring mechanism (010).

### Documentation

Audience: content authors. Destination: a short "Post authors" section in
`README.md` — added in 010 (structured form plus a visible note that the
legacy form is still accepted during migration), rewritten in 030 (structured
form only). No new documentation structure; `docs/development/documentation.md`
guidance applies to both edits.

### Task checklist

- [ ] tasks/20261029-post-author-migration/010-introduce-multi-author-model.md
- [ ] tasks/20261029-post-author-migration/020-migrate-existing-posts.md
- [ ] tasks/20261029-post-author-migration/030-retire-legacy-author.md

### Requirement verification

- R1 → owned by 010: integration test drives the real Eleventy build on a temp
  fixture site carrying a multi-author post and asserts the rendered post page
  (joined names) and feed (one `<author>` per author).
- R2 → owned by 010: unit tests on the shared normalization module plus
  recorded review that templates and tooling reference only the normalized
  model; `frontMatter` unit test for the authoring tool.
- R3 → owned by 010: integration test pinning repo-content build output
  (`Ada Example` / `Grace Example` on post pages and feed) plus the recorded
  before/after full-output comparison of every generated file; preserved by
  020's parity evidence.
- R4 → owned by 020: full-output hash comparison of the real production build
  before/after the content edit, plus the repository content scan.
- R5 → owned by 030: recorded gate-evidence review (parity + scan + tooling),
  then an integration test driving the real build on a legacy-form fixture
  post asserting failure with the actionable message, and a green real build
  of repository content.
- R6 → owned by 010 and 030: README updated in the same reviewed change as the
  behavior it describes.
