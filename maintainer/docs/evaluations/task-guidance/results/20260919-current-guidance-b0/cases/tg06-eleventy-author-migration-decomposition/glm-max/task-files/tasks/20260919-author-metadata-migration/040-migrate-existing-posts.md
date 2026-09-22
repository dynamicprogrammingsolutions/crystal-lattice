# 040 — Migrate existing posts to the structured form

Convert the two existing posts to the canonical `authors` list form and verify
their generated pages are unchanged against the 010 baseline.

Parent Task: tasks/20260919-author-metadata-migration/000-main.md
Depends On:
- tasks/20260919-author-metadata-migration/010-author-model-and-compat.md
- tasks/20260919-author-metadata-migration/020-templates-feed-and-archives.md

## Requirements checklist

- [ ] R7: `content/posts/first.md` and `content/posts/second.md` use the
      structured form; URLs and rendered author output are preserved.
- [ ] R4 (confirmation): archive, tag, home, and sitemap outputs remain
      correct after migration.
- [ ] R6 (confirmation): the site contains no legacy usage after this
      subtask; mixed-form behavior remains covered by the 020 fixture tests.

## Tasks

- [ ] Convert `first.md` and `second.md` to the structured form.
- [ ] Rebuild the real site and compare against the 010 baseline: post page
      URLs, rendered author text, feed author elements, archive/tag/home
      listings, sitemap URLs.
- [ ] Record the content-scan result (zero legacy `author:` usage in
      `content/`) as gate input for 050.

## Verification

- Build-boundary tests over real content pass; generated output matches the
  baseline for all author-bearing and author-independent surfaces.

## Notes

- Content-only change; templates and tooling already support the new form.
- Do not remove the legacy compatibility path here — that happens in 050
  after the gate.