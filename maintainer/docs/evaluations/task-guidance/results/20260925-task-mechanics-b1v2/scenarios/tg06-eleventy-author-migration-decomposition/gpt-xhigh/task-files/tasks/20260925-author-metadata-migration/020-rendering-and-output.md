# Move production rendering to canonical authors

Own all generated author output: individual post templates, shared archive
listing paths, feeds, and the tests that verify the real Eleventy production
build.

Parent Task: tasks/20260925-author-metadata-migration/000-main.md

Depends On: tasks/20260925-author-metadata-migration/010-metadata-content-tooling.md

## Requirements checklist

- [ ] Render the canonical multi-author value in individual post pages with
  stable ordering and no legacy-field lookup.
- [ ] Ensure the shared listing used by the home page, blog archive, and tag
  pages is compatible with and, where approved, displays the canonical
  multi-author value.
- [ ] Emit the approved representation for all authors in the feed without
  losing authors or producing undefined values.
- [ ] Preserve the generated route set and unrelated page content while
  changing author metadata.
- [ ] Replace placeholder tests with decisive generated-output coverage.

## Unresolved requirement questions and decisions

- Apply the parent-approved archive display decision. If archives remain title
  only, prove that their production path still carries no legacy author read;
  if authors are displayed, use one shared canonical rendering path and
  specify its separator/markup.
- Apply the parent-approved feed representation. Do not infer a new feed
  protocol from the current fixture without approval.

## Supporting facts and boundary

The post layout and feed currently read `author` directly. The home page,
`/blog/`, and tag pages all include `_includes/postslist.njk`, which currently
renders only titles. The decisive boundary is a real `npm run build` followed
by assertions against `_site/`, not isolated template rendering with mocked
post data.

## Execution plan

Status: Draft

Change templates to consume only the normalized canonical authors collection.
Keep author rendering shared where the same markup is used by post and archive
pages, and preserve source order. For the feed, emit the approved multi-author
structure for every entry while retaining the existing feed route and all
unrelated elements.

Expand the production-output tests so they invoke the normal build and inspect
the generated home page, blog archive, tag pages, individual posts, feed, and
sitemap. Assert route preservation, expected author names/order/count, absence
of `undefined` or empty author output, and retention of unrelated title/body
content. Include a transition fixture or test setup that demonstrates the
normalizer still protects the build before the strict cutover.

### Implementation decisions and open questions

- Templates must not contain fallback logic for both fields; that belongs at
  the normalization boundary owned by subtask 010.
- Archive routes are in scope even if their current markup does not show
  authors, because their shared production path must be audited for legacy
  reads and their generated output must remain valid.
- Preserve route names and feed URL exactly unless a separately approved
  requirement changes them.

### Documentation

If the approved archive or feed behavior is user-visible, document the
resulting output contract in the maintained README/development documentation
updated by the owning subtask. Do not document target behavior before it is
implemented and verified.

### Task checklist

- [ ] Update the individual post template to use canonical authors.
- [ ] Resolve and implement the archive/listing behavior through the shared
  partial.
- [ ] Update the feed to emit all canonical authors in the approved shape.
- [ ] Replace `tests/author-output.test.js` placeholder coverage.
- [ ] Replace `tests/archive-output.test.js` placeholder coverage.
- [ ] Run the full production build and record route/output evidence.

### Requirement verification

- Individual post pages and feeds: build the site through Eleventy and inspect
  generated files for every migrated author, stable order, and no legacy
  lookup artifacts.
- Archives: inspect `/index.html`, `/blog/index.html`, and each generated tag
  page from the same build, proving the shared listing path remains valid and
  follows the approved author behavior.
- Compatibility: run the production path while a legacy-shaped transition
  input is present in the dedicated fixture/setup, proving the build remains
  safe before cutover; remove that fixture from committed content before the
  strict gate.
- Regression safety: compare the generated route set and non-author output
  fields with the pre-migration baseline.

### Additional implementation verification

- Test one-author and multiple-author posts through the same build path.
- Assert the feed has the expected number of author elements per entry and no
  accidental serialization of objects such as `[object Object]`.
- Check HTML/XML escaping for names containing reserved characters.