# Task-guidance task-mechanics candidate status

- Producer attempt: `b1-v1-r1`
- Handoff attempt: `b1-v1-r1`
- Semantic attempt: `b1-metrics1`

| Stage | Expected | Present | Valid | Invalid | Missing |
|---|---:|---:|---:|---:|---:|
| Task creation | 18 | 18 | 18 | 0 | 0 |
| Fresh-agent planning | 12 | 12 | 12 | 0 | 0 |
| Same-agent planning | 6 | 6 | 5 | 1 | 0 |
| Semantic batches | 6 | 6 | — | — | 0 |
| Handoff semantic batches | 3 | 3 | — | — | 0 |
| Negative controls | 1 | 1 | — | — | 0 |
| Provider setup blockers | — | 0 | — | — | — |

## Invalid records

- `tg03-flask-vue-refresh-handoff:gpt:high`: parent task creation produced no task files

## Task-creation semantic quality

| Cohort | Assessments | Overall success | Fragmentation | Phase-only | Layer split | Evidence reownership | Dependency safety | Production crossing |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| All | 18 | 87.0% | 83.3% | 100.0% | 83.3% | 100.0% | 80.6% | 75.0% |
| GLM | 6 | 95.8% | 100.0% | 100.0% | 100.0% | 100.0% | 91.7% | 83.3% |
| GPT | 12 | 82.6% | 75.0% | 100.0% | 75.0% | 100.0% | 75.0% | 70.8% |
| GLM max | 6 | 95.8% | 100.0% | 100.0% | 100.0% | 100.0% | 91.7% | 83.3% |
| GPT high | 6 | 88.9% | 83.3% | 100.0% | 83.3% | 100.0% | 91.7% | 75.0% |
| GPT xhigh | 3 | 75.0% | 66.7% | 100.0% | 66.7% | 100.0% | 50.0% | 66.7% |
| GPT max | 3 | 77.8% | 66.7% | 100.0% | 66.7% | 100.0% | 66.7% | 66.7% |
