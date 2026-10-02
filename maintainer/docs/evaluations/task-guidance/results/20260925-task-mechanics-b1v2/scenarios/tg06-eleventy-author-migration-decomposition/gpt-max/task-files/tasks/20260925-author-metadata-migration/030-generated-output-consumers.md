# Move generated pages, archives, and feeds to structured authors

Update every public generated-output consumer to use the normalized
multi-author collection and prove the migration through the real Eleventy
build. This subtask owns post bylines, shared archive listings, feed output,
and route-preservation coverage.

## Requirements checklist

- [ ] Update the individual post layout to render the approved structured
      author collection for one and multiple authors.
- [ ] Update the shared post-list/archive surface used by the home page,
      `/blog/`, and tag pages according to the approved archive rendering
      contract.
- [ ] Update the feed to emit the approved representation for one and
      multiple authors, with valid escaped XML.
- [ ] Remove direct production reads of the legacy scalar field from
      templates and feed code.
- [ ] Preserve existing generated routes and page generation for individual
      posts, home, blog archive, tag pages, feed, and sitemap.
- [ ] Add executable production-build assertions that prove author output
      through the real Eleventy path.

Parent Task: tasks/20260925-author-metadata-migration/000-main.md

Depends On:
tasks/20260925-author-metadata-migration/010-author-schema-transition.md
tasks/20260925-author-metadata-migration/020-content-and-authoring-migration.md

## Unresolved requirement questions

- Confirm the visual/archive format and feed element structure for multiple
  authors before locking output assertions.
- Confirm whether author values in archive listings or feeds need stable links
  or identifiers beyond display names.

## Supporting facts and research

- `_includes/layouts/post.njk` currently renders `<p class="author">{{ author
  }}</p>`.
- `_includes/postslist.njk` is shared by `content/index.njk`,
  `content/blog.njk`, and `content/tag-pages.njk`; it currently emits only
  post titles.
- `content/feed.xml.njk` directly emits one `<author>` value from
  `post.data.author`.
- `content/sitemap.xml.njk` does not consume author metadata but must remain
  generated because the migration must not break the complete output set.
- Existing output tests contain no assertions, so the new coverage must build
  the site rather than mock page data.

## Execution plan

Status: Draft

Make the public consumers depend only on the normalized author collection
provided by the transition boundary. Keep presentation rules in the relevant
template/feed surface, but do not duplicate legacy-field detection there.
The production test should build the site using the repository's actual
Eleventy configuration and inspect generated files under `_site`.

1. Resolve the archive and feed output contract with the parent.
2. Update the post layout and shared post-list include, then verify that all
   three archive entry points receive the same author model.
3. Update the feed serialization for one and multiple authors, including
   XML escaping and the approved element/attribute structure.
4. Expand `tests/author-output.test.js` and
   `tests/archive-output.test.js` so they invoke the production build or a
   shared real-build harness and assert:
   individual post bylines, home/blog/tag archive output, feed author data,
   and preserved output routes.
5. Run the build with the transition compatibility path before legacy
   retirement, then run it again after the parent evidence gate has retired
   or rejected the scalar form.
6. Report any output contract or route change to the parent before changing
   scope.

### Implementation decisions and open questions

- Do not infer separators, links, or feed serialization from the current
  single-author output; those are public-contract questions.
- The decisive test must cross the Eleventy build boundary and inspect files
  in `_site`; a test that passes author objects directly to Nunjucks is not
  sufficient.

### Documentation

- Provide the parent with the final public rendering examples if they need to
  be reflected in `README.md`. Do not create output documentation that
  describes a draft contract.

### Task checklist

- [ ] Receive the approved archive/feed rendering contract.
- [ ] Update the post layout and shared archive list.
- [ ] Update feed serialization and remove production scalar reads.
- [ ] Add/expand real production-build output assertions.
- [ ] Verify routes and author output before and after the retirement gate.

### Requirement verification

- The decisive check is a real `npm run build` exercised by executable tests
  that inspect the generated individual post, home page, `/blog/`, tag page,
  feed, and sitemap. It must prove both single-author and multi-author output
  where the approved fixtures provide them.
- The same generated-output evidence is one half of the parent legacy
  retirement gate; the source-content inventory from
  `tasks/20260925-author-metadata-migration/020-content-and-authoring-migration.md`
  is the other half.

### Additional implementation verification

- Validate that the feed remains well-formed XML and that author names are
  escaped according to the approved serialization.
- Search all production templates and feed sources for direct scalar reads
  after the consumer migration.