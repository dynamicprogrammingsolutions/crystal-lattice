# Plugin actions

This page describes the plugin action model, including lifecycle-triggered
actions, as a completed runtime feature.

The core idea is that plugins expose one action concept, and actions may be:

- manually triggered by a user or UI
- triggered automatically by a lifecycle event

The distinction between application plugins and other plugin types is not the
action naming. The distinction is where actions run, what they are allowed to
return, and whether they are limited to a single session mutation scope.

Runtime references for the current codebase:

- `core/python/agent_app/app_plugins.py`
- `core/python/agent_app/application_future.py`
- `core/python/agent_app/session_listing.py`
- `core/python/agent_core/types.py`
- `core/python/agent_core/core.py`
- `application/python/agent_terminal_app/server.py`

## Overview

Actions follow these rules:

- Application plugins continue to define actions with `get_actions(...)` and
  execute them with `execute_action(...)`.
- Provider extensions use the same action concept and the same method names
  for session-scoped actions.
- Lifecycle-triggered work is modeled as an ordinary action with a `trigger`
  field, rather than a second hook naming scheme.
- `AgentApplication` decides when lifecycle-triggered actions run.
- `AgentCore` executes lifecycle-triggered actions for core-side plugins and
  returns a modified `Session`.

## Generic display payloads

Successful actions may return a generic user-facing display payload in
`result.display`.

This is the preferred way for plugins to tell frontends to show instructions,
status summaries, or rich follow-up text without introducing plugin-specific
result keys.

For choosing between an application notification, session notification, tool
notification, and direct action display, see
[Notifications and action displays](notifications-and-action-displays.md).

Recommended shape:

```json
{
  "display": {
    "format": "markdown",
    "title": "ChatGPT Login",
    "body": "Open [this link](https://example.test) and enter code `ABCD-EFGH`.",
    "variant": "info",
    "presentation": "inline",
    "dismissible": true,
    "display_id": "chatgpt-auth-login",
    "actions": [
      {
        "kind": "open_url",
        "id": "open-login-link",
        "label": "Open link",
        "url": "https://example.test"
      },
      {
        "kind": "copy_text",
        "id": "copy-login-code",
        "label": "Copy code",
        "text": "ABCD-EFGH"
      },
      {
        "kind": "run_action",
        "id": "check-login-status",
        "label": "Check status",
        "plugin": "chatgpt_auth",
        "action_id": "check_status",
        "preserve_display": true
      },
      {
        "kind": "dismiss",
        "id": "dismiss-login-instructions",
        "label": "Close"
      }
    ]
  }
}
```

Fields:

- `format`: `"markdown"` or `"text"`
- `body`: required display content
- `title`: optional heading
- `variant`: optional tone hint such as `info`, `success`, `warning`, or
  `error`
- `presentation`: optional frontend hint such as `modal`, `inline`, or
  `banner`
- `dismissible`: optional hint controlling whether the user can dismiss the
  rendered display
- `display_id`: optional stable id so frontends can update or replace an
  existing inline/banner display instead of always appending a new one
- `form`: optional embedded form; uses the same `kind: "form"` and `inputs`
  schema as action dialogs
- `actions`: optional list of generic follow-up actions

Guidance:

- keep `display` user-oriented and safe to render directly
- keep machine-readable fields alongside it when frontend logic or tests still
  need structured state
- do not overload top-level `message` keys for successful rich content when
  `display` is more appropriate
- keep follow-up actions intentionally narrow and generic; current supported
  shapes are `open_url`, `copy_text`, `run_action`,
  `download_attachment_asset`, and `dismiss`
- `presentation` is a standard cross-platform contract:
  - `banner` uses the connection-aware top notification rail
  - `inline` uses the nearest owning Sessions or Messages region
  - `modal` uses a mobile modal or desktop action-display window for direct
    action responses; desktop notification modals retain their inline fallback
- application, session, session-list, and message action responses honor valid
  explicit presentation subject to the host fallback above
- notification persistence, allowed presentations, placement, lifecycle, and
  current dismissal behavior are documented in
  [Notifications and action displays](notifications-and-action-displays.md)

Application actions that request full reload return an accepted result rather
than waiting for active work. The stable application owner publishes
application-global notification events for requested, completed, and failed
states. Frontends refresh action definitions only after completion, when the
replacement application is active.

