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

## Task-creation semantic detail

One row per judgment. Each cohort row above is the average of its rows here; dimension cells read `status (score)`.

| Scenario | Producer | Overall | Fragmentation | Phase-only | Layer split | Evidence reownership | Dependency safety | Production crossing | Run | Judgment |
|---|---|---:|---|---|---|---|---|---|---|---|
| `tg01-eleventy-archive-handoff` | glm max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [glm-max](scenarios/tg01-eleventy-archive-handoff/glm-max) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/task-creation/results.md) |
| `tg01-eleventy-archive-handoff` | gpt high | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [gpt-high](scenarios/tg01-eleventy-archive-handoff/gpt-high) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/task-creation/results.md) |
| `tg02-fastapi-pagination-handoff` | glm max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [glm-max](scenarios/tg02-fastapi-pagination-handoff/glm-max) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/task-creation/results.md) |
| `tg02-fastapi-pagination-handoff` | gpt high | 55.5 | medium (33) | present (0) | none (100) | present (0) | none (100) | none (100) | [gpt-high](scenarios/tg02-fastapi-pagination-handoff/gpt-high) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/task-creation/results.md) |
| `tg03-flask-vue-refresh-handoff` | glm max | 91.7 | none (100) | none (100) | none (100) | none (100) | none (100) | partial (50) | [glm-max](scenarios/tg03-flask-vue-refresh-handoff/glm-max) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/task-creation/results.md) |
| `tg03-flask-vue-refresh-handoff` | gpt high | 91.7 | none (100) | none (100) | none (100) | none (100) | none (100) | partial (50) | [gpt-high](scenarios/tg03-flask-vue-refresh-handoff/gpt-high) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/task-creation/results.md) |
| `tg04-flask-vue-discovery-decomposition` | glm max | 38.8 | medium (33) | present (0) | present (0) | none (100) | none (100) | present (0) | [glm-max](scenarios/tg04-flask-vue-discovery-decomposition/glm-max) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-creation/results.md) |
| `tg04-flask-vue-discovery-decomposition` | gpt high | 38.8 | medium (33) | present (0) | present (0) | present (0) | none (100) | none (100) | [gpt-high](scenarios/tg04-flask-vue-discovery-decomposition/gpt-high) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-creation/results.md) |
| `tg04-flask-vue-discovery-decomposition` | gpt max | 30.5 | medium (33) | present (0) | present (0) | present (0) | none (100) | partial (50) | [gpt-max](scenarios/tg04-flask-vue-discovery-decomposition/gpt-max) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-creation/results.md) |
| `tg04-flask-vue-discovery-decomposition` | gpt xhigh | 30.5 | medium (33) | present (0) | present (0) | partial (50) | none (100) | present (0) | [gpt-xhigh](scenarios/tg04-flask-vue-discovery-decomposition/gpt-xhigh) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-creation/results.md) |
| `tg05-fastapi-multi-consumer-decomposition` | glm max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [glm-max](scenarios/tg05-fastapi-multi-consumer-decomposition/glm-max) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-creation/results.md) |
| `tg05-fastapi-multi-consumer-decomposition` | gpt high | 52.8 | low (67) | present (0) | none (100) | present (0) | partial (50) | none (100) | [gpt-high](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-high) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-creation/results.md) |
| `tg05-fastapi-multi-consumer-decomposition` | gpt max | 91.7 | none (100) | none (100) | none (100) | none (100) | partial (50) | none (100) | [gpt-max](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-max) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-creation/results.md) |
| `tg05-fastapi-multi-consumer-decomposition` | gpt xhigh | 52.8 | low (67) | present (0) | none (100) | present (0) | partial (50) | none (100) | [gpt-xhigh](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-xhigh) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-creation/results.md) |
| `tg06-eleventy-author-migration-decomposition` | glm max | 77.8 | low (67) | none (100) | partial (50) | none (100) | partial (50) | none (100) | [glm-max](scenarios/tg06-eleventy-author-migration-decomposition/glm-max) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-creation/results.md) |
| `tg06-eleventy-author-migration-decomposition` | gpt high | 38.8 | medium (33) | present (0) | none (100) | present (0) | present (0) | none (100) | [gpt-high](scenarios/tg06-eleventy-author-migration-decomposition/gpt-high) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-creation/results.md) |
| `tg06-eleventy-author-migration-decomposition` | gpt max | 61.2 | low (67) | partial (50) | none (100) | present (0) | partial (50) | none (100) | [gpt-max](scenarios/tg06-eleventy-author-migration-decomposition/gpt-max) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-creation/results.md) |
| `tg06-eleventy-author-migration-decomposition` | gpt xhigh | 61.2 | low (67) | partial (50) | partial (50) | none (100) | present (0) | none (100) | [gpt-xhigh](scenarios/tg06-eleventy-author-migration-decomposition/gpt-xhigh) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-creation/results.md) |

