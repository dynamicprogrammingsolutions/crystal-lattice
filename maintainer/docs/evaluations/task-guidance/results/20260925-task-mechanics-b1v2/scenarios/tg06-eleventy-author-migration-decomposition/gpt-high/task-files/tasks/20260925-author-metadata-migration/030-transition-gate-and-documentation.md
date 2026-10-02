# Close the compatibility transition and document the supported contract

Use source-content and generated-output evidence to decide when the legacy
single-name field can be retired or rejected, then update maintained
authoring guidance to match the completed migration.

## Requirements checklist

- [ ] Run the complete production build and relevant test suite against the
  migrated corpus and structured authoring path.
- [ ] Produce source-content evidence that no post still depends on the
  legacy single-name field.
- [ ] Produce consumer evidence that templates, feed generation, authoring
  tools, and tests no longer depend on the legacy form.
- [ ] Retire or reject the legacy form only after both generated-output and
  content/consumer evidence pass.
- [ ] Make the post-gate behavior explicit and diagnosable if a legacy field is
  encountered.
- [ ] Update maintained developer/authoring documentation to describe the
  canonical form and final compatibility state.

Parent Task: tasks/20260925-author-metadata-migration/000-main.md
Depends On: tasks/20260925-author-metadata-migration/010-data-contract-and-authoring.md
Depends On: tasks/20260925-author-metadata-migration/020-public-rendering-surfaces.md

## Unresolved requirement questions

- Is the approved end state strict rejection of `author`, or continued
  acceptance with a deprecation warning? The user permits rejection after
  evidence but does not require it.
- If strict rejection is chosen, should failure happen during front matter
  normalization, Eleventy build evaluation, or a dedicated content check?
- Which generated artifacts are the minimum evidence set for archive, tag,
  post, and feed coverage if the build output contains additional pages?

## Decisions

- No legacy rejection may be enabled before the evidence gate passes.
- Evidence must cross the production path: source content and consumers are
  scanned, then Eleventy builds the site and generated artifacts are checked.
- A passing mock or template unit test cannot substitute for generated-output
  evidence.
- Documentation must describe current supported behavior after completion; any
  pre-completion target text must be visibly marked as not implemented.

## Research and supporting facts

- The current build writes to `_site`; `npm run build` is the repository’s
  production build command.
- The repository’s test command is `npm test`, but the author-output test is
  currently only a placeholder comment and must become executable evidence.
- Existing author consumers are discoverable in the post layout, feed
  template, shared post list, authoring script, post front matter, and tests.
- `docs/development/index.md` is the existing maintained development
  documentation location.

## Execution plan

Status: Draft

Treat compatibility closure as a gated release step. First establish a
baseline inventory of legacy references, then run the completed structured
path and inspect generated output. Only when migrated source content and all
supported consumers are clear should the implementation remove or reject the
legacy form. The final documentation update must be made in the same reviewed
change as the behavior it describes.

1. Resolve the approved post-gate policy and failure location.
2. Run `npm test` and `npm run build` with the migrated corpus, ensuring the
   tests collect and exit successfully.
3. Inspect generated post, home, blog archive, tag, feed, and metadata output
   for author completeness, ordering, escaping, and absence of legacy values.
4. Search source content, templates, scripts, configuration, and tests for
   legacy `author` dependencies; classify any remaining occurrence as an
   intentional compatibility check, documentation history, or a defect.
5. After the generated-output and content/consumer evidence passes, remove the
   fallback or enable the approved clear rejection behavior.
6. Re-run the build, tests, and legacy scan after closure, then update
   `docs/development/index.md` with the current supported contract and
   transition state.

### Implementation decisions and open questions

The strict-rejection versus deprecation choice and its failure boundary are
material and require approval. The recommended end state is explicit
build-time rejection with a message naming the replacement field, because it
prevents silent reintroduction of the legacy form; retain deprecation instead
if compatibility with external unpublished content is a requirement. This
recommendation does not authorize either behavior.

### Documentation

Update `docs/development/index.md` with the canonical metadata example,
authoring-tool usage, supported one/multiple-author cases, migration
compatibility status, and the final legacy-field policy. Keep the guidance
short and developer-facing; do not create a placeholder documentation tree.

### Task checklist

- [ ] Resolve the final legacy policy and failure boundary.
- [ ] Run baseline and post-migration production/test evidence.
- [ ] Complete source-content and consumer scans.
- [ ] Retire or reject the legacy form after the evidence gate.
- [ ] Re-run all decisive checks after closure.
- [ ] Update maintained documentation and reconcile parent requirement status.

### Requirement verification

- Generated-output evidence: `npm run build` followed by assertions over the
  generated post, archive, tag, and feed artifacts proves the public path.
- Content evidence: a repository scan proves every existing post uses the
  canonical field and identifies every remaining legacy token.
- Consumer evidence: a scan plus executable tests proves no template, authoring
  tool, or maintained test still reads or emits the legacy field except for
  explicitly approved rejection/compatibility coverage.
- Rejection timing: the final diff and test order show that legacy rejection
  was enabled only after the preceding build and scans passed; a legacy fixture
  then demonstrates the approved diagnostic.
- Documentation: inspect the final development guidance against the shipped
  behavior and schema.

### Additional implementation verification

- Run a clean build after removing or rejecting compatibility to catch hidden
  data-path assumptions.
- Verify that generated output does not contain stale files from a prior
  build when evaluating the evidence gate; clean or otherwise control the
  output directory as part of the documented check.
- Confirm the final error path points authors to the canonical structured
  field without accepting both fields ambiguously.