Actions that launch application-lifetime work should use the shared
[managed background process](managed-background-processes.md) contract. The
action can return an accepted result promptly, while later actions look up the
concrete process for operation-specific status or cancellation.

When the work also needs session admission or active lookup, reserve an
application operation separately. Managed processes and plugins own runtime
status and behavior; application operations own only active identity and
admission; notifications own presentation. See
`application/python/docs/development/operations.md`.

### Embedded display forms

Action displays may include an embedded form when the user should enter values
directly in the returned display surface before pressing a follow-up action.

The embedded form schema is intentionally the same form schema used by action
dialogs:

```json
{
  "display": {
    "format": "markdown",
    "title": "Finish external login",
    "body": "Paste the callback URL from your browser.",
    "variant": "info",
    "presentation": "inline",
    "form": {
      "kind": "form",
      "inputs": [
        {
          "name": "callback_url",
          "type": "multiline",
          "label": "Callback URL",
          "placeholder": "http://127.0.0.1:41793/callback?code=...&state=...",
          "required": true
        },
        {
          "name": "note",
          "type": "string",
          "label": "Note",
          "submit_empty": true
        }
      ]
    },
    "actions": [
      {
        "kind": "run_action",
        "id": "submit-callback-url",
        "label": "Submit",
        "plugin": "example_login_app",
        "action_id": "finish_login_from_callback_url",
        "fixed_params": {
          "source": "display_form"
        },
        "param_map": {
          "callback_url": "$form.callback_url",
          "note": "$form.note"
        },
        "preserve_display": true
      },
      {
        "kind": "dismiss",
        "id": "cancel-callback-url",
        "label": "Cancel"
      }
    ]
  }
}
```

Follow-up `run_action` entries may use `param_map` just like action UI
elements. Values entered into the embedded display form are addressed with
`$form.<field_name>`. Existing action dialogs continue to use
`$dialog.<field_name>`.

Default text inputs rendered for embedded display forms and action dialogs
carry the stable test identifier `action-form-input-<field_name>`, so native
UI tests can target plugin-declared fields by name.

For a direct action display, use `dismiss` when the display should close
locally without a backend call. Notification dismissal behavior is documented
separately in
[Notifications and action displays](notifications-and-action-displays.md).

For manual testing, the `plugins/dummy-action-display-form-app` plugin exposes
a `Show display form` session action that returns an embedded form and echoes
submitted values in a confirmation display.

### Future follow-up dialog proposal

Some workflows may eventually need a display action that opens a separate form
dialog rather than showing fields inline in the display. The proposed future
shape is for a `run_action` display action to include a `dialog` object that
reuses the same action-dialog schema, with submitted values mapped through
`$dialog.<field_name>`. This is not part of the current implemented contract;
it is tracked in `tasks/20260620-action-display-followup-dialogs.md`.

## Dynamic lifecycle names

Lifecycle names are dynamic strings.

That means:

- future application implementations may call `AgentApplication` with
  arbitrary lifecycle names
- future plugins may declare arbitrary lifecycle names in `trigger`
- the contract should not require lifecycle names to be chosen from a fixed
  enum baked into the API

The system still has a standard built-in lifecycle baseline for normal app
flows, but that baseline is not the full allowed set.

## Triggered actions

An action definition may include a `trigger` field.

Examples:

- `"trigger": "session_list"`
- `"trigger": "session_create"`
- `"trigger": "request_prepare"`
- `"trigger": "session_fork"`
- `"trigger": ["session_create", "request_prepare"]`
- `"trigger": "my_future_custom_lifecycle"`

The meaning of common triggers is:

- `session_list`: the application is building shared session-list summary data
- `session_create`: a new session has just been created and may need initial
  session-owned settings
- `session_save_prepare`: a session is about to be persisted and may need
  final metadata adjustments
- `request_prepare`: an existing session is about to be used for a request and
  may need repair or fallback initialization
- `request_complete`: a request completed successfully and post-request session
  metadata may need to be updated
- `response_finalize`: core-owned post-finalization stage where in-flight final
  messages and retained native history may still be adjusted before the final
  payload is emitted
- `request_error`: a request failed and failure-related session state may need
  to be recorded
