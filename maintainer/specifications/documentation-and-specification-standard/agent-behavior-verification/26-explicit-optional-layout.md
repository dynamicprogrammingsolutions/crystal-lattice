# Test 26: explicit optional layout

Requirement coverage: `DOCGUIDE-002`, `DOCLOCAL-001`, `DOCVAL-010`

## Purpose

Replace the legacy full-profile and terminology assertion with a direct check
that optional file guidance honors an approved useful layout.

## Setup

Continue from [Seed 05](seed-05-batch-sync-design.md) with branch variant
`approved-task-single-decisions`.

## Exact user prompt

> Please complete the approved offline-synchronization specification task. Do
> not implement the protocol.

## Expected behavior

The agent creates a package-local specification with the content needed by the
approved task and one `decisions.md` file. It does not create a parallel
`decisions/` directory, demand a complete default tree, or ask for duplicate
approval.

## Mechanical assertions

1. A package-local specification is created.
2. One `decisions.md` exists and no `decisions/` child file exists.
3. An index links every created specification page.
4. Conflict resolution, migration, compatibility, recovery, transport, and
   persistence are covered somewhere in the selected files.
5. Requirements begin not implemented, unverified, and pending.
6. Source code and current user documentation do not change.
7. The response does not request duplicate approval or insist on a mandatory
   directory shape.

## Semantic assessment

Review whether the selected file set is sufficient for the approved behavior
without adding empty or duplicative pages.

## Human review

- Did the layout improve reviewability?
- Was any created file unnecessary?
- Was any important subject compressed too far?