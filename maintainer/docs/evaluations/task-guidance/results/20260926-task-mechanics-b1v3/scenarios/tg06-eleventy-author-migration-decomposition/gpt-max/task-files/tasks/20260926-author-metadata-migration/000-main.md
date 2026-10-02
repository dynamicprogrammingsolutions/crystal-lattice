# Migrate post author metadata to structured multi-author data

Plan the staged migration of post author front matter from the current scalar
`author` value to an ordered structured author collection. The migration must
keep existing content and generated pages working while the new model is
introduced, then use content and production-build evidence before any legacy
rejection is enabled.

## Requirements checklist

- [ ] Define and implement an approved canonical multi-author data contract,
  including its ordering, rendering shape, and validation rules.
- [ ] Preserve the current behavior of existing posts and generated routes
  while both the canonical model and the legacy `author` form may be present
  during migration.
- [ ] Move post templates, archive/list surfaces, and feeds to consume the
  canonical author model; support multiple authors without emitting missing,
  duplicated, or malformed author data.
- [ ] Migrate every existing post to the canonical model without losing author
  names or their intended order.
- [ ] Update the authoring tool so newly generated front matter uses the
  canonical model and can represent the approved single- and multi-author
  cases safely.
- [ ] Produce generated-output and content evidence showing that no supported
  path still depends on the legacy form before rejecting it, if rejection is
  selected as the final compatibility state.
- [ ] Keep maintained developer/authoring documentation aligned with the
  supported front-matter model and the transition or final rejection state.

## Scope and workstreams

The migration is split by independently owned boundaries:

- The data-contract work owns the canonical representation and the one
  compatibility normalization boundary.
- The rendering work owns post pages, shared list/archive surfaces, feeds, and
  generated-output assertions.
- The content/authoring work owns existing source posts, the post-generation
  helper, and the real production-path check connecting generated front matter
  to Eleventy output.
- The retirement work owns the evidence gate and the final decision to retain
  compatibility or reject the legacy form.

This plan does not authorize implementation. The task files remain `Draft`
until execution is explicitly approved.

## Requirement questions and decisions

- **Question — canonical entry shape:** Should `authors` be an ordered list of
  display-name strings, or an ordered list of records such as `{ name }` with
  room for identity/link metadata? The plan uses “ordered author collection”
  until this is answered and does not invent identity, URL, or attribution
  semantics.
- **Question — archive presentation:** The current shared `postslist.njk`
  renders titles and links but no author. Does “archives move to the new
  model” require adding archive bylines, or should existing archive markup be
  preserved while all author-aware archive code is audited to use the
  canonical collection? The plan currently preserves existing visible output
  unless a byline requirement is approved.
- **Question — final compatibility state:** Should the completed migration
  reject legacy `author` input, or retain a read fallback indefinitely?
  Recommendation: make rejection a final, explicit phase only after the gate
  passes; if indefinite compatibility is preferred, document that state and
  retain the normalizer.
- **Question — conflicting fields:** What should happen when a source item
  contains both the canonical field and legacy `author`, or contains an empty
  or malformed author collection? This needs an explicit validation policy
  before implementation so precedence is not silently invented.
- **Decision required by the request:** No legacy rejection may be introduced
  before both the content audit and the generated-output evidence pass.

## Research and supporting facts

- The site is a compact Eleventy build. `package.json` exposes `npm run build`
  and `npm test`; the production output is `_site/`.
- `content/posts/posts.json` applies `layouts/post.njk` and the `posts` tag to
  all posts. The existing posts use scalar `author` front matter in
  `content/posts/first.md` and `content/posts/second.md`.
- `_includes/layouts/post.njk` reads `author` directly. The feed template
  reads `post.data.author` directly.
- `content/blog.njk`, `content/index.njk`, and `content/tag-pages.njk` all
  reach the shared `_includes/postslist.njk`. That include currently emits
  only title links, so archive compatibility needs an explicit audit rather
  than an assumed author rendering change.
- `content/sitemap.xml.njk` does not read author data, but it is part of the
  generated-page regression surface and should remain buildable.
- `scripts/new-post.js` currently accepts `(title, author)` and writes a scalar
  `author` key. Its output is not currently covered by a substantive test.
- `tests/archive-output.test.js` and `tests/author-output.test.js` are
  placeholders describing intended generated-output coverage rather than
  executable assertions.
- There is no existing `tasks/` tree and no root `docs/index.md`. The
  maintained development documentation is under `docs/development/`; the
  documentation guidance has been read before planning this change.

## Subtasks

- [ ] [tasks/20260926-author-metadata-migration/010-schema-compatibility.md](tasks/20260926-author-metadata-migration/010-schema-compatibility.md)
- [ ] [tasks/20260926-author-metadata-migration/020-rendering-output.md](tasks/20260926-author-metadata-migration/020-rendering-output.md)
- [ ] [tasks/20260926-author-metadata-migration/030-content-authoring.md](tasks/20260926-author-metadata-migration/030-content-authoring.md)
- [ ] [tasks/20260926-author-metadata-migration/040-legacy-retirement.md](tasks/20260926-author-metadata-migration/040-legacy-retirement.md)

