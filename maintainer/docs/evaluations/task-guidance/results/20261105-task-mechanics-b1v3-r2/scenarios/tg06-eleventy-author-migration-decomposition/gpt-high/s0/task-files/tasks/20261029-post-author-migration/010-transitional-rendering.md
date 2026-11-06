# Add Transitional Author Rendering

Add the production rendering compatibility needed to support structured multi-author metadata without changing output for posts that still use the legacy single-name field.

Parent Task: tasks/20261029-post-author-migration/000-main.md

## Requirements checklist

- [ ] Structured multi-author post metadata can be rendered by the production path.
- [ ] Legacy-only posts retain their existing author presentation during the transition.
- [ ] Post pages, archive paths, and feed output are covered by generated-output regression evidence.

## Supporting details

- Current post pages render `author` in `_includes/layouts/post.njk`.
- The feed reads `post.data.author`; blog and tag archives share `_includes/postslist.njk`.
- Current archive entries show titles and links but no author. Extend their presentation only as required by the approved output decision.
- Existing `tests/author-output.test.js` is a placeholder and must be replaced with real generated-output assertions.

## Execution notes

Depends on agreement for the author schema and required generated representation in `tasks/20261029-post-author-migration/000-main.md`. Keep fallback behavior in the production data/rendering path. Exercise mixed legacy and new content through Eleventy, and inspect generated post pages, blog and tag archives, and the feed.