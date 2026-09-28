# Session — tg06-eleventy-author-migration-decomposition · file-readability-assessment-glm-max-s0 · glm max

- Run: `20260928T204310.758440Z-task-guidance-file-readability-tg06-eleventy-author-migration-decomposition-glm-max-s0-73c1d3a3`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `75ac30d3d4024734…`)
- Config: [glm-assessor-max](../../../../../../shared/configs/glm-assessor-max.json)
- Activity: 3 messages · 0 tool calls · 0 tool results
- Usage: unknown — saved session contains no provider usage metadata

## Transcript

**User**

Assess how easily a human reader can work with the task files below.
You are that reader: a maintainer who must find, understand, and act on
what the files say. Judge every top-level section that is present; do
not invent sections that are absent, and do not grade files or sections
that do not appear.

Grade each present top-level section `readable`, `partial`, or
`unreadable`: can a reader take in that section's content with
reasonable effort — scan it, hold it, and use it? A section is
`unreadable` when a reader must re-read dense prose or wall-like list
items to extract what matters; `partial` when parts strain the reader.

Then grade the whole file's navigation `navigable`, `partial`, or
`confusing`: can a reader find the thing they are looking for — the
outcome, the constraint, the open question, the plan status — from the
file's structure alone?

Measured structure facts are provided per section; anchor on these
numbers rather than impressions. They are facts, not rules: no shape is
banned or required. Formatting elements — tables, ordered lists, code
snippets, short paragraphs — are tools among many; what is graded is
the reader's experience, never the presence of a specific element.

Every grade carries findings: concrete `{where, quote, why}` items. A
non-top grade with empty findings is invalid. Then hunt for
presentation mistakes explicitly — prose walls, list items that mix
several facts, buried load-bearing facts, headings that do not match
their content, walls of unchecked boxes — and list each as
`{where, quote, why}` in `mistakes`.

Depth must match impact: a short section is not a defect; a dense
section is not automatically one either. Verbosity is not rewarded;
brevity that loses nothing is not penalized.

Return JSON only:

{
  "schema_version": 1,
  "scenario_id": "tg06-eleventy-author-migration-decomposition",
  "assessment": {
    "sections": {
      "SECTION TITLE": {
        "grade": "readable|partial|unreadable",
        "findings": [{"where": "...", "quote": "...", "why": "..."}]
      }
    },
    "navigation": {"grade": "navigable|partial|confusing", "findings": []},
    "mistakes": [{"where": "...", "quote": "...", "why": "..."}],
    "summary": "concise evidence-based interpretation"
  }
}

`sections` contains exactly the top-level sections listed in the
measured facts, keyed by the exact Section values of that table
(`<file path> — <section title>`), so multi-file task sets stay
addressable.

What these files are for:

# Eleventy author metadata migration decomposition

Partition a broad content/build migration by compatible working states rather than files and phases.

Category: decomposition

Measured structure facts (per file, per top-level section):

#### tasks/20260926-author-metadata-migration/000-main.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-author-metadata-migration/000-main.md — Requirements checklist | 224 | 0 | 0 | 7 | 13 | 0 | 0 | 0 | 9 |
| tasks/20260926-author-metadata-migration/000-main.md — Subtasks | 143 | 1 | 4 | 3 | 18 | 0 | 9 | 0 | 0 |
| tasks/20260926-author-metadata-migration/000-main.md — Requirement questions | 67 | 0 | 0 | 1 | 14 | 0 | 0 | 0 | 4 |
| tasks/20260926-author-metadata-migration/000-main.md — Supporting facts | 224 | 0 | 0 | 7 | 14 | 0 | 0 | 0 | 31 |
| tasks/20260926-author-metadata-migration/000-main.md — Execution plan | 678 | 5 | 59 | 24 | 15 | 4 | 0 | 0 | 12 |

#### tasks/20260926-author-metadata-migration/010-structured-authors-adoption.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-author-metadata-migration/010-structured-authors-adoption.md — Requirements checklist | 162 | 0 | 0 | 7 | 12 | 0 | 0 | 0 | 9 |
| tasks/20260926-author-metadata-migration/010-structured-authors-adoption.md — Supporting facts | 119 | 0 | 0 | 6 | 11 | 0 | 0 | 0 | 17 |
| tasks/20260926-author-metadata-migration/010-structured-authors-adoption.md — Execution plan | 655 | 2 | 20 | 28 | 13 | 5 | 0 | 0 | 32 |

