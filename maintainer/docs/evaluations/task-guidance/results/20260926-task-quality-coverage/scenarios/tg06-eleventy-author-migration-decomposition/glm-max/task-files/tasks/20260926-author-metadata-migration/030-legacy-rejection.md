# Reject legacy single-author field after evidence gate

After re-verifying that nothing still depends on the legacy single-name
`author` field, remove the compatibility path and make the legacy form an
error in the build and the authoring tool, ending the migration in a
structured-only state.

Parent Task: tasks/20260926-author-metadata-migration/000-main.md

Depends On:
- tasks/20260926-author-metadata-migration/010-structured-authors-adoption.md
- tasks/20260926-author-metadata-migration/020-content-migration.md

## Requirements checklist

- [ ] Gate (precondition, verified fresh at the start of execution, not
      assumed from earlier stages): content scan shows no legacy `author`
      field; the consumer inventory shows every author consumer (post layout,
      feed, authoring tool) operating on the structured model and archives
      free of legacy dependence; the latest production build and full test
      suite pass. Execution stops if any check fails.
- [ ] Legacy compatibility normalization (deriving structured data from
      `author`) is removed from the data cascade and templates.
- [ ] Content using the legacy field fails the production build with a clear,
      actionable error; no silent fallback or warning-only behavior.
- [ ] `scripts/new-post.js` rejects legacy single-name input and emits only
      the structured form.
- [ ] Existing generated output remains unchanged (the 010-era author
      assertions still pass, now structured-only).
- [ ] Tests updated: legacy-equivalence assertions replaced by structured-only
      assertions plus a rejection assertion exercised through a real build.
- [ ] Documentation updated to the structured-only end state; the legacy form
      is documented as unsupported current behavior.

## Supporting facts

- The gate constraint comes from the original request: the legacy form may be
  rejected only after generated-output and content evidence show that nothing
  still depends on it. Both halves of that evidence exist only after 010
  (generated-output assertions) and 020 (content migrated, scan clean).
- After 020, no content uses `author`; after 010, templates and the tooling
  read the normalized structured form. The remaining legacy dependence is the
  compatibility normalization itself — which is exactly what this stage
  removes.
- The rejection must be proven through the real production build (a legacy
  fixture in a sandboxed copy fails `npm run build`), not through a mocked
  validator, per the repository testing guidance.
- A warning-only acceptance would leave a silent dependency path and would
  not satisfy "rejected"; the recommendation is a hard build failure. This is
  user-visible authoring behavior and is surfaced for approval with the plan.

## Execution plan

Status: Draft

- Gate check first: rerun the content scan, the consumer inventory, and the
  full build/test cycle. Record the evidence before touching compatibility
  code. If the gate fails, stop and report rather than forcing the removal.
- Remove the legacy normalization path from the posts data cascade; templates
  keep reading the normalized structured form only.
- Add build-time validation that fails the build with an actionable error
  when a post carries the legacy `author` field (mechanism: an Eleventy
  data-validation point in the real build path; exact mechanism is an
  implementation choice).
- Update `scripts/new-post.js` to accept only the structured form and reject
  legacy input.
- Update tests: structured-only rendering assertions plus the rejection test
  (sandboxed copy with a legacy fixture; the build must fail). Archive checks
  unchanged.
- Update documentation: structured form only; legacy explicitly unsupported
  as current behavior.
- Full production build and test suite; confirm existing generated output is
  unchanged for the migrated content.

Execution tasks:

1. Fresh gate verification (content scan + consumer inventory + build/tests);
   record evidence.
2. Remove legacy compatibility normalization.
3. Add legacy-field build validation with an actionable error.
4. Restrict `scripts/new-post.js` to the structured form.
5. Update tests (structured-only + rejection through real build).
6. Update documentation to structured-only.
7. Full build + test run; confirm output stability.

### Implementation decisions and open questions

- Rejection mechanism: hard build failure for legacy content plus rejection
  in the authoring tool (recommendation; user-visible — surfaced for
  approval with this plan). A warning-based fallback is not planned because
  it would keep a silent legacy path alive.
- The rejection test uses a temporary legacy fixture in a sandboxed copy; no
  permanent legacy content is added to `content/`.

### Documentation

- Update the authoring/front-matter documentation to structured-only: the
  legacy `author` field is listed as unsupported. Audience: content authors.
  Keep the smallest structure established in stage 1; follow
  `docs/development/documentation.md` for any page moves.

### Task checklist

- [ ] Gate evidence recorded (scan + inventory + passing build/tests)
- [ ] Legacy normalization removed from the data cascade
- [ ] Build validation rejects the legacy field with actionable error
- [ ] `scripts/new-post.js` rejects legacy input
- [ ] Tests: structured-only assertions + real-build rejection test
- [ ] Documentation updated to structured-only
- [ ] Full build + test run clean; output unchanged for existing content

### Requirement verification

- Gate (parent R5): fresh evidence recorded in this stage before any removal —
  content scan clean, consumer inventory, passing production build and tests.
- Rejection end state (parent R6): a production build fails on a sandboxed
  legacy fixture (real build path, not a mocked validator), and the authoring
  tool rejects legacy input.
- Output stability (parent R2/R4): the pinned author assertions from 010 pass
  in structured-only form after the compatibility removal.
- Documentation (parent R7): maintained docs reviewed to describe the
  structured-only supported behavior.

### Additional implementation verification

- Confirm no template, data file, or script reference to the legacy field
  remains (repo-wide search), complementing the build-level rejection.