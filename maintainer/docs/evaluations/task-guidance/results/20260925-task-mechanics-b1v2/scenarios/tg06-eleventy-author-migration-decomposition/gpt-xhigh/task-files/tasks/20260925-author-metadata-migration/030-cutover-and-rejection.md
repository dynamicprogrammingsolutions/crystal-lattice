# Prove migration completion and reject the legacy author field

Own the ordered evidence gate that permits removal of the legacy read, the
strict rejection behavior, and final documentation/status handoff.

Parent Task: tasks/20260925-author-metadata-migration/000-main.md

Depends On: tasks/20260925-author-metadata-migration/010-metadata-content-tooling.md, tasks/20260925-author-metadata-migration/020-rendering-and-output.md

## Requirements checklist

- [ ] Produce source-content evidence that all supported posts use the
  canonical field and none still depend on legacy `author`.
- [ ] Produce generated-output evidence that the canonical templates, archive
  routes, feed, and post pages work from migrated content.
- [ ] Run the complete relevant test/build gate before enabling strict legacy
  rejection.
- [ ] After the evidence gate passes, reject legacy `author` with an
  actionable failure at the approved enforcement boundary.
- [ ] Leave documentation and task status consistent with the final supported
  contract.

## Unresolved requirement questions and decisions

- Confirm whether strict rejection applies only to production content
  validation or also to direct calls to the authoring helper. Recommendation:
  both production input and newly authored output should be canonical, while
  only the production input needs a hard failure for a legacy field.
- Confirm whether intentional migration diagnostics/tests may retain the
  literal legacy key. If allowed, the final audit must scope references by
  dependency rather than require a misleading zero-text search.

## Supporting facts and boundary

The current repository has no strict metadata validator and its author-output
tests are placeholders. Therefore “nothing depends on legacy” cannot be
claimed from the current test suite; it requires a source scan plus a real
build and output assertions from subtask 020, followed by the rejection
behavior itself.

## Execution plan

Status: Draft

Run the cutover in an explicit order:

1. Confirm subtask 010 has migrated all committed post sources and has
   transition coverage.
2. Run subtask 020's real production build and inspect the route set and
   generated author output.
3. Scan production templates, configuration, scripts, tests, and content for
   executable legacy reads or writes, classifying any intentional migration
   documentation/fixture references separately.
4. Record the evidence and only then switch the canonical data boundary to
   reject a post containing the legacy field, with a file-specific error.
5. Re-run the complete test/build gate from the strict mode and verify that a
   deliberately legacy-shaped input fails for the intended reason without
   weakening the migrated production path.

The rejection change is a separate final step in the implementation history,
so reviewers can verify that it was not enabled before content and generated
output were clean.

### Implementation decisions and open questions

- No strict rejection is allowed while committed posts or production
  templates/scripts still require the legacy field.
- The pre-rejection evidence must be recorded in test output or an equivalent
  reviewable check, not inferred from a successful unit test.
- Keep migration-only diagnostics explicit and non-production; do not leave a
  hidden compatibility fallback after strict mode.
- If the evidence finds a remaining dependency, stop the cutover, return to
  the relevant subtask, and leave legacy acceptance in place.

### Documentation

Update the maintained documentation to state the canonical field and the
strict rejection behavior after it is true. If a migration note is retained,
mark the transition as historical/currently supported accurately; do not
describe the legacy field as supported after the gate.

### Task checklist

- [ ] Receive source migration evidence from subtask 010.
- [ ] Receive production-output evidence from subtask 020.
- [ ] Complete and record the dependency scan.
- [ ] Obtain the evidence-gate review/approval.
- [ ] Enable strict rejection only after approval.
- [ ] Add strict-mode regression coverage and rerun the complete build/test
  gate.
- [ ] Update parent requirement status and document any deferred scope.

### Requirement verification

- Source independence: a scoped scan of `content/`, templates, config, and
  authoring code shows no executable legacy read/write remaining after
  migration; any intentional test/documentation mention is classified.
- Generated-output independence: the production build produces all expected
  routes and canonical author output before strict mode is enabled.
- Conditional rejection: the strict-mode test proves a legacy-only input
  fails with an actionable message, while the migrated repository passes the
  same complete build/test invocation.
- Final contract: inspect the maintained documentation and task evidence
  together so the documented supported form matches the enforced form.

### Additional implementation verification

- Run from a clean checkout or equivalent clean source copy to avoid stale
  `_site` files masking missing output.
- Verify the strict failure identifies the offending post and field.
- Confirm no generated output or migration scratch artifact is accidentally
  added to version control.