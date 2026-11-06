# Cell `tg01-eleventy-archive-handoff` — `gpt-high`

- Model: `gpt-6-luna` (profile `gpt`, effort `high`)
- [Scenario results](../results.md) — every number for the scenario

## Runs

### `task-creation` — s0 (valid)

- [Session](s0/session.md) — includes the prompt and response
- [Assessment](s0/assessment.md) — the grades judging this run
- Task file [`20261029-blog-archive-pagination.md`](s0/task-files/tasks/20261029-blog-archive-pagination.md)
- [Delivered instructions](../../../shared/system-messages/gpt-c419e5877d27.md) — reconstructed (original SHA-256 `f3389a19da8f1cfa…`)
- [Effective config](../../../shared/configs/gpt-high.json)

### `plan-retain` — s0 (valid)

- [Session](plan-retain/s0/session.md) — includes the prompt and response
- [Assessment](plan-retain/s0/assessment.md) — the grades judging this run
- Task file [`20260919-tg01-eleventy-archive-handoff.md`](plan-retain/s0/task-files/tasks/20260919-tg01-eleventy-archive-handoff.md)
- [Delivered instructions](../../../shared/system-messages/gpt-c419e5877d27.md) — reconstructed (original SHA-256 `e204a4f79f00529d…`)
- [Effective config](../../../shared/configs/gpt-high.json)

### `plan-omit` — s0 (invalid)

- [Session](plan-omit/s0/session.md) — includes the prompt and response
- [Invalid sample note](plan-omit/s0/invalid.md)
- Task file [`20260919-tg01-eleventy-archive-handoff.md`](plan-omit/s0/task-files/tasks/20260919-tg01-eleventy-archive-handoff.md)
- [Delivered instructions](../../../shared/system-messages/gpt-c419e5877d27.md) — reconstructed (original SHA-256 `d038c532f9db3a9f…`)
- [Effective config](../../../shared/configs/gpt-high.json)
- Invalid because: run failure: None, ('OpenAI Responses stream failed: Error code: 401 - {\'error\': {\'message\': \'authentication failed (status=503): {"error":"Too many concurrent requests"}\', \'type\': \'authentication_error\', \'param\': None, \'code\': None}}',); empty planning response

### `continuation` — s0 (valid)

- [Session](continuation/s0/session.md) — includes the prompt and response
- [Assessment](continuation/s0/assessment.md) — the grades judging this run
- Task file [`20261029-blog-archive-pagination.md`](continuation/s0/task-files/tasks/20261029-blog-archive-pagination.md)
- [Delivered instructions](../../../shared/system-messages/gpt-c419e5877d27.md) — inherited (original SHA-256 `f3389a19da8f1cfa…`)
- [Effective config](../../../shared/configs/gpt-high.json)
- Continuation parent run: `20261029T181443.555227Z-task-guidance-tg01-eleventy-archive-handoff-high-266502a3`

### `generated-plan` — s0 (valid)

- [Session](generated-plan/s0/session.md) — includes the prompt and response
- [Assessment](generated-plan/s0/assessment.md) — the grades judging this run
- Task file [`20261029-blog-archive-pagination.md`](generated-plan/s0/task-files/tasks/20261029-blog-archive-pagination.md)
- Delivered instructions: **unavailable**
- [Effective config](../../../shared/configs/gpt-high.json)

## Assessor runs

Judgments of this cell's evidence; grades sit beside the judged sample as `assessment.md`.

- [`assessment/file-fidelity/s0`](assessment/file-fidelity/s0/session.md)
- [`assessment/file-readability/s0`](assessment/file-readability/s0/session.md)
- [`assessment/handoff/generated-file/s0`](assessment/handoff/generated-file/s0/session.md)
- [`assessment/handoff/generated-task/s0`](assessment/handoff/generated-task/s0/session.md)
- [`assessment/handoff/retain/s0`](assessment/handoff/retain/s0/session.md)
- [`assessment/plan-content/generated-file/s0`](assessment/plan-content/generated-file/s0/session.md)
- [`assessment/plan-content/generated-task/s0`](assessment/plan-content/generated-task/s0/session.md)
- [`assessment/plan-content/retain/s0`](assessment/plan-content/retain/s0/session.md)
- [`assessment/task-creation/s0`](assessment/task-creation/s0/session.md)

Assessment summaries:

- [Task-creation semantic results](../assessment/task-creation/results.md)
- [Handoff semantic results](../assessment/handoff/results.md)
- [Presented-plan content results](../assessment/plan-content/results.md)
- [Task-file fidelity results](../assessment/file-fidelity/results.md)
- [Task-file readability results](../assessment/file-readability/results.md)
