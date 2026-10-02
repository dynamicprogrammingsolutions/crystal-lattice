# Migrate post author metadata to a structured multi-author model

Plan the staged migration from the site's scalar post `author` field to an
approved structured form that can represent one or more authors. The plan
covers the compatibility boundary, existing content, the post authoring
helper, generated page consumers, and the evidence required before the legacy
form can be rejected. This task is planning-only until the draft is approved.

## Requirements checklist

- [ ] Adopt an approved structured post-author form that represents one or
      more named authors and is the single model consumed by the site.
- [ ] Keep existing source content and generated site behavior working while
      the transition compatibility path is active; preserve existing post
      content and generated routes.
- [ ] Move post templates, home/blog/tag archive surfaces, and the feed to the
      structured author model without leaving consumers dependent on the
      scalar field.
- [ ] Update the post authoring helper to emit the structured form and migrate
      every existing post safely, preserving its title, body, and current
      generated-page identity.
- [ ] Retire or reject the legacy scalar form only after both source-content
      evidence and production generated-output evidence show that no remaining
      dependency requires it.
- [ ] Keep the maintained developer-facing documentation aligned with the
      supported authoring form and the transition state.

## Unresolved requirement questions

- What is the exact structured schema and field name: an array of author
  records such as `{ name }`, an array of strings, or another approved
  representation? Are stable IDs, slugs, links, or other author attributes
  required now?
- What is the required public rendering contract for multiple authors in post
  bylines, archive listings, and the feed? In particular, should the feed emit
  one author element per author or a serialized combined value, and must
  archive authors be linked?
- Is final rejection of the legacy scalar required after the evidence gate, or
  is an indefinitely retained read-compatibility adapter acceptable once all
  maintained content has migrated? The plan below targets retirement after
  evidence, but this outcome should be confirmed before execution.

## Decisions and scope boundaries

- Use a main task with three subtasks because the compatibility contract,
  authoring/source migration, and public generated-output consumers are
  separate acceptance and ownership boundaries.
- Keep integration verification, documentation coordination, and the final
  legacy-retirement decision in this parent. They depend on all child
  capabilities and are not independent deliveries.
- This turn creates task files only. It does not alter source content,
  templates, scripts, tests, documentation, dependencies, or generated output.
- During the transition, legacy support belongs at one normalization boundary;
  templates, archives, feeds, and other consumers must not each implement
  their own scalar fallback.

## Supporting facts and research

- `README.md` describes a production Eleventy build that emits a home page,
  blog archive, tag pages, feed, sitemap, and individual posts.
- Both existing posts,
  `content/posts/first.md` and `content/posts/second.md`, currently use the
  scalar front-matter key `author`.
- `_includes/layouts/post.njk` renders the scalar layout variable `author`.
- `content/feed.xml.njk` reads `post.data.author` directly.
- `content/index.njk`, `content/blog.njk`, and `content/tag-pages.njk` all
  delegate their post listing to `_includes/postslist.njk`; that include
  currently renders titles only, so archive author behavior must be decided
  and covered rather than assumed.
- `scripts/new-post.js` currently emits scalar `author` front matter.
- `tests/author-output.test.js` and `tests/archive-output.test.js` contain
  comments describing intended coverage but no executable assertions.
- `package.json` exposes `npm run build` and `npm test`; `_site/` is ignored.
- No `docs/index.md` or task directory exists. The maintained documentation
  guidance is in `docs/development/documentation.md`, and
  `docs/development/index.md` currently contains only a note about archive
  pagination.

## Subtasks

- [ ] `tasks/20260925-author-metadata-migration/010-author-schema-transition.md`
- [ ] `tasks/20260925-author-metadata-migration/020-content-and-authoring-migration.md`
- [ ] `tasks/20260925-author-metadata-migration/030-generated-output-consumers.md`

## Requirement ownership

- Structured model: owned by
  `tasks/20260925-author-metadata-migration/010-author-schema-transition.md`,
  with source adoption in
  `tasks/20260925-author-metadata-migration/020-content-and-authoring-migration.md`
  and public consumption in
  `tasks/20260925-author-metadata-migration/030-generated-output-consumers.md`.
- Transition compatibility and legacy retirement: owned by
  `tasks/20260925-author-metadata-migration/010-author-schema-transition.md`;
  the parent owns the final evidence gate, using the source inventory from
  `tasks/20260925-author-metadata-migration/020-content-and-authoring-migration.md`
  and the production-build evidence from
  `tasks/20260925-author-metadata-migration/030-generated-output-consumers.md`.
- Templates, archives, feeds, and route preservation: owned by
  `tasks/20260925-author-metadata-migration/030-generated-output-consumers.md`,
  with the decisive check being a real Eleventy build inspected under `_site`.
