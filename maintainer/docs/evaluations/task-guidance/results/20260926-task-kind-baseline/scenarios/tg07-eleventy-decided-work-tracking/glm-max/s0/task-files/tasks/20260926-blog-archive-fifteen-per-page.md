# Blog archive: fifteen posts per page

Approved decision (2026-09-26): the blog archive shows fifteen posts per page
instead of one long list of every post. `/blog/` remains the archive entry,
posts stay newest-first, and deeper pagination is deliberately deferred until
the team has seen how the fifteen-post page feels.

Planning is intentionally on hold: the execution plan is to be written after
the scheduled design conversation, so this file records requirements, open
questions, and supporting facts only — no implementation direction.

## Requirements checklist

- [ ] The blog archive shows fifteen posts per page instead of one long list of every post.
- [ ] `/blog/` remains the archive entry point for the new presentation.
- [ ] Posts remain ordered newest-first in the archive.
- [ ] Deeper pagination (archive pages beyond the first, and any navigation between them) is out of scope for this change, deferred by decision.

## Open requirement questions

- Interim handling of older posts: with deeper pagination deferred, what does the archive do about posts beyond the first fifteen — omit them from the listing entirely, or provide minimal access or an indication that older posts exist (for example, through the existing tag pages)? The answer changes the required outcome and is to be resolved in the design conversation.

## Facts and supporting details

- Current archive: `content/blog.njk` (permalink `/blog/`) renders the entire `collections.posts` list through `_includes/postslist.njk`; the partial reverses collection order, which is how newest-first is produced today. The archive has no pagination front matter.
- `_includes/postslist.njk` is shared: `content/index.njk` (three newest posts via the `head` filter) and `content/tag-pages.njk` (per-tag lists) also include it. Tag pages are the only place Eleventy `pagination` is used today (one page per tag, `size: 1`).
- Interpretation of the request: the change applies to the blog archive listing only; the home page, tag pages, and feed are not part of the approved decision.
- Fact: current fixture content is two posts (`content/posts/first.md`, `content/posts/second.md`), so the fifteen-post limit is not exercised by today's content. Observing "how this feels" as intended will require content beyond the current two posts; the design conversation may need to take that into account.