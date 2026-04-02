# Feature plugins

Feature plugins (`FeaturePlugin`) operate at the core layer and can participate in message transformation, lifecycle hooks, and session-scoped actions. They receive layered context that provides core capabilities at baseline, with optional application-level enhancements when called from `AgentApplication`.

This page documents FeaturePlugin capabilities, context structure, and when to use them versus other plugin types.

Runtime references (source of truth):

- Protocol: `core/python/agent_core/types.py` (`FeaturePlugin` class)
- Core context enrichment: `core/python/agent_core/core.py` (`execute_session_action`, `execute_lifecycle_actions`)
- Application context enrichment: `core/python/agent_app/application_future.py` (`_build_lifecycle_context`)

Reference implementations:

- `plugins/gemini-compaction-feature/src/gemini_compaction_feature/__init__.py`

---

## What feature plugins are for

Feature plugins are ideal for features that need:

- **Message transformation**: Modify `native_messages` during request processing
- **Session-scoped actions**: Execute actions on a single session's native history
- **Lifecycle participation**: React to session creation, save, request events
- **Provider-agnostic behavior**: Work with any provider's native message format
- **Core-level operation**: Access to `AgentCore` for session/message operations

Feature plugins **cannot** directly:

- Persist sessions (return values only)
- Create or delete sessions
- Publish events
- Switch agents
- Coordinate multiple sessions

For these capabilities, use [Application plugins](application-plugins.md) instead.

---

## Capabilities

### Core capabilities (Layer 1 - always available)

| Capability | Method/Access | Description |
|------------|---------------|-------------|
| Session operations | `core.slice_session()` | Create temporary sessions |
| Message operations | `core.add_message()` | Add messages to sessions |
| LLM requests | `core.send_request()` / `core.stream_request()` | Send LLM requests (same agent) |
| Native messages | `native_messages` parameter | Access provider-native history |
| Session info | `session` parameter | Access current session object |
| Config access | `context["config"]` | Current resolved config |

### Application capabilities (Layer 2 - when called from AgentApplication)

| Capability | Method/Access | Description |
|------------|---------------|-------------|
| Agent switching | `app.update_agent(agent_id, session)` | Switch to a different agent |
| Full LLM requests | `app.send_request(...)` | Full request with tool loop |
| Base config | `context["base_config"]` | Full application config (all agents) |
| Session assets | `context.get("session_asset_store")` | Access file attachments |

---

## Protocol

```python
class FeaturePlugin(BasePlugin, Protocol):
    # Identity (required)
    name: str
    version: str
    priority: int = 100  # Execution order (lower runs first)

    # Configuration
    def get_config_schema(self) -> Dict[str, Any]:
        """Return JSON schema for plugin configuration."""

    def get_ui_elements(
        self,
        config: Dict[str, Any],
        tags: List[str],
        models: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Return UI element definitions."""

    # Lifecycle
    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize with config and shared provider state."""

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Prepare for a new request (optional)."""

    # Message transformation (stateless)
    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Transform core messages to native (optional)."""

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Transform native messages to core (optional)."""

    # Finalization
    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Final processing after streaming (optional)."""

    # Actions
    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return session-scoped action definitions."""

    def execute_action(
        self,
        action_id: str,
        session: Session,
        native_messages: List[Dict[str, Any]],
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a session-scoped action."""

    # Capabilities
    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        """Return capability tags contributed by this feature."""

    def required_tags(self) -> List[str]:
        """Tags required for this feature to be enabled."""

    def forbidden_tags(self) -> List[str]:
        """Tags that disable this feature."""

    def is_enabled(
        self, config: Dict[str, Any], tags: List[str], models: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> Optional[bool]:
        """Complex enablement logic (optional)."""

    # Templates and completions (optional)
    def get_template(self, config: Dict[str, Any]) -> str:
        """Return a template string for applications."""

    def get_completions(self, config: Dict[str, Any], text: str) -> List[Dict[str, Any]]:
        """Return completion suggestions."""

    def apply_completion(self, config: Dict[str, Any], text: str, completion: Dict[str, Any]) -> str:
        """Transform an accepted completion."""
```

