# Migrate post author metadata to structured multi-author data

Plan the staged migration from the single `author` front-matter string to a
structured field that can represent multiple authors, while preserving current
content and generated-site behavior until migration evidence permits removal of
the legacy form.

## Requirements checklist

- [ ] Adopt a reviewed structured post-author field that represents one or more
  named authors and becomes the supported authoring contract.
- [ ] Keep existing posts and generated pages working during the transition
  through an explicit compatibility boundary.
- [ ] Move post templates, home/archive/tag listings, feeds, and authoring tools
  to the structured model while preserving the site’s existing URL, ordering,
  and content contracts unless a changed author rendering is explicitly
  approved.
- [ ] Migrate every existing post safely, without losing front matter or body
  content.
- [ ] Update tests and maintained developer guidance with evidence for the
  structured model, compatibility period, migration, and cutover.
- [ ] Reject the legacy form only after source-content evidence and
  production-generated-output evidence show that no supported path still
  depends on it.

## Scope and workstreams

- Contract and inventory: define the field shape, output rules, compatibility
  boundary, and complete producer/consumer inventory.
- Runtime and generated output: normalize the transition data and update post
  layouts, listing/archive views, feeds, and related generated-output checks.
- Content and tooling: migrate existing post front matter and make the
  authoring helper emit the supported structure.
- Cutover and evidence: prove content and generated output are independent of
  the legacy field, then remove or reject legacy handling under a gated change.
- Documentation: keep the developer-facing authoring and migration guidance
  with the owning development documentation.

## Open requirement questions and material decisions

- What is the exact new field and value shape: an ordered `authors` array of
  names, or an ordered array of author records such as `{ name }` with
  identity/link fields?
- How should multiple authors be rendered in HTML post pages and archive
  listings, and how should they be serialized in the feed: one combined value,
  repeated author elements, links, or another reviewed contract?
- Does the authoring helper need to accept the legacy single-name argument
  during the compatibility period, or may its public input contract change
  immediately while only content/template reads remain dual-compatible?
- Are stable author identifiers, slugs, profile URLs, or author archive pages
  in scope? The current fixture has no author collection or author pages, so
  these should not be introduced without an explicit requirement.

Recommendation for review: use the smallest ordered structured value that
supports the required output (an `authors` list, with one entry for each
existing name) unless author identity or links are required. Keep any legacy
`author` interpretation in one normalization boundary, rather than spreading
fallback checks through templates.

## Supporting facts

- The post defaults in `content/posts/posts.json` provide the shared `post`
  layout and `posts` tag; individual posts currently define `author` as a
  quoted scalar.
- `_includes/layouts/post.njk` renders the current scalar in the post page.
- `_includes/postslist.njk` is shared by the home page, `/blog/` archive, and
  tag pages, but currently renders only title and URL. The migration must
  explicitly decide whether its author presentation changes or only its data
  contract does.
- `content/feed.xml.njk` reads `post.data.author`; the sitemap only emits page
  URLs and has no author dependency.
- `scripts/new-post.js` writes the legacy front matter and is the only
  discovered authoring producer.
- `tests/archive-output.test.js` and `tests/author-output.test.js` are
  comments describing intended coverage, not executable assertions.
- The repository has no `docs/index.md`; the applicable maintained
  development documentation is `docs/development/index.md`, alongside the
  repository README and guidance in `docs/development/documentation.md`.

## Execution plan

Status: Draft

First settle the author data and output contracts, then implement the
compatibility boundary and migrate consumers. Convert existing content with a
reviewable, deterministic operation and make the authoring helper produce only
the supported representation (or an explicitly approved transition input).
Exercise the real Eleventy build and inspect generated pages and feeds. Keep
the legacy reader and rejection test out of the final cutover until source and
generated-output scans demonstrate that no content or supported consumer still
uses the old field. Update the maintained development guidance only for the
behavior that is actually implemented and verified.

The ordered work is tracked in the subtasks below. Subtask 050 is the final
cutover gate and depends on all preceding work.

### Implementation decisions and open questions

The schema, multi-author rendering/serialization rules, and authoring-helper
transition input policy remain open requirement questions above. The plan
assumes a single normalization boundary and an ordered author collection, but
execution must not finalize the public shape until those questions are
answered.

### Documentation

Update the smallest relevant developer-facing documentation, likely
`docs/development/index.md` or a focused page under `docs/development/`, with
the supported front-matter shape, authoring-helper contract, compatibility
period, and evidence-based cutover rule. Update `README.md` only if it is the
maintained user/developer entry point for post authoring. Do not add a
placeholder documentation tree.

### Task checklist

- [ ] Review and resolve the author schema and output-contract questions.
- [ ] Complete subtask
  [tasks/20260919-author-metadata-migration/010-contract-and-inventory.md](010-contract-and-inventory.md).
- [ ] Complete subtask
  [tasks/20260919-author-metadata-migration/020-compatibility-and-rendering.md](020-compatibility-and-rendering.md).
- [ ] Complete subtask
  [tasks/20260919-author-metadata-migration/030-content-migration.md](030-content-migration.md).
- [ ] Complete subtask
  [tasks/20260919-author-metadata-migration/040-authoring-tool-and-guidance.md](040-authoring-tool-and-guidance.md).
- [ ] Complete subtask
  [tasks/20260919-author-metadata-migration/050-evidence-and-legacy-cutover.md](050-evidence-and-legacy-cutover.md).
- [ ] Record requirement evidence and completion notes after approved execution.

### Requirement verification

- The structured field and authoring contract are verified by executable
  front-matter/tool tests and a real production build containing at least
  single-author and multi-author posts.
- Transition safety is verified by building a representative legacy post
  alongside structured posts and asserting the post page, home/archive/tag
  output, feed, and preserved URL/order behavior.
- Safe content migration is verified by source inventory, reviewed front
  matter diffs, and a build using every migrated post.
- Legacy rejection is verified only after a source-content scan and generated
  output scan find no supported legacy dependency, plus a negative test proves
  the final boundary rejects the old form.

### Additional implementation verification

- Run the repository’s production build and test command after the cutover.
- Assert that feed output is valid for the chosen multi-author contract and
  that no raw legacy scalar is emitted.
- Preserve or explicitly review escaping/quoting behavior for names containing
  YAML- or HTML-sensitive characters.