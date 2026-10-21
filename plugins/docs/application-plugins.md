# Application plugins

Application plugins (`ApplicationPlugin`) operate at the application layer with full access to session persistence, multi-session coordination, and UI effects. They are the most powerful plugin type and are suitable for features that need application-level capabilities.

This page documents ApplicationPlugin capabilities, context structure, and when to use them versus other plugin types.

Runtime references (source of truth):

- Protocol: `core/python/agent_app/app_plugins.py`
- Application context: `core/python/agent_app/application_future.py`
- Shared session listing: `core/python/agent_app/session_listing.py`

Reference implementations:

- `plugins/gemini-compaction-app/src/gemini_compaction_app/__init__.py`

Related guides:

- [Notifications and action displays](notifications-and-action-displays.md)
- [Plugin actions](actions.md)

---

## What application plugins are for

Application plugins are ideal for features that need:

- **Session persistence**: Load and save sessions to the session store
- **Multi-session coordination**: Create, fork, delete, or coordinate multiple sessions
- **Application-owned settings**: Read and update server-scoped settings or
  per-session settings without owning separate persistence
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
| List session summaries | `app.list_session_summaries(...)` | Build shared fields, presentation, ordering, optional in-process filtering, and limits |
| Load one session summary | `app.get_session_summary(session_id)` | Build the same summary contract for one exact ID without list filtering |
| List diagnostics | `app.get_session_list_diagnostics()` | Inspect nonfatal field/action/order diagnostics from the latest list query |
| Save sessions | `app.save_session(session)` | Persist a session to the session store |
| Server settings | `app.get_server_settings()` | Read application-owned server-scoped settings |
| Update server settings | `app.patch_server_settings(values, source=...)` | Persist server-scoped setting updates and run lifecycle triggers |
| Delete server setting | `app.delete_server_setting(key, source=...)` | Remove one server-scoped setting and run lifecycle triggers |
| Session settings | `app.get_session_settings(session_id)` | Read per-session settings stored in session overrides |
| Update session settings | `app.patch_session_settings(session_id, values, source=...)` | Persist per-session setting updates and run lifecycle triggers |
| Delete session setting | `app.delete_session_setting(session_id, key, source=...)` | Remove one per-session setting and run lifecycle triggers |
| LLM requests | `app.send_request(core, session, config, overrides)` | Send an LLM request with tool loop |
| Session locking | `app.acquire_session_lock(session_id)` | Context manager for safe concurrent access |
| Event publishing | `app.publish_event(event)` | Publish events to subscribers |
| Switch agents | `app.update_agent(agent_id, session)` | Switch a session to a different agent |
| Request full reload | `app.request_application_reload(reason=..., on_failure=...)` | Ask the owner to drain admitted work and reconstruct `AgentApplication` |
| Application notifications | `app.create_application_notification(...)`, `update_application_notification(...)`, `dismiss_application_notification(...)`, `resolve_application_notification(...)`, `expire_application_notification(...)`, `list_application_notifications()` | Create durable notifications global to one connected application runtime. |
| Session notifications | `app.create_session_notification(...)`, `update_session_notification(...)`, `update_session_notification_by_key(...)`, `dismiss_session_notification(...)`, `resolve_session_notification(...)`, `expire_session_notification(...)`, `list_session_notifications(...)` | Create persistent session notifications stored in metadata and published through lifecycle events. |
| Application operations | `get_application_operation_service(app.get_runtime_store())` | Reserve minimal active identity and cross-producer admission without storing plugin status, progress, presentation, or outcomes. |
| Full config access | `self._config` (via `init`) | Access to the full application configuration |
| Runtime env access | `os.environ[...]` | Real process environment installed from config resolution env |
| Request config resolution | `resolve_request_config(base_config, overrides)` | Resolve effective config for a request |

Server settings are application-owned state. Plugins may expose UI controls for
those settings and react to `server_settings_changed`, but should not maintain a
second authoritative copy in plugin-owned persistence. Plugin-owned sidecar
files are still appropriate for private caches, credentials, or implementation
state that is not user-editable server configuration.

