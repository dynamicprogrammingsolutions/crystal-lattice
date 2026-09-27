# Migrate the post-authoring helper

Update the post-generation helper so new posts are authored with the
structured multi-author model while the transition contract remains explicit
and testable.

Parent Task: tasks/20260925-author-metadata-migration/000-main.md

Depends On: tasks/20260925-author-metadata-migration/010-author-contract-and-content.md

## Requirements checklist

- [ ] The helper accepts the approved structured author input for one or more authors.
- [ ] Generated front matter uses the new field and preserves author order and values.
- [ ] The helper no longer makes the singular field the normal output path.
- [ ] Helper tests cover single- and multi-author generation and malformed input behavior required by the approved contract.

## Unresolved requirement questions

- [ ] Confirm the helper API: an array of author records, a variadic list, or
  another caller-facing shape.
- [ ] Confirm whether accepting the old scalar helper argument is required
  during the transition or should fail immediately.

## Research and supporting facts

- `scripts/new-post.js` currently exports `frontMatter(title, author)` and
  interpolates the scalar directly into `author`.
- There is no current helper test; the new test must exercise the exported
  function directly and inspect its complete front-matter output.

## Execution plan

Status: Draft

Align the helper's caller-facing input with the approved content contract,
validate the minimum required author data, and serialize it without losing
order or names. Add focused tests for one and multiple authors. If scalar
compatibility is retained temporarily, make it an explicit adapter with a
removal marker rather than allowing it to remain the undocumented default.

### Implementation decisions and open questions

- The helper should share the same serialization rules as checked-in content;
  it must not emit a shape that templates accept only through a special case.
- Do not silently coerce empty names or discard extra authors; validation
  behavior awaits the schema decision.

### Documentation

- Document the helper input and a one/multiple-author example in the
  maintained authoring documentation.
- Clearly mark any scalar compatibility argument as transitional until the
  retirement gate removes it.

### Task checklist

- [ ] Resolve the helper API and scalar compatibility question.
- [ ] Update `scripts/new-post.js`.
- [ ] Add direct helper tests for single and multiple authors.
- [ ] Verify emitted front matter against the content contract.
- [ ] Update the parent task checklist and evidence after verification.

### Requirement verification

- Call the exported helper with approved single- and multi-author inputs and
  parse the resulting front matter.
- Assert the field name, record shape, order, and values match the approved
  contract exactly.
- If scalar compatibility is temporarily supported, test it separately and
  mark the case for removal under subtask 040.