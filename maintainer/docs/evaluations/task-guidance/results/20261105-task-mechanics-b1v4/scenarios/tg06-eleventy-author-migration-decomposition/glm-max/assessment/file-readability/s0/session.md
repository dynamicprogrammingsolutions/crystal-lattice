# Session — tg06-eleventy-author-migration-decomposition · file-readability-assessment-glm-max-s0 · glm max

- Run: `20261102T110313.526443Z-task-guidance-file-readability-tg06-eleventy-author-migration-decomposition-glm-max-s0-29814ff1`
- Model: glm-5.3-flash (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-c440c4f661a7.md) — captured (original SHA-256 `25ff2e593f6025de…`)
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

#### tasks/20261102-multi-author-migration/000-main.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261102-multi-author-migration/000-main.md — Requirements checklist | 219 | 0 | 0 | 7 | 12 | 0 | 0 | 0 | 3 |
| tasks/20261102-multi-author-migration/000-main.md — Questions and decisions | 168 | 1 | 131 | 4 | 12 | 0 | 0 | 4 | 3 |
| tasks/20261102-multi-author-migration/000-main.md — Subtasks | 104 | 1 | 52 | 2 | 1 | 0 | 0 | 0 | 3 |
| tasks/20261102-multi-author-migration/000-main.md — Supporting details | 179 | 1 | 6 | 6 | 9 | 0 | 0 | 0 | 32 |

#### tasks/20261102-multi-author-migration/010-structured-author-adoption.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261102-multi-author-migration/010-structured-author-adoption.md — Requirements checklist | 180 | 0 | 0 | 7 | 12 | 0 | 0 | 0 | 11 |
| tasks/20261102-multi-author-migration/010-structured-author-adoption.md — Implementation plan | 1140 | 7 | 72 | 32 | 14 | 8 | 0 | 0 | 66 |

#### tasks/20261102-multi-author-migration/020-legacy-author-rejection.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261102-multi-author-migration/020-legacy-author-rejection.md — Requirements checklist | 148 | 0 | 0 | 5 | 11 | 0 | 0 | 0 | 3 |
| tasks/20261102-multi-author-migration/020-legacy-author-rejection.md — Implementation plan | 566 | 5 | 50 | 18 | 14 | 5 | 0 | 0 | 9 |

The produced task files:

### tasks/20261102-multi-author-migration/000-main.md

````markdown
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
````

### tasks/20261102-multi-author-migration/010-structured-author-adoption.md

````markdown
# Structured author adoption

Parent Task: tasks/20261102-multi-author-migration/000-main.md

Introduce the structured `authors` model as the single canonical form of post
author data, switch every consumer to it, migrate the two existing posts, keep
legacy-form posts working through one normalization point, and establish the
generated-output evidence and tests that the later rejection step (020) is
gated on.

## Requirements checklist

- [ ] `_includes/layouts/post.njk` and `content/feed.xml.njk` render only from
  the structured `authors` model, and `scripts/new-post.js` emits only the
  structured form; the transition normalization accessor is the only code
  aware of the legacy `author` field.
- [ ] A post carrying only the legacy `author` string builds and renders with
  output identical to the same post expressed in structured form; the
  legacy→structured mapping lives in exactly one shared place.
- [ ] The production build over the current two posts produces output
  identical to the pre-migration baseline across every generated page.
- [ ] Both existing posts use only the structured form and no legacy
  `author:` remains anywhere under `content/`.
- [ ] A multi-author post renders every author in the post-page byline and
  one `<author>` element per author in the feed, verified through a
  production build of a temporary fixture.
- [ ] `tests/` contains generated-output coverage for author rendering —
  real-content single-author pages and feed, fixture multi-author, fixture
  legacy equivalence — and `npm test` collects and passes it.
- [ ] Maintained documentation states the supported author front-matter model.

## Implementation plan

Status: Draft

### Design

Data flow: front matter (`authors`, or legacy `author` while tolerated) →
Eleventy data cascade → one normalization accessor guarantees page data always
exposes `authors` as the structured list → `post.njk` renders the byline from
it, `feed.xml.njk` emits one `<author>` per entry. The accessor never changes
rendered output; templates never see the legacy field.

