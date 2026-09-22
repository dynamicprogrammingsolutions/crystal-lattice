# Task-guidance evaluation scenarios

Scenario definitions and stage inputs for the task-guidance evaluation suite, generated from the suite sources in `maintainer/agent-evaluation/suites/task_guidance/` (`result_package.py extract-scenarios`) with the guidance bundle `maintainer/guidance/current`.

These definitions may change between evaluations; git tracks their evolution here while each result package under `../results/` freezes its own copies of the material it was produced with.

## Shared inputs

| Material | Contents |
|---|---|
| [configs](shared/configs/) | sanitized effective configurations per profile |
| [system-messages](shared/system-messages/) | compiled delivered instructions per provider and project family |
| [included-files](shared/included-files/) | every file added to the workspaces: fixture projects, guidance compilation, assessor stub |

## Prompt templates

| Template | Used by |
|---|---|
| [handoff-plan-prompt.md](templates/handoff-plan-prompt.md) | fresh planning agents and same-agent continuations |
| [task-creation-assessment-prompt.md](templates/task-creation-assessment-prompt.md) | task-creation semantic assessor |
| [handoff-assessment-prompt.md](templates/handoff-assessment-prompt.md) | handoff semantic assessor |

## Scenarios

| Scenario | Reviewed target | Producer prompt | Stage inputs |
|---|---|---|---|
| `tg01-eleventy-archive-handoff` | [target](tg01-eleventy-archive-handoff/target.md) | [prompt](tg01-eleventy-archive-handoff/prompt.md) | [task-creation](tg01-eleventy-archive-handoff/task-creation/input.md) · [plan-retain](tg01-eleventy-archive-handoff/plan-retain/input.md) · [plan-omit](tg01-eleventy-archive-handoff/plan-omit/input.md) · [continuation](tg01-eleventy-archive-handoff/continuation/input.md) · assessments: [task-creation](tg01-eleventy-archive-handoff/assessment/task-creation/input.md) · [handoff](tg01-eleventy-archive-handoff/assessment/handoff/input.md) |
| `tg02-fastapi-pagination-handoff` | [target](tg02-fastapi-pagination-handoff/target.md) | [prompt](tg02-fastapi-pagination-handoff/prompt.md) | [task-creation](tg02-fastapi-pagination-handoff/task-creation/input.md) · [plan-retain](tg02-fastapi-pagination-handoff/plan-retain/input.md) · [plan-omit](tg02-fastapi-pagination-handoff/plan-omit/input.md) · [continuation](tg02-fastapi-pagination-handoff/continuation/input.md) · [control](tg02-fastapi-pagination-handoff/control/input.md) · assessments: [task-creation](tg02-fastapi-pagination-handoff/assessment/task-creation/input.md) · [handoff](tg02-fastapi-pagination-handoff/assessment/handoff/input.md) |
| `tg03-flask-vue-refresh-handoff` | [target](tg03-flask-vue-refresh-handoff/target.md) | [prompt](tg03-flask-vue-refresh-handoff/prompt.md) | [task-creation](tg03-flask-vue-refresh-handoff/task-creation/input.md) · [plan-retain](tg03-flask-vue-refresh-handoff/plan-retain/input.md) · [plan-omit](tg03-flask-vue-refresh-handoff/plan-omit/input.md) · [continuation](tg03-flask-vue-refresh-handoff/continuation/input.md) · assessments: [task-creation](tg03-flask-vue-refresh-handoff/assessment/task-creation/input.md) · [handoff](tg03-flask-vue-refresh-handoff/assessment/handoff/input.md) |
| `tg04-flask-vue-discovery-decomposition` | [target](tg04-flask-vue-discovery-decomposition/target.md) | [prompt](tg04-flask-vue-discovery-decomposition/prompt.md) | [task-creation](tg04-flask-vue-discovery-decomposition/task-creation/input.md) · assessments: [task-creation](tg04-flask-vue-discovery-decomposition/assessment/task-creation/input.md) |
| `tg05-fastapi-multi-consumer-decomposition` | [target](tg05-fastapi-multi-consumer-decomposition/target.md) | [prompt](tg05-fastapi-multi-consumer-decomposition/prompt.md) | [task-creation](tg05-fastapi-multi-consumer-decomposition/task-creation/input.md) · assessments: [task-creation](tg05-fastapi-multi-consumer-decomposition/assessment/task-creation/input.md) |
| `tg06-eleventy-author-migration-decomposition` | [target](tg06-eleventy-author-migration-decomposition/target.md) | [prompt](tg06-eleventy-author-migration-decomposition/prompt.md) | [task-creation](tg06-eleventy-author-migration-decomposition/task-creation/input.md) · assessments: [task-creation](tg06-eleventy-author-migration-decomposition/assessment/task-creation/input.md) |
