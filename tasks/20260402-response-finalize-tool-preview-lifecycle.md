# Response Finalize Lifecycle For Final Message Enrichment

Short description: Add a new core-owned `response_finalize` lifecycle that triggers normal plugin actions before final messages are emitted, allowing plugins to mutate both in-flight final core messages and persisted native history. Use it to move tool-call preview generation out of `ToolLoopRunner` and into a dedicated feature plugin.

## Task checklist

- [x] Add the new `response_finalize` lifecycle execution path inside `AgentCore` request finalization.
- [x] Extend the action context/result model for this lifecycle so actions can read and replace `final_messages` in addition to `native_messages`.
- [x] Add stable `AgentCore` helper APIs for tool-call preview generation and native `_metadata` patching.
- [x] Implement a feature plugin that annotates tool-call previews during `response_finalize` and restores them in `from_native_messages(...)`.
- [x] Remove the transient `ToolLoopRunner` preview mutation path and cover the new behavior with tests.

## Background

Current preview generation lives in `core/python/agent_app/tool_loop.py` in `_generate_tool_call_previews(...)`, and the result is injected only into the emitted `final` event payload. That data is not persisted into native history and does not survive rebuild-from-native.

The existing `request_complete` lifecycle in `AgentApplication` runs too late for this use case. It occurs after request execution has already produced and emitted the current turn's `final` payload, so it can mutate the stored session but cannot affect the just-produced final messages.

We want to preserve the plugin action model rather than introduce a separate one-off postprocessing hook. The new execution point should therefore be modeled as a lifecycle trigger exposed via `get_actions(...)`, but executed inside `AgentCore` request finalization rather than via the application-owned session lifecycle dispatcher.

## Agreed design

### New lifecycle

- Add a new lifecycle name: `response_finalize`.
- This lifecycle is owned by `AgentCore`, not `AgentApplication`.
- It runs:
  1. after provider/feature native `finalize(...)`
  2. after provider/extensions/features `from_native_messages(...)`
  3. after `native_indices` normalization on the turn's final core messages
  4. before the final session is built and before any `final` event / return value is emitted

### Why not reuse `request_complete`

- `request_complete` is application-owned and currently runs only when `AgentApplication` sees `request_completed`.
- That is too late to change the current turn's `final_messages` payload.
- `response_finalize` needs to happen while the request is still inside the core request path.

### Action model

- Plugins still opt in through ordinary `get_actions(...)` action definitions.
- Matching uses `trigger: "response_finalize"`.
- We should not overload `execute_lifecycle_actions(...)`, because that executor is session-rebuild-oriented and assumes actions only replace `native_messages` and session metadata.
- Instead, add a dedicated response-lifecycle action executor in core that still uses the normal action definitions and `execute_action(...)` method.

### Response-finalize action context

For `response_finalize`, `context` should include at least:

```python
{
    "core": self,
    "config": config,
    "trigger_source": "core",
    "session": session.to_dict(),
    "lifecycle": "response_finalize",
    "final_messages": final_messages,
    "native_final_messages": native_final_messages,
    "native_messages": native_messages,
    "stream": stream,
    "turn_native_start_index": baseline_native_len,
}
```

This lifecycle is core-internal, so unlike application lifecycle context it does not need to be restricted to JSON-serializable data.

### Response-finalize action results

For this lifecycle, actions may return:

```python
{
    "final_messages": [...],
    "native_messages": [...],
    "session_metadata": {...},
}
```

Behavior:

- If `final_messages` is omitted, keep the current value.
- If `native_messages` is omitted, keep the current value.
- `session_metadata` is optional and merged into the final session metadata.
- Other keys remain opaque/public result data as with the current action model.

## Required core helpers

Feature plugins should not reach into tool wrappers directly. `AgentCore` should expose stable helpers that internally use the interop-aware tool resolution added in task `tasks/20260225-codex-tools-parity/012-core-freeform-tool-prerequisite.md`.

Add at least:

```python
def format_tool_call_preview(self, tool_call: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    ...

def format_tool_call_previews(self, tool_calls: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    ...

def patch_native_internal_metadata(
    self,
    native_messages: List[Dict[str, Any]],
    indices: List[int],
    patch: Dict[str, Any],
) -> List[Dict[str, Any]]:
    ...
```

These helpers should internally:

- inspect tool calls through the effective interop registry
- resolve handlers using `can_handle_tool_call(...)` first, then legacy name/schema matching
- call the tool wrapper's `format_tool_call_preview(...)`
- patch native `_metadata` immutably for persistence through rebuild-from-native

## Implementation plan

### Phase 1: Core lifecycle plumbing

1. Update protocol/docs in `core/python/agent_core/types.py` to document the extra `response_finalize` lifecycle semantics and the fact that some lifecycle actions may return `final_messages`.
2. Add a dedicated `AgentCore` response-lifecycle executor that:
   - uses already-resolved provider/features/state for the current request
   - enumerates provider-extension and feature actions via `get_actions(...)`
   - filters `trigger == "response_finalize"`
   - calls `execute_action(...)` with the enriched context
   - threads updated `final_messages`, `native_messages`, and an accumulated `session_metadata` patch
