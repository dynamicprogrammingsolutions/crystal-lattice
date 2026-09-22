# Prove migration completeness and reject the legacy author form

Own the final compatibility gate: establish that source content and generated
outputs no longer depend on the single-name field, then enable and verify
legacy-form rejection.

Parent Task: tasks/20260920-author-metadata-migration/000-main.md

Depends On:
tasks/20260920-author-metadata-migration/010-source-contract-and-content-migration.md
tasks/20260920-author-metadata-migration/020-rendering-and-output-surfaces.md

## Requirements checklist

- [ ] A complete content/source inventory shows no supported post still relies
  on the legacy single-name field.
- [ ] A clean production build and generated-output inspection show that post
  pages, home/blog/tag archives, and feeds do not depend on the legacy field.
- [ ] Transition compatibility is retained until both evidence conditions pass.
- [ ] After the evidence gate passes, the approved boundary rejects legacy
  input with a clear actionable error.
- [ ] The final documentation describes only the now-supported canonical form
  and the verified rejection behavior.

## Unresolved requirement questions and decisions

- The exact enforcement boundary remains the parent-level requirement
  question: authoring helper, front matter validation, Eleventy build, or a
  combination. The chosen boundary must cover all supported authoring paths.
- Decide whether a legacy-field negative test remains permanently as regression
  coverage after rejection; the recommended approach is yes, because it
  protects the compatibility contract.

## Research and supporting facts

- The repository currently has two post files and both use `author`; the
  content inventory must be rerun after migration rather than assuming this
  remains the complete set.
- Existing generated-output tests are placeholders, so current test names
  cannot serve as the evidence gate.
- The build output directory is `_site`, and the normal build command is
  `npm run build`.
- The legacy field is currently consumed directly by the post layout and feed;
  any remaining reference or fallback must be classified as intentional
  transition code before rejection.

## Execution plan

Status: Draft

First run a repository/content inventory that distinguishes migrated source,
intentional compatibility code, tests, documentation, and generated output.
Then run the production build with representative migrated and
multiple-author content and inspect all author-bearing output surfaces from
subtask 020. Repeat with a real legacy fixture while compatibility is still
enabled. Record the commands and decisive assertions in the implementation
notes so the cutover is auditable.

Only when the inventory and generated-output checks are both clean, enable the
approved legacy rejection at the agreed boundary. Add a negative test that
passes legacy input through the actual supported path and asserts the clear
failure. Remove obsolete compatibility branches only after that test and the
full production build pass; retain intentional historical migration evidence
as documentation or test data without allowing it as supported input.

### Implementation decisions and open questions

- The rejection gate is a hard dependency, not a cleanup step: no legacy
  rejection may ship on source inspection alone.
- Generated-output evidence must cross the Eleventy build boundary and include
  the public page/archive/feed paths, not just inspect template source.
- Resolve the enforcement boundary before execution and do not broaden it to
  reject unrelated unknown metadata.

### Documentation

Update the package-owned authoring guidance only after the gate passes. State
the canonical field, accepted multi-author shape, authoring-helper usage, and
the legacy-field rejection with an example of the supported replacement. If
the project retains migration notes, label them as historical rather than
supported input instructions.

### Task checklist

- [ ] Confirm the enforcement boundary and permanent negative-test policy.
- [ ] Inventory source/content and classify every remaining legacy reference.
- [ ] Run clean production-build and generated-output evidence.
- [ ] Verify transition compatibility before rejection.
- [ ] Enable legacy rejection only after both evidence conditions pass.
- [ ] Run the negative legacy-input test through the real supported path.
- [ ] Run the full test suite and final production build.
- [ ] Update maintained documentation and record immutable completion notes.

### Requirement verification

- **Content evidence:** Search all supported post sources and authoring
  inputs, then parse the complete inventory through the normal build path.
  The only remaining legacy references may be explicitly classified
  migration fixtures or historical documentation.
- **Generated-output evidence:** Build from migrated content and inspect
  generated post, home, blog, tag, and feed files for complete canonical
  author output and absence of legacy-dependent rendering.
- **Transition ordering:** Demonstrate that the legacy fixture succeeds before
  the gate and fails only after the clean inventory/build evidence is
  recorded.
- **Rejection:** Invoke the actual supported input/build path with a legacy
  `author` field and assert a deterministic, actionable failure.
- **Final regression:** Run `npm test` and `npm run build`, then verify the
  generated pages and feed remain complete after compatibility code is
  removed or disabled.