- `session_fork`: a new forked session has been created from an existing
  session and may need fork-aware adjustments
- `agent_switch_prepare`: a session is about to switch from one agent to
  another and may need pre-switch adjustments
- `agent_switch_complete`: a session has completed an agent switch and may need
  post-switch adjustments
- `session_settings_changed`: application-owned per-session settings have
  changed and plugins may need to re-apply session-scoped derived state
- `server_settings_changed`: application-owned server settings have changed and
  application plugins may need to apply process-wide behavior
- `session_delete_prepare`: a session is about to be deleted and plugins may
  need to record or clean up related state

Actions without a `trigger` are manual actions.

## Non-mutating session actions

Feature and provider-extension session actions use the mutating session path
by default. An inspection or display-only action may declare:

```json
{
  "id": "inspect_effective_state",
  "label": "Inspect effective state",
  "inputs": {},
  "mutates_session": false
}
```

A non-mutating action may return a direct `display` without returning
`native_messages` or `session_metadata`. The application does not rebuild,
save, touch the modification time, or report the session as updated. The
action still receives the resolved config, session, native history, request
context, and request runtime.

Do not declare an action non-mutating if it changes native history, session
metadata, or reports session mutations. Omission of `mutates_session` preserves
the existing mutating behavior.

## `session_list` trigger contract

`session_list` is a cold-path application trigger owned by
`AgentApplication`. HTTP and terminal adapters do not discover or execute these
actions independently.

The application runs every matching application-plugin action once per stored
session, in application plugin configuration order and action declaration
order. It supplies only inputs the action declares:

| Declared input | Supplied value |
| --- | --- |
| `session_id` | Opaque session ID |
| `session_summary` | Summary accumulated so far, including fields from earlier actions |
| `session` | Loaded live `Session` object |

Execution context includes:

```python
{
    "lifecycle": "session_list",
    "trigger_source": "application",
    "session_id": session_id,
}
```

An action that does not need full history should omit `session`; this lets the
application avoid treating a failed/malformed load as a prerequisite for that
action. List-trigger actions should be deterministic for a stored session and
should not mutate it as a side effect.

### Contributed fields

An action can add JSON-serializable fields:

```python
return {
    "session_list_fields": {
        "message_count": len(session.messages),
        "status_rank": 20,
    }
}
```

Contributed fields become top-level members of the shared summary and are
available to later trigger actions, `session_list_field` paths, order
specifications, and filters. The application reserves:

- `session_id`
- `modified`
- `preview`
- `metadata`
- `presentation`

Invalid keys, reserved-key writes, and non-JSON-serializable values are
reported and ignored individually.

A list trigger can also translate a stored machine value into presentation or
search text without changing session metadata:

```python
status = summary.get("metadata", {}).get("status", "todo")
labels = {
    "todo": "To do",
    "in_progress": "In progress",
    "blocked": "Blocked",
    "done": "Done",
}
return {
    "session_list_fields": {
        "session_status_label": labels.get(status, "To do"),
    }
}
```

The resulting field can feed a `role: "meta"` session-list field while the
original `metadata.status` remains authoritative for actions and filters.

### Contributed ordering

An action can contribute one order object or an ordered list:

```python
return {
    "session_list_fields": {
        "status_rank": 20,
        "last_updated_sort_key": -summary["modified"],
    },
    "session_list_order": [
        {
            "key": "status_rank",
            "direction": "asc",
            "fallback": 100,
            "priority": 20,
        },
        {
            "key": "last_updated_sort_key",
            "direction": "asc",
            "fallback": 0,
            "priority": 30,
        },
    ],
}
```

Each specification has:

| Field | Contract |
| --- | --- |
| `key` | Required non-empty dotted path into the shared summary |
| `direction` | Required `asc` or `desc` |
| `fallback` | Required when the key is missing from any summary |
| `priority` | Optional integer, default `100`; lower values run first |

Specifications compose by:

1. ascending `priority`;
2. application plugin configuration order;
3. action and specification declaration order within the plugin.

Each key keeps its own direction. Modification time descending is applied first
as the stable final tie-break and is also the complete fallback when no valid
plugin order remains. There is no built-in pinned-first fallback.

