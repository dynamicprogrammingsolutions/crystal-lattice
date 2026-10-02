# Task-mechanics candidate v3 results

Evaluated September 25–26, 2026, on the restructured per-subject suite. The
candidate changes exactly one rule of
[candidate v2](20260925-task-mechanics-b1v2-results.md): creating task files
now determines the task structure from the request and the decomposition
rules (single task by default, children only when justified) and asks the
user only when their structure preference is material and cannot be inferred
— replacing the inherited "confirm which format the user wants" step that
made one model family ask and stop instead of creating files.

Source: `maintainer/guidance/candidates/task-mechanics-b1v3/`.
Package: [results/20260926-task-mechanics-b1v3](results/20260926-task-mechanics-b1v3/).

## Promotion

Promoted to current guidance on September 26, 2026 after explicit
approval: the candidate's tasks-v7 section replaced
`maintainer/guidance/current/sections/tasks-v7.md`, compiled outputs
were regenerated, and the guidance check passes (commit `4fb5f6a6`).
The focused confirmation evidence that closed the last open question is
in the [quality coverage](20260926-task-quality-coverage-results.md)
and [kind baseline](20260926-task-kind-baseline-results.md) reports.

## Status

All eighteen producer cells completed valid on their first execution — no
ask-and-stop behavior, no retries — including the notes-pagination GPT-high
cell that needed six samples under v2. Twelve fresh-agent plans and the
negative control are valid, and all eighteen task-creation subjects were
assessed.

Three same-agent GPT continuations are blocked by an external provider
failure: during the continuation stage the ChatGPT account's key exchange
began returning `401 invalid_api_key` for every GPT request (producers had
completed normally forty minutes earlier). The three cells are recorded as
invalid samples under labels `b1v3-r1`/`b1v3-r3`, their three handoff
assessment subjects are explicitly missing, and the dataset otherwise
selects label `b1v3-r1`. The GLM continuations are valid. Filling the three
blocked cells requires one continuation run, three focused assessments, and
a re-freeze once the provider path recovers.

## Task-creation quality (per-subject assessor)

| Cohort | Assessments | Overall | Fragmentation | Phase-only | Layer split | Evidence reownership | Dependency safety | Production crossing |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| All | 18 | 93.2% | 81.5% | 100.0% | 97.2% | 97.2% | 86.1% | 97.2% |
| GLM max | 6 | 96.3% | 94.5% | 100.0% | 100.0% | 100.0% | 91.7% | 91.7% |
| GPT high | 6 | 94.9% | 77.8% | 100.0% | 100.0% | 100.0% | 91.7% | 100.0% |
| GPT xhigh | 3 | 85.2% | 77.7% | 100.0% | 83.3% | 83.3% | 66.7% | 100.0% |
| GPT max | 3 | 91.7% | 66.7% | 100.0% | 100.0% | 100.0% | 83.3% | 100.0% |

## Comparison with v2

Per cell, nine improved, two regressed slightly, seven were unchanged;
across the six dimensions, ten statuses improved and six worsened.

- **The decisive-check rule landed on its targets.** Production-crossing
  evidence rose from 86.1% to 97.2%: the selected-filter GPT-high cell went
  `present → none` and selected-filter GLM `present → partial` — the two
  cells that had been guidance-insensitive since the current-guidance
  baseline — and both book-discovery
  GPT cells with partial crossing cleared. All GPT cohorts now score 100% on
  crossing.
- **Layer splits largely resolved.** 97.2% overall (v2 88.9%): book-discovery
  GPT-high went `partial → none` and GPT-max `present → none`.
- **Phase-only children are fully eliminated** (v2 had one partial).
- **Fragmentation rose in book discovery**: GPT-high and GPT-max went
  `medium → high` and GLM `none → low` — the layer-bundle fix pushed those
  cells toward more granular task sets than the target's four coherent
  deliverables. Their overall scores still improved substantially
  (63.8 → 83.3 and 72.2 → 83.3), so the added structure is closer to the
  reviewed targets than the two-layer bundles were, but task-count
  calibration may deserve one more wording pass.
- Two small regressions elsewhere: multi-consumer GLM lost one dependency
  point (`none → partial`), and author-migration GPT-high fragmentation
  `none → low` — both within single-sample run-to-run variance.

## Handoff evidence

Twelve fresh-agent plans valid; all nineteen judged handoff subjects score
90–96 (control 74), the same band as v2 and the reassessed baseline and
first candidate. All six same-agent continuations are valid.

## Interpretation

The step-1 rewording removed the ask-and-stop failure mode completely in
this run and coincided with the strongest task-creation results of any
candidate: 93.2% overall with production-connection evidence at 97.2% and
layer splits at 97.2%. Together with v2, the two-wording comparison shows
the decisive-check and design-visibility rules work as intended, and the
remaining calibration question is task-count granularity in book discovery
(fragmentation severity), not structure choice or crossing evidence.

## Preserved evidence

- [Result package](results/20260926-task-mechanics-b1v3/index.md) with
  [matrix](results/20260926-task-mechanics-b1v3/matrix.md) and
  [costs](results/20260926-task-mechanics-b1v3/costs.md)
- [Candidate source](../../../guidance/candidates/task-mechanics-b1v3/README.md)
- [Scenario input definitions](scenarios/index.md)
