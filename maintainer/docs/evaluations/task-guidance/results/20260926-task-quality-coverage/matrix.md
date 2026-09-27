# Task-guidance task-mechanics candidate v3 with quality coverage status

- Labels: `b1v3-r1`, `b1v3-r4`

| Stage | Expected | Present | Valid | Invalid | Missing |
|---|---:|---:|---:|---:|---:|
| Task creation | 18 | 18 | 18 | 0 | 0 |
| Fresh-agent planning | 12 | 12 | 12 | 0 | 0 |
| Same-agent planning | 6 | 6 | 6 | 0 | 0 |
| Semantic batches | 18 | 18 | — | — | 0 |
| Handoff semantic batches | 25 | 25 | — | — | 0 |
| Negative controls | 1 | 1 | — | — | 0 |
| Provider setup blockers | — | 0 | — | — | — |

## Invalid records — provider failures

Run-level provider errors (outages, authentication), not guidance-behavior findings.

- `tg03-flask-vue-refresh-handoff:gpt:high`: run failure: None, ("OpenAI Responses stream failed: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-svcac***********************************************************************************************************************************************************fvMA. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_api_key'}}",)
- `tg01-eleventy-archive-handoff:gpt:high`: run failure: None, ("OpenAI Responses stream failed: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-svcac***********************************************************************************************************************************************************fvMA. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_api_key'}}",)
- `tg02-fastapi-pagination-handoff:gpt:high`: run failure: None, ("OpenAI Responses stream failed: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-svcac***********************************************************************************************************************************************************fvMA. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_api_key'}}",)

## Task-creation semantic quality

| Cohort | Assessments | Overall success | Fragmentation | Phase-only | Layer split | Evidence reownership | Dependency safety | Production crossing |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| All | 18 | 93.2% | 81.5% | 100.0% | 97.2% | 97.2% | 86.1% | 97.2% |
| GLM | 6 | 96.3% | 94.5% | 100.0% | 100.0% | 100.0% | 91.7% | 91.7% |
| GPT | 12 | 91.7% | 75.0% | 100.0% | 95.8% | 95.8% | 83.3% | 100.0% |
| GLM max | 6 | 96.3% | 94.5% | 100.0% | 100.0% | 100.0% | 91.7% | 91.7% |
| GPT high | 6 | 94.9% | 77.8% | 100.0% | 100.0% | 100.0% | 91.7% | 100.0% |
| GPT xhigh | 3 | 85.2% | 77.7% | 100.0% | 83.3% | 83.3% | 66.7% | 100.0% |
| GPT max | 3 | 91.7% | 66.7% | 100.0% | 100.0% | 100.0% | 83.3% | 100.0% |

## Task-creation semantic detail

One row per judgment. Each cohort row above is the average of its rows here; dimension cells read `status (score)`.

| Scenario | Producer | Overall | Fragmentation | Phase-only | Layer split | Evidence reownership | Dependency safety | Production crossing | Run | Judgment | Sample |
|---|---|---:|---|---|---|---|---|---|---|---|---|
| `tg01-eleventy-archive-handoff` | glm max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg01-eleventy-archive-handoff/glm-max/s0) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/task-creation/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | gpt high | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg01-eleventy-archive-handoff/gpt-high/s0) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/task-creation/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | glm max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/task-creation/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | gpt high | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg02-fastapi-pagination-handoff/gpt-high/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/task-creation/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | glm max | 91.7 | none (100) | none (100) | none (100) | none (100) | none (100) | partial (50) | [s0](scenarios/tg03-flask-vue-refresh-handoff/glm-max/s0) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/task-creation/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | gpt high | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/s0) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/task-creation/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | glm max | 94.5 | low (67) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg04-flask-vue-discovery-decomposition/glm-max/s0) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-creation/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | gpt high | 83.3 | high (0) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg04-flask-vue-discovery-decomposition/gpt-high/s0) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-creation/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | gpt max | 83.3 | high (0) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg04-flask-vue-discovery-decomposition/gpt-max/s0) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-creation/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | gpt xhigh | 72.2 | medium (33) | none (100) | partial (50) | partial (50) | none (100) | none (100) | [s0](scenarios/tg04-flask-vue-discovery-decomposition/gpt-xhigh/s0) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-creation/results.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | glm max | 91.7 | none (100) | none (100) | none (100) | none (100) | partial (50) | none (100) | [s0](scenarios/tg05-fastapi-multi-consumer-decomposition/glm-max/s0) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-creation/results.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | gpt high | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-high/s0) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-creation/results.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | gpt max | 91.7 | none (100) | none (100) | none (100) | none (100) | partial (50) | none (100) | [s0](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-max/s0) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-creation/results.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | gpt xhigh | 91.7 | none (100) | none (100) | none (100) | none (100) | partial (50) | none (100) | [s0](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-xhigh/s0) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-creation/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | glm max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg06-eleventy-author-migration-decomposition/glm-max/s0) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-creation/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | gpt high | 86.2 | low (67) | none (100) | none (100) | none (100) | partial (50) | none (100) | [s0](scenarios/tg06-eleventy-author-migration-decomposition/gpt-high/s0) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-creation/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | gpt max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg06-eleventy-author-migration-decomposition/gpt-max/s0) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-creation/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | gpt xhigh | 91.7 | none (100) | none (100) | none (100) | none (100) | partial (50) | none (100) | [s0](scenarios/tg06-eleventy-author-migration-decomposition/gpt-xhigh/s0) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-creation/results.md) | s0 |