## Handoff semantic detail

One row per judgment, across plan variants and stages.

| Scenario | Variant | Stage | Producer | Handoff quality | Plan coverage | Self-contained | Broad rediscovery | Documentation | Testing | Run | Judgment |
|---|---|---|---|---:|---|---|---|---|---|---|---|
| `tg01-eleventy-archive-handoff` | generated-task | same-agent | glm max | 96 | complete | yes | no | appropriate | decisive | [continuation](scenarios/tg01-eleventy-archive-handoff/glm-max/continuation) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) |
| `tg01-eleventy-archive-handoff` | generated-task | same-agent | gpt high | 75 | complete | yes | no | appropriate | decisive | [continuation](scenarios/tg01-eleventy-archive-handoff/gpt-high/continuation) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) |
| `tg01-eleventy-archive-handoff` | omit | fresh-agent | glm max | 92 | complete | yes | no | appropriate | decisive | [plan-omit](scenarios/tg01-eleventy-archive-handoff/glm-max/plan-omit) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) |
| `tg01-eleventy-archive-handoff` | omit | fresh-agent | gpt high | 91 | complete | yes | no | appropriate | decisive | [plan-omit](scenarios/tg01-eleventy-archive-handoff/gpt-high/plan-omit) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) |
| `tg01-eleventy-archive-handoff` | retain | fresh-agent | glm max | 95 | complete | yes | no | appropriate | decisive | [plan-retain](scenarios/tg01-eleventy-archive-handoff/glm-max/plan-retain) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) |
| `tg01-eleventy-archive-handoff` | retain | fresh-agent | gpt high | 86 | complete | yes | no | appropriate | decisive | [plan-retain](scenarios/tg01-eleventy-archive-handoff/gpt-high/plan-retain) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) |
| `tg02-fastapi-pagination-handoff` | generated-task | same-agent | glm max | 96 | complete | yes | no | appropriate | decisive | [continuation](scenarios/tg02-fastapi-pagination-handoff/glm-max/continuation) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) |
| `tg02-fastapi-pagination-handoff` | generated-task | same-agent | gpt high | 87 | complete | yes | no | appropriate | decisive | [continuation](scenarios/tg02-fastapi-pagination-handoff/gpt-high/continuation) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) |
| `tg02-fastapi-pagination-handoff` | incomplete | fresh-agent | glm max | 79 | complete | no | yes | appropriate | decisive | [control](scenarios/tg02-fastapi-pagination-handoff/glm-max/control) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) |
| `tg02-fastapi-pagination-handoff` | omit | fresh-agent | glm max | 93 | complete | yes | no | appropriate | decisive | [plan-omit](scenarios/tg02-fastapi-pagination-handoff/glm-max/plan-omit) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) |
| `tg02-fastapi-pagination-handoff` | omit | fresh-agent | gpt high | 85 | complete | yes | no | appropriate | decisive | [plan-omit](scenarios/tg02-fastapi-pagination-handoff/gpt-high/plan-omit) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) |
| `tg02-fastapi-pagination-handoff` | retain | fresh-agent | glm max | 91 | complete | yes | no | appropriate | decisive | [plan-retain](scenarios/tg02-fastapi-pagination-handoff/glm-max/plan-retain) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) |
| `tg02-fastapi-pagination-handoff` | retain | fresh-agent | gpt high | 90 | complete | yes | no | appropriate | decisive | [plan-retain](scenarios/tg02-fastapi-pagination-handoff/gpt-high/plan-retain) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) |
| `tg03-flask-vue-refresh-handoff` | generated-task | same-agent | glm max | 84 | complete | yes | no | appropriate | partial | [continuation](scenarios/tg03-flask-vue-refresh-handoff/glm-max/continuation) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) |
| `tg03-flask-vue-refresh-handoff` | omit | fresh-agent | glm max | 94 | complete | yes | no | appropriate | decisive | [plan-omit](scenarios/tg03-flask-vue-refresh-handoff/glm-max/plan-omit) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) |
| `tg03-flask-vue-refresh-handoff` | omit | fresh-agent | gpt high | 82 | complete | yes | no | appropriate | partial | [plan-omit](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/plan-omit) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) |
| `tg03-flask-vue-refresh-handoff` | retain | fresh-agent | glm max | 92 | complete | yes | no | appropriate | decisive | [plan-retain](scenarios/tg03-flask-vue-refresh-handoff/glm-max/plan-retain) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) |
| `tg03-flask-vue-refresh-handoff` | retain | fresh-agent | gpt high | 79 | complete | yes | no | appropriate | partial | [plan-retain](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/plan-retain) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) |

