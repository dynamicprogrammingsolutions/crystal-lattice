# Establish structured author data and migrate authoring inputs

Define the canonical post metadata shape, make new-post authoring emit it,
preserve a temporary compatibility path for existing legacy content, and
migrate the current post corpus without content loss.

## Requirements checklist

- [ ] Define the approved structured value for one or more authors, including
  ordering and validation behavior.
- [ ] Update `scripts/new-post.js` so newly created posts use the canonical
  structured form and can represent the approved one- and multi-author cases.
- [ ] Provide an explicit transition normalization path for legacy single-name
  metadata until the final evidence gate.
- [ ] Migrate every existing post to the canonical form while preserving
  titles, body content, author identity, and author order.

Parent Task: tasks/20260925-author-metadata-migration/000-main.md

## Unresolved requirement questions

- Is the canonical value an ordered list of strings or an ordered list of
  records? Do records require fields beyond `name`?
- What should the authoring function accept for multiple authors: a list,
  repeated arguments, or another input form?
- What validation applies to an empty list, empty name, duplicate name, or
  legacy `author` plus new `authors` supplied together?

## Decisions

- The migration must preserve source content; rewriting bodies or unrelated
  front matter is out of scope.
- Compatibility is temporary and must have a clearly identifiable removal or
  rejection point in the final transition workstream.
- The contract is shared with templates and cannot be finalized independently
  of the approved public rendering semantics.

## Research and supporting facts

- `scripts/new-post.js` currently exposes `frontMatter(title, author)` and
  writes `author: "<name>"`.
- `content/posts/first.md` and `content/posts/second.md` are the complete
  current corpus and each has one legacy author.
- Eleventy reads post front matter directly; the existing repository has no
  author schema module or validation helper.

## Execution plan

Status: Draft

Add the approved structured metadata contract at the narrowest shared input
boundary, then update the post generator and source files to use it. Keep
legacy normalization available while the public templates are being migrated.
Avoid inventing author identity fields that have no current consumer. Make the
conversion mechanical and reviewable so a diff can prove that bodies and
unrelated metadata did not change.

1. Record the approved shape and validation rules in this task and the
   maintained development documentation.
2. Implement the normalization/validation boundary used by production
   rendering, including the temporary legacy fallback and its diagnostics.
3. Update `scripts/new-post.js` and its focused tests for one and multiple
   authors.
4. Convert every existing post to the canonical field and inspect the diff
   for preservation of title, body, and author order.
5. Run the production build as a handoff check for the rendering workstream;
   do not remove the legacy path yet.

### Implementation decisions and open questions

The exact data shape and authoring API remain blocked on the parent task’s
material questions. Once approved, resolve local formatting and helper-module
choices here, but do not change the public contract or rejection timing
without updating the parent plan.

### Documentation

Document the canonical front matter and `new-post.js` input in the maintained
development authoring guidance. During the transition, label compatibility
behavior as transitional rather than presenting the legacy field as current
authoring guidance.

### Task checklist

- [ ] Resolve and record the canonical schema and validation policy.
- [ ] Implement the shared normalization/validation boundary.
- [ ] Update and test the authoring tool.
- [ ] Migrate all existing posts and review the preservation diff.
- [ ] Run a production-build handoff check without retiring legacy support.

### Requirement verification

- Canonical authoring output: call the real exported authoring function for
  one and multiple authors, parse its front matter, and verify the canonical
  structure and ordering.
- Safe corpus migration: compare the migrated post bodies, titles, and
  non-author front matter with their pre-migration values, then run the real
  Eleventy build over all posts.
- Compatibility: build a fixture or retained legacy post through the actual
  Eleventy data path and verify it normalizes to the same structured shape;
  this evidence must not remove the fallback.

### Additional implementation verification

- Verify malformed structured values produce the approved diagnostic rather
  than silently dropping authors.
- Verify the conversion does not alter line endings or content outside the
  author metadata unless the repository’s formatter requires it.