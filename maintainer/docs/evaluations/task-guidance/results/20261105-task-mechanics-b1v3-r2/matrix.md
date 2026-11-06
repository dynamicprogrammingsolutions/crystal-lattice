# Task-guidance b1v3 baseline retest status

- Labels: `b1v3-gpt6-r2`

| Stage | Expected | Present | Valid | Invalid | Missing |
|---|---:|---:|---:|---:|---:|
| Task creation | 26 | 26 | 24 | 2 | 0 |
| Fresh-agent planning | 12 | 12 | 11 | 1 | 0 |
| Same-agent planning | 6 | 6 | 6 | 0 | 0 |
| Semantic batches | 26 | 24 | — | — | 2 |
| Handoff semantic batches | 25 | 24 | — | — | 1 |
| Negative controls | 1 | 1 | — | — | 0 |
| Plan-content judgments | 25 | 24 | — | — | 1 |
| File-fidelity judgments | 26 | 23 | — | — | 3 |
| File-readability judgments | 26 | 24 | — | — | 2 |
| Provider setup blockers | — | 0 | — | — | — |

## Invalid records — validity failures

- `tg09-flask-vue-deployment-runbook:gpt:high`: no task files were produced
- `tg10-flask-vue-interface-copy:gpt:high`: no task files were produced

## Invalid records — provider failures

Run-level provider errors (outages, authentication), not guidance-behavior findings.

- `tg01-eleventy-archive-handoff:omit:gpt:high`: run failure: None, ('OpenAI Responses stream failed: Error code: 401 - {\'error\': {\'message\': \'authentication failed (status=503): {"error":"Too many concurrent requests"}\', \'type\': \'authentication_error\', \'param\': None, \'code\': None}}',); empty planning response

## Task-creation semantic quality

| Cohort | Assessments | Overall success | Fragmentation | Phase-only | Layer split | Evidence reownership | Dependency safety | Production crossing |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| All | 24 | 95.0% | 76.4% | 100.0% | 100.0% | 100.0% | 100.0% | 93.8% |
| GLM | 10 | 98.0% | 93.3% | 100.0% | 100.0% | 100.0% | 100.0% | 95.0% |
| GPT | 14 | 92.8% | 64.3% | 100.0% | 100.0% | 100.0% | 100.0% | 92.9% |
| GLM max | 10 | 98.0% | 93.3% | 100.0% | 100.0% | 100.0% | 100.0% | 95.0% |
| GPT high | 8 | 95.8% | 87.5% | 100.0% | 100.0% | 100.0% | 100.0% | 87.5% |
| GPT xhigh | 3 | 88.9% | 33.3% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| GPT max | 3 | 88.9% | 33.3% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |

## Task-creation semantic detail

One row per judgment. Each cohort row above is the average of its rows here; dimension cells read `status (score)`.

