# Task-quality coverage results

Evaluated September 26, 2026 on the [task-mechanics v3](20260926-task-mechanics-b1v3-results.md)
outputs with the two new coverage stages from subtask
`120-task-file-quality-coverage.md`: the per-subject task-file quality
assessment (six positive completeness dimensions, identity-blind GLM judge)
and the fresh-agent generated-file planning stage judged by the existing
handoff rubric.

Package: [results/20260926-task-quality-coverage](results/20260926-task-quality-coverage/).
The frozen dataset adds `quality_records` (18 subjects), `generated_plan_records`
(6 cells, all valid), and six `generated-file` handoff subjects to the complete
v3 matrix; labels `b1v3-r1`/`b1v3-r4`.

## Quality grades (18 subjects)

| Dimension | Top grade | Partial/other |
|---|---:|---:|
| `plan_design_completeness` | 14 complete | 4 partial |
| `durable_context_preservation` | 13 complete | 5 partial |
| `findability` | 18 complete | 0 |
| `section_appropriateness` | 18 complete | 0 |
| `plan_justification` | 16 justified | **2 fabricated** |
| `task_kind_fit` | 16 fits | **2 missing** |

The two dimensions with zero variance (`findability`, `section_appropriateness`)
either reflect genuinely uniform v3 structure or GLM-judge leniency; the
committed baseline (b0) packages are the calibration reference for deciding
which, and that comparison has not been run yet.

## What the flags show

- **Fabricated plans (2):** both book-discovery GPT cells (high and max) —
  the plan asserts design detail the producer conversation never
  established. This is the risky case gap 5 targets: invention filling a
  section, not restated planning.
- **Missing acceptance evidence (2):** the same two cells.
- **Dropped durable context (5):** notes-pagination GPT-high, both
  book-discovery GLM/GPT-max, author-migration GPT-xhigh.
- Book discovery concentrates almost every flag — the same scenario whose
  fragmentation rose under v3. Its task-count calibration and plan honesty
  are the same underlying problem.

## Fresh-agent generated-file planning (6 cells)

All six plans valid (no mutation, files unchanged). The existing handoff
rubric judged them at 91–95 alongside the canonical-handoff plans (90–96),
with `broad_rediscovery` false everywhere: a fresh agent can plan from the
v3-written files without repeating the producer's investigation. This is
the first evidence that model-written files carry enough context for a new
agent — the focused confirmation task 090 required.

## Findings recorded for follow-up

- **Framework:** GLM intermittently returns completed-but-empty responses;
  the run layer publishes them to the cache (`publish_when_no_provider_errors`
  cannot see them), permanently poisoning the identity. Six empty entries
  were purged manually during this run; the publish policy should treat an
  empty response as non-publishable, and the suite's validity layer should
  catch it before the driver asserts.
- The tg03 GLM producer re-executed genuinely today (its v3 cache entry was
  missing) and produced a different-but-valid task set; the dataset holds
  today's producer sample alongside the September 25 assessment subjects —
  acceptable for this coverage package since the quality assessment judges
  each record's own material.

## Preserved evidence

- [Result package](results/20260926-task-quality-coverage/index.md) with
  [matrix](results/20260926-task-quality-coverage/matrix.md),
  [costs](results/20260926-task-quality-coverage/costs.md), per-subject
  quality results pages under each scenario's
  `assessment/task-quality/results.md`, and each judgment's grades beside
  its evidence (`<cell>/s<N>/assessment.md`)
- [Scenario input definitions](scenarios/index.md)
