# Session — tg06-eleventy-author-migration-decomposition · file-readability-assessment-glm-max-s0 · glm max

- Run: `20261029T233753.342339Z-task-guidance-file-readability-tg06-eleventy-author-migration-decomposition-glm-max-s0-d1c32e2f`
- Model: glm-5.3-flash (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-c440c4f661a7.md) — captured (original SHA-256 `f283ff637fb1df09…`)
- Config: [glm-assessor-max](../../../../../../shared/configs/glm-assessor-max.json)
- Activity: 3 messages · 0 tool calls · 0 tool results
- Usage: 0 input · 0 cached · 0 output · provider cost $0.0000000

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

#### tasks/20261029-post-author-migration/000-main.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261029-post-author-migration/000-main.md — Requirements checklist | 175 | 0 | 0 | 6 | 14 | 0 | 0 | 0 | 1 |
| tasks/20261029-post-author-migration/000-main.md — Requirement questions and decisions | 143 | 1 | 18 | 4 | 14 | 0 | 0 | 0 | 5 |
| tasks/20261029-post-author-migration/000-main.md — Supporting facts | 149 | 1 | 5 | 11 | 12 | 0 | 0 | 0 | 27 |
| tasks/20261029-post-author-migration/000-main.md — Subtasks | 12 | 0 | 0 | 3 | 1 | 0 | 0 | 0 | 0 |
| tasks/20261029-post-author-migration/000-main.md — Execution plan | 691 | 7 | 51 | 19 | 17 | 4 | 0 | 0 | 12 |

#### tasks/20261029-post-author-migration/010-introduce-multi-author-model.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261029-post-author-migration/010-introduce-multi-author-model.md — Requirements checklist | 173 | 0 | 0 | 6 | 12 | 0 | 0 | 0 | 3 |
| tasks/20261029-post-author-migration/010-introduce-multi-author-model.md — Supporting details | 164 | 0 | 0 | 6 | 12 | 0 | 0 | 0 | 10 |
| tasks/20261029-post-author-migration/010-introduce-multi-author-model.md — Execution plan | 481 | 1 | 61 | 19 | 12 | 5 | 0 | 0 | 16 |

#### tasks/20261029-post-author-migration/020-migrate-existing-posts.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261029-post-author-migration/020-migrate-existing-posts.md — Requirements checklist | 91 | 0 | 0 | 4 | 12 | 0 | 0 | 0 | 3 |
| tasks/20261029-post-author-migration/020-migrate-existing-posts.md — Supporting details | 64 | 0 | 0 | 3 | 13 | 0 | 0 | 0 | 3 |
| tasks/20261029-post-author-migration/020-migrate-existing-posts.md — Execution plan | 250 | 0 | 0 | 17 | 14 | 4 | 0 | 0 | 12 |

#### tasks/20261029-post-author-migration/030-retire-legacy-author.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261029-post-author-migration/030-retire-legacy-author.md — Requirements checklist | 134 | 0 | 0 | 5 | 12 | 0 | 0 | 0 | 2 |
| tasks/20261029-post-author-migration/030-retire-legacy-author.md — Supporting details | 89 | 0 | 0 | 3 | 13 | 0 | 0 | 0 | 0 |
| tasks/20261029-post-author-migration/030-retire-legacy-author.md — Execution plan | 341 | 0 | 0 | 18 | 14 | 4 | 0 | 0 | 6 |

The produced task files:

### tasks/20261029-post-author-migration/000-main.md

````markdown
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
````

### tasks/20261029-post-author-migration/010-introduce-multi-author-model.md

````markdown
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
````

### tasks/20261029-post-author-migration/020-migrate-existing-posts.md

````markdown
# Migrate existing posts to the structured form

Convert all existing post front matter from the legacy single-name `author`
field to the structured multi-author form, proving production-build output
parity for every generated file. The build still accepts the legacy form after
this subtask (retirement is 030); repository content simply no longer uses it.

Parent Task: tasks/20261029-post-author-migration/000-main.md

Depends On: tasks/20261029-post-author-migration/010-introduce-multi-author-model.md

## Requirements checklist

- [ ] Every file in `content/posts/` uses only the structured authors form; no
      legacy `author:` key remains anywhere in `content/`.
