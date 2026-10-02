# Task-mechanics candidate v2 results

Evaluated September 25, 2026, on the restructured per-subject suite. The
candidate adds two rules to
[task-mechanics candidate](20260919-task-mechanics-b1-results.md): the decisive
production-connection check may not be satisfied by separate per-side checks
and may not be waived or made conditional; and a nontrivial execution plan
explains the decided design before ordered steps.

Source: `maintainer/guidance/candidates/task-mechanics-b1v2/`.
Package: [results/20260925-task-mechanics-b1v2](results/20260925-task-mechanics-b1v2/).

## Status

All 74 cases completed; every producer, handoff plan, continuation, control,
and assessment subject is valid. One producer cell needed retries: GPT-high
notes pagination stopped to ask the single-file-versus-subtasks format
question in four of six genuine samples before producing a valid task set —
the same ask-and-stop behavior the earlier baseline and candidate worked around with retries. The
frozen dataset selects the valid sample (labels `b1v2-r1`, `b1v2-r4`,
`b1v2-r6`); the ask-format records remain in the raw runs.

## Task-creation quality (per-subject assessor)

| Cohort | Assessments | Overall | Fragmentation | Phase-only | Layer split | Evidence reownership | Dependency safety | Production crossing |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| All | 18 | 90.0% | 87.0% | 97.2% | 88.9% | 100.0% | 80.6% | 86.1% |
| GLM max | 6 | 97.2% | 100.0% | 100.0% | 100.0% | 100.0% | 83.3% | 100.0% |
| GPT high | 6 | 92.9% | 94.5% | 83.3% | 83.3% | 100.0% | 91.7% | 83.3% |
| GPT xhigh | 3 | 85.2% | 77.7% | 83.3% | 83.3% | 100.0% | 66.7% | 100.0% |
| GPT max | 3 | 86.1% | 77.7% | 100.0% | 83.3% | 100.0% | 66.7% | 83.3% |

Against the reassessed first-candidate comparison (64.8% → 88.1%), v2 reaches 90.0% with
production-crossing evidence up from 69.4% to 86.1% — the decisive-check rule
moved its target dimension. Dependency safety is lower than the first candidate's reassessed
94.4% (80.6% here); with one sample per cell per evaluation, cross-run
sampling variance of this size is expected and the per-cell detail in the
package shows the affected cells changed rather than a systematic regression.

## Handoff evidence

Twelve fresh-agent plans and the negative control are valid; all eighteen
judged handoff subjects score 90–96 (control 74), consistent with the
reassessed baseline and first-candidate band. Same-agent continuations are valid for all six cells.

## Interpretation

The two added rules did not regress any cohort, materially improved
production-connection evidence, and kept every other dimension at or above
the reassessed first-candidate level except dependency safety (single-sample variance).
The ask-and-stop format behavior remains: it is caused by the inherited
"confirm which format the user wants" rule interacting with requests that
delegate the structure choice, and is corrected in
[candidate v3](20260926-task-mechanics-b1v3-results.md).

## Preserved evidence

- [Result package](results/20260925-task-mechanics-b1v2/index.md) with
  [matrix](results/20260925-task-mechanics-b1v2/matrix.md) and
  [costs](results/20260925-task-mechanics-b1v2/costs.md)
- [Candidate source](../../../guidance/candidates/task-mechanics-b1v2/README.md)
- [Scenario input definitions](scenarios/index.md)
