# Blog archive: fifteen posts per page

Track the approved decision for the blog archive pagination. Implementation
planning has not happened yet; it follows the scheduled design conversation.
This file records the decision so the implementer does not re-litigate it.

## Requirements checklist

- [ ] The blog archive shows posts fifteen per page instead of the current
      single long list.
- [ ] `/blog/` remains the archive entry — the URL and its role as the
      starting point of the archive do not change.
- [ ] Posts remain in newest-first order on every archive page.
- [ ] Deeper pagination design (page-size changes, additional navigation, or
      related UX) is deliberately deferred and is out of scope until the team
      sees how fifteen-per-page feels in practice.

## Questions and decisions

None open. All four items above are approved decisions. Revisit pagination
design only after the deferred review.

## Supporting details

- Decision (approved 2026-11-02): fifteen posts per page; entry URL, ordering,
  and deferral of deeper pagination as listed in the requirements.
- Fact: the archive is currently rendered by `content/blog.njk`
  (permalink `/blog/`), which includes `_includes/postslist.njk` over the full
  `collections.posts` reversed, newest-first, with no pagination.
- Fact: `_includes/postslist.njk` is shared. `content/index.njk` also includes
  it, capped at the 3 newest posts as a teaser. The approved decision concerns
  the archive at `/blog/` only; the homepage teaser keeps its current behavior
  unless a future decision says otherwise.
- Fact: the content set currently contains two posts
  (`content/posts/first.md`, `content/posts/second.md`), so with this content
  the archive produces a single page. Verifying the fifteen-per-page behavior
  will need more posts or attention to the page-size logic rather than relying
  on visible page splits alone.
- Dependency: implementation planning is deferred to the scheduled design
  conversation. Whoever picks this up should plan first, not implement
  directly from this file.
