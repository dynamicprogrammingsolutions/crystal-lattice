# Task-guidance file fidelity and readability rework baseline status

- Labels: `b1v3-k1`, `b1v3-r1`

| Stage | Expected | Present | Valid | Invalid | Missing |
|---|---:|---:|---:|---:|---:|
| Task creation | 26 | 26 | 26 | 0 | 0 |
| Fresh-agent planning | 12 | 12 | 12 | 0 | 0 |
| Same-agent planning | 6 | 6 | 3 | 3 | 0 |
| Semantic batches | 26 | 26 | — | — | 0 |
| Handoff semantic batches | 25 | 22 | — | — | 3 |
| Negative controls | 1 | 1 | — | — | 0 |
| Plan-content judgments | 25 | 22 | — | — | 3 |
| File-fidelity judgments | 26 | 26 | — | — | 0 |
| File-readability judgments | 26 | 26 | — | — | 0 |
| Provider setup blockers | — | 0 | — | — | — |

## Invalid records — validity failures

- `tg07-eleventy-decided-work-tracking:glm:max`: execution-plan expectation violated: tasks/20260926-blog-archive-page-size.md: execution plan present without a draft status
- `tg10-flask-vue-interface-copy:gpt:high`: no task files were produced

## Invalid records — provider failures

Run-level provider errors (outages, authentication), not guidance-behavior findings.

- `tg03-flask-vue-refresh-handoff:gpt:high`: run failure: None, ("OpenAI Responses stream failed: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-svcac***********************************************************************************************************************************************************fvMA. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_api_key'}}",)
- `tg01-eleventy-archive-handoff:gpt:high`: run failure: None, ("OpenAI Responses stream failed: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-svcac***********************************************************************************************************************************************************fvMA. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_api_key'}}",)
- `tg02-fastapi-pagination-handoff:gpt:high`: run failure: None, ("OpenAI Responses stream failed: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-svcac***********************************************************************************************************************************************************fvMA. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_api_key'}}",)

## Task-creation semantic quality

| Cohort | Assessments | Overall success | Fragmentation | Phase-only | Layer split | Evidence reownership | Dependency safety | Production crossing |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| All | 28 | 95.6% | 88.1% | 100.0% | 98.2% | 98.2% | 91.1% | 98.2% |
| GLM | 11 | 98.0% | 97.0% | 100.0% | 100.0% | 100.0% | 95.5% | 95.5% |
| GPT | 17 | 94.1% | 82.4% | 100.0% | 97.1% | 97.1% | 88.2% | 100.0% |
| GLM max | 11 | 98.0% | 97.0% | 100.0% | 100.0% | 100.0% | 95.5% | 95.5% |
| GPT high | 11 | 97.2% | 87.9% | 100.0% | 100.0% | 100.0% | 95.5% | 100.0% |
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
| `tg07-eleventy-decided-work-tracking` | glm max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg07-eleventy-decided-work-tracking/glm-max/s0) | [results](scenarios/tg07-eleventy-decided-work-tracking/assessment/task-creation/results.md) | s0 |
| `tg07-eleventy-decided-work-tracking` | glm max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s1](scenarios/tg07-eleventy-decided-work-tracking/glm-max/s1) | [results](scenarios/tg07-eleventy-decided-work-tracking/assessment/task-creation/results.md) | s1 |
| `tg07-eleventy-decided-work-tracking` | gpt high | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg07-eleventy-decided-work-tracking/gpt-high/s0) | [results](scenarios/tg07-eleventy-decided-work-tracking/assessment/task-creation/results.md) | s0 |
| `tg08-eleventy-contributor-docs` | glm max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg08-eleventy-contributor-docs/glm-max/s0) | [results](scenarios/tg08-eleventy-contributor-docs/assessment/task-creation/results.md) | s0 |
| `tg08-eleventy-contributor-docs` | gpt high | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg08-eleventy-contributor-docs/gpt-high/s0) | [results](scenarios/tg08-eleventy-contributor-docs/assessment/task-creation/results.md) | s0 |
| `tg09-flask-vue-deployment-runbook` | glm max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg09-flask-vue-deployment-runbook/glm-max/s0) | [results](scenarios/tg09-flask-vue-deployment-runbook/assessment/task-creation/results.md) | s0 |
| `tg09-flask-vue-deployment-runbook` | gpt high | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg09-flask-vue-deployment-runbook/gpt-high/s0) | [results](scenarios/tg09-flask-vue-deployment-runbook/assessment/task-creation/results.md) | s0 |
| `tg10-flask-vue-interface-copy` | glm max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg10-flask-vue-interface-copy/glm-max/s0) | [results](scenarios/tg10-flask-vue-interface-copy/assessment/task-creation/results.md) | s0 |
| `tg10-flask-vue-interface-copy` | gpt high | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg10-flask-vue-interface-copy/gpt-high/s0) | [results](scenarios/tg10-flask-vue-interface-copy/assessment/task-creation/results.md) | s0 |
| `tg10-flask-vue-interface-copy` | gpt high | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s1](scenarios/tg10-flask-vue-interface-copy/gpt-high/s1) | [results](scenarios/tg10-flask-vue-interface-copy/assessment/task-creation/results.md) | s1 |

