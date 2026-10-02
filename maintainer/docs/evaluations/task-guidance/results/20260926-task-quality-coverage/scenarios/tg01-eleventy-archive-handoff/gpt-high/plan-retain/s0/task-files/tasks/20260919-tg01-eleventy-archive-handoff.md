# Add Accessible Archive Pagination

Create bounded static archive pages while preserving existing generated
surfaces and zero-JavaScript output.

## Requirements checklist

- [ ] `ARCHIVE-1`: `/blog/` remains the first page and later pages use an
  approved stable URL pattern.
- [ ] `ARCHIVE-2`: Every archive page contains no more than twenty posts.
- [ ] `ARCHIVE-3`: Posts remain newest-first and appear exactly once across
  archive pages.
- [ ] `ARCHIVE-4`: Accessible previous and next navigation appears only when
  the corresponding destination exists.
- [ ] `ARCHIVE-5`: Home, tags, feed, sitemap, and individual-post navigation
  retain current behavior.
- [ ] `ARCHIVE-6`: Archive output remains static and uses no client-side
  JavaScript.

## Supporting details

Relevant entry points include `content/blog.njk`,
`_includes/postslist.njk`, the home/tag/feed/sitemap templates, and
`tests/archive-output.test.js`. The exact later-page URL pattern and navigation
presentation remain approval questions.

## Execution plan

Status: Draft

Inspect archive collection and template behavior, obtain approval for the
public URL/navigation decisions, implement pagination and boundary-aware
navigation, then verify first/middle/last generated archive pages and all
protected surfaces through the production Eleventy build.

### Implementation decisions and open questions

- Requirement question: approve the stable URL pattern for pages after
  `/blog/`.
- Design decision: choose navigation markup after the accessibility behavior is
  approved.

### Documentation

Update current archive documentation only when an existing claim or public URL
description changes.

### Task checklist

- [ ] Inspect archive and protected generated-surface entry points.
- [ ] Resolve the public URL and navigation questions.
- [ ] Implement bounded archive generation and adjacent-page navigation.
- [ ] Add focused production-build acceptance and regression evidence.
- [ ] Update affected current documentation.

### Requirement verification

- `ARCHIVE-1`–`ARCHIVE-4`: production build with first, middle, and last
  archive pages.
- `ARCHIVE-3`: generated membership/order check proves every post appears once.
- `ARCHIVE-5`: focused generated-output regressions for protected surfaces.
- `ARCHIVE-6`: generated output contains no client-side pagination behavior.