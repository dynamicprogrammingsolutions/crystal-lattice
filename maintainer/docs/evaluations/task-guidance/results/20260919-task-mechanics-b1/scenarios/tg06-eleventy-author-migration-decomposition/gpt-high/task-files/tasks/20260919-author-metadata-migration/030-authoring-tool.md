# Update the post-authoring helper for structured authors

Move the new-post helper to the canonical multi-author input and prove that
its output is consumable by the same content/build path as hand-authored
posts.

Parent Task: tasks/20260919-author-metadata-migration/000-main.md
Depends On: tasks/20260919-author-metadata-migration/010-schema-and-content-migration.md

## Requirements checklist

- [ ] The helper accepts the approved structured author input, including
      multiple ordered authors.
- [ ] Generated front matter uses the canonical field and valid serialization
      for the repository's parser.
- [ ] The helper no longer requires callers to provide the legacy scalar field
      for new posts.
- [ ] Helper output is verified by parsing/building a representative post,
      not only by comparing a string.
- [ ] Transition guidance makes clear how existing legacy posts and newly
      authored posts differ until cutover.

## Requirement questions and decisions

- Confirm the helper API shape: a list of author objects, a list of display
  names normalized into objects, or another approved interface.
- Confirm whether retaining a compatibility overload for callers of
  `frontMatter(title, author)` is required during the transition. If retained,
  define its warning/deprecation behavior separately from the content parser.

## Supporting facts

- `scripts/new-post.js` currently exports `frontMatter(title, author)` and
  interpolates an unescaped scalar into `author:`.
- There is no existing CLI wrapper or helper test, so the new contract should
  be tested at the exported-function boundary and then through the Eleventy
  build.

## Execution plan

Status: Draft

Define the helper input in terms of the approved canonical model and serialize
it safely as front matter. Add tests for one and multiple authors, including
names that could expose quoting or YAML serialization problems. Feed the
generated front matter into a temporary or test fixture post and run the real
build path so the helper cannot drift from the content parser.

### Implementation decisions and open questions

- Prefer structured serialization over hand-built YAML interpolation so author
  names are quoted/escaped correctly.
- Keep any legacy helper overload only if explicitly required; it must not
  cause newly generated content to write the legacy field.
- Do not make the helper reject legacy input before the integrated cutover
  evidence has established that existing content and callers no longer need
  it.

### Documentation

- Update the authoring instructions with the helper signature and a
  canonical one-/multi-author example.
- Explain the compatibility window and the later evidence-gated legacy
  rejection without claiming that rejection has already happened.

### Task checklist

- [ ] Confirm the helper input contract.
- [ ] Serialize canonical author front matter safely.
- [ ] Add one- and multi-author helper tests.
- [ ] Build a post from helper output through the production path.
- [ ] Update the owning authoring documentation.

### Requirement verification

- Assert helper output parses to the approved canonical structure.
- Build representative generated posts and verify author output matches the
  ordered input.
- Exercise any retained legacy call shape and verify its explicitly approved
  transition behavior.

### Additional implementation verification

- Include names containing punctuation, quotes, or non-ASCII characters in
  serialization coverage where the chosen format requires escaping.
- Confirm helper tests do not bypass the front-matter parser or Eleventy
  rendering boundary.
