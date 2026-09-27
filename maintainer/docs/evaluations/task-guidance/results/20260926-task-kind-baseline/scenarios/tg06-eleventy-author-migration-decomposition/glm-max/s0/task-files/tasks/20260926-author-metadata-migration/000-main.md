# Post author metadata migration to structured multi-author model

Migrate post author metadata from the single-name `author` front matter field
to a structured multi-author model across templates, archives, feeds, and the
authoring tool, without breaking existing content or generated pages during
the transition. The legacy single-name form may be rejected only after
generated-output and content evidence show that nothing still depends on it.

Planning only: no implementation has been requested or performed yet.

## Requirements checklist

- [ ] R1 — Post author metadata supports a structured multi-author form as the
      target representation (exact schema per the approved answer to Q1 below).
- [ ] R2 — During the transition, existing content and generated pages keep
      working: posts still in the legacy form build and render with unchanged
      author output (post pages and feed).
- [ ] R3 — All author consumers move to the new model: post page layout
      (`_includes/layouts/post.njk`), feed (`content/feed.xml.njk`), the
      authoring tool (`scripts/new-post.js`), and the archive surfaces
      (`content/blog.njk`, `content/tag-pages.njk`, `_includes/postslist.njk`,
      `content/index.njk`), which today render no author and therefore must
      keep building correctly with multi-author data and not depend on legacy.
- [ ] R4 — Both existing posts (`content/posts/first.md`,
      `content/posts/second.md`) are migrated to the new model with author
      values preserved exactly ("Ada Example", "Grace Example").
- [ ] R5 — The legacy single-name form is rejected only after generated-output
      and content evidence show that nothing still depends on it; that gate is
      verified fresh immediately before rejection, not assumed from earlier
      stages.
- [ ] R6 — End state: the legacy form is rejected (build fails on legacy
      content; authoring tool rejects legacy input) and no dual acceptance
      remains.
- [ ] R7 — Maintained documentation reflects the supported author model at
      each stage (current behavior only; no unmarked target-only claims),
      per the repository documentation policy.

## Subtasks

- [ ] tasks/20260926-author-metadata-migration/010-structured-authors-adoption.md — introduce the structured model with legacy still accepted; build the generated-output evidence later stages depend on
- [ ] tasks/20260926-author-metadata-migration/020-content-migration.md — migrate existing post front matter; prove output unchanged
- [ ] tasks/20260926-author-metadata-migration/030-legacy-rejection.md — evidence-gated removal and rejection of the legacy form

Requirement → owning subtask:

| Requirement | Owner |
| --- | --- |
| R1 (new model supported) | 010 |
| R2 (transition non-breaking) | 010, preserved through 020 |
| R3 (all consumers moved) | 010 (templates, feed, tool, archives) |
| R4 (existing posts migrated) | 020 |
| R5 (evidence gate before rejection) | 030, using evidence built by 010 and content evidence from 020 |
| R6 (legacy rejected, end state) | 030 |
| R7 (documentation current per stage) | 010, 020, 030 (each within its own stage) |

## Requirement questions

- Q1 (blocks execution of 010 and everything downstream) — What is the exact
  schema of the structured multi-author form? Recommendation: an `authors`
  list of objects with a required `name` field
  (`authors:\n  - name: Ada Example`), extensible later (e.g. `url`).
  Alternative: a list of plain strings. This choice shapes content files,
  templates, the authoring tool, and the migration of R4, so it needs
  approval before execution starts.

## Supporting facts

- Current model: `author` as a single quoted string in post front matter —
  `content/posts/first.md:3` ("Ada Example"), `content/posts/second.md:3`
  ("Grace Example"). `content/posts/posts.json` sets the post layout and
  `tags: ["posts"]` for the collection.
- A repo-wide search for `author` finds every consumer:
  `_includes/layouts/post.njk:2` (`<p class="author">{{ author }}</p>`),
  `content/feed.xml.njk:5` (`<entry><author>{{ post.data.author }}</author>`
  per post), `scripts/new-post.js:1-2` (emits `author: "..."` front matter),
  and the two content files above. No other consumer exists.
- Archive surfaces (`_includes/postslist.njk`, `content/blog.njk`,
  `content/tag-pages.njk`, `content/index.njk`) render only titles and URLs,
  so "moving archives to the new model" is a compatibility requirement, not a
  display change. Adding author display to archives would be new scope and is
  not planned (recommendation).
- `tests/author-output.test.js` and `tests/archive-output.test.js` contain
  placeholder comments only; the author-output comment claims generated-output
  coverage that does not exist. There is currently no automated evidence of
  any kind, so the R5 gate must be built as part of this migration, not cited
  as pre-existing coverage.
