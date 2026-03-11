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

## Execution plan (added during completion)

1. Implement `OpenAIResponsesToolsExtension` behavior for this subtask:
- keep provider scoping tags and required tags
- store tool schemas from config in shared state
- inject Responses-native tool schemas in `initialize_request` using `agent_core.tool_interop`
- implement assistant/tool metadata mapping in `to_native_messages` and `from_native_messages`
- implement streaming tool-call accumulation in `process_chunk`, including argument stitching and completed-event final patching
2. Enable tools extension activation by adding `supports_tools` provider capability tag in `openai_responses` provider.
3. Add unit tests for:
- schema conversion + request payload injection
- streaming tool-call delta accumulation and argument stitching
- round-trip metadata mapping for tool calls and `tool_call_id`
4. Add integration tests (fixture-backed, no live API dependency) covering single-turn and multi-turn tool loop execution with `AgentCore`.
5. Run relevant `plugins/openai_responses/tests` subsets and full package tests, then record completion notes in this task file.

## Completion notes (added during completion)

### What changed

1. Implemented `openai_responses_tools` extension behavior in `plugins/openai_responses/src/openai_responses_plugins/openai_responses_tools_extension.py`:
- request-time tool schema injection using `DEFAULT_TOOL_INTEROP_REGISTRY.convert_schemas(...)` with `OpenAIChatToolSchemaToOpenAIResponsesToolSchema`
- assistant `metadata.tool_calls` -> Responses-native `function_call` conversion in `to_native_messages`
- Responses-native `function_call` -> assistant `metadata.tool_calls` mapping in `from_native_messages` using `OpenAIResponsesToolCallToOpenAIChatToolCall`
- streaming tool-call event accumulation in `process_chunk` for:
  - `response.output_item.added`
  - `response.output_item.done`
  - `response.function_call_arguments.delta`
  - `response.function_call_arguments.done`
  - `response.completed`
- argument stitching and final-message patching on `response.completed` so canonical tool-call arguments survive streaming delta fragmentation

2. Enabled extension activation by adding `supports_tools` to provider capability tags in `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`.

3. Added tools-extension unit tests in `plugins/openai_responses/tests/test_openai_responses_tools_extension_unit.py`:
- schema conversion and payload injection
- streaming tool-call delta accumulation and stitched argument patching
- round-trip mapping for `tool_calls` and `tool_call_id`

4. Added fixture-backed integration tests (no live API dependency) in `plugins/openai_responses/tests/test_openai_responses_tools_extension_integration.py`:
- single-turn tool loop execution (assistant tool call -> `execute_tool_calls`)
- multi-turn tool loop execution with `function_call_output` continuity into second request

5. Updated provider tag expectation in `plugins/openai_responses/tests/test_openai_responses_provider_unit.py` to include `supports_tools`.

### Files touched

1. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_tools_extension.py`
2. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
3. `plugins/openai_responses/tests/test_openai_responses_tools_extension_unit.py`
4. `plugins/openai_responses/tests/test_openai_responses_tools_extension_integration.py`
5. `plugins/openai_responses/tests/test_openai_responses_provider_unit.py`
6. `tasks/20260310-openai-responses-provider/050-tools-extension-responses-api.md`

### Tests run

1. `pytest plugins/openai_responses/tests/test_openai_responses_tools_extension_unit.py -q`
- result: `3 passed`

2. `pytest plugins/openai_responses/tests/test_openai_responses_tools_extension_integration.py -q`
- result: `2 passed`

3. `pytest plugins/openai_responses/tests -q`
- result: `34 passed`

### Outcomes

1. Subtask 050 scope implemented and validated with unit + integration coverage.
2. Provider remains transport/native-history focused; tool schema shaping and tool-call reconstruction now live in the tools extension.

### Open issues

1. None identified in subtask 050 scope.
