# Migrate post authors to structured multi-author metadata

Plan the staged migration from the post front matter `author` string to an
approved structured multi-author representation while preserving existing
content and generated-site behavior until the repository proves that the
legacy form is no longer needed.

## Requirements checklist

- [ ] Adopt an approved canonical structured multi-author field and use it as
  the only author metadata consumed by production rendering after cutover.
- [ ] Preserve a compatibility path for legacy `author` content during the
  transition, so existing posts and builds continue to work while content is
  being migrated.
- [ ] Move post templates, archive/listing paths, feeds, and the post-authoring
  tool to the canonical multi-author model, including deterministic rendering
  for more than one author.
- [ ] Migrate every existing post safely without changing its title, body,
  route, or unrelated front matter.
- [ ] Reject the legacy form only after generated-output evidence and source
  content evidence demonstrate that no supported content or production path
  still depends on it.
- [ ] Update maintained authoring/development documentation to describe the
  canonical field, transition boundary, and any intentional compatibility or
  rejection behavior.

## Scope and workstreams

The work is split by independently reviewable boundaries:

- [Metadata contract, content migration, and authoring tool](./010-metadata-content-tooling.md)
  owns the canonical shape, transition normalization, existing-post rewrite,
  and generated front matter.
- [Production rendering and generated-output evidence](./020-rendering-and-output.md)
  owns post pages, archive/listing routes, feeds, and tests that cross the
  real Eleventy build.
- [Cutover gate and legacy rejection](./030-cutover-and-rejection.md) owns
  the final dependency audit and the strict rejection change after the
  evidence gate passes.

## Subtasks

- [ ] `tasks/20260925-author-metadata-migration/010-metadata-content-tooling.md`
- [ ] `tasks/20260925-author-metadata-migration/020-rendering-and-output.md`
- [ ] `tasks/20260925-author-metadata-migration/030-cutover-and-rejection.md`

The task does not include unrelated archive pagination, URL redesign, author
profiles, or changes to post body content.

## Unresolved requirement questions and decisions

- The repository does not specify the exact structured author schema. Confirm
  the public front matter shape before execution. Recommendation, not yet an
  approved decision: use an `authors` array whose entries are structured
  records with a required display `name`, leaving room for stable identity or
  profile fields without forcing them into this migration.
- Confirm whether archive/list pages should newly display author names or only
  route their existing post data through the canonical field. The migration
  must make all author-aware archive rendering canonical; adding visible author
  text changes archive output and therefore needs an explicit product choice.
- Confirm the desired feed representation for multiple authors. Recommendation,
  not yet an approved decision: preserve the existing feed element shape and
  emit one author element per canonical author in source order.
- Confirm the enforcement boundary for legacy rejection. Recommendation, not
  yet an approved decision: fail the production build with an actionable
  message when a post still contains `author`, and make the authoring tool
  generate only the canonical field.

## Research and supporting facts

- Existing posts use a scalar `author` front matter value in
  `content/posts/first.md` and `content/posts/second.md`.
- `_includes/layouts/post.njk` renders the scalar directly, while
  `content/feed.xml.njk` reads `post.data.author` directly.
- `content/index.njk`, `content/blog.njk`, and `content/tag-pages.njk` all
  share `_includes/postslist.njk`; that partial currently renders titles only,
  so archive author behavior must be decided and then covered explicitly.
- `scripts/new-post.js` currently emits the legacy field through
  `frontMatter(title, author)`.
- `tests/archive-output.test.js` and `tests/author-output.test.js` are
  placeholders rather than decisive generated-output tests.
- The production output directory is `_site/` and is ignored by Git. The
  verification plan must therefore assert against a real build or a
  deliberately captured route/output manifest rather than relying on committed
  generated files.
- `README.md` describes the generated site at a high level but does not
  document post front matter or the authoring helper. `docs/development/index.md`
  currently contains only an archive-pagination note.

## Execution plan

Status: Draft

The migration will use a canonical-data boundary between front matter and
templates. During the transition, that boundary accepts the legacy scalar and
normalizes it to the canonical multi-author value; templates, feeds, archives,
and the authoring helper depend only on the canonical value. Existing posts are
then rewritten at the front matter boundary with a narrow, content-preserving
transform. The compatibility branch remains in place until the final audit
proves that committed content and production consumers no longer use it.

The production-output boundary is the decisive integration point. A real
Eleventy build must continue to produce the existing route set, individual
post output, archive/tag pages, feed, and sitemap while emitting the approved
multi-author result. Tests must inspect generated output and source content,
not only mocked template data. Only after those checks pass may the
normalization boundary become strict and reject legacy `author`.

### Implementation decisions and open questions

- Treat the exact `authors` schema, archive display choice, feed shape, and
  rejection surface listed above as approval questions. Do not begin
  implementation with an invented public contract.
- Keep the compatibility conversion at one data boundary so no template or
  feed needs to branch on old versus new front matter.
- Make migration idempotent and narrow: alter only the author field and its
  required serialization, preserve title/body/unrelated front matter, and
  report files that do not match the expected shape instead of guessing.
- Preserve author ordering from source content in post pages, archives, and
  feeds unless the approved schema explicitly defines another ordering.
- Treat generated route preservation and author rendering as one production
  check. Component-level assertions alone are not sufficient evidence for the
  migration.

### Documentation

After the behavior is implemented, update the maintained documentation owned by
this fixture: document the canonical post front matter and authoring helper in
`README.md`, and add only the smallest development note needed to explain the
transition/rejection gate. Do not add a placeholder documentation hierarchy.

### Task checklist

- [ ] Approve the canonical structured author schema and the archive/feed
  output decisions.
- [ ] Complete `010-metadata-content-tooling.md`.
- [ ] Complete `020-rendering-and-output.md`.
- [ ] Complete `030-cutover-and-rejection.md` after the first two subtasks
  provide their evidence.
- [ ] Update the maintained documentation in the owning implementation
  subtask.
- [ ] Review the final requirement evidence and leave this parent task in a
  state that clearly distinguishes completed checks from any human approval
  still needed.

### Requirement verification

- Canonical field and transition compatibility: decisive evidence is the
  metadata/content/tooling subtask's normalization and migration checks plus a
  real build that consumes both a legacy-shaped transition fixture and the
  migrated posts before strict rejection.
- Templates, archives, and feeds: decisive evidence is the rendering
  subtask's production-build test, which checks post pages, `/`, `/blog/`,
  every generated tag page, and `/feed/feed.xml` for canonical multi-author
  output and absence of undefined author data.
- Safe migration of existing content: decisive evidence is a source inventory
  and migration assertion that every existing post has the canonical field and
  that title/body/unrelated front matter remain unchanged.
- Conditional legacy rejection: decisive evidence is the cutover subtask's
  ordered audit—source/reference scan, generated-output assertions, and the
  complete test/build run—recorded before the strict rejection is enabled.
- Documentation: decisive evidence is inspection of the updated maintained
  authoring/development documentation against the final implemented contract.

### Additional implementation verification

- Run the repository's declared test and build commands with the normal
  production path; do not count placeholder or mocked-only checks as proof.
- Check for accidental output changes outside author metadata by comparing the
  pre-migration and post-migration route sets and stable page fields.
- Verify that malformed or mixed old/new metadata is reported clearly rather
  than silently discarded during migration or cutover.