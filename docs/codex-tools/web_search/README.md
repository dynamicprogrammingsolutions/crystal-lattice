# `web_search`

Codex can optionally expose the OpenAI `web_search` tool.

## JSON tool specs

- `schema.cached.json` sets `external_web_access: false` (cached search).
- `schema.live.json` sets `external_web_access: true` (live internet access).

## Handler behavior (implementation notes)

This tool is implemented by the upstream OpenAI tool runtime (not by Codex core). Codex only controls whether it is present and whether it is configured for cached vs live access.