Missing is distinct from explicit `null`, false, zero, and an empty string.
Values for one order key must be mutually comparable scalar values. Invalid
directions, priorities, missing fallbacks, conflicting declarations, or
non-sortable/incompatible values invalidate only that specification.

Ordering always occurs before filtering. Filtering preserves that order, and a
query `limit` is applied after both.

The built-in `session-ordering-buckets-app` uses this contract to place its
`recent_archived_rank` at priority 5. With `session-archive-app` enabled, that
rank moves archived summaries updated within the last 60 days below
non-archived summaries. It reads
`application.session_archived_metadata_key`; older archived summaries are
exempt and keep the subsequent recency, pin, and last-updated ordering.

### Failure isolation and diagnostics

A failed list-trigger action affects only that action for that session. Other
actions and summaries remain available. Invalid contributed fields, UI fields,
and order specifications are likewise isolated. `AgentApplication` exposes
structured diagnostics from the latest list query, while HTTP continues to
return the stable `{"sessions": [...]}` response shape.

## Standard built-in lifecycle set

Even though lifecycle names are dynamic, `AgentApplication` provides a
standard built-in set for its mutating flows.

The standard built-in lifecycles are:

- `session_create`
- `session_save_prepare`
- `request_prepare`
- `request_complete`
- `request_error`
- `session_fork`
- `agent_switch_prepare`
- `agent_switch_complete`
- `session_settings_changed`
- `server_settings_changed`
- `session_delete_prepare`

Lifecycle meanings:

- `session_create`: run after a brand-new session is created and before first
  persistence
- `session_save_prepare`: run immediately before a session is saved to the
  session store; intended for final metadata normalization or session-owned
  bookkeeping that must happen before persistence
- `request_prepare`: run after effective config resolution and before the tool
  loop/provider request begins
- `request_complete`: run after a successful request has produced its final
  session and before the application completes post-request persistence
- `request_error`: run after a request fails and before the application exits
  the request flow; intended for recording failure metadata or clearing
  partially initialized values
- `session_fork`: run on the new forked session after the fork is created;
  fork-specific context may include the serialized source session
- `agent_switch_prepare`: run when a session is about to switch from one agent
  to another
- `agent_switch_complete`: run after the session has been updated to its new
  agent assignment
- `session_settings_changed`: run after application-owned session settings
  have changed; context includes the previous settings, updated settings,
  changed keys, and source
- `server_settings_changed`: run after application-owned server settings have
  changed; context includes the previous settings, updated settings, changed
  keys, and source
- `session_delete_prepare`: run before a session is deleted; intended for any
  last-chance session-scoped cleanup or bookkeeping

The built-in lifecycle set is the standard vocabulary used by
`AgentApplication`. It intentionally excludes load/read paths, because built-in
lifecycle actions are allowed to be mutating and may be long-running. Callers
may still use additional lifecycle names when they need application-specific
behavior.

## Lifecycle timing and ownership

The standard lifecycles are triggered at these points:

- `session_create`: owned by `AgentApplication` session creation flows such as
  `create_session_ephemeral(...)` and any persisted create flow built on top of
  it
- `session_save_prepare`: owned by `AgentApplication.save_session(...)`
- `request_prepare`: owned by `AgentApplication.send_request(...)`, after
  effective config resolution and before the tool loop/provider request starts
- `request_complete`: owned by `AgentApplication.send_request(...)`, after the
  request finishes successfully and a final session exists
- `response_finalize`: owned by `AgentCore` request execution, after provider /
  feature native finalization and native-to-core conversion, but before final
  messages are emitted or appended to the session
- `request_error`: owned by `AgentApplication.send_request(...)`, when request
  execution raises or returns a terminal error path
- `session_fork`: owned by session-fork flows in the application layer and runs
  on the new forked session
- `agent_switch_prepare`: owned by agent-switch flows before the new agent id
  is written to the session
- `agent_switch_complete`: owned by agent-switch flows after the new agent id
  has been written
- `session_settings_changed`: owned by `AgentApplication` session settings
  helpers such as `patch_session_settings(...)` and
  `delete_session_setting(...)`
- `server_settings_changed`: owned by `AgentApplication` server settings
  helpers such as `patch_server_settings(...)` and
  `delete_server_setting(...)`; it can run without a session
- `session_delete_prepare`: owned by application-layer delete-session flows

