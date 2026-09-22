# Migrate templates, archives, and feeds

Move every generated author consumer from the scalar field to the normalized
structured author collection while preserving the site's existing public
surfaces.

Parent Task: tasks/20260919-author-metadata-migration/000-main.md
Depends On: tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md
Depends On: tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md

## Requirements checklist

- [ ] The post layout renders the approved single- and multi-author form.
- [ ] The shared archive/list include and its home, blog, and tag-page
      consumers follow the approved author behavior.
- [ ] The feed renders the approved author representation for each post.
- [ ] No template or feed consumer depends on the scalar legacy field after
      the approved transition point.
- [ ] Existing routes, collection ordering, and non-author output remain
      stable.

## Research and supporting facts

`_includes/layouts/post.njk` directly prints `author`.
`content/feed.xml.njk` directly prints `post.data.author`.
`_includes/postslist.njk` is reused by the home page, blog archive, and tag
pages but currently prints only titles. The output contract from subtask 010
must determine whether it gains author markup or remains deliberately
author-independent.

## Execution plan

Status: Draft

1. Update the post layout to iterate or otherwise consume the normalized
   author collection using the approved escaping and ordering rules.
2. Update the shared archive/list surface if the approved archive contract
   exposes authors; ensure all three archive consumers receive the same
   behavior.
3. Update the feed to emit the approved XML representation for each author.
4. Build the site with migrated single-author content and a multiple-author
   fixture, then inspect generated post, archive, tag, and feed output.
5. Keep the legacy compatibility branch available until subtask 040's final
   source/content/output evidence permits its removal.

### Implementation decisions and open questions

- Rendering shape, separators, and feed structure come from subtask 010.
- A shared normalization boundary is preferred so templates do not each
  implement scalar-to-array compatibility logic; confirm the appropriate
  Eleventy boundary during implementation.
- Archive author display remains conditional on the approved public contract.

### Documentation

Provide verified output examples and any feed compatibility note to subtask
050. Do not document generated output that has not been checked by a build.

### Task checklist

- [ ] Update the post layout.
- [ ] Update the shared archive/list include as required.
- [ ] Update the feed template.
- [ ] Build and inspect all affected generated surfaces.
- [ ] Confirm unrelated routes and collection behavior remain stable.

### Requirement verification

Use production-build tests and generated-output assertions for a post page,
home page, blog archive, tag page, and feed. Assertions must cover both
single- and multiple-author cases and the approved public representation.

### Additional implementation verification

Validate HTML/XML escaping, author order, empty/invalid metadata behavior
only where the approved contract specifies it, and unchanged sitemap URLs.