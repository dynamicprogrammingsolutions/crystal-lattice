# Structured post author metadata migration

Migrate post authors from the current scalar `author` front-matter value to a
structured, ordered multi-author representation while preserving existing
content and generated output throughout the transition. Execution is not
approved by creating this task set.

## Requirements checklist

- [ ] Post metadata supports the agreed structured multi-author form, including
      ordered authors and the single-author case.
- [ ] Existing posts and any still-supported legacy inputs remain renderable
      during the transition, with their author meaning preserved.
- [ ] Post templates, shared archive/list surfaces, feeds, and authoring tools
      consume and produce the structured form rather than depending on the
      scalar legacy field.
- [ ] The repository's existing posts are migrated safely without changing
      their titles, body content, routes, tags, or intended author identity.
- [ ] Production-generated pages and feeds preserve required author output for
      single-author posts and correctly represent multiple authors.
- [ ] Legacy `author` input is rejected or removed only after repository content
      and generated-output evidence demonstrates that no supported path still
      depends on it.
- [ ] Maintained user/developer guidance describes the supported authoring form
      and the completed transition.

## Scope and workstreams

The migration covers post front matter and shared post defaults, the post
layout, the archive/list include used by the home page, blog archive, and tag
pages, the XML feed, `scripts/new-post.js`, the existing post fixtures, and
production-build tests. Sitemap behavior is not an author consumer and should
remain unchanged except for regression evidence. Generated `_site` output is
verification evidence, not a source to edit.

The work is split so the author contract and compatibility policy are decided
before content or templates change; content/tool and rendering changes can then
proceed independently; the legacy form is removed only through the final
evidence gate. Documentation is completed with the migration rather than
creating speculative standalone pages.

## Unresolved requirement questions

1. What is the approved structured shape and required identity field? The
   recommended starting point is an ordered `authors` array whose entries have
   a required `name` field, mapping `"Ada Example"` to
   `authors: [{ name: "Ada Example" }]`. Adding IDs, URLs, or biographies
   would expand the public contract and needs approval.
2. What public representation is required for multiple authors in post pages,
   archive/list output, and the feed? The implementation needs an approved
   separator/markup policy for HTML and whether the feed emits one author
   element per author or a structured nested form.
3. During the transition, should the authoring tool accept both the legacy
   scalar argument and the new collection, or should only repository content
   be dual-read? The plan assumes a deliberately bounded compatibility window,
   with any accepted legacy input normalized to the new model before the final
   rejection gate.

## Research and supporting facts

- `content/posts/first.md` and `content/posts/second.md` use scalar
  `author` values.
- `content/posts/posts.json` supplies the shared post layout and `posts` tag.
- `_includes/layouts/post.njk` renders `author` directly.
- `content/feed.xml.njk` renders `post.data.author` directly into one feed
  entry per post.
- `_includes/postslist.njk` is shared by `content/index.njk`,
  `content/blog.njk`, and `content/tag-pages.njk`; it currently renders titles
  only, so it is an archive consumer that must be checked for the new
  structured author display or deliberately kept author-independent.
- `scripts/new-post.js` serializes the scalar `author` field and is the
  authoring-tool boundary.
- `tests/archive-output.test.js` and `tests/author-output.test.js` currently
  contain comments describing intended coverage but no executable assertions.
- `package.json` exposes `npm run build` through Eleventy and
  `npm test` through Node's test runner.
- `README.md` documents the generated site surfaces but does not document
  post author front matter or the authoring tool.

## Execution plan

Status: Draft

1. Resolve the structured metadata and public rendering questions, then
   record the compatibility window and the exact condition for rejecting
   `author`.
2. Add focused migration coverage and update the existing posts plus shared
   defaults and authoring tool to use the agreed model, retaining only the
   approved transitional read/normalization path.
3. Update the post layout, archive/list surface, and feed to consume the
   normalized author collection. Preserve routes, tags, post content, and
   non-author site surfaces.
4. Build the real site and assert generated post pages, home/blog/tag
   archive output, and feed output for one and multiple authors. Search source
   content, templates, tools, and generated output for remaining legacy
   dependencies.
5. Only when the evidence gate is green, remove or reject the legacy form.
   Rebuild and rerun the full focused suite after that change.
6. Update the smallest maintained documentation surface with the supported
   front-matter/tool contract, transition status, and verification boundary.

### Implementation decisions and open questions

- The exact `authors` schema, HTML/feed representation, and authoring-tool
  compatibility API remain open and require approval before execution.
- Recommended compatibility behavior is dual-read/normalize during migration,
  followed by explicit rejection of scalar `author` only after content and
  generated-output scans plus production-build tests pass.
- No URL, title, body, tag, or sitemap contract should change as part of this
  migration.

### Documentation

- Update `README.md` or the owning developer documentation only after the
  supported schema and compatibility status are implemented and verified.
- Document the authoring-tool input and the single-/multi-author examples.
- Do not add a placeholder documentation directory or edit generated output.

### Task checklist

- [ ] Complete `tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md`.
- [ ] Complete `tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md`.
- [ ] Complete `tasks/20260919-author-metadata-migration/030-rendering-and-output-migration.md`.
- [ ] Complete `tasks/20260919-author-metadata-migration/040-verification-and-legacy-removal.md`.
- [ ] Complete `tasks/20260919-author-metadata-migration/050-documentation-and-release-handoff.md`.
- [ ] Append completion notes only after all requirements have evidence.

### Requirement verification

- Structured metadata and transition compatibility: contract tests plus a
  production build containing migrated single-author content and a
  multi-author fixture.
- Template, archive, and feed migration: generated-output assertions at the
  public HTML/XML boundary for post pages, home/blog/tag pages, and the feed.
- Safe existing-content migration: source diff/content inspection plus
  generated route, title, body, tag, and author-identity assertions.
- Legacy rejection gate: repository-wide source/content scan and generated
  output scan show no remaining supported dependency, followed by a build and
  test run with the legacy form rejected.
- Documentation: review the maintained guidance against the implemented
  schema and tool behavior.

### Additional implementation verification

- Confirm XML remains well-formed after multiple author elements or the
  approved nested representation is emitted.
- Confirm HTML escaping and author ordering with names containing punctuation
  or characters that require escaping.
- Confirm archives and tag pages still render with the existing collection
  ordering and routes.