- Build and test entry points: `npm run build` (Eleventy 3, input `content/`,
  includes `_includes/`, output `_site/`; feed `/feed/feed.xml`, archive
  `/blog/`, tag pages `/tags/<slug>/`) and `npm test`
  (`node --test tests/*.test.js`).
- `node_modules` is absent in this workspace; `npm install` is required before
  any build or test verification during execution.
- No `tasks/` directory existed prior to this planning; it is created by this
  handoff. Nothing outside `tasks/` has been changed by planning.

## Execution plan

Status: Draft

Approach — three sequential compatibility states, each independently
verifiable, with a hard evidence gate before the last:

1. Stage 1 (subtask 010): introduce the structured multi-author model and make
   every consumer able to render it, while legacy `author` continues to work
   unchanged. This stage also builds the generated-output evidence (tests
   asserting real `_site` output) that stages 2 and 3 rely on.
2. Stage 2 (subtask 020): convert both existing posts to the structured form
   and prove, through the same production-build assertions, that generated
   output is unchanged. Completing this stage is the content half of the R5
   gate.
3. Stage 3 (subtask 030): re-verify the gate fresh (content scan + consumer
   inventory + passing build), then remove legacy compatibility and reject the
   legacy form in the build and the authoring tool, updating tests and
   documentation to the structured-only end state.

Ordering is strict: 010 → 020 → 030, declared as dependencies in the subtask
files. Every permitted execution order is safe because 020 requires 010's
model and evidence, and 030 requires both.

Design common to the stages: normalize author data once at the data layer so
templates consume a single normalized form (see 010 for the design), and keep
the canonical rendered form for a single author byte-identical to today's
legacy output. That equivalence is what makes the migration provably safe and
the R5 gate decidable by comparison rather than judgment.

Decisive checks (one per product connection, through the real production
path):

- Author rendering on post pages and feed: production-build output assertions
  (`npm run build`, then assert on `_site` HTML/XML), owned by 010 and
  maintained by 020 and 030.
- Legacy rejection: a production build fails on a legacy fixture (sandboxed
  copy, no permanent legacy content), owned by 030.

Risks:

- The placeholder test comments could be mistaken for existing coverage; the
  gate must be built from real build-output assertions.
- Dependencies are not installed in this workspace; verification requires
  `npm install` first.
- Any unapproved schema choice (Q1) invalidates the plans below; execution
  waits until Q1 is resolved.

### Implementation decisions and open questions

- Q1 (requirement question, unresolved — see above): structured schema shape.
  Recommendation: `authors` list of objects with required `name`.
- Multi-author display on a post page: join names with ", " inside the
  existing `<p class="author">` element (recommendation; user-visible, so
  surfaced for approval with the plan).
- Feed representation: one `<author>` element per author, preserving the
  current element shape (recommendation).
- Legacy rejection mechanism: hard build failure with an actionable error,
  and rejection in the authoring tool — not a silent fallback or warning
  (recommendation; user-visible authoring behavior).
- Normalization mechanism (directory computed data vs. per-template logic):
  implementation choice made in 010; templates must not each re-implement it.

### Documentation

- Audience: content authors (front matter format, authoring tool usage).
- Smallest structure: a concise authoring/front-matter section in the nearest
  maintained doc (README.md is today's only site-level doc), updated within
  each subtask's reviewed change — dual acceptance in 010, structured-only in
  030. `docs/development/documentation.md` guidance applies to any new or
  moved pages. No placeholder pages.

### Task checklist

- [ ] tasks/20260926-author-metadata-migration/010-structured-authors-adoption.md
- [ ] tasks/20260926-author-metadata-migration/020-content-migration.md (Depends On 010)
- [ ] tasks/20260926-author-metadata-migration/030-legacy-rejection.md (Depends On 010, 020)

### Requirement verification

- R1, R2, R3 — production build plus build-output assertions added in 010:
  legacy posts render the current author line and feed element unchanged; a
  structured multi-author fixture renders the approved form on the post page
  and feed through the real build; archives still build. The authoring tool
  is covered by a component test plus a real build of its output.
- R4 — content scan (no legacy `author:` in `content/`) plus the same
  build-output assertions passing after 020 now exercise the structured path,
  proving output equivalence.
- R5 — fresh gate evidence recorded at the start of 030: content scan, consumer
  inventory, and a passing production build with the full test suite.
- R6 — production build fails on a legacy fixture; authoring tool rejects
  legacy input (integration through the real build, not a mocked validator).
- R7 — maintained documentation reviewed and updated within each stage;
  checked for stale claims about the legacy form.