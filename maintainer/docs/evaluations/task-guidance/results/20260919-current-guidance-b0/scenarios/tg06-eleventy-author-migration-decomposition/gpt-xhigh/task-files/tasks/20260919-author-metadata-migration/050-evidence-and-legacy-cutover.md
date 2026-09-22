# Prove migration completeness and remove legacy dependence

Close the migration only after content and generated-output evidence prove the
site no longer depends on the single-name field, then make the legacy form
unavailable with a regression test.

Parent Task: tasks/20260919-author-metadata-migration/000-main.md

Depends On: tasks/20260919-author-metadata-migration/020-compatibility-and-rendering.md, tasks/20260919-author-metadata-migration/030-content-migration.md, tasks/20260919-author-metadata-migration/040-authoring-tool-and-guidance.md

## Requirements checklist

- [ ] Run the complete relevant test suite and production build against the
  migrated content and structured fixtures.
- [ ] Verify generated post, home, archive, tag, feed, and sitemap output has no
  remaining legacy author dependency and preserves required site behavior.
- [ ] Verify source content, templates, scripts, and tests have no supported
  runtime dependency on the legacy field.
- [ ] Remove the temporary compatibility path only after the preceding
  evidence is recorded.
- [ ] Make the final legacy form fail clearly and add regression coverage for
  that rejection.

## Open requirement questions and material decisions

- The exact rejection error/message and whether rejection occurs at build,
  validation, or authoring input are implementation details only after the
  parent contract defines the final boundary.
- If external content outside this repository is discovered, pause the
  cutover and ask whether that source is in scope; do not claim repository
  evidence proves external independence.

## Supporting facts

The current test command is `node --test tests/*.test.js`, and the production
build command is `eleventy` via `npm run build`. Existing archive and author
test files do not yet execute assertions, so this gate must establish real
coverage rather than rely on their comments.

## Execution plan

Status: Draft

Run source scans that exclude planning text but include all supported content,
templates, scripts, and tests. Build with migrated posts plus explicit
single-/multi-author fixtures, inspect every generated surface, and run the
full test command. Record the evidence in the parent task. Only then remove
the compatibility reader and add a negative test showing that a legacy
front-matter post is rejected at the chosen boundary. Re-run the build and
tests after removal, and update the task checklist only from those results.

### Implementation decisions and open questions

The cutover is a gated decision, not a date-based cleanup. Any remaining
legacy source read, generated legacy output, or unclassified content blocks
rejection and must be resolved or explicitly brought back to the parent task
for scope review.

### Documentation

Update the developer guidance to state that the structured field is now
required and the legacy field is rejected only when the recorded evidence
supports that claim. Preserve migration notes only if they help maintainers
handle historical content.

### Task checklist

- [ ] Run source-content and runtime-dependency scans.
- [ ] Run production build and inspect all relevant generated surfaces.
- [ ] Run `npm test` and record meaningful passing coverage.
- [ ] Record the evidence threshold as met or identify blockers.
- [ ] Remove compatibility handling only after the threshold is met.
- [ ] Add and pass final legacy-rejection regression coverage.
- [ ] Re-run build/tests and update parent requirement evidence.

### Requirement verification

- Source scan proves no supported post, template, script, test, or config
  depends on the legacy field.
- Generated-output scan/build proves all relevant pages and feeds are produced
  from structured metadata and meet the approved output contract.
- Full test and build runs pass after compatibility removal.
- A negative regression test proves the legacy form is rejected at the final
  approved boundary.

### Additional implementation verification

- Check generated output for accidental empty author elements, duplicate
  authors, malformed feed XML, and URL/order regressions.
- Confirm the final source scan does not mistake task-history wording for a
  runtime dependency, while still covering all executable inputs.