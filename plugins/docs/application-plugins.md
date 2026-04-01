# Application plugins

Application plugins (`ApplicationPlugin`) operate at the application layer with full access to session persistence, multi-session coordination, and UI effects. They are the most powerful plugin type and are suitable for features that need application-level capabilities.

This page documents ApplicationPlugin capabilities, context structure, and when to use them versus other plugin types.

Runtime references (source of truth):

- Protocol: `core/python/agent_app/app_plugins.py`
- Application context: `core/python/agent_app/application_future.py`

Reference implementations:

- `plugins/gemini-compaction-app/src/gemini_compaction_app/__init__.py`

---

## What application plugins are for

Application plugins are ideal for features that need:

- **Session persistence**: Load and save sessions to the session store
- **Multi-session coordination**: Create, fork, delete, or coordinate multiple sessions
- **LLM requests**: Send requests through the application layer with full tool loop support
- **Session locking**: Acquire locks for safe concurrent session modifications
- **Event publishing**: Publish events for UI updates or other subscribers
- **Agent switching**: Switch a session from one agent to another
- **UI effects**: Return navigation hints, reload requests, or other UI coordination

---

## Capabilities

| Capability | Method/Access | Description |
|------------|---------------|-------------|
| Load sessions | `app.load_session(session_id)` | Load a session from the session store |
| Save sessions | `app.save_session(session)` | Persist a session to the session store |
| LLM requests | `app.send_request(core, session, config, overrides)` | Send an LLM request with tool loop |
| Session locking | `app.acquire_session_lock(session_id)` | Context manager for safe concurrent access |
| Event publishing | `app.publish_event(event)` | Publish events to subscribers |
| Switch agents | `app.update_agent(agent_id, session)` | Switch a session to a different agent |
| Full config access | `self._config` (via `init`) | Access to the full application configuration |
| Request config resolution | `resolve_request_config(base_config, overrides)` | Resolve effective config for a request |

---

## Protocol

```python
class ApplicationPlugin(Protocol):
    # Identity (required)
    name: str
    version: str

    # Configuration
    def get_config_schema(self) -> Dict[str, Any]:
        """Return JSON schema for plugin configuration."""

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Return UI element definitions."""

    # Lifecycle
    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize plugin state from application config."""

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return action definitions."""

    def execute_action(
        self,
        app: "AgentApplication",
        action_id: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute an action with validated parameters."""
```

---

## Context in `execute_action`

Application plugins receive the `AgentApplication` instance as the first parameter to `execute_action`. This provides full access to application capabilities.

Additional context is available via the `context` parameter:

```python
def execute_action(
    self,
    app: "AgentApplication",
    action_id: str,
    params: Dict[str, Any],
    context: Optional[Dict[str, Any]],
    state: Dict[str, Any],
) -> Dict[str, Any]:
    # Application instance
    app.load_session(session_id)
    app.save_session(session)
    app.send_request(core, session, config, overrides)
    
    # Context (for lifecycle-triggered actions)
    lifecycle = context.get("lifecycle")  # e.g., "session_create"
    trigger_source = context.get("trigger_source")  # "application"
    session_dict = context.get("session")  # Serialized session
    config = context.get("config")  # Effective config
    base_config = context.get("base_config")  # Full app config
```

### Context keys

| Key | Type | Description |
|-----|------|-------------|
| `lifecycle` | `str` | Lifecycle trigger name (e.g., `"session_create"`) |
| `trigger_source` | `str` | Where action was triggered (`"application"`, `"manual"`) |
| `session` | `dict` | Serialized session (`session.to_dict()`) |
| `config` | `dict` | Effective config for the current agent |
| `app` / `application` | `AgentApplication` | Application instance |
| `base_config` | `dict` | Full application configuration (all agents) |

---

## Action definitions

Application plugins define actions via `get_actions()`. Each action is a dictionary describing the action's interface:

```python
def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "id": "compact_range",
            "label": "Compact range",
            "description": "Compact messages into a state snapshot.",
            "inputs": {
                "session_id": {"type": "string", "required": True},
                "start": {"type": "integer", "required": False},
                "end": {"type": "integer", "required": False},
                "instructions": {"type": "string", "required": False},
            },
            # Optional: lifecycle triggers
            "trigger": ["session_create", "request_prepare"],
        }
    ]
```

### Lifecycle triggers

Actions can include a `trigger` field to be automatically invoked during application lifecycle events:

| Trigger | When it runs |
|---------|--------------|
| `session_create` | After a new session is created |
| `session_save_prepare` | Before a session is saved |
| `request_prepare` | Before an LLM request |
| `request_complete` | After a successful request |
| `request_error` | After a failed request |
| `session_fork` | After a session is forked |
| `agent_switch_prepare` | Before switching agents |
| `agent_switch_complete` | After switching agents |
| `session_delete_prepare` | Before a session is deleted |

