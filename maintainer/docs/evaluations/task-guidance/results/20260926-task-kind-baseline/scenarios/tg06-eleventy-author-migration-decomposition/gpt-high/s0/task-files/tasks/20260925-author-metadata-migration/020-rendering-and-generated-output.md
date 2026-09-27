# Migrate rendering and generated output

Move post templates and feed generation to the structured author model, audit
archives and related listing paths for legacy reads, and prove the production
build remains complete and compatible during the transition.

Parent Task: tasks/20260925-author-metadata-migration/000-main.md

Depends On: tasks/20260925-author-metadata-migration/010-author-contract-and-content.md

## Requirements checklist

- [ ] Individual post rendering consumes the structured author model.
- [ ] The feed represents one or more authors deterministically using the approved output form.
- [ ] Archive, home, tag, sitemap, and other generated paths are audited for legacy author dependencies and continue to build.
- [ ] Existing URLs and non-author page content remain intact unless a separately approved archive-byline change is made.
- [ ] Generated-output tests exercise the real Eleventy build and cover both compatibility and multi-author cases.

## Unresolved requirement questions

- [ ] Confirm whether archive/list pages should gain visible author output or
  only stop depending on the legacy field.
- [ ] Confirm the exact feed XML shape for multiple structured authors.

## Research and supporting facts

- `_includes/layouts/post.njk` directly renders the legacy `author` value.
- `content/feed.xml.njk` directly reads `post.data.author`.
- `_includes/postslist.njk` is shared by the home page, blog archive, and tag
  pages and currently renders only title/link data.
- `content/sitemap.xml.njk` traverses all pages but does not read author data.
- Existing generated-output test files do not yet execute or assert the
  production build.

## Execution plan

Status: Draft

Update the post layout and feed to consume the normalized structured data,
preserving visible single-author output and defining deterministic
multi-author output. Audit every consumer reachable from home, blog, tag,
sitemap, post, and feed templates. Keep archive markup unchanged if the
approved requirement is dependency removal only; add bylines only if that
open question is approved. Replace placeholder tests with a real build-backed
test that inspects generated files rather than injecting mocked post objects.

### Implementation decisions and open questions

- Use one shared normalized representation for template consumers so the
  layout and feed cannot drift in how they interpret legacy content.
- Preserve the feed path and entry count. The exact author element strategy
  remains pending the approved schema and feed decision.
- Include at least one multi-author fixture in test input or a temporary
  test-owned content fixture that crosses the production build boundary,
  without bypassing Eleventy data loading.

### Documentation

- Document any visible feed or archive rendering change alongside the
  approved author contract.
- Keep README/site-surface claims accurate after generated-output behavior is
  verified.

### Task checklist

- [ ] Resolve archive and feed output decisions.
- [ ] Update post and feed consumers.
- [ ] Audit shared archive/listing and metadata templates.
- [ ] Replace placeholder generated-output coverage with real build-backed
  assertions.
- [ ] Verify representative post, home/archive, tag, sitemap, and feed output.
- [ ] Update the parent task checklist and evidence after verification.

### Requirement verification

- Run `npm run build` and inspect generated post HTML for preserved author
  output and correct multi-author output.
- Inspect `_site/blog/index.html`, the home page, generated tag pages, and
  `_site/sitemap.xml` to confirm the full page set builds and contains no
  unexpected legacy dependency.
- Inspect `_site/feed/feed.xml` for stable entry coverage and the approved
  deterministic author representation.
- Use the real production build in the automated test; a test that supplies
  pre-normalized mock data is not decisive evidence for this subtask.