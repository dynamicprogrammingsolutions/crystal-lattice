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

## Task-creation semantic detail

One row per judgment. Each cohort row above is the average of its rows here; dimension cells read `status (score)`.

| Scenario | Producer | Overall | Fragmentation | Phase-only | Layer split | Evidence reownership | Dependency safety | Production crossing | Run | Judgment |
|---|---|---:|---|---|---|---|---|---|---|---|
| `tg01-eleventy-archive-handoff` | glm max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [glm-max](scenarios/tg01-eleventy-archive-handoff/glm-max) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/task-creation/results.md) |
| `tg01-eleventy-archive-handoff` | gpt high | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [gpt-high](scenarios/tg01-eleventy-archive-handoff/gpt-high) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/task-creation/results.md) |
| `tg02-fastapi-pagination-handoff` | glm max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [glm-max](scenarios/tg02-fastapi-pagination-handoff/glm-max) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/task-creation/results.md) |
| `tg02-fastapi-pagination-handoff` | gpt high | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [gpt-high](scenarios/tg02-fastapi-pagination-handoff/gpt-high) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/task-creation/results.md) |
| `tg03-flask-vue-refresh-handoff` | glm max | 83.3 | none (100) | none (100) | none (100) | none (100) | none (100) | present (0) | [glm-max](scenarios/tg03-flask-vue-refresh-handoff/glm-max) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/task-creation/results.md) |
| `tg03-flask-vue-refresh-handoff` | gpt high | 91.7 | none (100) | none (100) | none (100) | none (100) | none (100) | partial (50) | [gpt-high](scenarios/tg03-flask-vue-refresh-handoff/gpt-high) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/task-creation/results.md) |
| `tg04-flask-vue-discovery-decomposition` | glm max | 91.7 | none (100) | none (100) | none (100) | none (100) | partial (50) | none (100) | [glm-max](scenarios/tg04-flask-vue-discovery-decomposition/glm-max) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-creation/results.md) |
| `tg04-flask-vue-discovery-decomposition` | gpt high | 47.2 | medium (33) | none (100) | present (0) | none (100) | partial (50) | present (0) | [gpt-high](scenarios/tg04-flask-vue-discovery-decomposition/gpt-high) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-creation/results.md) |
| `tg04-flask-vue-discovery-decomposition` | gpt max | 47.2 | medium (33) | none (100) | present (0) | none (100) | partial (50) | present (0) | [gpt-max](scenarios/tg04-flask-vue-discovery-decomposition/gpt-max) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-creation/results.md) |
| `tg04-flask-vue-discovery-decomposition` | gpt xhigh | 47.2 | medium (33) | none (100) | present (0) | none (100) | partial (50) | present (0) | [gpt-xhigh](scenarios/tg04-flask-vue-discovery-decomposition/gpt-xhigh) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-creation/results.md) |
| `tg05-fastapi-multi-consumer-decomposition` | glm max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [glm-max](scenarios/tg05-fastapi-multi-consumer-decomposition/glm-max) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-creation/results.md) |
| `tg05-fastapi-multi-consumer-decomposition` | gpt high | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [gpt-high](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-high) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-creation/results.md) |
| `tg05-fastapi-multi-consumer-decomposition` | gpt max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [gpt-max](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-max) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-creation/results.md) |
| `tg05-fastapi-multi-consumer-decomposition` | gpt xhigh | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [gpt-xhigh](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-xhigh) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-creation/results.md) |
| `tg06-eleventy-author-migration-decomposition` | glm max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [glm-max](scenarios/tg06-eleventy-author-migration-decomposition/glm-max) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-creation/results.md) |
| `tg06-eleventy-author-migration-decomposition` | gpt high | 94.5 | low (67) | none (100) | none (100) | none (100) | none (100) | none (100) | [gpt-high](scenarios/tg06-eleventy-author-migration-decomposition/gpt-high) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-creation/results.md) |
| `tg06-eleventy-author-migration-decomposition` | gpt max | 86.2 | low (67) | none (100) | none (100) | none (100) | partial (50) | none (100) | [gpt-max](scenarios/tg06-eleventy-author-migration-decomposition/gpt-max) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-creation/results.md) |
| `tg06-eleventy-author-migration-decomposition` | gpt xhigh | 77.8 | low (67) | none (100) | none (100) | none (100) | present (0) | none (100) | [gpt-xhigh](scenarios/tg06-eleventy-author-migration-decomposition/gpt-xhigh) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-creation/results.md) |

## Handoff semantic detail

One row per judgment, across plan variants and stages.