- [ ] A production build after the migration is byte-identical to the
      pre-migration build for every generated file (home, archive, tag pages,
      post pages, feed, sitemap).
- [ ] The parity comparison result and the content scan are recorded in this
      task file as the gate evidence later consumed by 030.
- [ ] The full test suite remains green, including the 010 integration pins
      against the migrated content.

## Supporting details

- Only two posts exist: `content/posts/first.md` (Ada Example) and
  `content/posts/second.md` (Grace Example); each becomes a one-element
  structured list per approved D1.
- `_site/` is gitignored; keep baseline snapshots in a temp location outside
  version control and do not commit them.
- This subtask changes only content files. If output parity fails, stop and
  investigate the 010 normalization/model path — do not "fix" templates here.

## Execution plan

Status: Draft

1. Build at the current state and hash every file under `_site/` (baseline
   snapshot in a temp directory).
2. Rewrite the two posts' front matter to the structured form (mechanical
   one-element lists).
3. Rebuild and compare hashes for every generated file; any diff is a defect
   in the model/normalization work — investigate before proceeding.
4. Scan `content/` for the legacy `author:` key (expected: no matches).
5. Run `npm test`; confirm the 010 integration pins still pass against the
   migrated content.
6. Record the parity result, scan result, and suite status in
   `## Implementation Notes` — this is the R5 gate evidence.

### Implementation decisions and open questions

- None new; shape and rendering follow the decisions approved on the parent.

### Documentation

- None: the 010 README wording ("legacy still accepted during migration")
  remains accurate after content migration; it is rewritten in 030.

### Task checklist

- [ ] Baseline build + hash snapshot captured before any content edit.
- [ ] `content/posts/first.md` and `content/posts/second.md` converted.
- [ ] Post-migration hash comparison run — all generated files identical.
- [ ] Legacy-key content scan run — no matches in `content/`.
- [ ] `npm test` green.
- [ ] Gate evidence recorded in `## Implementation Notes` and referenced by
      the parent checklist.

### Requirement verification

- Safe content migration (R4): the hash comparison over the real production
  build output before/after the content edit — decisive, full-surface, no
  mocked rendering.
- Content fully migrated (R4): the repository content scan showing no legacy
  `author:` keys.
- Suite green: `npm test` collects and exits cleanly.
````

### tasks/20261029-post-author-migration/030-retire-legacy-author.md

````markdown
# Retire the legacy author form (evidence-gated)

After reviewing the recorded migration evidence, make the build reject the
legacy single-name `author` form with an actionable error, replace the
temporary dual-acceptance test coverage, and update documentation so the
structured form is documented as the only supported author form.

Parent Task: tasks/20261029-post-author-migration/000-main.md

Depends On: tasks/20261029-post-author-migration/010-introduce-multi-author-model.md, tasks/20261029-post-author-migration/020-migrate-existing-posts.md

## Requirements checklist

- [ ] Gate evidence is reviewed and recorded in this task file before
      rejection is enabled: (a) 020 generated-output parity, (b) 020 content
      scan showing no legacy keys, (c) 010 evidence that
      `scripts/new-post.js` emits only the new form. If any leg is missing,
      stop — rejection must not be enabled.
- [ ] The production build fails with an actionable error (naming the file and
      the fix) when a post still uses the legacy `author` form.
- [ ] Repository content builds cleanly under the strict validation.
- [ ] Temporary dual-acceptance coverage from 010 is replaced: the legacy-form
      acceptance test is removed and rejection coverage added (unit +
      real-build integration); the repo-content pins stay valid.
- [ ] README updated: the structured form is the only supported author form;
      dual-acceptance wording removed.

## Supporting details

- Rejection lives in the shared normalization point added in 010, so the
  production build fails and every consumer of the model shares one rule.
- Out-of-repo consumers of the legacy form (if any) are not observable here;
  the gate covers in-repo content and generated output only. The actionable
  rejection message is the mitigation for unknown external consumers.
- The 010 repo-content pins (author strings on post pages and feed) remain
  valid because 020 proved migrated content renders the same output; only the
  temp-fixture legacy-acceptance test is replaced here.

