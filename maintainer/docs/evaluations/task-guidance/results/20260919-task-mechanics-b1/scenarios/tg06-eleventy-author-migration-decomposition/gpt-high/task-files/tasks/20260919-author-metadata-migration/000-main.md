# Migrate post author metadata to structured multi-author data

Plan the transition from the single `author` front-matter string to an
ordered, structured multi-author model across source content, Eleventy
templates, generated artifacts, and the post-authoring helper while preserving
existing content and public pages during the compatibility window.

## Requirements checklist

- [ ] Posts have a canonical structured representation that can express the
      ordered authors for a post, including the current single-author cases.
- [ ] Existing posts are migrated safely without losing titles, body content,
      routes, tags, layout behavior, or author display data.
- [ ] Post templates, home/blog/tag archive paths, and the feed consume the
      canonical author model; generated pages and feed output remain valid and
      preserve existing single-author behavior while representing multiple
      authors according to the approved public contract.
- [ ] The post-authoring helper emits the canonical metadata and no longer
      requires callers to author the legacy single-name field.
- [ ] The legacy field remains supported for the transition until source
      content and generated-output evidence demonstrate that no dependency
      remains; any rejection/removal is a separately verified final step.
- [ ] Tests exercise the real Eleventy production build and the authoring
      helper at the boundaries where the migration can regress.
- [ ] Maintained user/developer guidance describes the supported authoring
      format and transition state after implementation.

## Scope and workstreams

The migration is organized into four dependent workstreams:

1. Establish the canonical data shape, a transition normalizer/compatibility
   policy, and migrate the checked-in posts.
2. Move the post layout, shared archive rendering, and feed generation to the
   canonical model while preserving public routes and valid output.
3. Update the authoring helper and its contract so newly created posts use the
   new model.
4. Run the integrated source/output audit and authorize legacy rejection only
   when the evidence gate passes.

The work includes the existing Eleventy source tree, checked-in post content,
the `scripts/new-post.js` helper, generated-output tests, and maintained
guidance. It excludes unrelated archive pagination and unrelated upstream
fixture changes.

## Requirement questions and decisions

- The request does not specify the exact structured schema. The recommended
  direction is an ordered `authors` list whose entries carry at least a
  display name, with one canonical internal representation for both migrated
  single-author and new multi-author posts. Confirm whether author entries
  need an identifier, URL, or other fields before implementation.
- The request does not specify how multiple authors should appear in the XML
  feed. Decide whether the feed should emit one `<author>` element per author
  in source order or use another approved feed contract.
- Decide whether a post containing both legacy `author` and canonical
  `authors` is accepted during transition, and if so how conflicts are
  detected or resolved. Do not silently define this compatibility behavior
  during implementation.
- The exact point at which legacy rejection is enabled is intentionally
  evidence-driven. The cutover subtask must keep rejection disabled until the
  source and generated-output checks pass and record the evidence used.

## Supporting facts

- `content/posts/first.md` and `content/posts/second.md` currently provide a
  scalar `author` value; `content/posts/posts.json` supplies the post layout
  and `posts` tag.
- `_includes/layouts/post.njk` renders the legacy value directly.
- `content/index.njk`, `content/blog.njk`, and `content/tag-pages.njk` share
  `_includes/postslist.njk`; the current list exposes title and URL only, so
  archive coverage must verify that moving author data does not alter list
  routes, ordering, or rendering.
- `content/feed.xml.njk` reads `post.data.author` directly and is the current
  feed dependency on the legacy field.
- `scripts/new-post.js` accepts `(title, author)` and writes scalar
  `author` front matter.
- `tests/author-output.test.js` and `tests/archive-output.test.js` currently
  contain comments but no decisive assertions. `npm test` runs
  `node --test tests/*.test.js`, while `npm run build` is the production
  Eleventy boundary.
- There is no `docs/index.md`; the maintained documentation currently
  consists of `README.md` and `docs/development/index.md` plus the repository
  guidance in `AGENTS.md`.

## Execution plan

Status: Draft

First agree the canonical schema and public feed semantics. Then implement the
normalization/migration boundary, update each production consumer, and update
the authoring helper. Keep the compatibility path active while the integrated
build renders migrated and legacy-shaped fixtures. Finally audit source
references and generated output, record the passing evidence, and only then
enable legacy rejection as a separately reviewable cutover.

### Implementation decisions and open questions

- The canonical model must be ordered so author display and feed output are
  deterministic.
- Compatibility should be centralized at the data boundary rather than
  duplicating legacy-field checks across templates.
- The feed contract and dual-field behavior remain open until the requester
  confirms them; they affect public output and validation behavior.
- A source grep alone is not sufficient for cutover: the evidence must include
  a successful production build and inspection/assertions over generated post,
  archive, and feed artifacts.

### Documentation

- Update `README.md` or the owning developer documentation with the canonical
  front-matter example, authoring-helper usage, and the transition/rejection
  status once implementation makes those claims true.
- Do not document legacy rejection as current behavior before the cutover
  evidence gate is complete.
- Keep migration-specific test and verification notes with this task or the
  owning subtask; do not create placeholder documentation sections.

### Task checklist

- [ ] Complete `tasks/20260919-author-metadata-migration/010-schema-and-content-migration.md`.
- [ ] Complete
      `tasks/20260919-author-metadata-migration/020-generated-consumers.md`.
- [ ] Complete
      `tasks/20260919-author-metadata-migration/030-authoring-tool.md`.
- [ ] Complete
      `tasks/20260919-author-metadata-migration/040-legacy-cutover-evidence.md`.
- [ ] Resolve the public schema and feed/dual-field requirement questions
      before marking execution approved.
- [ ] Keep this plan and child statuses synchronized as execution proceeds.

### Requirement verification

- Canonical metadata and safe source migration: the schema/content subtask
  must show migrated post front matter plus a real Eleventy build that
  renders the migrated posts without route, tag, body, or title loss.
- Generated consumers: the generated-consumers subtask must assert post,
  home/blog/tag archive, and feed artifacts from the production build,
  including ordered multi-author behavior and preserved single-author output.
- Authoring tool: the authoring-tool subtask must test the helper's generated
  front matter through the same parsing/build path used by posts.
- Legacy transition and rejection: the cutover subtask must show no remaining
  legacy source dependencies, successful generated-output assertions, and an
  explicit decision/evidence record before enabling rejection.

### Additional implementation verification

- Run the complete test command and production build after all subtasks are
  integrated.
- Inspect the build output for malformed markup, empty author values, and
  accidental route changes.
- Confirm the repository diff contains only the approved migration,
  verification, and documentation changes.
