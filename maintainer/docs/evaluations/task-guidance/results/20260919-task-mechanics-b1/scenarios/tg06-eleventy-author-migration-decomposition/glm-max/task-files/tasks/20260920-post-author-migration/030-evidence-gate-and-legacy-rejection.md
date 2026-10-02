# Evidence gate, legacy rejection, and compatibility cleanup

Final migration state: verify nothing still depends on the legacy single-name
`author` form, then reject it at build time, remove the legacy read path, and
document the rejection — in that order, with the gate evidence recorded
before any rejection change lands.

Parent Task: tasks/20260920-post-author-migration/000-main.md
Depends On: tasks/20260920-post-author-migration/010-multi-author-model-and-compat.md
Depends On: tasks/20260920-post-author-migration/020-content-and-tooling-migration.md

## Requirements checklist

- [ ] Pre-rejection evidence is recorded and fully green before any rejection
      change: (a) content audit shows zero legacy `author` keys in `content/`
      (from 020), (b) the full generated-output suite passes rendering from
      the new model, (c) the authoring tool emits only the new form.
- [ ] Only after that evidence: the production build fails when a post's
      front matter carries the legacy `author` key, with a clear error
      message.
- [ ] The legacy normalization/fallback read path is removed in the same
      change as rejection; templates and the posts data file read only the
      new model.
- [ ] After rejection lands, the full generated-output suite and archive
      tests still pass, and an integration test proves a legacy-form fixture
      fails the real build while the real content builds cleanly.
- [ ] Documentation states the legacy form is rejected, updated in the same
      reviewed change that enables rejection.

## Supporting facts

- The rejection gate ("legacy may be rejected only after generated-output and
  content evidence") is a requirement from the original request, not a
  preference. Gate inputs: 020's recorded content audit, the 010-generated
  generated-output suite, and the 020 tooling tests.
- After 020, legacy support exists only as the normalization fallback added
  in 010 (`content/posts/posts.json` computed data or the shared filter) plus
  its acceptance in front matter.
- Rejection and fallback removal must land together: rejecting the form while
  keeping the fallback would leave dead code that still reads `author`.
- `npm test` runs `node --test tests/*.test.js`; the build helper from 010
  supports building an alternate input directory into a temp output — reused
  for the legacy-failure integration test.

## Execution plan

Status: Draft

Approach:

1. Gate check (blocking, recorded in this file before proceeding):
   - Content audit: search all of `content/` for legacy `author` keys —
     expect zero. (Reuse/verify the 020 audit; re-run it here rather than
     trusting a stale record.)
   - Run the full generated-output suite — expect green, rendering from the
     new model.
   - Confirm the authoring tool emits only the new form (020 unit tests).
   If any check fails, stop and report; do not enable rejection.
2. Implement build-time rejection: validate post front matter in
   `eleventy.config.js` (choose the Eleventy 3 hook during execution —
   e.g., a data preprocessor or collection/data check) so that any post
   carrying the legacy `author` key fails the build with a clear message.
   Export the validation predicate so it is unit-testable without bypassing
   the wired behavior.
3. Integration test at the real boundary: using the build helper, build a
   temp copy of the real site plus one legacy-form fixture post and assert
   the build fails with the rejection error; assert the real content (no
   legacy keys) still builds cleanly.
4. Remove the legacy normalization fallback (010's legacy branch), leaving
   the new model as the only read path. Re-run the full suite — the
   exact-string baseline tests must still pass, proving generated output is
   carried by the new model alone.
5. Documentation (same change): update the README "Adding posts" section to
   state that the legacy `author` form is no longer accepted and the build
   fails on it — true in the same reviewed change.
6. Final verification: full `npm test` green; `npm run build` green; record
   all results and complete the parent requirement checkboxes.

Boundaries: rejection and failure-path evidence come from the real Eleventy
build (temp-copy fixture), not from invoking the validator in isolation.

### Implementation decisions and open questions

- Local: exact Eleventy 3 hook for build-time validation (chosen during
  execution; exported predicate keeps it unit-testable); rejection triggers
  on presence of the legacy `author` key in post front matter regardless of
  value.
- No open requirement questions remain from the parent at this stage (Q1/Q2
  resolved before 010 executed).

### Documentation

- README "Adding posts" section is updated in the same reviewed change that
  enables rejection, per `docs/development/documentation.md` (claim becomes
  true in the same change that publishes it).

### Task checklist

- [ ] Run and record the three-part gate check (audit, suite, tooling) before
      any rejection change.
- [ ] Implement build-time rejection in `eleventy.config.js` with exported,
      unit-testable validation predicate.
- [ ] Add legacy-failure integration test (temp copy + fixture post; real
      build must fail; real content must pass).
- [ ] Remove legacy normalization fallback; re-run full suite.
- [ ] Update README to state legacy rejection (same change).
- [ ] Full suite + production build green; update requirement checkboxes in
      this file and the parent.

### Requirement verification

- Gate evidence before rejection → decisive: the recorded gate checklist in
  this file, completed and green before step 2 begins.
- Build rejects legacy form → decisive: integration test where a legacy
  fixture fails the real build and real content passes.
- Legacy read path removed → decisive: full generated-output suite green
  after removal, plus source audit showing no template/data-file reads of the
  legacy key.
- Documentation current → decisive: README rejection statement present in the
  same change enabling rejection (inspection of the merged state).

### Additional implementation verification

- Confirm the rejection error names the offending file/content so a content
  author can fix it without reading build internals.
- Confirm the rejection check cannot be skipped by the front-matter parser
  treating `author` as data in an unexpected shape (e.g., list value) —
  presence of the key is what triggers rejection.