## Execution plan

Status: Draft

1. Review and record the gate evidence (a–c) in `## Implementation Notes`
   before touching validation.
2. Make the normalization strict: a legacy `author` key present on a post
   throws with a message naming the file and pointing to the structured form,
   so the production build fails.
3. Unit test the strict path; integration test: a temp fixture site with a
   legacy-form post fails the real build with the expected message, and
   repository content still builds cleanly.
4. Remove the 010 temp-fixture legacy-acceptance test; keep all other
   coverage.
5. Rewrite the README authoring section (structured form only).
6. `npm test` and `npm run build` green on repository content; record
   evidence.

### Implementation decisions and open questions

- Resolved (local): enforcement point is the shared normalization module, not
  per-template checks — one rule, and the build fails at the source.
- Enabling rejection after the gate is itself the approved parent outcome
  (R5); no further approval is needed beyond the parent plan approval and the
  recorded gate evidence.

### Documentation

- Rewrite the README "Post authors" section in the same change that enables
  rejection: the legacy form is removed from supported behavior and the
  migration note is deleted.

### Task checklist

- [ ] Gate evidence (a–c) reviewed and recorded before validation changes.
- [ ] Strict validation implemented (actionable build error).
- [ ] Rejection tests added (unit + real-build integration asserting the
      expected message); repo-content real build still green.
- [ ] Temporary legacy-acceptance test removed.
- [ ] README authoring section rewritten (structured form only).
- [ ] `npm test` green; `npm run build` green on repository content; evidence
      recorded.

### Requirement verification

- Rejection behavior (R5): integration test drives the real Eleventy build on
  a temp fixture with a legacy-form post and asserts failure with the
  actionable message; a real build of repository content succeeds.
- Gate honored (R5): the recorded review of parity, scan, and tooling evidence
  in this task file, written before the validation change.
- Documentation current (R6): README shows the structured form as the only
  supported form, changed in the same reviewed change as the strict
  validation.
````


**Assistant** *(reasoning present)*

