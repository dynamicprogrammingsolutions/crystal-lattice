# Archive pagination generation

Define the Eleventy pagination boundary that produces the first and later
blog archive pages without changing the existing collection order.

Parent Task: tasks/20260919-blog-archive-pagination/000-main.md

## Requirements checklist

- [ ] Keep the first archive page at `/blog/`.
- [ ] Generate deterministic later archive pages with no more than twenty
  posts per page.
- [ ] Preserve the archive's current rendered post order.
- [ ] Leave home, tag, feed, sitemap, and individual-post consumers on their
  existing collection and route contracts.

## Supporting facts

- `content/blog.njk` currently has a fixed `/blog/` permalink and no
  pagination block.
- `_includes/postslist.njk` reverses its input collection for display, so
  the pagination slice must be defined with that existing behavior in mind.
- The later-page URL pattern is a requirement question in the parent task;
  the current recommendation is `/blog/page/<page-number>/`.

## Execution plan

Status: Draft

- Configure archive pagination over the existing posts collection with a
  twenty-item page size.
- Keep page one’s permalink explicit and define deterministic later-page
  permalinks after the parent URL decision is approved.
- Pass only the current page’s posts to the existing list rendering boundary,
  avoiding changes to collection sorting or reversal.
- Verify that the archive source does not cause home, tag, feed, sitemap, or
  post routes to consume paginated subsets accidentally.

### Implementation decisions and open questions

- Resolve the parent task’s later-page URL question before implementation.
- Confirm whether the current archive's displayed sequence is best preserved
  by paginating before the include's reverse or by supplying a page-specific
  ordered slice; prove the choice with fixture posts whose order is
  unambiguous.

### Documentation

No separate documentation change belongs in this subtask. Report the final
URL and ordering behavior to the parent documentation subtask.

### Task checklist

- [ ] Implement the approved archive pagination configuration.
- [ ] Verify first-page and later-page output paths in a production build.
- [ ] Verify no shared collection consumer changed behavior.

### Requirement verification

- Build with more than twenty posts and inspect every archive page for a
  maximum of twenty list entries, stable paths, and preserved display order.
- Inspect home, tag, feed, sitemap, and individual-post output from the same
  build to confirm their existing routes and collection behavior remain
  intact.