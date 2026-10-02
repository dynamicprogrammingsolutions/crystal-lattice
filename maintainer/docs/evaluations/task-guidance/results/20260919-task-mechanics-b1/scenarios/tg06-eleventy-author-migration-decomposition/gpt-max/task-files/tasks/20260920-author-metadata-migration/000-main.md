# Migrate post author metadata

Plan the migration from the single `author` front-matter value to a canonical
ordered multi-author value while keeping legacy content and generated output
working until repository evidence permits the legacy form to be rejected.

## Requirements checklist

- [ ] R1. Define and adopt one canonical structured author collection that
  supports one or more authors, preserves source order, and exposes each
  author's display identity to every production consumer.
- [ ] R2. Preserve existing content and generated pages during the transition:
  legacy `author` content must continue to normalize to the canonical model
  until the retirement gate passes, without changing post bodies, routes,
  tags, archive membership, feed location, or sitemap coverage.
- [ ] R3. Move the authoring helper to the canonical model and make its
  single- and multi-author behavior explicit, while preserving safe input
  compatibility during the transition.
- [ ] R4. Migrate every repository post from the legacy field without losing,
  duplicating, or reordering author names, and leave auditable source evidence
  that the migration is complete.
- [ ] R5. Move post layouts, home/blog/tag archive consumers, shared post-list
  rendering, feeds, and any other author consumers to the canonical model.
  Generated pages must continue to build and all authors must be represented
  deterministically.
- [ ] R6. Reject the legacy field only after both source/consumer evidence and
  production generated-output evidence show that nothing in the repository
  still depends on it; the rejection must have a clear diagnostic and a
  regression check.
- [ ] R7. Update maintained authoring documentation and regression evidence
  with the supported canonical form and the completed transition state.

## Scope and workstreams

The scope is the repository’s Eleventy source, content, authoring helper,
production templates, build-time validation, tests, and the maintained
documentation that explains how posts are authored. Existing URLs, post body
content, tags, archive membership, feed location, and sitemap behavior are
compatibility constraints.

The work is intentionally divided by independently reviewable capability:

- establish the data contract and authoring boundary;
- migrate all rendering and collection consumers;
- migrate source content and prove its inventory is clean; and
- perform the generated-output/content gate before enforcing canonical-only
  input.

Author profile pages, stable author IDs, roles, avatars, author sorting, and
new public routes are out of scope unless the canonical-shape decision below
requires one of them.

## Subtasks

- [ ] tasks/20260920-author-metadata-migration/010-author-contract-and-authoring.md
- [ ] tasks/20260920-author-metadata-migration/020-rendering-and-archive-consumers.md
- [ ] tasks/20260920-author-metadata-migration/030-source-content-migration.md
- [ ] tasks/20260920-author-metadata-migration/040-output-evidence-and-legacy-retirement.md

## Unresolved requirement questions and decisions

- Requirement question: does “structured” mean an ordered list of display
  strings (`authors: ["Ada Example"]`) or an ordered list of records with a
  required `name` (`authors: [{ name: "Ada Example" }]`)? Recommendation:
  use records with a required `name` and no additional fields in this
  migration, so each author has an explicit structured boundary without
  inventing profile behavior.
- Requirement question: if both `author` and `authors` are present during the
  compatibility window, should the build fail as ambiguous input or should
  one field win? Recommendation: fail with a targeted diagnostic; silently
  choosing one would hide a content migration error.
- Design decision: install compatibility normalization before changing
  consumers or source content; migrate content and collect output evidence;
  only then enable canonical-only rejection. This ordering is required by the
  requested transition guarantee.
- Recommendation requiring confirmation at execution time: preserve the
  existing one-author display text, join multiple post-page names in source
  order with a deterministic separator, and emit one feed author element per
  canonical author. This avoids a URL or feed-location redesign while making
  multiple authors lossless.

## Research and supporting facts

- `content/posts/first.md` and `content/posts/second.md` are the only current
  posts and each has a scalar quoted `author`.
- `_includes/layouts/post.njk` renders `author` directly.
- `content/feed.xml.njk` reads `post.data.author` directly and currently emits
  one author element per post.
