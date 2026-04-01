# 222 - Documentation for Phase 2: Plugin Documentation

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`
Depends On: `tasks/20260315-gemini-qwen-grok-tool-packages/221-feature-plugin-context.md`

This subtask completes the documentation for Phase 2 of Task 221. The tasks created include this subtask.

## Goal

Create comprehensive documentation for:
1. **ApplicationPlugin capabilities and context** - Document what ApplicationPlugin can do do2. **FeaturePlugin capabilities and context** - Document the FeaturePlugin can do access with layered context
3. **ProviderExtensionPlugin capabilities and context** - Document what ProviderExtensionPlugin can access with layered context
4. **Session Actions API** - Document `execute_session_action` and `execute_lifecycle_actions` methods signatures,5. **Update existing documentation** - Match structure and style,6. **Create new documentation files** as described below

## Files to Create

| File | Purpose |
|------|------|
| `plugins/docs/application-plugins.md` | Document ApplicationPlugin capabilities |
| `plugins/docs/feature-plugins.md` | Document FeaturePlugin capabilities |
| `plugins/docs/provider-extensions.md` |Update with context documentation |
| `plugins/docs/actions.md` |Update with layered context section |
| `TYPES_AND_PROTOCOLS.md` | Add session actions and context section |
| `docs/api/core-sdk.md` |Add session actions section |

## Requirements Checklist

- [ ] Investigate ApplicationPlugin implementation and capabilities
- [ ] Investigate FeaturePlugin implementation and capabilities
- [ ] Investigate ProviderExtensionPlugin implementation and capabilities
- [ ] Document ApplicationPlugin context structure (all layers)
- [ ] Document FeaturePlugin context structure (all layers)
- [ ] Document ProviderExtensionPlugin context structure (all layers)
- [ ] Document `execute_session_action` method signature
- [ ] Document `execute_lifecycle_actions` method signature
- [ ] Create `plugins/docs/application-plugins.md`
- [ ] Create `plugins/docs/feature-plugins.md`
- [ ] Update `plugins/docs/provider-extensions.md` with context documentation
- [ ] Update `plugins/docs/actions.md` with layered context section
- [ ] Update `TYPES_AND_PROTOCOLS.md` with session actions and context documentation
- [ ] Update `docs/api/core-sdk.md` with session actions documentation

## Existing Documentation to Review

Before writing, review the existing documentation structure:
 match style, and tone with the existing docs files:
- `plugins/docs/provider-plugins.md` - Reference for provider implementation
- `plugins/docs/provider-extensions.md` - Documents extensions
- `plugins/docs/actions.md` - Documents actions
- `plugins/docs/ui-elements.md` - Documents UI elements

## Features to Document

### ApplicationPlugin

**Capabilities to** file:
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

**Context in `execute_action` (Layer 2: Application-level)
- `app: AgentApplication` instance
- `application`: AgentApplication (alias)
- `base_config: Full base config with- `session_asset_store`: Session asset store
- `event_store`: Event store
- `session_id`: Current session ID
- `agent_id`: Current agent ID
- `overrides`: Current session overrides

### FeaturePlugin

**Capabilities (NEW in this task)**file:
| Capability | Method/Access |
|------------|---------------|
| LLM requests | `core.stream_request()` or `core.send_request()` (core-only) |
| Temp sessions | `core.slice_session()` for compaction |
|Modify native_messages | Via `to_native_messages`/`from_native_messages` |
| Session metadata | Return `session_metadata` patch |

**Context in `execute_action` (Layer 1: Core-level - always present
- `core: AgentCore` instance
- `config: Current resolved config
- `trigger_source`: "core" or "application" (where triggered)
- `session`: Serialized session dict
- `lifecycle`: Lifecycle trigger name (for lifecycle actions)

**Layer 2: Application-level - when called from AgentApplication
- `app` / `application`: AgentApplication instance
- `base_config`: Full base config
- `session_asset_store`: SessionAssetStore

**Layer 3: Terminal/Server-level - optional,- Terminal: TerminalApplication instance
- Server: FastAPI server
- Custom keys passed via `context` parameter

### ProviderExtensionPlugin

**Capabilities
Same as FeaturePlugin
**Context in `execute_action`
Same as FeaturePlugin (Layer 1 always present)

## Implementation Notes

1. Read existing documentation to understand structure and style
2. For each plugin type, read the implementations in:
   - `core/python/agent_app/app_plugins.py` - ApplicationPlugin wrapper
   - `core/python/agent_core/types.py` - Protocols
   - `plugins/gemini-compaction-app/src/gemini_compaction_app/__init__.py` - Reference implementation
   - `plugins/gemini-compaction-feature/src/gemini_compaction_feature/__init__.py` - FeaturePlugin reference

3. Focus on behavior differences between ApplicationPlugin and FeaturePlugin
   - ApplicationPlugin: Richer capabilities, full session persistence,   - FeaturePlugin: Lightweight, stateless, operates at native-message level

4. Follow AGENTS.md guidelines for documentation structure,