## Requirement ownership

- The canonical data contract and transition compatibility requirements are
  owned by `010-schema-compatibility.md`; the final compatibility state is
  completed jointly with `040-legacy-retirement.md`.
- The post, archive/list, feed, and generated-page requirements are owned by
  `020-rendering-output.md`.
- Existing-source migration and authoring-tool requirements are owned by
  `030-content-authoring.md`, with its production-output connection verified
  through `020-rendering-output.md`.
- The evidence gate, conditional legacy rejection, and final documentation
  state are owned by `040-legacy-retirement.md`, using the preceding
  subtasks’ build evidence.

## Execution plan
Status: Draft

The migration will use a staged compatibility flow. A single page-data
normalizer will expose the approved canonical author collection to every
consumer. During the transition it may translate legacy `author` into a
single-entry canonical collection, but templates and tools will not duplicate
that fallback logic. Existing posts will be converted before the compatibility
path is considered for removal.

The canonical collection is an ordered interface: order in front matter must
be retained in post bylines, archive bylines if approved, and feed output.
The exact entry shape and conflict policy are open requirements questions above.
Singleton output should preserve current visible text, markup, routes, and
feed meaning wherever possible; multi-author output must be deterministic and
valid for the selected output format.

The work proceeds in this order:

1. Resolve the canonical `authors` shape, conflict behavior, and output
   semantics, then implement the shared compatibility/normalization boundary.
2. Update the post layout, shared archive/list path, and feed to consume only
   normalized authors. Replace the placeholder generated-output coverage with
   assertions for a legacy-compatible singleton, a canonical singleton, and a
   multi-author post.
3. Migrate all current post front matter and update `new-post.js` to emit the
   canonical field. Connect the authoring helper to the real Eleventy path by
   building content generated from the helper and checking the resulting post
   and feed, rather than testing serialization in isolation only.
4. Run the content inventory and clean production build. Review every remaining
   runtime reference to `author`; classify intentional compatibility fixtures
   separately from supported content and consumers.
5. Only after the evidence gate passes, apply the approved final compatibility
   state: either remove the fallback and reject legacy input with a clear
   diagnostic, or retain the fallback and document it as supported. Run the
   full build and tests again after that state change.

The parent build check must exercise the real Eleventy input, collection,
template, feed, and output directories together. A mocked `post.data` object
or a template-only unit test is not sufficient evidence that the migration
works end to end.

### Implementation decisions and open questions

- The working field name is `authors`, pending confirmation of the exact
  scalar-versus-record entry shape.
- Normalization belongs at the page/collection data boundary so raw legacy
  access does not spread across templates.
- Archive bylines and the final rejection policy remain requirement decisions,
  not implementation assumptions.
- If implementation reveals an additional public-contract choice, return the
  plan to `Draft` and record the choice before executing that part.

### Documentation

Update `docs/development/index.md` or a more focused document under
`docs/development/` only if the authoring contract needs more room than the
existing index. Document the canonical front-matter example, ordering and
rendering semantics, the transition fallback if retained, and the evidence
condition for any rejection. Do not document the target as current guidance
until the corresponding implementation and build evidence exist.

### Task checklist

- [ ] Resolve the requirement questions and mark the plan `Approved` before
  implementation.
- [ ] Complete `010-schema-compatibility.md`.
- [ ] Complete `020-rendering-output.md`.
- [ ] Complete `030-content-authoring.md`.
- [ ] Complete `040-legacy-retirement.md`.
- [ ] Review the final build, tests, content scan, and maintained
  documentation together.

### Requirement verification

- **Canonical contract and safe transition:** Verify the approved canonical and
  legacy inputs through the shared normalizer and a real Eleventy build. The
  decisive evidence is that both input forms reach the same canonical
  rendering/feed boundary without raw `author` reads in consumers.
- **Templates, archives, feeds, and generated pages:** Run the production
  build and inspect/assert the post page, home page, blog archive, tag page,
  feed, and sitemap. Verify existing routes and singleton output remain valid
  and that a multi-author source produces deterministic output.
- **Existing content migration:** Scan all post source files for legacy
  front-matter keys, inspect the migrated names/order, then build those exact
  sources and assert their names appear in the expected generated outputs.
- **Authoring tool:** Invoke `scripts/new-post.js` for approved one- and
  multi-author inputs, use its generated front matter as real post input, run
  Eleventy, and assert the generated post/feed output. This is the decisive
  check for the helper-to-site connection.
- **Evidence-gated legacy retirement:** Record the content scan, runtime
  reference audit, pre-retirement generated-output results, and post-retirement
  build/test results. A rejection change is complete only when all four are
  clean; otherwise the compatibility fallback remains and the unresolved state
  is documented.

### Additional implementation verification

- Check YAML/JSON escaping for names containing punctuation or quotes.
- Check empty, duplicate, and malformed author entries according to the
  approved validation policy.
- Check that the migration does not create `[object Object]`, `undefined`,
  duplicate feed authors, or empty bylines in generated output.
- Check the final diff for accidental route, title, tag, or sitemap changes.