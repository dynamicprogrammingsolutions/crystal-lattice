# Test 31: per-request timeout requirement quality

Requirement coverage: `DOCGUIDE-005`, `DOCVAL-010`, `DOCVAL-011`

Status: Optional same-family control; not part of the primary 21-run baseline.

## Purpose

Observe how model and reasoning effort affect requirements for a small
per-operation configuration extension.

## Exact user prompt

> Please inspect `packages/request-client`. Some callers need a different
> timeout for one request without reconfiguring the client. Add an optional
> per-call timeout override to `fetch`. A positive override applies only to
> that request, omitting it keeps the current client default, and a non-positive
> override must be rejected before the transport is called. Existing callers
> must continue to work. Prepare the package specification and requirements
> only. Do not implement the change.

## Fixture facts

- `Client` stores a default timeout supplied at construction.
- `fetch(url)` calls the transport with that stored timeout.
- The README documents the constructor default and current `fetch(url)` call.
- The package development index states that no per-request timeout
  specification exists.
- No task file is present and `TASKS-v7` is not injected.

## Desired target

The evaluator-only target is
[`targets/31-request-timeout.json`](targets/31-request-timeout.json). Producing
models do not receive it.

## Producer controls

- Start from a fresh fixture with no model-generated seed.
- Inject the approved requirement-minimal guidance variant.
- Permit changes only under
  `packages/request-client/docs/development/`.
- Do not assert exact requirement wording, row count, heading, or file shape.

## Control status

This scenario and its completed target-review history are retained while the
diverse-project baseline runs. Keep it only if later comparison shows a
distinct requirement-quality signal not covered by Tests 33–35.

## Semantic assessment

If this control is run later, compare generated requirements directly with the
target outcomes and identify material missing or additional scope, clarity,
verifiability, and grouping with model and effort visible.

## Human review

The human verifies the concise AI assessment and opens the complete
specification, requirements, or reviewer reasoning only when a finding needs
investigation. The human confirms, corrects, rejects, or identifies a target
problem for every run.