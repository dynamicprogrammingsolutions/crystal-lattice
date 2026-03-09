# OpenRouter Responses API Provider (Streaming + Tools)

Short description: Add a first-class OpenRouter provider that calls the `/responses` endpoint (including streaming) while keeping existing tools/providers working with minimal change. Introduce a lightweight one-direction adapter + accessor layer for tool schemas and tool calls so the provider can speak Responses-native wire formats without forcing an immediate repo-wide tool schema refactor.

## Subtasks

1. `tasks/20260309-openrouter-responses-provider/010-tool-schema-and-call-adapters-and-accessors.md`
2. `tasks/20260309-openrouter-responses-provider/020-implement-openrouter-responses-provider.md`

Suggested execution order: `010` -> `020`.

## Context / motivation

- The existing OpenRouter provider targets `/chat/completions` and assumes OpenAI chat-completions streaming chunk shapes.
- OpenRouter’s `/responses` endpoint is desired (including streaming) and should be treated as first-class, not as “Responses but converted into chat-completions on the hot path”.
- The current tool ecosystem is explicitly “OpenAI-style” (`ToolPlugin.get_tool_schemas`) and the tool loop expects `assistant.metadata.tool_calls` in OpenAI-ish shapes.

This task keeps OpenAI-ish tool schemas/calls as the *canonical internal representation for now*, and introduces small adapter classes (one direction each) plus accessor classes (read-only “views”) to reduce tight coupling to a single wire format.
