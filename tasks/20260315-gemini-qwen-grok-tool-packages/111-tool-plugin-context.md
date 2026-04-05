# 111 - Tool Plugin Context Enhancement

Short description: Extend the `ToolPlugin` protocol to accept layered context (`core`, `app`, `config`) in `execute_tool` and `stream_tool`, matching the pattern from Task 221 for feature/extension actions. This enables tools to make LLM calls through high-level APIs.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On: `tasks/20260315-gemini-qwen-grok-tool-packages/221-feature-plugin-context.md`

## Goal

Enable tool plugins to call LLM requests by adding layered context that provides core capabilities at baseline, with optional application-level enhancements. This matches the approach implemented in Task 221 for feature/extension plugins.

## Background

Currently, tool plugins can only:
- Access their own `state` from `init()`
- Execute tool logic and return results

They cannot:
- Make LLM requests (no access to `core` or `app`)
- Access the current session context
- Use provider capabilities

Feature and extension plugins (after Task 221) can access:
- `context["core"]` - AgentCore instance for LLM calls
- `context["app"]` - AgentApplication instance (when called from app)
- `context["config"]` - Current resolved config
- `context["base_config"]` - Full base config (when called from app)

This task extends the same capability to tool plugins.

## Current State Analysis

### Tool Plugin Protocol (Current)

```python
class ToolPlugin(BasePlugin, Protocol):
    def execute_tool(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        *,
        payload_kind: Optional[str] = None,
        payload_format: Optional[str] = None,
        payload_metadata: Optional[Dict[str, Any]] = None,
        tool_call: Optional[Dict[str, Any]] = None,
        cancellation: Any | None = None,
    ) -> Dict[str, Any]:
        # No context parameter
```

### Feature/Extension Action Context (After Task 221)

```python
# Layer 1: Core provides
context = {
    "core": self,              # AgentCore instance
    "config": config,          # Current resolved config
    "trigger_source": "core",
    "session": session.to_dict(),
}

# Layer 2: Application adds
context = {
    **core_context,
    "app": self,               # AgentApplication instance
    "base_config": self._config,
    "trigger_source": "application",
}
```

## Requirements Checklist

- [x] Update `ToolPlugin.execute_tool` signature to accept `context` parameter
- [x] Update `ToolPlugin.stream_tool` signature to accept `context` parameter
- [x] Update `iter_tool_messages` in `core.py` to build and pass context
- [x] Update `execute_tool_calls` in `core.py` to accept and pass context
- [x] Update `stream_tool_call` in `core.py` to accept and pass context
- [x] Update `ToolDefaultsAdapter` to pass through context
- [x] Update `ToolWrapper` to accept and pass context
- [x] Update `ToolLoopRunner` to accept and pass context
- [x] Update application layer to enrich context for tools
- [x] Add core-level context tests
- [x] Add application-level context tests
- [x] Update `TYPES_AND_PROTOCOLS.md` with tool context documentation
- [x] Update `plugins/docs/tool-plugins.md` with tool context usage

## Key Files

| File | Purpose |
|------|---------|
| `core/python/agent_core/types.py` | Protocol definition |
| `core/python/agent_core/core.py` | Context building and passing |
| `core/python/agent_core/plugin/adapters.py` | Adapter pass-through |
| `core/python/agent_core/plugin/tool.py` | ToolWrapper updates |
| `core/python/agent_app/tool_loop.py` | ToolLoopRunner context support |
| `core/python/agent_app/application_future.py` | Application-level enrichment |
| `core/python/tests/fixtures/context_recording_tool.py` | Test fixture |
| `core/python/tests/test_tool_plugin_context.py` | Core-level tests |
| `application/python/tests/test_tool_plugin_context.py` | App-level tests |

## Notes

- The `context` parameter is optional to maintain backward compatibility
- Tools should gracefully handle missing context (check `context.get("core")`)
- This pattern matches the approach from Task 221 for feature/extension plugins
- Enables future tools like web fetch, web search, and subagent delegation to make LLM calls

---

## Execution Plan

### Phase 1: Protocol Changes (types.py)

