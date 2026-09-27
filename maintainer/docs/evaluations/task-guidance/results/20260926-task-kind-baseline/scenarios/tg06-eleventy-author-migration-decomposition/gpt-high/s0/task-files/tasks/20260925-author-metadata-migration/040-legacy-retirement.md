# Retire the legacy author field

Perform the final evidence review and remove/reject singular `author` input
only after all source content, production consumers, generated outputs, and
authoring paths demonstrate that they use the structured model.

Parent Task: tasks/20260925-author-metadata-migration/000-main.md

Depends On: tasks/20260925-author-metadata-migration/010-author-contract-and-content.md, tasks/20260925-author-metadata-migration/020-rendering-and-generated-output.md, tasks/20260925-author-metadata-migration/030-authoring-tool.md

## Requirements checklist

- [ ] The repository contains no supported content, template, feed, helper, or test path that depends on singular `author`.
- [ ] Clean production-build evidence covers migrated content and generated post, archive, tag, sitemap, and feed outputs.
- [ ] The legacy field is rejected or removed only after the evidence gate passes.
- [ ] Regression coverage prevents accidental reintroduction of singular author metadata.
- [ ] Documentation no longer presents the singular field as supported current input.

## Research and supporting facts

- The current singular consumers are known in the post layout, feed template,
  and post-generation helper; the final search must be broader than this
  initial inventory.
- Existing tests are placeholders, so the gate must include real build
  execution and content inspection rather than treating test collection as
  evidence.

## Execution plan

Status: Draft

Run the completed focused tests, a repository-wide search for legacy field
references, and a clean Eleventy build from migrated content. Compare
representative generated output with the preserved single-author behavior and
verify a multi-author case. Review the evidence as a single gate. If any
supported path still needs the old field, retain compatibility and record the
gap rather than rejecting it. Once the gate passes, remove the legacy
normalization/rejection allowance, add a regression that fails on singular
front matter or emitted helper output, and update documentation.

### Implementation decisions and open questions

- The legacy cutoff is a compatibility decision, not a cleanup step; it must
  be made only after the named evidence is available.
- If the repository has an external content source not visible in the local
  inventory, pause retirement and add it to the evidence scope before
  rejecting the field.
- Preserve generated URLs and feed location while changing only the author
  data contract and its intended rendering.

### Documentation

- Update the maintained authoring/development guidance to state that
  structured authors are the sole supported form after retirement.
- Record the migration/retirement evidence in the implementation change or
  task completion notes, not as unsupported permanent user guidance.

### Task checklist

- [ ] Run all focused content, rendering, and helper checks.
- [ ] Run a clean production build and inspect representative generated files.
- [ ] Search source, content, scripts, templates, tests, and generated output
  for unsupported singular-field dependencies.
- [ ] Decide whether the evidence gate passes; retain compatibility if it does
  not.
- [ ] Remove/reject the legacy form only if the gate passes.
- [ ] Add the regression guard and finalize documentation.
- [ ] Update the parent task checklist and requirement evidence.

### Requirement verification

- Decisive evidence is the combined real build plus generated-output
  inspection, migrated-content inventory, authoring-helper output checks, and
  repository-wide legacy dependency search.
- Confirm the old field is absent from supported source content and is not
  read by production templates or emitted by the helper.
- Run the complete test command (`npm test`) and the production build
  (`npm run build`) after the cutoff; report any unavailable dependency or
  external-content check as a blocker rather than marking retirement complete.