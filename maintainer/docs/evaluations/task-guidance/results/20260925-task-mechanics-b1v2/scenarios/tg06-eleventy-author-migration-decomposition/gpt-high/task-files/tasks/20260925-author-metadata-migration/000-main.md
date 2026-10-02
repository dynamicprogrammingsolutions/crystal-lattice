# Migrate post author metadata to structured multi-author data

Plan the migration from the single `author` front-matter string to a
structured representation that can express multiple authors while preserving
existing posts and generated output throughout the transition.

## Requirements checklist

- [ ] Establish and document one canonical structured multi-author metadata
  contract for posts, including the representation of one author and multiple
  authors.
- [ ] Keep existing content and generated pages working during the transition
  while the legacy single-name form still exists.
- [ ] Move post pages, archive/list views, tag/home post lists, feeds, and any
  shared templates that expose author data to the structured model.
- [ ] Update the post-authoring tool to emit the canonical structured form and
  define how its inputs represent one or more authors.
- [ ] Migrate every existing post safely without losing author identity,
  ordering, or other front matter.
- [ ] Retire or reject the legacy form only after generated-output checks and
  source-content evidence demonstrate that no supported path still depends on
  it.
- [ ] Update maintained developer/authoring documentation to describe the
  supported form and the transition or rejection behavior.

## Scope and workstreams

The work is split by independently reviewable ownership boundaries:

- [ ] [tasks/20260925-author-metadata-migration/010-data-contract-and-authoring.md](010-data-contract-and-authoring.md)
  owns the metadata contract, authoring tool, compatibility normalization, and
  migration of the existing post corpus.
- [ ] [tasks/20260925-author-metadata-migration/020-public-rendering-surfaces.md](020-public-rendering-surfaces.md)
  owns post, archive/list, tag/home, and feed rendering of the structured
  authors.
- [ ] [tasks/20260925-author-metadata-migration/030-transition-gate-and-documentation.md](030-transition-gate-and-documentation.md)
  owns the final evidence gate, legacy-form retirement/rejection, and
  maintained authoring documentation.

## Unresolved requirement questions

- What is the exact structured value shape: an array of names, or an array of
  author records with fields such as name, URL, or identifier? This changes the
  authoring contract and generated markup, so it must be approved before
  implementation.
- In archive, home, and tag list views, should author names be displayed, and
  if so, should they be plain text or links? The current shared list renders
  titles only, while the request requires archive surfaces to move to the new
  model.
- During the transition, should legacy `author` be normalized as a temporary
  fallback when `authors` is absent, or should migrated content be the only
  supported input while a separate compatibility check reports stragglers?
- Once the evidence gate passes, should an old `author` field fail the build
  with a clear validation error, or should it remain accepted but deprecated?

## Decisions

- This is planning only; no implementation, content migration, generated
  output, or test changes are authorized by this handoff.
- The production Eleventy build is the decisive integration boundary. Unit
  checks that inject already-normalized data cannot alone prove the migration.
- The legacy form remains available to the compatibility path until the
  generated-output and source-content evidence required by the user has
  passed.
- Existing author identity and ordering are preserved as migration invariants;
  no author merge, deduplication, or identity enrichment is assumed.
- Tests and documentation stay with the workstream that owns the behavior they
  prove or describe; there is no standalone test-only or documentation-only
  child.

## Research and supporting facts

- The production input directory is `content`, with shared templates under
  `_includes`; Eleventy writes generated pages to `_site`.
- Post metadata is inherited from `content/posts/posts.json`, and the current
  post layout reads `author` directly.
- The current feed reads `post.data.author` directly. The shared
  `_includes/postslist.njk` is used by the home page, `/blog/`, and generated
  tag pages, but currently renders titles only.
- Existing content consists of `content/posts/first.md` and
  `content/posts/second.md`, each with a quoted single-name `author` field.
- `scripts/new-post.js` emits the legacy field and accepts one author argument.
- The repository exposes `npm run build` and `npm test`; the current author
  test file is a placeholder comment rather than an executable assertion.
- Maintained development documentation currently consists of
  `docs/development/index.md`; there is no `docs/index.md` and no existing
  task directory.

## Execution plan

Status: Draft

The migration should establish one canonical author data boundary before
changing presentation. Content and the authoring tool will converge on the
same structured value; a temporary normalization/compatibility layer will
allow old content to render while migration evidence is collected. Templates
will consume normalized structured authors rather than branching independently
on legacy and new fields. The final workstream will scan source content and
the repository’s author consumers, build the site through Eleventy, inspect
the relevant generated pages and feed, and only then remove or reject the
legacy field according to the approved policy.

Execution order:

1. Resolve the four requirement questions above and record the chosen schema,
   archive presentation, compatibility behavior, and post-gate failure mode.
2. Execute `010-data-contract-and-authoring.md`: implement the canonical
   metadata contract, update the authoring tool, and migrate all existing
   posts while preserving their content.
3. Execute `020-public-rendering-surfaces.md`: update the shared post/list
   templates and feed, then add output assertions that exercise the actual
   Eleventy build.
4. Execute `030-transition-gate-and-documentation.md`: run the complete
   build and tests, inspect generated post/archive/tag/feed output, scan source
   content and author consumers for legacy dependencies, and retire or reject
   the old form only after those checks pass.
5. Update the task checklists and requirement evidence as each boundary is
   completed. Record any approved plan change before implementing it.

### Implementation decisions and open questions

The unresolved questions above are material because they alter the metadata
shape or public output and must be answered before the plan can become
Approved. The recommended direction is a minimally structured ordered list
whose entries retain the author name, with additional fields added only if the
repository has a real consumer for them. The compatibility layer should be
temporary and explicit, and the post-gate behavior should produce a clear
build-time error if rejection is chosen. These are recommendations, not
approved requirements.

### Documentation

Update `docs/development/index.md`, or add one focused page under
`docs/development/` only if the approved contract needs more room, to cover
the canonical front matter, authoring-tool input, migration compatibility, and
the condition under which the legacy field is rejected. Keep target-only
transition text visibly marked until implementation makes it current.

### Task checklist

- [ ] Resolve the material schema, archive presentation, compatibility, and
  post-gate behavior questions.
- [ ] Complete the data-contract and authoring workstream.
- [ ] Complete the public-rendering workstream.
- [ ] Complete the transition evidence, legacy retirement, and documentation
  workstream.
- [ ] Reconcile all requirement evidence and append immutable completion notes
  after implementation is actually complete.

### Requirement verification

- Structured contract and authoring tool: decisive evidence is the updated
  authoring-tool output plus migrated post front matter consumed by the real
  Eleventy build.
- Existing-content safety: decisive evidence is a clean build of every
  migrated post with assertions that each original author and post remains in
  the expected generated output.
- Public surfaces: decisive evidence is one production build inspected by
  executable assertions for a post page, `/blog/`, a generated tag page, and
  `/feed/feed.xml`, covering every author in the approved order.
- Legacy retirement: decisive evidence is the source-content and consumer scan
  plus the same production build succeeding after the approved rejection or
  removal is enabled. No mock-only check satisfies this gate.
- Documentation: decisive evidence is review of the maintained development
  documentation against the implemented contract and final transition state.

### Additional implementation verification

- Check that HTML/XML escaping remains correct for author names containing
  characters meaningful to markup.
- Check that zero, one, and multiple-author cases follow the approved
  validation and rendering policy.
- Check that the authoring tool’s output is parseable front matter and that
  unrelated title/content fields remain unchanged during migration.