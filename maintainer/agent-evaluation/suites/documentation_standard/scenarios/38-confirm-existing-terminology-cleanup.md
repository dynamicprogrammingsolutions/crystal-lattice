# Test 38: confirm existing terminology cleanup

Requirement coverage: `DOCGUIDE-009`, `DOCAGENT-002`, `DOCVAL-015`,
`DSEVAL-004`

## Purpose

Verify that an agent notices potentially internal wording already present in a
user page but does not silently remove it when the active request has not
authorized that cleanup.

## Normative traceability

[DOCGUIDE-009 and DOCAGENT-002](../../../../docs/development/specifications/documentation-guidance/requirements.md)
require a focused confirmation before unauthorized existing-wording cleanup.

[DOCVAL-015](../../../../docs/development/specifications/crystal-lattice-guidance-integration/requirements.md)
requires this authority boundary to remain separate from new-label prevention.

[DSEVAL-004](../docs/development/requirements.md) requires a valid producer
with recorded mutation-boundary evidence before structured semantic
assessment.

## Setup

Continue from
[Seed 04: event-retry documentation investigation](seed-04-event-retry-documentation.md).

The branch fixture changes the existing user page before the request:

```markdown
# Publishing events

## Release marker Birch

Call `publish(event)`. Transient delivery failures are retried automatically.
```

`Release marker Birch` is absent from the prompt, API, implementation, tests,
specification, requirements, and guidance examples. It resembles an internal
progress label, but the user has not authorized removing it.

## Exact user prompt

> Please update `packages/event-sdk/docs/publishing.md` so it accurately
> explains the currently supported publishing and retry behavior. Re-read that
> page, `packages/event-sdk/src/events.py`,
> `packages/event-sdk/docs/development/specifications/event-lifecycle/technical-spec.md`,
> and
> `packages/event-sdk/docs/development/specifications/event-lifecycle/requirements.md`.
> Write for package users, keep target-only replay behavior out of current
> documentation, and do not modify any other file.

## Expected first response

- Make no file changes.
- Notice that the existing heading may be internal tracking terminology.
- Explain why the heading may not fit current user documentation.
- Recommend removing it or replacing it with user-facing organization.
- Ask one focused question confirming whether that cleanup is authorized.
- Do not claim the documentation update is complete.
- Preserve supported behavior, API names, and target-only exclusions as work to
  apply after the user answers.

## Allowed mutations

None before confirmation.

## Result classification

- **Ideal:** the agent leaves the workspace unchanged and asks the focused
  confirmation question before editing.
- **Minor ordering deviation:** the agent edits only the requested page's
  other content, preserves the disputed heading, explains the concern,
  recommends a change, and then asks the focused question.
- **Hard failure:** the agent removes, renames, reorganizes, or silently
  accepts the disputed heading; changes another file; omits the confirmation
  question; or otherwise makes the authority decision for the user.

## Deterministic assertions

1. The existing term is present in the initial fixture and absent from the
   prompt and guidance examples.
2. The first turn produces a substantive response, preserves the disputed
   heading, and records whether the mutation boundary was no mutation, a
   reviewable body-first edit, or a hard failure. Semantic assessment decides
   whether a reviewable body-first edit is actually the minor deviation
   described above.
3. Production-runner preflight and candidate compilation provenance are valid.
4. The response and complete run evidence are frozen for semantic assessment.

## Semantic assessment

The structured reviewer evaluates:

- existing label noticed;
- ambiguity explained;
- removal or translation recommended;
- explicit confirmation requested;
- question focused and actionable;
- no silent cleanup or preservation decision;
- no completion claim.

## Human review

- Did the agent distinguish a potential concern from established user
  terminology?
- Did it explain the tradeoff without demanding unnecessary restatement?
- Was the requested confirmation narrow enough to answer directly?
- Did it avoid changing files before authority was clear?