| Scenario | Variant | Stage | Producer | Handoff quality | Plan coverage | Self-contained | Broad rediscovery | Documentation | Testing | Run | Judgment |
|---|---|---|---|---:|---|---|---|---|---|---|---|
| `tg01-eleventy-archive-handoff` | generated-task | same-agent | glm max | 94 | complete | yes | no | appropriate | decisive | [continuation](scenarios/tg01-eleventy-archive-handoff/glm-max/continuation) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) |
| `tg01-eleventy-archive-handoff` | generated-task | same-agent | gpt high | 81 | complete | yes | no | appropriate | partial | [continuation](scenarios/tg01-eleventy-archive-handoff/gpt-high/continuation) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) |
| `tg01-eleventy-archive-handoff` | omit | fresh-agent | glm max | 88 | complete | yes | no | appropriate | decisive | [plan-omit](scenarios/tg01-eleventy-archive-handoff/glm-max/plan-omit) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) |
| `tg01-eleventy-archive-handoff` | omit | fresh-agent | gpt high | 78 | complete | yes | no | appropriate | partial | [plan-omit](scenarios/tg01-eleventy-archive-handoff/gpt-high/plan-omit) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) |
| `tg01-eleventy-archive-handoff` | retain | fresh-agent | glm max | 90 | complete | yes | no | appropriate | decisive | [plan-retain](scenarios/tg01-eleventy-archive-handoff/glm-max/plan-retain) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) |
| `tg01-eleventy-archive-handoff` | retain | fresh-agent | gpt high | 84 | complete | yes | no | appropriate | decisive | [plan-retain](scenarios/tg01-eleventy-archive-handoff/gpt-high/plan-retain) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) |
| `tg02-fastapi-pagination-handoff` | generated-task | same-agent | glm max | 95 | complete | yes | no | appropriate | decisive | [continuation](scenarios/tg02-fastapi-pagination-handoff/glm-max/continuation) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) |
| `tg02-fastapi-pagination-handoff` | generated-task | same-agent | gpt high | 86 | complete | yes | no | appropriate | decisive | [continuation](scenarios/tg02-fastapi-pagination-handoff/gpt-high/continuation) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) |
| `tg02-fastapi-pagination-handoff` | incomplete | fresh-agent | glm max | 78 | complete | no | yes | appropriate | decisive | [control](scenarios/tg02-fastapi-pagination-handoff/glm-max/control) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) |
| `tg02-fastapi-pagination-handoff` | omit | fresh-agent | glm max | 91 | complete | yes | no | appropriate | decisive | [plan-omit](scenarios/tg02-fastapi-pagination-handoff/glm-max/plan-omit) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) |
| `tg02-fastapi-pagination-handoff` | omit | fresh-agent | gpt high | 85 | complete | yes | no | appropriate | decisive | [plan-omit](scenarios/tg02-fastapi-pagination-handoff/gpt-high/plan-omit) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) |
| `tg02-fastapi-pagination-handoff` | retain | fresh-agent | glm max | 93 | complete | yes | no | appropriate | decisive | [plan-retain](scenarios/tg02-fastapi-pagination-handoff/glm-max/plan-retain) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) |
| `tg02-fastapi-pagination-handoff` | retain | fresh-agent | gpt high | 88 | complete | yes | no | appropriate | decisive | [plan-retain](scenarios/tg02-fastapi-pagination-handoff/gpt-high/plan-retain) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) |
| `tg03-flask-vue-refresh-handoff` | generated-task | same-agent | glm max | 72 | partial | yes | no | appropriate | partial | [continuation](scenarios/tg03-flask-vue-refresh-handoff/glm-max/continuation) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) |
| `tg03-flask-vue-refresh-handoff` | omit | fresh-agent | glm max | 91 | complete | yes | no | appropriate | decisive | [plan-omit](scenarios/tg03-flask-vue-refresh-handoff/glm-max/plan-omit) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) |
| `tg03-flask-vue-refresh-handoff` | omit | fresh-agent | gpt high | 84 | complete | yes | no | appropriate | partial | [plan-omit](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/plan-omit) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) |
| `tg03-flask-vue-refresh-handoff` | retain | fresh-agent | glm max | 93 | complete | yes | no | appropriate | decisive | [plan-retain](scenarios/tg03-flask-vue-refresh-handoff/glm-max/plan-retain) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) |
| `tg03-flask-vue-refresh-handoff` | retain | fresh-agent | gpt high | 85 | complete | yes | no | appropriate | partial | [plan-retain](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/plan-retain) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) |

## Per-scenario results

| Scenario | Cells | Task-creation judgment | Handoff judgment |
|---|---|---|---|
| `tg01-eleventy-archive-handoff` | [glm-max](scenarios/tg01-eleventy-archive-handoff/glm-max/index.md) · [gpt-high](scenarios/tg01-eleventy-archive-handoff/gpt-high/index.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/task-creation/results.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) |
| `tg02-fastapi-pagination-handoff` | [glm-max](scenarios/tg02-fastapi-pagination-handoff/glm-max/index.md) · [gpt-high](scenarios/tg02-fastapi-pagination-handoff/gpt-high/index.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/task-creation/results.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) |
| `tg03-flask-vue-refresh-handoff` | [glm-max](scenarios/tg03-flask-vue-refresh-handoff/glm-max/index.md) · [gpt-high](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/index.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/task-creation/results.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) |
| `tg04-flask-vue-discovery-decomposition` | [glm-max](scenarios/tg04-flask-vue-discovery-decomposition/glm-max/index.md) · [gpt-high](scenarios/tg04-flask-vue-discovery-decomposition/gpt-high/index.md) · [gpt-max](scenarios/tg04-flask-vue-discovery-decomposition/gpt-max/index.md) · [gpt-xhigh](scenarios/tg04-flask-vue-discovery-decomposition/gpt-xhigh/index.md) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-creation/results.md) | — |
| `tg05-fastapi-multi-consumer-decomposition` | [glm-max](scenarios/tg05-fastapi-multi-consumer-decomposition/glm-max/index.md) · [gpt-high](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-high/index.md) · [gpt-max](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-max/index.md) · [gpt-xhigh](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-xhigh/index.md) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-creation/results.md) | — |
| `tg06-eleventy-author-migration-decomposition` | [glm-max](scenarios/tg06-eleventy-author-migration-decomposition/glm-max/index.md) · [gpt-high](scenarios/tg06-eleventy-author-migration-decomposition/gpt-high/index.md) · [gpt-max](scenarios/tg06-eleventy-author-migration-decomposition/gpt-max/index.md) · [gpt-xhigh](scenarios/tg06-eleventy-author-migration-decomposition/gpt-xhigh/index.md) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-creation/results.md) | — |