1. Add `context: Optional[Dict[str, Any]] = None` parameter to `ToolPlugin.execute_tool`
2. Add `context: Optional[Dict[str, Any]] = None` parameter to `ToolPlugin.stream_tool`
3. Update docstrings to document Layer 1 and Layer 2 context structure

### Phase 2: Core Implementation (core.py)

1. Update `iter_tool_messages`:
   - Add optional `context` parameter
   - Build Layer 1 context with `setdefault` for enrichment
   - Pass context to `tool.stream_tool()`

2. Update `execute_tool_calls`:
   - Add optional `context` parameter
   - Pass through to `iter_tool_messages`

3. Update `stream_tool_call`:
   - Add optional `context` parameter
   - Build Layer 1 context
   - Pass context to `tool.stream_tool()`

### Phase 3: Adapter Updates (adapters.py)

1. Update `ToolDefaultsAdapter.execute_tool`:
   - Add `context` parameter
   - Use `_call_with_optional_kwargs` for backward compatibility

2. Update `ToolDefaultsAdapter.stream_tool`:
   - Add `context` parameter
   - Use `_call_with_optional_kwargs` for backward compatibility

### Phase 4: ToolWrapper Updates (tool.py)

1. Update `ToolWrapper.execute_tool`, `execute_tool_async`, and `stream_tool`:
   - Add `context` parameter
   - Pass to adapter methods

### Phase 5: ToolLoopRunner Updates (tool_loop.py)

1. Add `context` parameter to `ToolLoopRunner.__init__`
2. Pass context to `core.iter_tool_messages` in `_apply_tool_calls`

### Phase 6: Application Layer (application_future.py)

1. Pass Layer 2 context when creating `ToolLoopRunner`:
   - `app`, `application`, `base_config`, `session_asset_store`, `trigger_source`

### Phase 7: Tests

1. Create `context_recording_tool.py` fixture
2. Create `core/python/tests/test_tool_plugin_context.py`
3. Create `application/python/tests/test_tool_plugin_context.py`

---

## Completion Notes

**Implementation completed successfully.**

### Files Modified

| File | Changes |
|------|---------|
| `core/python/agent_core/types.py` | Added `context` parameter to `ToolPlugin.execute_tool` and `ToolPlugin.stream_tool` with documentation |
| `core/python/agent_core/plugin/adapters.py` | Added `context` parameter to `ToolDefaultsAdapter.execute_tool` and `stream_tool` with backward-compatible `_call_with_optional_kwargs` |
| `core/python/agent_core/plugin/tool.py` | Added `context` parameter to `ToolWrapper.execute_tool`, `execute_tool_async`, and `stream_tool` |
| `core/python/agent_core/core.py` | Added `context` parameter to `iter_tool_messages`, `execute_tool_calls`, and `stream_tool_call` with Layer 1 enrichment |
| `core/python/agent_app/tool_loop.py` | Added `context` parameter to `ToolLoopRunner.__init__` and passes to `iter_tool_messages` |
| `core/python/agent_app/application_future.py` | Passes Layer 2 context to `ToolLoopRunner` |

### Files Created

| File | Purpose |
|------|---------|
| `core/python/tests/fixtures/context_recording_tool.py` | Test fixture tool that records received context |
| `core/python/tests/test_tool_plugin_context.py` | 8 core-level tests for tool context enrichment |
| `application/python/tests/test_tool_plugin_context.py` | 5 application-level tests for tool context flow |

### Context Structure Implemented

**Layer 1 (Core - always available):**
- `core`: AgentCore instance for session/message operations
- `config`: Current resolved request configuration  
- `trigger_source`: "core"

**Layer 2 (Application - when called from AgentApplication):**
- `app` / `application`: AgentApplication instance
- `base_config`: Full base configuration (all agents)
- `session_asset_store`: Session asset store for file attachments
- `trigger_source`: "application"

### Test Results

- **Core tests**: 8 tests passing (context enrichment, backward compatibility)
- **Application tests**: 5 tests passing (ToolLoopRunner context flow)
- **Existing tests**: All tool-related tests continue to pass

### Remaining Work

All requirements completed. Documentation updated:
- `TYPES_AND_PROTOCOLS.md` - Added context parameter to ToolPlugin execute_tool and stream_tool signatures
- `plugins/docs/tool-plugins.md` - Added new "Tool execution context" section with usage examples
