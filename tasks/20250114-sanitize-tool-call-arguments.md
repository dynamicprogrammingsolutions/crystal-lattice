``# Sanitize Tool Call Arguments Before Storing in History

## Description

When LLMs return corrupted JSON in tool call `arguments` fields, the corrupted data gets stored in history. On subsequent requests, the API rejects the invalid JSON. We need to sanitize tool call arguments before storing them in history.

## Problem

Example corrupted tool call:
```json
{
  "id": "call_ZCs41WnqeASDMlbOMFPkZQW7",
  "type": "function",
  "function": {
    "name": "glob",
    "arguments": "{corrupted json"
  }
}
```

When sent back to the API, it fails with invalid JSON error.

## Solution

Add `sanitize_call` method to `ToolCallAccessor` protocol that returns a sanitized copy of the tool call. Implement in each accessor based on format (JSON formats sanitize, text formats pass through). Call from provider extensions before storing in history.

## Requirements Checklist

- [x] Add `sanitize_call` to `ToolCallAccessor` Protocol in `tool_interop.py`
- [x] Implement `sanitize_call` in `OpenAIChatToolCallAccessor`
- [x] Implement `sanitize_call` in `OpenAIResponsesFunctionCallAccessor`
- [x] Implement `sanitize_call` in `OpenAIResponsesCustomToolCallAccessor` (no-op)
- [x] Add `sanitize_tool_call` method to `ToolInteropRegistry`
- [x] Remove `get_arguments` from Protocol, consolidate into `get_payload`
- [x] Update `_get_call_payload` to only use `get_payload`
- [x] Update `OpenAIToolsExtension.finalize` to sanitize tool calls
- [x] Update `OpenAIResponsesToolsExtension` to sanitize tool calls
- [x] Update `OpenRouterToolsExtension` to sanitize tool calls
- [x] Add unit tests for `sanitize_call` in each accessor
- [x] Add unit tests for `sanitize_tool_call` in registry
- [x] Update existing tests for `get_payload` changes
- [x] Update documentation in `plugins/docs/`

## Implementation Plan

### 1. `core/python/agent_core/tool_interop.py`

#### 1.1 Add `sanitize_call` to `ToolCallAccessor` Protocol
- Location: After `get_payload_metadata` method (around line 139)
- Add new method returning sanitized copy of call

#### 1.2 Update `OpenAIChatToolCallAccessor`
- Remove `get_arguments` method
- Update `get_payload` to handle all cases, return `{}` on parse failure
- Add `sanitize_call` that fixes corrupted JSON arguments

#### 1.3 Update `OpenAIResponsesFunctionCallAccessor`
- Same pattern: remove `get_arguments`, update `get_payload`, add `sanitize_call`

#### 1.4 Update `OpenAIResponsesCustomToolCallAccessor`
- Remove `get_arguments`
- Keep `get_payload` as-is (returns text)
- Add no-op `sanitize_call`

#### 1.5 Update `ToolInteropRegistry`
- Add `sanitize_tool_call(call)` method
- Simplify `_get_call_payload` to only use `get_payload`

### 2. Provider Extensions

#### 2.1 `core/python/plugins/openai_tools_extension.py`
- Update `finalize` to sanitize `tool_calls` in `state["partial"]`

#### 2.2 `plugins/openai_responses/src/openai_responses_plugins/openai_responses_tools_extension.py`
- Add sanitization when converting tool calls

#### 2.3 `plugins/openrouter/src/openrouter_plugins/openrouter_tools_extension.py`
- Check and update if needed

### 3. Tests

#### 3.1 New test file: `core/python/tests/test_tool_interop_sanitize.py`
- Test each accessor's `sanitize_call`
- Test registry's `sanitize_tool_call`

#### 3.2 Update existing tests
- Remove tests for `get_arguments`
- Update tests for `get_payload` to verify `{}` on parse failure

### 4. Documentation

#### 4.1 Update `plugins/docs/provider-plugins.md`
- Document the `sanitize_call` method
- Explain when/how to use it in provider extensions

#### 4.2 Update `plugins/docs/provider-extensions.md`
- Add section on tool call sanitization
- Example implementation for custom extensions

## Completion Notes

### Changes Made

1. **`core/python/agent_core/tool_interop.py`**:
   - Added `sanitize_call` method to `ToolCallAccessor` Protocol
   - Removed `get_arguments` from Protocol (consolidated into `get_payload`)
   - Updated `OpenAIChatToolCallAccessor`:
     - Removed `get_arguments`
     - Updated `get_payload` to parse JSON and return `{}` on failure
     - Added `sanitize_call` that replaces invalid JSON with `"{}"`
   - Updated `OpenAIResponsesFunctionCallAccessor`:
     - Same pattern as above
   - Updated `OpenAIResponsesCustomToolCallAccessor`:
     - Removed `get_arguments`
     - Added no-op `sanitize_call` (text payload, no JSON sanitization)
   - Added `sanitize_tool_call` method to `ToolInteropRegistry`
   - Simplified `_get_call_payload` to only use `get_payload`
   - Updated `OpenAIResponsesToolCallToOpenAIChatToolCall.convert` to use `get_payload` and serialize

2. **`core/python/plugins/openai_tools_extension.py`**:
   - Imported `DEFAULT_TOOL_INTEROP_REGISTRY`
   - Updated `finalize` to sanitize `tool_calls` in `state["partial"]`

3. **`plugins/openai_responses/src/openai_responses_plugins/openai_responses_tools_extension.py`**:
   - Added `_sanitize_native_tool_call` method
   - Updated `_native_tool_call_to_core_tool_call` to sanitize before conversion

4. **`plugins/openrouter/src/openrouter_plugins/openrouter_tools_extension.py`**:
   - Imported `DEFAULT_TOOL_INTEROP_REGISTRY`
   - Updated `finalize` to sanitize `tool_calls` in `state["partial"]`

5. **`core/python/tests/test_tool_interop_sanitize.py`** (new file):
   - Tests for `sanitize_call` in each accessor
   - Tests for `sanitize_tool_call` in registry
   - Tests for `get_payload` behavior

6. **`core/python/tests/test_tool_interop.py`**:
   - Updated test to use `get_payload` instead of `get_arguments`
   - Updated adapter test to compare JSON semantically

7. **`plugins/docs/provider-extensions.md`**:
   - Added "Tool call sanitization" section under "Runtime interop contracts"
   - Documented `sanitize_call` method and when to use it
   - Added example implementation in `finalize`

### Key Design Decisions

1. **Removed `get_arguments` from Protocol**: Consolidated to `get_payload` which handles both raw and parsed cases. This simplifies the API and ensures all accessors implement proper parsing.

2. **Sanitization in `finalize`**: Provider extensions sanitize tool calls in their `finalize` method before they are stored in history. This ensures corrupted JSON doesn't persist in native history.

3. **Format-specific sanitization**: Each accessor implements `sanitize_call` based on its format:
   - JSON formats (OpenAI chat, Responses function_call): Replace invalid JSON with `"{}"`
   - Text formats (Responses custom_tool_call): No sanitization needed

4. **Registry convenience method**: `ToolInteropRegistry.sanitize_tool_call()` delegates to the appropriate accessor, returning the call unchanged if the format is not recognized.