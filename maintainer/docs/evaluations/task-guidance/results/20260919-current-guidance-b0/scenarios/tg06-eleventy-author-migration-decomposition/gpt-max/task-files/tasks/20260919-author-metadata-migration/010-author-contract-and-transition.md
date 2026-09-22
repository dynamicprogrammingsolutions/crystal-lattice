# Establish the author metadata contract and transition boundary

Define the structured multi-author data contract and the compatibility boundary
that lets old and new post metadata coexist while the repository is migrated.

Parent Task: tasks/20260919-author-metadata-migration/000-main.md

## Requirements checklist

- [ ] Record the approved structured author collection, required fields,
      cardinality, ordering, and display semantics.
- [ ] Define one canonical normalized value for templates and output
      generators.
- [ ] Accept the legacy scalar `author` form during transition without
      changing its rendered name or breaking old content.
- [ ] Define deterministic behavior for new-only, legacy-only, both-field, and
      malformed metadata before strict rejection is considered.
- [ ] Keep the compatibility path isolated so the rest of the site does not
      read the legacy field directly.

## Supporting facts

- The only current content examples are scalar names in
  `content/posts/first.md` and `content/posts/second.md`.
- There is no existing data normalization in `eleventy.config.js` or
  `content/posts/posts.json`.
- The post layout and feed currently read legacy data independently, which
  makes a shared boundary necessary for consistent output.

## Execution plan

Status: Draft

Resolve the open contract questions in the parent task before implementation.
Choose the smallest structured representation that supports one or more
ordered authors and the approved output contract. Define the normalized
record/list shape that all templates will receive, including how names are
escaped and displayed.

Implement the compatibility behavior at one owned boundary in the Eleventy
data/configuration path. It should translate legacy scalar input into the
normalized collection during transition, without requiring each template to
know about both forms. Add focused evidence for precedence and invalid-input
behavior, but defer removal of the legacy branch to subtask 050.

### Implementation decisions and open questions

- The target record shape and mixed-field policy are intentionally unresolved
  until the parent task questions are answered.
- Do not add optional identity/profile fields merely because a record shape
  could hold them; they are outside the requested migration.
- The compatibility boundary must be usable by both page templates and feed
  generation, not just by the post layout.

### Documentation

Record the approved contract in the parent task's implementation notes during
execution. Do not update current user guidance from this Draft subtask.

### Task checklist

- [ ] Obtain approval for the structured collection and rendering contract.
- [ ] Define new-only, legacy-only, both-field, and malformed-input behavior.
- [ ] Implement one normalization/compatibility owner after execution is
      approved.
- [ ] Add focused contract evidence consumed by subtask 040.
- [ ] Update the parent task with the decided contract and any deviations.

### Requirement verification

- Contract evidence demonstrates the normalized collection for one and
  multiple authors, including source ordering.
- A real Eleventy build using legacy metadata demonstrates that transition
  compatibility preserves the existing author name.
- A mixed/malformed metadata test demonstrates the approved deterministic
  behavior without silently selecting an undocumented value.
- A source scan confirms that legacy branching is confined to the owned
  compatibility boundary and its intentional tests.