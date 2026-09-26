# Task-guidance task-mechanics candidate v2 status

- Labels: `b1v2-r1`, `b1v2-r4`, `b1v2-r6`

| Stage | Expected | Present | Valid | Invalid | Missing |
|---|---:|---:|---:|---:|---:|
| Task creation | 18 | 18 | 18 | 0 | 0 |
| Fresh-agent planning | 12 | 12 | 12 | 0 | 0 |
| Same-agent planning | 6 | 6 | 6 | 0 | 0 |
| Semantic batches | 18 | 18 | — | — | 0 |
| Handoff semantic batches | 19 | 19 | — | — | 0 |
| Negative controls | 1 | 1 | — | — | 0 |
| Provider setup blockers | — | 0 | — | — | — |

## Task-creation semantic quality

| Cohort | Assessments | Overall success | Fragmentation | Phase-only | Layer split | Evidence reownership | Dependency safety | Production crossing |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| All | 18 | 90.0% | 87.0% | 97.2% | 88.9% | 100.0% | 80.6% | 86.1% |
| GLM | 6 | 95.8% | 100.0% | 100.0% | 100.0% | 100.0% | 91.7% | 83.3% |
| GPT | 12 | 87.0% | 80.5% | 95.8% | 83.3% | 100.0% | 75.0% | 87.5% |
| GLM max | 6 | 95.8% | 100.0% | 100.0% | 100.0% | 100.0% | 91.7% | 83.3% |
| GPT high | 6 | 89.8% | 88.8% | 100.0% | 91.7% | 100.0% | 83.3% | 75.0% |
| GPT xhigh | 3 | 85.2% | 77.7% | 83.3% | 83.3% | 100.0% | 66.7% | 100.0% |
| GPT max | 3 | 83.4% | 66.7% | 100.0% | 66.7% | 100.0% | 66.7% | 100.0% |

## Task-creation semantic detail

One row per judgment. Each cohort row above is the average of its rows here; dimension cells read `status (score)`.

| Scenario | Producer | Overall | Fragmentation | Phase-only | Layer split | Evidence reownership | Dependency safety | Production crossing | Run | Judgment | Sample |
|---|---|---:|---|---|---|---|---|---|---|---|---|
| `tg01-eleventy-archive-handoff` | glm max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [glm-max](scenarios/tg01-eleventy-archive-handoff/glm-max) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/task-creation/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | gpt high | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [gpt-high](scenarios/tg01-eleventy-archive-handoff/gpt-high) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/task-creation/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | glm max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [glm-max](scenarios/tg02-fastapi-pagination-handoff/glm-max) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/task-creation/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | gpt high | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [gpt-high](scenarios/tg02-fastapi-pagination-handoff/gpt-high) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/task-creation/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | glm max | 83.3 | none (100) | none (100) | none (100) | none (100) | none (100) | present (0) | [glm-max](scenarios/tg03-flask-vue-refresh-handoff/glm-max) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/task-creation/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | gpt high | 83.3 | none (100) | none (100) | none (100) | none (100) | none (100) | present (0) | [gpt-high](scenarios/tg03-flask-vue-refresh-handoff/gpt-high) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/task-creation/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | glm max | 91.7 | none (100) | none (100) | none (100) | none (100) | partial (50) | none (100) | [glm-max](scenarios/tg04-flask-vue-discovery-decomposition/glm-max) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-creation/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | gpt high | 63.8 | medium (33) | none (100) | partial (50) | none (100) | partial (50) | partial (50) | [gpt-high](scenarios/tg04-flask-vue-discovery-decomposition/gpt-high) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-creation/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | gpt max | 72.2 | medium (33) | none (100) | present (0) | none (100) | none (100) | none (100) | [gpt-max](scenarios/tg04-flask-vue-discovery-decomposition/gpt-max) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-creation/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | gpt xhigh | 72.2 | medium (33) | partial (50) | partial (50) | none (100) | none (100) | none (100) | [gpt-xhigh](scenarios/tg04-flask-vue-discovery-decomposition/gpt-xhigh) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-creation/results.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | glm max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [glm-max](scenarios/tg05-fastapi-multi-consumer-decomposition/glm-max) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-creation/results.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | gpt high | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [gpt-high](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-high) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-creation/results.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | gpt max | 91.7 | none (100) | none (100) | none (100) | none (100) | partial (50) | none (100) | [gpt-max](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-max) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-creation/results.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | gpt xhigh | 91.7 | none (100) | none (100) | none (100) | none (100) | partial (50) | none (100) | [gpt-xhigh](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-xhigh) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-creation/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | glm max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [glm-max](scenarios/tg06-eleventy-author-migration-decomposition/glm-max) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-creation/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | gpt high | 91.7 | none (100) | none (100) | none (100) | none (100) | partial (50) | none (100) | [gpt-high](scenarios/tg06-eleventy-author-migration-decomposition/gpt-high) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-creation/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | gpt max | 86.2 | low (67) | none (100) | none (100) | none (100) | partial (50) | none (100) | [gpt-max](scenarios/tg06-eleventy-author-migration-decomposition/gpt-max) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-creation/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | gpt xhigh | 91.7 | none (100) | none (100) | none (100) | none (100) | partial (50) | none (100) | [gpt-xhigh](scenarios/tg06-eleventy-author-migration-decomposition/gpt-xhigh) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-creation/results.md) | s0 |

## Handoff semantic detail

One row per judgment, across plan variants and stages.