## Per-scenario results

| Scenario | Cells | Task-creation judgment | Handoff judgment |
|---|---|---|---|
| `tg01-eleventy-archive-handoff` | [glm-max](scenarios/tg01-eleventy-archive-handoff/glm-max/index.md) · [gpt-high](scenarios/tg01-eleventy-archive-handoff/gpt-high/index.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/task-creation/results.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) |
| `tg02-fastapi-pagination-handoff` | [glm-max](scenarios/tg02-fastapi-pagination-handoff/glm-max/index.md) · [gpt-high](scenarios/tg02-fastapi-pagination-handoff/gpt-high/index.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/task-creation/results.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) |
| `tg03-flask-vue-refresh-handoff` | [glm-max](scenarios/tg03-flask-vue-refresh-handoff/glm-max/index.md) · [gpt-high](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/index.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/task-creation/results.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) |
| `tg04-flask-vue-discovery-decomposition` | [glm-max](scenarios/tg04-flask-vue-discovery-decomposition/glm-max/index.md) · [gpt-high](scenarios/tg04-flask-vue-discovery-decomposition/gpt-high/index.md) · [gpt-max](scenarios/tg04-flask-vue-discovery-decomposition/gpt-max/index.md) · [gpt-xhigh](scenarios/tg04-flask-vue-discovery-decomposition/gpt-xhigh/index.md) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-creation/results.md) | — |
| `tg05-fastapi-multi-consumer-decomposition` | [glm-max](scenarios/tg05-fastapi-multi-consumer-decomposition/glm-max/index.md) · [gpt-high](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-high/index.md) · [gpt-max](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-max/index.md) · [gpt-xhigh](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-xhigh/index.md) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-creation/results.md) | — |
| `tg06-eleventy-author-migration-decomposition` | [glm-max](scenarios/tg06-eleventy-author-migration-decomposition/glm-max/index.md) · [gpt-high](scenarios/tg06-eleventy-author-migration-decomposition/gpt-high/index.md) · [gpt-max](scenarios/tg06-eleventy-author-migration-decomposition/gpt-max/index.md) · [gpt-xhigh](scenarios/tg06-eleventy-author-migration-decomposition/gpt-xhigh/index.md) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-creation/results.md) | — |
