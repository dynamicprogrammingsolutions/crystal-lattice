# Migrate existing post front matter safely

Convert every existing post from the legacy scalar field to the approved
structured multi-author field while preserving titles, body content, dates,
tags, URLs, and other front matter.

Parent Task: tasks/20260919-author-metadata-migration/000-main.md

Depends On: tasks/20260919-author-metadata-migration/010-contract-and-inventory.md

## Requirements checklist

- [ ] Migrate every existing post that currently uses the legacy author field.
- [ ] Preserve each post’s author name, order, front matter, body, and generated
  identity during conversion.
- [ ] Make the migration deterministic and reviewable, with no partial or
  silently lossy conversion.
- [ ] Produce source-content evidence that no supported post still depends on
  the legacy field before final rejection.

## Open requirement questions and material decisions

- The conversion target depends on the approved structured value shape.
- If malformed, duplicate, empty, or unusually quoted legacy values are found,
  decide whether to repair them as part of migration or stop for review; do not
  invent a fallback value.

## Supporting facts

The current content inventory contains `content/posts/first.md` with `Ada
Example` and `content/posts/second.md` with `Grace Example`. Both inherit
layout and tags from `content/posts/posts.json`. No dates or explicit URLs are
currently present in these sample posts, so URL preservation must be checked
from the built output rather than inferred from front matter alone.

## Execution plan

Status: Draft

After the schema is approved, convert the content with a narrowly scoped,
reviewable operation. Compare the before/after front matter and body for every
post, run the production build, and inspect the generated post and collection
outputs. Keep the compatibility reader available until this evidence and the
repository-wide source scan are complete.

### Implementation decisions and open questions

Prefer a deterministic migration operation that fails on unexpected input
instead of guessing. The final choice of script or manual edits is an
implementation detail, but the resulting diff must remain easy to review.

### Documentation

Record the supported front-matter example and any migration caveats in the
developer guidance selected by the parent task. Do not document a temporary
conversion command as a supported authoring interface unless it is retained.

### Task checklist

- [ ] Inventory and classify every post author value.
- [ ] Convert all valid legacy values to the approved structured form.
- [ ] Review front matter/body diffs for preservation.
- [ ] Build all migrated posts and record source-content evidence.

### Requirement verification

- A complete content scan finds no legacy author field in supported post
  front matter after migration.
- A diff review and production build show each migrated post retains its
  content, metadata, URL, and author value(s).
- Structured single- and multi-author content is accepted by the actual
  Eleventy build.

### Additional implementation verification

- Check names containing punctuation, quotes, colons, or non-ASCII characters
  if present in the inventory.
- Verify the migration did not alter unrelated front matter or Markdown body
  bytes.