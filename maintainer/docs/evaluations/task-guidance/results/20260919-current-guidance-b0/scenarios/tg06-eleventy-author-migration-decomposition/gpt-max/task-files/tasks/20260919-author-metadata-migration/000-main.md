# Migrate post author metadata to structured multi-author data

Plan the migration from the current scalar `author` post field to an
approved structured multi-author representation while preserving existing
content and generated pages during the transition. This task is a planning
handoff only; the Draft does not authorize implementation.

## Requirements checklist

- [ ] Define and adopt an approved structured author collection that supports
      one or more authors, preserves author order, and has an explicit display
      contract.
- [ ] Keep existing content and generated public pages working while the
      migration is in progress by retaining an explicit compatibility path for
      the legacy scalar form until the retirement gate is satisfied.
- [ ] Move every author-consuming template and output surface to the approved
      model, including the post layout, home/archive/tag listing surfaces,
      feeds, and any additional consumers found during the inventory.
- [ ] Move the post-authoring tool to the approved model with safe
      serialization and validation for single- and multi-author input.
- [ ] Migrate every existing post without changing its body, title, URL,
      ordering, or unrelated metadata.
- [ ] Produce production-boundary evidence for migrated content, legacy
      compatibility, multi-author rendering, archives, feeds, and generated
      page stability.
- [ ] Reject the legacy form only after content and generated-output evidence
      shows that no production content, template, authoring path, or other
      in-repository dependency still requires it; otherwise leave the
      compatibility path in place and record the blocker.

## Scope and workstreams

The work is divided into five dependency-ordered workstreams:

1. Establish the metadata contract and the single compatibility/normalization
   boundary.
2. Convert existing front matter and the post-authoring helper.
3. Update post, archive/list, tag, and feed rendering to consume the
   normalized collection while preserving routes and unrelated output.
4. Replace placeholder output checks with production-build evidence and a
   complete content/dependency inventory.
5. Retire or reject the legacy form only when the evidence gate is green, and
   update maintained developer guidance to describe the resulting contract.

The task does not include author profile pages, author URLs, identity
resolution, taxonomy changes, archive URL changes, or unrelated template
redesign unless the contract questions below are answered in a way that makes
one of them necessary.

## Requirement questions and decisions

### Unresolved requirement questions

1. What is the exact target shape? The working recommendation is an
   `authors` collection of records such as
   `authors: [{ name: "Ada Example" }]`, preserving source order. A list of
   strings or another record shape would change the authoring and rendering
   contracts and must be chosen before execution.
2. Should archive, home, and tag listings gain a visible multi-author byline,
   or should they preserve their current title-only presentation while
   consuming the new model wherever author data is actually rendered? The
   current `postslist.njk` does not render an author, so adding a byline would
   be a user-visible output change.
3. Is `scripts/new-post.js` a public API whose old
   `frontMatter(title, author)` call shape must remain accepted for a
   deprecation window, or may that call shape be rejected once repository
   evidence is complete? The plan assumes the old shape remains accepted
   during transition and makes final rejection conditional.
4. What should happen if a document contains both legacy `author` and the new
   collection, or if either form is malformed? The migration needs an
   explicit precedence/conflict policy before a strict rejection is enabled.

### Provisional decisions for planning

- Treat the new field as an ordered collection and keep one canonical
  normalized value for all templates and output generators.
- Preserve current URLs, route names, post body content, and non-author output
  unless the approved display contract explicitly adds author text.
- Keep legacy input readable during the migration phase; do not make the
  compatibility branch fail merely because all checked-in posts have been
  converted.
- Make legacy retirement a separately verified final step. A failing or
  incomplete evidence run leaves compatibility enabled and the retirement
  requirement incomplete.

## Research and supporting facts

- `content/posts/first.md` and `content/posts/second.md` currently use the
  scalar front-matter key `author`.
- `_includes/layouts/post.njk` renders the scalar `author` directly.
- `content/feed.xml.njk` reads `post.data.author` directly for every feed
  entry.
- `_includes/postslist.njk` is shared by `content/index.njk`,
  `content/blog.njk`, and `content/tag-pages.njk`; it currently renders only
  title and URL, so archive surfaces do not currently expose an author.
- `scripts/new-post.js` exposes `frontMatter(title, author)` and emits the
  scalar `author` key.
- `eleventy.config.js` has no author normalization or validation boundary.
- `content/posts/posts.json` supplies the post layout and `posts` tag but no
  author data transformation.
