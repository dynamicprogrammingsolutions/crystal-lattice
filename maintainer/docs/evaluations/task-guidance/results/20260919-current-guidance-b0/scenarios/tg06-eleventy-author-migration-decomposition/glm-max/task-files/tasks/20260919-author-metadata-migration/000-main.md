# Migrate post author metadata to a structured multi-author model

Migrate the site's single-name `author` front-matter field to a structured
multi-author model across post templates, the feed, archives, and the authoring
tool. Existing posts are migrated safely under a compatibility window, and the
legacy single-name form is rejected only after generated-output and content
evidence show nothing still depends on it. Planning only: this file does not
authorize implementation.

## Requirements checklist

- [ ] R1: Posts support a single canonical structured author field representing
      an ordered list of authors; it replaces the single-name `author` field as
      the supported authoring model. (Exact shape per approved decision in
      `### Implementation decisions and open questions`.)
- [ ] R2: The post page layout renders every author of a post, for both
      single-author and multi-author posts.
- [ ] R3: The feed emits an author element for every author of every post,
      preserving the currently emitted author-text semantics.
- [ ] R4: Archives, tag pages, the home listing, and the sitemap keep
      rendering all posts (title/link) unchanged through the migration; they
      have no author dependence and are regression-protected.
- [ ] R5: The authoring tool (`scripts/new-post.js`) generates the structured
      form for new posts.
- [ ] R6: During the transition, legacy single-name posts and structured-form
      posts coexist: both build and render correctly, with no content loss and
      no broken generated pages at any intermediate state.
- [ ] R7: Existing posts (`content/posts/first.md`, `content/posts/second.md`)
      are migrated to the structured form with their URLs and rendered author
      output preserved.
- [ ] R8: Evidence exists for the new model, the compatibility behavior, and
      the migration: unit tests for normalization and the authoring tool, plus
      production-build integration tests over post pages, feed, and archives
      that include multi-author and legacy/new mixed cases without adding
      test-only content to production `content/`.
- [ ] R9: The legacy single-name form is rejected only after gate evidence —
      a content scan showing zero legacy usage and green generated-output
      evidence — and the rejection is an explicit, documented build failure.
- [ ] R10: Maintained documentation reflects the author model, the transition
      state, and the final rejection state, kept in the same reviewed changes
      as the code that makes each claim true.

## Subtasks

- [ ] tasks/20260919-author-metadata-migration/010-author-model-and-compat.md
- [ ] tasks/20260919-author-metadata-migration/020-templates-feed-and-archives.md
- [ ] tasks/20260919-author-metadata-migration/030-authoring-tool.md
- [ ] tasks/20260919-author-metadata-migration/040-migrate-existing-posts.md
- [ ] tasks/20260919-author-metadata-migration/050-legacy-gate-and-rejection.md

## Open questions and decisions

These change scope or outcomes and must be resolved (by approval of this plan
or explicit instruction) before the affected subtask executes.

1. **Structured shape (R1, blocks 010).** Recommend: `authors` as an ordered
   YAML list of display-name strings, e.g. `authors: ["Ada Example"]`, always a
   list (no scalar shorthand for the new field; the authoring tool always emits
   a list). Alternative: entries as objects with at least `name` (optionally
   `url`) if per-author attributes beyond the display name are required now.
   Choose one before 010 executes.
2. **Rejection mechanism (R9, blocks 050).** Recommend: a build-time check in
   the Eleventy data path that fails the build with an error listing files that
   still define legacy `author:`, so rejection is machine-enforced and matches
   documentation. Alternative: silently ignoring/stripping the legacy field
   (rejected recommendation: hides authoring mistakes).
3. **Feed Atom validity (R3, affects 020 scope).** The current feed emits bare
   text inside `<author>` (not an Atom-valid `<name>` child). Recommend:
   preserve current semantics (one `<author>` per author, same text form) and
   defer any Atom-validity rework out of this migration. Confirm or expand 020
   scope.

## Supporting details

Verified facts from inspection (2026-09-19):

