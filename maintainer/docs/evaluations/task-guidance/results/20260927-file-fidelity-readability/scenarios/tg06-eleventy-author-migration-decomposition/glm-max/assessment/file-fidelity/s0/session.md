# Session — tg06-eleventy-author-migration-decomposition · file-fidelity-assessment-glm-max-s0 · glm max

- Run: `20260928T194922.630870Z-task-guidance-file-fidelity-tg06-eleventy-author-migration-decomposition-glm-max-s0-af2c3636`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `fc31955686fc4741…`)
- Config: [glm-assessor-max](../../../../../../shared/configs/glm-assessor-max.json)
- Activity: 3 messages · 0 tool calls · 0 tool results
- Usage: unknown — saved session contains no provider usage metadata

## Transcript

**User**

Assess the task files one agent produced for a fixed scenario, together
with that agent's final conversation response. Judge whether the files
carry what a continuing agent and a human reviewer need: the decided
design, the conversation's durable context, content in the right
sections, a plan justified by planning that actually happened, and
acceptance evidence that fits the work's kind.

Grade these dimensions:

- `plan_design_completeness`: a reader of the implementation plan alone
  can reconstruct the decided design — component responsibilities,
  interfaces or data flow, compatibility and dependency states, material
  decisions, and how the requirements are verified. An ordered list of
  work steps without the design behind it is `poor`; covering some
  design elements is `partial`.
- `durable_context_preservation`: every approved outcome, material
  decision, verified fact with its source, and verification approach the
  conversation established appears in the task files — compressed, not
  dropped. Use `not checked here` only when the conversation established
  nothing durable.
- `section_appropriateness`: content sits where a continuing agent looks
  for it — outcomes and constraints in requirements, rationale and
  learned facts in supporting details, direction in the implementation
  plan, unresolved items in questions and decisions.
- `plan_justification`: the implementation plan reflects planning that
  actually happened. `justified` when the plan restates or organizes the
  conversation's planning; `not_applicable` when no plan section exists;
  `fabricated` when the plan asserts design detail the conversation
  never established.
- `task_kind_fit`: the file uses the sections the work needs and states
  acceptance evidence appropriate to the work's kind — tests for code,
  review acceptance for documentation, rollback and verification for
  operations, brief or style acceptance for content, recorded decisions
  for tracking work. `forced` when inapplicable sections are filled
  mechanically; `missing` when the work's own acceptance evidence is
  absent.

Every grade carries findings: concrete `{where, quote, why}` items
backing it. A non-top grade with empty findings is invalid. Then hunt
for mistakes explicitly — dropped facts, invented decisions or scope,
content a continuing agent would look for in the wrong place, missing
acceptance evidence — and list each as `{where, quote, why}` in
`mistakes`. Grades stay completeness judgments; the mistake hunt is
your search strategy, not a grade.

Do not reward verbosity or formatting of its own. Do not penalize
brevity that loses nothing. The target excerpt and the natural user
request define what is material.

Return JSON only:

{
  "schema_version": 1,
  "scenario_id": "tg06-eleventy-author-migration-decomposition",
  "assessment": {
    "dimensions": {
      "plan_design_completeness": {
        "grade": "complete|partial|poor",
        "findings": [{"where": "...", "quote": "...", "why": "..."}]
      },
      "durable_context_preservation": {"grade": "...", "findings": []},
      "section_appropriateness": {"grade": "...", "findings": []},
      "plan_justification": {
        "grade": "justified|not_applicable|fabricated",
        "findings": []
      },
      "task_kind_fit": {"grade": "fits|forced|missing", "findings": []}
    },
    "mistakes": [{"where": "...", "quote": "...", "why": "..."}],
    "summary": "concise evidence-based interpretation"
  }
}

Reviewed target excerpt:

# Eleventy author metadata migration decomposition

Partition a broad content/build migration by compatible working states rather than files and phases.

Category: decomposition

Approved outcomes:

- AUTHOR-1: Legacy single-author and structured one-or-more-author metadata normalize to one documented internal representation during migration.
- AUTHOR-2: Pages, archives, feeds, and metadata render equivalent single-author behavior and approved multi-author behavior from the normalized model.
- AUTHOR-3: Content and authoring tools migrate safely to the structured form.
- AUTHOR-4: Legacy form is retired only after no maintained source or generated surface depends on it.
- AUTHOR-5: Every intermediate revision builds and publishes valid output.

Open questions:

- Stable author identifier format and legacy deprecation period require approval.

Acceptable alternatives:

- Combine normalization and generated-surface adoption when a clear dual-format working state remains.
- Split content migration only for independently owned content collections.

Natural user request:

Migrate post author metadata from the current single-name field to a structured multi-author form without breaking existing content or generated pages during the transition. Templates, archives, feeds, and authoring tools must move to the new model, existing posts must be migrated safely, and the legacy form may be rejected only after generated-output and content evidence show that nothing still depends on it. Plan the work and create the appropriate task structure without implementing it.

The producer's final conversation response (the durable-context source
the files must preserve):

````markdown
Task structure created — `tasks/20260926-author-metadata-migration/` is the only change; nothing was implemented.

## Plan summary (all plans `Status: Draft`)

**Outcome** — Post author metadata moves from the single-name `author` front matter field to a structured multi-author model; all consumers migrate; existing posts migrate value-preserving; the legacy form ends rejected.

**Decomposition** — Three sequential stages, each an independently verifiable compatibility state, declared with dependencies (`010 → 020 → 030`):

1. **010-structured-authors-adoption** — new model supported by post layout, feed, and `scripts/new-post.js`, with legacy still accepted and rendered byte-identically. Also builds the generated-output evidence: the existing tests are placeholder comments only (`tests/author-output.test.js` claims coverage that doesn't exist), so the evidence gate must be built, not cited.
2. **020-content-migration** — `first.md`/`second.md` converted ("Ada Example", "Grace Example" preserved), with the 010 build-output assertions passing through the structured path as the output-unchanged proof.
3. **030-legacy-rejection** — gate re-verified **fresh** (content scan + consumer inventory + passing build) before any removal, then legacy compatibility removed and rejected with a hard build failure plus authoring-tool rejection.

**Material decisions / open questions**
- **Q1 (blocks execution)** — structured schema shape: recommendation is `authors:` list of objects with required `name`; alternative is a list of strings. Needs your approval before execution.
- Recommendations surfaced for approval: multi-author display joined with ", " in the existing `<p class="author">`; one `<author>` element per author in the feed; hard build failure (no warning fallback) for legacy rejection.

**Acceptance evidence** — production-build assertions on real `_site` output (post pages, feed, archives) owned by 010 and maintained downstream; legacy rejection proven by a real build failing on a sandboxed legacy fixture; the 030 gate re-verified at execution start.

**Documentation audience** — content authors; smallest structure (README authoring section), updated within each stage's change.

**Risks** — uninstalled `node_modules` (execution needs `npm install` first); archive author *display* excluded as new scope (archives render no author today).

Execution waits: approve Q1 and the plans (or adjust them), and tell me to start with 010.
````

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
    "dimensions": {
      "plan_design_completeness": {
        "grade": "complete",
        "findings": [
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md → Execution plan → Design common to the stages",
            "quote": "normalize author data once at the data layer so templates consume a single normalized form (see 010 for the design), and keep the canonical rendered form for a single author byte-identical to today's legacy output",
            "why": "States the core architectural decision and the equivalence invariant that makes the R5 gate decidable by comparison; component responsibilities (data layer normalizes, templates consume) and data flow are reconstructible from the plan alone."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/010-structured-authors-adoption.md → Execution plan → Design",
            "quote": "directory-level computed data on `content/posts/` (via `posts.json`, e.g. `eleventyComputed`) derives a normalized `authors` list (objects per approved Q1) from either the new `authors` field or the legacy `author` field... templates read only the normalized list",
            "why": "Gives the concrete normalization mechanism, the interface contract (templates read only the normalized list), and the constraint bounding the implementation choice — the design detail the parent deferred to 010 is actually there."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md → Requirements checklist and requirement→owner table",
            "quote": "R5 — The legacy single-name form is rejected only after generated-output and content evidence show that nothing still depends on it; that gate is verified fresh immediately before rejection, not assumed from earlier stages.",
            "why": "Compatibility and dependency states are explicit: dual acceptance (010) → migrated content (020) → structured-only with a fresh gate (030), with the strict 010 → 020 → 030 ordering and per-requirement owner table."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md → Implementation decisions and open questions",
            "quote": "Multi-author display on a post page: join names with \", \" inside the existing `<p class=\"author\">` element (recommendation; user-visible, so surfaced for approval with the plan)",
            "why": "Material user-visible decisions are recorded with their approval status rather than silently assumed; Q1 records both the recommended schema and the alternative."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md → Requirement verification",
            "quote": "R1, R2, R3 — production build plus build-output assertions added in 010: legacy posts render the current author line and feed element unchanged; a structured multi-author fixture renders the approved form on the post page and feed through the real build; archives still build.",
            "why": "Every requirement R1–R7 has named verification evidence and an owner, so the plan states how the requirements are verified, not just what the steps are."
          }
        ]
      },
      "durable_context_preservation": {
        "grade": "complete",
        "findings": [
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md → Supporting facts",
            "quote": "tests/author-output.test.js and tests/archive-output.test.js contain placeholder comments only; the author-output comment claims generated-output coverage that does not exist. There is currently no automated evidence of any kind, so the R5 gate must be built as part of this migration, not cited as pre-existing coverage.",
            "why": "The conversation's key verified fact about placeholder tests and its consequence (build the gate, don't cite it) is preserved with its source and repeated in 010's supporting facts and the parent's risks."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md → Supporting facts",
            "quote": "Archive surfaces (`_includes/postslist.njk`, `content/blog.njk`, `content/tag-pages.njk`, `content/index.njk`) render only titles and URLs, so \"moving archives to the new model\" is a compatibility requirement, not a display change. Adding author display to archives would be new scope and is not planned (recommendation).",
            "why": "The response's archive-scope exclusion ('archive author display excluded as new scope; archives render no author today') is preserved with the factual basis behind it."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/020-content-migration.md → Execution plan",
            "quote": "The 010 build-output assertions (which pin the exact legacy-era author strings) must pass after migration — passing through the structured path is the output-unchanged proof for this stage.",
            "why": "The response's stated proof mechanism for stage 2 (010 assertions passing through the structured path) is carried intact, including the preserved author values in the requirements (\"Ada Example\", \"Grace Example\")."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/030-legacy-rejection.md → Supporting facts",
            "quote": "The gate constraint comes from the original request: the legacy form may be rejected only after generated-output and content evidence show that nothing still depends on it.",
            "why": "The gate's origin and the fresh-re-verification approach ('content scan + consumer inventory + passing build', verified at execution start) from the response are preserved in the stage that executes the gate."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md → Requirement questions and Risks",
            "quote": "Q1 (blocks execution of 010 and everything downstream) — What is the exact schema of the structured multi-author form? Recommendation: an `authors` list of objects with a required `name` field... Alternative: a list of plain strings.",
            "why": "The blocking open question, its recommendation, its alternative, and the execution-waits state (\"execution waits until Q1 is resolved\") are all preserved from the response."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md → Risks and 010 → Supporting facts",
            "quote": "Dependencies are not installed in this workspace; verification requires `npm install` first.",
            "why": "The environment risk (uninstalled node_modules) and the other response facts (new-post.js frontMatter signature, build/test entry points, docs audience and smallest-structure choice) appear in the files with sources."
          }
        ]
      },
      "section_appropriateness": {
        "grade": "complete",
        "findings": [
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md → Requirements checklist",
            "quote": "R2 — During the transition, existing content and generated pages keep working: posts still in the legacy form build and render with unchanged author output (post pages and feed).",
            "why": "Outcomes and constraints sit in the requirements section, with the R1–R7 → owner table giving a continuing agent a direct lookup of who owns what."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/010-structured-authors-adoption.md → Supporting facts",
            "quote": "`content/posts/posts.json` sets `layout: layouts/post.njk` and `tags: [\"posts\"]` for all posts — the natural place for directory-wide computed data normalization.",
            "why": "Learned repo facts with file:line sources live in supporting details, separated from direction and decisions; the same pattern holds in 020 (current front matter values) and 030 (gate rationale)."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md → Requirement questions",
            "quote": "Q1 (blocks execution of 010 and everything downstream)",
            "why": "The unresolved approval item sits in a dedicated questions section and is cross-referenced (not buried) in the decisions sections of the parent and 010."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/030-legacy-rejection.md → Supporting facts",
            "quote": "A warning-only acceptance would leave a silent dependency path and would not satisfy \"rejected\"; the recommendation is a hard build failure.",
            "why": "Rationale and learned reasoning live in supporting details while the decision itself is recorded in 'Implementation decisions and open questions' — where a reviewer checks both."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md → Execution plan",
            "quote": "Ordering is strict: 010 → 020 → 030, declared as dependencies in the subtask files.",
            "why": "Execution direction (stage order, per-stage execution tasks, decisive checks) is concentrated in the Execution plan sections of each file rather than scattered."
          }
        ]
      },
      "plan_justification": {
        "grade": "justified",
        "findings": [
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md → Execution plan → Approach",
            "quote": "three sequential compatibility states, each independently verifiable, with a hard evidence gate before the last",
            "why": "Restates the conversation's decomposition ('Three sequential stages, each an independently verifiable compatibility state, declared with dependencies (010 → 020 → 030)') — the plan organizes planning that demonstrably happened."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md → Supporting facts and Risks",
            "quote": "The placeholder test comments could be mistaken for existing coverage; the gate must be built from real build-output assertions.",
            "why": "The plan's central move (evidence must be built, not cited) traces directly to the conversation's inspection finding about tests/author-output.test.js."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/010-structured-authors-adoption.md → Implementation decisions and open questions",
            "quote": "Normalization mechanism: directory computed data in `content/posts/posts.json` (recommended); alternatives acceptable if they keep normalization in one place in the real build path.",
            "why": "Mechanism specifics beyond the conversation summary are labeled as recommendations or implementation choices grounded in stated repo facts (posts.json's role), not asserted as already-decided design."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/030-legacy-rejection.md → Requirements checklist",
            "quote": "Gate (precondition, verified fresh at the start of execution, not assumed from earlier stages)",
            "why": "Matches the response's 'gate re-verified fresh... at execution start'; no plan element asserts design detail the conversation never established."
          }
        ]
      },
      "task_kind_fit": {
        "grade": "fits",
        "findings": [
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md → Subtasks and requirement→owner table",
            "quote": "| R1 (new model supported) | 010 |",
            "why": "For decomposition/tracking work, the acceptance evidence is the recorded structure itself: dependency-ordered subtasks, requirement ownership, and the Q1 approval gate — all present rather than forced code-test sections."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/010-structured-authors-adoption.md → Requirement verification",
            "quote": "A mock of the data cascade would not be decisive; the check is the actual Eleventy output.",
            "why": "For the downstream code migration the plans specify the evidence of the right kind: production-build assertions on real `_site` output, legacy-rejection proven by a real build failing on a sandboxed fixture, and a real-build check of the authoring tool's output."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md → Documentation",
            "quote": "Audience: content authors (front matter format, authoring tool usage). Smallest structure: a concise authoring/front-matter section in the nearest maintained doc (README.md...), updated within each subtask's reviewed change",
            "why": "Documentation acceptance is scoped per stage with an audience and a smallest-structure rule, matching the repository's documentation guidance rather than a mechanical placeholder docs section."
          },
          {
            "where": "tasks/20260926-author-metadata-migration/000-main.md → Risks",
            "quote": "Any unapproved schema choice (Q1) invalidates the plans below; execution waits until Q1 is resolved.",
            "why": "The planning deliverable's own acceptance gate (user approval of Q1 and the plans before execution) is recorded, so the tracking-work kind has its decisions and gate recorded, nothing missing."
          }
        ]
      }
    },
    "mistakes": [
      {
        "where": "tasks/20260926-author-metadata-migration/000-main.md → Requirement questions (and every 'Implementation decisions and open questions' section, by absence)",
        "quote": "Open questions: Stable author identifier format and legacy deprecation period require approval. — vs. the files' only surfaced question: \"Q1 — What is the exact schema of the structured multi-author form?\"",
        "why": "The target excerpt flags two additional approval items that the task files never surface. The legacy deprecation period is fixed implicitly by the 010 → 020 → 030 gate structure without being presented as a decision needing approval, and author identifier stability is only gestured at by Q1's 'extensible later (e.g. url)'. A continuing agent reading only the files would not know these were marked as requiring approval."
      }
    ],
    "summary": "The handoff is high fidelity. The parent plus three subtask files let a reader reconstruct the decided design: a single normalization point in the posts data cascade with templates consuming only the normalized list, byte-identical single-author rendering as the safety invariant, three dependency-ordered compatibility states (dual acceptance → migrated content → structured-only), and an evidence gate built from real build-output assertions rather than cited from placeholder tests. Everything durable from the conversation is compressed into the files with sources: the placeholder-test fact, Q1 with recommendation and alternative, the three surfaced recommendations (', ' display join, one <author> per feed entry, hard build failure), the archive-scope exclusion, the npm install risk, documentation audience/structure, and per-requirement verification through the real production path. Content sits in conventional sections (requirements, supporting facts, execution plan, decisions/open questions, requirement verification), the plans restate the conversation's planning without asserting unestablished design, and the decomposition kind is served by recorded decisions, dependency declarations, and the Q1 approval gate as acceptance evidence. The single gap versus the target excerpt: its other two open questions — stable author identifier format and the legacy deprecation period — are never surfaced for approval; the deprecation period is resolved implicitly by the stage structure."
  }
}
```