| Scenario | Variant | Stage | Producer | Handoff quality | Plan coverage | Self-contained | Broad rediscovery | Documentation | Testing | Run | Judgment | Sample |
|---|---|---|---|---:|---|---|---|---|---|---|---|---|
| `tg01-eleventy-archive-handoff` | generated-task | same-agent | glm max | 96 | complete | yes | no | appropriate | decisive | [continuation](scenarios/tg01-eleventy-archive-handoff/glm-max/continuation) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | generated-task | same-agent | gpt high | 96 | complete | yes | no | appropriate | decisive | [continuation](scenarios/tg01-eleventy-archive-handoff/gpt-high/continuation) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | omit | fresh-agent | glm max | 94 | complete | yes | no | appropriate | decisive | [plan-omit](scenarios/tg01-eleventy-archive-handoff/glm-max/plan-omit) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | omit | fresh-agent | gpt high | 94 | complete | yes | no | appropriate | decisive | [plan-omit](scenarios/tg01-eleventy-archive-handoff/gpt-high/plan-omit) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | retain | fresh-agent | glm max | 93 | complete | yes | no | appropriate | decisive | [plan-retain](scenarios/tg01-eleventy-archive-handoff/glm-max/plan-retain) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | retain | fresh-agent | gpt high | 93 | complete | yes | no | appropriate | decisive | [plan-retain](scenarios/tg01-eleventy-archive-handoff/gpt-high/plan-retain) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | generated-task | same-agent | glm max | 95 | complete | yes | no | appropriate | decisive | [continuation](scenarios/tg02-fastapi-pagination-handoff/glm-max/continuation) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | generated-task | same-agent | gpt high | 95 | complete | yes | no | appropriate | decisive | [continuation](scenarios/tg02-fastapi-pagination-handoff/gpt-high/continuation) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | incomplete | fresh-agent | glm max | 85 | complete | no | yes | appropriate | decisive | [control](scenarios/tg02-fastapi-pagination-handoff/glm-max/control) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | omit | fresh-agent | glm max | 95 | complete | yes | no | appropriate | decisive | [plan-omit](scenarios/tg02-fastapi-pagination-handoff/glm-max/plan-omit) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | omit | fresh-agent | gpt high | 92 | complete | yes | no | appropriate | decisive | [plan-omit](scenarios/tg02-fastapi-pagination-handoff/gpt-high/plan-omit) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | retain | fresh-agent | glm max | 94 | complete | yes | no | appropriate | decisive | [plan-retain](scenarios/tg02-fastapi-pagination-handoff/glm-max/plan-retain) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | retain | fresh-agent | gpt high | 92 | complete | yes | no | appropriate | decisive | [plan-retain](scenarios/tg02-fastapi-pagination-handoff/gpt-high/plan-retain) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | generated-task | same-agent | glm max | 94 | complete | yes | no | appropriate | decisive | [continuation](scenarios/tg03-flask-vue-refresh-handoff/glm-max/continuation) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | generated-task | same-agent | gpt high | 92 | complete | yes | no | appropriate | decisive | [continuation](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/continuation) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | omit | fresh-agent | glm max | 92 | complete | yes | no | appropriate | decisive | [plan-omit](scenarios/tg03-flask-vue-refresh-handoff/glm-max/plan-omit) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | omit | fresh-agent | gpt high | 90 | complete | yes | no | appropriate | decisive | [plan-omit](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/plan-omit) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | retain | fresh-agent | glm max | 94 | complete | yes | no | appropriate | decisive | [plan-retain](scenarios/tg03-flask-vue-refresh-handoff/glm-max/plan-retain) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | retain | fresh-agent | gpt high | 93 | complete | yes | no | appropriate | decisive | [plan-retain](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/plan-retain) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |

## Per-scenario results

| Scenario | Cells | Task-creation judgment | Handoff judgment |
|---|---|---|---|
| `tg01-eleventy-archive-handoff` | [glm-max](scenarios/tg01-eleventy-archive-handoff/glm-max/index.md) · [gpt-high](scenarios/tg01-eleventy-archive-handoff/gpt-high/index.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/task-creation/results.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) |
| `tg02-fastapi-pagination-handoff` | [glm-max](scenarios/tg02-fastapi-pagination-handoff/glm-max/index.md) · [gpt-high](scenarios/tg02-fastapi-pagination-handoff/gpt-high/index.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/task-creation/results.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) |
| `tg03-flask-vue-refresh-handoff` | [glm-max](scenarios/tg03-flask-vue-refresh-handoff/glm-max/index.md) · [gpt-high](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/index.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/task-creation/results.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) |
| `tg04-flask-vue-discovery-decomposition` | [glm-max](scenarios/tg04-flask-vue-discovery-decomposition/glm-max/index.md) · [gpt-high](scenarios/tg04-flask-vue-discovery-decomposition/gpt-high/index.md) · [gpt-max](scenarios/tg04-flask-vue-discovery-decomposition/gpt-max/index.md) · [gpt-xhigh](scenarios/tg04-flask-vue-discovery-decomposition/gpt-xhigh/index.md) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-creation/results.md) | — |
| `tg05-fastapi-multi-consumer-decomposition` | [glm-max](scenarios/tg05-fastapi-multi-consumer-decomposition/glm-max/index.md) · [gpt-high](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-high/index.md) · [gpt-max](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-max/index.md) · [gpt-xhigh](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-xhigh/index.md) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-creation/results.md) | — |
| `tg06-eleventy-author-migration-decomposition` | [glm-max](scenarios/tg06-eleventy-author-migration-decomposition/glm-max/index.md) · [gpt-high](scenarios/tg06-eleventy-author-migration-decomposition/gpt-high/index.md) · [gpt-max](scenarios/tg06-eleventy-author-migration-decomposition/gpt-max/index.md) · [gpt-xhigh](scenarios/tg06-eleventy-author-migration-decomposition/gpt-xhigh/index.md) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-creation/results.md) | — |
