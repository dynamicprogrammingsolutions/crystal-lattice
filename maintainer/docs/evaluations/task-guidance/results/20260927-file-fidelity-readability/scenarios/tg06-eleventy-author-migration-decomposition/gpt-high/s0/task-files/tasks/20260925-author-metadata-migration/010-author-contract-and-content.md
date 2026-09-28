# Define the author contract and migrate content

Establish the approved structured author metadata, provide transition
compatibility for existing singular-authored posts, and migrate all checked-in
post front matter without changing author identity or order.

Parent Task: tasks/20260925-author-metadata-migration/000-main.md

## Requirements checklist

- [ ] The approved structured multi-author field and record shape are defined.
- [ ] Legacy singular author data can be read during the transition and maps deterministically to one structured author.
- [ ] Every existing post is migrated with the original author name preserved.
- [ ] The migration supports one or more authors in explicit order and does not silently drop values.
- [ ] Focused checks detect missing, malformed, or accidentally regressed source metadata according to the approved contract.

## Unresolved requirement questions

- [ ] Confirm whether the structured value is an array of author records
  (recommended) or an array of strings, and which record fields are required.
- [ ] Confirm validation behavior for empty or malformed author entries.

## Research and supporting facts

- Both checked-in posts currently use `author: "Name"` and are the complete
  known source-content inventory at planning time.
- The post directory data file sets the post layout and `posts` tag but does
  not define an author normalization layer.
- The migration must preserve the existing author names `Ada Example` and
  `Grace Example`.

## Execution plan

Status: Draft

Define the target front-matter contract first, then add the smallest
repository-owned normalization/validation boundary that allows old and new
content to coexist during migration. Convert each existing post to the new
field, retaining author order and values. Add focused checks over the actual
content files so future edits cannot reintroduce the singular form or create
an empty author list. Keep the legacy reader available until the generated
output and content evidence in subtask 040 authorizes its removal.

### Implementation decisions and open questions

- Prefer an ordered `authors` array of `{ name }` records for extensibility,
  pending approval of the public schema.
- Keep source migration mechanical and reviewable: each old scalar maps to a
  one-element structured list with the same visible name.
- Do not invent fallback authors or infer names from filenames.

### Documentation

- Record the approved front-matter example and migration semantics in the
  maintained authoring/development documentation selected by the parent plan.

### Task checklist

- [ ] Resolve the target schema and validation behavior.
- [ ] Implement the temporary compatibility/normalization boundary.
- [ ] Migrate all existing post files.
- [ ] Add focused content-contract checks.
- [ ] Update the parent task checklist and evidence after verification.

### Requirement verification

- Enumerate `content/posts/**/*.md`, parse each front matter block, and assert
  the approved structured field contains the expected ordered author values.
- Exercise one legacy-shaped fixture through the compatibility boundary and
  confirm it produces the same structured value as its migrated equivalent.
- Run the focused content checks after migration; do not rely only on a
  repository text search because that cannot prove the mapping preserves
  values.