---

## Layered context in `execute_action`

Feature plugins receive layered context that provides different capabilities depending on where the action is triggered.

### Layer 1: Core-level context (always present)

When called from `AgentCore.execute_session_action()` or `AgentCore.execute_lifecycle_actions()`:

```python
context = {
    "core": self,              # AgentCore instance
    "config": config,          # Current resolved config
    "trigger_source": "core",  # Where action was triggered
    "session": session.to_dict(),  # Serialized session
    "lifecycle": trigger,      # Lifecycle trigger name (if applicable)
}
```

| Key | Type | Description |
|-----|------|-------------|
| `core` | `AgentCore` | Core instance for session/message operations |
| `config` | `dict` | Current resolved request configuration |
| `trigger_source` | `str` | Where action was triggered (`"core"`, `"application"`) |
| `session` | `dict` | Serialized session (`session.to_dict()`) |
| `lifecycle` | `str` | Lifecycle trigger name (for lifecycle-triggered actions) |

### Layer 2: Application-level context (when called from AgentApplication)

When called from `AgentApplication.execute_session_action()` or `AgentApplication.run_session_lifecycle()`:

```python
context = {
    # Layer 1 (from core)
    "core": core,
    "config": effective_config,
    "trigger_source": "application",
    "session": session.to_dict(),
    "lifecycle": lifecycle,  # if applicable

    # Layer 2 (from application)
    "app": self,             # AgentApplication instance
    "application": self,     # Alias for "app"
    "base_config": self._config,  # Full base config (all agents)
    "session_asset_store": self._session_asset_store,  # File attachment store
}
```

| Key | Type | Description |
|-----|------|-------------|
| `app` / `application` | `AgentApplication` | Application instance for enhanced capabilities |
| `base_config` | `dict` | Full application configuration (all agents) |
| `session_asset_store` | `SessionAssetStore` | File attachment store (optional) |

### Layer 3: Terminal/Server-level context (implementation-specific)

Terminal or HTTP server implementations may add additional context keys:

```python
# TerminalApplication may add:
context["terminal"] = self

# HTTP server may add:
context["server"] = self
context["request_id"] = request_id
```

These keys are implementation-specific and should be documented by the respective applications.

---

## Checking for capabilities

Feature plugins should gracefully handle missing capabilities by checking context:

```python
def execute_action(
    self,
    action_id: str,
    session: Session,
    native_messages: List[Dict[str, Any]],
    params: Dict[str, Any],
    context: Optional[Dict[str, Any]],
    state: Dict[str, Any],
) -> Dict[str, Any]:
    # Core is always available
    core = context["core"]
    config = context["config"]
    
    # Application is optional (check before using)
    app = context.get("app")
    base_config = context.get("base_config", config)
    
    if app is not None:
        # Application-level capabilities available
        # Can switch agents, use full request flow
        pass
    else:
        # Core-only mode
        # Use core.send_request() for same-agent requests
        pass
```

### Note on config resolution

The `config` key in context is the **resolved request configuration** for the current agent, passed to `execute_session_action()`. When called from `AgentApplication`, this is the result of `resolve_request_config(base_config, session_overrides)`.

The `base_config` key (when present) is the **full flattened agent configuration** from `build_agent_config()`. This includes all agent-level settings like `compaction`, `reasoning`, etc.

When implementing feature plugins that access agent-level configuration:

```python
# Correct: Use base_config for agent-level settings
compaction_cfg = base_config.get("compaction") or {}

# Fallback to config when base_config is not available (core-only calls)
if not compaction_cfg and "compaction" in config:
    compaction_cfg = config.get("compaction") or {}
```

### Error handling pattern

Feature plugins should return error dictionaries rather than raising exceptions, allowing the caller to decide how to handle errors:

```python
def execute_action(
    self,
    action_id: str,
    session: Session,
    native_messages: List[Dict[str, Any]],
    params: Dict[str, Any],
    context: Optional[Dict[str, Any]],
    state: Dict[str, Any],
) -> Dict[str, Any]:
    # Validate context
    if not isinstance(context, dict):
        return {
            "native_messages": native_messages,
            "error": {"type": "invalid_context", "message": "Context is required"},
        }
    
    core = context.get("core")
    if core is None:
        return {
            "native_messages": native_messages,
            "error": {"type": "missing_core", "message": "Context must include 'core'"},
        }
    
    # Check enablement
    base_config = context.get("base_config", context.get("config", {}))
    if not self._is_enabled(base_config):
        return {
            "native_messages": native_messages,
            "error": {"type": "disabled", "message": "Feature is not enabled."},
        }
    
    # ... rest of implementation
```

This pattern differs from Application plugins, which typically raise exceptions for validation errors. The difference exists because feature plugins operate at the core layer where errors should be returned as part of the result dictionary, allowing the core to properly handle native_messages updates even in error cases.

---

## Return value contract

Feature plugin `execute_action()` returns a dictionary with:

```python
{
    # Required: replacement native messages
    "native_messages": [...],  # Full provider-native history
    
    # Optional: session metadata patch
    "session_metadata": {
        "last_compaction": "2025-01-15T10:30:00",
        "compaction_count": 5,
    },
    
    # Optional: error information
    "error": {
        "type": "disabled",
        "message": "Feature is not enabled for this agent.",
    },
    
    # Optional: status
    "status": "ok",  # or "error", "noop"
    "message": "Operation completed successfully.",
    
    # Optional: debug information
    "debug_info": {...},
}
```

The `native_messages` field is required and should contain the full provider-native message history after the action is applied. The `session_metadata` field is merged into `session.metadata`.

---

## Action definitions

Feature plugins define session-scoped actions via `get_actions()`:

```python
def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "id": "compact_range",
            "label": "Compact range",
            "description": "Compact messages into a state snapshot.",
            "inputs": {
                "start": {"type": "integer", "required": False},
                "end": {"type": "integer", "required": False},
                "instructions": {"type": "string", "required": False},
            },
            # Optional: lifecycle triggers
            "trigger": ["session_save_prepare"],
        }
    ]
```

Unlike application plugins, feature plugin actions:
- Operate on a single session's native history
- Return replacement `native_messages` instead of mutations
- Cannot create/delete sessions or publish events

---

## Example implementation

```python
from datetime import datetime
from typing import Any, Dict, List, Optional

from agent_core import Message


class MyFeaturePlugin:
    """Example feature plugin demonstrating key capabilities."""
    
    name = "my_feature"
    version = "1.0.0"
    priority = 100
    
    def __init__(self) -> None:
        self._state: Dict[str, Any] = {}
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enabled": {"type": "boolean", "default": True},
            "max_items": {"type": "integer", "default": 100},
        }
    
    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        # Store config in state
        return {**state, "config": config}
    
    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        # Contribute capability tags
        return ["my_feature_capable"]
    
    def required_tags(self) -> List[str]:
        # No required tags
        return []
    
    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> tuple[list[Dict[str, Any]], list[Dict[str, Any]], Dict[str, Any]]:
        # Optional: modify final messages
        return final_messages, native_messages, state
    
    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "id": "summarize_range",
                "label": "Summarize range",
                "description": "Summarize a range of messages.",
                "inputs": {
                    "start": {"type": "integer", "required": False},
                    "end": {"type": "integer", "required": False},
                },
            }
        ]
    
    def execute_action(
        self,
        action_id: str,
        session: Any,
        native_messages: List[Dict[str, Any]],
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        if action_id != "summarize_range":
            return {
                "native_messages": native_messages,
                "error": {"type": "unknown_action", "message": f"Unknown action: {action_id}"},
            }
        
        # Validate context
        if not isinstance(context, dict):
            return {
                "native_messages": native_messages,
                "error": {"type": "invalid_context", "message": "Context is required"},
            }
        
        core = context.get("core")
        config = context.get("config", {})
        base_config = context.get("base_config", config)
        
        if core is None:
            return {
                "native_messages": native_messages,
                "error": {"type": "missing_core", "message": "Context must include 'core'"},
            }
        
        # Check enablement
        if not self._is_enabled(base_config):
            return {
                "native_messages": native_messages,
                "error": {"type": "disabled", "message": "Feature is not enabled."},
            }
        
        # Get parameters
        start = params.get("start")
        end = params.get("end")
        
        # Perform action using core capabilities
        # ...
        
        # Return modified native_messages
        new_native_messages = self._apply_summarization(native_messages, start, end)
        
        return {
            "native_messages": new_native_messages,
            "session_metadata": {
                "last_summarization": datetime.now().isoformat(),
            },
        }
    
    def _is_enabled(self, config: Dict[str, Any]) -> bool:
        feature_cfg = config.get("my_feature") or {}
        return feature_cfg.get("enabled", True)
    
    def _apply_summarization(
        self,
        native_messages: List[Dict[str, Any]],
        start: Optional[int],
        end: Optional[int],
    ) -> List[Dict[str, Any]]:
        # Implementation details...
        return native_messages
```

