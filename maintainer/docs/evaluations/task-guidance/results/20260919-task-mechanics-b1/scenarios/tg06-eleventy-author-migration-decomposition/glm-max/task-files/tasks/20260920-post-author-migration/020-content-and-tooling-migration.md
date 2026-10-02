# Migrate existing posts and authoring tool to the new author model

Second migration state: move all source content and the authoring tool to the
structured `authors` form while legacy is still accepted, with generated
output for the existing posts unchanged, and document the new authoring form
for content authors.

Parent Task: tasks/20260920-post-author-migration/000-main.md
Depends On: tasks/20260920-post-author-migration/010-multi-author-model-and-compat.md

## Requirements checklist

- [ ] All source posts declare authors with the new `authors` form (shape per
      parent Q1); no post front matter carries the legacy `author` key.
- [ ] `scripts/new-post.js` emits the new form and supports multiple authors;
      its behavior is unit-tested.
- [ ] Generated output for the two migrated posts is unchanged after
      migration (equivalence evidence at the production-build boundary).
- [ ] Maintained documentation describes the `authors` front-matter form for
      content authors, updated in the same reviewed change that migrates the
      content.

## Supporting facts

- Only two posts exist: `content/posts/first.md` (`Ada Example`),
  `content/posts/second.md` (`Grace Example`).
- `scripts/new-post.js` exports `frontMatter(title, author)` returning
  legacy-form front matter; nothing invokes it from `package.json` scripts.
- After subtask 010, the generated-output suite (author + archive tests plus
  temp-fixture coverage) exists and is green; legacy content still builds via
  normalization.
- The content audit performed here (zero legacy `author` keys in `content/`)
  is a required input to subtask 030's rejection gate — record it, do not
  just observe it.

## Execution plan

Status: Draft

Approach:

1. Migrate `content/posts/first.md` and `content/posts/second.md` to the new
   `authors` form (each becomes a one-element list per Q1 shape). No other
   front-matter changes.
2. Update `scripts/new-post.js`: `frontMatter(title, authors)` accepts an
   ordered list of author names and emits the new form with correct YAML
   quoting; keep it dependency-free. Unit test: single author, multiple
   authors, and emitted front matter matches the form documented for content
   authors.
3. Equivalence evidence: run the full generated-output suite — the exact
   author strings asserted by the 010 baseline tests must pass unchanged
   after the content migration, proving no output regression.
4. Documentation (same change): add a short "Adding posts" section to
   `README.md` documenting the `authors` front-matter field with an example.
   At this state legacy `author` is still accepted, so the section describes
   the new form as the supported way to author posts without claiming legacy
   is rejected.
5. Content audit: confirm `content/` contains no legacy `author` keys
   (search for the singular key) and record the result — this is gate
   evidence for 030.
6. Verify: full `npm test` green; production build green; record results.

### Implementation decisions and open questions

- Open (parent): Q1 field shape determines the emitted front matter in both
  content and the tool.
- Local: tool signature takes an ordered author-name list; documentation home
  is a README section per the parent's documentation decision.

### Documentation

- README gains the "Adding posts" section in the same change as the content
  migration, per `docs/development/documentation.md` (claims describe current
  behavior; legacy is still accepted at this state, so the section must not
  claim it is rejected).

### Task checklist

- [ ] Migrate both posts' front matter to the new form.
- [ ] Update `scripts/new-post.js` for the new form (multi-author); add unit
      tests.
- [ ] Run generated-output suite; confirm exact-string equivalence.
- [ ] Add README "Adding posts" section documenting `authors`.
- [ ] Run content audit; record zero legacy keys as gate evidence for 030.
- [ ] Full suite + production build green; update requirement checkboxes.

### Requirement verification

- Content migrated → decisive: content audit shows zero legacy `author` keys
  in `content/posts/` (recorded).
- Tool emits new form → decisive: unit tests covering single and multiple
  authors against the documented form.
- Output equivalence → decisive: exact-string generated-output tests pass
  unchanged post-migration.
- Documentation current → decisive: README section present in the same change
  (inspection of the merged state).

### Additional implementation verification

- Confirm the audit search covers all of `content/`, not just `posts/`, so
  the 030 gate evidence is complete.