`AgentCore` does not decide when any of these lifecycles happen. It only
executes matching core-side actions for the lifecycle name that
`AgentApplication` passes in.

Exception:

- `response_finalize` is a core-owned lifecycle executed directly by
  `AgentCore` during request finalization so core-side plugins can still mutate
  the current turn's `final_messages` before they are returned.

## Dispatcher ownership

Lifecycle dispatch belongs to `AgentApplication`.

Reasons:

- `AgentApplication` owns session creation and request entrypoints.
- `AgentApplication` owns session persistence, locks, checkpoints, and event
  publication.
- `AgentApplication` can coordinate both application plugins and core-side
  plugins from one place.

`AgentApplication` also provides a generic lifecycle-dispatch entry point that
accepts:

- a lifecycle name
- the current session and effective config for session-scoped lifecycles
- optional extra context

It also provides an application-scoped lifecycle path for lifecycles that do
not have a current session, such as `server_settings_changed`. This is what
allows future application implementations to run arbitrary lifecycle names
beyond the built-in set.

The intended flow is:

1. `AgentApplication` decides that a lifecycle trigger should run.
2. `AgentApplication` executes matching application-plugin actions.
3. For session-scoped lifecycles, `AgentApplication` calls a high-level
   `AgentCore` helper for matching provider-extension or feature actions.
4. For session-scoped lifecycles, `AgentApplication` persists any changed
   session through the normal application-layer save/checkpoint path.

For session-scoped lifecycles in the standard built-in set, the generic flow is:

1. determine the lifecycle name and effective config
2. build serializable execution context
3. run matching application-plugin actions
4. run matching core-side actions through `AgentCore`
5. merge resulting session mutations
6. continue the owning application operation such as save, request, fork, or
   agent switch

For application-scoped lifecycles such as `server_settings_changed`, the flow
does not include a session or a core-side pass:

1. determine the lifecycle name
2. build serializable application context
3. run matching application-plugin actions
4. continue the owning application operation such as applying server settings
   or replaying persisted settings on startup

For `response_finalize`, the flow is slightly different:

1. `AgentCore` finishes provider / feature native `finalize(...)`
2. `AgentCore` converts the current turn's native finals back into core
   `final_messages`
3. `AgentCore` runs matching core-side actions with `trigger: "response_finalize"`
4. actions may return replacement `final_messages`, replacement
   `native_messages`, and `session_metadata`
5. `AgentCore` emits / returns the updated `final_messages` and stores the
   updated native history

## Execution context

Lifecycle-triggered action execution may include extra context in addition to
normal action params.

This context exists so callers can provide lifecycle-specific information such
as the original session used to create a fork.

Requirements:

- extra context must be serializable
- plugin code must treat extra context as language-neutral data
- multi-language plugin implementations must not depend on Python object
  identity or Python-only types in this context channel

Recommended examples:

- `{"lifecycle": "request_prepare"}`
- `{"lifecycle": "session_fork", "original_session": {...}}`
- `{"lifecycle": "agent_switch_prepare", "previous_agent_id": "a", "next_agent_id": "b"}`
- `{"lifecycle": "request_error", "error": {"type": "RuntimeError", "message": "tool loop failed"}}`
- `{"lifecycle": "session_delete_prepare", "delete_reason": "user_request"}`
- `{"lifecycle": "session_settings_changed", "scope": "session", "changed_keys": ["temperature"]}`
- `{"lifecycle": "server_settings_changed", "scope": "server", "source": "api"}`

When a fork lifecycle is triggered, the original session is passed in a
serialized form such as the result of `Session.to_dict()`, not as a live
Python `Session` object.

### Reserved context keys

The runtime may populate these commonly used keys in `context`:

- `lifecycle`: the lifecycle name being executed
- `trigger_source`: string describing who initiated execution, such as
  `application`, `server`, or `manual`
- `original_session`: serialized source session for fork-style flows
- `previous_agent_id`: source agent id for agent-switch flows
- `next_agent_id`: destination agent id for agent-switch flows
- `error`: serialized error payload for failure lifecycles
- `scope`: lifecycle scope such as `session` or `server`
- `old_settings`: previous settings map for settings-change lifecycles
- `new_settings`: updated settings map for settings-change lifecycles
- `changed_keys`: list of setting keys that changed
- `source`: serializable string describing the change source, such as `api`,
  `startup`, or `bridge_sync`

