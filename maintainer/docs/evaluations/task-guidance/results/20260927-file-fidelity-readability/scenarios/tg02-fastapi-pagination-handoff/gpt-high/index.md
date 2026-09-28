# Cell `tg02-fastapi-pagination-handoff` — `gpt-high`

- Model: `gpt-5.6-luna` (profile `gpt`, effort `high`)
- [Scenario results](../results.md) — every number for the scenario

## Runs

### `task-creation` — s0 (valid)

- [Session](s0/session.md) — includes the prompt and response
- [Assessment](s0/assessment.md) — the grades judging this run
- Task file [`20260926-notes-pagination.md`](s0/task-files/tasks/20260926-notes-pagination.md)
- [Delivered instructions](../../../shared/system-messages/gpt-818f4bf8bc2b.md) — reconstructed (original SHA-256 `ff25ba59c77d0874…`)
- [Effective config](../../../shared/configs/gpt-high.json)

### `plan-retain` — s0 (valid)

- [Session](plan-retain/s0/session.md) — includes the prompt and response
- [Assessment](plan-retain/s0/assessment.md) — the grades judging this run
- Task file [`20260919-tg02-fastapi-pagination-handoff.md`](plan-retain/s0/task-files/tasks/20260919-tg02-fastapi-pagination-handoff.md)
- [Delivered instructions](../../../shared/system-messages/gpt-818f4bf8bc2b.md) — reconstructed (original SHA-256 `75f4cbd27ce5de1a…`)
- [Effective config](../../../shared/configs/gpt-high.json)

### `plan-omit` — s0 (valid)

- [Session](plan-omit/s0/session.md) — includes the prompt and response
- [Assessment](plan-omit/s0/assessment.md) — the grades judging this run
- Task file [`20260919-tg02-fastapi-pagination-handoff.md`](plan-omit/s0/task-files/tasks/20260919-tg02-fastapi-pagination-handoff.md)
- [Delivered instructions](../../../shared/system-messages/gpt-818f4bf8bc2b.md) — reconstructed (original SHA-256 `fc151b3d50ece5bc…`)
- [Effective config](../../../shared/configs/gpt-high.json)

### `continuation` — s0 (invalid)

- [Session](continuation/s0/session.md) — includes the prompt and response
- [Invalid sample note](continuation/s0/invalid.md)
- Task file [`20260926-notes-pagination.md`](continuation/s0/task-files/tasks/20260926-notes-pagination.md)
- [Delivered instructions](../../../shared/system-messages/gpt-818f4bf8bc2b.md) — inherited (original SHA-256 `ff25ba59c77d0874…`)
- [Effective config](../../../shared/configs/gpt-high.json)
- Continuation parent run: `20260925T224417.914181Z-task-guidance-tg02-fastapi-pagination-handoff-high-9058ec68`
- Invalid because: run failure: None, ("OpenAI Responses stream failed: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-svcac***********************************************************************************************************************************************************fvMA. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_api_key'}}",)

### `generated-plan` — s0 (valid)

- [Session](generated-plan/s0/session.md) — includes the prompt and response
- [Assessment](generated-plan/s0/assessment.md) — the grades judging this run
- Task file [`20260926-notes-pagination.md`](generated-plan/s0/task-files/tasks/20260926-notes-pagination.md)
- Delivered instructions: **unavailable**
- [Effective config](../../../shared/configs/gpt-high.json)

## Assessor runs

Judgments of this cell's evidence; grades sit beside the judged sample as `assessment.md`.

- [`assessment/file-fidelity/s0`](assessment/file-fidelity/s0/session.md)
- [`assessment/file-readability/s0`](assessment/file-readability/s0/session.md)
- [`assessment/handoff/generated-file/s0`](assessment/handoff/generated-file/s0/session.md)
- [`assessment/handoff/omit/s0`](assessment/handoff/omit/s0/session.md)
- [`assessment/handoff/retain/s0`](assessment/handoff/retain/s0/session.md)
- [`assessment/plan-content/generated-file/s0`](assessment/plan-content/generated-file/s0/session.md)
- [`assessment/plan-content/omit/s0`](assessment/plan-content/omit/s0/session.md)
- [`assessment/plan-content/retain/s0`](assessment/plan-content/retain/s0/session.md)
- [`assessment/task-creation/s0`](assessment/task-creation/s0/session.md)
- [`assessment/task-quality/s0`](assessment/task-quality/s0/session.md)

Assessment summaries:

- [Task-creation semantic results](../assessment/task-creation/results.md)
- [Handoff semantic results](../assessment/handoff/results.md)
- [Task-file quality results](../assessment/task-quality/results.md)
- [Presented-plan content results](../assessment/plan-content/results.md)
- [Task-file fidelity results](../assessment/file-fidelity/results.md)
- [Task-file readability results](../assessment/file-readability/results.md)
