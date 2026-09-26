# Cell `tg01-eleventy-archive-handoff` — `gpt-high`

- Model: `gpt-5.6-luna` (profile `gpt`, effort `high`)

## Runs

### `task-creation` (valid)

- [Session](session.md) — includes the prompt and response
- Task file [`20260926-blog-archive-pagination.md`](task-files/tasks/20260926-blog-archive-pagination.md)
- [Delivered instructions](../../../shared/system-messages/gpt-06e58964b231.md) — reconstructed (original SHA-256 `0a250395e7101c33…`)
- [Effective config](../../../shared/configs/gpt-high.json)

### `continuation` (invalid)

- [Session](continuation/session.md) — includes the prompt and response
- Task file [`20260926-blog-archive-pagination.md`](continuation/task-files/tasks/20260926-blog-archive-pagination.md)
- [Delivered instructions](../../../shared/system-messages/gpt-06e58964b231.md) — inherited (original SHA-256 `0a250395e7101c33…`)
- [Effective config](../../../shared/configs/gpt-high.json)
- Continuation parent run: `20260925T224337.764438Z-task-guidance-tg01-eleventy-archive-handoff-high-92f179b9`
- Invalid because: run failure: None, ("OpenAI Responses stream failed: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-svcac***********************************************************************************************************************************************************fvMA. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_api_key'}}",)

### `plan-omit` (valid)

- [Session](plan-omit/session.md) — includes the prompt and response
- Task file [`20260919-tg01-eleventy-archive-handoff.md`](plan-omit/task-files/tasks/20260919-tg01-eleventy-archive-handoff.md)
- [Delivered instructions](../../../shared/system-messages/gpt-06e58964b231.md) — reconstructed (original SHA-256 `cd6b68eb5d7944d4…`)
- [Effective config](../../../shared/configs/gpt-high.json)

### `plan-retain` (valid)

- [Session](plan-retain/session.md) — includes the prompt and response
- Task file [`20260919-tg01-eleventy-archive-handoff.md`](plan-retain/task-files/tasks/20260919-tg01-eleventy-archive-handoff.md)
- [Delivered instructions](../../../shared/system-messages/gpt-06e58964b231.md) — reconstructed (original SHA-256 `87ce1c0a1cedac18…`)
- [Effective config](../../../shared/configs/gpt-high.json)

## Assessment

- [Task-creation semantic results](../assessment/task-creation/results.md)
- [Handoff semantic results](../assessment/handoff/results.md)
