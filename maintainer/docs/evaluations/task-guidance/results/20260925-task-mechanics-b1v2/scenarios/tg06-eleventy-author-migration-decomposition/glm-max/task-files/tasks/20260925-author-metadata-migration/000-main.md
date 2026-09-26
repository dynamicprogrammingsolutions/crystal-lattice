# Migrate post author metadata to a structured multi-author model

Staged migration of the single-name `author` front-matter field to a structured
multi-author model across content, templates, feed, archive outputs, and the
authoring tool, ending with a rejection of the legacy form that is gated on
recorded generated-output and content evidence.

## Requirements checklist

- [ ] R1 — Posts accept a structured multi-author metadata form: a single ordered
  `authors` list where every author resolves to at least a display name (exact
  item shape per approved decision Q1).
- [ ] R2 — Transitional compatibility: until legacy rejection executes, the
  legacy `author` string stays accepted and posts using it render byte-identically
  to today; no existing content or generated page breaks at any stage boundary.
- [ ] R3 — Author-consuming templates render through the new model: the post
  layout byline renders every author in declared order; the feed emits one
  author entry per author. Single-author generated output remains unchanged.
- [ ] R4 — Non-author outputs unaffected: home, blog archive, tag pages, and
  sitemap keep their current generated output throughout the migration.
- [ ] R5 — The authoring tool (`scripts/new-post.js`) emits the structured form only.
- [ ] R6 — Existing posts (`content/posts/first.md`, `content/posts/second.md`)
  are migrated to the structured form as content changes.
- [ ] R7 — The legacy form is rejected (production build fails on legacy `author`
  content) only after recorded generated-output and content evidence shows no
  remaining dependency on it; if the evidence shows a straggler, rejection does
  not execute and the finding is reported instead.
- [ ] R8 — Maintained documentation (README authoring note) reflects the current
  supported model at each stage, updated in the same change as the behavior it
  describes.

## Subtasks

- [ ] tasks/20260925-author-metadata-migration/010-multi-author-model.md
- [ ] tasks/20260925-author-metadata-migration/020-authoring-and-content-migration.md
- [ ] tasks/20260925-author-metadata-migration/030-legacy-rejection.md

## Open questions (execution blockers)

- Q1 (design decision — data + feed contract): item shape of `authors` —
  (a) plain name strings, or (b) objects with required `name` (optional
  `url`/`email` deferred). Recommendation: (b); both preserve current
  single-author output. Must be approved before 010 executes.
- Q2 (scope confirmation): no new per-author archive pages or author profile
  pages are included; "archives" is covered as continuity of existing archive
  output. Confirm before execution.
- Q3 (minor, user-visible, resolvable at review): multi-author byline join
  format. Recommendation: comma-joined names (e.g. `Ada Example, Grace
  Example`); single-author output stays byte-identical.

## Supporting facts

- Current model: single string `author` in post front matter
  (`content/posts/first.md:3`, `content/posts/second.md:3`).
- Consumers: `_includes/layouts/post.njk:2` renders top-level `author` in the
  byline; `content/feed.xml.njk:5` renders `post.data.author` per feed entry.
  Repo-wide search confirms no other template, script, or test reads author
  data; home, archive, tag pages, and sitemap render none.
- Authoring tool: `scripts/new-post.js:1-3` exports `frontMatter(title, author)`
  emitting the legacy single-name form; nothing in the repo imports it.
- Test state: `tests/author-output.test.js` and `tests/archive-output.test.js`
  are placeholder files containing only comments — no assertions exist yet.
- Build: Eleventy 3 (`eleventy.config.js`, input `content/`, includes
  `_includes/`, output `_site/`); scripts `npm run build` and `npm test`
  (`node --test tests/*.test.js`). `node_modules` is not installed in this
  workspace (gitignored); execution must install before running.
- Current single-author generated output: post page `<p class="author">{name}</p>`;
  feed `<author>{name}</author>`. This is the regression anchor for the
  byte-identical continuity claims in R2/R3.
- Multi-author rendering cannot be proven by adding a permanent post to
  `content/` (that would change public output); integration tests must drive the
  real build against a temporary content fixture reusing the production config
  and templates (see 010).

## Execution plan

Status: Draft

### Design

Three gated stages, each leaving the build green and generated output stable.

One canonical read path owns the author shape so every consumer moves together
and the legacy branch has exactly one home. Components:

- **Canonical author model + normalizer (new)**: a single function (config
  filter or computed data owned by the posts collection config) that accepts the
  structured form and, during transition, the legacy scalar, and returns the
  ordered canonical author list exposed as `authors`. It is the only code that
  reads raw `author`. Item shape per Q1.
- **Consumers**: `_includes/layouts/post.njk` byline and `content/feed.xml.njk`
  entries read only the canonical `authors`; they never read raw author front
  matter directly. Single-author rendering remains byte-identical.
- **Authoring tool**: `scripts/new-post.js` emits the structured form only.
- **Content**: both posts migrate to the structured form.
- **Rejection**: the same canonical read path throws on legacy input after the
  evidence gate, failing the production build; covered by a test.

Compatibility states: S1 (after 010) — dual-form accepted, new model live in
templates; S2 (after 020) — content and tooling fully on the new form, legacy
still tolerated but unused; S3 (after 030) — legacy rejected with a build error
and transitional documentation removed.

Verification strategy: integration tests drive the real Eleventy production
build (no mocks at the important boundary) and assert generated HTML/XML —
author-output test (byline and feed for multi-author and legacy posts at S1;
rejection behavior at S3) and archive-output test (home/archive/tags/sitemap
continuity). A unit test covers the tooling's emitted front matter. 020 records
the evidence bundle (content scan plus before/after output comparison) that
gates 030.

### Implementation decisions and open questions

- D1 (decision): one canonical read path (normalizer) is the only reader of the
  legacy `author` key, keeping the rejection surface to a single branch.
- D2 (decision): canonical key `authors`, ordered as declared in front matter;
  consumers must not read raw author keys.
- D3 (decision): rejection via the normalizer raising an actionable error that
  fails the build; no silent fallback or auto-conversion after rejection.
- Q1 (question, blocker): `authors` item shape — strings vs objects with
  required `name`. Recommendation: objects with required `name`, matching the
  "structured" intent and leaving room for feed metadata later.
- Q2 (question, blocker): confirm no per-author archive/profile page scope.
- Q3 (recommendation): comma-joined multi-author byline; single author unchanged.
- D4 (recommendation, confirm): no new presence validation for missing `authors`
  — today a missing author renders an empty byline, and this migration's scope
  is the legacy key, not new validation rules.

### Documentation

`README.md` gains a short Authoring note describing the `authors` front-matter
contract and the `scripts/new-post.js` output, added in 010 with a visible
transitional note about the still-accepted legacy field; 020 keeps it accurate
for tooling and content; 030 removes the transitional note and documents the
rejection error and migration path. Audience: content authors working in this
repo. No new docs directories or placeholder pages.

### Task checklist

- [ ] 010 Multi-author model with legacy-compatible rendering —
  tasks/20260925-author-metadata-migration/010-multi-author-model.md
- [ ] 020 Authoring-tool and content migration, legacy-dependency evidence
  gate (depends on 010) —
  tasks/20260925-author-metadata-migration/020-authoring-and-content-migration.md
- [ ] 030 Legacy-form rejection gated on recorded evidence (depends on 020) —
  tasks/20260925-author-metadata-migration/030-legacy-rejection.md

### Requirement verification

- R1, R3, R2 (S1 state): `tests/author-output.test.js` integration test through
  the real Eleventy production build — multi-author post page byline lists all
  authors in order, feed carries one `<author>` per author, and a legacy-form
  post's output matches the pre-migration baseline. Decisive; traverses content
  → build → generated HTML/XML.
- R2, R4: `tests/archive-output.test.js` integration test — home, blog archive,
  tag pages, and sitemap output unchanged; full `npm run build` green at each
  stage boundary.
- R5: unit test asserting `frontMatter()` emits the structured form; migrated
  content building in the production build corroborates the contract.
- R6: production build of migrated posts plus per-post byline/feed comparison
  against the pre-migration baseline recorded in 020.
- R7: evidence bundle recorded in 020's `## Implementation Notes` (content scan
  results plus output diff summary); 030 is blocked without it. 030 adds a test
  asserting the build fails on legacy-form content and a final green full build.
- R8: README reviewed and updated within each stage's change set.

### Additional implementation verification

None beyond the above. The fixture's surface is small and fully covered by the
production-build tests; the 020 scan additionally confirms no Eleventy data
cascade path (directory data, globals, layouts) injects `author`.