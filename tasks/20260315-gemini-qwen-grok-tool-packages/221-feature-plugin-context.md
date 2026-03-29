# 221 - Feature Plugin Context Enhancement & Gemini Compaction Feature Plugin

Short description: Implement layered context for feature/extension plugins and reimplement compaction as a FeaturePlugin that works at core level with optional application-level enhancements.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`
Depends On: `tasks/20260315-gemini-qwen-grok-tool-packages/220-gemini-compaction-plugin.md`

## Goal

Enable feature and extension plugins to call LLM requests by adding layered context that provides core capabilities at baseline, with optional application-level enhancements. Implement Gemini-style compaction as a FeaturePlugin to validate the approach and provide a reference implementation.

## Background

Currently, feature/extension plugins can only:
- Modify `native_messages` and return them
- Patch `session_metadata`
- Access provider state (may include client)

They cannot:
- Make LLM requests (except via provider-specific client in state)
- Load/save sessions
- Switch agents
- Publish events

This task adds a layered context approach where:
1. **Core** provides baseline capabilities (core, config)
2. **Application** adds enhanced capabilities (app, base_config, agent registry)
3. **Terminal/Server** can add implementation-specific features

## Scope

### In Scope

1. **Layer 1: Core-level context**
   - Add `core: AgentCore` to context
   - Add `config: Dict` (current resolved config) to context
   - Feature plugins can create temp sessions and call `core.stream_request()`

2. **Layer 2: Application-level context**
   - Add `app: AgentApplication` to context (when called from app)
   - Add `base_config: Dict` (full config with all agents) to context
   - Feature plugins can use `app.send_request()`, `app.update_agent()`, etc.
   - Graceful degradation: check `context.get("app")` before using

3. **Layer 3: Terminal/Server-level context** (tests only, no implementation)
   - Test that terminal/server can add context keys
   - Document how applications should add context
   - No actual compaction usage of this layer

4. **GeminiCompactionFeaturePlugin**
   - Reimplement compaction as FeaturePlugin
   - Use layered context to access LLM
   - Works with core-only (same agent) or app-level (different agent)
   - Coexists with existing GeminiCompactionAppPlugin

5. **Documentation**
   - Document ApplicationPlugin capabilities and context
   - Document FeaturePlugin capabilities and context (new)
   - Document ExtensionPlugin capabilities and context (new)
   - Add to `plugins/docs/` for plugin authors
   - Update `TYPES_AND_PROTOCOLS.md`
   - Update `docs/api/core-sdk.md`

### Out of Scope

1. Lifecycle-triggered auto-compaction (Task 222)
2. Tool plugin subagent support (future)
3. Session persistence from feature plugins (needs design - return values only)
4. Removing or replacing the ApplicationPlugin version

## Current State Analysis

### Application Plugin Capabilities (Existing)

| Capability | Method/Access |
|------------|---------------|
| Load sessions | `app.load_session(session_id)` |
| Save sessions | `app.save_session(session)` |
| LLM requests | `app.send_request(core, session, config, overrides)` |
| Session locking | `app.acquire_session_lock(session_id)` |
| Event publishing | `app.publish_event(event)` |
| Switch agents | `app.update_agent(agent_id, session)` |
| Full config access | `self._config` (all agents) |
| Request config resolution | `resolve_request_config(base_config, overrides)` |

### Feature/Extension Plugin Capabilities (Current)

| Capability | Available | Notes |
|------------|-----------|-------|
| Operate on native messages | ✅ | `native_messages` parameter |
| Return modified native_messages | ✅ | Required in return dict |
| Return session_metadata patch | ✅ | Merged into session.metadata |
| Provider-native APIs | ⚠️ | Only if client in state |
| LLM requests | ❌ | No core/app access |
| Load/Save sessions | ❌ | No store access |
| Session locking | ❌ | No lock access |
| Event publishing | ❌ | No event store access |
| Switch agents | ❌ | No config access |

### Current Context Structure

```python
# From _build_lifecycle_context in application_future.py
context = {
    "lifecycle": "session_save_prepare",
    "trigger_source": "application",
    "session": session.to_dict(),
    "config": effective_config,
    # ... any extra_context passed by caller
}
```

## Implementation Plan

### Phase 1: Core Context Enhancement

**Files to modify**:
- `core/python/agent_core/core.py` - Add context in `execute_session_action`, `execute_lifecycle_actions`
- `core/python/agent_core/types.py` - Update protocol docstrings

**Context structure**:
```python
# Layer 1: Core provides
context = {
    **(context or {}),
    "core": self,              # AgentCore instance
    "config": config,          # Current resolved config
    "lifecycle": trigger,      # Lifecycle trigger (if any)
    "trigger_source": "core",  # Where action was triggered
    "session": session.to_dict(),
}
```

**Implementation location**: In `execute_session_action` and `execute_lifecycle_actions` before calling plugin's `execute_action`.

### Phase 2: Application Context Enhancement

**Files to modify**:
- `core/python/agent_app/application_future.py` - Enrich context in `run_session_lifecycle`, `execute_session_action`

**Context structure**:
```python
# Layer 2: Application adds (wraps core context)
context = {
    **core_context,
    "app": self,                    # AgentApplication instance
    "base_config": self._config,    # Full base config (all agents)
    "trigger_source": "application",
}
```

**Key insight**: For lifecycle actions called from within `AgentApplication.run_session_lifecycle`, the application can enrich the context before passing to core. For manually triggered session actions, the application can also add context.

### Phase 3: Feature Plugin Implementation

**Files to create**:
- `plugins/gemini-compaction-app/src/gemini_compaction_app/feature_plugin.py` - GeminiCompactionFeaturePlugin

**Plugin structure**:
```python
class GeminiCompactionFeaturePlugin(FeaturePlugin):
    name = "gemini_compaction_feature"
    version = "1.0.0"
    
    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "id": "compact_range",
                "label": "Compact range",
                "description": "Compact a message range into a state snapshot.",
                "inputs": {
                    "start": {"type": "integer", "required": False},
                    "end": {"type": "integer", "required": False},
                    "instructions": {"type": "string", "required": False},
                    "agent_id": {"type": "string", "required": False},  # Optional: different agent
                },
            },
        ]
    
    def execute_action(self, action_id, session, native_messages, params, context, state):
        # Check available capabilities
        app = context.get("app")
        core = context["core"]
        config = context["config"]
        
        # Build compaction messages from native_messages
        compaction_messages = self._build_compaction_messages(native_messages, params)
        
        if app:
            # Full capability: can use different agent
            agent_id = params.get("agent_id")
            if agent_id:
                # Use app to switch agent and get config
                agent_config = context["base_config"].get("agents", {}).get(agent_id)
                if agent_config:
                    compaction_core, compaction_config, _ = app.update_agent(agent_id, session)
                else:
                    # Fall back to same agent
                    compaction_core = core
                    compaction_config = self._modify_config(config, params)
            else:
                compaction_core = core
                compaction_config = self._modify_config(config, params)
            
            # Use app's request method
            temp_session = self._create_temp_session(compaction_messages, session)
            events = app.send_request(compaction_core, temp_session, compaction_config, {})
        else:
            # Core-only: same agent with config overrides
            compaction_config = self._modify_config(config, params)
            temp_session = self._create_temp_session(compaction_messages, session)
            events = core.stream_request(temp_session, compaction_config)
        
        # Extract summary from events
        summary = self._extract_summary(events)
        
        # Apply compaction to native_messages
        new_native = self._apply_compaction(native_messages, summary, params)
        
        return {
            "native_messages": new_native,
            "session_metadata": {
                "last_compaction": datetime.now().isoformat(),
            },
        }
