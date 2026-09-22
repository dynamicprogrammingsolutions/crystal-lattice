# Migrate templates, archives, and feeds to the author collection

Update every rendering surface that can expose post metadata to consume the
normalized multi-author value while preserving existing routes and unrelated
generated output.

Parent Task: tasks/20260919-author-metadata-migration/000-main.md
Depends On: tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md

## Requirements checklist

- [ ] Update the post layout to render the approved author collection,
      including the chosen one- and multi-author display contract.
- [ ] Audit the shared post list used by the home page, archive, and tag
      pages; if it renders author data under the approved contract, use the
      normalized collection rather than the legacy field.
- [ ] Update feed generation for all authors, preserving order and valid
      escaped output under the approved feed representation.
- [ ] Keep sitemap generation, page URLs, archive routes, and unrelated
      output working.
- [ ] Leave no direct legacy-field reads in production templates outside the
      deliberate compatibility boundary.

## Supporting facts

- `_includes/layouts/post.njk` directly renders `author`.
- `content/feed.xml.njk` directly reads `post.data.author`.
- `_includes/postslist.njk` is shared by `content/index.njk`,
  `content/blog.njk`, and `content/tag-pages.njk`, but currently renders only
  titles and links.
- `content/sitemap.xml.njk` has no author dependency and should be covered as
  a generated-page regression surface rather than changed unnecessarily.

## Execution plan

Status: Draft

Use the normalization boundary from subtask 010 in the post layout and feed.
Render every approved author according to the chosen order/separator or feed
entry contract, with proper escaping. Audit the shared list template and its
three callers; preserve the current title-only archive presentation unless
the open archive question is explicitly answered in favor of visible
bylines, but ensure no author consumer is left on the scalar field.

Build the complete site with migrated content and inspect the post, home,
archive, tag, feed, and sitemap outputs. Add assertions at the generated
output boundary rather than relying only on template text inspection.

### Implementation decisions and open questions

- Archive byline visibility and feed multiple-author representation remain
  open until the parent contract is approved.
- The feed must not collapse multiple authors into an ambiguous string unless
  that is the explicitly approved contract.
- No sitemap author data should be added solely to make the migration appear
  complete; it has no current author consumer.

### Documentation

Document the resulting rendered byline/feed behavior in the maintained
developer guidance only after it is verified. This subtask does not change
current documentation while the plan is Draft.

### Task checklist

- [ ] Confirm the post, archive/list, and feed rendering contract.
- [ ] Update the post layout and feed to consume normalized authors.
- [ ] Audit/update the shared list and all home/archive/tag callers as
      required by the approved display contract.
- [ ] Add generated-output assertions for one and multiple authors and for
      escaped names.
- [ ] Run a full build and pass route/output observations to subtask 040.

### Requirement verification

- Generated individual post pages show the approved author output for
  single- and multi-author content without `undefined`, scalar-object
  artifacts, or missing names.
- Generated home, archive, and tag pages build at their existing URLs and
  satisfy the approved archive byline contract.
- The feed contains all authors in the approved order/structure and remains
  valid escaped output.
- The sitemap and unrelated page URLs remain generated, and a source scan
  finds no direct legacy reads outside the compatibility owner.