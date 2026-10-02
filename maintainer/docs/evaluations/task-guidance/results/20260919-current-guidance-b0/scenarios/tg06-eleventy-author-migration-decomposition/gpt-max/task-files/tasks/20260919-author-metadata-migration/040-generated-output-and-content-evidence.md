# Prove generated-output and content safety before retirement

Replace placeholder checks with evidence at the production Eleventy boundary
and establish the inventory that controls whether legacy author input may be
rejected.

Parent Task: tasks/20260919-author-metadata-migration/000-main.md
Depends On: tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md
Depends On: tasks/20260919-author-metadata-migration/030-template-archive-and-feed-migration.md

## Requirements checklist

- [ ] Add executable tests for the production build paths named by the
      migration: individual posts, home/archive/tag pages, feed, and sitemap.
- [ ] Cover migrated single-author content, at least one realistic
      multi-author case, and legacy-form compatibility while the transition
      branch is still enabled.
- [ ] Verify URL/path stability and preservation of non-author post content
      and generated page structure.
- [ ] Scan production content, templates, configuration, and authoring tools
      for remaining legacy dependencies and classify intentional compatibility
      coverage separately.
- [ ] Produce a clear green/red evidence result that subtask 050 can use
      before changing legacy behavior.

## Supporting facts

- `tests/archive-output.test.js` and `tests/author-output.test.js` currently
  contain no executable assertions.
- `npm run build` is the repository's real Eleventy production build and
  writes `_site`; `npm test` invokes Node's test runner.
- Existing output consumers include the post layout, shared list, feed, and
  sitemap, while the current archive test does not verify their content.

## Execution plan

Status: Draft

Turn the placeholder test files into focused production-build tests. Exercise
the actual content/templates and inspect generated files for author names,
ordering, escaping, absence of missing values, expected routes, and preserved
non-author content. Ensure the multi-author case crosses the Eleventy
rendering boundary rather than only calling a formatter in isolation.

Run a repository inventory after content and template migration. Every
remaining `author` occurrence must be classified. Production post front
matter, production templates, and the new authoring path must not depend on
the legacy scalar; an intentional transition fixture/test is evidence of the
compatibility branch, not evidence that production still requires it.

Record exact commands, collection/exit results, generated paths inspected,
and any blocker in the parent task. This evidence must be complete before
subtask 050 attempts retirement.

### Implementation decisions and open questions

- The tests must use the real build boundary and may not mock away the
  normalizer or substitute a test-only rendering path.
- The accepted archive and feed assertions depend on the contract approved by
  the parent task.
- Decide whether to keep a legacy compatibility fixture after rejection. If
  retained, it must assert rejection rather than silently keeping a positive
  dependency.

### Documentation

The evidence report belongs in task implementation/completion notes during
execution. Do not publish a claim that legacy input is rejected until the
final gate actually passes.

### Task checklist

- [ ] Add executable archive and author output coverage.
- [ ] Add production-build coverage for single, multiple, and legacy-form
      cases.
- [ ] Verify post, home/archive/tag, feed, sitemap, route, and content
      stability.
- [ ] Run content/template/tool inventory and classify all legacy references.
- [ ] Mark the evidence gate green only when every approved condition passes;
      otherwise record the exact blocker and keep retirement disabled.

### Requirement verification

- `npm test` collects and exits successfully with meaningful assertions.
- `npm run build` exits successfully and generated files contain the expected
  author output on all relevant surfaces.
- Generated-output assertions prove existing URLs and non-author content are
  preserved while all approved authors render.
- The inventory proves no unclassified production dependency remains on the
  legacy scalar before retirement is considered.
- The resulting evidence record explicitly authorizes or blocks subtask 050;
  no inference from a passing unit test alone is sufficient.