# 010 — Multi-author model with legacy-compatible rendering

Add the canonical structured `authors` model and its normalizer, move the
post-layout byline and feed entries onto it, and keep the legacy `author`
string accepted and byte-identically rendered during the transition. Establishes
the integration tests for author output and archive continuity.

Parent Task: tasks/20260925-author-metadata-migration/000-main.md

Depends On: (none — first subtask)

## Requirements checklist

- [ ] R1 — Canonical structured multi-author metadata is supported (item shape
  per approved Q1).
- [ ] R2 — Legacy `author` stays accepted; a legacy-form post renders
  byte-identically to today.
- [ ] R3 — Byline and feed render all authors in declared order through the
  canonical path; single-author output unchanged.
- [ ] R4 — Home, blog archive, tag pages, and sitemap output unchanged
  (continuity assertions).
- [ ] R8 (part) — README authoring note documents the new model with a visible
  transitional note about the legacy field.

## Task checklist

- [ ] Implement the normalizer as the single canonical read path; only code
  that reads raw `author`/`authors` raw keys
- [ ] Update `_includes/layouts/post.njk` byline to render canonical `authors`
- [ ] Update `content/feed.xml.njk` to emit one `<author>` per author
- [ ] Rewrite `tests/author-output.test.js` as a production-build integration
  test: real build of public content (legacy era) plus a temporary content
  fixture reusing the production config/templates for the multi-author case
- [ ] Strengthen `tests/archive-output.test.js` with continuity assertions
  (home, archive, tag pages, sitemap)
- [ ] README authoring note (new model + transitional note)
- [ ] `npm install` if needed; `npm test` and `npm run build` green; record
  results

## Verification

Decisive: production-build integration test asserting the generated post-page
byline and feed author entries for multi-author and legacy-form posts, plus
archive continuity assertions on the real build. Supporting: full test run and
full build exit cleanly.

Note: a permanent multi-author post must not be added to `content/` — that
would change public output. Multi-author evidence comes from the temporary
fixture built through the same real pipeline.