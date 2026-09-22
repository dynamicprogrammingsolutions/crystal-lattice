# Task-guidance current-guidance baseline status

- Producer attempt: `b0-v5-r1`
- Handoff attempt: `b0-v5-r1`
- Semantic attempt: `b0-metrics1`

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
| All | 18 | 67.4% | 68.5% | 50.0% | 72.2% | 58.3% | 75.0% | 80.6% |
| GLM | 6 | 84.7% | 83.3% | 83.3% | 75.0% | 100.0% | 91.7% | 75.0% |
| GPT | 12 | 58.8% | 61.1% | 33.3% | 70.8% | 37.5% | 66.7% | 83.3% |
| GLM max | 6 | 84.7% | 83.3% | 83.3% | 75.0% | 100.0% | 91.7% | 75.0% |
| GPT high | 6 | 62.9% | 61.0% | 33.3% | 83.3% | 33.3% | 75.0% | 91.7% |
| GPT xhigh | 3 | 48.2% | 55.7% | 16.7% | 50.0% | 50.0% | 50.0% | 66.7% |
| GPT max | 3 | 61.1% | 66.7% | 50.0% | 66.7% | 33.3% | 66.7% | 83.3% |
