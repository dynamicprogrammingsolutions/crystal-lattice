# Migrate post author metadata to structured multi-author records

Plan the migration from the single `author` front-matter string to a structured
multi-author representation while preserving existing content, routes, and
generated pages throughout the transition.

## Requirements checklist

- [ ] R1. Posts use an approved structured metadata form that represents one or
  more authors without losing each author's display name.
- [ ] R2. Every existing post is migrated safely to the new form, preserving
  its author data and all existing generated URLs/content.
- [ ] R3. The post layout, shared post-list/archive paths, tag pages, and feed
  consume the new author model and render valid output for one and multiple
  authors.
- [ ] R4. The post-authoring helper writes the new form for newly created posts
  and does not create new dependencies on the legacy field.
- [ ] R5. Legacy `author` metadata is tolerated only during the migration
  window and is rejected or removed only after repository-content and
  production-generated-output evidence demonstrates that no supported path
  still depends on it.

## Unresolved requirement questions

- Q1. What is the canonical record shape? Recommended target: an `authors`
  sequence of objects with a required `name` field, leaving room for a stable
  identifier or profile URL later. Confirm whether names alone are sufficient
  or whether identity/link fields are required now.
- Q2. Should archive, home, and tag list entries begin displaying all author
  names, or should they retain their current title-only presentation while
  becoming safe consumers of the new metadata? The current shared list emits
  titles only, so adding author text would be a user-visible presentation
  change.
- Q3. After the evidence gate, should legacy front matter fail the build with a
  validation error, or should it be ignored as unsupported input? A clear
  build-time error is recommended so an accidental regression cannot silently
  lose author data.

## Research and supporting facts

- `content/posts/first.md` and `content/posts/second.md` are the only current
  posts; both use a quoted scalar `author` value.
- `_includes/layouts/post.njk` renders `author` directly.
- `content/feed.xml.njk` reads `post.data.author` directly.
- `_includes/postslist.njk` currently renders only title and URL, but it is
  shared by `content/index.njk`, `content/blog.njk`, and
  `content/tag-pages.njk`; those archive paths still need production-build
  coverage during the migration.
- `scripts/new-post.js` exports `frontMatter(title, author)` and writes the
  legacy field, making it the authoring boundary for new content.
- `tests/archive-output.test.js` and `tests/author-output.test.js` contain
  comments only; they do not currently collect or assert behavior.
- `README.md` documents the generated site at a high level. There is no
  existing author-metadata guide or checked-in generated `_site`.
- `package.json` provides `npm run build` and `npm test`; no lockfile or
  `node_modules` directory is present in the inspected worktree.

## Execution plan

Status: Draft

The proposed design uses a canonical `authors` sequence of author records and
keeps a read-only compatibility normalization for legacy `author` input during
the migration window. Source migration and the authoring helper stop producing
the legacy key. Rendering consumes one normalized sequence, so the post page
can render all names and the feed can emit the appropriate author elements
without interpolating an object as a string. The archive/list paths retain
their existing routes and presentation unless Q2 approves an author display
change.

Legacy support is not removed as part of source conversion or template
conversion. The final cutover is a separate dependent boundary: first scan
content and implementation references, then run the real Eleventy build and
inspect the post, archive, tag, home, and feed outputs. Only passing evidence
may authorize deleting the compatibility path and enabling the approved
legacy-input rejection behavior.

Ordered work:

1. Resolve Q1–Q3 and record the approved schema, archive presentation, and
   post-cutover invalid-input behavior.
2. Define the normalized author contract, migrate the existing post files, and
   update `scripts/new-post.js` so newly authored content uses the canonical
   form.
3. Update the post layout, feed, and shared archive/list consumers to use the
   normalized multi-author data while preserving routes and valid output.
4. Replace placeholder tests with production-path checks for migrated content,
   single- and multi-author rendering, all archive routes, and the feed.
5. Run the content-reference and generated-output evidence gate. If it passes,
   remove legacy production dependencies and add the approved regression check
   for rejected legacy input; otherwise keep compatibility and record the
   remaining dependency.
6. Update the maintained developer documentation with the current metadata
   shape and authoring/migration behavior in the same change as the final
   implementation.

## Subtasks

- [ ] `tasks/20260926-author-metadata-migration/010-source-and-authoring.md`
- [ ] `tasks/20260926-author-metadata-migration/020-public-rendering.md`
- [ ] `tasks/20260926-author-metadata-migration/030-legacy-cutover.md`

### Implementation decisions and open questions

- The task remains Draft until the canonical record shape, archive
  presentation, and post-cutover legacy-input behavior are approved.
- The compatibility reader belongs to the transition, not the final contract;
  no child may remove it before the cutover child records both content and
  generated-output evidence.
- The migration must preserve existing route paths and post body content. Any
  desired new author links or identifiers should be added only if Q1 approves
  them.

### Documentation

Update `README.md` or the nearest existing developer-facing documentation
section, rather than creating an empty documentation hierarchy. Document the
canonical front-matter shape, how the authoring helper creates it, the
temporary legacy compatibility state while applicable, and the final
unsupported-input behavior. Keep the documentation change with the
implementation that makes each claim true.

### Task checklist

- [ ] Resolve the three requirement questions before marking this plan
  Approved.
- [ ] Complete the source/content/authoring child.
- [ ] Complete the public-rendering child.
- [ ] Complete the evidence-gated cutover child.
- [ ] Update the requirement evidence and parent status as each child closes.

### Requirement verification

- R1: A production build of representative single- and multi-author source
  posts, backed by a direct authoring-helper assertion, proves that the
  approved structured records survive parsing and render as intended.
- R2: A repository-wide content scan plus the production build verifies that
  every existing post has the new metadata, retains its author names, and
  preserves existing post/archive/tag URLs and body output.
- R3: One real `npm run build` followed by assertions over the post page,
  `/`, `/blog/`, generated tag pages, and `/feed/feed.xml` is the decisive
  check across the shared templates and public generation paths.
- R4: The authoring-helper test verifies the emitted front matter, and a
  generated post created from that output is consumed by the same Eleventy
  build used for R3.
- R5: The final cutover records both (a) no remaining legacy-key dependencies
  in source content/templates/tools/tests and (b) successful generated-output
  inspection for every affected route before any rejection is enabled.

### Additional implementation verification

- Check for accidental `[object Object]`, missing names, malformed feed
  elements, duplicate author output, and unsafe escaping in generated HTML/XML.
- Compare the route set before and after migration so metadata changes do not
  silently alter permalink, archive, tag, or feed generation.
- Keep the transition testable without changing production paths or adding a
  test-only data shortcut.