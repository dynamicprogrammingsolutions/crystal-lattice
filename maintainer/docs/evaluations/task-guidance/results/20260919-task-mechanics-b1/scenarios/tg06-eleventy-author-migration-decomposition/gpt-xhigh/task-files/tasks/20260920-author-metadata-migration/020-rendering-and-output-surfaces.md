# Move author rendering across pages, archives, and feeds

Convert the production templates and all archive/list entry points to consume
the structured author collection, while preserving generated output for
existing one-author posts and defining deterministic multi-author output.

Parent Task: tasks/20260920-author-metadata-migration/000-main.md

Depends On: tasks/20260920-author-metadata-migration/010-source-contract-and-content-migration.md

## Requirements checklist

- [ ] The post layout renders authors from the canonical structured field.
- [ ] The shared archive/list path and its home, blog, and tag-page consumers no
  longer depend on the legacy field when author data is rendered or exposed.
- [ ] The feed renders the canonical author data according to the approved
  feed representation.
- [ ] Legacy-form input remains renderable during the approved transition
  window, if the parent compatibility decision requires it.
- [ ] One-author output remains compatible with the current generated pages,
  while multiple authors are complete and deterministic.

## Unresolved requirement questions and decisions

- The parent task must approve the visible multi-author formatting and the
  feed serialization before this subtask can define exact assertions.
- The current archive list renders only titles and URLs. Confirm whether the
  migration should add an author byline there or only ensure that any existing
  or newly exposed archive author data uses the canonical field.
- Decide whether the feed emits one author element per author or one
  serialized element, and preserve the existing feed contract for a
  one-author post unless the approved migration explicitly changes it.

## Research and supporting facts

- `_includes/layouts/post.njk` currently prints `{{ author }}`.
- `content/feed.xml.njk` currently prints `post.data.author` inside each
  entry.
- `content/index.njk`, `content/blog.njk`, and `content/tag-pages.njk` all
  include `_includes/postslist.njk`.
- `_includes/postslist.njk` currently prints only `post.data.title` and
  `post.url`; it is the shared integration point for all three archive paths.
- `tests/author-output.test.js` and `tests/archive-output.test.js` do not
  currently run a build or assert generated output.

## Execution plan

Status: Draft

Using the canonical field from subtask 010, update the post layout, shared
archive/list rendering, and feed template. Keep compatibility handling at the
approved boundary so templates do not each implement divergent legacy
fallbacks. If archive bylines are part of the approved output, render them
through one shared author formatter and exercise home, blog, and tag pages.
If archives intentionally remain title-only, verify they do not read the
legacy field and add coverage that the shared path remains safe with canonical
data.

Replace the placeholder tests with production-build assertions. Build the
site using the normal Eleventy command, then inspect representative generated
post, home, blog, tag, and feed files. Include a multi-author fixture or
migrated post so the tests prove list completeness, ordering, escaping, and
feed validity rather than only checking that files exist.

### Implementation decisions and open questions

- Centralize any presentation logic needed by several templates so post,
  archive, and feed output cannot drift.
- Do not remove transition support from templates until subtask 030 has
  completed its source and generated-output evidence gate.
- Resolve archive byline behavior and feed element shape before fixing exact
  output assertions.

### Documentation

Supply the final visible/output examples and feed behavior to the parent
documentation update. Do not document unverified generated output as a
supported contract.

### Task checklist

- [ ] Confirm archive presentation and feed serialization.
- [ ] Update the post layout to consume canonical authors.
- [ ] Update the shared archive/list integration and all archive consumers as
  required by the approved output contract.
- [ ] Update the feed to consume canonical authors.
- [ ] Replace placeholder author/archive tests with production-build checks.
- [ ] Verify legacy-form rendering during the transition.
- [ ] Update this subtask with implementation and completion notes after
  execution.

### Requirement verification

- **Post rendering:** Run the real build and assert the generated post page
  contains the approved one- and multiple-author representation.
- **Archive paths:** Inspect generated home, blog archive, and tag archive
  pages and assert the shared list path is compatible with canonical author
  data and has no legacy-field dependency.
- **Feed:** Inspect the generated feed XML and assert every author is present,
  ordered, escaped, and serialized according to the approved contract.
- **Transition:** Build with a real legacy-form post before cutover and
  compare its author output with the equivalent canonical post.
- **Regression:** Confirm existing titles, URLs, post bodies, and one-author
  author output remain intact in the generated files.