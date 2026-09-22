# Task-guidance evaluation scenarios

Scenario definitions for the task-guidance evaluation suite, generated from the suite sources in `maintainer/agent-evaluation/suites/task_guidance/` (`result_package.py extract-scenarios`).

These definitions may change between evaluations; git tracks their evolution here while each result package under `../results/` freezes its own copies of the material it was produced with.

## Prompt templates

| Template | Used by |
|---|---|
| [handoff-plan-prompt.md](templates/handoff-plan-prompt.md) | fresh planning agents in handoff scenarios |
| [task-creation-assessment-prompt.md](templates/task-creation-assessment-prompt.md) | task-creation semantic assessor |
| [handoff-assessment-prompt.md](templates/handoff-assessment-prompt.md) | handoff semantic assessor |

## Scenarios

| Scenario | Reviewed target | Producer prompt |
|---|---|---|
| `tg01-eleventy-archive-handoff` | [target](tg01-eleventy-archive-handoff/target.md) | [prompt](tg01-eleventy-archive-handoff/prompt.md) |
| `tg02-fastapi-pagination-handoff` | [target](tg02-fastapi-pagination-handoff/target.md) | [prompt](tg02-fastapi-pagination-handoff/prompt.md) |
| `tg03-flask-vue-refresh-handoff` | [target](tg03-flask-vue-refresh-handoff/target.md) | [prompt](tg03-flask-vue-refresh-handoff/prompt.md) |
| `tg04-flask-vue-discovery-decomposition` | [target](tg04-flask-vue-discovery-decomposition/target.md) | [prompt](tg04-flask-vue-discovery-decomposition/prompt.md) |
| `tg05-fastapi-multi-consumer-decomposition` | [target](tg05-fastapi-multi-consumer-decomposition/target.md) | [prompt](tg05-fastapi-multi-consumer-decomposition/prompt.md) |
| `tg06-eleventy-author-migration-decomposition` | [target](tg06-eleventy-author-migration-decomposition/target.md) | [prompt](tg06-eleventy-author-migration-decomposition/prompt.md) |
