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
- `core/python/agent_core/types.py`
- `core/python/agent_core/core.py`
- `application/python/agent_terminal_app/server.py`

## Overview

After the update, actions will follow these rules:

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
- `actions`: optional list of generic follow-up actions

Guidance:

- keep `display` user-oriented and safe to render directly
- keep machine-readable fields alongside it when frontend logic or tests still
  need structured state
- do not overload top-level `message` keys for successful rich content when
  `display` is more appropriate
- keep follow-up actions intentionally narrow and generic; current supported
  shapes are `open_url`, `copy_text`, and `run_action`

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

- `session_list`: the application/server is building session-list summary data
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
- `session_delete_prepare`: a session is about to be deleted and plugins may
  need to record or clean up related state

Actions without a `trigger` are manual actions.

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
- the current session
- the effective config
- optional extra context

This is what allows future application implementations to run arbitrary
lifecycle names beyond the built-in set.

The intended flow is:

1. `AgentApplication` decides that a lifecycle trigger should run.
2. `AgentApplication` executes matching application-plugin actions.
3. `AgentApplication` calls a high-level `AgentCore` helper for matching
   provider-extension or feature actions.
4. `AgentApplication` persists any changed session through the normal
   application-layer save/checkpoint path.

For the standard built-in set, the generic flow is:

1. determine the lifecycle name and effective config
2. build serializable execution context
3. run matching application-plugin actions
4. run matching core-side actions through `AgentCore`
5. merge resulting session mutations
6. continue the owning application operation such as save, request, fork, or
   agent switch

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

Plugins may also use additional serializable context keys supplied by the
caller.

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

The current code already has one server-interpreted triggered-action pattern:
application-plugin actions with `trigger: "session_list"`.

The runtime generalizes that idea so lifecycle triggers are no longer a
server-only special case and can also be used by non-application plugins
through shared application/core orchestration.

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