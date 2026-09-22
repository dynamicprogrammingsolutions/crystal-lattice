# Migrate post author metadata to structured multi-author form

Migrate post author metadata from the legacy single-name `author` front-matter
string to a structured multi-author form across templates, archives, feeds, and
the authoring tool, migrating existing posts safely and rejecting the legacy
form only after generated-output and content evidence shows nothing still
depends on it.

Scope note: this task plans and tracks the migration. These files do not
authorize execution; every plan below is `Draft` and execution waits on
explicit approval plus resolution of the requirement questions.

## Requirements checklist

- [ ] Posts support a structured multi-author field as the supported content
      model; a post can declare multiple named authors. (Field shape pending
      requirement question Q1.)
- [ ] Every consumer of post author metadata — post page template, feed,
      archive/tag surfaces, and the authoring tool — reads only the new model
      in the final state. (Archive display scope pending requirement
      question Q2.)
- [ ] At every executed state of the migration, the production build succeeds
      and generated output for existing content (post pages, blog archive, tag
      pages, feed, sitemap) remains correct; existing posts end up migrated to
      the new form.
- [ ] The legacy single-name `author` form is rejected by the production build
      only after generated-output and content evidence shows that no source
      content, template, tooling, or generated output still depends on it.
- [ ] Maintained documentation describes the new author form and, in the same
      reviewed change that enables it, the rejection of the legacy form.

## Requirement questions

- **Q1 — Field shape (material; persisted content format).** Options:
  - **A (recommended):** `authors` is a list of author name strings, e.g.
    `authors: ["Ada Example", "Grace Example"]`. Smallest change that satisfies
    "structured multi-author"; rendering semantics stay name-text-only.
  - **B:** `authors` is a list of objects, e.g. `authors: [{ name: "...", url:
    "..." }]`. Leaves room for per-author metadata (links, ids) but introduces
    fields no current template renders.
- **Q2 — Archive display scope.** The blog archive and tag pages currently
  render only title and URL (`_includes/postslist.njk`) and consume no author
  data. Does "archives must move to the new model" mean:
  - **A (recommended):** archives are verified as non-consumers and their
    output stays unchanged; no new author display is added.
  - **B:** archive/tag pages must start displaying author names from the new
    model (new visible behavior, extends subtask 010 scope).

## Subtasks

- [ ] tasks/20260920-post-author-migration/010-multi-author-model-and-compat.md
- [ ] tasks/20260920-post-author-migration/020-content-and-tooling-migration.md
- [ ] tasks/20260920-post-author-migration/030-evidence-gate-and-legacy-rejection.md

## Supporting facts

Current state, verified by inspection (2026-09-20):

- Legacy form: `author: "<name>"` string in post front matter.
  `content/posts/first.md` (`Ada Example`), `content/posts/second.md`
  (`Grace Example`). These are the only content files.
- Consumers of author data:
  - `_includes/layouts/post.njk:2` — `<p class="author">{{ author }}</p>`.
  - `content/feed.xml.njk:5` — simplified Atom-like document; renders
    `{{ post.data.author }}` inside `<entry><author>`; `layout: false`,
    permalink `/feed/feed.xml`.
- Author non-consumers (verified): `_includes/postslist.njk` renders only
  title + URL and is shared by `content/blog.njk` (archive),
  `content/index.njk` (home), and `content/tag-pages.njk` (tag pages);
  `content/sitemap.xml.njk` renders URLs only; `content/posts/posts.json` sets
  layout/tags only.
- Authoring tool: `scripts/new-post.js` exports `frontMatter(title, author)`
  emitting the legacy string form. No npm script invokes it.
- Tests: `tests/author-output.test.js` and `tests/archive-output.test.js` are
  comment-only stubs; `npm test` (`node --test tests/*.test.js`) currently
  passes with no executable coverage. No generated-output coverage exists yet.
- Dependencies are not installed (`node_modules/` absent, gitignored);
  build/test evidence requires `npm install` (devDependency
  `@11ty/eleventy ^3.0.0`). `_site/` is gitignored output.
- Build config: `eleventy.config.js` — input `content/`, includes
  `../_includes`, output `_site`.
- `docs/development/index.md` notes a missing archive pagination
  specification — unrelated to authors; leave unchanged. There is no
  `docs/index.md` and no existing documentation describes author metadata.
- Fixture provenance: `UPSTREAM.md` (adapted from Eleventy Base Blog).

## Execution plan

Status: Draft

Three subtasks in strict order, one per compatibility state. Each ends with
the site building green and its evidence recorded, so every executed state is
independently acceptable.

1. **010 — dual-read state.** Introduce the structured `authors` model with a
   normalization path that maps legacy `author` strings into it, move the post
   layout and feed templates to read only the new model, and replace the two
   comment-only test stubs with real generated-output tests run through the
   production Eleventy build. Existing content stays legacy-form and its
   generated output must be byte-identical to the pre-change baseline.
