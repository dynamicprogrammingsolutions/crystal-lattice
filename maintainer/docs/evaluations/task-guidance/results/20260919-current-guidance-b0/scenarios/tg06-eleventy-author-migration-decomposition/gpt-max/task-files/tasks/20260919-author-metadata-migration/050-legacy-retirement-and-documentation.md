# Retire the legacy author form when the evidence gate permits

Conditionally reject the legacy scalar author form after generated-output and
content evidence is green, then publish the verified authoring contract in
the smallest maintained documentation surface.

Parent Task: tasks/20260919-author-metadata-migration/000-main.md
Depends On: tasks/20260919-author-metadata-migration/040-generated-output-and-content-evidence.md

## Requirements checklist

- [ ] Inspect subtask 040's evidence before changing legacy behavior.
- [ ] If and only if the evidence gate is green, reject or remove the legacy
      scalar form according to the approved policy and update its intentional
      tests.
- [ ] If the gate is not green, leave legacy compatibility enabled, document
      the blocker, and do not claim that the migration is complete.
- [ ] Update maintained developer guidance with the approved front-matter
      structure, authoring-tool input, rendered behavior, and actual
      transition/retirement status.
- [ ] Run the final production build and test suite after the chosen outcome.

## Supporting facts

- The current repository has no authoring-guide section; `README.md` is the
  shortest existing project-level guidance surface.
- The legacy field currently appears in production content, the post layout,
  the feed, and the authoring helper, so retirement is unsafe until subtasks
  020, 030, and 040 have completed.
- The user requirement permits rejection only after evidence demonstrates that
  no remaining dependency requires the old form; it does not require
  rejection when evidence is incomplete.

## Execution plan

Status: Draft

Read the evidence and inventory produced by subtask 040. If any production
content, template, authoring path, generated output, or required regression
case still depends on the legacy scalar, make no rejection change. Record the
blocking dependency and leave the transition normalizer active for a later
follow-up.

If every approved evidence condition is green, replace the transitional
acceptance branch with the approved rejection/validation behavior, update
tests to prove that legacy input now fails in the documented way, and rerun
the complete production build. Keep an intentional migration-history note
only where it does not create a live production dependency.

Update the smallest existing maintained documentation surface after the
behavior is verified. The documentation must distinguish current supported
input from historical transition behavior and must not claim rejection if the
gate blocked it.

### Implementation decisions and open questions

- The exact rejection error and whether the old authoring function signature
  remains as a compatibility wrapper depend on the approved contract and
  external-consumer decision.
- Retirement is conditional, not automatic: a red or incomplete evidence
  record requires compatibility to remain enabled.
- Do not create a new documentation hierarchy solely for this migration; use
  the existing owner-facing guidance unless a later scope decision identifies
  a better owner.

### Documentation

Update `README.md` or the confirmed existing development owner document with:

- the approved structured author front-matter example;
- the authoring helper's approved input and safe serialization expectations;
- how one and multiple authors appear on post/archive/feed surfaces;
- whether legacy `author` is still accepted, deprecated, or rejected, based on
  the evidence gate.

Review the wording against the final build/test evidence so target-only
behavior is not presented as current guidance.

### Task checklist

- [ ] Review and record the subtask 040 evidence result.
- [ ] Keep compatibility and record a blocker if the evidence gate is not
      green.
- [ ] If green, implement and test the approved legacy rejection behavior.
- [ ] Update maintained documentation with verified current behavior.
- [ ] Run `npm test` and `npm run build` after the final outcome.
- [ ] Append immutable completion notes to the parent and this task when the
      execution is complete.

### Requirement verification

- A green gate is traceable to the generated-output and content evidence from
  subtask 040; no rejection is based on source search alone.
- If rejected, a legacy-form input test proves the documented failure and the
  migrated production build still passes.
- If not rejected, the task records the exact unresolved dependency and
  demonstrates that legacy content still builds during the transition.
- The final documentation matches the verified runtime behavior.
- Final `npm test` and `npm run build` runs collect, exit, and generate the
  expected public paths successfully.