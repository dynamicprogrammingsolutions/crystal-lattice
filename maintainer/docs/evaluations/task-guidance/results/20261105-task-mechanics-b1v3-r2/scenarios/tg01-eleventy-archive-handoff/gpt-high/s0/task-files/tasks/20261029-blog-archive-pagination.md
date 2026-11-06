# Paginate the blog archive

Keep the first archive at `/blog/` and make the growing archive easier to browse with stable, bounded pages and accessible navigation, without changing the site's other outputs or adding client-side JavaScript.

## Requirements checklist

- [ ] Keep `/blog/` as the first archive page and show no more than twenty posts on any archive page.
- [ ] Generate stable later archive pages and provide accessible previous/next navigation between applicable pages.
- [ ] Preserve the home page, tag pages, feed, sitemap, individual-post navigation, post order, and static zero-JavaScript output.

## Unresolved questions

- Which URL pattern should identify later pages? Recommendation: `/blog/page/2/`, `/blog/page/3/`, and so on, while retaining `/blog/` for page one.

## Supporting details

- **Fact:** `content/blog.njk` currently owns `/blog/` and renders `collections.posts` through `_includes/postslist.njk`.
- **Fact:** The shared post list reverses its input. Preserve that ordering behavior for archive pages and avoid changing ordering for tags or other consumers.
- **Fact:** The production build writes to `_site`; the existing archive test file currently contains only a note and does not assert output.
- **Fact:** The README states that the production build emits the home page, archive, tag pages, feed, sitemap, and posts without client-side JavaScript.

## Execution plan
Status: Draft

Implement archive pagination through Eleventy’s normal production build, keeping `/blog/` as the first page and using a fixed page size of twenty. Give subsequent pages deterministic URLs, subject to confirmation of the URL pattern above. Render a semantic navigation region with clearly named previous/next links where those destinations exist; omit a direction’s link at the corresponding boundary rather than emitting a dead or misleading link. Keep pagination scoped to the archive so shared post-list behavior, tag pages, individual posts, and other generated outputs remain unchanged. The build remains fully static and requires no client-side script.

Add or update production-build tests that inspect generated archive output across enough posts to exercise multiple pages and boundary navigation. Verify that the first archive remains at `/blog/`, every page contains at most twenty posts, pages do not skip or duplicate posts, and displayed post order remains unchanged. In the same build-level evidence, check that the home page, tag pages, feed, sitemap, and individual-post navigation remain present and that generated output does not introduce JavaScript for archive navigation. Update the README as user-facing documentation of the resulting archive behavior; do not document the target as current behavior before implementation lands.

### Implementation decisions and open questions

- **Open question:** Confirm the later-page URL pattern. Recommendation: `/blog/page/<number>/`; this keeps the first-page URL unchanged and provides predictable, non-query-based static paths.
- **Decision:** Keep pagination behavior archive-specific rather than changing the shared post-list include or tag pagination.
- **Decision:** Use the production build as the decisive test boundary so generated paths, rendered links, and preserved site outputs are checked together.

### Documentation

- Update `README.md` with the supported archive page size, later-page URL pattern, and previous/next navigation after implementation and URL confirmation.

### Task checklist

- [ ] Confirm the later-page URL pattern.
- [ ] Implement static archive pagination and accessible boundary-aware navigation.
- [ ] Add production-build assertions for page contents, order, links, and preserved outputs.
- [ ] Update the README to describe the implemented behavior.
- [ ] Run the production-build test suite and inspect generated archive output.

### Requirement verification

- **Archive pagination and navigation:** A production build with more than twenty posts verifies `/blog/`, deterministic later URLs, no page over twenty posts, complete ordered coverage without duplication, and correctly bounded accessible previous/next links.
- **Preserved outputs and static behavior:** The same production-build verification checks home, tag pages, feed, sitemap, individual-post navigation, and absence of JavaScript-dependent archive navigation.

### Additional implementation verification

- Run `npm test` and `npm run build`; ensure tests exercise the actual Eleventy production output rather than mocked pagination data.