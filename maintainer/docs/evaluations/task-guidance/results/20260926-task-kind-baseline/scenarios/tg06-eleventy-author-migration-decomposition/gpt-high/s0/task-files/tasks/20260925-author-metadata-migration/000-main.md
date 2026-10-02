# Migrate post author metadata

Plan the transition from the singular `author` post field to a structured,
ordered multi-author model while preserving existing content and generated
pages until the repository proves that the legacy field is no longer needed.

## Requirements checklist

- [ ] Posts use an approved structured multi-author metadata form that can represent one or more authors in a stable order.
- [ ] Existing post content is migrated safely, with no loss or unintended change to current author names.
- [ ] Post templates, archive paths, and feeds consume the new author model and continue to build successfully.
- [ ] The post-authoring helper emits the new model and no longer makes the singular field the normal authoring path.
- [ ] Legacy `author` input remains compatible during the migration transition and is rejected only after content and generated-output evidence demonstrate that no supported path depends on it.
- [ ] Maintained documentation describes the supported author metadata and transition state after implementation.

## Subtasks

The work is split by independently reviewable compatibility and ownership
boundaries:

- [ ] `tasks/20260925-author-metadata-migration/010-author-contract-and-content.md` owns the metadata contract, transition
  compatibility, and migration of source posts.
- [ ] `tasks/20260925-author-metadata-migration/020-rendering-and-generated-output.md` owns post rendering, archive
  traversal, feeds, and production-build evidence.
- [ ] `tasks/20260925-author-metadata-migration/030-authoring-tool.md` owns the post-generation helper and its contract
  documentation.
- [ ] `tasks/20260925-author-metadata-migration/040-legacy-retirement.md` owns the cross-surface evidence gate and removal
  of the legacy fallback.

## Unresolved requirement questions

- [ ] Confirm the public structured shape. Recommendation: replace `author`
  with an ordered `authors` array of objects such as `{ name: "Ada Example" }`
  so the model can grow without another front-matter migration. An ordered
  array of strings is a smaller alternative, but it is less extensible.
- [ ] Confirm whether archive listings should display author names as part of
  this migration. The current archive/list include displays titles only, so
  the minimum safe interpretation is to audit it for legacy reads and verify
  unchanged output; adding archive bylines would be a separate user-visible
  design choice.

## Decisions

- This task records a Draft plan only. No source content, templates, scripts,
  tests, or documentation are changed by creating these files.
- Compatibility is staged: accept the old field while new content and
  templates move to the new model, then remove/reject it only at the explicit
  evidence gate.
- Existing rendered names, URLs, feed location, and page coverage are
  preserved unless the user approves a separate output change.

## Research and supporting facts

- The current posts at `content/posts/first.md` and
  `content/posts/second.md` each contain a singular quoted `author` value.
- `_includes/layouts/post.njk` renders `author` directly.
- `content/feed.xml.njk` reads `post.data.author`; the archive and tag
  listing include currently render titles and links but do not read author
  metadata.
- `scripts/new-post.js` exports `frontMatter(title, author)` and emits the
  singular field.
- `tests/author-output.test.js` and `tests/archive-output.test.js` are
  placeholders for generated-output coverage; decisive evidence must run the
  real Eleventy build and inspect its output.
- `README.md` documents the generated site surfaces but not front matter or
  authoring conventions. `docs/development/index.md` contains no author
  specification.

## Execution plan

Status: Draft

The implementation should proceed as a staged data-contract migration. First
define and document the approved structured field and a temporary adapter that
can read legacy content. Migrate every checked-in post and update the
authoring helper to produce the new shape. Then update all production
consumers, including the post layout and feed, while auditing archive and tag
paths for indirect legacy dependencies. A real build must establish both
output preservation and correct multi-author rendering before the adapter and
singular-field acceptance are removed.

The migration boundary is deliberately evidence-driven:

1. Establish the approved schema and compatibility behavior.
2. Add focused source-content checks and migrate all existing posts.
3. Update production templates and the authoring helper, with generated-output
   assertions for posts, archives, feeds, and relevant metadata.
4. Run a repository-wide dependency search plus a clean production build and
   inspect representative generated files for old and new forms.
5. Only after those checks pass, remove the legacy fallback/rejection path and
   add a regression that fails if singular `author` metadata returns.

### Implementation decisions and open questions

- The recommended model is `authors` as an ordered array of `{ name }`
  records. The final field name, record shape, and any additional required
  fields remain blocked on the unresolved schema question above.
- The compatibility adapter must define behavior for legacy single-name
  content, new single-author content, and multiple authors. It must preserve
  author order and must not silently discard names.
- Feed representation for multiple authors must be decided with the schema:
  each author should have a deterministic XML representation, while the
  existing feed URL and entry coverage remain stable.
- No fallback behavior for malformed or empty author data is approved by this
  plan; decide validation and failure behavior when the schema is approved.

### Documentation

- Update the maintained package/development documentation in the same change
  as the implementation, most likely `README.md` or a focused authoring
  document if the approved contract warrants one.
- Document the new front-matter form, ordering semantics, the authoring helper
  input, and the fact that the singular field is transitional only until the
  retirement gate is complete.
- Do not describe the new model as current guidance until implementation and
  generated-output evidence make it true.

### Task checklist

- [ ] Resolve the structured-author schema and archive-display question.
- [ ] Complete `tasks/20260925-author-metadata-migration/010-author-contract-and-content.md`.
- [ ] Complete `tasks/20260925-author-metadata-migration/020-rendering-and-generated-output.md`.
- [ ] Complete `tasks/20260925-author-metadata-migration/030-authoring-tool.md`.
- [ ] Complete `tasks/20260925-author-metadata-migration/040-legacy-retirement.md`.
- [ ] Keep this plan Draft until the user approves execution.
- [ ] After approval, mark the plan Approved before changing implementation files.

### Requirement verification

- Structured metadata and safe source migration: inspect every post front
  matter and run the focused content/schema checks from subtask 010.
- Templates, archives, and feeds: run `npm run build` through the real
  Eleventy pipeline, then assert representative post, archive/tag, and feed
  output from the generated `_site` as specified by subtask 020.
- Authoring tool: test the exported helper with one and multiple authors and
  assert that its emitted front matter uses only the approved new model, as
  specified by subtask 030.
- Legacy rejection: combine repository-wide source/content search, migrated
  content inspection, clean generated-output inspection, and the regression
  guard from subtask 040. Do not mark this requirement complete from isolated
  template tests or mocked data.
- Documentation: review the maintained documentation against the implemented
  contract and transition state after the behavioral checks pass.