`request_application_reload` returns an accepted result immediately. Plugins
must not close or replace their own application. The owner rejects new
application operations, waits for admitted work, constructs and validates the
replacement, and emits application-global requested/completed/failed
notifications. `on_failure` is an optional in-process compensating callback for
plugin-owned writes such as restoring a dotenv file.

Application plugins can create owner-scoped application notifications and
persistent session notifications through the methods listed above. The
notification APIs validate records and report malformed input to the calling
application plugin. Tools use a separate failure-contained
`notification_sink`.

Application notifications are stored in the runtime's injected durable store
and survive application replacement and server-process restart until
retention removes them. Session notifications are stored in
`Session.metadata["notifications"]["items"]` and remain hidden from model
history. Records have monotonic revisions and support pending, dismissed,
resolved, and expired states.

Producers publish notifications using stable keys. Repeated publication
updates the active occurrence for that key. If the key currently maps to a
terminal record, publication creates a new lifecycle occurrence. Producer
publication (create, update, resolve, expire) does not require
`expected_revision`; the notification service owns revision assignment and
increment. Dismissal is the only frontend lifecycle mutation that accepts
optional `expected_revision`, so a stale user gesture cannot hide a newer
revision or a later stable-key occurrence.

For complete record fields, examples, presentation behavior, stable-key
publication, dismissal, resolution, expiration, tool-sink usage, current
frontend integration limitations, event names, and focused test commands, see
[Notifications and action displays](notifications-and-action-displays.md).

For background work, keep active registration, runtime ownership, and
presentation separate:

- use `ApplicationOperationService` for active identity, lookup, and admission;
- use `ManagedProcessRegistry` for the concrete process object;
- let the plugin/process own status, progress, cancellation, and outcomes;
- use notifications for visible progress and follow-up actions.

The application operation contract and future operation-history direction are
documented in `application/python/docs/development/operations.md`.

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
        context: Optional[Dict[str, Any]] = None,
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

Plugins that hold process resources may also implement an optional cleanup
hook:

```python
def close(self, state: Dict[str, Any]) -> None:
    ...
```

`AgentApplication.close()` calls this hook when present. The hook should be
idempotent and release resources owned by the plugin, such as background
processes or OS handles.

For background work that must be found by later actions and close with the
application generation, prefer the shared
[managed background process registry](managed-background-processes.md). It is
stored in `RuntimeStore`, so plugins do not need to duplicate process maps or
add another `AgentApplication` contract.

---

## UI context in `get_ui_elements`

Application plugins should prefer the context-aware UI signature:

```python
def get_ui_elements(
    self,
    state: dict[str, Any],
    config: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    ...
```

The application wrapper keeps older signatures working for compatibility,
including:

- `get_ui_elements()`
- `get_ui_elements(state)`
- `get_ui_elements(state, config)`
- `get_ui_elements(state, config, tags, models)`

New plugins should read `tags`, `models`, and surface-specific data from
`context`, not as positional parameters.

Common UI context keys:

| Key | Type | Description |
|-----|------|-------------|
| `ui_context` | `str` | UI surface name, such as `"application"`, `"session"`, or `"server_settings"` |
| `config` | `dict` | Effective configuration for the current UI surface |
| `tags` | `list[str]` | Capability tags computed for this config, when available |
| `models` | `list[dict]` | Model descriptors computed for this config, when available |
| `session` | `dict` | Serialized session for session-contextual UI schema |
| `session_id` | `str` | Session id for session-contextual UI schema |
| `server_settings` | `dict` | Current application-owned server settings for all application UI-schema surfaces |
| `settings` | `dict` | Generic alias for the active settings scope |
| `settings_scope` | `str` | Settings scope, such as `"server"` |

Server settings are supplied through `context["server_settings"]`; they are not
configuration and should not be read from `config`.

Because the current values are available on ordinary application and session
UI-schema surfaces too, a plugin can use a server setting to include or omit a
declarative list field, filter, or action. Keep the application configuration
as the startup default and treat a persisted server setting as the live
override:

```python
settings = (context or {}).get("server_settings") or {}
enabled = settings.get(
    "session_status_show_in_session_list_footer",
    state["configured_default"],
)
```

The persisted settings mapping remains authoritative. Do not mirror
user-editable settings into a second plugin-owned state store merely to
generate UI schema.

---

## Runtime env contract

`AgentApplication` installs the same runtime env mapping used during config
placeholder resolution into the real process environment before application
plugins initialize.

Example:

```python
import os


def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
    config_dir = os.environ.get("CONFIG_DIR")
    return {
        "config_dir": config_dir,
    }
```

This runtime environment is intended for path derivation and subprocesses that
need to inherit the same anchors used during `${env:...}` config resolution.
Common keys include:

- `CONFIG_DIR`
- `WORKING_DIR`
- `BUILTIN_PLUGINS`

This is the preferred way for application plugins to anchor sidecar files such
as cached metadata, auth credentials, or other application-owned state.

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
    ctx = context or {}
    lifecycle = ctx.get("lifecycle")  # e.g., "session_create"
    trigger_source = ctx.get("trigger_source")  # "application"
    session_dict = ctx.get("session")  # Serialized session
    config = ctx.get("config")  # Effective config
    base_config = ctx.get("base_config")  # Full app config
    changed_keys = ctx.get("changed_keys", [])  # Settings lifecycles
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
| `scope` | `str` | Settings lifecycle scope, usually `"session"` or `"server"` |
| `old_settings` | `dict` | Previous settings map for settings-change lifecycles |
| `new_settings` | `dict` | Updated settings map for settings-change lifecycles |
| `changed_keys` | `list[str]` | Setting keys changed by the lifecycle owner |
| `source` | `str` | Change source, such as `"api"`, `"startup"`, or `"bridge_sync"` |

Application-scoped lifecycles such as `server_settings_changed` do not include
`session` or `session_id`. Plugins should check for those keys before using
them.

An application-owned background process that must call
`AgentCore.execute_session_action(...)` directly should build its context
through `app.build_core_handoff_context(...)`. Pass the captured base and
effective configurations plus process-specific extra context. This preserves
application dependencies such as `session_asset_store` and runtime stores
without copying the application context schema into the plugin. Ordinary
actions should continue to prefer `app.execute_session_action(...)`, which
builds this handoff context automatically.

---

## Action definitions

### Snapshot before a destructive session mutation

Application plugins receive the active `AgentApplication`, including the
public session snapshot methods. A destructive action can create a recovery
point after validation and immediately before saving the changed session:

```python
snapshot = app.create_session_snapshot(
    session_id,
    reason="Before deleting messages [12:]",
    metadata={
        "origin": "automatic",
        "plugin": self.name,
        "action": "delete_messages",
        "range": {"start": 12, "end": len(session.messages)},
    },
)

try:
    saved = app.save_session(updated_session)
except BaseException:
    app.delete_session_snapshot(session_id, snapshot.snapshot_id)
    raise
```

Run validation first so no-op or invalid actions do not create snapshots. Keep
snapshot creation and persistence under the same session lock. For background
operations, create the snapshot at the final commit boundary rather than when
provider work starts, so cancellation and provider failure leave no recovery
record.

This is a plugin-owned policy, not automatic behavior for every application
action. Plugins should use precise pre-state reasons and structured origin,
plugin, action, and normalized range metadata. Snapshot storage and retention
behavior is owned by the application.

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
| `session_list` | While the application builds each shared session summary |
| `session_create` | After a new session is created |
| `session_save_prepare` | Before a session is saved |
| `request_prepare` | Before an LLM request |
| `request_complete` | After a successful request |
| `request_error` | After a failed request |
| `session_fork` | After a session is forked |
| `agent_switch_prepare` | Before switching agents |
| `agent_switch_complete` | After switching agents |
| `session_settings_changed` | After application-owned per-session settings change |
| `server_settings_changed` | After application-owned server settings change |
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
        "reload_sessions_list": true,
        "reload_application_actions": true,
        "navigate_to_session_id": "session-2",
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

### Action/notification UI-effect relationship

