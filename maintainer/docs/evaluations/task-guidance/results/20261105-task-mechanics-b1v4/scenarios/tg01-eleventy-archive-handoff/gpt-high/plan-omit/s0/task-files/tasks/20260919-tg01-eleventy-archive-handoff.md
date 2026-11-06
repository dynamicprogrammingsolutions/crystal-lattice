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
`tests/archive-output.test.js`. The archive currently renders the full post
collection in one page. The exact later-page URL pattern and navigation
presentation remain unresolved public decisions.