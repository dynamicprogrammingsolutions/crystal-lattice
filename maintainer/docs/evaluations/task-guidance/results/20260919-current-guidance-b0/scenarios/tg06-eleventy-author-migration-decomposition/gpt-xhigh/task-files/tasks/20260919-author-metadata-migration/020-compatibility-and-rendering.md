# Move templates and generated surfaces to structured authors

Update the Eleventy data path and all relevant rendering surfaces so structured
authors are the primary model while legacy posts remain renderable during the
approved transition.

Parent Task: tasks/20260919-author-metadata-migration/000-main.md

Depends On: tasks/20260919-author-metadata-migration/010-contract-and-inventory.md

## Requirements checklist

- [ ] Make the post layout consume the structured author representation.
- [ ] Make home, blog archive, and tag-listing paths use the structured model
  wherever author data is displayed or passed through.
- [ ] Make feed generation serialize all authors according to the approved feed
  contract.
- [ ] Preserve existing post URLs, archive/tag URLs, listing order, and
  sitemap URLs unless an explicitly approved author-output change requires
  otherwise.
- [ ] Keep legacy content working through the compatibility period without
  duplicating fallback logic across templates.

## Open requirement questions and material decisions

- The exact author presentation and feed serialization depend on the contract
  approved in subtask 010.
- Confirm whether archive listings should visibly display authors or only stop
  depending on a legacy post-data shape; the current shared listing emits title
  and link only.

## Supporting facts

The post layout and feed are direct legacy consumers. The shared
`_includes/postslist.njk` is used by the home page, `/blog/`, and tag pages,
which makes it the relevant archive boundary even though it currently renders
no author. `content/sitemap.xml.njk` does not read author data but should be
covered by URL-preservation checks because it is part of generated output.

## Execution plan

Status: Draft

Introduce or use the approved normalization boundary, then update the post
layout, shared listing include, feed, and any collection-facing code to consume
the structured value. Keep the compatibility read at that boundary for the
transition. Add executable build-level assertions for legacy and structured
fixtures, including one post with multiple authors, and compare URL/order
output across home, archive, tags, feed, and sitemap.

### Implementation decisions and open questions

Do not scatter `author`/`authors` conditionals through Nunjucks templates.
Choose the narrowest shared data boundary supported by Eleventy after the
contract is approved. Any visible archive rendering change must be recorded as
an approved output decision.

### Documentation

Document the public generated-output behavior only after build assertions
verify it. The authoring and data-contract documentation belongs in subtask
040; this subtask supplies its rendering facts.

### Task checklist

- [ ] Add the compatibility normalization at the approved boundary.
- [ ] Update post, listing/archive, and feed consumers.
- [ ] Add or update build assertions for single, multiple, and legacy authors.
- [ ] Verify URL, ordering, and sitemap preservation.

### Requirement verification

- A real Eleventy production build renders a legacy fixture and structured
  single-/multi-author fixtures successfully.
- Generated post, home, `/blog/`, tag, feed, and sitemap outputs meet the
  approved author and URL contracts.
- Assertions prove no duplicate or missing author output for multi-author
  posts.

### Additional implementation verification

- Inspect generated HTML/XML for escaping and malformed markup.
- Confirm the compatibility behavior is localized and removable at cutover.