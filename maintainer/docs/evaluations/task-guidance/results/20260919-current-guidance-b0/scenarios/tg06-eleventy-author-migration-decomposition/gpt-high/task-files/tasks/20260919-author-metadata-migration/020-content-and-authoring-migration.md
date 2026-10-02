# Migrate post content and authoring tools

Convert existing post metadata and the new-post generator to the approved
structured author model while preserving a bounded transitional read path.

Parent Task: tasks/20260919-author-metadata-migration/000-main.md
Depends On: tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md

## Requirements checklist

- [ ] Existing posts are converted to the approved structured field without
      changing their author identity or unrelated front matter/body content.
- [ ] Shared post defaults and any metadata normalization support the approved
      model.
- [ ] `scripts/new-post.js` emits the approved structured form and follows the
      approved compatibility API.
- [ ] Transitional legacy handling is limited to the approved window and does
      not hide malformed new metadata.

## Research and supporting facts

`content/posts/first.md` and `content/posts/second.md` are the only current
post files and each has one scalar author. `content/posts/posts.json` owns
shared post layout/tag metadata. `scripts/new-post.js` currently accepts
`(title, author)` and writes a scalar field.

## Execution plan

Status: Draft

1. Add or update focused tests for tool serialization and metadata
   normalization according to the contract from subtask 010.
2. Migrate the existing post front matter mechanically and inspect the diff
   for preservation of titles, body text, tags, and author identity.
3. Update shared defaults or configuration needed for the structured field.
4. Update the new-post tool to emit the new model and implement only the
   approved transition behavior.
5. Leave final legacy rejection to subtask 040 after all consumers and
   evidence are ready.

### Implementation decisions and open questions

- Do not decide a new tool signature here; use the contract approved by
  subtask 010.
- Do not delete legacy handling before the production-output evidence gate.
- Do not rewrite generated `_site` files or alter post routes as part of the
  metadata conversion.

### Documentation

Provide the final tool invocation/examples and migration note to subtask 050;
do not publish guidance until the implementation is verified.

### Task checklist

- [ ] Add focused tool/metadata tests.
- [ ] Migrate all existing post metadata.
- [ ] Update shared post metadata configuration if required.
- [ ] Update the authoring tool.
- [ ] Record source-preservation evidence for the migrated posts.

### Requirement verification

Use tool-level tests for exact serialization and a production build with the
migrated repository posts to verify that front matter remains consumable.
Inspect the source diff for preservation of non-author fields and body text.

### Additional implementation verification

Exercise one single-author and one multiple-author tool input, including
escaping-sensitive names, under the approved API.