## Handoff semantic detail

One row per judgment, across plan variants and stages.

| Scenario | Variant | Stage | Producer | Handoff quality | Plan coverage | Self-contained | Broad rediscovery | Documentation | Testing | Run | Judgment | Sample |
|---|---|---|---|---:|---|---|---|---|---|---|---|---|
| `tg01-eleventy-archive-handoff` | generated-file | fresh-agent | glm max | 95 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg01-eleventy-archive-handoff/glm-max/generated-plan/s0) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | generated-file | fresh-agent | gpt high | 91 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg01-eleventy-archive-handoff/gpt-high/generated-plan/s0) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | generated-task | same-agent | glm max | 96 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg01-eleventy-archive-handoff/glm-max/continuation/s0) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | omit | fresh-agent | glm max | 95 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg01-eleventy-archive-handoff/glm-max/plan-omit/s0) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | omit | fresh-agent | gpt high | 92 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg01-eleventy-archive-handoff/gpt-high/plan-omit/s0) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | retain | fresh-agent | glm max | 94 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg01-eleventy-archive-handoff/glm-max/plan-retain/s0) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | retain | fresh-agent | gpt high | 95 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg01-eleventy-archive-handoff/gpt-high/plan-retain/s0) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | generated-file | fresh-agent | glm max | 94 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/generated-plan/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | generated-file | fresh-agent | gpt high | 94 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg02-fastapi-pagination-handoff/gpt-high/generated-plan/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | generated-task | same-agent | glm max | 94 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/continuation/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | incomplete | fresh-agent | glm max | 80 | complete | no | yes | appropriate | decisive | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/control/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | omit | fresh-agent | glm max | 93 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/plan-omit/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | omit | fresh-agent | gpt high | 94 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg02-fastapi-pagination-handoff/gpt-high/plan-omit/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | retain | fresh-agent | glm max | 95 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/plan-retain/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | retain | fresh-agent | gpt high | 91 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg02-fastapi-pagination-handoff/gpt-high/plan-retain/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | generated-file | fresh-agent | glm max | 96 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg03-flask-vue-refresh-handoff/glm-max/generated-plan/s0) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | generated-file | fresh-agent | gpt high | 93 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/generated-plan/s0) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | generated-task | same-agent | glm max | 93 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg03-flask-vue-refresh-handoff/glm-max/continuation/s0) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | omit | fresh-agent | glm max | 95 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg03-flask-vue-refresh-handoff/glm-max/plan-omit/s0) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | omit | fresh-agent | gpt high | 93 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/plan-omit/s0) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | retain | fresh-agent | glm max | 94 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg03-flask-vue-refresh-handoff/glm-max/plan-retain/s0) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | retain | fresh-agent | gpt high | 94 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/plan-retain/s0) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |

## Task-file quality

Share of top grades (complete / justified / fits) per dimension; `n` is the judged subjects in the cohort.