- Author touchpoints (complete):
  - `content/posts/first.md:3` — legacy scalar `author: "Ada Example"`.
  - `content/posts/second.md:3` — legacy scalar `author: "Grace Example"`.
  - `_includes/layouts/post.njk:2` — renders scalar `{{ author }}` inside
    `<p class="author">`.
  - `content/feed.xml.njk:5` — `<entry><author>{{ post.data.author }}</author></entry>`
    per post in `collections.posts`.
  - `scripts/new-post.js:1-3` — pure `frontMatter(title, author)` emits the
    legacy scalar string form.
  - `tests/author-output.test.js`, `tests/archive-output.test.js` —
    comment-only placeholders, no assertions.
- Author-independent generated surfaces: `_includes/postslist.njk` renders
  title + url only; `content/index.njk`, `content/blog.njk`, and
  `content/tag-pages.njk` all include `postslist.njk`;
  `content/sitemap.xml.njk` renders URLs only.
- Data cascade: `content/posts/posts.json` sets only `layout` and
  `tags: ["posts"]`; there is no directory-level author default.
- Build config (`eleventy.config.js`): input `content`, includes
  `../_includes`, output `_site`; provides a `head` filter; passthrough-copies
  `public` (directory does not exist — pre-existing condition, not in scope).
- Test harness: `npm test` runs `node --test tests/*.test.js`; both files
  currently collect and exit cleanly (verified with node v20.19.5) but assert
  nothing. Generated output (`_site/`) is gitignored.
- Dependencies are not installed in this worktree (`node_modules` absent);
  execution must start with `npm install` (`@11ty/eleventy ^3.0.0`).
- Documentation surface: root `README.md` describes build outputs;
  `docs/development/index.md` and `docs/development/documentation.md` are
  maintainer guidance; there is no `docs/index.md`. Author-model documentation
  belongs in the author-facing surface (`README.md`) per
  `docs/development/documentation.md` rules.
- `UPSTREAM.md`: fixture adapted from Eleventy Base Blog.

Constraints:

- No test-only posts may be added to production `content/`; multi-author and
  mixed-form build coverage must come from a separate fixture site (see 020).
- For single-author posts, the new pipeline must produce equivalent generated
  output to the current build, which allows before/after comparison as
  transition evidence.
- New public documentation claims must land in the same reviewed change as the
  code that makes them true (repository documentation guidance).

## Execution plan

Status: Draft

Layered migration: normalize both author forms behind one data view, migrate
all consumers (post layout, feed) to that view with generated-output tests,
migrate the authoring tool, migrate existing content, then evaluate the
legacy-dependency gate and reject the legacy form. Consumers are changed
before content so that migrated posts render correctly the moment they are
converted; the legacy path is removed last, after evidence.

Sequence and boundaries:

1. **010 — model + compatibility.** Install dependencies, capture a baseline
   production build of the current content (comparison artifact), then
   introduce the canonical `authors` model with a normalization step that
   yields a uniform authors list from either the new form or the legacy scalar.
   Templates do not change yet. Unit tests cover normalization of both forms.
2. **020 — consumers.** Post layout renders all authors (joined display,
   existing `p.author` element class retained); feed emits one author element
   per author with current text semantics; archives are regression-covered
   (posts listed with titles/links, not just existence). Generated-output
   tests cross the real build boundary via a fixture site that includes a
   multi-author post, a new-form single-author post, and a legacy post, so the
   compat path is exercised; real-content build checks cover first/second.
3. **030 — authoring tool.** `frontMatter` emits the structured list form;
   unit test pins the exact emitted front matter.
4. **040 — content migration.** Convert `first.md` and `second.md` to the
   structured form; compare generated output against the 010 baseline (same
   URLs, same rendered author text, archive/feed/sitemap intact).
5. **050 — gate + rejection.** Evidence gate: content scan shows zero legacy
   `author:` usage in `content/`, authoring tool no longer emits it, all
   build-boundary tests green. Only then remove legacy acceptance from the
   normalization path, add the explicit build-time rejection error, re-run the
   full suite and production build, and update `README.md` to the final
   rejection state (removing the transitional note added earlier).

Risks:

- Normalization must integrate with the Eleventy data cascade without
  shadowing unrelated post data; `posts.json` has no author keys, so risk is
  low but the integration tests must catch regressions.