```

### Phase 4: Layer 3 Tests (Terminal/Server)

**Test approach**:
```python
# In application/python/tests

def test_terminal_adds_context_to_lifecycle_actions():
    """Terminal can add context keys that feature plugins can access."""
    # Setup: Create a feature plugin that records context
    # Trigger a lifecycle action from terminal
    # Assert the plugin received terminal-specific context

def test_server_adds_context_to_session_actions():
    """HTTP server can add context keys that feature plugins can access."""
    # Setup: Create a feature plugin that records context
    # Execute a session action via server
    # Assert the plugin received server-specific context
```

**Note**: These tests verify the mechanism works, but compaction plugin doesn't use Layer 3 context.

### Phase 5: Documentation

**Files to create/update**:

1. `plugins/docs/application-plugins.md` (new) - Document ApplicationPlugin:
   - Capabilities table
   - Context received in `execute_action`
   - Configuration schema
   - Example implementations
   - When to use vs FeaturePlugin

2. `plugins/docs/feature-plugins.md` (new) - Document FeaturePlugin:
   - Capabilities table (before/after this task)
   - Context structure and layers
   - How to check for capabilities
   - Example: GeminiCompactionFeaturePlugin
   - Return value contract

3. `plugins/docs/provider-extensions.md` (update) - Add context documentation:
   - Context received in `execute_action`
   - Layered context approach
   - Provider-specific state access

4. `plugins/docs/actions.md` (update) - Add context section:
   - How context flows through action execution
   - Layered context for feature/extension actions
   - How applications can add context

5. `TYPES_AND_PROTOCOLS.md` (update) - Add context specification

6. `docs/api/core-sdk.md` (update) - Add session actions section

## Context Flow Diagram

```
TerminalApplication.execute_action()
    ↓ adds: {"terminal": self, ...}