#### tasks/20260926-author-metadata-migration/020-content-migration.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-author-metadata-migration/020-content-migration.md — Requirements checklist | 112 | 0 | 0 | 5 | 11 | 0 | 0 | 0 | 3 |
| tasks/20260926-author-metadata-migration/020-content-migration.md — Supporting facts | 95 | 0 | 0 | 6 | 12 | 0 | 0 | 0 | 4 |
| tasks/20260926-author-metadata-migration/020-content-migration.md — Execution plan | 317 | 1 | 2 | 19 | 15 | 4 | 0 | 0 | 7 |

#### tasks/20260926-author-metadata-migration/030-legacy-rejection.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-author-metadata-migration/030-legacy-rejection.md — Requirements checklist | 173 | 0 | 0 | 7 | 12 | 0 | 0 | 0 | 3 |
| tasks/20260926-author-metadata-migration/030-legacy-rejection.md — Supporting facts | 147 | 0 | 0 | 4 | 14 | 0 | 0 | 0 | 2 |
| tasks/20260926-author-metadata-migration/030-legacy-rejection.md — Execution plan | 485 | 1 | 2 | 29 | 14 | 5 | 0 | 0 | 7 |

The produced task files:

### tasks/20260926-author-metadata-migration/000-main.md

````markdown
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
````

### tasks/20260926-author-metadata-migration/010-structured-authors-adoption.md

````markdown
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
````

### tasks/20260926-author-metadata-migration/020-content-migration.md

````markdown
# Migrate existing post content to structured authors

Convert the existing posts' front matter from the legacy single-name `author`
field to the structured multi-author model, preserving values exactly and
proving through the production build that generated output is unchanged.

Parent Task: tasks/20260926-author-metadata-migration/000-main.md

Depends On: tasks/20260926-author-metadata-migration/010-structured-authors-adoption.md
(the structured model must exist and the build-output evidence must be in
place before content switches to it)

## Requirements checklist

- [ ] `content/posts/first.md` and `content/posts/second.md` use only the
      structured model; the legacy `author` field is removed from them.
- [ ] Author values are preserved exactly and in order: "Ada Example" and
      "Grace Example".
- [ ] Generated output after migration is unchanged versus the pre-migration
      output: post page author lines and feed author elements stay identical
      (proven by the production-build assertions from 010, now exercising the
      structured path).
- [ ] No content file retains or introduces the legacy field after migration
      (repo-wide content scan clean).
- [ ] Documentation contains no stale claim that existing posts still use the
      legacy form (no behavioral change is introduced by this stage).

## Supporting facts

- Current front matter to migrate:
  - `content/posts/first.md`: `author: "Ada Example"`
  - `content/posts/second.md`: `author: "Grace Example"`
- Conversion is mechanical and value-preserving (1:1): the legacy string
  becomes a single structured entry carrying the same name, in file order.
- Both posts are single-author, so their canonical rendered output must be
  byte-identical before and after migration — this is exactly what the 010
  equivalence assertions are designed to prove.
- If an unexpected front matter shape is found during migration (missing
  author, non-string value), report it instead of inventing a default; no
  fallback behavior is specified.

## Execution plan

Status: Draft

- Convert both content files to the approved structured schema (Q1), removing
  the legacy field from each.
- Run the production build and the full test suite. The 010 build-output
  assertions (which pin the exact legacy-era author strings) must pass after
  migration — passing through the structured path is the output-unchanged
  proof for this stage.
- Run a content scan confirming no `author:` legacy field remains under
  `content/`.
- Documentation: no behavior change in this stage (dual acceptance is still
  the supported behavior); verify no maintained doc claims existing posts use
  the legacy form, and leave the rest unchanged.

Execution tasks:

1. Migrate `content/posts/first.md` to the structured form.
2. Migrate `content/posts/second.md` to the structured form.
3. Production build + full test suite (equivalence assertions pass).
4. Content scan for residual legacy fields.
5. Check maintained docs for stale claims.

### Implementation decisions and open questions

