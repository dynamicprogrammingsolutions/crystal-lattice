# Gate removal or rejection of the legacy author field

Define and execute the final compatibility gate. Legacy input must remain
available until source and generated-output evidence proves that the migrated
site and authoring path no longer depend on it.

Parent Task: tasks/20260919-author-metadata-migration/000-main.md
Depends On:
  - tasks/20260919-author-metadata-migration/010-schema-and-content-migration.md
  - tasks/20260919-author-metadata-migration/020-generated-consumers.md
  - tasks/20260919-author-metadata-migration/030-authoring-tool.md

## Requirements checklist

- [ ] The compatibility window remains enabled while migrated and
      legacy-shaped content are both covered.
- [ ] A source/content audit finds no remaining required legacy field usage in
      posts, templates, scripts, or maintained fixtures.
- [ ] A production build proves generated posts, home/blog/tag archives, feed,
      and sitemap still generate successfully from the canonical model.
- [ ] Generated artifacts are inspected/asserted for preserved routes and
      approved author output, including multi-author cases.
- [ ] Legacy rejection/removal is enabled only after the preceding evidence
      passes and is recorded as a deliberate cutover.
- [ ] Post-cutover tests prove the canonical path remains supported and the
      intended legacy failure behavior is explicit.

## Requirement questions and decisions

- Confirm whether the desired final state is hard rejection of legacy
  front matter, removal of a compatibility normalizer, or both.
- Confirm whether any external/untracked content source is in scope for the
  dependency audit; the repository currently exposes only checked-in posts.
- Confirm the exact error/reporting contract for a legacy field after
  rejection. Do not introduce an undocumented failure mode.

## Supporting facts

- Existing generated-output test files are currently placeholders, so the
  cutover cannot rely on prior test names as evidence.
- `npm run build` is the production generation boundary and `npm test` is the
  repository test boundary.
- Direct legacy dependencies are currently visible in the post layout, feed,
  and authoring helper; archive rendering must still be checked because it is
  a shared production path even though it does not currently print authors.

## Execution plan

Status: Draft

Keep compatibility enabled while all child changes land. Run a repository-wide
dependency audit and the complete production build/test suite with migrated
single- and multi-author content. Inspect the generated artifact set and
assert the relevant public output. Record the evidence and approval decision.
Only then make the legacy field rejectable/removable, update the tests and
guidance for that final state, and rerun the same production checks to prove
the cutover did not regress generated pages.

### Implementation decisions and open questions

- The cutover is a separate compatibility state, not an incidental cleanup
  bundled into the first source migration.
- A passing source search is necessary but not sufficient; generated-output
  evidence is mandatory because Eleventy data cascade and template behavior
  can retain dependencies not obvious from migrated front matter.
- If the evidence finds an unresolved dependency, leave compatibility enabled,
  record the dependency, and do not reject the legacy field.

### Documentation

- Record the final compatibility state and migration evidence in the owning
  developer documentation.
- If rejection is not yet safe, document the remaining dependency and keep the
  legacy format described as transitional rather than unsupported.
- Do not rewrite historical generated output by hand; update its maintained
  source and regenerate it through Eleventy.

### Task checklist

- [ ] Keep legacy compatibility active during integrated verification.
- [ ] Audit content, templates, scripts, tests, and documentation for legacy
      dependencies.
- [ ] Run `npm test` and `npm run build` with representative content.
- [ ] Inspect/assert generated post, archive, feed, and sitemap artifacts.
- [ ] Record the evidence and obtain the cutover decision.
- [ ] If approved, enable explicit legacy rejection/removal.
- [ ] Rerun all decisive checks after cutover and update documentation.

### Requirement verification

- Source evidence: repository-wide search plus inspection of every remaining
  match, with no unclassified required legacy dependency.
- Generated evidence: successful production build and assertions over all
  public artifact classes named in the requirements.
- Compatibility evidence: a legacy-shaped fixture passes before cutover;
  after cutover, the canonical fixture passes and the approved legacy failure
  behavior is asserted.
- Preservation evidence: generated route set, archive links/order, post
  content, feed author order, and sitemap URLs remain valid.

### Additional implementation verification

- Run the complete test suite after any rejection change, not only the
  focused author tests.
- Check for stale generated files or documentation that still teaches the
  rejected format.
- Keep the evidence record in this task's completion notes so a later
  maintainer can distinguish “not found” from “not searched.”
