# Cell `tg01-eleventy-archive-handoff` — `gpt-high`

- Model: `gpt-5.6-luna` (profile `gpt`, effort `high`)
- [Scenario results](../results.md) — every number for the scenario

## Runs

### `task-creation` — s0 (valid)

- [Session](s0/session.md) — includes the prompt and response
- [Assessment](s0/assessment.md) — the grades judging this run
- Task file [`20260926-blog-archive-pagination.md`](s0/task-files/tasks/20260926-blog-archive-pagination.md)
- [Delivered instructions](../../../shared/system-messages/gpt-06e58964b231.md) — reconstructed (original SHA-256 `0a250395e7101c33…`)
- [Effective config](../../../shared/configs/gpt-high.json)

### `plan-retain` — s0 (valid)

- [Session](plan-retain/s0/session.md) — includes the prompt and response
- [Assessment](plan-retain/s0/assessment.md) — the grades judging this run
- Task file [`20260919-tg01-eleventy-archive-handoff.md`](plan-retain/s0/task-files/tasks/20260919-tg01-eleventy-archive-handoff.md)
- [Delivered instructions](../../../shared/system-messages/gpt-06e58964b231.md) — reconstructed (original SHA-256 `87ce1c0a1cedac18…`)
- [Effective config](../../../shared/configs/gpt-high.json)

### `plan-omit` — s0 (valid)

- [Session](plan-omit/s0/session.md) — includes the prompt and response
- [Assessment](plan-omit/s0/assessment.md) — the grades judging this run
- Task file [`20260919-tg01-eleventy-archive-handoff.md`](plan-omit/s0/task-files/tasks/20260919-tg01-eleventy-archive-handoff.md)
- [Delivered instructions](../../../shared/system-messages/gpt-06e58964b231.md) — reconstructed (original SHA-256 `cd6b68eb5d7944d4…`)
- [Effective config](../../../shared/configs/gpt-high.json)

### `continuation` — s0 (valid)

- [Session](continuation/s0/session.md) — includes the prompt and response
- [Assessment](continuation/s0/assessment.md) — the grades judging this run
- Task file [`20260926-blog-archive-pagination.md`](continuation/s0/task-files/tasks/20260926-blog-archive-pagination.md)
- [Delivered instructions](../../../shared/system-messages/gpt-06e58964b231.md) — inherited (original SHA-256 `0a250395e7101c33…`)
- [Effective config](../../../shared/configs/gpt-high.json)
- Continuation parent run: `20260926T053403.233318Z-task-guidance-tg01-eleventy-archive-handoff-high-0ba9d42c`

### `continuation` — s1 (invalid)

- [Session](continuation/s1/session.md) — includes the prompt and response
- [Invalid sample note](continuation/s1/invalid.md)
- Task file [`20260926-blog-archive-pagination.md`](continuation/s1/task-files/tasks/20260926-blog-archive-pagination.md)
- [Delivered instructions](../../../shared/system-messages/gpt-06e58964b231.md) — inherited (original SHA-256 `0a250395e7101c33…`)
- [Effective config](../../../shared/configs/gpt-high.json)
- Continuation parent run: `20260925T224337.764438Z-task-guidance-tg01-eleventy-archive-handoff-high-92f179b9`
- Invalid because: run failure: None, ("OpenAI Responses stream failed: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-svcac***********************************************************************************************************************************************************fvMA. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_api_key'}}",)

### `generated-plan` — s0 (valid)

- [Session](generated-plan/s0/session.md) — includes the prompt and response
- [Assessment](generated-plan/s0/assessment.md) — the grades judging this run
- Task file [`20260926-blog-archive-pagination.md`](generated-plan/s0/task-files/tasks/20260926-blog-archive-pagination.md)
- Delivered instructions: **unavailable**
- [Effective config](../../../shared/configs/gpt-high.json)

## Assessor runs

Judgments of this cell's evidence; grades sit beside the judged sample as `assessment.md`.

- [`assessment/handoff/generated-file/s0`](assessment/handoff/generated-file/s0/session.md)
- [`assessment/handoff/generated-task/s0`](assessment/handoff/generated-task/s0/session.md)
- [`assessment/handoff/omit/s0`](assessment/handoff/omit/s0/session.md)
- [`assessment/handoff/retain/s0`](assessment/handoff/retain/s0/session.md)
- [`assessment/task-creation/s0`](assessment/task-creation/s0/session.md)
- [`assessment/task-quality/s0`](assessment/task-quality/s0/session.md)

Assessment summaries:

- [Task-creation semantic results](../assessment/task-creation/results.md)
- [Handoff semantic results](../assessment/handoff/results.md)
- [Task-file quality results](../assessment/task-quality/results.md)