Normalization accessor (recommended): convert `content/posts/posts.json` to
`content/posts/posts.11tydata.js`, keeping the existing `layout` and `tags`
and adding `eleventyComputed.authors` that returns the structured value when
present and otherwise derives `[{ name: <legacy string> }]`. The accessor
handles both keys explicitly rather than relying on Eleventy's data-precedence
semantics. Accepted fallback: keep `posts.json` and add an `authors` Nunjucks
filter in `eleventy.config.js` that every template calls — functionally fine,
but it spreads the compat rule across call sites.

Rendering: the post byline joins author names; a single author must produce
exactly the current text (e.g. `Ada Example`). Multi-author join is new
display behavior — recommend `", "` (deterministic, scales past two authors).
The feed emits `<author>{{ a.name }}</author>` per entry, which for
single-author posts reproduces the current element exactly.

Authoring tool: `frontMatter(title, authors)` takes the structured list and
emits block-style `authors:` YAML matching the content convention, so script
output and hand-written front matter agree.

Verification strategy: the decisive evidence is the production build compared
against a pre-change baseline. Permanent regression coverage lives in tests
that invoke the real build into disposable output directories.

### Order and rationale

1. `npm install`; run the production build; record the baseline `_site` output
   (gitignored path or temp dir outside the repo) plus the exact
   author-bearing expectations (byline text per post page, feed `<author>`
   contents, full page set). Stop-safe point: nothing changed yet.
2. Add the accessor; switch `post.njk` and `feed.xml.njk` to consume
   `authors`. Content is still legacy, so the accessor supplies everything.
   Build; full comparison against the baseline must be identical.
3. Migrate `first.md` and `second.md` to the structured form. Build; compare —
   identical. Content evidence now exists: zero legacy `author:` under
   `content/`.
4. Update `scripts/new-post.js` to the structured interface.
5. Tests. Rework `tests/author-output.test.js` to run the production build on
   the real content and assert (a) both post pages' byline text and (b) the
   feed's `<author>` contents. For multi-author and legacy-equivalence cases,
   build a temporary fixture site through the real pipeline: a fixture input
   dir with its own minimal `eleventy.config.js` pointing `includes` at the
   repo `_includes` (absolute path), with `content/feed.xml.njk` copied into
   the fixture at test runtime from the live file so the template cannot
   drift. Builds go to disposable output dirs; fixture dirs are removed in
   teardown. Extend `tests/archive-output.test.js` minimally to assert the
   archive lists both migrated posts (archives unaffected).
6. Documentation: add a short front-matter note stating the supported
   `authors` model (recommended: `README.md` — the site currently documents
   only build outputs, and no front-matter doc exists to update).
7. Final production build + full baseline comparison + `npm test`; confirm
   clean exits and record the evidence 020 is gated on in Implementation
   notes.

Milestones 1–3 are safe stopping points; the state after milestone 3 — fully
migrated, legacy still tolerated, evidence recorded — is independently
acceptable and is what unblocks 020.

### Risks and way back

- Divergent normalization (template and accessor disagreeing about the model):
  mitigated by the single-accessor rule and the legacy-equivalence test.
- Eleventy computed-data precedence surprises: the accessor handles both keys
  explicitly, so correctness does not depend on precedence; the fixture test
  catches regressions.
- Baseline drift from nondeterminism: author-bearing templates contain no
  dates or random values; any diff outside author-bearing surfaces is a defect
  to explain, not noise to accept.
- Test leftovers: fixture/temp artifacts must be created under gitignored or
  teardown-removed paths so a failed run cannot dirty the tree.
- Blast radius: two templates, one script, two posts, tests, docs — all
  git-tracked. Rollback is reverting the change; no persisted or external
  state exists beyond the repository.

### Implementation decisions and open questions

- Adopted locally (reversible): block-style YAML for `authors` in content;
  `", "` byline join for multi-author display; `frontMatter(title, authors)`
  signature; accessor via `posts.11tydata.js`. These affect only new
  multi-author output or the in-repo-unused script interface; existing
  rendered output is pinned by the baseline comparison.
- Blocked on the main task's pending decision: final data shape (adds or
  changes `url` handling). Execution must not start before it is confirmed;
  this plan is Draft until then. The rejection mechanism is 020's concern.
- Open questions: none local.

### Documentation