- Existing post migration, authoring helper, and authoring documentation:
  owned by
  `tasks/20260925-author-metadata-migration/020-content-and-authoring-migration.md`,
  with the decisive checks being helper-output assertions and the maintained
  source-content inventory.

## Execution plan

Status: Draft

The migration should introduce one approved author contract and one
normalization boundary before changing every consumer. The boundary must
produce a stable collection of author values for both the structured form and
the legacy scalar form during the transition. This keeps compatibility logic
out of Nunjucks templates and the feed, and makes the eventual retirement
decision observable.

The intended sequence is:

1. Resolve the schema and output questions, then define the transition
   contract, including how a legacy scalar value maps to one author and what
   the post-retirement rejection behavior is.
2. Implement and test the normalization/compatibility boundary. Keep the
   legacy path available while source content and all generated consumers are
   being migrated.
3. Update the authoring helper and migrate all existing post front matter to
   the new form. Preserve post titles, bodies, ordering inputs, URLs, tags,
   and other unrelated metadata.
4. Update the post layout, shared post-list include, archive pages, and feed
   to consume only the normalized structured collection. Verify the complete
   Eleventy build, including individual posts, home/blog/tag archives, feed,
   and sitemap.
5. Add executable source-content and production-output checks. The source
   check must find no maintained scalar dependencies; the production build
   check must prove that both single-author and multi-author data reach the
   public surfaces and that existing generated routes remain present.
6. Only after both evidence classes pass, remove or reject the legacy form
   according to the approved requirement. Re-run the production build and
   test suite so the rejection cannot silently reintroduce a consumer
   dependency.
7. Update the maintained developer documentation with the final authoring
   form, compatibility status, and any migration command or validation
   expectations.

The decisive integration check is a real production build followed by
assertions against `_site`, not a template test with author data injected
directly. The transition test should exercise at least one legacy-shaped
input and one structured input before the legacy path is retired; the final
test state should exercise the migrated repository content and the approved
legacy rejection or retention policy.

### Implementation decisions and open questions

- This remains `Draft` until the structured schema, public multi-author
  rendering contract, and final legacy-retirement outcome are confirmed.
- The normalized author collection is a design direction, not an approved
  public field name or record shape.
- No source or generated files should be changed as part of planning.

### Documentation

- Update `README.md` with the supported post front-matter form and the
  authoring-helper contract, unless execution establishes a concrete need for
  a separate developer page. Do not create a placeholder documentation
  directory or page.
- Keep any transition-only compatibility note clearly labeled as such; after
  retirement, document only the supported current behavior.

### Task checklist

- [ ] Resolve the three requirement questions and mark this plan `Approved`
      before execution.
- [ ] Complete
      `tasks/20260925-author-metadata-migration/010-author-schema-transition.md`.
- [ ] Complete
      `tasks/20260925-author-metadata-migration/020-content-and-authoring-migration.md`.
- [ ] Complete
      `tasks/20260925-author-metadata-migration/030-generated-output-consumers.md`.
- [ ] Run the source-content inventory and the production generated-output
      assertions through the real Eleventy build.
- [ ] Apply the legacy-retirement gate only after both evidence classes pass.
- [ ] Update and inspect the maintained documentation.

### Requirement verification

- Structured model: the schema/transition subtask's contract test must prove
  that one-author and multi-author inputs normalize to the same consumer
  shape; the generated-output subtask's production-build assertions must prove
  that shape reaches public output.
- Compatibility and preservation: a transition-stage production build using
  a legacy-shaped input plus the migrated repository posts must retain the
  existing post, archive, tag, feed, and sitemap routes and preserve the
  existing post content.
- Templates, archives, and feed: `npm run build` followed by assertions on
  the individual post, home page, `/blog/`, tag page, and `/feed/feed.xml`
  must verify author output and route generation through the actual Eleventy
  path. Feed assertions must also validate the approved XML representation
  for more than one author.
- Authoring and content migration: an executable helper test must verify the
  new front matter, and a source inventory must show every maintained post has
  the structured field with no scalar `author` key.
- Legacy retirement: the final gate must record a clean source-content scan
  and a passing production generated-output scan before any rejection is
  enabled. The post-gate test must prove the approved rejection or retained
  compatibility behavior.
- Documentation: inspect the maintained documentation after the implementation
  changes and verify that its examples match the format exercised by the
  helper and production build.

### Additional implementation verification

- Run `npm test` with all executable tests collected and exiting cleanly.
- Run `npm run build` independently and inspect the expected output paths,
  rather than relying only on unit-level assertions.
- Search templates, scripts, tests, and content for direct legacy scalar
  references; distinguish the intentionally retained transition test from
  production dependencies.