- None new. The schema is fixed by the approved answer to parent Q1. The
  conversion is mechanical; any anomaly in existing front matter is reported,
  not silently normalized.

### Documentation

- No user-facing change is made here; supported behavior (dual acceptance)
  is unchanged. Only a stale-claims check is in scope for this stage.

### Task checklist

- [ ] `content/posts/first.md` migrated, value preserved
- [ ] `content/posts/second.md` migrated, value preserved
- [ ] Production build + tests clean (output unchanged)
- [ ] Content scan shows no legacy `author:` field
- [ ] Docs checked for stale legacy-content claims

### Requirement verification

- Values preserved and legacy removed (parent R4): front-matter inspection of
  both files plus the content scan.
- Output unchanged (parent R2, R4): the production-build assertions from 010
  pin the exact author strings; they pass after migration while reading the
  structured field — real build output, not a mocked cascade.
- Gate contribution (parent R5): the clean content scan and passing build
  from this stage are the content half of the 030 gate; 030 re-verifies it
  fresh rather than assuming it.
````

### tasks/20260926-author-metadata-migration/030-legacy-rejection.md

````markdown
# Reject legacy single-author field after evidence gate

After re-verifying that nothing still depends on the legacy single-name
`author` field, remove the compatibility path and make the legacy form an
error in the build and the authoring tool, ending the migration in a
structured-only state.

Parent Task: tasks/20260926-author-metadata-migration/000-main.md

Depends On:
- tasks/20260926-author-metadata-migration/010-structured-authors-adoption.md
- tasks/20260926-author-metadata-migration/020-content-migration.md

## Requirements checklist

- [ ] Gate (precondition, verified fresh at the start of execution, not
      assumed from earlier stages): content scan shows no legacy `author`
      field; the consumer inventory shows every author consumer (post layout,
      feed, authoring tool) operating on the structured model and archives
      free of legacy dependence; the latest production build and full test
      suite pass. Execution stops if any check fails.
- [ ] Legacy compatibility normalization (deriving structured data from
      `author`) is removed from the data cascade and templates.
- [ ] Content using the legacy field fails the production build with a clear,
      actionable error; no silent fallback or warning-only behavior.
- [ ] `scripts/new-post.js` rejects legacy single-name input and emits only
      the structured form.
- [ ] Existing generated output remains unchanged (the 010-era author
      assertions still pass, now structured-only).
- [ ] Tests updated: legacy-equivalence assertions replaced by structured-only
      assertions plus a rejection assertion exercised through a real build.
- [ ] Documentation updated to the structured-only end state; the legacy form
      is documented as unsupported current behavior.

## Supporting facts

- The gate constraint comes from the original request: the legacy form may be
  rejected only after generated-output and content evidence show that nothing
  still depends on it. Both halves of that evidence exist only after 010
  (generated-output assertions) and 020 (content migrated, scan clean).
- After 020, no content uses `author`; after 010, templates and the tooling
  read the normalized structured form. The remaining legacy dependence is the
  compatibility normalization itself — which is exactly what this stage
  removes.
- The rejection must be proven through the real production build (a legacy
  fixture in a sandboxed copy fails `npm run build`), not through a mocked
  validator, per the repository testing guidance.
- A warning-only acceptance would leave a silent dependency path and would
  not satisfy "rejected"; the recommendation is a hard build failure. This is
  user-visible authoring behavior and is surfaced for approval with the plan.

## Execution plan

Status: Draft

- Gate check first: rerun the content scan, the consumer inventory, and the
  full build/test cycle. Record the evidence before touching compatibility
  code. If the gate fails, stop and report rather than forcing the removal.
- Remove the legacy normalization path from the posts data cascade; templates
  keep reading the normalized structured form only.
- Add build-time validation that fails the build with an actionable error
  when a post carries the legacy `author` field (mechanism: an Eleventy
  data-validation point in the real build path; exact mechanism is an
  implementation choice).
- Update `scripts/new-post.js` to accept only the structured form and reject
  legacy input.
- Update tests: structured-only rendering assertions plus the rejection test
  (sandboxed copy with a legacy fixture; the build must fail). Archive checks
  unchanged.
- Update documentation: structured form only; legacy explicitly unsupported
  as current behavior.