Plugins may also use additional serializable context keys supplied by the
caller.

Reserved context keys are owned by the core/application builders. Caller
context is additive only. If caller-provided context reuses a reserved key,
the builder keeps the owned value and emits a warning instead of silently
overriding it.

### Layered context for feature/extension plugins

Feature plugins and provider extensions receive **layered context** that provides different capabilities depending on where the action is triggered. This allows plugins to access enhanced capabilities when available while gracefully degrading when running in core-only mode.

#### Layer 1: Core-level context (always present)

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
| `request_context` | `dict` | Request-initialized plugin context for action-style flows |
| `request_runtime` | `dict` | Request runtime helpers (`provider`, `features`) for action-style flows |

#### Layer 2: Application-level context (when called from AgentApplication)

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
    "session_asset_store": self._session_asset_store,  # Optional
}
```

| Key | Type | Description |
|-----|------|-------------|
| `app` / `application` | `AgentApplication` | Application instance for enhanced capabilities |
| `base_config` | `dict` | Full application configuration (all agents) |
| `session_asset_store` | `SessionAssetStore` | File attachment store (optional) |

For application-scoped lifecycle actions that do not have a session, such as
`server_settings_changed`, application-plugin actions receive the application
keys (`app`, `application`, `base_config`, runtime stores, and supplied extra
context) but no `session` or `session_id`.

When application and core both contribute context, ownership is explicit:
application contributes application-owned keys such as `app`,
`application`, `base_config`, and `session_asset_store`, while the core
contributes core-owned keys such as `core`, `config`, `session`,
`trigger_source`, `request_context`, and `request_runtime`.

#### Layer 3: Terminal/Server-level context (implementation-specific)

Terminal or HTTP server implementations may add additional context keys:

```python
# TerminalApplication may add:
context["terminal"] = self