- Audience: content authors and maintainers of this fixture. Requirement: the
  supported `authors` front-matter model is documented where authoring is
  documented — recommended: a short "Post front matter" note in `README.md`,
  per `docs/development/documentation.md` (smallest structure that helps the
  reader; claim lands in the same reviewed change as the code). In this phase
  the legacy form is still tolerated; docs describe the structured form as the
  supported model and may note the transition tolerance.

### Task checklist

- [ ] Install dependencies; production build; record baseline output and
  author-bearing expectations.
- [ ] Add the single normalization accessor for legacy→structured authors.
- [ ] Switch `_includes/layouts/post.njk` and `content/feed.xml.njk` to
  consume `authors`; build and confirm output identical to baseline.
- [ ] Migrate `content/posts/first.md` and `content/posts/second.md`; build
  and confirm identical; confirm zero legacy `author:` under `content/`.
- [ ] Update `scripts/new-post.js` to emit the structured form.
- [ ] Implement generated-output tests (real-content single-author, fixture
  multi-author, fixture legacy equivalence) and minimal archive coverage.
- [ ] Document the supported author model.
- [ ] Final build + full comparison + `npm test`; record the evidence 020 is
  gated on.

### Requirement verification

- Structured model is canonical (req 1): code inspection — the only remaining
  `author` reference is the accessor; decisive check is the baseline
  comparison below through the production build.
- Transition tolerance (req 2): fixture build through the real pipeline —
  legacy-only post output equals the structured equivalent (byline and feed
  element compared).
- Existing output unchanged (req 3): full `_site` comparison against the
  pre-change baseline after the template switch, after content migration, and
  at the final build — the named decisive check for this subtask.
- Content migrated, nothing lost (req 4): repo scan showing zero legacy
  `author:` under `content/`, plus the identical-output comparison proving no
  rendered loss.
- Multi-author rendering (req 5): production build of the two-author fixture;
  assert both names in the byline and two `<author>` elements in the feed.
- Regression coverage (req 6): `npm test` collects the new tests and exits
  cleanly; tests exercise the real build, not mocks.
- Documentation (req 7): the documented section reviewed against the
  implemented model.

Deliberately not covered: zero-author posts (behavior unspecified — no
requirement invented); URL/sitemap/feed structure beyond the author element
(no change planned); fixture templates other than the runtime-copied feed and
the repo `_includes` layout (real templates are covered by the real-content
assertions).

### Additional implementation verification

- Confirm the final `npm test` run actually collected the new tests (count or
  per-file output), guarding the real failure mode of this repo today: empty
  placeholder test files that pass without testing anything.
````

### tasks/20261102-multi-author-migration/020-legacy-author-rejection.md

````markdown
# Legacy author rejection

Parent Task: tasks/20261102-multi-author-migration/000-main.md

Depends On: tasks/20261102-multi-author-migration/010-structured-author-adoption.md

Flip the compatibility state after 010's evidence is re-confirmed: stop
accepting the legacy `author` form, remove the transition normalization, and
verify both the rejection and that the migrated site's output is unchanged.

## Requirements checklist

- [ ] The gate is honored: the flip is executed only after re-confirming
  (a) content evidence — zero legacy `author:` occurrences under `content/` —
  and (b) generated-output evidence — 010's build comparison against the
  baseline still holds; the evidence is recorded before the flip.
- [ ] The transition normalization is removed: no template, script, data
  file, or test maps or reads the legacy `author` field anywhere.
- [ ] Legacy-form input is rejected per the approved mechanism (main task
  recommendation: production build fails with an error naming the offending
  file), verified by building a temporary legacy-form fixture and asserting
  the approved observable outcome.
- [ ] The migrated production content still builds and every existing page's
  output remains identical to the baseline recorded in 010.
- [ ] Documentation no longer presents the legacy form as supported and
  states the rejection behavior where it is user-visible.

## Implementation plan

Status: Draft

Design: replace the accessor's legacy fallback (010's `eleventyComputed.authors`
derivation, or the equivalent filter) with the approved rejection behavior, in
one coherent change together with the test and documentation updates. After
this subtask, page data contains only structured `authors`, and supplying
legacy `author:` produces the approved outcome instead of silent tolerance.

Order and rationale:

1. Re-confirm the gate (read-only checkpoint; record dated evidence in
   Implementation notes): content scan — zero legacy `author:` under
   `content/`; `npm test` on the migrated site passes; spot-check 010's
   baseline comparison expectations still describe current output. If anything
   still depends on the legacy form, stop and report — do not reject.
2. Flip: remove the normalization fallback, implement the approved rejection,
   retire 010's legacy-equivalence fixture test (it would fail by design) and
   replace it with the rejection test, update documentation — all in one
   change so no intermediate state claims the wrong contract.
3. Verify: production build over migrated content compared against 010's
   baseline must be identical; production build of a legacy-form fixture must
   produce the approved outcome (nonzero exit and error naming the file, or
   the alternative if that is what was approved); `npm test` collects and
   passes everything. If the comparison fails, revert the flip and report the
   dependency that surfaced — the gate did its job.

Stop-safe: step 1 is read-only. Steps 2–3 are a single reversible change;
reverting restores 010's tolerated state.

Risks: a consumer outside the repository or added later regresses (assumption:
the repository is the complete scope — no external consumers identified during
planning); removing the accessor subtly changes data shape (mitigated by the
full-output comparison). Way back: revert the single change; legacy tolerance
returns.

### Implementation decisions and open questions

- The rejection mechanism is the main task's pending material decision; this
  subtask executes whichever mechanism is approved (recommendation recorded
  there: loud build error naming the file).
- Adopted locally: the rejection test runs through the production build on a
  temporary fixture — the real path, not a unit-level shim.
- Open questions: none local.

### Documentation

- Same change as the flip: wherever 010 documented the author model, state
  that the legacy single-name form is no longer accepted and describe what
  happens when it is supplied. Audience unchanged: content authors and
  maintainers of this fixture.

### Task checklist

- [ ] Re-confirm gate evidence (content scan, test run, baseline comparison
  currency) and record it before the flip.
- [ ] Remove the normalization fallback; implement the approved rejection.
- [ ] Replace 010's legacy-equivalence test with the rejection-evidence test.
- [ ] Build migrated content; confirm output identical to baseline.
- [ ] Build the legacy fixture; confirm the approved observable outcome.
- [ ] Update documentation; `npm test` collects and passes everything.

### Requirement verification

- Gate honored: dated Implementation-notes record of the step-1 evidence,
  written before the flip — decisive for ordering.
- Normalization removed: repo scan — no code path reads or maps the legacy
  field.
- Rejection works: production build of the legacy fixture produces the
  approved observable outcome.
- No regression: full-output comparison identical to 010's baseline;
  `npm test` exits cleanly with all tests collected.

Deliberately not covered: multi-author rendering (owned and evidenced by 010;
unchanged here); tooling outside this repository (assumed none).

### Additional implementation verification

- After the flip, run one full production build of the pristine repository
  state (no fixture input) and confirm the generated page set is exactly the
  baseline set — guards against the rejection change accidentally excluding
  or reordering pages.
````


**Assistant** *(reasoning present)*