```json
{
  "schema_version": 1,
  "scenario_id": "tg06-eleventy-author-migration-decomposition",
  "assessment": {
    "sections": {
      "tasks/20261029-post-author-migration/000-main.md — Requirements checklist": {
        "grade": "partial",
        "findings": [
          {
            "where": "R5 checklist item",
            "quote": "The legacy form is rejected by the build with an actionable error, and only after recorded generated-output parity plus content-scan evidence show nothing in content or output still depends on it.",
            "why": "Present-tense 'is rejected' followed by a trailing 'only after...' clause forces a re-read to untangle that rejection does not exist yet and is gated; the load-bearing gate condition is buried in a subordinate clause."
          },
          {
            "where": "R4 checklist item",
            "quote": "All existing post content is migrated to the structured form with production-build output parity proven for every generated file.",
            "why": "Items at ~29 words each (175 words / 6 items) mix the requirement with its proof obligation; a reader must separate 'what must be true' from 'how it will be shown' box by box."
          }
        ]
      },
      "tasks/20261029-post-author-migration/000-main.md — Requirement questions and decisions": {
        "grade": "readable",
        "findings": [
          {
            "where": "D1–D4 list",
            "quote": "D1 (requirement — data shape): structured form shape — list of author name strings vs list of objects (e.g. `{ name, url }`). Recommendation: list of plain name strings",
            "why": "Every decision follows the same 'label — category: question. Recommendation:' pattern, so the 143-word section scans in one pass; the 18-word intro also points readers to where tradeoffs live."
          },
          {
            "where": "D4 item",
            "quote": "recommendation: `authors` takes precedence and legacy is ignored (no error) until 030 enables rejection.",
            "why": "This item bundles the decision, its runtime semantics, and its expiry phase in one line — holdable, but the densest of the four."
          }
        ]
      },
      "tasks/20261029-post-author-migration/000-main.md — Supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "Legacy-form usage inventory bullet",
            "quote": "Legacy-form usage inventory (the complete author dependency surface):",
            "why": "One top-level item carries five nested sub-facts (two content files, template, feed, script, test stub); the nesting is correct, so the 27 code spans stay scannable as one path per line."
          },
          {
            "where": "Build facts item",
            "quote": "Build: Eleventy 3, input `content/`, includes `_includes/`, output `_site/` (gitignored). Commands: `npm run build`, `npm test` (`node --test`).",
            "why": "Several facts per line, but each is a short labelled span; 149 words total keeps the section within one pass."
          }
        ]
      },
      "tasks/20261029-post-author-migration/000-main.md — Subtasks": {
        "grade": "readable",
        "findings": [
          {
            "where": "whole section",
            "quote": "- [ ] tasks/20261029-post-author-migration/010-introduce-multi-author-model.md",
            "why": "12 words, three checkboxes — trivially scannable; the only issue is that the same list reappears verbatim as '### Task checklist' (recorded under mistakes)."
          }
        ]
      },
      "tasks/20261029-post-author-migration/000-main.md — Execution plan": {
        "grade": "partial",
        "findings": [
          {
            "where": "Numbered step 1",
            "quote": "**010 — Introduce the structured model behind dual acceptance.** One shared normalization point feeds the post layout and feed templates; the authoring tool emits the new form; legacy posts keep rendering exactly as today. Real-build integration tests pin both paths, plus a full-output before/after comparison proving the model introduction changed no generated file.",
            "why": "At ~50 words each (longest paragraph 51), the three step paragraphs bundle mechanism, compatibility behavior, and verification in one block; a reader must re-read to separate plan from proof."
          },
          {
            "where": "### Implementation decisions and open questions subsection",
            "quote": "- D1 data shape: recommendation — `authors` as a list of plain name strings.",
            "why": "D1–D4 are restated here after already appearing in the top-level 'Requirement questions and decisions' section, with slightly different wording; the reader must diff two copies to be sure they agree. This subsection drives the section to 691 words — roughly 2–4× any other section here."
          },
          {
            "where": "Prose block before subsections (Approach, steps, Compatibility states, Verification strategy, Risks)",
            "quote": "Compatibility states: after 010 both forms render; after 020 all content uses the new form while legacy is still tolerated; after 030 the legacy form is rejected.",
            "why": "About 400 words of continuous prose precede the four subsections; it is labelled and sequenced well enough to follow, but it is the densest stretch in the corpus and strains a single-pass read."
          }
        ]
      },
      "tasks/20261029-post-author-migration/010-introduce-multi-author-model.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "Fifth checklist item",
            "quote": "Automated evidence: integration tests run the real Eleventy build — repository content, plus a temp fixture site carrying both forms including a multi-author post — and assert rendered post-page and feed output; unit tests cover the normalization point and `frontMatter`.",
            "why": "The densest box (~40 words) mixes three test layers and two build targets; it parses linearly but is the one item a reader slows down for. Other items average ~27 words and stay single-focus."
          },
          {
            "where": "First two checklist items",
            "quote": "(shape per approved D1), and the production build renders single- and multi-author posts on post pages and in the feed per approved D2.",
            "why": "Inline D1/D2/D4 references tie each requirement to its decision record — helpful traceability rather than a burden."
          }
        ]
      },
      "tasks/20261029-post-author-migration/010-introduce-multi-author-model.md — Supporting details": {
        "grade": "readable",
        "findings": [
          {
            "where": "Mechanism sketch item",
            "quote": "a shared module (suggested `lib/authors.js`, outside the Eleventy input dir) exports a normalizer mapping front matter to an authors list — `authors` (list of strings) wins; a legacy `author` string becomes a one-element list (D4). Expose it to templates via Eleventy computed data on the posts collection",
            "why": "One ~60-word bullet covers module location, precedence rule, Eleventy wiring, and the template contract; it strains slightly but the '(implementer may adjust)' framing and 164-word section total keep it workable."
          }
        ]
      },
      "tasks/20261029-post-author-migration/010-introduce-multi-author-model.md — Execution plan": {
        "grade": "partial",
        "findings": [
          {
            "where": "Intro paragraph under 'Status: Draft'",
            "quote": "Capture the output baseline before touching anything: build at the current state and hash every file under `_site/` into a temp directory. Then implement the model, templates, and tooling; rebuild and require a byte-identical comparison. Add the two test layers (unit for the model and generator, integration through the real build for rendering), and update the README in the same change.",
            "why": "At 61 words this is the corpus's longest paragraph, chaining five sequential instructions (baseline, implement, rebuild+compare, two test layers, README) in one block — the subtask's whole sequencing compressed into a single straining paragraph. The 19 list items and five subsections below it recover the structure, which is why this is partial rather than unreadable."
          }
        ]
      },
      "tasks/20261029-post-author-migration/020-migrate-existing-posts.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "whole section",
            "quote": "- [ ] A production build after the migration is byte-identical to the pre-migration build for every generated file (home, archive, tag pages, post pages, feed, sitemap).",
            "why": "91 words across 4 single-focus items, each stating one testable end state with its surface enumeration in parentheses — one pass, nothing to untangle."
          }
        ]
      },
      "tasks/20261029-post-author-migration/020-migrate-existing-posts.md — Supporting details": {
        "grade": "readable",
        "findings": [
          {
            "where": "Third detail item",
            "quote": "If output parity fails, stop and investigate the 010 normalization/model path — do not \"fix\" templates here.",
            "why": "64 words, three items; the failure-handling rule is stated outright instead of buried, which is exactly what a reader of a content-only subtask needs."
          }
        ]
      },
      "tasks/20261029-post-author-migration/020-migrate-existing-posts.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "Numbered steps 1–6",
            "quote": "3. Rebuild and compare hashes for every generated file; any diff is a defect in the model/normalization work — investigate before proceeding.",
            "why": "250 words, no paragraphs, 17 short items: six single-purpose numbered steps plus uniformly short subsection entries. Each step holds one action and one consequence — the cleanest plan section in the set."
          }
        ]
      },
      "tasks/20261029-post-author-migration/030-retire-legacy-author.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "First checklist item",
            "quote": "(a) 020 generated-output parity, (b) 020 content scan showing no legacy keys, (c) 010 evidence that `scripts/new-post.js` emits only the new form. If any leg is missing, stop — rejection must not be enabled.",
            "why": "The gate item runs ~45 words but the explicit (a)–(c) enumeration and the em-dash stop rule keep it holdable; the load-bearing 'must not enable rejection' condition is stated plainly rather than buried."
          }
        ]
      },
      "tasks/20261029-post-author-migration/030-retire-legacy-author.md — Supporting details": {
        "grade": "readable",
        "findings": [
          {
            "where": "Third detail item",
            "quote": "The 010 repo-content pins (author strings on post pages and feed) remain valid because 020 proved migrated content renders the same output; only the temp-fixture legacy-acceptance test is replaced here.",
            "why": "89 words, three items; each states one fact with its justification inline. Slightly dense but each is a single coherent thought."
          }
        ]
      },
      "tasks/20261029-post-author-migration/030-retire-legacy-author.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "Numbered steps 1–6",
            "quote": "1. Review and record the gate evidence (a–c) in `## Implementation Notes` before touching validation.",
            "why": "341 words, no paragraphs, 18 short items; each step is one action, and the evidence-before-change ordering is stated in step 1 and again in the first checklist box, so the critical sequence is hard to miss."
          }
        ]
      }
    },
    "navigation": {
      "grade": "navigable",
      "findings": [
        {
          "where": "All four files, under '## Execution plan'",
          "quote": "Status: Draft",
          "why": "Plan status sits in the same labelled place in every file, so a reader can check approval state without hunting."
        },
        {
          "where": "Subtask headers",
          "quote": "Parent Task: tasks/20261029-post-author-migration/000-main.md — Depends On: tasks/20261029-post-author-migration/010-introduce-multi-author-model.md, tasks/20261029-post-author-migration/020-migrate-existing-posts.md",
          "why": "Explicit parent and dependency lines plus the parent's 'Execution order 010 → 020 → 030 is required' make the cross-file graph recoverable from structure alone."
        },
        {
          "where": "000-main, '### Requirement verification'",
          "quote": "R1 → owned by 010: integration test drives the real Eleventy build on a temp fixture site...",
          "why": "A direct R1–R6-to-subtask map lets a reader route any requirement to its owning file; the same (R#) tags recur in the subtasks' verification subsections."
        },
        {
          "where": "000-main, '## Requirement questions and decisions' vs Execution plan '### Implementation decisions and open questions'",
          "quote": "- D2 (requirement — user-visible output): multi-author rendering. Recommendation: post page joins names with `\", \"`; feed emits one `<author>` element per author",
          "why": "The decisions a reader looks for exist in two places in the same file with non-identical wording, so 'finding the decision' succeeds but confirming which copy is authoritative takes extra comparison."
        }
      ]
    },
    "mistakes": [
      {
        "where": "000-main.md — '## Subtasks' vs '### Task checklist'",
        "quote": "- [ ] tasks/20261029-post-author-migration/020-migrate-existing-posts.md",
        "why": "The identical three-checkbox list appears twice in one file under two headings; a reader tracking completion must check and reconcile both, and the copies can drift."
      },
      {
        "where": "000-main.md — '## Requirement questions and decisions' vs '### Implementation decisions and open questions'",
        "quote": "- D1 (requirement — data shape): structured form shape — list of author name strings vs list of objects ... / - D1 data shape: recommendation — `authors` as a list of plain name strings. Extensible later to objects without re-migrating single-name content.",
        "why": "D1–D4 are recorded twice with different detail and no pointer marking one copy canonical; the reader cannot assume the versions agree and must diff them manually."
      },
      {
        "where": "000-main.md — Requirements checklist, R5",
        "quote": "The legacy form is rejected by the build with an actionable error, and only after recorded generated-output parity plus content-scan evidence show nothing in content or output still depends on it.",
        "why": "A load-bearing gate condition (rejection is conditional on evidence) is buried in a trailing subordinate clause after a present-tense claim, making the item read as if rejection already exists."
      },
      {
        "where": "000-main.md — Execution plan, numbered steps 1–3",
        "quote": "One shared normalization point feeds the post layout and feed templates; the authoring tool emits the new form; legacy posts keep rendering exactly as today. Real-build integration tests pin both paths, plus a full-output before/after comparison proving the model introduction changed no generated file.",
        "why": "Each ~50-word step paragraph merges scope, mechanism, compatibility behavior, and verification into one block — list items that mix several facts and require re-reading to decompose."
      },
      {
        "where": "010-introduce-multi-author-model.md — Execution plan intro paragraph",
        "quote": "Capture the output baseline before touching anything: build at the current state and hash every file under `_site/` into a temp directory. Then implement the model, templates, and tooling; rebuild and require a byte-identical comparison. Add the two test layers (unit for the model and generator, integration through the real build for rendering), and update the README in the same change.",
        "why": "Five sequential instructions compressed into a single 61-word prose paragraph — the longest in the corpus — with no internal list structure; the discrete checklist boxes below exist but the prose itself is a mini-wall."
      },
      {
        "where": "010-introduce-multi-author-model.md — Requirements checklist, fifth item",
        "quote": "Automated evidence: integration tests run the real Eleventy build — repository content, plus a temp fixture site carrying both forms including a multi-author post — and assert rendered post-page and feed output; unit tests cover the normalization point and `frontMatter`.",
        "why": "One unchecked box mixes three coverage layers (repo-content integration, fixture integration, unit) and two build targets; splitting it would let a reader tick off evidence layers independently."
      }
    ],
    "summary": "All four files follow one consistent template — requirements checklist, supporting facts, execution plan with decisions/documentation/checklist/verification subsections — which makes navigation genuinely strong: 'Status: Draft', explicit Parent Task / Depends On lines, the stated 010 → 020 → 030 ordering, and the parent's R1–R6-to-subtask map let a reader locate outcome, constraints, open decisions, and plan status from structure alone. Readability is uniformly solid in the subtasks (020 and 030 sections run 64–341 words with short single-purpose list items); strain concentrates in 000-main, whose 691-word Execution plan restates D1–D4 a second time in non-identical wording, duplicates the subtask list as 'Task checklist', and packs each increment into ~50-word multi-clause step paragraphs, plus 010's single 61-word plan-intro paragraph and a few checklist boxes that bundle requirement, mechanism, and proof. The defects are duplication and density, not missing or misleading structure."
  }
}
```
