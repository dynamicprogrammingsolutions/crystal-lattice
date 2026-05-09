# Tool Result Interop And Display Contract

Add first-class tool-result inspection and conversion to `core/python/agent_core/tool_interop.py`, and formalize the core/public contract for rich tool results. Today complex tool results are split across `content`, `tool_output_content`, `multipartContent`, and provider-specific helper branches. The target direction is a single structured `toolResult` field, a rich `metadata.display` contract for UI rendering, and compact provider-native history that can carry `asset_ref` until request-time expansion.

## Requirements checklist

- [x] Introduce a first-class top-level `toolResult` field for core/public `tool` messages.
- [x] Keep `content` as a string fallback populated from `toolResult.text` so staged frontends and simple clients remain compatible.
- [x] Define `metadata.display` as the primary user-facing rendering contract for rich tool results, including non-text variants such as image and diff/file-style views.
- [x] Avoid `multipartContent` as the long-term rich rendering path for tool messages; reserve it for generic attachment-bearing non-tool messages unless there is a clear compatibility need.
- [x] Add result-accessor support to `ToolInteropContribution`, `ToolInteropRegistry`, and surrounding types in `core/python/agent_core/tool_interop.py`.
- [x] Add result-adapter support to convert `toolResult` payloads between provider-native formats, especially OpenAI chat-completions and OpenAI Responses.
- [x] Provide default result accessors for string fallback, OpenAI chat-completions result envelopes, OpenAI Responses result envelopes, and the existing `provider_native_tool_result` envelope shape.
- [x] Support compact provider-native tool-result envelopes that may contain attachment references such as `asset_ref`, `filename`, and `mime_type`.
- [x] Treat `native_messages` as provider-native durable history, not necessarily raw API-wire payloads.
- [x] Make `to_native_messages()` produce durable provider-native history and keep compact attachment refs where the provider can understand them.
- [x] Make `initialize_request()` perform final request-time expansion of tool-result attachment refs into API-compatible payloads.
- [x] Ensure `from_native_messages()` preserves or reconstructs `toolResult`, `content` fallback, and display-capable attachment references without expanding them into full inline data.
- [x] Prevent duplication of structured tool-result data into native `_metadata` when that result is already represented directly in native message content/output.
- [x] Remove legacy parallel paths such as `tool_output_content` as the primary structured result channel once migration is complete.
- [x] Remove temporary compatibility bridges and helper-only result inspection once first-class result interop is in place.

## Execution plan

Added during completion on 2026-05-09.

1. Verify the task requirements against the current working changes and identify any remaining compatibility bridges or incomplete migrations.
2. Remove the leftover helper-only bridge code so `toolResult` interop is driven by the first-class result accessor/adapter path.
3. Re-run the focused core, provider, and application tests that cover tool-result inspection, durable native history, request-time attachment expansion, and display rendering.
4. Update this task file to reflect completion and record the final verification notes.

## Current state and context

Existing schema and call interop already lives in `core/python/agent_core/tool_interop.py`:

- `ToolSchemaAccessor` and `ToolCallAccessor` inspect provider wire formats.
- `ToolSchemaAdapter` and `ToolCallAdapter` convert between provider wire formats.
- `ToolInteropContribution` currently has schema/call accessors and adapters, but no result equivalents.

Current rich tool-result behavior is fragmented:

- `core/python/agent_core/tool_result_payloads.py` defines `provider_native_tool_result` envelopes and helper functions such as `openai_chat_tool_result_content()` and `openai_responses_tool_result_output()`.
- Complex tools may emit raw structured facts from `execute_tool()`, but `format_tool_result()` and `to_display_format()` are not yet the sole canonical sources for provider-facing vs user-facing representations.
- `tool_output_content` exists as an untyped structured side channel and is currently closest to OpenAI Responses output items, but it is not a typed envelope and is awkward to convert generically.
- Tool message `multipartContent` has been used as a UI image path, but this does not scale well to richer result displays like diffs, file modifications, or other non-attachment renderers.
- Public message `content` is still the most broadly supported frontend field and should stay string-compatible during staged migration.

The desired direction is:

- `execute_tool()` returns internal/raw facts.
- `format_tool_result()` returns the canonical structured tool-result envelope, compact and provider-native/provider-convertible.
- `to_display_format()` returns the primary user-facing render description.
- Core stores:
  - string `content` fallback
  - top-level `toolResult`
  - `metadata.display`
- Providers convert `toolResult` into durable native history in `to_native_messages()`.
- Providers expand `asset_ref` into final API-compatible payloads in `initialize_request()`.

## Suggested implementation approach

1. Add `toolResult` support to core/public message types and serialization.
2. Add `ToolResultAccessor`, `ToolResultAdapter`, and `InspectedToolResult` in `tool_interop.py`.
3. Extend `ToolInteropContribution` and `compose_tool_interop_registry()` with result accessors/adapters.
4. Add `ToolInteropRegistry.inspect_result()` and `ToolInteropRegistry.convert_tool_result()`, mirroring schemas and calls.
5. Move or wrap the current helper behavior from `core/python/agent_core/tool_result_payloads.py` into the new result interop implementation.
6. Update `AgentCore.iter_tool_messages()` to:
   - store string fallback in `content`
   - store structured result in `toolResult`
   - store rich UI payload in `metadata.display`
7. Update providers to consume `toolResult` rather than legacy side channels when converting tool messages.
8. Update provider `initialize_request()` paths to expand compact attachment refs from tool results into API-ready payloads.
9. Update frontend SDK and renderers to treat `metadata.display` as the preferred rendering contract for rich tool results, while keeping `content` as a fallback.
10. Remove compatibility bridges such as `tool_output_content` and any temporary transient handoff fields once migration is complete.

## Tests to update or add

- Add unit tests for result accessors/adapters in `core/python/tests`, likely alongside existing tool interop tests.
- Add tests for the new `toolResult` message field serialization and roundtrip behavior.
- Update provider multipart/result conversion tests in:
  - `plugins/openrouter/tests/test_openrouter_provider_multipart_conversion_unit.py`
  - `plugins/reference-openai-compatible-provider/tests/test_provider_multipart_conversion_unit.py`
  - `plugins/openrouter_responses/tests/test_openrouter_provider_multipart_conversion_unit.py`
  - `plugins/openai_responses/tests/test_openai_responses_provider_unit.py`
- Add tests that asset-ref-bearing tool results stay compact in stored core messages and native history, while `initialize_request()` expands them to API-compatible payloads.
- Add or preserve integration tests where:
  - a rich image tool result roundtrips through core/native/core without losing `asset_ref`
  - a chat-style provider consumes a Responses-style structured tool result through result interop
  - frontend clients can render rich tool results from `metadata.display` while older clients still show string `content`

## Completion Notes

Added during completion on 2026-05-09.

- Verified the implementation now writes first-class `toolResult` payloads, derives string `content` fallbacks from inspected result text, and prefers `metadata.display` for rich rendering.
- Confirmed provider conversions now consume `toolResult` directly, preserve compact provider-native payloads in durable history, and expand attachment references at request time where needed.
- Removed the unused `NormalizedToolResultPayload` / `normalize_tool_result_payload()` compatibility bridge from `core/python/agent_core/tool_result_payloads.py`; no remaining runtime references to that helper remain.
- Re-ran focused regression suites covering core interop, structured tool output, OpenAI Responses, OpenRouter chat/responses providers, reference OpenAI-compatible provider, asset-ref request expansion, and terminal tool rendering.