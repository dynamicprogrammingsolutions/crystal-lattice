# 030 — Authoring tool emits the structured form

Move `scripts/new-post.js` to the canonical structured multi-author model so
new posts are authored in the supported form.

Parent Task: tasks/20260919-author-metadata-migration/000-main.md
Depends On: tasks/20260919-author-metadata-migration/010-author-model-and-compat.md

## Requirements checklist

- [ ] R5: `frontMatter(title, authors)` emits the canonical `authors` list
      form (shape per approved D1; always a list, per D5).
- [ ] R8 (slice): unit test pins the exact emitted front matter.

## Tasks

- [ ] Update `scripts/new-post.js` to accept the authors list and emit the
      structured front matter.
- [ ] Add/update the unit test pinning the emitted output.

## Verification

- Unit test runs cleanly under `node --test tests/*.test.js`; emitted front
  matter builds through the normalization path (covered by 010 unit tests).

## Notes

- API change is internal to the authoring tool; no template or content change.
- README authoring-tool claim (if added in 020) is updated here in the same
  change if the emitted form is documented.