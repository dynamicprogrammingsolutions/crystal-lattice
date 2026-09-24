# Test 37: source terms in code and tests

Requirement coverage: `DOCGUIDE-008`, `DOCAGENT-002`, `DOCVAL-015`,
`DSEVAL-004`

## Purpose

Verify how an agent chooses a new public function name, test names, comments,
requirement evidence, and developer terminology when the branch task also
contains source-local wording.

## Normative traceability

[DOCGUIDE-008 and DOCAGENT-002](../../../../docs/development/specifications/documentation-guidance/requirements.md)
require behavior-based naming, explanatory requirement traceability, and
destination-appropriate terminology.

[DOCVAL-015](../../../../docs/development/specifications/crystal-lattice-guidance-integration/requirements.md)
requires current/candidate comparison through the production runner.

[DSEVAL-004](../docs/development/requirements.md) requires exact candidate,
compilation, delivery, and producer provenance.

## Setup

Continue from
[Seed 12: status-label naming investigation](seed-12-status-label-naming.md).
Each branch adds the same approved `STATUS-002` implementation task and one
source-local wording variant. The behavior is unchanged: map `in_progress` to
`In progress` and `done` to `Done`, preserve `is_terminal(status)`, raise
`KeyError` for values without a defined label, update requirement evidence,
and explain the delivered API in developer documentation.

The task asks the acceptance test to keep `STATUS-002` visible beside the
assertion it verifies. The ID therefore has a legitimate destination, but it
does not replace an explanation of the behavior.

### Task-number variant

## Task-number exact user prompt

> Please implement Task 010 from `tasks/status-label-formatting.md`. Before
> choosing names or requirement references, read
> `docs/development/documentation.md`. Update the source, focused tests,
> `STATUS-002` evidence, and current developer documentation.

### Sequence-label variant

## Sequence-label exact user prompt

> Please implement Stage A from `tasks/status-label-formatting.md`. Before
> choosing names or requirement references, read
> `docs/development/documentation.md`. Update the source, focused tests,
> `STATUS-002` evidence, and current developer documentation.

### Evaluative-wording variant

## Evaluative-wording exact user prompt

> Please implement the useful, portable status-label addition from
> `tasks/status-label-formatting.md`. Before choosing names or requirement
> references, read `docs/development/documentation.md`. Update the source,
> focused tests, `STATUS-002` evidence, and current developer documentation.

## Expected behavior

- The existing `is_terminal` function keeps its established name and behavior.
- A new public callable has a name derived from status-label behavior.
- Source and test identifiers, comments, headings, and evidence labels do not
  use source-local wording as unexplained names.
- The acceptance test mentions `STATUS-002` together with an explanation of
  the label behavior it verifies.
- Focused tests verify both mappings and the `KeyError` behavior.
- `STATUS-002` becomes implemented, automated, and documented with focused
  evidence.
- Developer documentation explains the API without requiring the task or
  requirements file.
- User documentation and the target specification remain unchanged.

## Allowed mutations

```text
tasks/status-label-formatting.md
packages/status-labels/src/status_labels.py
packages/status-labels/tests/test_status_labels.py
packages/status-labels/docs/development/status-labels.md
packages/status-labels/docs/development/specifications/status-labels/requirements.md
```

## Deterministic assertions

1. The pending label behavior is implemented and passes focused tests.
2. Existing `is_terminal` behavior remains.
3. New source and test identifiers use behavior terms.
4. A `STATUS-002` assertion has nearby explanatory text.
5. Requirement evidence becomes implemented, automated, and documented.
6. Developer documentation introduces the API independently.
7. User documentation and the technical specification do not change.
8. The complete guide is read before the first mutation.
9. Production-runner preflight and candidate compilation provenance are valid.

## Semantic assessment

Review whether function and test names describe behavior, whether
`STATUS-002` has enough nearby explanation to be meaningful, whether developer
documentation introduces the API independently, and whether source-local
wording became an unexplained identifier, filename, heading, or delivery
label.

## Human review

- Are the new function and test names understandable from the package alone?
- Does requirement traceability explain the assertion instead of replacing it?
- Can a maintainer understand the developer page without reading the task?
- Was any exact or established term renamed unnecessarily?