2. **020 — migrated-content state.** Rewrite both posts' front matter to the
   new form and update `scripts/new-post.js` to emit it (multiple authors
   supported). Generated output for the two posts must remain identical;
   content audit shows zero legacy keys. Document the `authors` front-matter
   form for content authors in the same change.
3. **030 — rejection state.** Gate: content audit (zero legacy keys) plus
   full green generated-output suite plus tooling emitting only the new form.
   Only when all three hold, enable build-time rejection of legacy `author`,
   remove the legacy normalization fallback, add an integration test proving a
   legacy fixture fails the real build, and document the rejection in the same
   change.

Sequencing rationale: the rejection gate required by the request is encoded as
subtask 030's dependency on 010 + 020 and its explicit pre-rejection evidence
checklist. Tests from 010 assert exact author strings at the generated-output
boundary, so they stay valid across the internal migration and provide the
before/after equivalence evidence for the "nothing breaks" constraint.

Prerequisites and risks:

- `npm install` must succeed before any build evidence; if it is blocked,
  report that build evidence is not run rather than claiming it.
- Computed-data normalization must be visible on `post.data` inside the feed
  template; verified by the real-build feed test in 010, with a shared filter
  as the fallback mechanism.
- Test fixture posts (multi-author cases) must be built in temp copies of the
  content tree, never added to the real `content/`, so the public site output
  is not altered by tests.
- Q1 and Q2 must be resolved before 010 executes; both change requirements,
  not just implementation.

### Implementation decisions and open questions

- **Open requirement questions:** Q1 (field shape) and Q2 (archive display
  scope) above. Neither is resolved by this plan; subtasks 010 and 020 depend
  on Q1, 010 depends on Q2. Recommendation: Q1=A, Q2=A.
- **Decision (pending approval with the plan):** new field is named `authors`;
  legacy key is `author`.
- **Decision:** rejection is enforced at build time by validating post front
  matter in `eleventy.config.js` (exact Eleventy 3 hook chosen during 030);
  the authoring tool additionally never emits the legacy form (from 020).
- **Decision:** during the dual-read state, normalization maps legacy
  `author` to the new model via Eleventy computed data in
  `content/posts/posts.json`; a shared filter is the fallback if computed data
  is not visible on collection items in the feed.
- **Decision:** multi-author display on post pages joins names with `", "`;
  the feed emits one `<author>` element per author in post order. Affects only
  posts that opt into multiple authors; existing single-author output is
  unchanged.

### Documentation

- Follows `docs/development/documentation.md` (read before restructuring).
- No maintained documentation currently describes author metadata, so subtask
  010 needs no documentation change (unless Q2 resolves to archive display).
- Subtask 020 adds a short "Adding posts" section to `README.md` documenting
  the `authors` front-matter form — placed with the site entry point that
  content authors use; smallest structure that helps the reader (alternative
  considered: a new `docs/` page, rejected as unnecessary structure).
- Subtask 030 updates the same README section, in the same reviewed change
  that enables rejection, so the "legacy form is rejected" claim is true when
  published. No placeholder pages or `docs/index.md` are created.

### Task checklist

- [ ] Resolve Q1 and Q2 with the requester; update affected requirements.
- [ ] Execute and complete
      tasks/20260920-post-author-migration/010-multi-author-model-and-compat.md
- [ ] Execute and complete
      tasks/20260920-post-author-migration/020-content-and-tooling-migration.md
- [ ] Verify 030's pre-rejection evidence gate is fully green before any
      rejection change lands.
- [ ] Execute and complete
      tasks/20260920-post-author-migration/030-evidence-gate-and-legacy-rejection.md
- [ ] Final review: full `npm test` + production build green; all requirement
      checkboxes in main and subtasks supported by recorded evidence.

### Requirement verification

- Multi-author model supported → decisive evidence: production-build test
  with a multi-author fixture post (temp content copy) asserting all authors
  render on the post page and in the feed (subtask 010).
- Consumers moved to the new model → decisive evidence: source audit shows no
  template or tool reads the legacy key, and the full generated-output suite
  passes after the legacy fallback is removed (subtasks 020 + 030).
- No breakage during transition → decisive evidence: generated-output tests
  asserting exact author strings and archive contents pass against unchanged
  content before the model change, and pass again after each migration step
  (subtasks 010 and 020).
- Legacy rejected only after evidence → decisive evidence: 030's recorded
  pre-rejection checklist (content audit zero legacy keys; green suite;
  tool emits new form only) followed by an integration test in which a
  legacy-form fixture fails the real build while the real content builds
  cleanly (subtask 030). The gate order itself is a requirement; it is
  enforced by subtask dependency plus the recorded checklist.
- Documentation current with behavior → evidence: README section present in
  the same changes that introduce the new form (020) and enable rejection
  (030); verified by inspection of the merged state.

### Additional implementation verification

- Verify computed-data visibility on `post.data` in the feed context via the
  real build early in 010 (material risk to the normalization approach).
- Confirm the shared test build helper is exercised by every generated-output
  test (maintained test infrastructure verified through real consumers).
- Confirm `node --test` collects all test files and exits cleanly after each
  subtask; record suite results in the executing subtask.