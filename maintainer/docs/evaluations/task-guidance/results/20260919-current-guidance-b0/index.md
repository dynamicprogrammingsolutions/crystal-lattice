# current-guidance baseline result package

- Dataset: `task-guidance-b0-20260919`
- Producer attempt: `b0-v5-r1`
- Handoff attempt: `b0-v5-r1`
- Semantic attempt: `b0-metrics1`

This package preserves the completed evaluation's reviewed inputs, model outputs, execution context, semantic assessments, and usage evidence. Every navigation, matrix, and cost view regenerates deterministically from the committed records.

## Navigation

- [Quality matrix](matrix.md) — status and semantic dimensions.
- [Usage and estimated cost](costs.md) — one row per run.
- [Scenario cells and assessments](#scenarios) below.

## Scenarios

- [`tg01-eleventy-archive-handoff`](cases/tg01-eleventy-archive-handoff/index.md)
- [`tg02-fastapi-pagination-handoff`](cases/tg02-fastapi-pagination-handoff/index.md)
- [`tg03-flask-vue-refresh-handoff`](cases/tg03-flask-vue-refresh-handoff/index.md)
- [`tg04-flask-vue-discovery-decomposition`](cases/tg04-flask-vue-discovery-decomposition/index.md)
- [`tg05-fastapi-multi-consumer-decomposition`](cases/tg05-fastapi-multi-consumer-decomposition/index.md)
- [`tg06-eleventy-author-migration-decomposition`](cases/tg06-eleventy-author-migration-decomposition/index.md)

## Known limitations

- Historical GLM runs saved no provider usage metadata; their usage and estimated cost remain unknown.
- GPT same-agent continuation runs recorded no compiled-message hash, so their delivered instructions stay unavailable rather than reconstructed without verification.
- Session transcripts omit full tool-result content and encrypted reasoning; concise failure excerpts are retained.