- `content/sitemap.xml.njk` emits URLs only; it is not an author consumer but
  belongs in generated-page regression coverage.
- `tests/archive-output.test.js` and `tests/author-output.test.js` currently
  contain comments rather than executable assertions. `npm test` runs
  `node --test tests/*.test.js`, and `npm run build` runs the Eleventy
  production build into `_site`.
- Existing maintained documentation contains no author-front-matter or
  authoring-tool contract. `README.md` is a short site overview and
  `docs/development/index.md` contains only an archive-pagination note.

## Subtasks

- [ ] [tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md](tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md)
- [ ] [tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md](tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md)
- [ ] [tasks/20260919-author-metadata-migration/030-template-archive-and-feed-migration.md](tasks/20260919-author-metadata-migration/030-template-archive-and-feed-migration.md)
- [ ] [tasks/20260919-author-metadata-migration/040-generated-output-and-content-evidence.md](tasks/20260919-author-metadata-migration/040-generated-output-and-content-evidence.md)
- [ ] [tasks/20260919-author-metadata-migration/050-legacy-retirement-and-documentation.md](tasks/20260919-author-metadata-migration/050-legacy-retirement-and-documentation.md)

## Execution plan

Status: Draft

Begin by resolving the target collection shape, rendering contract, authoring
API compatibility, and mixed/malformed-input behavior. Then implement one
normalization boundary that can read both the approved new form and the
legacy scalar form during transition. All templates should consume that
normalized value instead of independently branching on front matter.

After the boundary is available, migrate checked-in posts and the authoring
helper, then update the post layout and all shared listing/feed surfaces. Keep
the existing routes and content stable. Use a real Eleventy build for
multi-author and legacy-compatibility cases; do not rely only on unit tests
that bypass template rendering.

The evidence phase must inventory every remaining legacy reference and
classify it as a production dependency, an intentional migration test, or
historical/documentation text. It must also prove the expected author output
on post pages and feeds, successful archive/home/tag generation, stable URLs,
and successful content scanning. Only that evidence can authorize replacing
the transitional fallback with a rejection/validation path. If it is not
green, leave the fallback enabled and carry the blocker forward.

### Implementation decisions and open questions

- The exact `authors` shape, archive presentation, old authoring-call
  compatibility, and mixed-field policy remain open as listed above.
- The normalizer should have one owner and one documented precedence policy;
  templates must not grow divergent legacy fallbacks.
- The feed representation for multiple authors must be chosen together with
  the display contract, including escaping and author ordering.
- A repository scan cannot establish compatibility for unknown external
  callers of `scripts/new-post.js`; if that helper is externally consumed,
  the final rejection step needs an explicit release/deprecation decision.

### Documentation

No maintained user/developer documentation is changed by this planning task.
Once the contract is implemented, update the smallest existing owner-facing
document, likely `README.md` or an existing development page, with the
approved front-matter example, authoring-tool input, transition behavior, and
the verified legacy status. Do not describe the target contract as current
guidance while this plan is still Draft.

### Task checklist

- [ ] Resolve the four contract questions or record approved answers in the
      implementation notes before changing code.
- [ ] Complete subtask 010 and establish the compatibility/normalization
      boundary.
- [ ] Complete subtasks 020 and 030, preserving content and generated routes.
- [ ] Complete subtask 040 and attach generated-output and content-scan
      evidence to the task.
- [ ] Complete subtask 050 conditionally: reject the legacy form only if the
      evidence gate passes; otherwise retain compatibility and record the
      follow-up.
- [ ] Run the final production build and test suite after the chosen
      retirement outcome.

### Requirement verification

- The approved metadata contract is verified by contract-level tests and an
  inspected example covering one author and multiple ordered authors.
- Transition safety is verified by building a legacy-form post and a
  new-form post through the actual Eleventy input/templates, then checking
  post pages, archive/list routes, tag routes, feed output, sitemap output,
  and unchanged URLs/content.
- Template and feed migration is verified by a repository reference scan plus
  generated-output assertions showing that all rendered author text comes
  from the normalized collection and that no missing/legacy scalar value leaks
  into output.
- Content/tool migration is verified by scanning all production posts and
  authoring-tool output, with focused tests for one author, multiple authors,
  ordering, and safe serialization of names requiring quoting/escaping.
- Legacy rejection is verified only after the content/dependency inventory is
  clean and the generated-output suite passes with migrated content. A
  failed gate is evidence for retaining compatibility, not permission to
  reject the field.