- Feed output for multi-author posts necessarily differs from the legacy
  single-element output; single-author output must remain text-equivalent
  (R3/R7 comparison evidence).
- Removing the legacy path before the gate would break transition guarantees;
  subtask ordering (050 strictly after 030/040 evidence) enforces the gate.
- Fresh `npm install` and an Eleventy 3 build in this worktree are
  prerequisites; if the build cannot run, the gate cannot be evaluated and the
  plan stops at the blocked subtask with the blocker reported.

### Implementation decisions and open questions

- D1 (open, needs approval): field shape — recommend `authors` list of
  display-name strings, always a list. See top-level question 1.
- D2 (open, needs approval): rejection mechanism — recommend explicit
  build-time error listing offending files. See top-level question 2.
- D3 (open, needs approval): feed keeps current bare-text `<author>` semantics,
  one element per author; Atom-validity rework deferred. See top-level
  question 3.
- D4 (resolved locally): multi-author post-page display joins author names
  with a comma inside the existing `p.author` element; element/class retained
  so page structure and styling hooks are unchanged.
- D5 (resolved locally): canonical form is list-only; legacy scalar is
  accepted only by the compatibility path during the transition window and is
  not a shorthand for the new field.
- D6 (resolved locally): generated-output tests build a small fixture site
  under `tests/` (own content, real templates/config) rather than adding
  test-only posts to production `content/`; real-content builds cover the
  actual posts.
- D7 (resolved locally): test builds write to a gitignored/temporary output
  directory so the working tree stays clean.

### Documentation

- Audience: post authors/contributors (front-matter model, authoring tool
  behavior, legacy rejection state). Maintainers get context from this task
  tree.
- 010/020: `README.md` gains a short author-metadata section describing the
  structured `authors` model with an example and the transitional note that
  the legacy single-name form is still accepted.
- 030: same section notes the authoring tool emits the structured form.
- 050: the section is updated in the same change as the rejection code —
  transitional note removed, legacy `author:` documented as rejected with an
  explicit build error, with an example of the accepted form.
- No new documentation directories or pages; smallest structure per
  `docs/development/documentation.md`.

### Task checklist

- [ ] tasks/20260919-author-metadata-migration/010-author-model-and-compat.md
- [ ] tasks/20260919-author-metadata-migration/020-templates-feed-and-archives.md
- [ ] tasks/20260919-author-metadata-migration/030-authoring-tool.md
- [ ] tasks/20260919-author-metadata-migration/040-migrate-existing-posts.md
- [ ] tasks/20260919-author-metadata-migration/050-legacy-gate-and-rejection.md

### Requirement verification

- R1 → unit tests for normalization (both forms) plus generated-output tests
  showing structured posts build and render (010, 020).
- R2 → fixture-site build test: multi-author post page contains every author
  name; single-author post page contains its author (020).
- R3 → fixture-site build test: feed contains one `<author>` element per
  author per post; single-author feed text matches the pre-migration form
  (020, 040 comparison).
- R4 → archive/tag/home build tests assert full post lists (title + link),
  not existence only; sitemap URLs unchanged (020, 040).
- R5 → unit test pinning `frontMatter` output to the structured list form
  (030).
- R6 → fixture-site test includes a legacy post and a new-form post building
  side by side and rendering correctly (020, 040).
- R7 → real-content build comparison against the 010 baseline: same URLs,
  same rendered author text, archives/feed intact (040).
- R8 → full `node --test tests/*.test.js` run collecting all unit and
  build-boundary tests cleanly (010–040; final confirmation 050).
- R9 → gate evidence recorded in 050 (content scan result + green suite) and
  a test showing a legacy-form post now fails the build with the documented
  error; `README.md` updated in the same change (050).
- R10 → README sections present at each phase and matching the behavior of
  that change (010/020, 030, 050).

### Additional implementation verification

- Final production build of the real site succeeds and `git status` shows no
  scratch/fixture leakage into production `content/`.
- Legacy-dependency re-check immediately before rejection: grep for
  `author:`-style scalar usage across `content/` (scan recorded in 050).
- Confirm `npm install` warnings/errors (if any) are reviewed; record the
  installed Eleventy version in 010 notes.