3. Add a small internal helper in `AgentCore` to run this stage from:
   - `send_request(...)`
   - `send_request_stream(...)`
   - `send_request_stream_async(...)`

### Phase 2: Helper API extraction

1. Extract the tool preview generation logic from `ToolLoopRunner._generate_tool_call_previews(...)` into new `AgentCore` helper methods.
2. Reuse the interop-aware call inspection and tool resolution already present in `AgentCore` from task `012`.
3. Add native `_metadata` patching helper for response-finalize actions.

### Phase 3: Preview feature plugin

1. Add a dedicated feature plugin, likely under `core/python/plugins`, for tool-call preview annotation.
2. The plugin should:
   - define an action with `trigger: "response_finalize"`
   - read `final_messages` from context
   - compute previews via `context["core"].format_tool_call_previews(...)`
   - update assistant `final_messages[*].metadata.tool_call_previews`
   - persist the same preview payload into native `_metadata` for the assistant message's `native_indices`
3. The same plugin should implement `from_native_messages(...)` to restore `tool_call_previews` from native `_metadata` back into public core message metadata during rebuild-from-native.

### Phase 4: Remove application-loop mutation

1. Delete `_generate_tool_call_previews(...)` from `ToolLoopRunner`.
2. Remove the ad hoc event-payload mutation in the sync and streaming `final` paths.
3. Ensure the emitted `final` payload now already contains previews because core ran `response_finalize` first.

### Phase 5: Tests

Add tests for:

- sync `send_request(...)` applying `response_finalize` action mutations to the returned `final_messages`
- streaming `send_request_stream(...)` applying the same mutations before the `final` event is yielded
- persistence of preview data through native `_metadata` and rebuild-from-native
- `AgentCore.format_tool_call_previews(...)` working with custom/freeform tool calls as well as function calls
- no preview duplication when restored from native metadata
- existing behavior remaining unchanged when no plugin declares `trigger: "response_finalize"`

## Key code references

- Current transient preview path: `core/python/agent_app/tool_loop.py`
- Core request finalization paths: `core/python/agent_core/core.py`
- Action/lifecycle execution: `core/python/agent_core/core.py`, `core/python/agent_app/application_future.py`
- Feature plugin context and action contract: `core/python/agent_core/types.py`
- Durable native metadata guidance: `plugins/docs/provider-plugins.md`

## Completion Notes

Added a new core-owned `response_finalize` lifecycle executor in `AgentCore` and threaded it through `send_request(...)`, `send_request_stream(...)`, and `send_request_stream_async(...)`. This lifecycle reuses ordinary action definitions from `get_actions(...)`, but its result contract also accepts `final_messages`, allowing core-side plugins to mutate the in-flight final payload before it is emitted while still being able to replace `native_messages` and patch `session_metadata`.

Added new public `AgentCore` helpers:

- `extract_tool_calls_from_messages(...)`
- `format_tool_call_preview(...)`
- `format_tool_call_previews(...)`
- `patch_native_internal_metadata(...)`

These helpers use the interop-aware tool resolution introduced in task `tasks/20260225-codex-tools-parity/012-core-freeform-tool-prerequisite.md` rather than `ToolLoopRunner`-local schema assumptions.

Implemented a built-in feature plugin at `core/python/plugins/tool_call_preview_feature.py` that:

- registers an action with `trigger: "response_finalize"`
- annotates assistant `final_messages[*].metadata.tool_call_previews`
- persists the same preview payload into native `_metadata`
- restores previews during rebuilds in `from_native_messages(...)`

Removed the transient preview mutation path from `core/python/agent_app/tool_loop.py`. The application layer now forwards preview-enriched final messages produced by core instead of generating previews ad hoc.

Important compatibility note: preview generation is now provided by the `ToolCallPreviewFeature` plugin. Requests only include `metadata.tool_call_previews` when that feature is registered/enabled for the active core/config.

Updated docs in:

- `plugins/docs/actions.md`
- `plugins/docs/feature-plugins.md`
- `core/python/agent_core/types.py`

Validation performed:

- `ruff check core/python/agent_core/core.py core/python/agent_app/tool_loop.py core/python/agent_core/types.py core/python/plugins/tool_call_preview_feature.py core/python/tests/test_core_execute_tool_calls.py core/python/tests/test_response_finalize_lifecycle.py`
- `pytest core/python/tests/test_core_execute_tool_calls.py core/python/tests/test_response_finalize_lifecycle.py core/python/tests/test_feature_plugin_context_enrichment.py -q`
- `pytest core/python/tests/test_application_layer_integration.py core/python/tests/test_plugin_default_adapters.py core/python/tests/test_tool_interop.py -q`

Note: `ruff` was intentionally run only on Python sources, not Markdown docs.
