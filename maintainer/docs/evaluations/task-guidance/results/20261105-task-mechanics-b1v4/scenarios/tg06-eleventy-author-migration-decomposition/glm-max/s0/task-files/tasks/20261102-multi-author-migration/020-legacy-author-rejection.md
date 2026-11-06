# Legacy author rejection

Parent Task: tasks/20261102-multi-author-migration/000-main.md

Depends On: tasks/20261102-multi-author-migration/010-structured-author-adoption.md

Flip the compatibility state after 010's evidence is re-confirmed: stop
accepting the legacy `author` form, remove the transition normalization, and
verify both the rejection and that the migrated site's output is unchanged.

## Requirements checklist

- [ ] The gate is honored: the flip is executed only after re-confirming
  (a) content evidence — zero legacy `author:` occurrences under `content/` —
  and (b) generated-output evidence — 010's build comparison against the
  baseline still holds; the evidence is recorded before the flip.
- [ ] The transition normalization is removed: no template, script, data
  file, or test maps or reads the legacy `author` field anywhere.
- [ ] Legacy-form input is rejected per the approved mechanism (main task
  recommendation: production build fails with an error naming the offending
  file), verified by building a temporary legacy-form fixture and asserting
  the approved observable outcome.
- [ ] The migrated production content still builds and every existing page's
  output remains identical to the baseline recorded in 010.
- [ ] Documentation no longer presents the legacy form as supported and
  states the rejection behavior where it is user-visible.

## Implementation plan

Status: Draft

Design: replace the accessor's legacy fallback (010's `eleventyComputed.authors`
derivation, or the equivalent filter) with the approved rejection behavior, in
one coherent change together with the test and documentation updates. After
this subtask, page data contains only structured `authors`, and supplying
legacy `author:` produces the approved outcome instead of silent tolerance.

Order and rationale:

1. Re-confirm the gate (read-only checkpoint; record dated evidence in
   Implementation notes): content scan — zero legacy `author:` under
   `content/`; `npm test` on the migrated site passes; spot-check 010's
   baseline comparison expectations still describe current output. If anything
   still depends on the legacy form, stop and report — do not reject.
2. Flip: remove the normalization fallback, implement the approved rejection,
   retire 010's legacy-equivalence fixture test (it would fail by design) and
   replace it with the rejection test, update documentation — all in one
   change so no intermediate state claims the wrong contract.
3. Verify: production build over migrated content compared against 010's
   baseline must be identical; production build of a legacy-form fixture must
   produce the approved outcome (nonzero exit and error naming the file, or
   the alternative if that is what was approved); `npm test` collects and
   passes everything. If the comparison fails, revert the flip and report the
   dependency that surfaced — the gate did its job.

Stop-safe: step 1 is read-only. Steps 2–3 are a single reversible change;
reverting restores 010's tolerated state.

Risks: a consumer outside the repository or added later regresses (assumption:
the repository is the complete scope — no external consumers identified during
planning); removing the accessor subtly changes data shape (mitigated by the
full-output comparison). Way back: revert the single change; legacy tolerance
returns.

### Implementation decisions and open questions

- The rejection mechanism is the main task's pending material decision; this
  subtask executes whichever mechanism is approved (recommendation recorded
  there: loud build error naming the file).
- Adopted locally: the rejection test runs through the production build on a
  temporary fixture — the real path, not a unit-level shim.
- Open questions: none local.

### Documentation

- Same change as the flip: wherever 010 documented the author model, state
  that the legacy single-name form is no longer accepted and describe what
  happens when it is supplied. Audience unchanged: content authors and
  maintainers of this fixture.

### Task checklist

- [ ] Re-confirm gate evidence (content scan, test run, baseline comparison
  currency) and record it before the flip.
- [ ] Remove the normalization fallback; implement the approved rejection.
- [ ] Replace 010's legacy-equivalence test with the rejection-evidence test.
- [ ] Build migrated content; confirm output identical to baseline.
- [ ] Build the legacy fixture; confirm the approved observable outcome.
- [ ] Update documentation; `npm test` collects and passes everything.

### Requirement verification

- Gate honored: dated Implementation-notes record of the step-1 evidence,
  written before the flip — decisive for ordering.
- Normalization removed: repo scan — no code path reads or maps the legacy
  field.
- Rejection works: production build of the legacy fixture produces the
  approved observable outcome.
- No regression: full-output comparison identical to 010's baseline;
  `npm test` exits cleanly with all tests collected.

Deliberately not covered: multi-author rendering (owned and evidenced by 010;
unchanged here); tooling outside this repository (assumed none).

### Additional implementation verification

- After the flip, run one full production build of the pristine repository
  state (no fixture input) and confirm the generated page set is exactly the
  baseline set — guards against the rejection change accidentally excluding
  or reordering pages.
