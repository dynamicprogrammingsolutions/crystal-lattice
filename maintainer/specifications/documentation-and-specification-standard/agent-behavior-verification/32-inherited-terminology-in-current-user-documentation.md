# Test 32: inherited terminology in current user documentation

Requirement coverage: `DOCGUIDE-007`–`DOCGUIDE-008`, `DOCVAL-011`

## Purpose

Verify that an agent removes an internal progress label already present in a
current user page when the page is updated, even though the new prompt does not
repeat or identify that label.

This is distinct from Tests 30 and 31. Those tests verify that source-local
terms do not enter newly created records. This test begins with the term
already present in the maintained page.

## Normative traceability

[DOCGUIDE-007–DOCGUIDE-008](../requirements.md#L132-L133) require terminology
to be selected for the maintained context and apply that rule specifically to
user documentation.

[DOCVAL-011](../requirements.md#L136) requires realistic terminology
validation using complete files, diffs, responses, tool behavior, and
provenance without reusing guidance examples as scenario wording.

## Setup

Continue from
[Seed 04: event-retry documentation investigation](seed-04-event-retry-documentation.md).

The branch fixture changes the existing user page before the request:

```markdown
# Publishing events

## Milestone Cedar

Call `publish(event)`. Transient delivery failures are retried automatically.
```

`Milestone Cedar` represents progress terminology that leaked into current
documentation. It does not appear in the branch prompt, package API,
implementation, tests, specification, requirements, or candidate guidance
examples.

## Exact user prompt

> Please update `packages/event-sdk/docs/publishing.md` so it accurately
> explains the currently supported publishing and retry behavior. Re-read that
> page, `packages/event-sdk/src/events.py`,
> `packages/event-sdk/docs/development/specifications/event-lifecycle/technical-spec.md`,
> and
> `packages/event-sdk/docs/development/specifications/event-lifecycle/requirements.md`.
> Write for package users, keep target-only replay behavior out of current
> documentation, and do not modify any other file.

## Expected behavior

- Remove the inherited `Milestone Cedar` heading.
- Preserve the documented `publish(event)` entry point.
- Explain that transient failures retry until the configured attempt limit and
  then fail.
- Exclude target-only replay behavior and internal requirement/specification
  terminology.
- Do not replace the inherited heading with another progress or tracking
  label.
- Modify only the current publishing page.

## Allowed mutations

```text
packages/event-sdk/docs/publishing.md
```

## Mechanical assertions

1. The inherited term is present in the initial branch fixture but absent from
   the branch prompt.
2. The final page does not contain `Milestone Cedar`.
3. The final page retains publishing and retry behavior and explains the
   attempt-limit failure boundary.
4. The final page does not describe replay or internal records.
5. Headings contain no replacement milestone, phase, stage, checkpoint,
   workstream, or iteration label.
6. No other file changes.

## Semantic assessment

Review whether the page is organized around supported user behavior, whether
the inherited progress term was removed rather than renamed, whether the retry
boundary is understandable without specification context, and whether
target-only behavior remains excluded.

## Human review

- Does the page read as current package documentation rather than a progress
  record?
- Was the existing internal term removed without prompt priming?
- Were supported behavior and established API names preserved?
- Did the agent avoid substituting a different unexplained tracking label?