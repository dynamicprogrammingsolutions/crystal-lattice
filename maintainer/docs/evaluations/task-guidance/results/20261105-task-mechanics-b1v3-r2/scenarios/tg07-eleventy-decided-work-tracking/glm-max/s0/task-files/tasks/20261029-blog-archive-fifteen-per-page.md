# Blog archive: fifteen posts per page (deeper pagination deferred)

The blog archive moves from one long list to a fifteen-post page size. `/blog/`
stays the archive entry and newest-first order stays. Deeper pagination is
deliberately deferred until the team sees how fifteen-per-page feels.

**Planning is intentionally not started.** The execution plan is to be written
after the scheduled design conversation; until then this file records approved
decisions and the current state only. Creating this task file does not
authorize implementation.

## Requirements checklist

- [ ] Blog archive page size is fifteen: `/blog/` lists at most the fifteen
      newest posts instead of the full post list.
- [ ] `/blog/` remains the archive entry: the first archive page is served at
      the existing URL, with no redirect or rename.
- [ ] Archive ordering remains newest-first.
- [ ] Constraint: this change does not introduce deeper archive pagination —
      no additional archive pages and no pagination navigation. The deferral
      is approved scope, not an omission to fix.

## Open requirement questions

- Once the blog holds more than fifteen posts, posts beyond the first fifteen
  will not appear in the archive until deeper pagination exists. With the
  current two posts this is latent, not immediate. Confirm in the design
  conversation whether that interim state is acceptable or whether this change
  needs an interim affordance for older posts.

## Supporting facts

- Current archive: `content/blog.njk` (permalink `/blog/`) renders
  `_includes/postslist.njk` with `collections.posts` and has no pagination
  front matter — it is one long list today.
- `_includes/postslist.njk` produces newest-first order via `| reverse`
  (Eleventy collections default oldest-first) and is shared with
  `content/tag-pages.njk`; the include is not archive-only.
- The project already uses Eleventy pagination elsewhere:
  `content/tag-pages.njk` paginates `collections` with `size: 1` per tag.
  Recorded as an existing pattern only; the approach for the archive is a
  design-conversation topic.
- Content volume: two posts (`content/posts/first.md`,
  `content/posts/second.md`), well under the approved page size.
- `tests/archive-output.test.js` currently asserts only that
  `/blog/index.html` exists; nothing covers list length or ordering.
- Recorded decision: revisit deeper pagination after evaluating the
  fifteen-per-page experience in practice.