| Scenario | Producer | Overall | Fragmentation | Phase-only | Layer split | Evidence reownership | Dependency safety | Production crossing | Run | Judgment | Sample |
|---|---|---:|---|---|---|---|---|---|---|---|---|
| `tg01-eleventy-archive-handoff` | glm max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg01-eleventy-archive-handoff/glm-max/s0) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/task-creation/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | gpt high | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg01-eleventy-archive-handoff/gpt-high/s0) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/task-creation/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | glm max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/task-creation/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | gpt high | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg02-fastapi-pagination-handoff/gpt-high/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/task-creation/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | glm max | 91.7 | none (100) | none (100) | none (100) | none (100) | none (100) | partial (50) | [s0](scenarios/tg03-flask-vue-refresh-handoff/glm-max/s0) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/task-creation/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | gpt high | 83.3 | none (100) | none (100) | none (100) | none (100) | none (100) | present (0) | [s0](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/s0) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/task-creation/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | glm max | 88.8 | medium (33) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg04-flask-vue-discovery-decomposition/glm-max/s0) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-creation/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | gpt high | 83.3 | high (0) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg04-flask-vue-discovery-decomposition/gpt-high/s0) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-creation/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | gpt max | 83.3 | high (0) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg04-flask-vue-discovery-decomposition/gpt-max/s0) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-creation/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | gpt xhigh | 83.3 | high (0) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg04-flask-vue-discovery-decomposition/gpt-xhigh/s0) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-creation/results.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | glm max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg05-fastapi-multi-consumer-decomposition/glm-max/s0) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-creation/results.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | gpt high | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-high/s0) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-creation/results.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | gpt max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-max/s0) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-creation/results.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | gpt xhigh | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-xhigh/s0) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-creation/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | glm max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg06-eleventy-author-migration-decomposition/glm-max/s0) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-creation/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | gpt high | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg06-eleventy-author-migration-decomposition/gpt-high/s0) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-creation/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | gpt max | 83.3 | high (0) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg06-eleventy-author-migration-decomposition/gpt-max/s0) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-creation/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | gpt xhigh | 83.3 | high (0) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg06-eleventy-author-migration-decomposition/gpt-xhigh/s0) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-creation/results.md) | s0 |
| `tg07-eleventy-decided-work-tracking` | glm max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg07-eleventy-decided-work-tracking/glm-max/s0) | [results](scenarios/tg07-eleventy-decided-work-tracking/assessment/task-creation/results.md) | s0 |
| `tg07-eleventy-decided-work-tracking` | gpt high | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg07-eleventy-decided-work-tracking/gpt-high/s0) | [results](scenarios/tg07-eleventy-decided-work-tracking/assessment/task-creation/results.md) | s0 |
| `tg08-eleventy-contributor-docs` | glm max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg08-eleventy-contributor-docs/glm-max/s0) | [results](scenarios/tg08-eleventy-contributor-docs/assessment/task-creation/results.md) | s0 |
| `tg08-eleventy-contributor-docs` | gpt high | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg08-eleventy-contributor-docs/gpt-high/s0) | [results](scenarios/tg08-eleventy-contributor-docs/assessment/task-creation/results.md) | s0 |
| `tg09-flask-vue-deployment-runbook` | glm max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg09-flask-vue-deployment-runbook/glm-max/s0) | [results](scenarios/tg09-flask-vue-deployment-runbook/assessment/task-creation/results.md) | s0 |
| `tg10-flask-vue-interface-copy` | glm max | 100 | none (100) | none (100) | none (100) | none (100) | none (100) | none (100) | [s0](scenarios/tg10-flask-vue-interface-copy/glm-max/s0) | [results](scenarios/tg10-flask-vue-interface-copy/assessment/task-creation/results.md) | s0 |

## Handoff semantic detail

One row per judgment, across plan variants and stages.

| Scenario | Variant | Stage | Producer | Handoff quality | Plan coverage | Self-contained | Broad rediscovery | Documentation | Testing | Run | Judgment | Sample |
|---|---|---|---|---:|---|---|---|---|---|---|---|---|
| `tg01-eleventy-archive-handoff` | generated-file | fresh-agent | glm max | 96 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg01-eleventy-archive-handoff/glm-max/generated-plan/s0) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | generated-file | fresh-agent | gpt high | 92 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg01-eleventy-archive-handoff/gpt-high/generated-plan/s0) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | generated-task | same-agent | glm max | 96 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg01-eleventy-archive-handoff/glm-max/continuation/s0) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | generated-task | same-agent | gpt high | 93 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg01-eleventy-archive-handoff/gpt-high/continuation/s0) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | omit | fresh-agent | glm max | 93 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg01-eleventy-archive-handoff/glm-max/plan-omit/s0) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | retain | fresh-agent | glm max | 94 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg01-eleventy-archive-handoff/glm-max/plan-retain/s0) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | retain | fresh-agent | gpt high | 92 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg01-eleventy-archive-handoff/gpt-high/plan-retain/s0) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | generated-file | fresh-agent | glm max | 94 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/generated-plan/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | generated-file | fresh-agent | gpt high | 93 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg02-fastapi-pagination-handoff/gpt-high/generated-plan/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | generated-task | same-agent | glm max | 93 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/continuation/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | generated-task | same-agent | gpt high | 93 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg02-fastapi-pagination-handoff/gpt-high/continuation/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | incomplete | fresh-agent | glm max | 75 | complete | no | yes | appropriate | decisive | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/control/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | omit | fresh-agent | glm max | 94 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/plan-omit/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | omit | fresh-agent | gpt high | 93 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg02-fastapi-pagination-handoff/gpt-high/plan-omit/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | retain | fresh-agent | glm max | 95 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/plan-retain/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | retain | fresh-agent | gpt high | 93 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg02-fastapi-pagination-handoff/gpt-high/plan-retain/s0) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | generated-file | fresh-agent | glm max | 96 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg03-flask-vue-refresh-handoff/glm-max/generated-plan/s0) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | generated-file | fresh-agent | gpt high | 85 | complete | yes | no | appropriate | partial | [s0](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/generated-plan/s0) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | generated-task | same-agent | glm max | 96 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg03-flask-vue-refresh-handoff/glm-max/continuation/s0) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | generated-task | same-agent | gpt high | 90 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/continuation/s0) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | omit | fresh-agent | glm max | 96 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg03-flask-vue-refresh-handoff/glm-max/plan-omit/s0) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | omit | fresh-agent | gpt high | 90 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/plan-omit/s0) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | retain | fresh-agent | glm max | 95 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg03-flask-vue-refresh-handoff/glm-max/plan-retain/s0) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | retain | fresh-agent | gpt high | 94 | complete | yes | no | appropriate | decisive | [s0](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/plan-retain/s0) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | s0 |