- `content/index.njk`, `content/blog.njk`, and `content/tag-pages.njk` all
  use `_includes/postslist.njk`; that include currently renders titles and
  links but no author data. These archive paths still need an explicit
  canonical-model audit and route/output checks.
- `content/posts/posts.json` supplies the shared post layout and `posts` tag;
  `content/sitemap.xml.njk` enumerates all page URLs but has no author lookup.
- `scripts/new-post.js` exports `frontMatter(title, author)` and serializes
  the legacy field.
- `tests/author-output.test.js` and `tests/archive-output.test.js` currently
  contain comments only, so there is no executable author or archive
  regression evidence to preserve.
- `package.json` exposes `npm run build` and `npm test`; dependencies are not
  installed in this planning checkout, so neither command is evidence for
  this Draft plan.
- There is no `docs/index.md`; `docs/development/index.md` only records that
  no archive pagination specification exists. The smallest likely maintained
  documentation change is a focused authoring section in `README.md`, unless
  the approved contract needs a dedicated development page.

## Execution plan

Status: Draft

First agree the canonical author element shape and collision behavior. Add a
single normalization/validation boundary that can represent canonical input
and temporarily adapt the legacy scalar. Update the authoring helper and
rendering consumers against that boundary before editing source posts. Then
convert every existing post, run a scoped source/consumer inventory, and
exercise a real Eleventy build that checks post pages, archive routes, feed
entries, and sitemap coverage. The final subtask removes the compatibility
path and enables a canonical-only rejection only after those checks pass.

Each child owns its focused tests and documentation updates; the final child
owns the cross-capability retirement gate rather than being a generic test
or cleanup task.

### Implementation decisions and open questions

- The canonical field name is planned as `authors`; its element shape remains
  the requirement question above and must be settled before execution.
- Normalization should live at the Eleventy data boundary so layouts and
  collection templates do not each implement different legacy fallbacks.
- The legacy adapter must be observable in tests and removable without
  changing canonical rendering.
- The final rejection is planned as a build-time validation failure with a
  field-specific message; confirm this is the desired authoring-tool failure
  mode before implementation.

### Documentation

- Update the maintained authoring guidance with the canonical front-matter
  example, single/multi-author rules, ordering behavior, and the fact that
  legacy `author` is no longer accepted after the retirement gate.
- Keep migration-only rationale and evidence in these task files rather than
  publishing a target-only claim as current documentation before execution.
- Do not create an empty documentation hierarchy or unrelated archive
  pagination material.

### Task checklist

- [ ] Confirm the canonical element shape, collision behavior, and rejection
  diagnostic before execution.
- [ ] Complete tasks/20260920-author-metadata-migration/010-author-contract-and-authoring.md.
- [ ] Complete tasks/20260920-author-metadata-migration/020-rendering-and-archive-consumers.md.
- [ ] Complete tasks/20260920-author-metadata-migration/030-source-content-migration.md.
- [ ] Complete tasks/20260920-author-metadata-migration/040-output-evidence-and-legacy-retirement.md.
- [ ] Review the final generated-output, source-inventory, and negative
  legacy-input evidence together before marking R6 complete.

### Requirement verification

- R1 is complete only when the canonical contract is exercised through the
  authoring/data boundary and a real rendered post with one and multiple
  authors.
- R2 is complete only when a pre-migration/compatibility build accepts the
  legacy fixture and preserves routes, post content, archive membership, feed
  location, and sitemap coverage.
- R3 is complete when the authoring helper’s generated front matter is parsed
  by the production data path for both one and multiple authors, including
  relevant escaping/validation cases.
- R4 is complete when a scoped source scan finds no legacy post field and a
  reviewed content diff proves names and order were preserved.
- R5 is complete when the production build and output assertions cover the
  post layout, home/blog/tag archive routes, feed author entries, and sitemap
  URLs without a legacy lookup.
- R6 is complete only after the source/consumer scan and canonical-content
  build pass, followed by a real negative build/input check proving that a
  legacy field now fails with the intended diagnostic.
- R7 is complete when the maintained authoring documentation matches the
  enforced behavior and `npm test` plus `npm run build` exit successfully
  with dependencies available.