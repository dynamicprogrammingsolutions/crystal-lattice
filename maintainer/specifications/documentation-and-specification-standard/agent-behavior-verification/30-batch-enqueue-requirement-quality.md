# Test 30: batch-enqueue requirement quality

Requirement coverage: `DOCGUIDE-005`, `DOCVAL-010`, `DOCVAL-011`

Status: Optional same-family control; not part of the primary 21-run baseline.

## Purpose

Observe how model and reasoning effort affect the minimum sufficient
requirements for a small stateful API extension.

## Exact user prompt

> Please inspect `packages/offline-queue`. Callers need to enqueue a group of
> items in one operation. A valid batch should be appended in the order
> supplied, using 100 as the default maximum size. Empty or oversized batches
> must be rejected before the queue changes, and existing single-item callers
> must continue to work. Prepare the package specification and requirements
> only. Do not implement the change.

## Fixture facts

- `Queue` stores items in an in-memory list.
- `enqueue(item)` appends one item.
- The README documents only the single-item operation.
- The package development index states that no batch-enqueue specification
  exists.
- No task file is present and `TASKS-v7` is not injected.

## Desired target

The evaluator-only target is
[`targets/30-batch-enqueue.json`](targets/30-batch-enqueue.json). Producing
models do not receive it.

## Producer controls

- Start from a fresh fixture with no model-generated seed.
- Inject the approved requirement-minimal guidance variant.
- Permit changes only under
  `packages/offline-queue/docs/development/`.
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