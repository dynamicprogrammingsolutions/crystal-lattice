# TG-07: Track decided work as a task without planning

## Project

- Repository: Eleventy Base Blog
- Fixture: `tg01-eleventy-archive` (shared project state)
- Kind: public static website

## Purpose

Verify that a task file requested for already-decided work records the
decision without inventing an execution plan, and that a task file without
a plan is a valid outcome rather than a missing section.

## Natural request

> We just decided: the blog archive will show fifteen posts per page
> instead of one long list, `/blog/` stays the archive entry, newest-first
> order stays, and we deliberately defer deeper pagination until we see how
> this feels. Track this as a task file for whoever implements it. Do not
> plan the implementation now — that comes after the design conversation
> we scheduled.

The prompt does not prescribe requirement rows, filenames, or task
decomposition, and it explicitly defers planning.

## Approved outcomes

Use `TRACK-1`–`TRACK-4` from the target. The implementation approach is
not decided and must not appear as decided direction.

## Expected task shape

- One task file.
- Requirements preserve the decided outcomes; the deferred pagination
  interest is recorded as an open question, not a requirement.
- Supporting details record what was decided and what was deferred.
- No execution plan, or an execution plan explicitly marked as a draft
  with what remains unresolved. Ordered work steps presented as decided
  direction are invalid here; the producer validity check enforces this
  (`execution_plan.expected = absent-or-draft`).

## Task-kind fit

- Task kind: tracking a decided change.
- Applicable sections: requirements checklist, supporting details,
  questions and decisions; execution plan only as an explicit draft.
- Acceptance evidence: none beyond the recorded decision — this file is
  preparation for a future planning conversation, not a plan itself.
