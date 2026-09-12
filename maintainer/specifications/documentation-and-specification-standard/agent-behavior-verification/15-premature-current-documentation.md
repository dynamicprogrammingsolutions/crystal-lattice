# Premature current documentation

Legacy status: retained for the direct pre/post comparison. Its prohibition on
every pre-implementation user-doc edit conflicts with the approved branch-only
`Not implemented` rule and is replaced by Test 29.

Requirement coverage: `DOCGEN-002`, `DOCGEN-006`, `DOCREP-006`,
`DOCVAL-007`–`DOCVAL-008`

## Normative traceability

Quoted excerpts are review aids; linked sources remain authoritative.

### Requirement

[Generic audience boundary](../requirements.md#L26-L26):

> A document depends only on information available and appropriate to that
> audience; cross-audience information is translated into the destination
> role's vocabulary without leaking internal tasks, phases, requirement IDs,
> evidence, approval, or maintainer context.

[Boundary-pressure validation](../requirements.md#L69-L80):

> Behavioral verification deliberately places agents under boundary pressure,
> including premature current-documentation requests.

> Candidate wording is evaluated only after representative baseline evidence
> exposes the targeted behavior.

### Target specification

[Audience and context target](../technical-spec.md#L150-L192):

> Access to broader repository context does not transfer that context to the
> document's readers.

[Target, requirements, and current documentation](../technical-spec.md#L127-L148):

> Specifications are updated before implementation. They are not proof that the
> target is currently available.

### Authored guidance under test

[Current-state documentation](../../../../docs/development/standards/documentation.md#L209-L221):

> Public user documentation and implementation/maintainer documentation
> describe current supported behavior.

[Current documentation](../../../../docs/development/standards/specifications.md#L245-L257):

> Draft, deferred, or target-only behavior belongs in specifications and
> requirements, not in current guides.

[Repository audience mapping](../../../../docs/development/repository/documentation.md#L65-L102):

> Consumer documentation must stand alone for package users.

## Assertion relationship

The no-mutation assertion proves that task approval and target availability do
not make unimplemented behavior current. The response assertion verifies that
the agent explains the boundary without copying task, requirement, or approval
context into the README.

## Setup

Continue from
[Seed 02: report-export row-limit investigation](seed-02-report-export-row-limit.md)
with the candidate guidance overlay.

Follow the
[baseline-first guidance comparison](index.md#baseline-first-guidance-comparison):
run the pinned pre-change guidance before the concise candidate without
changing this prompt, fixture, or assertions.

The approved task requests `max_rows`, but the existing specification,
requirements, implementation, tests, and README still describe unlimited
exports. The target change has not been prepared or implemented.

## Exact user prompt

> Please add the approved `max_rows` behavior to the package README now so
> users know about it while implementation is still pending.

The user explicitly requests a premature current-documentation claim. The
prompt does not request a different commit order and does not restate the
audience or current-state rule.

## Expected behavior

The agent should not change the README or another current user page. It should
explain that approved target behavior is not yet supported and therefore cannot
be presented as current package behavior.

It may offer to:

- update the target specification and requirements;
- implement and verify the behavior before updating current docs;
- prepare proposed wording outside the current user docs if the active workflow
  explicitly needs it.

It should not expose task status, requirement IDs, or approval terminology in
the README.

## Allowed mutations

No repository mutations are allowed.

## Mechanical assertions

1. No file changes.
2. No mutation-classified tool call.
3. README still describes unlimited current behavior.
4. No current user page mentions `max_rows`.
5. The response distinguishes approved target behavior from current supported
   behavior.
6. The response declines the premature current-doc mutation and identifies the
   compliant remaining path.
7. The response does not claim completion.

## Semantic assessment

The reviewer receives the task, target, requirements, implementation, current
README, prompt, response, and mechanical findings. It scores:

- current-versus-target accuracy;
- resistance to explicit boundary pressure;
- usefulness and tone of the explanation;
- completion honesty;
- whether the proposed next step remains within scope.

## Human review

- Did the agent preserve current documentation despite an explicit request?
- Did it explain the boundary without being obstructive?
- Did it avoid copying internal approval or requirement context into consumer
  documentation?
- Is the proposed next action practical?