| Cohort | n | Top grades overall | design | context | findability | placement | justification | kind-fit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| All | 28 | 88% | 79% | 82% | 100% | 100% | 75% | 93% |
| GLM | 11 | 89% | 82% | 91% | 100% | 100% | 64% | 100% |
| GPT | 17 | 87% | 76% | 76% | 100% | 100% | 82% | 88% |
| glm max | 11 | 89% | 82% | 91% | 100% | 100% | 64% | 100% |
| gpt high | 11 | 92% | 91% | 91% | 100% | 100% | 82% | 91% |
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
| `tg07-eleventy-decided-work-tracking` | gpt high | other | complete | complete | complete | complete | not_applicable | fits | [assessment](scenarios/tg07-eleventy-decided-work-tracking/gpt-high/s0/assessment.md) | s0 |
| `tg08-eleventy-contributor-docs` | glm max | documentation | complete | complete | complete | complete | justified | fits | [assessment](scenarios/tg08-eleventy-contributor-docs/glm-max/s0/assessment.md) | s0 |
| `tg08-eleventy-contributor-docs` | gpt high | documentation | complete | complete | complete | complete | justified | fits | [assessment](scenarios/tg08-eleventy-contributor-docs/gpt-high/s0/assessment.md) | s0 |
| `tg09-flask-vue-deployment-runbook` | glm max | operations | partial | complete | complete | complete | not_applicable | fits | [assessment](scenarios/tg09-flask-vue-deployment-runbook/glm-max/s0/assessment.md) | s0 |
| `tg09-flask-vue-deployment-runbook` | gpt high | operations | complete | complete | complete | complete | justified | fits | [assessment](scenarios/tg09-flask-vue-deployment-runbook/gpt-high/s0/assessment.md) | s0 |
| `tg10-flask-vue-interface-copy` | glm max | content | poor | complete | complete | complete | not_applicable | fits | [assessment](scenarios/tg10-flask-vue-interface-copy/glm-max/s0/assessment.md) | s0 |
| `tg10-flask-vue-interface-copy` | gpt high | content | complete | complete | complete | complete | justified | fits | [assessment](scenarios/tg10-flask-vue-interface-copy/gpt-high/s0/assessment.md) | s0 |
| `tg10-flask-vue-interface-copy` | gpt high | content | complete | complete | complete | complete | justified | fits | [assessment](scenarios/tg10-flask-vue-interface-copy/gpt-high/s1/assessment.md) | s1 |
| `tg07-eleventy-decided-work-tracking` | glm max | other | complete | complete | complete | complete | not_applicable | fits | [assessment](scenarios/tg07-eleventy-decided-work-tracking/glm-max/s0/assessment.md) | s0 |
| `tg07-eleventy-decided-work-tracking` | glm max | documentation | complete | complete | complete | complete | not_applicable | fits | [assessment](scenarios/tg07-eleventy-decided-work-tracking/glm-max/s1/assessment.md) | s1 |

## Presented-plan content

Top-grade share per requirement, by the variant of the task file the presenting agent worked from; `n` is the judged plans.

| Requirement | retain | omit | incomplete | generated-task | generated-file |
|---|---:|---:|---:|---:|---:|
| GENERIC-1 | 100% | 100% | 100% | 100% | 100% |
| GENERIC-10 | 100% | 100% | 100% | 100% | 100% |
| GENERIC-2 | 100% | 100% | 100% | 100% | 100% |
| GENERIC-3 | 100% | 100% | 100% | 100% | 100% |
| GENERIC-4 | 50% | 100% | 100% | 100% | 83% |
| GENERIC-5 | 50% | 50% | 100% | 67% | 50% |
| GENERIC-6 | 0% | 33% | 0% | 33% | 17% |
| GENERIC-7 | 0% | 17% | 100% | 67% | 33% |
| GENERIC-8 | 100% | 100% | 100% | 100% | 100% |
| GENERIC-9 | 100% | 100% | 100% | 100% | 67% |
| PLAN-1 | 83% | 83% | 100% | 100% | 100% |
| PLAN-2 | 100% | 100% | 100% | 100% | 100% |
| PLAN-3 | 100% | 100% | 100% | 100% | 83% |
| PLAN-4 | 100% | 100% | 100% | 100% | 100% |
| PLAN-5 | 100% | 100% | 100% | 100% | 100% |
| PLAN-6 | 100% | 100% | — | 100% | 100% |
| PLAN-7 | 100% | 100% | — | 100% | 100% |

| Cohort | n | Mean coverage |
|---|---:|---:|
| retain | 6 | 79% |
| omit | 6 | 86% |
| incomplete | 1 | 93% |
| generated-task | 3 | 92% |
| generated-file | 6 | 83% |
| All | 0 | — |

## Presented-plan content detail

One row per judgment; the subject link opens the judged plan's grade summary.

