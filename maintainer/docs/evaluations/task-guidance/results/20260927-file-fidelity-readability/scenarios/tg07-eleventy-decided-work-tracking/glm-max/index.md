# Cell `tg07-eleventy-decided-work-tracking` — `glm-max`

- Model: `glm-5.3-flash:cloud` (profile `glm`, effort `max`)
- [Scenario results](../results.md) — every number for the scenario

## Runs

### `task-creation` — s0 (valid)

- [Session](s0/session.md) — includes the prompt and response
- [Assessment](s0/assessment.md) — the grades judging this run
- Task file [`20260926-blog-archive-fifteen-per-page.md`](s0/task-files/tasks/20260926-blog-archive-fifteen-per-page.md)
- [Delivered instructions](../../../shared/system-messages/glm-b940ffcd2153.md) — captured (original SHA-256 `bae356f008c8c0d5…`)
- [Effective config](../../../shared/configs/glm-max.json)

### `task-creation` — s1 (valid)

- [Session](s1/session.md) — includes the prompt and response
- [Assessment](s1/assessment.md) — the grades judging this run
- Task file [`20260926-blog-archive-fifteen-per-page.md`](s1/task-files/tasks/20260926-blog-archive-fifteen-per-page.md)
- [Delivered instructions](../../../shared/system-messages/glm-b940ffcd2153.md) — captured (original SHA-256 `4d9fac5161687977…`)
- [Effective config](../../../shared/configs/glm-max.json)

### `task-creation` — s2 (invalid)

- [Session](s2/session.md) — includes the prompt and response
- [Invalid sample note](s2/invalid.md)
- Task file [`20260926-blog-archive-page-size.md`](s2/task-files/tasks/20260926-blog-archive-page-size.md)
- [Delivered instructions](../../../shared/system-messages/glm-b940ffcd2153.md) — captured (original SHA-256 `e4f706753e15ad7a…`)
- [Effective config](../../../shared/configs/glm-max.json)
- Invalid because: execution-plan expectation violated: tasks/20260926-blog-archive-page-size.md: execution plan present without a draft status

## Assessor runs

Judgments of this cell's evidence; grades sit beside the judged sample as `assessment.md`.

- [`assessment/file-fidelity/s0`](assessment/file-fidelity/s0/session.md)
- [`assessment/file-fidelity/s1`](assessment/file-fidelity/s1/session.md)
- [`assessment/file-readability/s0`](assessment/file-readability/s0/session.md)
- [`assessment/file-readability/s1`](assessment/file-readability/s1/session.md)
- [`assessment/task-creation/s0`](assessment/task-creation/s0/session.md)
- [`assessment/task-creation/s1`](assessment/task-creation/s1/session.md)
- [`assessment/task-quality/s0`](assessment/task-quality/s0/session.md)
- [`assessment/task-quality/s1`](assessment/task-quality/s1/session.md)

Assessment summaries:

- [Task-creation semantic results](../assessment/task-creation/results.md)
- [Task-file quality results](../assessment/task-quality/results.md)
- [Task-file fidelity results](../assessment/file-fidelity/results.md)
- [Task-file readability results](../assessment/file-readability/results.md)