---

## Using application capabilities

When operating at Layer 2 (called from `AgentApplication`), feature plugins can access enhanced capabilities:

```python
def execute_action(
    self,
    action_id: str,
    session: Session,
    native_messages: List[Dict[str, Any]],
    params: Dict[str, Any],
    context: Optional[Dict[str, Any]],
    state: Dict[str, Any],
) -> Dict[str, Any]:
    core = context["core"]
    config = context["config"]
    app = context.get("app")
    base_config = context.get("base_config", config)
    
    # Check if we should use a different agent for summarization
    agent_id = base_config.get("summarization", {}).get("agent_id")
    
    if app is not None and agent_id:
        # Switch to dedicated summarization agent
        core_compact, base_config_compact, session_for_compact = app.update_agent(
            agent_id, session
        )
        # Use app.send_request for full tool loop support
        events = app.send_request(
            core_compact,
            session_for_compact,
            base_config_compact,
            {},
            stream=False,
        )
    else:
        # Core-only: use same agent
        new_session, final_messages = core.send_request(
            session,
            config,
        )
    
    # Process results...
    return {"native_messages": new_native_messages}
```

---

## UI elements

Feature plugins can also contribute UI elements. The shape is similar to application plugins:

```python
def get_ui_elements(
    self,
    config: Dict[str, Any],
    tags: List[str],
    models: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    # Filter based on enablement
    if not self._is_enabled(config):
        return []
    
    return [
        {
            "ui_type": "session_action",
            "id": "summarize_range",
            "label": "Summarize range",
            "icon": "compress",
            "order": 45,
            "action_id": "summarize_range",
            "dialog": {
                "kind": "form",
                "title": "Summarize range",
                "inputs": [
                    {"name": "start", "type": "integer", "label": "Start"},
                    {"name": "end", "type": "integer", "label": "End"},
                ],
            },
        }
    ]
```

---

## When to use FeaturePlugin vs ApplicationPlugin

| Use FeaturePlugin when | Use ApplicationPlugin when |
|-----------------------|---------------------------|
| You operate on native messages | You need to persist sessions |
| You want provider-agnostic behavior | You need multi-session coordination |
| You want lightweight, stateless operation | You need to switch agents |
| You participate in lifecycle hooks | You need to publish events |
| You return modified messages only | You need UI effects/navigation |
| You work at the core level | You need session locking |

---

## See also

- [Application plugins](application-plugins.md) for application-level capabilities
- [Provider extensions](provider-extensions.md) for hot-path streaming plugins
- [Plugin actions](actions.md) for action and lifecycle documentation
- [Provider plugins](provider-plugins.md) for provider implementation