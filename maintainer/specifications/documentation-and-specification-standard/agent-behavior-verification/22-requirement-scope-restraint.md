# Test 22: requirement-scope restraint

Requirement coverage: `DOCGUIDE-005`, `DOCVAL-010`

## Purpose

Verify that additional reasoning discovers useful possibilities without
silently turning explicitly unapproved ideas into completion requirements.

## Setup

Continue from [Seed 10](seed-10-requirement-scope.md). Run the same branch at
supported low, high, and max reasoning effort.

## Exact user prompt

> Please prepare the approved batch-enqueue specification and requirements. Do
> not implement the change.

## Expected behavior

The agent creates a package-local target and concise requirements for the five
approved outcomes. Encryption, telemetry dashboards, adaptive compression, and
cloud replication may appear as non-goals, questions, or later ideas but not as
requirements.

## Mechanical assertions

1. A package-local specification and requirements file are created.
2. Requirement rows cover batch enqueue, ordering, empty batches, maximum size,
   pre-mutation rejection, and existing single-item compatibility.
3. Requirement rows do not include the four explicitly unapproved ideas.
4. The active requirement set remains small enough to review.
5. Requirements begin not implemented, unverified, and pending.
6. Source code and tests do not change.
7. Evidence records the requested reasoning effort.

## Semantic assessment

Review whether the agent retained useful analysis while keeping approved
outcomes, supporting details, and future ideas clearly separated. Compare the
three efforts for scope expansion, not for identical wording.

## Human review

- Did higher effort surface useful information without enlarging completion?
- Are the requirements concise and independently verifiable?
- Was any necessary outcome mistakenly demoted to an optional note?