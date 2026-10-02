# Migrate post content and the new-post authoring helper

Move maintained post front matter and the post creation helper to the
approved structured author form while preserving existing post identity and
content. This subtask owns source data and authoring behavior; it depends on
the schema/compatibility contract and does not own generated template
consumers.

## Requirements checklist

- [ ] Update `scripts/new-post.js` so newly generated front matter uses the
      approved structured author form and supports the approved author count.
- [ ] Migrate every existing post in `content/posts/` from the scalar field to
      the structured form, preserving title, body, tags, layout, ordering
      inputs, and generated-page identity.
- [ ] Preserve author names exactly unless the approved schema explicitly
      requires a documented normalization.
- [ ] Add executable evidence for helper output and a source inventory that
      detects unmigrated maintained posts.
- [ ] Align the maintained developer documentation with the new authoring
      workflow.

Parent Task: tasks/20260925-author-metadata-migration/000-main.md

Depends On: tasks/20260925-author-metadata-migration/010-author-schema-transition.md

## Unresolved requirement questions

- The helper's parameter shape and generated front-matter syntax depend on the
  schema approved by
  `tasks/20260925-author-metadata-migration/010-author-schema-transition.md`.
- If the public contract requires author IDs, slugs, or links, confirm whether
  the helper accepts those values now or only names.

## Supporting facts and research

- `scripts/new-post.js` currently exports `frontMatter(title, author)` and
  emits `author: "<value>"`.
- The repository currently contains two maintained posts:
  `content/posts/first.md` and `content/posts/second.md`.
- Neither current post has multiple authors, so the migration must add
  explicit multi-author fixture coverage without rewriting the existing prose.
- The current test file for author output is a comment-only placeholder, so
  helper/source evidence must be added as executable coverage during
  execution.

## Execution plan

Status: Draft

After the parent approves the contract, make the authoring helper the source
of the new format and migrate the existing files mechanically only where the
author field changes. Preserve all unrelated front matter and body text.
Add a representative multi-author fixture or test input so the helper's
multi-author behavior is exercised even though the current production posts
are single-author.

1. Define the helper's input shape and output serialization from the approved
   schema.
2. Update the helper and add a focused test that checks one-author and
   multi-author output, including front-matter quoting/escaping required by
   the approved syntax.
3. Migrate every existing post and review the diff for title, body, tags,
   layout, and route-affecting changes.
4. Add a source inventory/regression check that fails when a maintained post
   still declares the legacy scalar field or lacks the required structured
   field.
5. Update the README's authoring guidance with a current example and the
   transition/retirement status once that status is approved.
6. Hand the migrated source and helper contract to the generated-output
   subtask for production-build verification.

### Implementation decisions and open questions

- Do not choose a front-matter shape or helper API until the parent resolves
  the schema question.
- The source inventory may allow an explicitly documented transition fixture
  only if the parent approves that fixture; maintained production posts must
  not remain scalar.

### Documentation

- Update the developer-facing authoring section in `README.md` with the
  supported front matter and helper usage. Keep any temporary compatibility
  example visibly transitional and remove it when the legacy form is retired.

### Task checklist

- [ ] Receive the approved schema from
      [010-author-schema-transition.md](010-author-schema-transition.md).
- [ ] Update and test `scripts/new-post.js`.
- [ ] Migrate all maintained post files and review preservation of unrelated
      metadata/content.
- [ ] Add the source inventory/regression check.
- [ ] Update the maintained authoring documentation.

### Requirement verification

- The helper test is the decisive authoring-boundary check: it must inspect
  the actual exported helper output for one and multiple authors.
- The source inventory is the decisive content check: it must enumerate all
  maintained posts and prove that no production post still depends on the
  scalar field.
- The parent production build remains necessary to prove that the migrated
  source is consumable by Eleventy and reaches generated pages.

### Additional implementation verification

- Compare migrated post bodies and unrelated front matter against the
  pre-migration content.
- Search scripts, content, and tests for stale scalar author writes or reads,
  retaining only explicitly approved transition evidence.