AgentApplication.run_session_lifecycle()
    ↓ adds: {"app": self, "base_config": ...}
AgentCore.execute_lifecycle_actions()
    ↓ adds: {"core": self, "config": config}
FeaturePlugin.execute_action(session, native_messages, params, context, state)
    ↓ Plugin checks: app = context.get("app")
                    core = context["core"]
```

## Requirements Checklist

- [ ] Implement Layer 1: Core context (core, config) in `execute_session_action`
- [ ] Implement Layer 1: Core context (core, config) in `execute_lifecycle_actions`
- [ ] Implement Layer 2: Application context (app, base_config) in `run_session_lifecycle`
- [ ] Implement Layer 2: Application context in manual session action execution
- [ ] Update protocol docstrings in `types.py`
- [ ] Implement GeminiCompactionFeaturePlugin
- [ ] Add unit tests for core-level context
- [ ] Add unit tests for app-level context
- [ ] Add integration tests with GeminiCompactionFeaturePlugin
- [ ] Add Layer 3 tests (terminal/server context)
- [ ] Create `plugins/docs/application-plugins.md`
- [ ] Create `plugins/docs/feature-plugins.md`
- [ ] Update `plugins/docs/provider-extensions.md`
- [ ] Update `plugins/docs/actions.md`
- [ ] Update `TYPES_AND_PROTOCOLS.md`
- [ ] Update `docs/api/core-sdk.md`

## Key Files

| File | Purpose |
|------|---------|
| `core/python/agent_core/core.py` | Core context implementation |
| `core/python/agent_core/types.py` | Protocol docstring updates |
| `core/python/agent_app/application_future.py` | Application context enhancement |
| `plugins/gemini-compaction-app/src/.../feature_plugin.py` | Feature plugin implementation |
| `plugins/docs/application-plugins.md` | Application plugin docs (new) |
| `plugins/docs/feature-plugins.md` | Feature plugin docs (new) |
| `plugins/docs/provider-extensions.md` | Extension plugin docs (update) |
| `plugins/docs/actions.md` | Actions docs (update) |

## Open Questions

1. Should feature plugins be able to save sessions directly, or always go through return values?
   - **Current answer**: Return values only. Feature plugins return `session_metadata` patch.
   - This maintains the pattern where core handles session mutation.

2. How to handle the case where core-level feature needs session persistence?
   - **Current answer**: Not in scope. Use ApplicationPlugin for full session control.

## Notes

- The GeminiCompactionAppPlugin (Task 220) remains as the primary implementation
- GeminiCompactionFeaturePlugin demonstrates the new capability
- Both can coexist; users can choose based on their needs
- ApplicationPlugin is simpler for full-featured operations
- FeaturePlugin is useful when operating at the native-message level or when provider-specific optimizations are needed