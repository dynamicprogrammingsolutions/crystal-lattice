# Migrate post content and the authoring tool

Convert checked-in post metadata and the post-generation helper to the
approved structured author model while preserving post content and providing
safe transition behavior.

Parent Task: tasks/20260919-author-metadata-migration/000-main.md
Depends On: tasks/20260919-author-metadata-migration/010-author-contract-and-transition.md

## Requirements checklist

- [ ] Convert every existing post to the approved structured author field
      without changing title, body, URL, ordering, or unrelated front matter.
- [ ] Update `scripts/new-post.js` to emit the approved representation for
      one or more authors.
- [ ] Define and test the authoring helper's transition behavior for the
      legacy call shape, if it remains supported during the deprecation
      window.
- [ ] Serialize author names safely, including names that require quoting or
      escaping in front matter.
- [ ] Leave production content with no unclassified legacy scalar field before
      the retirement evidence is evaluated.

## Supporting facts

- `content/posts/first.md` and `content/posts/second.md` are the complete
  checked-in post set observed during planning and each currently has one
  scalar author.
- `scripts/new-post.js` currently accepts `(title, author)` and interpolates
  both values directly into YAML, so names requiring quoting are not covered
  by executable tests.
- The package's test script runs Node's test runner over `tests/*.test.js`;
  current author tests are placeholders.

## Execution plan

Status: Draft

After subtask 010's contract is approved, migrate each production post
mechanically while checking the resulting front matter and preserving all
non-author content. Include a representative multi-author case in the
production-boundary coverage without inventing unrelated post metadata or
changing routes.

Change the authoring helper to accept the approved structured input and emit
valid, safely quoted front matter. If the old call shape is retained for the
transition, route it through the same normalizer and mark it as a deliberate
compatibility path so it can be inventoried and retired later. Add tests for
single-author, multiple ordered authors, and special characters.

### Implementation decisions and open questions

- The exact function signature depends on the approved collection shape and
  the unresolved external-consumer question in the parent task.
- Whether a checked-in sample post becomes multi-author or a realistic build
  fixture supplies that case must preserve the repository's production path;
  test-only shortcuts that bypass Eleventy are not acceptable evidence.
- Do not remove the old helper call shape here if subtask 010 or the parent
  task still requires a transition window.

### Documentation

The final authoring input example belongs in the maintained developer
guidance handled by subtask 050. This subtask should only add comments or
test descriptions needed to explain executable behavior.

### Task checklist

- [ ] Confirm the approved schema and authoring API.
- [ ] Migrate all checked-in post front matter and inspect the diff for
      non-author changes.
- [ ] Update the authoring helper and its transition behavior.
- [ ] Add safe-serialization coverage for single, multiple, ordered, and
      special-character names.
- [ ] Produce a content inventory for subtask 040, distinguishing intentional
      compatibility fixtures from production content.

### Requirement verification

- A front-matter/content diff or parser check proves every existing post has
  the approved field and retains its title, body, URL, ordering, and other
  metadata.
- Authoring-helper tests prove valid output for one and multiple authors and
  names containing YAML-sensitive characters.
- A real generated post from the helper reaches the Eleventy build path and
  renders correctly; a serialization-only assertion is not sufficient.
- A production-content scan reports no unclassified legacy `author` field
  before subtask 040's retirement gate.