See [Plugin actions](actions.md) for detailed lifecycle documentation.

---

## Return value contract

Application plugin actions return a dictionary with the following structure:

```python
{
    # Session mutations (optional)
    "mutations": {
        "created_session_ids": ["new-session-1"],
        "updated_session_ids": ["session-2"],
        "deleted_session_ids": ["session-3"],
    },
    
    # UI effects (optional)
    "ui_effects": {
        "reload_session_ids": ["session-2"],
        "navigate": {"screen": "sessions"},
    },
    
    # Result message (optional)
    "message": "Operation completed successfully.",
    
    # Error information (for failures)
    "status": "error",
    "error_type": "disabled",
    "message": "Feature is not enabled.",
    
    # Plugin-specific data
    "debug": {...},
}
```

---

## UI elements

Application plugins contribute UI elements via `get_ui_elements()`. The UI element shape differs from core plugins:

```python
def get_ui_elements(
    self,
    state: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
    models: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    return [
        # Session action button
        {
            "ui_type": "session_action",
            "id": "compact_range",
            "label": "Compact range",
            "icon": "archive",
            "order": 45,
            "action_id": "compact_range",
            "fixed_params": {},
            "param_map": {
                "session_id": "$session.session_id",
                "start": "$dialog.start",
                "end": "$dialog.end",
            },
            "dialog": {
                "kind": "form",
                "title": "Compact range",
                "inputs": [...],
            },
        },
        # Message action button (appears on each message)
        {
            "ui_type": "message_action",
            "id": "compact_up_to_here",
            "label": "Compact up to here",
            "icon": "archive",
            "order": 25,
            "action_id": "compact_range",
            "fixed_params": {"start": 0, "end_inclusive": True},
            "param_map": {
                "session_id": "$session.session_id",
                "end": "$message.index",
            },
        },
    ]
```

---

## Example implementation

```python
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from agent_app.application_future import AgentApplication


class MyApplicationPlugin:
    """Example application plugin demonstrating key capabilities."""
    
    name = "my_app_plugin"
    version = "1.0.0"
    
    def __init__(self) -> None:
        self._state: Dict[str, Any] = {}
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enabled": {"type": "boolean", "default": True},
            "max_iterations": {"type": "integer", "default": 10},
        }
    
    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        # Filter based on enablement if config is provided
        if config is not None and not config.get("my_app_plugin", {}).get("enabled", True):
            return []
        
        return [
            {
                "ui_type": "session_action",
                "id": "my_action",
                "label": "My Action",
                "icon": "star",
                "order": 50,
                "action_id": "my_action",
                "dialog": {"kind": "form", "title": "My Action", "inputs": []},
            }
        ]
    
    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        # Store any application-level state
        return {"app_config": app_config}
    
    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "id": "my_action",
                "label": "My Action",
                "description": "Perform an application-level action.",
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                },
                # Optional: trigger on session creation
                "trigger": "session_create",
            }
        ]
    
    def execute_action(
        self,
        app: "AgentApplication",
        action_id: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        if action_id != "my_action":
            raise ValueError(f"Unknown action: {action_id}")
        
        session_id = params.get("session_id")
        if not session_id:
            raise ValueError("session_id is required")
        
        # Load session with lock
        with app.acquire_session_lock(session_id):
            ctx = app.load_session(session_id)
            if ctx is None:
                raise KeyError(f"Session {session_id} not found")
            
            core, base_config, session = ctx
            
            # Perform operations
            # ... your logic here ...
            
            # Save modified session
            app.save_session(session)
        
        # Publish event for UI update
        app.publish_event({
            "type": "my_action_complete",
            "session_id": session_id,
        })
        
        return {
            "mutations": {
                "updated_session_ids": [session_id],
            },
            "ui_effects": {
                "reload_session_ids": [session_id],
            },
            "message": "Action completed successfully.",
        }
```

---

## When to use ApplicationPlugin vs FeaturePlugin

| Use ApplicationPlugin when | Use FeaturePlugin when |
|---------------------------|------------------------|
| You need to persist sessions | You operate on native messages only |
| You need multi-session coordination | You want provider-agnostic behavior |
| You need to switch agents | You need lightweight, stateless operation |
| You need to publish events | You want to work at the core level |
| You need UI effects/navigation | You only need to return modified messages |
| You need session locking | You want to participate in lifecycle hooks |

See also:

- [Feature plugins](feature-plugins.md) for core-level plugin documentation
- [Provider extensions](provider-extensions.md) for hot-path streaming plugins
- [Plugin actions](actions.md) for action and lifecycle documentation