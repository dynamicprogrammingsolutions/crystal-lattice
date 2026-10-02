# Render structured authors across public surfaces

Move all author-consuming templates and generated surfaces to the canonical
multi-author model while preserving the approved transition compatibility.

## Requirements checklist

- [ ] Render every author on individual post pages using the approved order
  and presentation.
- [ ] Move the shared archive/list path used by the home page, `/blog/`, and
  tag pages to the structured model, with the approved author visibility and
  link behavior.
- [ ] Render every author in the feed using valid escaped XML and the approved
  feed representation.
- [ ] Ensure no template reads the legacy single-name field directly.

Parent Task: tasks/20260925-author-metadata-migration/000-main.md
Depends On: tasks/20260925-author-metadata-migration/010-data-contract-and-authoring.md

## Unresolved requirement questions

- What exact author presentation is required in archive/list views, which
  currently render only post titles?
- Should post-page authors and feed authors expose only names, or approved
  identity fields as links/attributes?
- Is one feed `<author>` element containing multiple names acceptable, or does
  the feed contract require one author element per author?

## Decisions

- The shared `_includes/postslist.njk` is the ownership point for the
  home/archive/tag list behavior; duplicating author logic in each page is
  out of scope.
- The production build must be exercised with real migrated content; tests
  that pass synthetic normalized data directly to a template are supporting
  checks only.
- Output escaping and stable author order are compatibility requirements for
  generated HTML and XML.

## Research and supporting facts

- `_includes/layouts/post.njk` currently prints `author` directly.
- `_includes/postslist.njk` is included by `content/index.njk`,
  `content/blog.njk`, and `content/tag-pages.njk`, but currently prints only
  title links.
- `content/feed.xml.njk` currently reads `post.data.author` directly and
  emits one `<author>` element per post.
- `content/posts/posts.json` supplies the post layout and `posts` tag; no
  author-specific collection or archive template exists.

## Execution plan

Status: Draft

Consume the normalized structured author data from the shared templates.
Implement the approved display semantics once in the post layout/list include
and once in the feed template, preserving the current URLs and page
collection behavior. Add executable generated-output assertions rather than
only template-string checks.

1. Confirm the approved HTML and feed representation against the data
   contract from subtask 010.
2. Update the post layout and shared list include, then verify all callers:
   home, blog archive, and tag pages.
3. Update the feed template to represent all authors and escape names
   correctly.
4. Extend author-output and archive-output coverage to run a production build
   and assert the public output for one- and multiple-author posts.
5. Inspect generated output for absence of literal legacy-field rendering and
   preservation of existing URLs.

### Implementation decisions and open questions

The archive display and feed cardinality questions are material public-output
decisions and stay open until approved. Local choices such as loop structure
and whitespace can be resolved during implementation. Any change to URLs,
feed location, or author identity semantics returns the parent plan to Draft.

### Documentation

Record the public author rendering semantics in the development guidance if
they are relevant to people creating or reviewing posts. Do not document
generated markup details that are not part of the approved contract.

### Task checklist

- [ ] Resolve public post, archive/list, and feed presentation.
- [ ] Update the post layout and shared list include.
- [ ] Update the feed template.
- [ ] Add generated-output assertions for all relevant surfaces.
- [ ] Verify URLs and escaping remain stable.

### Requirement verification

- Post and list rendering: run the real Eleventy build with representative
  one- and multiple-author posts, then assert the generated post, home,
  `/blog/`, and tag HTML contains all approved authors in order.
- Feed rendering: inspect generated `/feed/feed.xml` and assert every author
  appears in the approved XML structure with escaped markup.
- Legacy template dependency: scan author-consuming templates and inspect the
  generated output after the build; no direct legacy read or literal legacy
  value may remain.

### Additional implementation verification

- Confirm a name containing `&`, `<`, or `>` is escaped correctly in both HTML
  and XML contexts.
- Confirm shared list behavior remains valid when a post has multiple
  authors, including whitespace and separator behavior.