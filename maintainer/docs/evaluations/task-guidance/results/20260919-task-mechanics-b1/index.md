# task-mechanics candidate result package

- Dataset: `task-guidance-b1-20260919`
- Producer attempt: `b1-v1-r1`
- Handoff attempt: `b1-v1-r1`
- Semantic attempt: `b1-metrics1`

This package preserves the completed evaluation's reviewed inputs, model outputs, execution context, semantic assessments, and usage evidence. Every navigation, matrix, and cost view regenerates deterministically from the committed records.

## Navigation

- [Quality matrix](matrix.md) — status and semantic dimensions.
- [Usage and estimated cost](costs.md) — one row per run.
- [Scenario cells and assessments](#scenarios) below.

## Scenarios

- [`tg01-eleventy-archive-handoff`](scenarios/tg01-eleventy-archive-handoff/index.md)
- [`tg02-fastapi-pagination-handoff`](scenarios/tg02-fastapi-pagination-handoff/index.md)
- [`tg03-flask-vue-refresh-handoff`](scenarios/tg03-flask-vue-refresh-handoff/index.md)
- [`tg04-flask-vue-discovery-decomposition`](scenarios/tg04-flask-vue-discovery-decomposition/index.md)
- [`tg05-fastapi-multi-consumer-decomposition`](scenarios/tg05-fastapi-multi-consumer-decomposition/index.md)
- [`tg06-eleventy-author-migration-decomposition`](scenarios/tg06-eleventy-author-migration-decomposition/index.md)

## Known limitations

- Historical GLM runs saved no provider usage metadata; their usage and estimated cost remain unknown.
- GPT same-agent continuation runs recorded no compiled-message hash; their delivered instructions are inherited from the producer run's verified message instead of reconstructed independently.
- Session transcripts omit full tool-result content and encrypted reasoning; concise failure excerpts are retained.
