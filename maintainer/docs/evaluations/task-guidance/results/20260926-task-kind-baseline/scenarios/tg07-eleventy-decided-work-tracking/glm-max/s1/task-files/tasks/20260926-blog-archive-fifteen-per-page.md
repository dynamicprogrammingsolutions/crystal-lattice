# Blog archive: fifteen posts per page

Switch the blog archive from one long list to fifteen posts per page.
`/blog/` remains the archive entry point and posts stay newest-first.
Deeper pagination is deliberately deferred.

Status: decision recorded 2026-09-26. Planning is intentionally deferred to a
scheduled design conversation — do not plan or execute from this file until
that conversation has happened and a plan is approved.

## Requirements checklist

- [ ] `/blog/` remains the archive entry point at the same URL.
- [ ] The archive shows fifteen posts per page instead of one long list.
- [ ] Post order in the archive stays newest-first.
- [ ] Other consumers of the shared post-list partial (`content/index.njk`
      homepage, `content/tag-pages.njk` tag pages) keep their current behavior.

## Approved scope decision

- Deeper pagination is deliberately deferred until we see how fifteen-per-page
  feels. Do not extend this task with richer pagination behavior on your own;
  if implementation seems to force a call on that boundary, take it back to the
  design conversation.

## Open questions (resolve in the scheduled design conversation)

- Requirement question: does the first cut leave older posts reachable at all
  (a second page and beyond exist), or does `/blog/` simply show the fifteen
  newest posts with older posts not yet reachable? "Fifteen per page" implies
  further pages, while deferring "deeper pagination" could mean only the first
  page exists for now. The answer changes the required outcome, so it stays
  open until the design conversation resolves it.
- If older posts stay reachable: how readers navigate to them (URLs, links) is
  part of that same conversation.

## Supporting details

- `content/blog.njk` is the archive: permalink `/blog/`, an "Archive" heading,
  and an include of the shared partial `_includes/postslist.njk` fed with
  `collections.posts`.
- `_includes/postslist.njk` iterates `postslist | reverse`; Eleventy
  collections sort date-ascending, so the reverse is what produces
  newest-first. Ordering lives in the shared partial, not in
  `content/blog.njk`.
- The shared partial is also included by `content/index.njk` (latest three
  posts via `| head(-3)`) and `content/tag-pages.njk` (full list per tag), so
  the archive change must not leak into those views.
- `content/blog.njk` has no `pagination` front matter; the current long list
  is simply the absence of pagination configuration.