# HTTP server may add:
context["server"] = self
context["request_id"] = request_id
```

These keys are implementation-specific and should be documented by the respective applications.

#### Checking for capabilities

Feature and extension plugins should check for capabilities before using them:

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

**Note on config resolution:** The `config` key is the resolved request configuration for the current agent. When called from `AgentApplication`, `base_config` contains the full flattened agent configuration (from `build_agent_config()`). For agent-level settings like `compaction`, always use `base_config` when available, falling back to `config` for core-only calls.

#### Context flow diagram

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

## Application plugin contract

Application plugins keep the current action method names and semantics.

```python
class ApplicationPlugin(Protocol):
    name: str
    version: str

    def init(self, app_config: dict[str, Any]) -> dict[str, Any]:
        ...

    def get_actions(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        ...

    def execute_action(
        self,
        app: "AgentApplication",
        action_id: str,
        params: dict[str, Any],
        context: dict[str, Any] | None,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        ...
```

Application-plugin action definitions may be manual or lifecycle-triggered.

Example:

```python
{
    "id": "ensure_session_defaults",
    "label": "Ensure session defaults",
    "inputs": {
        "session_id": {"type": "string", "required": True},
    },
    "trigger": ["session_create", "request_prepare"],
}
```

`params` remains the plugin-defined action input surface.

`context` is execution context supplied by the caller, especially for
lifecycle-triggered execution. It may contain arbitrary serializable keys.

Application-plugin action results remain application-level. They may include:

- `mutations` for created, updated, or deleted sessions
- `ui_effects` such as reload requests or navigation hints
- additional app-facing payloads used by HTTP, terminal, or mobile flows

#### Shared UI-effect boundary

The shared refresh fields are:

- `reload_session_ids`;
- `reload_sessions_list`;
- `reload_application_actions`.

These fields have the same meaning for application-action responses, session
notifications, and application notifications. They invalidate data only on
the owning connection. A session reload refreshes a mounted/open session and
otherwise invalidates cached state; it does not open the session.

For notification-delivered refresh effects, frontend invalidation remains
pending until authoritative data reloads successfully. This allows inactive
or later-mounted cache consumers to catch up without requiring the producer to
repeat the notification. Action responses remain one-shot results in the
initiating action context and do not acquire notification revision or replay
semantics.

`navigate_to_session_id` remains action-response-only. Action execution has a
direct user gesture and a concrete navigation context. Asynchronous
notification delivery must not move focus or switch sessions. A notification
follow-up can still invoke an action that returns navigation after the user
clicks it.

Action `mutations` also remain action-only. Frontend policy may derive
additional behavior from an action's created, updated, or deleted session IDs,
including optional navigation to a newly created session or session-list
refresh. Notifications do not carry mutations and never derive implicit
effects; their `ui_effects` must be explicit.

Unknown JSON-compatible UI-effect fields remain allowed for forward
compatibility. Frontends ignore fields they do not implement.

When application actions are lifecycle-triggered, they still use the same
contract. The difference is only how they were selected for execution.

This is different from core-side plugin actions, which stay single-session
oriented.

## Provider extension contract

Provider extensions use the same action naming pattern for this concept.

```python
class ProviderExtensionPlugin(BasePlugin, Protocol):
    name: str
    version: str

    def init(self, config: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        ...

    def get_actions(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        ...

    def execute_action(
        self,
        action_id: str,
        session: Session,
        native_messages: list[dict[str, Any]],
        params: dict[str, Any],
        context: dict[str, Any] | None,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        ...
```

The important difference is the result contract.

Provider-extension actions stay single-session oriented. They do not return
application-level UI effects or navigation instructions. Instead, they follow
the existing core-side mutation style:

- return replacement `native_messages` when the visible message list should be
  rebuilt from provider-native history
- return `session_metadata` when session metadata should be patched

Because `session_metadata` can contain `"overrides"`, provider-extension
actions can initialize or repair session-owned settings without becoming
application plugins.

## Actions placed in session settings

A `session_action` may use the `session_settings` rich-UI placement when the
operation belongs next to a related config field rather than in the ordinary
session header or composer:

```python
{
    "ui_type": "session_action",
    "id": "regenerate_prompt_cache_key",
    "label": "Regenerate cache key",
    "icon": "refresh-cw",
    "action_id": "regenerate_prompt_cache_key",
    "action_owner": "provider_extension",
    "param_map": {
        "session_id": "$session.session_id",
    },
    "rich_ui": {
        "kind": "button",
        "placements": ["session_settings"],
        "anchor_key": "prompt_cache_key",
        "position": "after",
    },
}
```

`anchor_key` names the related config element. A frontend that supports the
placement renders the button after that field. If the field is unavailable,
the action remains visible in a general settings-actions section. Actions
without an explicit placement retain the existing session-header default.

Settings placement does not change execution semantics. Application,
feature, and provider-extension owners continue to use the same definitions,
input validation, action endpoints, mutation results, UI effects, and
idempotency behavior.

An action may also request a user-mediated client input:

```python
{
    "client_input": {
        "kind": "directory",
        "input_name": "workspace_grant_id",
        "access": "read_write",
        "persistent": True,
    },
    "param_map": {
        "grant_id": "$client.workspace_grant_id",
    },
}
```

For persistent directory input, the client opens its native directory picker
and stores the platform permission. The action receives only the opaque grant
identifier. Raw bookmarks and provider filesystem paths must not be placed in
session metadata or action parameters. Canceling client input skips action
execution.

`context` follows the same rule here: it is caller-provided execution metadata
and must be serializable.

## Feature plugin contract

Features that participate in triggered session actions follow the same
conceptual pattern as provider extensions: `get_actions(...)` plus
`execute_action(...)`, with single-session mutation results rather than
application-level UI effects.

## Core-side session mutation model

For provider extensions and similar non-application plugins, the core-side
action result is intentionally narrow.

Expected mutation surfaces:

- `native_messages`
- `session_metadata`

Expected outcomes:

- visible messages may change when the core rebuilds the transcript from
  returned `native_messages`
- session-owned settings may change when `session_metadata` patches
  `session.metadata["overrides"]`

The goal is to keep core-side actions limited to one session. They do not own
application concerns such as reload-all, switch-session, or multi-session UI
coordination.

## Lifecycle action ordering

Actions are executed in the same stable plugin/action ordering used elsewhere
in the runtime.

Practical rules:

- application-plugin lifecycle actions run in application-plugin registration
  order
- core-side lifecycle actions run in the resolved provider/plugin order for the
  effective config
- for a single plugin, actions run in the order returned by `get_actions(...)`
- later actions observe session changes produced by earlier actions in the same
  lifecycle run

Plugins should therefore make lifecycle actions idempotent when possible.

## Lifecycle examples

### Create-time initialization

A provider extension can ensure a session-owned setting exists for a new
session:

```python
{
    "id": "ensure_prompt_cache_key",
    "label": "Ensure prompt cache key",
    "inputs": {},
    "trigger": "session_create",
}
```

Its `execute_action(...)` may return:

```python
{
    "native_messages": native_messages,
    "session_metadata": {
        "overrides": {
            "prompt_cache_key": "generated-key"
        }
    },
}
```

### Request-time repair

The same action can also be triggered for older sessions that predate the
setting:

```python
{
    "id": "ensure_prompt_cache_key",
    "label": "Ensure prompt cache key",
    "inputs": {},
    "trigger": ["session_create", "request_prepare"],
}
```

`AgentApplication` is responsible for deciding that `request_prepare`
run before the request/tool loop begins and for persisting any resulting
session change.

### Save-time normalization

Plugins can normalize session metadata before persistence:

```python
{
    "id": "normalize_before_save",
    "label": "Normalize before save",
    "inputs": {},
    "trigger": "session_save_prepare",
}
```

### Request completion and error handling

Plugins can react after request completion or failure:

```python
{
    "id": "record_request_success",
    "label": "Record request success",
    "inputs": {},
    "trigger": "request_complete",
}
```

```python
{
    "id": "record_request_failure",
    "label": "Record request failure",
    "inputs": {},
    "trigger": "request_error",
}
```

### Fork-aware initialization

A plugin can also react to a newly created fork:

```python
{
    "id": "adjust_fork_settings",
    "label": "Adjust fork settings",
    "inputs": {},
    "trigger": "session_fork",
}
```

The caller may provide extra context like:

```python
{
    "lifecycle": "session_fork",
    "original_session": {
        "session_id": "session-123",
        "messages": [],
        "metadata": {"agent_id": "default"},
    },
}
```

That lets the action make fork-aware decisions without relying on Python-only
objects.

### Agent switch handling

Plugins can react before and after an agent switch:

```python
{
    "id": "prepare_for_agent_switch",
    "label": "Prepare for agent switch",
    "inputs": {},
    "trigger": "agent_switch_prepare",
}
```

```python
{
    "id": "finalize_agent_switch",
    "label": "Finalize agent switch",
    "inputs": {},
    "trigger": "agent_switch_complete",
}
```

Context commonly includes:

```python
{
    "lifecycle": "agent_switch_prepare",
    "previous_agent_id": "default",
    "next_agent_id": "research",
}
```

### Delete-time cleanup

Plugins can run one final action before deletion:

```python
{
    "id": "cleanup_before_delete",
    "label": "Cleanup before delete",
    "inputs": {},
    "trigger": "session_delete_prepare",
}
```

## Design guidance

Use an application plugin when the action needs application-level powers such
as:

- creating or deleting sessions
- coordinating multiple sessions
- returning UI navigation or reload instructions
- integrating with server-only or frontend-only flows

Use a provider extension or similar core-side plugin when the action is owned
by one session and one provider/config context, especially when it needs to:

- mutate provider-native history
- patch session metadata owned by that provider feature
- ensure or repair session-owned settings such as values stored under
  `session.metadata["overrides"]`

## Relation to existing `session_list` actions

Application-plugin actions with `trigger: "session_list"` run through the
dedicated application session-list service described above. They are not
server-interpreted and are not core/provider lifecycle actions.

Other dynamic lifecycle triggers continue through shared application/core
orchestration. `session_list` is distinct because its result contributes to a
read-only multi-session query rather than mutating one current session.

## Core-side lifecycle vocabulary

`AgentCore` supports execution for any lifecycle name that
`AgentApplication` passes to it.

The standard vocabulary it receives includes:

- `session_create`
- `session_save_prepare`
- `request_prepare`
- `request_complete`
- `request_error`
- `session_fork`
- `agent_switch_prepare`
- `agent_switch_complete`
- `session_delete_prepare`

`AgentCore` does not decide when these lifecycles happen. It only executes
matching core-side actions for the given lifecycle name, session, config, and
serializable execution context.