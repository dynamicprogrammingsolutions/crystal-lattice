# Architecture Scope And Boundaries

Short description: Lock architecture and responsibilities before implementation so the provider stays thin and domain behavior remains in extensions.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On: None

## Goals

1. Define exact provider vs extension boundaries.
2. Define v1 extension set: tools, reasoning, usage, verbosity.
3. Define test matrix required for every implementation subtask.

## Decisions

1. Package name: `openai_responses`.
2. Transport: OpenAI Python SDK.
3. Provider responsibilities:
- config/model discovery/tags
- request initialization
- core<->native conversion for generic Responses items
- streaming frame/event normalization and lifecycle boundaries
4. Extension responsibilities:
- tools: schema injection + tool call reconstruction + tool metadata mapping
- reasoning: request knobs + reasoning extraction/metadata
- usage: usage extraction and formatting metadata
- verbosity: request payload shaping for verbosity

## Required invariants

1. Provider must not absorb extension domain logic except minimal unavoidable glue.
2. All implementation subtasks must include tests in same PR/change.
3. Native history remains coherent across turns, slice/fork, and cross-core reload scenarios.

## Reference files consulted

- `plugins/docs/provider-plugins.md`
- `plugins/docs/provider-extensions.md`
- `plugins/docs/plugin-execution-order.md`
- `core/python/agent_core/plugin/provider.py`
- `core/python/agent_core/tool_interop.py`
- `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py`

## Completion notes (done during planning handoff)

- Completed by producing the parent task and concrete implementation subtasks.
- No code changes required for this subtask.
