# Define and migrate the structured author source model

Own the canonical post metadata contract, migration of existing front matter,
and the authoring helper that creates new posts.

Parent Task: `tasks/20260926-author-metadata-migration/000-main.md`

Depends On: None

## Requirements checklist

- [ ] R1. The approved structured author form represents one or more authors
  and preserves each author's display name.
- [ ] R2. All existing post front matter is migrated without losing author
  values, post bodies, or route-defining metadata.
- [ ] R4. `scripts/new-post.js` emits only the approved structured form for new
  posts.

## Unresolved requirement questions

- Q1. Confirm whether the canonical author records contain only a required
  `name` or also stable identity/profile fields; do not add fields during
  migration without approval.

## Research and supporting facts

- `content/posts/first.md` and `content/posts/second.md` are the complete
  current content inventory and each has one legacy author string.
- `scripts/new-post.js` is a small exported helper and currently accepts one
  `author` argument, then writes `author: "..."`.
- No schema validator or migration utility currently exists.
- The source migration must leave a compatibility read path available until
  `030-legacy-cutover.md` completes its evidence gate.

## Execution plan

Status: Draft

Use the approved canonical `authors` sequence as the only write format. Each
record must preserve the existing display name exactly; any additional fields
are included only if Q1 approves them. During the transition, expose one
normalization contract that turns a legacy scalar into a singleton sequence
for consumers that still need to read unmigrated content. This child does not
remove that fallback or reject legacy input.

Ordered work:

1. Record the approved author record shape and validation rules in the
   implementation and task evidence.
2. Update the authoring helper API and its tests so generated front matter
   contains the new key and supports one or multiple author records.
3. Migrate every current post, checking that titles, bodies, dates/URLs, tags,
   and author names remain unchanged.
4. Add source-level checks that prevent the helper or migrated fixtures from
   reintroducing the legacy write form.
5. Update the maintained developer documentation with the new authoring
   example, leaving any transition note clearly marked until cutover.

### Implementation decisions and open questions

- Q1 controls whether records contain only `name` or also identity/profile
  fields; do not invent stable identifiers during migration.
- Preserve exact existing name text, including spaces and punctuation.
- Compatibility reading is deliberately deferred to the rendering and final
  cutover boundaries; this child must not make legacy content fail early.

### Documentation

Document the canonical front-matter example and the authoring-helper input in
the existing developer-facing documentation location selected by the parent
task. Do not describe legacy input as current guidance after cutover.

### Task checklist

- [ ] Confirm the approved structured schema.
- [ ] Update and test the authoring helper.
- [ ] Migrate and inspect every existing post.
- [ ] Add source-level regression coverage.
- [ ] Update the maintained metadata/authoring documentation.

### Requirement verification

- R1: The authoring-helper test asserts the exact structured front matter for
  both one and multiple authors; the downstream production build in
  `020-public-rendering.md` confirms Eleventy consumes it.
- R2: A complete content inventory check verifies that each existing post has
  the canonical key and the same author names and body content; the real
  production build verifies the migrated files remain publishable.
- R4: A test invokes `scripts/new-post.js`, parses the returned front matter,
  and asserts that it writes the canonical key and never writes a new legacy
  `author` field.

### Additional implementation verification

- Exercise quoting, punctuation, and multiple records in front matter so the
  migration does not depend on names being plain ASCII or single-word values.
- Confirm no unrelated front-matter keys are rewritten as a side effect.