## Handoff semantic detail

One row per judgment, across plan variants and stages.

| Scenario | Variant | Stage | Producer | Handoff quality | Plan coverage | Self-contained | Broad rediscovery | Documentation | Testing | Run | Judgment | Sample |
|---|---|---|---|---:|---|---|---|---|---|---|---|---|
| `tg01-eleventy-archive-handoff` | generated-file | fresh-agent | glm max | 95 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg01-eleventy-archive-handoff/glm-max/generated-plan/s0) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | generated-file | fresh-agent | gpt high | 91 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg01-eleventy-archive-handoff/gpt-high/generated-plan/s0) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | generated-task | same-agent | glm max | 96 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg01-eleventy-archive-handoff/glm-max/continuation/s0) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | generated-task | same-agent | gpt high | 96 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg01-eleventy-archive-handoff/gpt-high/continuation/s0) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | omit | fresh-agent | glm max | 95 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg01-eleventy-archive-handoff/glm-max/plan-omit/s0) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | omit | fresh-agent | gpt high | 92 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg01-eleventy-archive-handoff/gpt-high/plan-omit/s0) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | retain | fresh-agent | glm max | 94 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg01-eleventy-archive-handoff/glm-max/plan-retain/s0) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | retain | fresh-agent | gpt high | 95 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg01-eleventy-archive-handoff/gpt-high/plan-retain/s0) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | generated-file | fresh-agent | glm max | 94 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/generated-plan/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | generated-file | fresh-agent | gpt high | 94 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg02-fastapi-pagination-handoff/gpt-high/generated-plan/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | generated-task | same-agent | glm max | 94 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/continuation/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | generated-task | same-agent | gpt high | 92 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg02-fastapi-pagination-handoff/gpt-high/continuation/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | incomplete | fresh-agent | glm max | 80 | complete | no | yes | appropriate | decisive | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/control/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | omit | fresh-agent | glm max | 93 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/plan-omit/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | omit | fresh-agent | gpt high | 94 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg02-fastapi-pagination-handoff/gpt-high/plan-omit/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | retain | fresh-agent | glm max | 95 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/plan-retain/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | retain | fresh-agent | gpt high | 91 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg02-fastapi-pagination-handoff/gpt-high/plan-retain/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | generated-file | fresh-agent | glm max | 96 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg03-flask-vue-refresh-handoff/glm-max/generated-plan/s0) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | generated-file | fresh-agent | gpt high | 93 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/generated-plan/s0) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | generated-task | same-agent | glm max | 93 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg03-flask-vue-refresh-handoff/glm-max/continuation/s0) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | generated-task | same-agent | gpt high | 90 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/continuation/s0) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | omit | fresh-agent | glm max | 95 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg03-flask-vue-refresh-handoff/glm-max/plan-omit/s0) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | omit | fresh-agent | gpt high | 93 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/plan-omit/s0) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | retain | fresh-agent | glm max | 94 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg03-flask-vue-refresh-handoff/glm-max/plan-retain/s0) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | retain | fresh-agent | gpt high | 94 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/plan-retain/s0) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |

## Task-file quality

Share of top grades (complete / justified / fits) per dimension; `n` is the judged subjects in the cohort.

| Cohort | n | Top grades overall | design | context | findability | placement | justification | kind-fit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| All | 18 | 88% | 78% | 72% | 100% | 100% | 89% | 89% |
| GLM | 6 | 97% | 100% | 83% | 100% | 100% | 100% | 100% |
| GPT | 12 | 83% | 67% | 67% | 100% | 100% | 83% | 83% |
| glm max | 6 | 97% | 100% | 83% | 100% | 100% | 100% | 100% |
| gpt high | 6 | 89% | 83% | 83% | 100% | 100% | 83% | 83% |
| gpt max | 3 | 78% | 67% | 67% | 100% | 100% | 67% | 67% |
| gpt xhigh | 3 | 78% | 33% | 33% | 100% | 100% | 100% | 100% |

## Task-file quality detail

One row per judgment; non-top grades are the findings to read.

