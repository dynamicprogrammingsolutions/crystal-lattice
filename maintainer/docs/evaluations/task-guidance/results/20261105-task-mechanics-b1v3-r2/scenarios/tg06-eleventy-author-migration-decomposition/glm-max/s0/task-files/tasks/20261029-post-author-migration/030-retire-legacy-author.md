# Retire the legacy author form (evidence-gated)

After reviewing the recorded migration evidence, make the build reject the
legacy single-name `author` form with an actionable error, replace the
temporary dual-acceptance test coverage, and update documentation so the
structured form is documented as the only supported author form.

Parent Task: tasks/20261029-post-author-migration/000-main.md

Depends On: tasks/20261029-post-author-migration/010-introduce-multi-author-model.md, tasks/20261029-post-author-migration/020-migrate-existing-posts.md

## Requirements checklist

- [ ] Gate evidence is reviewed and recorded in this task file before
      rejection is enabled: (a) 020 generated-output parity, (b) 020 content
      scan showing no legacy keys, (c) 010 evidence that
      `scripts/new-post.js` emits only the new form. If any leg is missing,
      stop — rejection must not be enabled.
- [ ] The production build fails with an actionable error (naming the file and
      the fix) when a post still uses the legacy `author` form.
- [ ] Repository content builds cleanly under the strict validation.
- [ ] Temporary dual-acceptance coverage from 010 is replaced: the legacy-form
      acceptance test is removed and rejection coverage added (unit +
      real-build integration); the repo-content pins stay valid.
- [ ] README updated: the structured form is the only supported author form;
      dual-acceptance wording removed.

## Supporting details

- Rejection lives in the shared normalization point added in 010, so the
  production build fails and every consumer of the model shares one rule.
- Out-of-repo consumers of the legacy form (if any) are not observable here;
  the gate covers in-repo content and generated output only. The actionable
  rejection message is the mitigation for unknown external consumers.
- The 010 repo-content pins (author strings on post pages and feed) remain
  valid because 020 proved migrated content renders the same output; only the
  temp-fixture legacy-acceptance test is replaced here.

## Execution plan

Status: Draft

1. Review and record the gate evidence (a–c) in `## Implementation Notes`
   before touching validation.
2. Make the normalization strict: a legacy `author` key present on a post
   throws with a message naming the file and pointing to the structured form,
   so the production build fails.
3. Unit test the strict path; integration test: a temp fixture site with a
   legacy-form post fails the real build with the expected message, and
   repository content still builds cleanly.
4. Remove the 010 temp-fixture legacy-acceptance test; keep all other
   coverage.
5. Rewrite the README authoring section (structured form only).
6. `npm test` and `npm run build` green on repository content; record
   evidence.

### Implementation decisions and open questions

- Resolved (local): enforcement point is the shared normalization module, not
  per-template checks — one rule, and the build fails at the source.
- Enabling rejection after the gate is itself the approved parent outcome
  (R5); no further approval is needed beyond the parent plan approval and the
  recorded gate evidence.

### Documentation

- Rewrite the README "Post authors" section in the same change that enables
  rejection: the legacy form is removed from supported behavior and the
  migration note is deleted.

### Task checklist

- [ ] Gate evidence (a–c) reviewed and recorded before validation changes.
- [ ] Strict validation implemented (actionable build error).
- [ ] Rejection tests added (unit + real-build integration asserting the
      expected message); repo-content real build still green.
- [ ] Temporary legacy-acceptance test removed.
- [ ] README authoring section rewritten (structured form only).
- [ ] `npm test` green; `npm run build` green on repository content; evidence
      recorded.

### Requirement verification

- Rejection behavior (R5): integration test drives the real Eleventy build on
  a temp fixture with a legacy-form post and asserts failure with the
  actionable message; a real build of repository content succeeds.
- Gate honored (R5): the recorded review of parity, scan, and tooling evidence
  in this task file, written before the validation change.
- Documentation current (R6): README shows the structured form as the only
  supported form, changed in the same reviewed change as the strict
  validation.
