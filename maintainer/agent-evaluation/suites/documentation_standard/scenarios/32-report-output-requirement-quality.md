# Test 32: report-output requirement quality

Requirement coverage: `DOCGUIDE-005`, `DOCVAL-010`, `DOCVAL-011`

Status: Optional same-family control; not part of the primary 21-run baseline.

## Purpose

Observe how model and reasoning effort affect requirements for a small CLI
output extension.

## Exact user prompt

> Please inspect `packages/report-cli`. Users need an optional
> `--output FILE` argument. When supplied, it writes the same UTF-8 JSON report
> currently printed to standard output and does not also print the report.
> Without the option, current output and successful behavior remain unchanged.
> A write failure must produce a non-zero result with a clear error and no
> success claim. Report formatting must not change. Prepare the package
> specification and requirements only. Do not implement the change.

## Fixture facts

- `render_report(rows)` returns the current formatted JSON text.
- The CLI prints that text to standard output and returns success.
- The README documents only the standard-output workflow.
- The package development index states that no output-file specification
  exists.
- No task file is present and `TASKS-v7` is not injected.

## Desired target

The evaluator-only target is
[`targets/32-report-output.json`](../targets/32-report-output.json). Producing
models do not receive it.

## Producer controls

- Start from a fresh fixture with no model-generated seed.
- Inject the approved requirement-minimal guidance variant.
- Permit changes only under `packages/report-cli/docs/development/`.
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