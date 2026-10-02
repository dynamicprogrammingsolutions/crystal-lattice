# Verify the migration and remove the legacy dependency

Turn the current placeholder coverage into evidence at the production
generated-output boundary, then remove or reject the scalar legacy form only
when the agreed gate is satisfied.

Parent Task: tasks/20260919-author-metadata-migration/000-main.md
Depends On: tasks/20260919-author-metadata-migration/020-content-and-authoring-migration.md
Depends On: tasks/20260919-author-metadata-migration/030-rendering-and-output-migration.md

## Requirements checklist

- [ ] Archive and author-output tests execute real production build behavior
      rather than only documenting intended coverage.
- [ ] Tests cover migrated single-author content and multiple authors across
      post pages, archives, tag pages, and feeds.
- [ ] Source/content scans and generated-output inspection show no supported
      dependency on scalar `author` before rejection.
- [ ] The legacy form is rejected or removed only after the evidence gate.
- [ ] A final build and test run passes after legacy rejection.

## Research and supporting facts

The existing `tests/archive-output.test.js` and
`tests/author-output.test.js` are comments only. `npm run build` is the
production Eleventy build and `npm test` runs Node tests. The parent task
requires evidence that crosses the generated-output boundary, not only unit
tests with mocked post data.

## Execution plan

Status: Draft

1. Replace the placeholder tests with executable tests that invoke the
   production build or its real output path and inspect generated files.
2. Add coverage for route preservation, author ordering/identity, archive
   visibility, feed structure, and existing non-author output.
3. Run repository-wide searches over source content, templates, scripts,
   tests, and generated output to classify every remaining `author` reference
   as approved compatibility code, documentation, or an obsolete dependency.
4. Apply the approved legacy rejection/removal only after the search and
   generated-output assertions are clean.
5. Rebuild and rerun the complete focused suite after rejection; retain the
   evidence and report any gated test that could not run.

### Implementation decisions and open questions

- The exact assertion strings and feed shape follow subtask 010.
- A search result alone is not sufficient evidence; it must be combined with
  a successful production build and generated-output assertions.
- Do not reject legacy content merely because migrated fixtures no longer use
  it; verify all supported content and tool paths first.

### Documentation

Provide the final test commands, evidence boundary, and legacy-removal date
or release condition to subtask 050.

### Task checklist

- [ ] Implement real archive-output coverage.
- [ ] Implement real author-output coverage.
- [ ] Add source/content/generated-output dependency scans.
- [ ] Pass the legacy rejection gate.
- [ ] Rebuild and rerun tests after rejection.

### Requirement verification

The decisive evidence is a clean production build plus generated HTML/XML
assertions for all affected surfaces, followed by a clean post-rejection
build/test run. Source and content scans corroborate that no supported path
still relies on scalar `author`.

### Additional implementation verification

Check that tests collect and exit cleanly, do not use test-only template
shortcuts, and do not leave generated artifacts or temporary fixtures in the
repository.