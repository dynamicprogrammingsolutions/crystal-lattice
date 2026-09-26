# Define and migrate the post author metadata contract

Own the canonical structured author field, its temporary compatibility
normalization, safe conversion of existing posts, and the authoring helper that
creates new posts.

Parent Task: tasks/20260925-author-metadata-migration/000-main.md

## Requirements checklist

- [ ] Implement the approved canonical structured multi-author front matter
  shape and a single normalization boundary for consumers.
- [ ] Continue accepting the legacy scalar `author` during the approved
  transition window, with deterministic conversion to the canonical value.
- [ ] Convert every existing post to the canonical field without changing
  title, body, route-affecting metadata, or unrelated front matter.
- [ ] Make `scripts/new-post.js` generate the canonical field and support the
  approved multi-author input.
- [ ] Provide evidence that the migration is complete and repeatable before
  the legacy form is rejected.

## Unresolved requirement questions and decisions

- Use the schema approved by the parent task; do not choose a public field
  shape here. The working recommendation is `authors` as an ordered array of
  records with a required `name`.
- Confirm whether stable author IDs, profile URLs, or other fields are part of
  this migration. If not approved, keep them out of the required contract.
- Confirm whether the authoring helper's existing function signature must remain
  source-compatible for callers during the transition or may change at the
  same time as its emitted front matter.

## Supporting facts and boundary

The only committed post sources are under `content/posts/`, and both currently
use `author: "..."`. The helper currently accepts one author argument and
returns serialized front matter. There is no existing validator or migration
command, so the implementation must make the conversion and its failure
reporting explicit rather than relying on a blind text replacement.

## Execution plan

Status: Draft

Define one canonical normalization function or data boundary that returns an
ordered collection of author records. In transition mode it reads the legacy
scalar only when the canonical field is absent; it reports ambiguous inputs
such as both fields being present or malformed author data. The post templates
and feed will consume only this normalized result.

Add a narrow migration path for committed Markdown sources. Before writing,
inventory all post files and capture stable fields needed to prove safety.
Rewrite only the front matter author representation, preserve Markdown bodies
byte-for-byte where practical, and fail or report unexpected front matter
instead of guessing. Make the operation idempotent so a second run produces no
additional changes.

Update the authoring helper to emit the canonical field and exercise it with
one-author and multi-author inputs. Preserve a compatibility API only if the
approved transition contract requires it; regardless of API compatibility, new
output must not introduce `author`.

### Implementation decisions and open questions

- The migration must not remove the compatibility read until the parent
  cutover evidence is complete.
- The canonical field is the only value exposed to rendering consumers; do not
  duplicate old/new branching across templates or scripts.
- Migration errors must identify the source file and reason, and must leave
  unrecognized files unchanged.
- Do not treat a source-code reference to the word `author` in migration
  diagnostics or documentation as a remaining data dependency; the cutover
  audit must distinguish intentional references from legacy reads.

### Documentation

Update the authoring section of `README.md` with the approved front matter
example and helper usage. If the transition requires contributor-facing
migration instructions, record them in the smallest existing development
documentation location after the contract is approved.

### Task checklist

- [ ] Record the approved canonical schema from the parent decision.
- [ ] Add transition normalization and malformed/mixed-input coverage.
- [ ] Add the content migration and safety/idempotence checks.
- [ ] Update and test the authoring helper.
- [ ] Inventory and migrate all committed posts.
- [ ] Report the source-evidence result to the parent before cutover.

### Requirement verification

- Canonical model and compatibility: run the metadata tests against one
  canonical post, one legacy post, a multi-author post, and invalid/mixed
  inputs; then consume the normalized data through the real Eleventy build
  before strict rejection.
- Safe existing-post migration: inspect every file under `content/posts/`,
  assert canonical author metadata is present, assert no legacy front matter
  remains, and compare title/body/unrelated metadata with the pre-migration
  inventory.
- Authoring tool: invoke the exported helper with one and multiple authors and
  parse its output as front matter, proving that new posts use the canonical
  field.

### Additional implementation verification

- Run the migration twice and verify the second run is a no-op.
- Check quoting, escaping, and author order for names containing YAML-sensitive
  characters.
- Confirm a malformed source is reported without partially rewriting other
  posts.