| Scenario | Variant | Producer | Coverage | Non-top requirements | Missed | Subject | Judgment | Sample |
|---|---|---|---:|---|---:|---|---|---|
| `tg01-eleventy-archive-handoff` | generated-file | glm max | 76% | GENERIC-5, GENERIC-6, GENERIC-7, GENERIC-9 | 0 | [s0](scenarios/tg01-eleventy-archive-handoff/glm-max/generated-plan/s0/assessment.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/plan-content/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | generated-file | gpt high | 88% | GENERIC-6, GENERIC-7 | 0 | [s0](scenarios/tg01-eleventy-archive-handoff/gpt-high/generated-plan/s0/assessment.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/plan-content/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | generated-task | glm max | 88% | GENERIC-6, GENERIC-7 | 0 | [s0](scenarios/tg01-eleventy-archive-handoff/glm-max/continuation/s0/assessment.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/plan-content/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | omit | glm max | 100% | — | 0 | [s0](scenarios/tg01-eleventy-archive-handoff/glm-max/plan-omit/s0/assessment.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/plan-content/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | omit | gpt high | 82% | GENERIC-5, GENERIC-6, GENERIC-7 | 0 | [s0](scenarios/tg01-eleventy-archive-handoff/gpt-high/plan-omit/s0/assessment.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/plan-content/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | retain | glm max | 82% | GENERIC-5, GENERIC-6, GENERIC-7 | 0 | [s0](scenarios/tg01-eleventy-archive-handoff/glm-max/plan-retain/s0/assessment.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/plan-content/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | retain | gpt high | 76% | GENERIC-4, GENERIC-5, GENERIC-6, GENERIC-7 | 0 | [s0](scenarios/tg01-eleventy-archive-handoff/gpt-high/plan-retain/s0/assessment.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/plan-content/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | generated-file | glm max | 80% | GENERIC-6, GENERIC-7, GENERIC-9 | 0 | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/generated-plan/s0/assessment.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/plan-content/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | generated-file | gpt high | 87% | GENERIC-5, GENERIC-6 | 0 | [s0](scenarios/tg02-fastapi-pagination-handoff/gpt-high/generated-plan/s0/assessment.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/plan-content/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | generated-task | glm max | 87% | GENERIC-5, GENERIC-6 | 0 | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/continuation/s0/assessment.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/plan-content/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | incomplete | glm max | 93% | GENERIC-6 | 0 | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/control/s0/assessment.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/plan-content/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | omit | glm max | 87% | GENERIC-6, GENERIC-7 | 0 | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/plan-omit/s0/assessment.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/plan-content/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | omit | gpt high | 73% | GENERIC-5, GENERIC-6, GENERIC-7, PLAN-1 | 0 | [s0](scenarios/tg02-fastapi-pagination-handoff/gpt-high/plan-omit/s0/assessment.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/plan-content/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | retain | glm max | 80% | GENERIC-6, GENERIC-7, PLAN-1 | 0 | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/plan-retain/s0/assessment.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/plan-content/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | retain | gpt high | 73% | GENERIC-4, GENERIC-5, GENERIC-6, GENERIC-7 | 0 | [s0](scenarios/tg02-fastapi-pagination-handoff/gpt-high/plan-retain/s0/assessment.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/plan-content/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | generated-file | glm max | 100% | — | 0 | [s0](scenarios/tg03-flask-vue-refresh-handoff/glm-max/generated-plan/s0/assessment.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/plan-content/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | generated-file | gpt high | 64% | GENERIC-4, GENERIC-5, GENERIC-6, GENERIC-7, PLAN-3 | 0 | [s0](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/generated-plan/s0/assessment.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/plan-content/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | generated-task | glm max | 100% | — | 0 | [s0](scenarios/tg03-flask-vue-refresh-handoff/glm-max/continuation/s0/assessment.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/plan-content/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | omit | glm max | 93% | GENERIC-7 | 0 | [s0](scenarios/tg03-flask-vue-refresh-handoff/glm-max/plan-omit/s0/assessment.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/plan-content/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | omit | gpt high | 79% | GENERIC-5, GENERIC-6, GENERIC-7 | 0 | [s0](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/plan-omit/s0/assessment.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/plan-content/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | retain | glm max | 86% | GENERIC-6, GENERIC-7 | 0 | [s0](scenarios/tg03-flask-vue-refresh-handoff/glm-max/plan-retain/s0/assessment.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/plan-content/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | retain | gpt high | 79% | GENERIC-4, GENERIC-6, GENERIC-7 | 0 | [s0](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/plan-retain/s0/assessment.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/plan-content/results.md) | s0 |

## Task-file fidelity

Share of top grades (complete / justified / fits) per dimension; `n` is the judged subjects in the cohort.

| Cohort | n | Top grades overall | design | context | placement | justification | kind-fit |
|---|---:|---:|---:|---:|---:|---:|---:|
| All | 28 | 91% | 89% | 86% | 96% | 82% | 100% |
| GLM | 11 | 89% | 91% | 91% | 100% | 64% | 100% |
| GPT | 17 | 92% | 88% | 82% | 94% | 94% | 100% |
| glm max | 11 | 89% | 91% | 91% | 100% | 64% | 100% |
| gpt high | 11 | 93% | 91% | 91% | 91% | 91% | 100% |
| gpt max | 3 | 93% | 100% | 67% | 100% | 100% | 100% |
| gpt xhigh | 3 | 87% | 67% | 67% | 100% | 100% | 100% |

Mistakes harvested across all judgments: 45.

## Task-file fidelity detail

| Scenario | Producer | design | context | placement | justification | kind-fit | Mistakes | Subject | Judgment | Sample |
|---|---|---|---|---|---|---|---:|---|---|---|
| `tg01-eleventy-archive-handoff` | glm max | complete | complete | complete | justified | fits | 0 | [s0](scenarios/tg01-eleventy-archive-handoff/glm-max/s0/assessment.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/file-fidelity/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | gpt high | complete | complete | complete | justified | fits | 0 | [s0](scenarios/tg01-eleventy-archive-handoff/gpt-high/s0/assessment.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/file-fidelity/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | glm max | complete | complete | complete | justified | fits | 1 | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/s0/assessment.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/file-fidelity/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | gpt high | complete | complete | complete | justified | fits | 2 | [s0](scenarios/tg02-fastapi-pagination-handoff/gpt-high/s0/assessment.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/file-fidelity/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | glm max | complete | complete | complete | justified | fits | 1 | [s0](scenarios/tg03-flask-vue-refresh-handoff/glm-max/s0/assessment.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/file-fidelity/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | gpt high | complete | partial | complete | justified | fits | 2 | [s0](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/s0/assessment.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/file-fidelity/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | glm max | complete | partial | complete | justified | fits | 4 | [s0](scenarios/tg04-flask-vue-discovery-decomposition/glm-max/s0/assessment.md) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/file-fidelity/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | gpt high | complete | complete | complete | justified | fits | 3 | [s0](scenarios/tg04-flask-vue-discovery-decomposition/gpt-high/s0/assessment.md) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/file-fidelity/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | gpt max | complete | partial | complete | justified | fits | 5 | [s0](scenarios/tg04-flask-vue-discovery-decomposition/gpt-max/s0/assessment.md) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/file-fidelity/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | gpt xhigh | complete | complete | complete | justified | fits | 3 | [s0](scenarios/tg04-flask-vue-discovery-decomposition/gpt-xhigh/s0/assessment.md) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/file-fidelity/results.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | glm max | complete | complete | complete | justified | fits | 2 | [s0](scenarios/tg05-fastapi-multi-consumer-decomposition/glm-max/s0/assessment.md) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/file-fidelity/results.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | gpt high | complete | complete | complete | justified | fits | 1 | [s0](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-high/s0/assessment.md) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/file-fidelity/results.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | gpt max | complete | complete | complete | justified | fits | 0 | [s0](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-max/s0/assessment.md) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/file-fidelity/results.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | gpt xhigh | complete | complete | complete | justified | fits | 1 | [s0](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-xhigh/s0/assessment.md) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/file-fidelity/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | glm max | complete | complete | complete | justified | fits | 1 | [s0](scenarios/tg06-eleventy-author-migration-decomposition/glm-max/s0/assessment.md) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/file-fidelity/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | gpt high | complete | complete | complete | justified | fits | 1 | [s0](scenarios/tg06-eleventy-author-migration-decomposition/gpt-high/s0/assessment.md) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/file-fidelity/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | gpt max | complete | complete | complete | justified | fits | 3 | [s0](scenarios/tg06-eleventy-author-migration-decomposition/gpt-max/s0/assessment.md) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/file-fidelity/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | gpt xhigh | partial | partial | complete | justified | fits | 4 | [s0](scenarios/tg06-eleventy-author-migration-decomposition/gpt-xhigh/s0/assessment.md) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/file-fidelity/results.md) | s0 |
| `tg07-eleventy-decided-work-tracking` | glm max | complete | complete | complete | not_applicable | fits | 0 | [s0](scenarios/tg07-eleventy-decided-work-tracking/glm-max/s0/assessment.md) | [results](scenarios/tg07-eleventy-decided-work-tracking/assessment/file-fidelity/results.md) | s0 |
| `tg07-eleventy-decided-work-tracking` | glm max | complete | complete | complete | not_applicable | fits | 0 | [s1](scenarios/tg07-eleventy-decided-work-tracking/glm-max/s1/assessment.md) | [results](scenarios/tg07-eleventy-decided-work-tracking/assessment/file-fidelity/results.md) | s1 |
| `tg07-eleventy-decided-work-tracking` | gpt high | complete | complete | partial | not_applicable | fits | 3 | [s0](scenarios/tg07-eleventy-decided-work-tracking/gpt-high/s0/assessment.md) | [results](scenarios/tg07-eleventy-decided-work-tracking/assessment/file-fidelity/results.md) | s0 |
| `tg08-eleventy-contributor-docs` | glm max | complete | complete | complete | justified | fits | 2 | [s0](scenarios/tg08-eleventy-contributor-docs/glm-max/s0/assessment.md) | [results](scenarios/tg08-eleventy-contributor-docs/assessment/file-fidelity/results.md) | s0 |
| `tg08-eleventy-contributor-docs` | gpt high | complete | complete | complete | justified | fits | 1 | [s0](scenarios/tg08-eleventy-contributor-docs/gpt-high/s0/assessment.md) | [results](scenarios/tg08-eleventy-contributor-docs/assessment/file-fidelity/results.md) | s0 |
| `tg09-flask-vue-deployment-runbook` | glm max | partial | complete | complete | not_applicable | fits | 1 | [s0](scenarios/tg09-flask-vue-deployment-runbook/glm-max/s0/assessment.md) | [results](scenarios/tg09-flask-vue-deployment-runbook/assessment/file-fidelity/results.md) | s0 |
| `tg09-flask-vue-deployment-runbook` | gpt high | complete | complete | complete | justified | fits | 1 | [s0](scenarios/tg09-flask-vue-deployment-runbook/gpt-high/s0/assessment.md) | [results](scenarios/tg09-flask-vue-deployment-runbook/assessment/file-fidelity/results.md) | s0 |
| `tg10-flask-vue-interface-copy` | glm max | complete | complete | complete | not_applicable | fits | 1 | [s0](scenarios/tg10-flask-vue-interface-copy/glm-max/s0/assessment.md) | [results](scenarios/tg10-flask-vue-interface-copy/assessment/file-fidelity/results.md) | s0 |
| `tg10-flask-vue-interface-copy` | gpt high | complete | complete | complete | justified | fits | 1 | [s0](scenarios/tg10-flask-vue-interface-copy/gpt-high/s0/assessment.md) | [results](scenarios/tg10-flask-vue-interface-copy/assessment/file-fidelity/results.md) | s0 |
| `tg10-flask-vue-interface-copy` | gpt high | partial | complete | complete | justified | fits | 1 | [s1](scenarios/tg10-flask-vue-interface-copy/gpt-high/s1/assessment.md) | [results](scenarios/tg10-flask-vue-interface-copy/assessment/file-fidelity/results.md) | s1 |

## Task-file readability

Share of `readable` section grades, `navigable` whole-file grades, and harvested presentation mistakes per cohort.

| Cohort | n | Readable sections | Navigable files | Mistakes |
|---|---:|---:|---:|---:|
| All | 28 | 89% | 100% | 159 |
| GLM | 11 | 79% | 100% | 57 |
| GPT | 17 | 93% | 100% | 102 |
| glm max | 11 | 79% | 100% | 57 |
| gpt high | 11 | 94% | 100% | 56 |
| gpt max | 3 | 94% | 100% | 22 |
| gpt xhigh | 3 | 92% | 100% | 24 |

## Task-file readability detail

| Scenario | Producer | Readable sections | Navigation | Mistakes | Subject | Judgment | Sample |
|---|---|---|---|---:|---|---|---|
| `tg01-eleventy-archive-handoff` | glm max | 6/7 | navigable | 5 | [s0](scenarios/tg01-eleventy-archive-handoff/glm-max/s0/assessment.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/file-readability/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | gpt high | 4/5 | navigable | 7 | [s0](scenarios/tg01-eleventy-archive-handoff/gpt-high/s0/assessment.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/file-readability/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | glm max | 2/4 | navigable | 6 | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/s0/assessment.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/file-readability/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | gpt high | 4/4 | navigable | 5 | [s0](scenarios/tg02-fastapi-pagination-handoff/gpt-high/s0/assessment.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/file-readability/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | glm max | 4/4 | navigable | 4 | [s0](scenarios/tg03-flask-vue-refresh-handoff/glm-max/s0/assessment.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/file-readability/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | gpt high | 5/5 | navigable | 4 | [s0](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/s0/assessment.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/file-readability/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | glm max | 7/11 | navigable | 8 | [s0](scenarios/tg04-flask-vue-discovery-decomposition/glm-max/s0/assessment.md) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/file-readability/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | gpt high | 3/4 | navigable | 8 | [s0](scenarios/tg04-flask-vue-discovery-decomposition/gpt-high/s0/assessment.md) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/file-readability/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | gpt max | 4/5 | navigable | 7 | [s0](scenarios/tg04-flask-vue-discovery-decomposition/gpt-max/s0/assessment.md) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/file-readability/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | gpt xhigh | 11/14 | navigable | 10 | [s0](scenarios/tg04-flask-vue-discovery-decomposition/gpt-xhigh/s0/assessment.md) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/file-readability/results.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | glm max | 11/11 | navigable | 7 | [s0](scenarios/tg05-fastapi-multi-consumer-decomposition/glm-max/s0/assessment.md) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/file-readability/results.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | gpt high | 17/17 | navigable | 6 | [s0](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-high/s0/assessment.md) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/file-readability/results.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | gpt max | 22/23 | navigable | 7 | [s0](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-max/s0/assessment.md) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/file-readability/results.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | gpt xhigh | 17/18 | navigable | 8 | [s0](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-xhigh/s0/assessment.md) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/file-readability/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | glm max | 10/14 | navigable | 9 | [s0](scenarios/tg06-eleventy-author-migration-decomposition/glm-max/s0/assessment.md) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/file-readability/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | gpt high | 21/21 | navigable | 7 | [s0](scenarios/tg06-eleventy-author-migration-decomposition/gpt-high/s0/assessment.md) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/file-readability/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | gpt max | 22/23 | navigable | 8 | [s0](scenarios/tg06-eleventy-author-migration-decomposition/gpt-max/s0/assessment.md) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/file-readability/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | gpt xhigh | 17/17 | navigable | 6 | [s0](scenarios/tg06-eleventy-author-migration-decomposition/gpt-xhigh/s0/assessment.md) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/file-readability/results.md) | s0 |
| `tg07-eleventy-decided-work-tracking` | glm max | 2/3 | navigable | 2 | [s0](scenarios/tg07-eleventy-decided-work-tracking/glm-max/s0/assessment.md) | [results](scenarios/tg07-eleventy-decided-work-tracking/assessment/file-readability/results.md) | s0 |
| `tg07-eleventy-decided-work-tracking` | glm max | 4/4 | navigable | 0 | [s1](scenarios/tg07-eleventy-decided-work-tracking/glm-max/s1/assessment.md) | [results](scenarios/tg07-eleventy-decided-work-tracking/assessment/file-readability/results.md) | s1 |
| `tg07-eleventy-decided-work-tracking` | gpt high | 2/2 | navigable | 1 | [s0](scenarios/tg07-eleventy-decided-work-tracking/gpt-high/s0/assessment.md) | [results](scenarios/tg07-eleventy-decided-work-tracking/assessment/file-readability/results.md) | s0 |
| `tg08-eleventy-contributor-docs` | glm max | 2/4 | navigable | 7 | [s0](scenarios/tg08-eleventy-contributor-docs/glm-max/s0/assessment.md) | [results](scenarios/tg08-eleventy-contributor-docs/assessment/file-readability/results.md) | s0 |
| `tg08-eleventy-contributor-docs` | gpt high | 4/4 | navigable | 4 | [s0](scenarios/tg08-eleventy-contributor-docs/gpt-high/s0/assessment.md) | [results](scenarios/tg08-eleventy-contributor-docs/assessment/file-readability/results.md) | s0 |
| `tg09-flask-vue-deployment-runbook` | glm max | 3/3 | navigable | 5 | [s0](scenarios/tg09-flask-vue-deployment-runbook/glm-max/s0/assessment.md) | [results](scenarios/tg09-flask-vue-deployment-runbook/assessment/file-readability/results.md) | s0 |
| `tg09-flask-vue-deployment-runbook` | gpt high | 2/4 | navigable | 6 | [s0](scenarios/tg09-flask-vue-deployment-runbook/gpt-high/s0/assessment.md) | [results](scenarios/tg09-flask-vue-deployment-runbook/assessment/file-readability/results.md) | s0 |
| `tg10-flask-vue-interface-copy` | glm max | 4/5 | navigable | 4 | [s0](scenarios/tg10-flask-vue-interface-copy/glm-max/s0/assessment.md) | [results](scenarios/tg10-flask-vue-interface-copy/assessment/file-readability/results.md) | s0 |
| `tg10-flask-vue-interface-copy` | gpt high | 6/7 | navigable | 4 | [s0](scenarios/tg10-flask-vue-interface-copy/gpt-high/s0/assessment.md) | [results](scenarios/tg10-flask-vue-interface-copy/assessment/file-readability/results.md) | s0 |
| `tg10-flask-vue-interface-copy` | gpt high | 6/6 | navigable | 4 | [s1](scenarios/tg10-flask-vue-interface-copy/gpt-high/s1/assessment.md) | [results](scenarios/tg10-flask-vue-interface-copy/assessment/file-readability/results.md) | s1 |

## Per-scenario results

| Scenario | Numbers | Cells | Task-creation | Handoff | Quality | Plan content | Fidelity | Readability |
|---|---|---|---|---|---|---|---|---|
| `tg01-eleventy-archive-handoff` | — | [glm-max](scenarios/tg01-eleventy-archive-handoff/glm-max/index.md) · [gpt-high](scenarios/tg01-eleventy-archive-handoff/gpt-high/index.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/task-creation/results.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/task-quality/results.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/plan-content/results.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/file-fidelity/results.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/file-readability/results.md) |
| `tg02-fastapi-pagination-handoff` | — | [glm-max](scenarios/tg02-fastapi-pagination-handoff/glm-max/index.md) · [gpt-high](scenarios/tg02-fastapi-pagination-handoff/gpt-high/index.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/task-creation/results.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/task-quality/results.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/plan-content/results.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/file-fidelity/results.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/file-readability/results.md) |
| `tg03-flask-vue-refresh-handoff` | — | [glm-max](scenarios/tg03-flask-vue-refresh-handoff/glm-max/index.md) · [gpt-high](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/index.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/task-creation/results.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/task-quality/results.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/plan-content/results.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/file-fidelity/results.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/file-readability/results.md) |
| `tg04-flask-vue-discovery-decomposition` | — | [glm-max](scenarios/tg04-flask-vue-discovery-decomposition/glm-max/index.md) · [gpt-high](scenarios/tg04-flask-vue-discovery-decomposition/gpt-high/index.md) · [gpt-max](scenarios/tg04-flask-vue-discovery-decomposition/gpt-max/index.md) · [gpt-xhigh](scenarios/tg04-flask-vue-discovery-decomposition/gpt-xhigh/index.md) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-creation/results.md) | — | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-quality/results.md) | — | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/file-fidelity/results.md) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/file-readability/results.md) |
| `tg05-fastapi-multi-consumer-decomposition` | — | [glm-max](scenarios/tg05-fastapi-multi-consumer-decomposition/glm-max/index.md) · [gpt-high](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-high/index.md) · [gpt-max](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-max/index.md) · [gpt-xhigh](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-xhigh/index.md) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-creation/results.md) | — | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-quality/results.md) | — | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/file-fidelity/results.md) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/file-readability/results.md) |
| `tg06-eleventy-author-migration-decomposition` | — | [glm-max](scenarios/tg06-eleventy-author-migration-decomposition/glm-max/index.md) · [gpt-high](scenarios/tg06-eleventy-author-migration-decomposition/gpt-high/index.md) · [gpt-max](scenarios/tg06-eleventy-author-migration-decomposition/gpt-max/index.md) · [gpt-xhigh](scenarios/tg06-eleventy-author-migration-decomposition/gpt-xhigh/index.md) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-creation/results.md) | — | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-quality/results.md) | — | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/file-fidelity/results.md) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/file-readability/results.md) |
| `tg07-eleventy-decided-work-tracking` | — | [glm-max](scenarios/tg07-eleventy-decided-work-tracking/glm-max/index.md) · [gpt-high](scenarios/tg07-eleventy-decided-work-tracking/gpt-high/index.md) | [results](scenarios/tg07-eleventy-decided-work-tracking/assessment/task-creation/results.md) | — | [results](scenarios/tg07-eleventy-decided-work-tracking/assessment/task-quality/results.md) | — | [results](scenarios/tg07-eleventy-decided-work-tracking/assessment/file-fidelity/results.md) | [results](scenarios/tg07-eleventy-decided-work-tracking/assessment/file-readability/results.md) |
| `tg08-eleventy-contributor-docs` | — | [glm-max](scenarios/tg08-eleventy-contributor-docs/glm-max/index.md) · [gpt-high](scenarios/tg08-eleventy-contributor-docs/gpt-high/index.md) | [results](scenarios/tg08-eleventy-contributor-docs/assessment/task-creation/results.md) | — | [results](scenarios/tg08-eleventy-contributor-docs/assessment/task-quality/results.md) | — | [results](scenarios/tg08-eleventy-contributor-docs/assessment/file-fidelity/results.md) | [results](scenarios/tg08-eleventy-contributor-docs/assessment/file-readability/results.md) |
| `tg09-flask-vue-deployment-runbook` | — | [glm-max](scenarios/tg09-flask-vue-deployment-runbook/glm-max/index.md) · [gpt-high](scenarios/tg09-flask-vue-deployment-runbook/gpt-high/index.md) | [results](scenarios/tg09-flask-vue-deployment-runbook/assessment/task-creation/results.md) | — | [results](scenarios/tg09-flask-vue-deployment-runbook/assessment/task-quality/results.md) | — | [results](scenarios/tg09-flask-vue-deployment-runbook/assessment/file-fidelity/results.md) | [results](scenarios/tg09-flask-vue-deployment-runbook/assessment/file-readability/results.md) |
| `tg10-flask-vue-interface-copy` | — | [glm-max](scenarios/tg10-flask-vue-interface-copy/glm-max/index.md) · [gpt-high](scenarios/tg10-flask-vue-interface-copy/gpt-high/index.md) | [results](scenarios/tg10-flask-vue-interface-copy/assessment/task-creation/results.md) | — | [results](scenarios/tg10-flask-vue-interface-copy/assessment/task-quality/results.md) | — | [results](scenarios/tg10-flask-vue-interface-copy/assessment/file-fidelity/results.md) | [results](scenarios/tg10-flask-vue-interface-copy/assessment/file-readability/results.md) |
