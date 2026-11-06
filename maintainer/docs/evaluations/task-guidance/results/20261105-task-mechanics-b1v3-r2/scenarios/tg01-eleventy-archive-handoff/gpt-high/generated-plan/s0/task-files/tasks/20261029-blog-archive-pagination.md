# Paginate the Blog Archive

Add static pagination to the growing blog archive while preserving the existing site outputs and navigation behavior.

## Requirements checklist

- [ ] Keep `/blog/` as the first archive page.
- [ ] Generate stable later archive pages, with no more than twenty posts per page.
- [ ] Provide accessible previous/next navigation between archive pages.
- [ ] Preserve the home page, tags, feed, sitemap, individual-post navigation, and existing post order.
- [ ] Keep the output static and free of client-side JavaScript.

## Unresolved questions

- **Requirement question:** What URL pattern should later pages use? Recommendation: `/blog/2/`, `/blog/3/`, and so on, keeping `/blog/` unchanged. The route pattern is user-visible and should be confirmed before execution.

## Supporting details

- **Fact:** `content/blog.njk` currently renders all of `collections.posts` at `/blog/`.
- **Fact:** `_includes/postslist.njk` reverses the passed list for display. The home page and tag pages use this include too, so pagination should preserve its existing shared behavior and the archive’s current order.
- **Fact:** `content/tag-pages.njk` already uses Eleventy pagination; `eleventy.config.js` has no custom pagination behavior.
- **Fact:** The sitemap is generated from `collections.all`; the feed separately uses the posts collection.
- **Fact:** `tests/archive-output.test.js` is currently a placeholder and has no assertions. `npm test` runs Node’s built-in test runner; `npm run build` runs the Eleventy production build.
- **Fact:** `README.md` describes the existing static outputs. `docs/development/index.md` says no archive pagination specification exists.

## Execution plan
Status: Draft

Use Eleventy’s production pagination to generate the archive from `collections.posts`, with a page size of twenty and a permalink scheme confirmed before execution. Keep the first generated page at `/blog/`; expose each page’s current posts to the existing list include so its established reverse-display ordering remains consistent. Render previous/next controls as a labeled navigation landmark with descriptive links only where a neighboring page exists. Keep all archive behavior in generated HTML, without client-side JavaScript.

The archive pages must be validated through the real Eleventy build, not just isolated template rendering. Build tests should exercise a content set large enough to produce multiple pages and check page boundaries, ordering, navigation, and the selected URLs. Also verify the existing home page, tag pages, feed, sitemap, and individual post output remain available and that the rendered site contains no client-side pagination script.

### Implementation decisions and open questions

- Resolve the later-page URL pattern before implementation; `/blog/<page-number>/` is recommended because it is stable and preserves the existing first-page route.
- Use Eleventy pagination and existing post-list rendering rather than adding a client-side or custom runtime paging layer.
- Keep previous/next links within the archive sequence, with no link for a missing neighbor at either end.

### Documentation

- Update `README.md` to describe the archive’s current page-size and navigation behavior after implementation.
- Update `docs/development/index.md` to remove its outdated statement that no archive pagination specification exists, replacing it with a concise link or description appropriate to that page’s audience.

### Task checklist

- [ ] Confirm the later-page URL pattern.
- [ ] Configure Eleventy archive pagination and accessible navigation.
- [ ] Add production-build coverage for multiple archive pages and preserved outputs.
- [ ] Update maintained documentation after behavior is implemented.

### Requirement verification

- Requirements 1–3: Build the site with more than twenty posts and inspect generated archive files and their rendered links. Assert `/blog/` remains page one, every page contains at most twenty posts, ordering matches the existing archive, and previous/next navigation is accessible and points to the adjacent generated pages.
- Requirement 4: In the same production-build test, assert the home page, tag pages, feed, sitemap, and individual post files remain present and their existing post order/navigation behavior is unchanged.
- Requirement 5: Inspect generated output from the production build and assert archive navigation and post lists are HTML links/lists, without client-side pagination JavaScript.

### Additional implementation verification

- Run `npm test` and `npm run build` after implementation; both cross the repository’s actual test or production-build boundary.