- Full production build and test suite; confirm existing generated output is
  unchanged for the migrated content.

Execution tasks:

1. Fresh gate verification (content scan + consumer inventory + build/tests);
   record evidence.
2. Remove legacy compatibility normalization.
3. Add legacy-field build validation with an actionable error.
4. Restrict `scripts/new-post.js` to the structured form.
5. Update tests (structured-only + rejection through real build).
6. Update documentation to structured-only.
7. Full build + test run; confirm output stability.

### Implementation decisions and open questions

- Rejection mechanism: hard build failure for legacy content plus rejection
  in the authoring tool (recommendation; user-visible — surfaced for
  approval with this plan). A warning-based fallback is not planned because
  it would keep a silent legacy path alive.
- The rejection test uses a temporary legacy fixture in a sandboxed copy; no
  permanent legacy content is added to `content/`.

### Documentation

- Update the authoring/front-matter documentation to structured-only: the
  legacy `author` field is listed as unsupported. Audience: content authors.
  Keep the smallest structure established in stage 1; follow
  `docs/development/documentation.md` for any page moves.

### Task checklist

- [ ] Gate evidence recorded (scan + inventory + passing build/tests)
- [ ] Legacy normalization removed from the data cascade
- [ ] Build validation rejects the legacy field with actionable error
- [ ] `scripts/new-post.js` rejects legacy input
- [ ] Tests: structured-only assertions + real-build rejection test
- [ ] Documentation updated to structured-only
- [ ] Full build + test run clean; output unchanged for existing content

### Requirement verification

- Gate (parent R5): fresh evidence recorded in this stage before any removal —
  content scan clean, consumer inventory, passing production build and tests.
- Rejection end state (parent R6): a production build fails on a sandboxed
  legacy fixture (real build path, not a mocked validator), and the authoring
  tool rejects legacy input.
- Output stability (parent R2/R4): the pinned author assertions from 010 pass
  in structured-only form after the compatibility removal.
- Documentation (parent R7): maintained docs reviewed to describe the
  structured-only supported behavior.

### Additional implementation verification

- Confirm no template, data file, or script reference to the legacy field
  remains (repo-wide search), complementing the build-level rejection.
````


**Assistant** *(reasoning present)*

