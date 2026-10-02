# Task-kind scenario baseline results

The four task-kind scenarios — decided-work tracking, contributor
documentation, deployment operations, and interface copywriting — ran
first on September 26, 2026 against
[task-mechanics v3](20260926-task-mechanics-b1v3-results.md), establishing
the baseline before any kind-specific guidance wording exists.

Package: [results/20260926-task-kind-baseline](results/20260926-task-kind-baseline/)
(labels `b1v3-r1`/`b1v3-r4` for the earlier matrix, `b1v3-k1` for the kind
scenarios).

## What the kind scenarios caught immediately

Two producer failure modes appeared on their first execution, each in one
of three samples per cell:

- **Content task, structure question (tg10 GPT-high):** the model
  investigated the copy surfaces, then stopped to ask whether the task
  should include a retained execution plan or requirements and facts only
  — a new instance of the ask-and-stop structure-choice mechanism, this
  time about the *conditional execution plan* rather than
  single-versus-subtasks. The other two samples produced valid files.
- **Unconditional plan (tg07 GLM):** despite an explicit "do not plan the
  implementation now", one sample wrote a filled execution plan without a
  draft status; the new deterministic absent-or-draft assertion rejected
  it. The other two samples correctly produced plan-free decision records.

Both are real B1v3 guidance gaps — nothing in the current wording says the
execution plan is conditional — and both are flaky (1/3), meaning
single-sample matrices can miss them.

## Quality grades (10 valid subjects)

| Dimension | Result |
|---|---|
| `task_kind_fit` | **10/10 fits** — no mechanically forced test sections |
| `plan_justification` | 5 `not_applicable` (tracking) + 5 `justified` |
| `durable_context_preservation` | 10 complete |
| `findability` / `section_appropriateness` | 10 complete |
| `plan_design_completeness` | 8 complete, 1 partial, 1 poor |

The task-creation decomposition assessor scored all ten subjects 100.0
overall. The kind declarations in the targets (`applicable_sections`,
`acceptance_evidence`) gave `task_kind_fit` a concrete authority to judge
against, and the GLM judge used it.

## Reading the baseline

- The four scenarios work as designed: they separate kind fit from
  decomposition quality, the deterministic plan assertion catches
  invented plans, and multi-sampling exposes flaky structure behavior.
- The B1v3 guidance has no notion of conditional sections yet, so the
  1/3 failure rates on tg07/tg10 are the calibration targets for the
  next candidate's wording (gap 5 and gap 6 of subtask
  `120-task-file-quality-coverage.md`).
- The `findability` and `section_appropriateness` dimensions again show
  no variance under the GLM judge; a baseline-comparison pass over the
  committed current-guidance package is the pending check for judge
  leniency.

## Preserved evidence

- [Result package](results/20260926-task-kind-baseline/index.md) with
  [matrix](results/20260926-task-kind-baseline/matrix.md) and
  [costs](results/20260926-task-kind-baseline/costs.md)
- [Scenario input definitions](scenarios/index.md) — regenerated with the
  four kind scenarios