Application-action responses retain the complete action UI-effect contract:

- refresh effects:
  - `reload_session_ids`;
  - `reload_sessions_list`;
  - `reload_application_actions`;
- action-only navigation:
  - `navigate_to_session_id`.

The three refresh effects are reused by both session and application
notifications. They are connection-scoped, idempotent
invalidation requests and do not open sessions or change focus.

`navigate_to_session_id` is intentionally not shared with asynchronous
notifications. For example, a user-invoked Fork action may navigate to the new
session, but a background notification must not unexpectedly move the user
away from the session or screen they are viewing. A notification follow-up may
invoke an action that navigates after the user explicitly chooses it.

Action `mutations` remain separate from UI effects. Existing frontend policy
may infer session-list refresh or created-session navigation from an action's
mutation result. Notifications do not have mutation semantics and must request
refreshes explicitly.

See [Notifications and action displays](notifications-and-action-displays.md)
for the proposed notification delivery and revision-deduplication rules.

---

## UI elements

Application plugins contribute UI elements via `get_ui_elements()`. The UI element shape differs from core plugins:

Actions returned by `get_actions()` are callable procedures, not automatic UI
or command inventory. Every user-facing exposure is an applicable
action-backed UI element. This includes `application_action`,
`session_action`, `session_list_action`, `message_action`, `cli_command`, and
`slash_command`. Several elements may intentionally bind the same procedure.

