# Establish the structured author contract and migrate source content

Define the canonical post metadata shape, move the authoring helper to that
shape, and migrate existing post front matter while preserving all author
information during the compatibility window.

Parent Task: tasks/20260920-author-metadata-migration/000-main.md

Depends On: None

## Requirements checklist

- [ ] The approved structured multi-author schema is documented as the
  canonical post input contract.
- [ ] `scripts/new-post.js` accepts the approved multi-author input and emits
  valid canonical front matter for one and multiple authors.
- [ ] Every existing post is migrated without losing, duplicating, or
  reordering author data.
- [ ] Legacy source data remains normalizable or otherwise supported at the
  approved transition boundary until the cutover subtask supplies its evidence.

## Unresolved requirement questions and decisions

- The parent task's canonical field name, element shape, and authoring-helper
  API must be resolved before execution; this subtask must not invent them.
- The transition behavior for a legacy scalar is a parent-level compatibility
  decision. If normalization is selected, define whether it produces a
  one-element canonical list and where that normalization occurs.

## Research and supporting facts

- `content/posts/first.md` contains the author value `Ada Example`.
- `content/posts/second.md` contains the author value `Grace Example`.
- `scripts/new-post.js` currently has the signature
  `frontMatter(title, author)` and writes `author: "..."`.
- `content/posts/posts.json` does not define or transform author metadata, so
  the source contract cannot currently be delegated to a collection data
  file.

## Execution plan

Status: Draft

After the parent questions are approved, define the canonical representation
and the compatibility normalization boundary. Update the authoring helper to
produce that representation for one and multiple authors, including safe
quoting/escaping for names. Migrate the two existing post files and any
additional post files discovered by the content inventory. Preserve author
order and compare the old scalar values with the migrated one-author values.

Add focused source-level evidence for the helper output and content inventory,
but leave final acceptance of rendered pages and the legacy rejection to the
dependent subtasks. If the chosen transition strategy needs Eleventy data
normalization or validation, keep that logic at the agreed source/build
boundary and document its lifetime so it can be removed or disabled at
cutover.

### Implementation decisions and open questions

- Keep the migration lossless: existing one-author values become exactly one
  canonical author entry, with no implicit author identity or link creation.
- Resolve any escaping or malformed-input behavior as part of the approved
  front matter contract; do not silently invent fallback authors.
- The compatibility adapter, if used, must be exercised with an actual legacy
  post and must remain available until subtask 030 closes the evidence gate.

### Documentation

Provide the canonical front matter and authoring-helper examples to the
parent's package documentation plan. Do not publish the legacy rejection rule
from this subtask while the output and content evidence is incomplete.

### Task checklist

- [ ] Confirm the approved canonical schema and helper API.
- [ ] Define and implement the transition normalization/validation boundary.
- [ ] Update the authoring helper for one and multiple authors.
- [ ] Inventory and migrate all existing post front matter.
- [ ] Add focused source/content evidence and pass it through the normal
  parsing boundary.
- [ ] Update this subtask with implementation and completion notes after
  execution.

### Requirement verification

- **Canonical source contract:** Parse generated helper output and each
  migrated post through the actual Eleventy input path; assert the canonical
  field and exact author list.
- **Authoring tool:** Exercise one-author and multiple-author calls,
  including names requiring front matter quoting/escaping, and assert valid
  output without relying on a hand-constructed fixture.
- **Lossless migration:** Compare the complete pre-migration author inventory
  with the canonical post inventory, including count and order.
- **Transition support:** Build or parse a real legacy-form fixture at the
  selected compatibility boundary and verify it normalizes to the same data
  as its migrated equivalent.