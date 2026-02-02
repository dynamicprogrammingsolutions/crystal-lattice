Parent Task: tasks/20260130-openrouter-usage-round-cost-and-ui-schema/000-main.md

Depends On:
- tasks/20260130-openrouter-usage-round-cost-and-ui-schema/010-config-aware-ui-schema-and-conditions.md

# Token breakdown + per-session UI toggles

Add UI-configurable footers for token breakdown (prompt/completion/reasoning tokens) and make them switchable per session.

## Background (real usage shape)

From `./.crystal/sessions/6d016aaf-bec9-491c-ba44-8b6dbb5944bd.json`, OpenRouter returns usage like:

- `usage.prompt_tokens`
- `usage.completion_tokens`
- `usage.total_tokens`
- `usage.prompt_tokens_details.cached_tokens`
- `usage.completion_tokens_details.reasoning_tokens`

## Goals

- Provide config switches (per session overrides) to show/hide:
  - Prompt tokens
  - Completion tokens
  - Reasoning tokens (from `completion_tokens_details.reasoning_tokens`)
- Prefer not to add more metadata than necessary; the raw `usage` dict is already mirrored into core message metadata.

## Proposed config keys (per session overrides)

Recommended keys (names can be bikeshedded, but keep them unambiguous):

- `openrouter_usage_show_prompt_tokens: bool`
- `openrouter_usage_show_completion_tokens: bool`
- `openrouter_usage_show_reasoning_tokens: bool`

Optional:

- `openrouter_usage_show_cached_tokens: bool`

## UI elements

With config-aware UI schema (Subtask 010), have the usage extension return different `message_footer` elements depending on config.

Example footer elements (no extra metadata required):

- Prompt tokens:
  - `data: "metadata.usage.prompt_tokens"`
  - `template: "prompt: {{data}}"`
- Completion tokens:
  - `data: "metadata.usage.completion_tokens"`
  - `template: "completion: {{data}}"`
- Reasoning tokens:
  - `data: "metadata.usage.completion_tokens_details.reasoning_tokens"`
  - `template: "reasoning: {{data}}"`

Notes:

- These will naturally render only on messages where `metadata.usage` exists.
- If you want nicer formatting (commas), you can add formatted strings similarly to how `usage_total_tokens_formatted` is done today.

## Acceptance criteria

- The OpenRouter usage extension exposes toggles as config UI elements.
- Footers appear/disappear per session when overrides change.
- Reasoning token footer works for models returning `completion_tokens_details.reasoning_tokens`.
