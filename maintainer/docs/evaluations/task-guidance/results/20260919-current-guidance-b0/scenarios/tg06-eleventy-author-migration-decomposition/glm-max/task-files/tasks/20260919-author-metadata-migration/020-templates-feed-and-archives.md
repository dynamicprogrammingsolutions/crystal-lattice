# 020 — Templates, feed, and archives on the normalized authors view

Move the post page layout and the feed to render all authors through the
normalized view from 010, keep archive/tag/home/sitemap surfaces
author-independent, and add the generated-output test boundary (fixture site
plus real-content builds).

Parent Task: tasks/20260919-author-metadata-migration/000-main.md
Depends On: tasks/20260919-author-metadata-migration/010-author-model-and-compat.md

## Requirements checklist

- [ ] R2 (slice): `_includes/layouts/post.njk` renders every author (joined
      display per D4; existing `p.author` element/class retained).
- [ ] R3 (slice): `content/feed.xml.njk` emits one `<author>` element per
      author per post, preserving current text semantics (D3).
- [ ] R4 (slice): archive/tag/home listing tests assert full post lists
      (title + link), replacing the existence-only placeholder; sitemap URLs
      unchanged.
- [ ] R6 (slice): fixture-site build test exercises a multi-author post, a
      new-form single-author post, and a legacy post building side by side.
- [ ] R8 (slice): generated-output tests cross the real build boundary
      (fixture content + real templates/config) without adding test-only
      posts to production `content/` (D6).

## Tasks

- [ ] Update `_includes/layouts/post.njk` to render the normalized authors.
- [ ] Update `content/feed.xml.njk` to emit one author element per author.
- [ ] Replace `tests/author-output.test.js` placeholder with fixture-site
      build tests (post pages + feed) covering multi-author, new-form, and
      legacy posts.
- [ ] Replace `tests/archive-output.test.js` placeholder with full listing
      assertions for archive/tag/home (and sitemap URL stability).
- [ ] Add real-content build checks for `first.md`/`second.md` (author text
      unchanged on pages and feed).
- [ ] Update `README.md` author-metadata section (structured model + example +
      transitional legacy note) in the same change (R10 slice).

## Verification

- Full `node --test tests/*.test.js` run collects unit tests from 010 and the
  new build-boundary tests cleanly.
- Single-author generated output remains text-equivalent to the 010 baseline
  (pages and feed); multi-author fixture output shows every author.

## Notes

- Test builds write to a gitignored/temporary output directory (D7).
- The fixture site lives under `tests/` with its own content and the real
  config/templates (D6); treat it as maintained test infrastructure.