New command integrations use `cli_command` and `slash_command` elements
documented in [UI elements](ui-elements.md#command-elements-cli_command-and-slash_command).
The older `get_commands()` hook is compatibility-only: the application adapts
its declarations to top-level CLI commands and never creates slash commands or
`/action` entries from them.

```python
def get_ui_elements(
    self,
    state: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
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

### Session-list contributions

Application plugins can contribute three independent parts of a session list:

1. ordinary row actions via `ui_type: "session_list_action"`;
2. presentation fields via `ui_type: "session_list_field"`;
3. declarative filters via `ui_type: "session_list_filter"`.

An ordinary `session_list_action` may additionally contain optional
`rich_ui.kind: "toggle"` or `"list"` metadata. This is a frontend enhancement,
not a new action type: retain `dialog`, `action_id`, and parameter mapping so
unsupported/invalid rich presentation always falls back to the ordinary
action. Pin/archive use immediate toggles; status uses an immediate list that
passes the selected option through its existing `$dialog.status` map.

They can also define an action with `trigger: "session_list"` to compute
summary fields and ordering:

```python
def get_actions(self, state):
    return [
        {
            "id": "compute_list_values",
            "label": "Compute list values",
            "trigger": "session_list",
            "inputs": {
                "session_id": {"type": "string", "required": True},
                "session_summary": {"required": True},
                "session": {"required": False},
            },
        }
    ]


def execute_action(self, app, action_id, params, context, state):
    summary = params["session_summary"]
    rank = 0 if summary.get("metadata", {}).get("important") else 1
    return {
        "session_list_fields": {
            "importance_rank": rank,
        },
        "session_list_order": [
            {
                "key": "importance_rank",
                "direction": "asc",
                "fallback": 1,
                "priority": 10,
            }
        ],
    }
```

`AgentApplication` is the application-facing authority for enumeration,
summary construction, trigger execution, presentation, and ordering. HTTP and
terminal adapters call the application methods rather than inspect a
filesystem session root.

The returned summary shape is:

```typescript
interface SessionSummary {
  session_id: string;
  modified: number;
  preview: string;
  metadata: Record<string, unknown>;
  presentation: {
    title: string;
    subtitle: string | null;
    meta: string | null;
  };
  [contributedField: string]: unknown;
}
```

`metadata.native_messages` is excluded because it may contain a heavyweight
provider-native copy of the transcript. Feature values such as pin, archive,
or status remain under their configured `metadata.*` paths rather than being
projected into feature-specific top-level fields.

The query API is:

```python
app.list_session_summaries(
    filter_values=None,
    apply_filter_defaults=False,
    limit=None,
)
```

Ordering happens first, optional in-process filtering second, and `limit`
last. HTTP requests the unfiltered collection. Terminal integrations can
supply filter state in-process. `app.get_session_summary(session_id)` is exact
and independent of list filters.

`session_list_filter` is metadata, not an action: it has no `action_id` and is
never passed to `execute_action`. One valid text filter may set
`main_search: true`. Terminal free-text search requires that declaration.
Mobile and desktop use it when available and retain a shared local summary-text
fallback search when it is absent or ambiguous; ambiguity is still exposed as
a schema diagnostic. See [UI elements](ui-elements.md), under
“Session-list filters,” for the full type, default, matching, Reset, and
Show-all contract.

The built-in `session-pinned-app` and `session-status-app` plugins are concrete
examples of keeping actions and filters aligned around one configurable
metadata key. Pinning declares one rich toggle at both the trailing title
header and the user-configurable action bar, then contributes an
inactive-by-default Boolean filter. Status contributes an ordinary select-form
row action and an inactive-by-default multi-select filter. Missing status
behaves as `todo`; selecting `todo` for an old session is therefore a no-op
unless a different explicit value was stored. Both mutation actions save a new
immutable `Session`, publish `session_metadata_updated`, record a checkpoint,
and report updated-session mutations.

Public HTTP adapters expose:

```text
GET /sessions
GET /sessions/{session_id}/summary
GET /application/ui-schema
```

The first two return application-derived summaries. The global UI-schema
endpoint carries list action, field, and filter declarations. See
[UI elements](ui-elements.md) and [Plugin actions](actions.md) for complete
normalization, fallback, dialog, filter, and ordering rules.

---

### Server-scoped settings UI

Application plugins can expose server-scoped settings by returning config-like
UI elements with `scope: "server"`. Frontends read these from
`GET /server/settings/ui-schema`, then read and write current values through the
server settings API.

```python
from typing import Any


class KeepAwakePlugin:
    name = "keep_awake"
    version = "1.0.0"

    def init(self, app_config: dict[str, Any]) -> dict[str, Any]:
        return {"enabled": False}

    def get_ui_elements(
        self,
        state: dict[str, Any],
        config: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        settings = (context or {}).get("server_settings") or {}
        label = "Keep server awake"
        if settings.get("keep_awake_enabled"):
            label = "Keep server awake (enabled)"
        return [
            {
                "ui_type": "config",
                "scope": "server",
                "key": "keep_awake_enabled",
                "type": "checkbox",
                "label": label,
                "default": False,
            }
        ]

    def get_actions(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {
                "id": "apply_keep_awake",
                "label": "Apply keep-awake setting",
                "inputs": {},
                "trigger": "server_settings_changed",
            }
        ]

    def execute_action(
        self,
        app: Any,
        action_id: str,
        params: dict[str, Any],
        context: dict[str, Any] | None,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        settings = (context or {}).get("new_settings") or app.get_server_settings()
        enabled = bool(settings.get("keep_awake_enabled", False))
        state["enabled"] = enabled
        return {"message": "Keep-awake state applied.", "enabled": enabled}
```

Settings lifecycle handlers should be idempotent. `server_settings_changed` may
also run during startup replay when persisted server settings already exist, so
plugins should apply the desired state rather than assuming every call came from
a fresh user interaction.

The built-in `sleep-prevention-app` plugin is a concrete example of this
pattern: it exposes a `sleep_prevention_enabled` server setting and applies or
releases the local OS sleep-prevention hold from `server_settings_changed`.

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

## Pattern: Background auth flows

Application plugins are the right place for minimal login flows that need to:

- start a long-running process in the background
- write credentials to disk under `CONFIG_DIR`
- expose small manual actions such as `login_start`, `check_status`, `cancel_login`, and `logout`

For cross-device login, keep persistence in the application plugin itself:

1. `login_start` begins the backend-side workflow and returns a URL/code.
2. A background worker polls or waits for completion.
3. The plugin writes credentials atomically when login succeeds.
4. `check_status` reports state only; it should not be responsible for saving credentials.

Provider or feature plugins can then consume the saved file during request-time
runtime setup.

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