| Scenario | Producer | Kind | design | context | findability | placement | justification | kind-fit | Subject | Sample |
|---|---|---|---|---|---|---|---|---|---|---|
| `tg01-eleventy-archive-handoff` | glm max | development | complete | complete | complete | complete | justified | fits | [assessment](scenarios/tg01-eleventy-archive-handoff/glm-max/s0/assessment.md) | s0 |
| `tg01-eleventy-archive-handoff` | gpt high | development | complete | complete | complete | complete | justified | fits | [assessment](scenarios/tg01-eleventy-archive-handoff/gpt-high/s0/assessment.md) | s0 |
| `tg02-fastapi-pagination-handoff` | glm max | development | complete | complete | complete | complete | justified | fits | [assessment](scenarios/tg02-fastapi-pagination-handoff/glm-max/s0/assessment.md) | s0 |
| `tg02-fastapi-pagination-handoff` | gpt high | development | complete | partial | complete | complete | justified | fits | [assessment](scenarios/tg02-fastapi-pagination-handoff/gpt-high/s0/assessment.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | glm max | development | complete | complete | complete | complete | justified | fits | [assessment](scenarios/tg03-flask-vue-refresh-handoff/glm-max/s0/assessment.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | gpt high | development | complete | complete | complete | complete | justified | fits | [assessment](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/s0/assessment.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | glm max | development | complete | partial | complete | complete | justified | fits | [assessment](scenarios/tg04-flask-vue-discovery-decomposition/glm-max/s0/assessment.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | gpt max | development | partial | partial | complete | complete | fabricated | missing | [assessment](scenarios/tg04-flask-vue-discovery-decomposition/gpt-max/s0/assessment.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | gpt high | development | complete | complete | complete | complete | justified | fits | [assessment](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-high/s0/assessment.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | gpt xhigh | development | complete | complete | complete | complete | justified | fits | [assessment](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-xhigh/s0/assessment.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | gpt max | development | complete | complete | complete | complete | justified | fits | [assessment](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-max/s0/assessment.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | glm max | development | complete | complete | complete | complete | justified | fits | [assessment](scenarios/tg06-eleventy-author-migration-decomposition/glm-max/s0/assessment.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | gpt high | development | complete | complete | complete | complete | justified | fits | [assessment](scenarios/tg06-eleventy-author-migration-decomposition/gpt-high/s0/assessment.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | gpt xhigh | development | partial | partial | complete | complete | justified | fits | [assessment](scenarios/tg06-eleventy-author-migration-decomposition/gpt-xhigh/s0/assessment.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | gpt max | development | complete | complete | complete | complete | justified | fits | [assessment](scenarios/tg06-eleventy-author-migration-decomposition/gpt-max/s0/assessment.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | gpt high | other | partial | complete | complete | complete | fabricated | missing | [assessment](scenarios/tg04-flask-vue-discovery-decomposition/gpt-high/s0/assessment.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | gpt xhigh | development | partial | partial | complete | complete | justified | fits | [assessment](scenarios/tg04-flask-vue-discovery-decomposition/gpt-xhigh/s0/assessment.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | glm max | development | complete | complete | complete | complete | justified | fits | [assessment](scenarios/tg05-fastapi-multi-consumer-decomposition/glm-max/s0/assessment.md) | s0 |

## Per-scenario results

| Scenario | Numbers | Cells | Task-creation | Handoff | Quality |
|---|---|---|---|---|---|
| `tg01-eleventy-archive-handoff` | — | [glm-max](scenarios/tg01-eleventy-archive-handoff/glm-max/index.md) · [gpt-high](scenarios/tg01-eleventy-archive-handoff/gpt-high/index.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/task-creation/results.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/task-quality/results.md) |
| `tg02-fastapi-pagination-handoff` | — | [glm-max](scenarios/tg02-fastapi-pagination-handoff/glm-max/index.md) · [gpt-high](scenarios/tg02-fastapi-pagination-handoff/gpt-high/index.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/task-creation/results.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/task-quality/results.md) |
| `tg03-flask-vue-refresh-handoff` | — | [glm-max](scenarios/tg03-flask-vue-refresh-handoff/glm-max/index.md) · [gpt-high](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/index.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/task-creation/results.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/task-quality/results.md) |
| `tg04-flask-vue-discovery-decomposition` | — | [glm-max](scenarios/tg04-flask-vue-discovery-decomposition/glm-max/index.md) · [gpt-high](scenarios/tg04-flask-vue-discovery-decomposition/gpt-high/index.md) · [gpt-max](scenarios/tg04-flask-vue-discovery-decomposition/gpt-max/index.md) · [gpt-xhigh](scenarios/tg04-flask-vue-discovery-decomposition/gpt-xhigh/index.md) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-creation/results.md) | — | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-quality/results.md) |
| `tg05-fastapi-multi-consumer-decomposition` | — | [glm-max](scenarios/tg05-fastapi-multi-consumer-decomposition/glm-max/index.md) · [gpt-high](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-high/index.md) · [gpt-max](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-max/index.md) · [gpt-xhigh](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-xhigh/index.md) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-creation/results.md) | — | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-quality/results.md) |
| `tg06-eleventy-author-migration-decomposition` | — | [glm-max](scenarios/tg06-eleventy-author-migration-decomposition/glm-max/index.md) · [gpt-high](scenarios/tg06-eleventy-author-migration-decomposition/gpt-high/index.md) · [gpt-max](scenarios/tg06-eleventy-author-migration-decomposition/gpt-max/index.md) · [gpt-xhigh](scenarios/tg06-eleventy-author-migration-decomposition/gpt-xhigh/index.md) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-creation/results.md) | — | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-quality/results.md) |
