# Tools Extension Responses API

Short description: Implement tool-specific logic in `openai_responses_tools` extension: request schema injection, tool-call accumulation/reconstruction, and metadata mapping.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On: `tasks/20260310-openai-responses-provider/040-provider-streaming-event-normalization-and-finalization.md`

## Implementation

1. Implement extension tags/required tags for provider scoping.
2. Inject tool schemas into request payload via `initialize_request`.
3. Reuse `agent_core.tool_interop` adapters for schema and tool-call conversion.
4. Parse/accumulate streaming tool-call events in extension hot path.
5. Surface canonical `metadata.tool_calls` and preserve `tool_call_id` mappings.
6. Keep provider free of this tool-specific behavior.

## Tests (required in this step)

1. Unit tests for schema conversion and request payload injection.
2. Unit tests for streaming tool-call delta accumulation and argument stitching.
3. Round-trip metadata mapping tests (`to_native_messages`/`from_native_messages`).
4. Integration test: single-turn + multi-turn tool loop execution.

## References

- `core/python/agent_core/tool_interop.py`
- `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_tools_extension.py`
- `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/tools_extension.py`