## Presented-plan content

Top-grade share per requirement, by the variant of the task file the presenting agent worked from; `n` is the judged plans.

| Requirement | retain | omit | incomplete | generated-task | generated-file |
|---|---:|---:|---:|---:|---:|
| GENERIC-1 | 67% | 100% | 100% | 83% | 83% |
| GENERIC-10 | 100% | 100% | 100% | 100% | 100% |
| GENERIC-2 | 100% | 100% | 100% | 100% | 100% |
| GENERIC-3 | 100% | 100% | 100% | 100% | 100% |
| GENERIC-4 | 33% | 80% | 100% | 50% | 50% |
| GENERIC-5 | 50% | 40% | 100% | 33% | 17% |
| GENERIC-6 | 17% | 20% | 0% | 0% | 17% |
| GENERIC-7 | 17% | 20% | 0% | 0% | 17% |
| GENERIC-8 | 100% | 100% | 100% | 83% | 100% |
| GENERIC-9 | 100% | 100% | 0% | 100% | 83% |
| PLAN-1 | 67% | 80% | 100% | 83% | 100% |
| PLAN-2 | 83% | 100% | 100% | 67% | 100% |
| PLAN-3 | 83% | 100% | 100% | 83% | 67% |
| PLAN-4 | 100% | 100% | 100% | 100% | 100% |
| PLAN-5 | 100% | 100% | 100% | 100% | 100% |
| PLAN-6 | 100% | 100% | — | 100% | 100% |
| PLAN-7 | 100% | 100% | — | 100% | 100% |

| Cohort | n | Mean coverage |
|---|---:|---:|
| retain | 6 | 75% |
| omit | 5 | 83% |
| incomplete | 1 | 80% |
| generated-task | 6 | 73% |
| generated-file | 6 | 76% |
| All | 0 | — |

## Presented-plan content detail

One row per judgment; the subject link opens the judged plan's grade summary.