```json
{
  "schema_version": 1,
  "scenario_id": "tg06-eleventy-author-migration-decomposition",
  "assessment": {
    "sections": {
      "tasks/20260926-author-metadata-migration/000-main.md — Requirements checklist": {
        "grade": "partial",
        "findings": [
          {
            "where": "R3 checkbox",
            "quote": "and the archive surfaces (`content/blog.njk`, `content/tag-pages.njk`, `_includes/postslist.njk`, `content/index.njk`), which today render no author and therefore must keep building correctly with multi-author data and not depend on legacy",
            "why": "One unchecked box carries the requirement, seven file paths, and a trailing relative clause whose scope (archives only, not all consumers) takes a second read to attach correctly — the densest box in the whole set (224 words across 7 items)."
          },
          {
            "where": "R5 checkbox",
            "quote": "The legacy single-name form is rejected only after generated-output and content evidence show that nothing still depends on it; that gate is verified fresh immediately before rejection, not assumed from earlier stages.",
            "why": "Two distinct requirements — the gate condition and the freshness rule — share one box separated only by a semicolon; the load-bearing freshness rule arrives second."
          },
          {
            "where": "R7 checkbox",
            "quote": "Maintained documentation reflects the supported author model at each stage (current behavior only; no unmarked target-only claims), per the repository documentation policy.",
            "why": "The compressed parenthetical jargon ('no unmarked target-only claims') forces the reader to unpack what the documentation constraint actually forbids."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/000-main.md — Subtasks": {
        "grade": "readable",
        "findings": [
          {
            "where": "subtask bullets",
            "quote": "tasks/20260926-author-metadata-migration/030-legacy-rejection.md — evidence-gated removal and rejection of the legacy form",
            "why": "Each subtask is one filename plus one purpose clause, so the three-stage partition is graspable at a glance (143 words total)."
          },
          {
            "where": "requirement→owner table, R5 row",
            "quote": "030, using evidence built by 010 and content evidence from 020",
            "why": "Even the longest cell stays a short, traceable dependency chain because the table layout, not prose, carries the mapping."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/000-main.md — Requirement questions": {
        "grade": "readable",
        "findings": [
          {
            "where": "Q1 bullet",
            "quote": "Q1 (blocks execution of 010 and everything downstream) — What is the exact schema of the structured multi-author form?",
            "why": "The only open question is front-loaded with its blocking scope, so the decision-relevant fact lands first; the recommendation, alternative, and blast radius that follow stay inside one short 67-word item."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/000-main.md — Supporting facts": {
        "grade": "partial",
        "findings": [
          {
            "where": "second bullet",
            "quote": "A repo-wide search for `author` finds every consumer: `_includes/layouts/post.njk:2` (`<p class=\"author\">{{ author }}</p>`), `content/feed.xml.njk:5` (`<entry><author>{{ post.data.author }}</author>` per post), `scripts/new-post.js:1-2` (emits `author: \"...\"` front matter)",
            "why": "A four-consumer inventory flattened into a single bullet; pairing each path with its snippet and role requires re-scanning instead of reading a sub-list, and this section carries 31 code spans in 7 items."
          },
          {
            "where": "fifth bullet",
            "quote": "`npm run build` (Eleventy 3, input `content/`, includes `_includes/`, output `_site/`; feed `/feed/feed.xml`, archive `/blog/`, tag pages `/tags/<slug>/`)",
            "why": "Six build facts are packed into nested parentheses inside one item; the route inventory is load-bearing for verification but buried in punctuation."
          },
          {
            "where": "third bullet",
            "quote": "Adding author display to archives would be new scope and is not planned (recommendation)",
            "why": "A scope decision sits at the end of a bullet that starts as a factual observation, so the reader meets a plan decision inside a section titled 'Supporting facts'."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/000-main.md — Execution plan": {
        "grade": "partial",
        "findings": [
          {
            "where": "design paragraph",
            "quote": "normalize author data once at the data layer so templates consume a single normalized form (see 010 for the design), and keep the canonical rendered form for a single author byte-identical to today's legacy output. That equivalence is what makes the migration provably safe and the R5 gate decidable by comparison rather than judgment.",
            "why": "The section's longest paragraph (~59 words) chains mechanism, equivalence claim, and gate consequence in a single pass; it is the one spot that must be re-read."
          },
          {
            "where": "stage paragraphs vs. rest of the file",
            "quote": "Stage 3 (subtask 030): re-verify the gate fresh (content scan + consumer inventory + passing build), then remove legacy compatibility and reject the legacy form in the build and the authoring tool",
            "why": "At 678 words the plan re-narrates material the Subtasks table, R5, the risks, and the subtask files already state; the reader must skim past repeated gate and stage stories to reach what is new here (ordering rule, decisive checks, risks)."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/010-structured-authors-adoption.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "second and third checkboxes",
            "quote": "posts still using the legacy field render byte-identical to current output (`<p class=\"author\">Ada Example</p>` for `content/posts/first.md`)",
            "why": "Six of seven boxes pair exactly one requirement with its concrete expected output string, which is what keeps the 162-word list scannable."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/010-structured-authors-adoption.md — Supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "fifth bullet",
            "quote": "post page `<p class=\"author\">Ada Example</p>`; feed `<feed><entry><author>Ada Example</author></entry><entry><author>Grace Example</author></entry></feed>`",
            "why": "The expected legacy output strings and their provenance caveat share one item, but the item is short and the strings are precisely what stages 2 and 3 pin — no re-reading needed."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/010-structured-authors-adoption.md — Execution plan": {
        "grade": "partial",
        "findings": [
          {
            "where": "Evidence bullet",
            "quote": "The multi-author case runs through a temporary post in a sandboxed copy of the content/config (no permanent content changes, no test-only build shortcuts); harness details are an implementation choice.",
            "why": "One ~70-word bullet mixes the coverage list (legacy unchanged, structured rendering, archives), the sandbox mechanism, two constraints, and an explicitly open choice; separating settled from open takes a second pass."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/020-content-migration.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "third checkbox",
            "quote": "Generated output after migration is unchanged versus the pre-migration output: post page author lines and feed author elements stay identical (proven by the production-build assertions from 010, now exercising the structured path).",
            "why": "Each of the five boxes states a single checkable claim with its proof pointer; at 112 words this is the lightest checklist in the set."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/020-content-migration.md — Supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "first bullet (nested list)",
            "quote": "Current front matter to migrate: `content/posts/first.md`: `author: \"Ada Example\"`",
            "why": "The file→value mapping is a sub-list rather than prose, so the migration targets are readable at a glance; the remaining three bullets each carry one short point."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/020-content-migration.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "second plan bullet",
            "quote": "The 010 build-output assertions (which pin the exact legacy-era author strings) must pass after migration — passing through the structured path is the output-unchanged proof for this stage.",
            "why": "The stage's one load-bearing mechanism gets its own sentence, and the five numbered tasks mirror the bullets 1:1; 317 words with no dense paragraph."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/030-legacy-rejection.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "first checkbox (Gate)",
            "quote": "Gate (precondition, verified fresh at the start of execution, not assumed from earlier stages): content scan shows no legacy `author` field; the consumer inventory shows every author consumer (post layout, feed, authoring tool) operating on the structured model and archives free of legacy dependence; the latest production build and full test suite pass. Execution stops if any check fails.",
            "why": "The heaviest box in the set (~55 words) but its three checks are parallel semicolon clauses with the stop rule last, so it reads as an inline checklist rather than a wall; the remaining six boxes are one claim each."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/030-legacy-rejection.md — Supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "second bullet",
            "quote": "After 020, no content uses `author`; after 010, templates and the tooling read the normalized structured form. The remaining legacy dependence is the compatibility normalization itself — which is exactly what this stage removes.",
            "why": "A three-step inference in one item, but each clause is short and the conclusion names the stage's actual target; the whole section is 147 words."
          }
        ]
      },
      "tasks/20260926-author-metadata-migration/030-legacy-rejection.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "lead bullets and Execution tasks 1–7",
            "quote": "1. Fresh gate verification (content scan + consumer inventory + build/tests); record evidence.",
            "why": "Each labeled bullet carries one action with its mechanism, and the numbered task list restates them 1:1, giving two easy-to-follow views of the same 7 steps with no prose paragraph longer than a sentence."
          }
        ]
      }
    },
    "navigation": {
      "grade": "navigable",
      "findings": [
        {
          "where": "all four files",
          "quote": "## Requirements checklist ... ## Supporting facts ... ## Execution plan",
          "why": "Every file uses the same heading skeleton with 'Status: Draft' in the same position, so a reader can jump to outcome, evidence, and plan state by structure alone."
        },
        {
          "where": "000-main.md — Subtasks table",
          "quote": "| Requirement | Owner |",
          "why": "The requirement→owner table routes any constraint (e.g. the R5 evidence gate) to the subtask that enforces it, and each subtask's verification section points back to parent R-numbers."
        },
        {
          "where": "030-legacy-rejection.md — header",
          "quote": "Depends On: tasks/20260926-author-metadata-migration/010-structured-authors-adoption.md",
          "why": "Zero-padded filenames plus explicit Depends On lines in every subtask make the strict 010→020→030 order discoverable without reading the plan prose."
        },
        {
          "where": "000-main.md — intro and Requirement questions",
          "quote": "Planning only: no implementation has been requested or performed yet.",
          "why": "Overall plan status is stated up front, and the single open question sits in its own section labeled with its blocking scope, so status and open question are both one scan away."
        }
      ]
    },
    "mistakes": [
      {
        "where": "000-main.md — Requirements checklist, R3",
        "quote": "the archive surfaces (`content/blog.njk`, `content/tag-pages.njk`, `_includes/postslist.njk`, `content/index.njk`), which today render no author and therefore must keep building correctly with multi-author data and not depend on legacy",
        "why": "List item mixing several facts: one checkbox bundles the requirement, seven file paths, and a conditional clause whose antecedent must be re-parsed — it initially reads as if all consumers must 'not depend on legacy'."
      },
      {
        "where": "000-main.md — Supporting facts, second bullet",
        "quote": "A repo-wide search for `author` finds every consumer: `_includes/layouts/post.njk:2` (`<p class=\"author\">{{ author }}</p>`), `content/feed.xml.njk:5` (`<entry><author>{{ post.data.author }}</author>` per post), `scripts/new-post.js:1-2` (emits `author: \"...\"` front matter)",
        "why": "A four-entry consumer inventory flattened into prose-in-a-bullet; a sub-list or table would pair path, snippet, and role 1:1 instead of forcing re-scanning."
      },
      {
        "where": "000-main.md — Supporting facts, fifth bullet",
        "quote": "`npm run build` (Eleventy 3, input `content/`, includes `_includes/`, output `_site/`; feed `/feed/feed.xml`, archive `/blog/`, tag pages `/tags/<slug>/`)",
        "why": "Buried load-bearing facts: the output and route locations a verifier needs are stacked inside nested parentheses rather than given their own lines."
      },
      {
        "where": "000-main.md — Supporting facts, third bullet",
        "quote": "Adding author display to archives would be new scope and is not planned (recommendation)",
        "why": "Heading/content mismatch: a scope decision and recommendation appear under 'Supporting facts' and are repeated under 'Implementation decisions and open questions', so decisions live in two places."
      },
      {
        "where": "000-main.md — Execution plan, ordering paragraph",
        "quote": "Ordering is strict: 010 → 020 → 030, declared as dependencies in the subtask files. Every permitted execution order is safe because 020 requires 010's model and evidence, and 030 requires both.",
        "why": "The first sentence fixes exactly one order while the second discusses 'every permitted execution order' as if several exist; the reader must stop and reconcile the two framings."
      },
      {
        "where": "000-main.md — Execution plan, Requirement verification R1 bullet",
        "quote": "R1, R2, R3 — production build plus build-output assertions added in 010: legacy posts render the current author line and feed element unchanged; a structured multi-author fixture renders the approved form on the post page and feed through the real build; archives still build.",
        "why": "Three requirements and four distinct checks compressed into one item; mapping which check verifies which requirement takes a second pass."
      },
      {
        "where": "010-structured-authors-adoption.md — Requirements checklist, sixth box",
        "quote": "Production-build generated-output tests assert author rendering for both legacy and structured posts on post pages and feed, replacing the placeholder comments in `tests/author-output.test.js`; the archive build check is also real (`tests/archive-output.test.js`).",
        "why": "The only box that bundles three facts (new coverage, placeholder replacement, second file's status), breaking the one-requirement-per-box pattern the other six boxes follow."
      },
      {
        "where": "010-structured-authors-adoption.md — Execution plan, Evidence bullet vs. Implementation decisions",
        "quote": "The exact mechanism is an implementation choice as long as it runs in the real build path",
        "why": "The plan defers the normalization mechanism while the decisions subsection in the same section recommends 'directory computed data in `content/posts/posts.json` (recommended)'; the reader must reconcile 'open choice' with 'recommended' to know what is settled."
      },
      {
        "where": "030-legacy-rejection.md — Supporting facts, fourth bullet",
        "quote": "A warning-only acceptance would leave a silent dependency path and would not satisfy \"rejected\"; the recommendation is a hard build failure.",
        "why": "Reasoning, recommendation, and its approval status sit under 'Supporting facts' and are restated almost verbatim in 'Implementation decisions and open questions' — the same decision must be read twice."
      }
    ],
    "summary": "The set is navigable: all four files share one skeleton (outcome intro, Parent/Depends On, Requirements checklist, Supporting facts, Execution plan with fixed subsections), the R→owner table routes every constraint to its enforcing subtask, zero-padded filenames plus Depends On lines expose the strict order, Q1 and 'Planning only / Status: Draft' are one scan away. Readability strain concentrates in 000-main, the densest file: its 224-word checklist folds seven paths plus an archive clause into R3 and two requirements into R5, two Supporting-facts bullets flatten four-consumer and six-fact inventories into parenthetical prose, and the 678-word plan re-narrates the subtasks with a 59-word design paragraph and multi-requirement verification items. 010's only dense spot is its Evidence bullet; 020 and 030 read cleanly throughout because their items carry one claim each and their plans pair short bullets with 1:1 task lists. Recurring presentation issue: plan decisions and recommendations surfacing under the 'Supporting facts' heading (000-main archives scope, 030 hard-failure), blurring facts and decisions."
  }
}
```
