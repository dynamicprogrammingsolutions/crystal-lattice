# Test 31: source terms in code and tests

Requirement coverage: `DOCGUIDE-007`–`DOCGUIDE-008`, `DOCVAL-011`

## Purpose

Verify how an agent chooses a new public function name, test names, comments,
requirement evidence, and developer terminology when the branch task also
contains source-local wording.

## Setup

Continue from
[Seed 12: status-label naming investigation](seed-12-status-label-naming.md).
Each branch adds the same approved `STATUS-002` implementation task and one
source-local wording variant. The required behavior is unchanged: map
`in_progress` to `In progress` and `done` to `Done`, preserve
`is_terminal(status)`, raise `KeyError` for values without a defined label,
update requirement evidence, and explain the delivered API in developer
documentation.

The task asks the acceptance test to keep `STATUS-002` visible beside the
assertion it verifies. The requirement ID therefore has a legitimate
destination, but it does not replace an explanation of the behavior.

### Task-number variant

The task says the conversation refers to the change as `Task 010`.

## Task-number exact user prompt

> Please implement Task 010 from `tasks/status-label-formatting.md`. Update the
> source, focused tests, `STATUS-002` evidence, and current developer
> documentation.

### Sequence-label variant

The task says the conversation refers to the change as `Stage A`.

## Sequence-label exact user prompt

> Please implement Stage A from `tasks/status-label-formatting.md`. Update the
> source, focused tests, `STATUS-002` evidence, and current developer
> documentation.

### Evaluative-wording variant

The task describes the change as a `useful, portable status-label addition`
without making those words public API requirements.

## Evaluative-wording exact user prompt

> Please implement the useful, portable status-label addition from
> `tasks/status-label-formatting.md`. Update the source, focused tests,
> `STATUS-002` evidence, and current developer documentation.

## Expected behavior

- The existing `is_terminal` function keeps its established name and behavior.
- A new public callable has a name derived from status-label behavior.
- Source filenames, function names, test filenames, test names, comments, and
  developer headings do not use source-local wording as unexplained names.
- The acceptance test mentions `STATUS-002` together with an explanation of
  the label behavior it verifies.
- Focused tests verify the two mappings and the `KeyError` behavior.
- `STATUS-002` becomes implemented, automated, and documented with focused
  evidence.
- Developer documentation explains the delivered API without requiring the
  task or requirements file.
- User documentation remains unchanged.

## Allowed mutations

```text
tasks/status-label-formatting.md
packages/status-labels/src/status_labels.py
packages/status-labels/tests/test_status_labels.py
packages/status-labels/docs/development/status-labels.md
packages/status-labels/docs/development/specifications/status-labels/requirements.md
```

## Initial mechanical observations

The initial baseline records, but does not rely on these checks alone:

1. The pending label behavior is implemented and tested.
2. Existing `is_terminal` behavior remains.
3. New source and test identifiers are collected.
4. The `STATUS-002` test context, requirement row, developer page, changed
   paths, complete diff, and response are retained.
5. No user-documentation or target-specification mutation occurs.

## Semantic assessment

Review whether function and test names describe the behavior, whether
`STATUS-002` has enough nearby explanation to be meaningful, whether developer
documentation introduces the API independently, and whether any source-local
wording became an unexplained identifier, filename, heading, or delivery
label.

## Human review

- Are the new function and test names understandable from the package alone?
- Does requirement traceability explain the assertion instead of replacing
  it?
- Can a maintainer understand the developer page without reading the task?
- Was any exact or established term renamed unnecessarily?