| Scenario | Variant | Producer | Coverage | Non-top requirements | Missed | Subject | Judgment | Sample |
|---|---|---|---:|---|---:|---|---|---|
| `tg01-eleventy-archive-handoff` | generated-file | glm max | 88% | GENERIC-5, GENERIC-6 | 0 | [s0](scenarios/tg01-eleventy-archive-handoff/glm-max/generated-plan/s0/assessment.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/plan-content/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | generated-file | gpt high | 71% | GENERIC-4, GENERIC-5, GENERIC-6, GENERIC-7, PLAN-3 | 0 | [s0](scenarios/tg01-eleventy-archive-handoff/gpt-high/generated-plan/s0/assessment.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/plan-content/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | generated-task | glm max | 82% | GENERIC-5, GENERIC-6, GENERIC-7 | 1 | [s0](scenarios/tg01-eleventy-archive-handoff/glm-max/continuation/s0/assessment.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/plan-content/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | generated-task | gpt high | 71% | GENERIC-4, GENERIC-5, GENERIC-6, GENERIC-7, PLAN-2 | 0 | [s0](scenarios/tg01-eleventy-archive-handoff/gpt-high/continuation/s0/assessment.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/plan-content/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | omit | glm max | 82% | GENERIC-5, GENERIC-6, GENERIC-7 | 0 | [s0](scenarios/tg01-eleventy-archive-handoff/glm-max/plan-omit/s0/assessment.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/plan-content/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | retain | glm max | 94% | GENERIC-6 | 0 | [s0](scenarios/tg01-eleventy-archive-handoff/glm-max/plan-retain/s0/assessment.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/plan-content/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | retain | gpt high | 65% | GENERIC-4, GENERIC-6, GENERIC-7, PLAN-1, PLAN-2, PLAN-3 | 0 | [s0](scenarios/tg01-eleventy-archive-handoff/gpt-high/plan-retain/s0/assessment.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/plan-content/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | generated-file | glm max | 73% | GENERIC-4, GENERIC-5, GENERIC-6, GENERIC-7 | 1 | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/generated-plan/s0/assessment.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/plan-content/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | generated-file | gpt high | 67% | GENERIC-1, GENERIC-4, GENERIC-5, GENERIC-6, GENERIC-7 | 0 | [s0](scenarios/tg02-fastapi-pagination-handoff/gpt-high/generated-plan/s0/assessment.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/plan-content/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | generated-task | glm max | 87% | GENERIC-6, GENERIC-7 | 0 | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/continuation/s0/assessment.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/plan-content/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | generated-task | gpt high | 67% | GENERIC-4, GENERIC-5, GENERIC-6, GENERIC-7, PLAN-1 | 0 | [s0](scenarios/tg02-fastapi-pagination-handoff/gpt-high/continuation/s0/assessment.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/plan-content/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | incomplete | glm max | 80% | GENERIC-6, GENERIC-7, GENERIC-9 | 0 | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/control/s0/assessment.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/plan-content/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | omit | glm max | 80% | GENERIC-5, GENERIC-6, GENERIC-7 | 0 | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/plan-omit/s0/assessment.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/plan-content/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | omit | gpt high | 80% | GENERIC-6, GENERIC-7, PLAN-1 | 0 | [s0](scenarios/tg02-fastapi-pagination-handoff/gpt-high/plan-omit/s0/assessment.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/plan-content/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | retain | glm max | 87% | GENERIC-5, GENERIC-7 | 1 | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/plan-retain/s0/assessment.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/plan-content/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | retain | gpt high | 60% | GENERIC-1, GENERIC-4, GENERIC-5, GENERIC-6, GENERIC-7, PLAN-1 | 0 | [s0](scenarios/tg02-fastapi-pagination-handoff/gpt-high/plan-retain/s0/assessment.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/plan-content/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | generated-file | glm max | 86% | GENERIC-7, GENERIC-9 | 0 | [s0](scenarios/tg03-flask-vue-refresh-handoff/glm-max/generated-plan/s0/assessment.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/plan-content/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | generated-file | gpt high | 71% | GENERIC-5, GENERIC-6, GENERIC-7, PLAN-3 | 0 | [s0](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/generated-plan/s0/assessment.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/plan-content/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | generated-task | glm max | 86% | GENERIC-6, GENERIC-7 | 0 | [s0](scenarios/tg03-flask-vue-refresh-handoff/glm-max/continuation/s0/assessment.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/plan-content/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | generated-task | gpt high | 43% | GENERIC-1, GENERIC-4, GENERIC-5, GENERIC-6, GENERIC-7, GENERIC-8, PLAN-2, PLAN-3 | 0 | [s0](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/continuation/s0/assessment.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/plan-content/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | omit | glm max | 100% | — | 0 | [s0](scenarios/tg03-flask-vue-refresh-handoff/glm-max/plan-omit/s0/assessment.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/plan-content/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | omit | gpt high | 71% | GENERIC-4, GENERIC-5, GENERIC-6, GENERIC-7 | 0 | [s0](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/plan-omit/s0/assessment.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/plan-content/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | retain | glm max | 71% | GENERIC-1, GENERIC-4, GENERIC-6, GENERIC-7 | 0 | [s0](scenarios/tg03-flask-vue-refresh-handoff/glm-max/plan-retain/s0/assessment.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/plan-content/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | retain | gpt high | 71% | GENERIC-4, GENERIC-5, GENERIC-6, GENERIC-7 | 1 | [s0](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/plan-retain/s0/assessment.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/plan-content/results.md) | s0 |

## Task-file fidelity

Share of top grades (complete / justified / fits) per dimension; `n` is the judged subjects in the cohort.

| Cohort | n | Top grades overall | design | context | placement | justification | kind-fit |
|---|---:|---:|---:|---:|---:|---:|---:|
| All | 23 | 90% | 87% | 78% | 96% | 91% | 100% |
| GLM | 10 | 94% | 90% | 90% | 100% | 90% | 100% |
| GPT | 13 | 88% | 85% | 69% | 92% | 92% | 100% |
| glm max | 10 | 94% | 90% | 90% | 100% | 90% | 100% |
| gpt high | 8 | 90% | 100% | 75% | 88% | 88% | 100% |
| gpt max | 2 | 80% | 50% | 50% | 100% | 100% | 100% |
| gpt xhigh | 3 | 87% | 67% | 67% | 100% | 100% | 100% |

Mistakes harvested across all judgments: 36.

## Task-file fidelity detail

| Scenario | Producer | design | context | placement | justification | kind-fit | Mistakes | Subject | Judgment | Sample |
|---|---|---|---|---|---|---|---:|---|---|---|
| `tg01-eleventy-archive-handoff` | glm max | complete | complete | complete | justified | fits | 0 | [s0](scenarios/tg01-eleventy-archive-handoff/glm-max/s0/assessment.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/file-fidelity/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | gpt high | complete | complete | complete | justified | fits | 1 | [s0](scenarios/tg01-eleventy-archive-handoff/gpt-high/s0/assessment.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/file-fidelity/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | glm max | complete | complete | complete | justified | fits | 1 | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/s0/assessment.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/file-fidelity/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | gpt high | complete | complete | complete | justified | fits | 1 | [s0](scenarios/tg02-fastapi-pagination-handoff/gpt-high/s0/assessment.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/file-fidelity/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | glm max | complete | complete | complete | justified | fits | 0 | [s0](scenarios/tg03-flask-vue-refresh-handoff/glm-max/s0/assessment.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/file-fidelity/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | gpt high | complete | complete | complete | justified | fits | 2 | [s0](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/s0/assessment.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/file-fidelity/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | glm max | complete | partial | complete | justified | fits | 2 | [s0](scenarios/tg04-flask-vue-discovery-decomposition/glm-max/s0/assessment.md) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/file-fidelity/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | gpt high | complete | complete | complete | justified | fits | 2 | [s0](scenarios/tg04-flask-vue-discovery-decomposition/gpt-high/s0/assessment.md) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/file-fidelity/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | gpt max | partial | partial | complete | justified | fits | 5 | [s0](scenarios/tg04-flask-vue-discovery-decomposition/gpt-max/s0/assessment.md) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/file-fidelity/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | gpt xhigh | partial | partial | complete | justified | fits | 3 | [s0](scenarios/tg04-flask-vue-discovery-decomposition/gpt-xhigh/s0/assessment.md) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/file-fidelity/results.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | glm max | complete | complete | complete | justified | fits | 0 | [s0](scenarios/tg05-fastapi-multi-consumer-decomposition/glm-max/s0/assessment.md) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/file-fidelity/results.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | gpt high | complete | complete | complete | justified | fits | 0 | [s0](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-high/s0/assessment.md) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/file-fidelity/results.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | gpt xhigh | complete | complete | complete | justified | fits | 0 | [s0](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-xhigh/s0/assessment.md) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/file-fidelity/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | glm max | complete | complete | complete | justified | fits | 2 | [s0](scenarios/tg06-eleventy-author-migration-decomposition/glm-max/s0/assessment.md) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/file-fidelity/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | gpt high | complete | partial | complete | justified | fits | 4 | [s0](scenarios/tg06-eleventy-author-migration-decomposition/gpt-high/s0/assessment.md) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/file-fidelity/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | gpt max | complete | complete | complete | justified | fits | 2 | [s0](scenarios/tg06-eleventy-author-migration-decomposition/gpt-max/s0/assessment.md) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/file-fidelity/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | gpt xhigh | complete | complete | complete | justified | fits | 3 | [s0](scenarios/tg06-eleventy-author-migration-decomposition/gpt-xhigh/s0/assessment.md) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/file-fidelity/results.md) | s0 |
| `tg07-eleventy-decided-work-tracking` | glm max | complete | complete | complete | not_applicable | fits | 0 | [s0](scenarios/tg07-eleventy-decided-work-tracking/glm-max/s0/assessment.md) | [results](scenarios/tg07-eleventy-decided-work-tracking/assessment/file-fidelity/results.md) | s0 |
| `tg07-eleventy-decided-work-tracking` | gpt high | complete | partial | partial | not_applicable | fits | 3 | [s0](scenarios/tg07-eleventy-decided-work-tracking/gpt-high/s0/assessment.md) | [results](scenarios/tg07-eleventy-decided-work-tracking/assessment/file-fidelity/results.md) | s0 |
| `tg08-eleventy-contributor-docs` | glm max | complete | complete | complete | justified | fits | 3 | [s0](scenarios/tg08-eleventy-contributor-docs/glm-max/s0/assessment.md) | [results](scenarios/tg08-eleventy-contributor-docs/assessment/file-fidelity/results.md) | s0 |
| `tg08-eleventy-contributor-docs` | gpt high | complete | complete | complete | justified | fits | 0 | [s0](scenarios/tg08-eleventy-contributor-docs/gpt-high/s0/assessment.md) | [results](scenarios/tg08-eleventy-contributor-docs/assessment/file-fidelity/results.md) | s0 |
| `tg09-flask-vue-deployment-runbook` | glm max | poor | complete | complete | justified | fits | 2 | [s0](scenarios/tg09-flask-vue-deployment-runbook/glm-max/s0/assessment.md) | [results](scenarios/tg09-flask-vue-deployment-runbook/assessment/file-fidelity/results.md) | s0 |
| `tg10-flask-vue-interface-copy` | glm max | complete | complete | complete | justified | fits | 0 | [s0](scenarios/tg10-flask-vue-interface-copy/glm-max/s0/assessment.md) | [results](scenarios/tg10-flask-vue-interface-copy/assessment/file-fidelity/results.md) | s0 |

## Task-file readability

Share of `readable` section grades, `navigable` whole-file grades, and harvested presentation mistakes per cohort.

| Cohort | n | Readable sections | Navigable files | Mistakes |
|---|---:|---:|---:|---:|
| All | 24 | 89% | 96% | 118 |
| GLM | 10 | 85% | 90% | 50 |
| GPT | 14 | 91% | 100% | 68 |
| glm max | 10 | 85% | 90% | 50 |
| gpt high | 8 | 92% | 100% | 34 |
| gpt max | 3 | 92% | 100% | 17 |
| gpt xhigh | 3 | 88% | 100% | 17 |

## Task-file readability detail

| Scenario | Producer | Readable sections | Navigation | Mistakes | Subject | Judgment | Sample |
|---|---|---|---|---:|---|---|---|
| `tg01-eleventy-archive-handoff` | glm max | 1/4 | partial | 8 | [s0](scenarios/tg01-eleventy-archive-handoff/glm-max/s0/assessment.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/file-readability/results.md) | s0 |
| `tg01-eleventy-archive-handoff` | gpt high | 3/4 | navigable | 6 | [s0](scenarios/tg01-eleventy-archive-handoff/gpt-high/s0/assessment.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/file-readability/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | glm max | 4/4 | navigable | 4 | [s0](scenarios/tg02-fastapi-pagination-handoff/glm-max/s0/assessment.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/file-readability/results.md) | s0 |
| `tg02-fastapi-pagination-handoff` | gpt high | 4/4 | navigable | 4 | [s0](scenarios/tg02-fastapi-pagination-handoff/gpt-high/s0/assessment.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/file-readability/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | glm max | 2/3 | navigable | 4 | [s0](scenarios/tg03-flask-vue-refresh-handoff/glm-max/s0/assessment.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/file-readability/results.md) | s0 |
| `tg03-flask-vue-refresh-handoff` | gpt high | 3/4 | navigable | 3 | [s0](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/s0/assessment.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/file-readability/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | glm max | 9/10 | navigable | 4 | [s0](scenarios/tg04-flask-vue-discovery-decomposition/glm-max/s0/assessment.md) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/file-readability/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | gpt high | 4/4 | navigable | 4 | [s0](scenarios/tg04-flask-vue-discovery-decomposition/gpt-high/s0/assessment.md) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/file-readability/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | gpt max | 3/4 | navigable | 7 | [s0](scenarios/tg04-flask-vue-discovery-decomposition/gpt-max/s0/assessment.md) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/file-readability/results.md) | s0 |
| `tg04-flask-vue-discovery-decomposition` | gpt xhigh | 3/4 | navigable | 5 | [s0](scenarios/tg04-flask-vue-discovery-decomposition/gpt-xhigh/s0/assessment.md) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/file-readability/results.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | glm max | 13/14 | navigable | 7 | [s0](scenarios/tg05-fastapi-multi-consumer-decomposition/glm-max/s0/assessment.md) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/file-readability/results.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | gpt high | 14/15 | navigable | 5 | [s0](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-high/s0/assessment.md) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/file-readability/results.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | gpt max | 17/17 | navigable | 7 | [s0](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-max/s0/assessment.md) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/file-readability/results.md) | s0 |
| `tg05-fastapi-multi-consumer-decomposition` | gpt xhigh | 16/17 | navigable | 6 | [s0](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-xhigh/s0/assessment.md) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/file-readability/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | glm max | 11/14 | navigable | 6 | [s0](scenarios/tg06-eleventy-author-migration-decomposition/glm-max/s0/assessment.md) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/file-readability/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | gpt high | 14/14 | navigable | 6 | [s0](scenarios/tg06-eleventy-author-migration-decomposition/gpt-high/s0/assessment.md) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/file-readability/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | gpt max | 3/4 | navigable | 3 | [s0](scenarios/tg06-eleventy-author-migration-decomposition/gpt-max/s0/assessment.md) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/file-readability/results.md) | s0 |
| `tg06-eleventy-author-migration-decomposition` | gpt xhigh | 4/5 | navigable | 6 | [s0](scenarios/tg06-eleventy-author-migration-decomposition/gpt-xhigh/s0/assessment.md) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/file-readability/results.md) | s0 |
| `tg07-eleventy-decided-work-tracking` | glm max | 3/3 | navigable | 2 | [s0](scenarios/tg07-eleventy-decided-work-tracking/glm-max/s0/assessment.md) | [results](scenarios/tg07-eleventy-decided-work-tracking/assessment/file-readability/results.md) | s0 |
| `tg07-eleventy-decided-work-tracking` | gpt high | 3/3 | navigable | 2 | [s0](scenarios/tg07-eleventy-decided-work-tracking/gpt-high/s0/assessment.md) | [results](scenarios/tg07-eleventy-decided-work-tracking/assessment/file-readability/results.md) | s0 |
| `tg08-eleventy-contributor-docs` | glm max | 4/5 | navigable | 6 | [s0](scenarios/tg08-eleventy-contributor-docs/glm-max/s0/assessment.md) | [results](scenarios/tg08-eleventy-contributor-docs/assessment/file-readability/results.md) | s0 |
| `tg08-eleventy-contributor-docs` | gpt high | 3/4 | navigable | 4 | [s0](scenarios/tg08-eleventy-contributor-docs/gpt-high/s0/assessment.md) | [results](scenarios/tg08-eleventy-contributor-docs/assessment/file-readability/results.md) | s0 |
| `tg09-flask-vue-deployment-runbook` | glm max | 4/4 | navigable | 4 | [s0](scenarios/tg09-flask-vue-deployment-runbook/glm-max/s0/assessment.md) | [results](scenarios/tg09-flask-vue-deployment-runbook/assessment/file-readability/results.md) | s0 |
| `tg10-flask-vue-interface-copy` | glm max | 6/6 | navigable | 5 | [s0](scenarios/tg10-flask-vue-interface-copy/glm-max/s0/assessment.md) | [results](scenarios/tg10-flask-vue-interface-copy/assessment/file-readability/results.md) | s0 |

## Per-scenario results

| Scenario | Numbers | Cells | Task-creation | Handoff | Quality | Plan content | Fidelity | Readability |
|---|---|---|---|---|---|---|---|---|
| `tg01-eleventy-archive-handoff` | — | [glm-max](scenarios/tg01-eleventy-archive-handoff/glm-max/index.md) · [gpt-high](scenarios/tg01-eleventy-archive-handoff/gpt-high/index.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/task-creation/results.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/handoff/results.md) | — | [results](scenarios/tg01-eleventy-archive-handoff/assessment/plan-content/results.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/file-fidelity/results.md) | [results](scenarios/tg01-eleventy-archive-handoff/assessment/file-readability/results.md) |
| `tg02-fastapi-pagination-handoff` | — | [glm-max](scenarios/tg02-fastapi-pagination-handoff/glm-max/index.md) · [gpt-high](scenarios/tg02-fastapi-pagination-handoff/gpt-high/index.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/task-creation/results.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/handoff/results.md) | — | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/plan-content/results.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/file-fidelity/results.md) | [results](scenarios/tg02-fastapi-pagination-handoff/assessment/file-readability/results.md) |
| `tg03-flask-vue-refresh-handoff` | — | [glm-max](scenarios/tg03-flask-vue-refresh-handoff/glm-max/index.md) · [gpt-high](scenarios/tg03-flask-vue-refresh-handoff/gpt-high/index.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/task-creation/results.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/handoff/results.md) | — | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/plan-content/results.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/file-fidelity/results.md) | [results](scenarios/tg03-flask-vue-refresh-handoff/assessment/file-readability/results.md) |
| `tg04-flask-vue-discovery-decomposition` | — | [glm-max](scenarios/tg04-flask-vue-discovery-decomposition/glm-max/index.md) · [gpt-high](scenarios/tg04-flask-vue-discovery-decomposition/gpt-high/index.md) · [gpt-max](scenarios/tg04-flask-vue-discovery-decomposition/gpt-max/index.md) · [gpt-xhigh](scenarios/tg04-flask-vue-discovery-decomposition/gpt-xhigh/index.md) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-creation/results.md) | — | — | — | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/file-fidelity/results.md) | [results](scenarios/tg04-flask-vue-discovery-decomposition/assessment/file-readability/results.md) |
| `tg05-fastapi-multi-consumer-decomposition` | — | [glm-max](scenarios/tg05-fastapi-multi-consumer-decomposition/glm-max/index.md) · [gpt-high](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-high/index.md) · [gpt-max](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-max/index.md) · [gpt-xhigh](scenarios/tg05-fastapi-multi-consumer-decomposition/gpt-xhigh/index.md) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/task-creation/results.md) | — | — | — | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/file-fidelity/results.md) | [results](scenarios/tg05-fastapi-multi-consumer-decomposition/assessment/file-readability/results.md) |
| `tg06-eleventy-author-migration-decomposition` | — | [glm-max](scenarios/tg06-eleventy-author-migration-decomposition/glm-max/index.md) · [gpt-high](scenarios/tg06-eleventy-author-migration-decomposition/gpt-high/index.md) · [gpt-max](scenarios/tg06-eleventy-author-migration-decomposition/gpt-max/index.md) · [gpt-xhigh](scenarios/tg06-eleventy-author-migration-decomposition/gpt-xhigh/index.md) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/task-creation/results.md) | — | — | — | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/file-fidelity/results.md) | [results](scenarios/tg06-eleventy-author-migration-decomposition/assessment/file-readability/results.md) |
| `tg07-eleventy-decided-work-tracking` | — | [glm-max](scenarios/tg07-eleventy-decided-work-tracking/glm-max/index.md) · [gpt-high](scenarios/tg07-eleventy-decided-work-tracking/gpt-high/index.md) | [results](scenarios/tg07-eleventy-decided-work-tracking/assessment/task-creation/results.md) | — | — | — | [results](scenarios/tg07-eleventy-decided-work-tracking/assessment/file-fidelity/results.md) | [results](scenarios/tg07-eleventy-decided-work-tracking/assessment/file-readability/results.md) |
| `tg08-eleventy-contributor-docs` | — | [glm-max](scenarios/tg08-eleventy-contributor-docs/glm-max/index.md) · [gpt-high](scenarios/tg08-eleventy-contributor-docs/gpt-high/index.md) | [results](scenarios/tg08-eleventy-contributor-docs/assessment/task-creation/results.md) | — | — | — | [results](scenarios/tg08-eleventy-contributor-docs/assessment/file-fidelity/results.md) | [results](scenarios/tg08-eleventy-contributor-docs/assessment/file-readability/results.md) |
| `tg09-flask-vue-deployment-runbook` | — | [glm-max](scenarios/tg09-flask-vue-deployment-runbook/glm-max/index.md) · [gpt-high](scenarios/tg09-flask-vue-deployment-runbook/gpt-high/index.md) | [results](scenarios/tg09-flask-vue-deployment-runbook/assessment/task-creation/results.md) | — | — | — | [results](scenarios/tg09-flask-vue-deployment-runbook/assessment/file-fidelity/results.md) | [results](scenarios/tg09-flask-vue-deployment-runbook/assessment/file-readability/results.md) |
| `tg10-flask-vue-interface-copy` | — | [glm-max](scenarios/tg10-flask-vue-interface-copy/glm-max/index.md) · [gpt-high](scenarios/tg10-flask-vue-interface-copy/gpt-high/index.md) | [results](scenarios/tg10-flask-vue-interface-copy/assessment/task-creation/results.md) | — | — | — | [results](scenarios/tg10-flask-vue-interface-copy/assessment/file-fidelity/results.md) | [results](scenarios/tg10-flask-vue-interface-copy/assessment/file-readability/results.md) |
