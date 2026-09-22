# Archive pagination regression coverage

Replace the placeholder archive check with production-build evidence for
pagination and preservation of the site's existing public outputs.

Parent Task: tasks/20260919-blog-archive-pagination/000-main.md

Depends On:

- tasks/20260919-blog-archive-pagination/010-archive-pagination-generation.md
- tasks/20260919-blog-archive-pagination/020-accessible-archive-navigation.md

## Requirements checklist

- [ ] Test the first archive page, later-page size, stable paths, and post
  order through the production Eleventy build.
- [ ] Test previous/next navigation at first, interior, and final pages.
- [ ] Test preservation of home, tags, feed, sitemap, individual posts, and
  static zero-JavaScript output.

## Supporting facts

- `tests/archive-output.test.js` currently has no executable assertions.
- The fixture has only two posts, which cannot prove a twenty-post page limit
  or later-page navigation. The test needs a realistic build input with more
  than twenty posts.
- The sitemap iterates `collections.all`, and the feed iterates
  `collections.posts`, so both are useful regression boundaries for accidental
  collection changes.

## Execution plan

Status: Draft

- Replace the placeholder with a Node test that invokes the normal Eleventy
  production build.
- Supply enough real post documents to exercise a full first page, an
  interior page, and a final partial page without mocking collections or
  bypassing permalink generation.
- Assert output paths, list counts, order, navigation semantics, preserved
  consumer routes, and static HTML characteristics.
- Keep assertions focused on public output so future implementation changes
  remain free to refactor internals.

### Implementation decisions and open questions

- Decide whether the >20-post input should be durable fixture content or a
  temporary production-build fixture. A temporary fixture is preferable if
  it reuses the real Eleventy configuration and generated output boundary;
  durable content is preferable if test setup would otherwise become a
  second build path.
- Avoid comparing incidental whitespace or generated metadata that is not
  part of the preservation contract.

### Documentation

No documentation changes belong in this subtask. Record the commands and
public boundaries verified for the parent completion notes.

### Task checklist

- [ ] Replace the placeholder test with executable production-build coverage.
- [ ] Add a >20-post scenario and assert all pagination boundaries.
- [ ] Add preservation assertions for existing site outputs.
- [ ] Run the focused test and the repository test command.

### Requirement verification

- A passing production-build test proves archive page size, stable paths,
  ordering, and accessible link states at the generated HTML boundary.
- The same test proves that home, tag, feed, sitemap, and individual-post
  routes continue to be emitted and that no JavaScript is required for the
  archive controls.