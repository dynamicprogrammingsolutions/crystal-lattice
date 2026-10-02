# Blog archive: fifteen posts per page

The blog archive at `/blog/` will show fifteen posts per page instead of
rendering the whole collection as one long list. `/blog/` stays the archive
entry point, newest-first order stays, and deeper pagination is deliberately
deferred until the team has seen how the fifteen-per-page archive feels.
Implementation planning happens after the scheduled design conversation; this
file records the decided requirements and the question that conversation must
settle.

## Requirements checklist

- [ ] The blog archive shows fifteen posts per page instead of one long list.
- [ ] `/blog/` remains the archive entry point.
- [ ] Archive post order stays newest-first.
- [ ] Constraint: deeper pagination is deliberately deferred. This change
      must not add deeper pagination beyond what the requirements above
      state; revisit the deferral once the fifteen-per-page archive has been
      in use.

## Requirement questions

Unresolved — to be settled in the scheduled design conversation, before the
execution plan is written:

1. **Posts beyond the first fifteen.** In this iteration, are older posts
   reachable at all (for example, additional generated archive pages), or is
   capping the archive list at fifteen the entire change, leaving older posts
   unlisted until deeper pagination lands? Any visible signal about older
   posts (a count, an "older posts" hint) belongs to this same open question.

## Supporting facts

- The archive is `content/blog.njk` (`permalink: /blog/`). It renders the
  full `collections.posts` through `_includes/postslist.njk`, which reverses
  the collection so the list displays newest-first. No pagination front
  matter or pagination configuration exists anywhere in the project today.
- The home page is a separate surface: `content/index.njk` shows the latest
  three posts via the `head` filter (`eleventy.config.js`). This decision
  concerns only the archive; the home page list is not part of it.
- Posts come from `content/posts/` (`posts.json` assigns `tags: ["posts"]`).
  The fixture currently holds two posts, so a fifteen-post cap changes
  nothing visible with current content — the requirement is about archive
  behavior, not fixture content.
- Existing coverage is minimal: `tests/archive-output.test.js` only checks
  that `/blog/index.html` exists.

## Planning status

No execution plan exists yet, intentionally. The design conversation is
scheduled first; whoever picks this up writes the plan there and presents it
for approval before touching code. This file was created only to record the
decision and hand it off.