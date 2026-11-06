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