```json
{
  "schema_version": 1,
  "scenario_id": "tg06-eleventy-author-migration-decomposition",
  "assessment": {
    "sections": {
      "tasks/20261102-multi-author-migration/000-main.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "whole section, owner tags on all 7 items",
            "quote": "(Owner: 010) ... (Owners: 010, 020)",
            "why": "Each box carries exactly one requirement plus an explicit owner, so 219 words scan as seven assignable one-line facts rather than a wall; nothing must be re-read."
          },
          {
            "where": "second checklist item",
            "quote": "All generated surfaces (post pages, home, archive, tag pages, feed, sitemap) build and render correctly under the new model",
            "why": "The six-surface enumeration is the densest moment, but it is a flat list of short names inside one clearly stated requirement; one read suffices."
          }
        ]
      },
      "tasks/20261102-multi-author-migration/000-main.md — Questions and decisions": {
        "grade": "readable",
        "findings": [
          {
            "where": "second bullet (rejection decision)",
            "quote": "Recommendation: active rejection — the production build fails with an error naming the offending file; silently ignoring the field would let content regress unnoticed. This decides subtask 020's mechanism; confirm before approving 020.",
            "why": "One item stacks the decision, the recommendation, the counter-rationale, and the downstream gate; the 'Pending/Recommendation' lead-in and the short closing gate sentence keep it extractable in a single read."
          },
          {
            "where": "first bullet (data-shape decision)",
            "quote": "Recommendation: `authors` as a YAML list of entries with required `name` and optional `url`, in block style",
            "why": "The 3-line fenced YAML example directly under the recommendation anchors the abstract shape in concrete form, so the reader never reconstructs the proposal from prose alone."
          }
        ]
      },
      "tasks/20261102-multi-author-migration/000-main.md — Subtasks": {
        "grade": "readable",
        "findings": [
          {
            "where": "order-rationale paragraph under the two subtask links",
            "quote": "020 is the compatibility-state flip and remains blocked if 010's evidence shows a remaining dependency, so it can be deferred or reported separately without reopening 010.",
            "why": "The load-bearing ordering constraint gets its own short paragraph immediately beneath the two subtask links; at 104 words the section loses nothing and hides nothing."
          }
        ]
      },
      "tasks/20261102-multi-author-migration/000-main.md — Supporting details": {
        "grade": "readable",
        "findings": [
          {
            "where": "first bullet (legacy-author inventory)",
            "quote": "`_includes/layouts/post.njk:2` renders `{{ author }}`; `content/feed.xml.njk:5` renders one `<author>{{ post.data.author }}</author>` per post; `scripts/new-post.js` emits `author: \"<name>\"` via `frontMatter(title, author)`; content: `content/posts/first.md` (`Ada Example`) and `content/posts/second.md` (`Grace Example`)",
            "why": "One bullet carries the whole inventory — template, feed, script, and two content files — chained by semicolons; the segments are short enough to scan and the topic label is upfront, but isolating a single location means unpicking the chain."
          },
          {
            "where": "fourth bullet (placeholder tests)",
            "quote": "Because empty test files pass, evidence must confirm tests actually collected and ran.",
            "why": "The load-bearing caveat lands as the final clause of a bullet that first lists two placeholder files and the trivially-passing test run; a reader skimming for the test risk gets it, but only after parsing the inventory above it."
          },
          {
            "where": "whole section",
            "quote": "Facts from inspection (20261102, repo-wide search):",
            "why": "Six labeled, topic-per-bullet inspection facts with precise code spans; 32 code spans in 179 words is dense but that density is the point of an evidence section, and each bullet has one topic."
          }
        ]
      },
      "tasks/20261102-multi-author-migration/010-structured-author-adoption.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "sixth checklist item (test coverage)",
            "quote": "`tests/` contains generated-output coverage for author rendering — real-content single-author pages and feed, fixture multi-author, fixture legacy equivalence — and `npm test` collects and passes it.",
            "why": "Three test cases ride inside one em-dash parenthetical; it stays a single requirement and reads in one pass, but it is the tightest packing in the section."
          },
          {
            "where": "whole section",
            "quote": "`_includes/layouts/post.njk` and `content/feed.xml.njk` render only from the structured `authors` model, and `scripts/new-post.js` emits only the structured form",
            "why": "Seven one-requirement boxes with exact file paths in code spans; each item is verifiable on its own, which keeps 180 words easy to hold."
          }
        ]
      },
      "tasks/20261102-multi-author-migration/010-structured-author-adoption.md — Implementation plan": {
        "grade": "partial",
        "findings": [
          {
            "where": "Order and rationale, step 5 (Tests)",
            "quote": "For multi-author and legacy-equivalence cases, build a temporary fixture site through the real pipeline: a fixture input dir with its own minimal `eleventy.config.js` pointing `includes` at the repo `_includes` (absolute path), with `content/feed.xml.njk` copied into the fixture at test runtime from the live file so the template cannot drift.",
            "why": "A ~120-word list item mixes what the tests assert with a six-part fixture recipe (input dir, config, includes path, runtime template copy, drift rationale, disposable outputs plus teardown) and then tacks on the archive extension; an implementer must re-read it to separate assertions from fixture mechanics."
          },
          {
            "where": "Design, second paragraph (normalization accessor)",
            "quote": "Accepted fallback: keep `posts.json` and add an `authors` Nunjucks filter in `eleventy.config.js` that every template calls — functionally fine, but it spreads the compat rule across call sites.",
            "why": "One paragraph carries the recommendation, its mechanics, the data-precedence rationale, and a second accepted option with its drawback; the fallback is load-bearing (an implementer may need the alternative) but is buried mid-paragraph rather than set off."
          },
          {
            "where": "Requirement verification, closing paragraph",
            "quote": "Deliberately not covered: zero-author posts (behavior unspecified — no requirement invented); URL/sitemap/feed structure beyond the author element (no change planned); fixture templates other than the runtime-copied feed and the repo `_includes` layout (real templates are covered by the real-content assertions).",
            "why": "Three scope exclusions, each with its own rationale, share one sentence; answering 'is X covered?' requires parsing semicolon-separated clauses with nested parentheticals."
          },
          {
            "where": "subsection skeleton of the whole plan",
            "quote": "Design ... Order and rationale ... Risks and way back ... Implementation decisions and open questions ... Documentation ... Task checklist ... Requirement verification ... Additional implementation verification",
            "why": "Eight intent-revealing subsections are what keep 1140 words workable — a reader can jump straight to risks, decisions, or the checklist; the strain sits inside the subsections, not between them."
          }
        ]
      },
      "tasks/20261102-multi-author-migration/020-legacy-author-rejection.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "first checklist item (the gate)",
            "quote": "(a) content evidence — zero legacy `author:` occurrences under `content/` — and (b) generated-output evidence — 010's build comparison against the baseline still holds",
            "why": "The (a)/(b) letters hold two evidence classes inside one gate requirement without collapsing into prose; each clause is short and the second sentence states when the evidence must exist."
          }
        ]
      },
      "tasks/20261102-multi-author-migration/020-legacy-author-rejection.md — Implementation plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "stop-safety paragraph after the numbered steps",
            "quote": "Stop-safe: step 1 is read-only. Steps 2–3 are a single reversible change; reverting restores 010's tolerated state.",
            "why": "Design, ordering, risks, and stop-safety are run-in labeled paragraphs rather than subsections (unlike 010's headings); at 566 words the plan sits in roughly one screen, so the labels do the job, though a reader pattern-matching 010's structure finds no 'Risks' heading to jump to."
          },
          {
            "where": "Order and rationale, step 2 (Flip)",
            "quote": "Flip: remove the normalization fallback, implement the approved rejection, retire 010's legacy-equivalence fixture test (it would fail by design) and replace it with the rejection test, update documentation — all in one change so no intermediate state claims the wrong contract.",
            "why": "Four distinct work items share one sentence; the closing one-change rationale explains the grouping and the verbs are parallel, so the scope is recoverable in one careful read rather than a re-read."
          }
        ]
      }
    },
    "navigation": {
      "grade": "navigable",
      "findings": [
        {
          "where": "020 header vs 000-main Subtasks",
          "quote": "Depends On: tasks/20261102-multi-author-migration/010-structured-author-adoption.md",
          "why": "The ordering constraint is declared in 020's file header and mirrored in 000-main's Subtasks rationale, so the dependency and the gate are findable without reading any plan body."
        },
        {
          "where": "first line under 'Implementation plan' in both subtask files; 000-main intro",
          "quote": "Status: Draft ... Planning only — no execution has been approved.",
          "why": "Plan status sits at an identical, predictable location in both plans, and the global planning-only state opens the main file; a reader never hunts for status."
        },
        {
          "where": "000-main 'Questions and decisions'; closing bullets of both plans",
          "quote": "Pending (material — persisted content data): ... Open questions: none local.",
          "why": "Open questions carry 'Pending' labels with their blocking consequence, and each plan explicitly declares 'none local', so question state is findable per file from headings and labels alone."
        },
        {
          "where": "020 Implementation plan vs 010 Implementation plan",
          "quote": "Risks: a consumer outside the repository or added later regresses",
          "why": "010 gives Design, Order, and Risks their own headings while 020 flattens them into run-in paragraphs, so the section-to-section navigation pattern breaks slightly between the two subtask files; at this length the cost is small."
        }
      ]
    },
    "mistakes": [
      {
        "where": "010-structured-author-adoption.md — Implementation plan, Order and rationale step 5",
        "quote": "For multi-author and legacy-equivalence cases, build a temporary fixture site through the real pipeline: a fixture input dir with its own minimal `eleventy.config.js` pointing `includes` at the repo `_includes` (absolute path), with `content/feed.xml.njk` copied into the fixture at test runtime from the live file so the template cannot drift.",
        "why": "Wall-like list item: test assertions, fixture construction, the runtime-copy-and-why, output hygiene, teardown, and the archive extension are fused into one bullet; splitting fixture mechanics from assertions (or sub-bulleting the recipe) would remove the only forced re-read in the set."
      },
      {
        "where": "010-structured-author-adoption.md — Implementation plan, Design second paragraph",
        "quote": "Accepted fallback: keep `posts.json` and add an `authors` Nunjucks filter in `eleventy.config.js` that every template calls — functionally fine, but it spreads the compat rule across call sites.",
        "why": "Buried load-bearing fact: an accepted alternative implementation (with the reason the primary is preferred) is embedded as the tail of a paragraph that is otherwise about the recommended accessor; it deserves its own line or bullet."
      },
      {
        "where": "010-structured-author-adoption.md — Implementation plan, Requirement verification closing paragraph",
        "quote": "Deliberately not covered: zero-author posts (behavior unspecified — no requirement invented); URL/sitemap/feed structure beyond the author element (no change planned); fixture templates other than the runtime-copied feed and the repo `_includes` layout (real templates are covered by the real-content assertions).",
        "why": "Three exclusions with individual rationales packed into a single sentence; as bullets, each 'not covered' item would be scannable instead of parsed."
      },
      {
        "where": "020-legacy-author-rejection.md — Implementation plan, Risks paragraph",
        "quote": "Risks: a consumer outside the repository or added later regresses (assumption: the repository is the complete scope — no external consumers identified during planning); removing the accessor subtly changes data shape (mitigated by the full-output comparison).",
        "why": "Buried load-bearing fact: the complete-scope assumption is what licenses ignoring external consumers, yet it sits inside a parenthetical inside the risk clause; two risk bullets plus a one-line way-back would surface it."
      },
      {
        "where": "020-legacy-author-rejection.md — Implementation plan, Order and rationale step 2",
        "quote": "Flip: remove the normalization fallback, implement the approved rejection, retire 010's legacy-equivalence fixture test (it would fail by design) and replace it with the rejection test, update documentation — all in one change so no intermediate state claims the wrong contract.",
        "why": "List item mixing several facts: four work items in one sentence; the one-change rationale justifies the grouping, but enumerating the pieces as sub-points would make the scope checkable at a glance."
      },
      {
        "where": "000-main.md — Supporting details, first bullet",
        "quote": "Complete legacy-`author` inventory: `_includes/layouts/post.njk:2` renders `{{ author }}`; `content/feed.xml.njk:5` renders one `<author>{{ post.data.author }}</author>` per post; `scripts/new-post.js` emits `author: \"<name>\"` via `frontMatter(title, author)`; content: `content/posts/first.md` (`Ada Example`) and `content/posts/second.md` (`Grace Example`).",
        "why": "One bullet mixes four distinct inventory facts (template, feed, script, content) into semicolon chains; a sub-list of locations would let a reader target one consumer without unpicking the line."
      }
    ],
    "summary": "The three files share one consistent template — intro, requirements checklist, plan, task checklist, per-requirement verification — and every short section reads cleanly: single-fact checklist boxes with owner tags, labeled 'Pending' decisions anchored by a fenced YAML example, a two-line subtask map with its ordering rationale, and topic-per-bullet inspection facts. The only strain is 010's 1140-word Implementation plan, graded partial not for its eight intent-revealing subsections but for what is inside them: a ~120-word step-5 fixture recipe fusing assertions with mechanics, Design paragraphs that stack recommendation, rationale, and an accepted fallback into one block, and a one-sentence triple exclusion list. Navigation is navigable from structure alone: 'Status: Draft', 'Depends On', 'Pending (material …)' labels, and mirrored checklists put outcome, constraints, open questions, and plan status at predictable spots. The recurring defect pattern is load-bearing facts embedded in parentheticals or trailing clauses (the accepted normalization fallback, 020's complete-scope assumption, the not-covered list). The uniformly unchecked boxes are not a wall: both plans declare Draft / planning-only status before any checklist, so the unchecked state is explained rather than unexplained."
  }
}
```
