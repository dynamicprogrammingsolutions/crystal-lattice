# Update the authoring helper and developer guidance

Move new-post creation to the structured author contract and explain the
supported transition behavior to maintainers.

Parent Task: tasks/20260919-author-metadata-migration/000-main.md

Depends On: tasks/20260919-author-metadata-migration/010-contract-and-inventory.md

## Requirements checklist

- [ ] Make `scripts/new-post.js` produce the approved structured author
  front matter.
- [ ] Define and test how the helper accepts one and multiple authors.
- [ ] Ensure generated front matter is safely quoted/serialized for supported
  author values.
- [ ] Document the current authoring contract and the temporary legacy policy
  in the owning developer documentation.

## Open requirement questions and material decisions

- Decide whether the helper takes an array, variadic names, or author records;
  this must match the approved schema rather than preserving an accidental
  JavaScript API.
- Decide whether a legacy scalar argument is accepted temporarily, normalized,
  warned about, or rejected only at final cutover.

## Supporting facts

The helper currently exports `frontMatter(title, author)` and interpolates both
values directly into YAML. It has no discovered executable tests, so the
updated contract needs direct tests plus a build-level consumer.

## Execution plan

Status: Draft

Change the helper’s input contract to the approved structured representation,
serialize it safely, and add focused tests for one and multiple authors and
special characters. If transition compatibility is approved for callers,
normalize it at the helper boundary and mark the legacy path for removal;
otherwise make the contract change explicit in the guidance. Verify output by
feeding generated front matter into the real site build.

### Implementation decisions and open questions

The public helper API is a material interface decision. Do not preserve or
reject legacy arguments until the parent task resolves the transition policy.
Avoid adding a second authoring abstraction when the helper can directly emit
the approved front matter.

### Documentation

Update `docs/development/index.md` or a focused development page only if it
has a meaningful authoring audience. Include the field example, helper
invocation shape, transition status, and final legacy-rejection condition.
Update README content only if it currently serves that audience.

### Task checklist

- [ ] Implement and test the approved helper input/output contract.
- [ ] Verify safe YAML serialization for supported author values.
- [ ] Verify generated front matter builds successfully.
- [ ] Update maintained developer guidance with current behavior.

### Requirement verification

- Direct helper tests prove one- and multi-author output matches the approved
  front-matter contract.
- A real Eleventy build consumes helper-produced front matter successfully.
- Documentation matches the verified supported behavior and labels any
  transition-only behavior accurately.

### Additional implementation verification

- Test names that would break unquoted YAML or HTML/XML output.
- Confirm no documentation presents the legacy field as current guidance after
  cutover.