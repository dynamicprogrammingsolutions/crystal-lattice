# Establish the structured author model and migrate posts

Define the canonical post metadata shape, centralize transition handling for
the legacy scalar field, and migrate the checked-in posts without changing
their public identity or content.

Parent Task: tasks/20260919-author-metadata-migration/000-main.md

## Requirements checklist

- [ ] The canonical field and entry shape are approved and documented in the
      implementation.
- [ ] The model preserves author order and supports current single-author
      posts as well as multiple authors.
- [ ] Existing post front matter is migrated without changing title, body,
      route, tags, or layout behavior.
- [ ] Legacy `author` input remains readable during the transition through one
      defined compatibility boundary.
- [ ] Ambiguous dual-field behavior is resolved and covered before execution
      marks this subtask complete.

## Requirement questions and decisions

- Confirm whether the canonical field is named `authors` and whether entries
  are objects with a required `name`, or whether a different approved shape
  is required.
- Confirm whether author identity/URL fields are in scope now or should remain
  absent until a later migration.
- Confirm the behavior when both `author` and `authors` are present.

## Supporting facts

- Current source files are `content/posts/first.md`,
  `content/posts/second.md`, and the cascade file
  `content/posts/posts.json`.
- Current source values are plain display-name strings, so migration must
  preserve their exact visible names.
- No data migration utility exists in the repository; the checked-in content
  is small enough for a reviewed, explicit source migration once the schema is
  approved.

## Execution plan

Status: Draft

Add the canonical metadata contract at the narrowest data boundary available
in the Eleventy fixture. During the compatibility window, normalize either
the new field or the approved legacy input into the same ordered author
collection consumed by templates. Migrate both checked-in posts to the new
front-matter shape and add focused fixtures for one and multiple authors.
Preserve the legacy path until the separate cutover task authorizes rejection.

### Implementation decisions and open questions

- Keep normalization out of individual Nunjucks templates so every consumer
  receives the same ordering and missing-data behavior.
- Do not invent fallback names or silently merge conflicting fields; use the
  approved dual-field policy once the requirement question is answered.
- The source migration is complete only when a production build proves the
  migrated documents still resolve to the same public routes.

### Documentation

- Add the canonical front-matter example to the owning authoring/developer
  documentation as part of this subtask or coordinate that update with the
  authoring-tool subtask.
- Record the compatibility-window status, not final legacy rejection, until
  the cutover evidence passes.

### Task checklist

- [ ] Confirm and record the canonical field/entry schema.
- [ ] Implement the centralized compatibility normalization.
- [ ] Migrate every checked-in post and preserve its existing metadata/body.
- [ ] Add focused one-author and multi-author source fixtures.
- [ ] Run the production build and verify routes/tags/content.

### Requirement verification

- Compare the migrated post metadata and rendered post artifacts against the
  pre-migration title, URL, body, and visible author values.
- Build at least one multi-author fixture and verify the normalized author
  order reaches the rendering boundary.
- Exercise a legacy-shaped fixture while compatibility is enabled to prove
  existing content remains readable.

### Additional implementation verification

- Search all source/templates/scripts for direct legacy-field reads and
  classify each remaining occurrence as compatibility code, test fixture, or
  unresolved dependency.
- Verify no migration step rewrites slugs, dates, tags, or post bodies.
