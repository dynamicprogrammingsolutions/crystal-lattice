Application-Level Plugins, Actions, and Session List Plan
=========================================================

This document describes a new **application-level plugin system**, a
structured **action model**, and **UI schema** extensions for
session-level features. It is designed so that someone can implement it
from scratch in a fresh session without seeing the original
conversation.

The goals are:

- Introduce a new **application-level plugin type** that operates on
  `AgentApplication` (sessions, requests, storage), distinct from core
  provider/feature/tool plugins.
- Define **actions** as pure logical operations (id + typed inputs),
  independent from how they are triggered in UIs.
- Describe **UI schema elements** that:
  - Invoke actions (buttons/menus in session views, session lists,
    message menus).
  - Define **session-list display fields** (title, subtitles, meta
    lines), analogous to current status bar/message footer elements.
- Add three application-level plugins built on this foundation:
  - **Copy/fork/delete** plugin (session & message level).
  - **Summarize range** plugin.
  - **Generate title** plugin.
- Expose a **single, simple HTTP endpoint** for executing actions:
  `POST /actions` with `plugin`, `action_id`, and an `inputs` object.
- Ensure that no new API responses embed entire session objects; only
  minimal identifiers or summaries are returned.


1. Existing Architecture Overview
---------------------------------

High-level context; implementation will rely on these components.

- **Core SDK – `agent_core`**
  - `core/python/agent_core/core.py`
    - `AgentCore` – core session/message engine and plugin integration.
  - `core/python/agent_core/types.py`
    - Core data types (`Message`, `Session`) and plugin protocols:
      `ProviderPlugin`, `ProviderExtensionPlugin`, `FeaturePlugin`,
      `ToolPlugin`.
  - `core/python/agent_core/plugin/*.py`
    - Wrappers for provider/feature/tool plugins.

- **Application layer – `agent_app`**
  - `core/python/agent_app/application_future.py`
    - `AgentApplication` – loads config, plugins, builds cores per
      agent/session, manages event store, exposes typed `send_request`.
  - `core/python/agent_app/config.py`
    - Config loading and placeholder resolution.
    - `load_plugins` for core plugins.
  - `core/python/agent_app/sessions.py`
    - `FilesystemSessionStore` – stores `Session` objects as JSON.
  - `core/python/agent_app/events.py`
    - Event store abstraction and `InMemoryEventStore`.

- **Terminal & HTTP app – `agent_terminal_app`**
  - `application/python/agent_terminal_app/terminal_app.py`
    - `TerminalApplication` – terminal-facing app API built on
      `AgentApplication` (create/delete/fork sessions, delete/modify
      messages, send requests, list events, etc.).
  - `application/python/agent_terminal_app/server.py`
    - FastAPI server exposing JSON endpoints for sessions, messages,
      overrides, send, events, etc.
    - Implements `/sessions`, `/sessions/{id}/messages`,
      `/sessions/{id}/fork`, delete-message endpoints, etc.
  - `application/python/agent_terminal_app/event_rendering.py`
    - Terminal rendering of events (assistant, tools, reasoning).

- **Mobile app – React Native client**
  - `mobile/crystal-lattice-control-rn/src/api.ts`
    - Typed wrappers for HTTP endpoints: list/create sessions, list
      messages, append, send, agents, fork, delete messages, etc.
  - `mobile/crystal-lattice-control-rn/src/SessionsScreen.tsx`
    - Renders the session list using `/sessions` response
      (`SessionSummary {session_id, modified, preview}`).


2. Files to Read Before Implementation
--------------------------------------

Before implementing this plan, read/sketch these files to understand
the current behavior and patterns:

- Root project docs
  - `AGENTS.md`
  - `ARCHITECTURE.md`
  - `TYPES_AND_PROTOCOLS.md`
  - `docs/plugins/development.md`

- Core SDK
  - `core/python/agent_core/types.py`
    - `BasePlugin`, `ProviderPlugin`, `ProviderExtensionPlugin`,
      `FeaturePlugin`, `ToolPlugin`, `Message`, `Session`.
  - `core/python/agent_core/core.py`
    - Plugin registration & config/ UI schema aggregation.

- Application layer
  - `core/python/agent_app/application_future.py`
    - `AgentApplication` construction, plugin loading, agent configs,
      session store, send_request, event compaction.
  - `core/python/agent_app/config.py`
    - `load_raw_config`, `resolve_placeholders`, `build_agent_config`,
      `resolve_request_config`, `load_plugins`.

- Terminal & HTTP app
  - `application/python/agent_terminal_app/AGENTS.md`
  - `application/python/agent_terminal_app/server.py`
    - Existing endpoints for sessions, messages, fork, delete, send,
      events, and their response shapes.
  - `application/python/agent_terminal_app/terminal_app.py`
    - Session/message operations (`start_new_session`, `fork_session`,
      `delete_messages*`, `modify_message`, `send_request`,
      `list_events`).
  - `application/python/tests` (especially server and terminal tests).

- Mobile client
  - `mobile/crystal-lattice-control-rn/AGENTS.md`
  - `mobile/crystal-lattice-control-rn/src/api.ts`
  - `mobile/crystal-lattice-control-rn/src/SessionsScreen.tsx`


3. New Application-Level Plugin System
--------------------------------------

We introduce a new **ApplicationPlugin** type that:

- Operates at the `AgentApplication` level.
- Defines **logical actions** via `get_actions` (no UI knowledge).
- Contributes **UI schema elements** via `get_ui_elements` for:
  - Action triggers (buttons/menus).
  - Session-list display fields.

### 3.1. ApplicationPlugin Protocol

Add a new protocol in a dedicated module, e.g.
`core/python/agent_app/app_plugins.py`:

- Attributes:
  - `name: str`
  - `version: str`

- Methods:

  ```python
  class ApplicationPlugin(Protocol):
      name: str
      version: str

      def get_config_schema(self) -> Dict[str, Any]: ...

      def get_ui_elements(self) -> List[Dict[str, Any]]: ...

      def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
          """Initialize plugin with resolved application config.

          Return opaque state dict stored by the wrapper.
          """

      def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
          """Return logical action definitions for this plugin."""

      def execute_action(
          self,
          app: "AgentApplication",
          action_id: str,
          params: Dict[str, Any],
          state: Dict[str, Any],
      ) -> Dict[str, Any]:
          """Execute action with validated params."""
  ```

Notes:

- `get_actions` and `execute_action` operate only on **typed params**;
  they are UI-agnostic.
- `get_ui_elements` will be used to emit **action UI elements** and
  **session-list field elements** (see section 5).


### 3.2. Plugin Loading & Config

Extend JSON config format to declare application plugins separately
from core provider/feature/tool plugins, and to keep **all
application-level config keys flat under the `application` section**
(no per-plugin nested `plugin_config` block). This mirrors how core
plugins see config under an agent (all plugin-related keys live
directly under the agent config), and allows application plugins to
share config keys.

Example snippet:

```json
{
  "providers": { ... },
  "plugins": { ... },          // existing core plugins
  "agents": { ... },           // agent configs, including models
  "application_plugins": [
    "plugins.session_actions_app.SessionActionsAppPlugin",
    "plugins.summarize_range_app.SummarizeRangeAppPlugin",
    "plugins.generate_title_app.GenerateTitleAppPlugin"
  ],
  "application": {
    "ui_theme": "light",

    // Example: keys used by SessionActionsAppPlugin
    "session_actions": { "allow_delete": true },

    // Example: keys used by SummarizeRangeAppPlugin
    "summarize_range": { "agent_id": "summarizer", "max_range_length": 50 },

    // Example: keys used by GenerateTitleAppPlugin
    "generate_title": { "agent_id": "title_generator", "max_messages": 50 },

    // Example of a shared key that multiple plugins may read
    "shared_title_defaults": { "max_words": 8 }
  }
}
```

- `application_plugins`: list of dotted class paths implementing
  `ApplicationPlugin`.
- `application` subtree: contains **all** application-level config,
  including config that individual plugins may care about. Plugins may
  also inspect other top-level sections (e.g. `agents`, `providers`)
  if needed.

Changes in `core/python/agent_app/config.py`:

- Add `load_application_plugins(plugin_paths: Iterable[str])` using the
  existing `_import_string` helper.
  - Returns `(List[type[Any]], List[Dict[str, Any]]]` like
    `load_plugins` for core plugins.

Changes in `AgentApplication.__init__`:

- After resolving `_config`, load application plugins:

  - Read `app_plugin_paths = resolved_config.get("application_plugins") or []`.
  - Call `load_application_plugins`.
  - Store classes in `self._app_plugin_classes: List[type[Any]]`.
  - Append import/config errors to `self._config_errors`.


### 3.3. ApplicationPluginWrapper

Introduce a lightweight wrapper, similar to core plugin wrappers, e.g.
`agent_app/app_plugins.py`:

- `ApplicationPluginWrapper`:
  - Holds:
    - `plugin_class`
    - `plugin` instance
    - `state` dict returned by `init`
    - `id` computed like `AgentApplication._plugin_id_for_class`
  - Methods:
    - `init(app_config)` → sets `state`.
    - `get_actions()` → returns list from `plugin.get_actions(state)`.
    - `get_ui_elements()` → returns list from
      `plugin.get_ui_elements()` (no state needed).
    - `execute_action(app, action_id, params)` → calls
      `plugin.execute_action(app, action_id, params, state)`, updates
      stored state if plugin returns an updated state (optional design).

`AgentApplication.__init__` should:

- Construct wrappers for all app plugin classes.
- Call `init` on each with **full `resolved_config`**, so that
  application plugins can see:
  - The `application` subtree with any plugin-specific keys (e.g.
    `application["generate_title"]`).
  - The `agents` configuration (including models and provider
    options), so features like title generation can select a cheaper
    model or a dedicated agent.
- Store them in `self._app_plugins: Dict[str, ApplicationPluginWrapper]`
  keyed by stable `plugin_id`.


### 3.4. Application-Level Registries & Helpers

Add new helpers on `AgentApplication`:

- `list_application_plugins() -> List[Dict[str, Any]]`
  - Minimal metadata for all app plugins:
    - `id` (plugin id)
    - `class_path`
    - `class_name`
    - `name` (class-level attribute, if present)

- `get_application_actions() -> List[Dict[str, Any]]`
  - Iterate wrappers, call `get_actions()`, and attach `plugin` id to
    each action definition.
  - Used by the HTTP `GET /application/actions` endpoint.

- `get_application_ui_schema() -> List[Dict[str, Any]]`
  - Iterate wrappers, call `get_ui_elements()`, attach `plugin` id when
    absent, and flatten into a single list.
  - Used by the HTTP `GET /application/ui-schema` endpoint.

- `execute_application_action(plugin_id, action_id, params) -> Dict[str, Any]`
  - Look up wrapper by `plugin_id`.
  - Validate that `action_id` exists in the plugin’s `get_actions`.
  - Execute `wrapper.execute_action(self, action_id, params)`.
  - The HTTP layer will do input validation (section 6) before calling
    this helper.


4. Action Model (Logical Operations)
------------------------------------

Actions are **logical operations** with typed inputs. They are defined
entirely by plugins via `get_actions` and are independent from any
particular UI button or location.

### 4.1. Action Definition Schema

We standardize the shape returned by `ApplicationPlugin.get_actions`.

Types:

- Primitive input types: `"string" | "integer" | "number" |
  "boolean"`.

Input parameter descriptor:

- `ActionInputParam`:
  - `type`: primitive type.
  - `required` (bool, default `False`).
  - `default` (optional; used if input missing).
  - `description` (optional string).

Action definition:

- `ApplicationActionDefinition`:
  - `id`: action id within the plugin (`"copy_session"`,
    `"summarize_range"`, etc.).
  - `label` (optional; human-readable).
  - `description` (optional).
  - `inputs`: mapping from parameter name → `ActionInputParam`.

`AgentApplication.get_application_actions()` returns these with a
`plugin` field attached:

```json
{
  "actions": [
    {
      "plugin": "session_actions",
      "id": "copy_session",
      "label": "Copy session",
      "description": "Duplicate a session.",
      "inputs": {
        "session_id": {"type": "string", "required": true},
        "source": {"type": "string", "required": false, "default": "manual"}
      }
    }
  ]
}
```


5. UI Schema Extensions
------------------------

`ApplicationPlugin.get_ui_elements()` returns **UI schema elements** for
two purposes:

1. **Action UI elements** – buttons/menus that invoke actions.
2. **Session-list field elements** – how to render extra fields in the
   session list.

These are separate from the core’s `AgentCore.get_ui_schema()`; they
live at the application level.


### 5.1. Action UI Elements

Where an element appears:

- `ui_type` values for action elements:
  - `"session_action"` – action in a per-session view.
  - `"session_list_action"` – action on a session row in the list.
  - `"message_action"` – action associated with an individual message.

Dialog semantics:

- `dialog.kind`:
  - `"none"` – no extra input; direct execute.
  - `"confirm"` – yes/no confirmation.
  - `"form"` – collect additional inputs via a small form.

Dialog input fields:

- `DialogInputField`:
  - `name`: field name (often matches an action parameter).
  - `type`: `"string" | "number" | "integer" | "boolean"`.
  - `label`, `placeholder` (optional text for UI).
  - `default` (optional).
  - `required` (optional bool; default `False`).
  - `description` (optional string).

Dialog config:

- `DialogConfig`:
  - `kind`: `"none" | "confirm" | "form"`.
  - `title` (optional; for confirm/form dialogs).
  - `message` (optional; mostly for confirm dialogs).
  - `inputs` (optional) – list of `DialogInputField` for `kind="form"`.

Action UI element schema:

- `ActionUiElement` (subset of the union under
  `ApplicationUiElement`):
  - `ui_type`: one of `"session_action"`, `"session_list_action"`,
    `"message_action"`.
  - `plugin`: plugin id.
  - `id`: ui-element id (unique within this plugin).
  - Visual:
    - `label` (required): button/menu label.
    - `icon` (optional): symbolic icon id.
    - `order` (optional int): ordering hint.
  - Action wiring:
    - `action_id` (required): id of an action from this plugin.
    - `fixed_params` (optional): mapping of action parameter → fixed
      value (e.g. `"source": "session_list"`).
    - `param_map` (optional): mapping of action parameter → source
      expression string.
      - Sources are interpreted on the **client**:
        - `$session.*` – values from the session context (e.g.
          `$session.session_id`).
        - `$message.*` – values from the message context (e.g.
          `$message.index`).
        - `$dialog.*` – values from dialog inputs (e.g.
          `$dialog.start`).
    - `dialog` (optional): `DialogConfig`.
    - `metadata` (optional dict): free-form UI metadata.

Example: copy session from the session list:

```json
{
  "ui_type": "session_list_action",
  "plugin": "session_actions",
  "id": "copy_session_from_list",
  "label": "Copy",
  "icon": "copy",
  "order": 10,
  "action_id": "copy_session",
  "fixed_params": {"source": "session_list"},
  "param_map": {"session_id": "$session.session_id"},
  "dialog": {"kind": "none"}
}
```

The same `copy_session` action can be referenced by multiple UI
elements (e.g. in session view and message menu) with different
`ui_type`, `label`, `icon`, `fixed_params`, or `dialog`.


### 5.2. Session-List Field Elements

These control what is shown in the **session list**, similar in spirit
to `message_footer` and `status_bar` elements for messages.

We operate on a **session summary object** produced by `GET /sessions`
for each session, which will include:

- `session_id: str`
- `modified: float` (mtime)
- `preview: str` (first user message snippet)
- `metadata: Dict[str, Any]` (session metadata only; **no messages**)

Session-list field roles:

- `"title"` – preferred primary line for the session.
- `"subtitle"` – additional lines under the title.
- `"meta"` – small secondary info (e.g. timestamps, agent name).

Session-list field schema:

- `SessionListFieldElement` (also part of `ApplicationUiElement` union):
  - `ui_type`: `"session_list_field"`.
  - `plugin`: plugin id.
  - `key` (optional): stable identifier for the field.
  - `label` (optional): human label; UIs may or may not use it.
  - `description` (optional).
  - `role` (optional): `"title" | "subtitle" | "meta"`.
    - Default: `"meta"`.
  - `data` (required): dotted path into the session summary object, e.g.:
    - `"metadata.title"`
    - `"metadata.agent_id"`
    - `"preview"`
    - `"modified"`
  - `template` (optional string): simple template where `"{{data}}"`
    is replaced by the resolved value.
    - Default: just the stringified data.
  - `order` (optional int): ordering hint among same-role fields.
  - `metadata` (optional dict): free-form UI metadata.

Example: use `metadata.title` as the primary title line when present:

```json
{
  "ui_type": "session_list_field",
  "plugin": "generate_title",
  "key": "session_title",
  "role": "title",
  "data": "metadata.title",
  "template": "{{data}}",
  "order": 0
}
```

Example: show agent id as a subtitle:

```json
{
  "ui_type": "session_list_field",
  "plugin": "session_actions",
  "key": "session_agent",
  "role": "subtitle",
  "data": "metadata.agent_id",
  "template": "Agent: {{data}}",
  "order": 10
}
```

Example: show last modified time as meta info:

```json
{
  "ui_type": "session_list_field",
  "plugin": "builtin",
  "key": "session_modified",
  "role": "meta",
  "data": "modified",
  "template": "Updated: {{data}}",
  "order": 0
}
```

Frontends apply these field definitions **client-side** by resolving
`data` on the `/sessions` summary object per session, then selecting the
first non-empty `role="title"` field as title, accumulating subtitles
and meta lines ordered by `order`, and falling back to `preview` or
`Session <id>` when no title fields yield a value.


6. HTTP API Changes
--------------------

We add three new HTTP endpoints in the FastAPI server
`application/python/agent_terminal_app/server.py`.


### 6.1. `GET /application/actions`

Purpose:

- Expose all application-level action definitions from all
  `ApplicationPlugin`s.

Request:

- `GET /application/actions`
- Optional query: `plugin` (string) – filter by plugin id.

Response:

```json
{
  "actions": [
    {
      "plugin": "session_actions",
      "id": "copy_session",
      "label": "Copy session",
      "description": "Duplicate a session.",
      "inputs": {
        "session_id": {"type": "string", "required": true},
        "source": {"type": "string", "required": false, "default": "manual"}
      }
    }
  ]
}
```

The implementation pulls from
`AgentApplication.get_application_actions()` and optionally filters by
`plugin` query param.


### 6.2. `GET /application/ui-schema`

Purpose:

- Expose UI schema elements defined by application plugins, including:
  - Action UI elements.
  - Session-list field elements.

Request:

- `GET /application/ui-schema`
- Optional query: `plugin` (string) – filter by plugin id.

Response:

```json
{
  "elements": [
    /* ActionUiElement and SessionListFieldElement objects */
  ]
}
```

Implementation:

- Use `AgentApplication.get_application_ui_schema()` and filter.
  - Must normalize each entry to include `plugin` and `ui_type`.


### 6.3. `POST /actions`

Purpose:

- Execute any application-level action in a single, simple endpoint.

Request body schema:

- `ExecuteActionRequest`:
  - `plugin: string` – application plugin id.
  - `action_id: string` – action id defined by that plugin.
  - `inputs: Dict[str, Any]` – final parameter values.

Example:

```json
{
  "plugin": "session_actions",
  "action_id": "copy_session",
  "inputs": {
    "session_id": "abc123",
    "source": "session_list"
  }
}
```

Validation rules:

1. Confirm that `plugin` corresponds to a registered application
   plugin.
2. Confirm that `action_id` exists in that plugin’s action definitions.
3. Retrieve the action’s input schema from
   `AgentApplication.get_application_actions()`.
4. For each defined parameter `p`:
   - If `p` missing from `inputs`:
     - If `default` is defined, server may implicitly add
       `inputs[p] = default`.
     - Else if `required` is true → **validation error**.
   - If `p` present:
     - Check that the value matches the declared primitive `type`.
5. Optionally, reject extra keys in `inputs` that are not declared in
   the action schema (strict mode), or allow them and pass them along (a
   design choice; strict mode is recommended).

If validation fails, return an early error **without** calling the
plugin.

Response envelope:

- On success:

  ```json
  {
    "status": "ok",
    "plugin": "session_actions",
    "action_id": "copy_session",
    "result": {
      "created_session_ids": ["new-session-id"],
      "updated_session_ids": [],
      "deleted_session_ids": [],
      "selected_session_id": "new-session-id",
      "message": "Session copied successfully.",
      "extra": {}
    }
  }
  ```

  - `created_session_ids`, `updated_session_ids`, `deleted_session_ids`:
    - Optional lists of session ids whose state changed.
    - These **replace** any notion of returning entire sessions.
  - `selected_session_id`:
    - Optional hint telling the client which session to show after the
      action.
  - `message`:
    - Optional human-readable description.
  - `extra`:
    - Optional plugin-specific payload (for debugging or detailed UIs).

- On error:

  ```json
  {
    "status": "error",
    "plugin": "summarize_range",
    "action_id": "summarize_range",
    "error_type": "validation",
    "message": "Missing required parameter 'start'.",
    "details": {
      "missing_params": ["start"]
    }
  }
  ```

  - `error_type` values:
    - `"validation"` – schema mismatch or missing required inputs.
    - `"not_found"` – unknown plugin or unknown action.
    - `"plugin_error"` – plugin raised a handled/expected error.
    - `"internal"` – unexpected server error.

**Important constraint:**

- Do **not** include full session objects in `result` or error payloads
  for `POST /actions`. Only ids and minimal scalar metadata are
  allowed.
- Session details continue to be available via existing endpoints such
  as `GET /sessions`, `GET /sessions/{id}/messages`.


7. Session List Display Behavior
--------------------------------

We extend the `/sessions` endpoint and leverage `session_list_field`
UI elements.

### 7.1. `GET /sessions` Changes

Current behavior (`server.py`):

- Returns `{"sessions": [{"session_id", "modified", "preview"}, ...]}`.

New behavior:

- Add a `metadata` field per session, containing **only** the session
  metadata (not messages):

  ```json
  {
    "sessions": [
      {
        "session_id": "abc123",
        "modified": 1735670000.0,
        "preview": "First user message...",
        "metadata": {
          "agent_id": "default",
          "title": "Daily standup notes"
        }
      }
    ]
  }
  ```

Implementation details:

- When scanning session JSON files under the session root, parse only
  `messages` (for preview) and `metadata` keys; do **not** keep
  `messages` in memory.
- Build each summary dict with `session_id`, `modified`, `preview`, and
  `metadata`.

This gives session-list field elements a stable structure to refer to
via `data` paths such as `metadata.title`, `metadata.agent_id`,
`preview`, and `modified`.

### 7.2. Frontend Usage

- Mobile (`SessionsScreen.tsx`) and any other session list UIs can:
  - Continue using `session_id`, `modified`, `preview` as today.
  - Optionally adopt `session_list_field` elements to:
    - Prefer `metadata.title` as the main title when present.
    - Show additional lines such as the agent id or formatted
      timestamp.
- No changes are required to `/sessions` beyond the addition of
  `metadata` per session and any new UIs are opt-in.


8. Concrete Application Plugins
-------------------------------

We define three concrete application plugins using this system.


### 8.1. SessionActionsAppPlugin (Copy/Fork/Delete)

Location:

- Suggested: `core/python/plugins/session_actions_app.py`.

Config (read from the flat `application` section; for example this
plugin may expect an object under `application["session_actions"]`, or
it may look for individual scalar keys there as needed):

- Example:

  ```json
  {
    "allow_delete": true
  }
  ```

Actions (`get_actions`):

- `copy_session`
  - Inputs:
    - `session_id: string, required`.
    - `source: string, optional, default "manual"`.

- `fork_session_at`
  - Inputs:
    - `session_id: string, required`.
    - `index: integer, required` (Python-style index; negatives allowed).
    - `source: string, optional`.

- `delete_session`
  - Inputs:
    - `session_id: string, required`.
    - `source: string, optional`.

- `delete_messages`
  - Inputs (mirroring existing delete endpoint):
    - `session_id: string, required`.
    - `indices: array of integer, optional`.
    - `start: integer, optional`.
    - `end: integer, optional`.
    - `last: integer, optional`.
    - `source: string, optional`.

Action UI elements (`get_ui_elements`):

- Session-list copy:
  - `ui_type: "session_list_action"`, `action_id: "copy_session"`.
  - `param_map: {"session_id": "$session.session_id"}`.
  - `fixed_params: {"source": "session_list"}`.

- Session-view copy:
  - `ui_type: "session_action"`, same `action_id` but `source:
    "session_view"`.

- Message-view fork:
  - `ui_type: "message_action"`, `action_id: "fork_session_at"`.
  - `param_map: {"session_id": "$session.session_id", "index": "$message.index"}`.

- Session-view delete last N messages (form dialog):
  - `ui_type: "session_action"`, `action_id: "delete_messages"`.
  - `dialog.kind = "form"` with single integer field `last`.
  - `param_map: {"session_id": "$session.session_id", "last": "$dialog.last"}`.

Execution (`execute_action`):

- Use `AgentApplication.load_session(session_id)` to get
  `(core, base_config, session)`.
- For copy/fork actions:
  - Reuse existing patterns from `TerminalApplication.fork_session` and
    `/sessions/{id}/fork`:
    - Normalize indices.
    - Use `resolve_request_config` with per-session overrides from
      `session.metadata.get("overrides")`.
    - Call `core.fork_session` with a new UUID.
    - Save via `save_session`.
    - Publish `session_created` event and checkpoint.
    - Return `created_session_ids = [new_session_id]`,
      `selected_session_id = new_session_id`.

- For deletion actions:
  - Reuse logic from `TerminalApplication.delete_messages*` and
    `DELETE /sessions/{id}/messages`:
    - Compute `indices` from `indices` or `start/end` or `last`.
    - Normalize indices similarly to `_normalize_index` and
      `_normalize_slice_bounds`.
    - Use `core.slice_session` with computed indices.
    - Save updated session.
    - Publish `messages_deleted` event and checkpoint.
    - Return `updated_session_ids = [session_id]`.

No action result returns full sessions; callers reload sessions or
messages as needed.


### 8.2. SummarizeRangeAppPlugin

Location:

- Suggested: `core/python/plugins/summarize_range_app.py`.

Config (read from the flat `application` section; suggested patterns):

- For example, either:
  - `application["summarize_range"] = {"agent_id": "summarizer", "max_range_length": 50, "settings_overrides": {"model": "cheap-model", "reasoningEffort": "low"}}`, or
  - flat scalar keys such as `application["summarize_range_agent_id"]`,
    `application["summarize_range_max_range_length"]`, etc.

- Example:

  ```json
  {
    "agent_id": "summarizer",          // dedicated summarizer agent
    "prompt_template": "Summarize the following messages...",
    "max_range_length": 50              // safety limit on #messages
  }
  ```

Action (`get_actions`):

- `summarize_range`
  - Inputs:
    - `session_id: string, required`.
    - `start: integer, required`.
    - `end: integer, required`.
    - Optional configuration overrides, if supported, e.g.:
      - `settings_overrides: object, optional` – arbitrary mapping that
        can be merged into the request config (e.g. model or
        reasoningEffort overrides).

Action UI elements:

- Session-view “Summarize range”:
  - `ui_type: "session_action"`,
  - `action_id: "summarize_range"`.
  - `dialog.kind = "form"` with `start` and `end` integer fields.
  - `param_map` mapping to `$session.session_id`, `$dialog.start`,
    `$dialog.end`.

Execution algorithm:

1. Load original session via `load_session(session_id)` to obtain
   `(core_orig, base_config_orig, session_orig)`.
2. Normalize `start`/`end` using the same slice semantics as
   `_normalize_slice_bounds`.
3. Enforce `max_range_length` (if exceeded, return validation-like
   error from plugin or treat as `plugin_error` with appropriate
   `message`).
4. Determine which agent and settings to use for summarization:
   - If a dedicated `agent_id` is configured for summarize_range,
     switch to that agent; otherwise use the `agent_id` from
     `session_orig.metadata`.
   - To switch agents, use `AgentApplication.update_agent(agent_id,
     session_orig)` to obtain `(core_sum, base_config_sum, session_for_sum)`.
   - If `settings_overrides` are configured (e.g. alternate `model` or
     `reasoningEffort`), merge them into `base_config_sum` via
     `resolve_request_config` or an equivalent helper to form an
     ephemeral request config.
5. Build an **ephemeral copy** of the session for the summarization
   run, rather than creating a brand new empty session:
   - Start from `session_for_sum` and construct a new `Session` object
     in memory (not persisted) with:
     - `session_id` copied.
     - `metadata` taken from `session_for_sum.metadata`.
     - `messages` initially empty.
   - Populate `messages` for the ephemeral run as follows:
     - Always include the original first message if it is a `system`
       message (and optionally any leading `system` messages) so that
       the original system instructions are kept as the first
       message(s), even when `start > 0`.
     - Append the messages in the `[start:end]` range *as-is*
       (preserving roles and metadata), rather than flattening them
       into a single prompt string.
     - Append a final `user` message whose content is the
       `prompt_template` (or a prompt built from it) instructing the
       model to summarize the preceding conversation.
6. Use the summarizer core (`core_sum`) and the ephemeral session copy
   to call `send_request` (either by delegating to
   `AgentApplication.send_request` in a way that does not persist this
   copy, or by driving the core directly), and extract the final
   assistant message text as the summary.
7. Under a session lock for the original session:
   - Reload latest session and re-check bounds.
   - Construct a new `Session` where the `[start:end]` messages are
     replaced by a single summary message (role `assistant` or
     `system`, decided by design).
   - Save updated session and publish an event, e.g.
     `range_summarized` with indices and session id.
8. Return `updated_session_ids = [session_id]` and optional `message`
   summarizing what happened.

Failure modes:

- If summarization request fails (no assistant answer, provider error):
  - Do not modify original session.
  - Return `status="error"` with `error_type="plugin_error"` and
    human-readable `message`.

No full sessions are returned.


### 8.3. GenerateTitleAppPlugin

Location:

- Suggested: `core/python/plugins/generate_title_app.py`.

Config (read from the flat `application` section; suggested patterns):

- For example, either:
  - `application["generate_title"] = {"agent_id": "title_generator", "max_messages": 50, "settings_overrides": {"model": "cheap-model", "reasoningEffort": "low"}}`, or
  - flat scalar keys such as `application["generate_title_agent_id"]`,
    `application["generate_title_max_messages"]`, etc.

- Example:

  ```json
  {
    "agent_id": "title_generator",
    "prompt_template": "Generate a short (max 8 words) title for this conversation.",
    "max_messages": 50,
    "field": "title"             // metadata key to write
  }
  ```

Action (`get_actions`):

- `generate_title_for_session`
  - Inputs:
    - `session_id: string, required`.
    - Optional `settings_overrides: object` (see above) to override
      request options like model or reasoningEffort.

Action UI elements:

- Session-list “Generate title”:
  - `ui_type: "session_list_action"`.
  - `action_id: "generate_title_for_session"`.
  - `param_map: {"session_id": "$session.session_id"}`.
  - `dialog.kind = "none"`.

- Session-view “Generate title”:
  - Same `action_id` and param_map, but `ui_type: "session_action"`.

Session-list field element:

- Expose `metadata.title` as the preferred title via `session_list_field`:

  ```json
  {
    "ui_type": "session_list_field",
    "plugin": "generate_title",
    "key": "session_title",
    "role": "title",
    "data": "metadata.title",
    "template": "{{data}}",
    "order": 0
  }
  ```

Execution algorithm:

1. Load original session via `load_session(session_id)` to obtain
   `(core_orig, base_config_orig, session_orig)`.
2. Determine which agent and settings to use for title generation:
   - If a dedicated `agent_id` is configured for generate_title, use
     that; otherwise use the `agent_id` from
     `session_orig.metadata`.
   - Use `AgentApplication.update_agent(agent_id, session_orig)` to get
     `(core_title, base_config_title, session_for_title)` when
     switching agents.
   - If `settings_overrides` are configured (e.g. cheaper model or
     reasoningEffort), merge them into `base_config_title` via
     `resolve_request_config` or equivalent.
3. Build a message subset for title generation:
   - Take up to the last `max_messages` messages from the original
     session (excluding any trailing tool-only noise as desired).
   - Always include the original first message if it is a `system`
     message (and optionally any leading `system` messages) so that the
     original system instructions are preserved as the first
     message(s), even if the title is based only on a suffix of the
     conversation.
4. Create an ephemeral **copy** of the session for the title run:
   - Construct a new in-memory `Session` object with:
     - `session_id` copied from `session_for_title`.
     - `metadata` from `session_for_title.metadata`.
     - `messages` initially empty.
   - Append messages to this ephemeral session preserving structure:
     - First, append the preserved system message(s).
     - Then append the selected recent messages as individual messages
       (user/assistant/tool) rather than collapsing them into a single
       long prompt.
     - Finally, append a `user` message whose content is the
       `prompt_template` (or a prompt built from it) instructing the
       model to generate a short title for the preceding conversation.
5. Run `send_request` for this ephemeral session using `core_title`
   (non-streaming is sufficient) and extract the final assistant
   content as `title`.
6. Under session lock:
   - Reload latest session.
   - Construct new metadata with `metadata[field_name] = title`.
   - Save session.
   - Publish `session_metadata_updated` event containing `session_id`
     and `fields: [field_name]`.
7. Return `updated_session_ids = [session_id]`, optional
   `selected_session_id = session_id`, and `message`.

Again, no full sessions in the result.


9. Terminal & Mobile Integration
--------------------------------


### 9.1. Terminal (TerminalApplication)

Changes in `TerminalApplication` (`terminal_app.py`):

- Add helpers to:
  - List application actions and UI schema via
    `agent_app.get_application_actions()` and
    `agent_app.get_application_ui_schema()`.
  - For terminal commands (e.g. `/copy`, `/summarize_range`, `/title`),
    construct `inputs` objects consistent with action schemas.
  - Call `AgentApplication.execute_application_action(plugin_id,
    action_id, params)` directly instead of re-implementing logic.
- Existing methods `fork_session`, `delete_messages*` can be refactored
  to compose the correct `inputs` and call the SessionActions plugin,
  but should maintain backwards-compatible behavior and event
  publishing.

Tests for terminal integration will come in later stages (see section
10).


### 9.2. Mobile Client

Changes in `mobile/crystal-lattice-control-rn/src/api.ts`:

- Add types for:
  - `ApplicationActionDefinition`.
  - `ActionUiElement`.
  - `SessionListFieldElement`.

- Add APIs:
  - `apiListApplicationActions(adapter): Promise<ApplicationActionDefinition[]>`.
  - `apiListApplicationUiSchema(adapter): Promise<ApplicationUiElement[]>`.
  - `apiExecuteAction(adapter, plugin, actionId, inputs): Promise<ExecuteActionResponse>`.

- Extend `SessionSummary` interface to include `metadata?: Record<string, any>`.

Updates in `SessionsScreen.tsx`:

- Continue to use `session_id`, `modified`, `preview` as today.
- Optionally:
  - Use fetched `session_list_field` elements to choose title,
    subtitles, and meta lines.
  - Use `session_list_action` elements to render additional per-session
    actions (e.g. copy/delete/title) and call `apiExecuteAction` with
    appropriate inputs.


10. Phased Implementation & Tests
---------------------------------

Implement in stages to keep changes tractable and testable.


### Stage 1 – Infrastructure: ApplicationPlugin & Registries

Code changes:

- Add `ApplicationPlugin` protocol and `ApplicationPluginWrapper` in
  `core/python/agent_app/app_plugins.py`.
- Extend config handling in `core/python/agent_app/config.py` with
  `load_application_plugins`.
- Extend `AgentApplication.__init__` to:
  - Load app plugin classes from `application_plugins`.
  - Construct wrappers, call `init`, and store in
    `self._app_plugins`.
- Add methods on `AgentApplication`:
  - `list_application_plugins()`.
  - `get_application_actions()`.
  - `get_application_ui_schema()`.
  - `execute_application_action(plugin_id, action_id, params)`.

Tests for Stage 1:

- New tests in `core/python/tests`, e.g.
  `test_application_layer_app_plugins_basic.py`:
  - Define a dummy `ApplicationPlugin` in the test package that:
    - Records config in `init`.
    - Returns one action with simple input schema via `get_actions`.
    - Returns one UI element via `get_ui_elements`.
    - Records params in `execute_action`.
  - Create a temporary config JSON that references this plugin in
    `application_plugins` and constructs an `AgentApplication`.
  - Assert:
    - `list_application_plugins()` exposes the plugin id and class
      metadata.
    - `get_application_actions()` returns the action with attached
      `plugin` field.
    - `get_application_ui_schema()` returns the UI element with
      attached `plugin` field.
    - `execute_application_action()` successfully calls the dummy plugin
      and returns its result.

Verification:

- Run `pytest core/python/tests -q` and ensure new tests pass without
  regressions.


### Stage 2 – HTTP Endpoints, `/sessions` Metadata & Session-List Fields

Code changes:

- In `application/python/agent_terminal_app/server.py`:
  - Add `GET /application/actions` handler:
    - Calls `app_instance.get_application_actions()`.
    - Applies optional `plugin` filter.
  - Add `GET /application/ui-schema` handler:
    - Calls `app_instance.get_application_ui_schema()`.
    - Applies optional `plugin` filter.
  - Add `POST /actions` handler:
    - Parses `plugin`, `action_id`, `inputs` from body.
    - Locates action schema in `get_application_actions()`.
    - Validates `inputs` (required fields, defaults, types).
    - On success:
      - Calls `execute_application_action`.
      - Serializes plugin result to the standard success envelope
        (without sessions).
    - On failure:
      - Returns the error envelope with `status="error"` and
        appropriate `error_type`.

- Update `GET /sessions` handler in `server.py` to:
  - Read and include `metadata` from each session file, in addition to
    `session_id`, `modified`, and `preview`.
  - Continue to avoid loading `messages` into the response.

- Optionally, define a small builtin app plugin or static config that
  contributes `session_list_field` elements for:
  - Title fallback from `preview` or first part of `session_id`.
  - Updated timestamp from `modified`.

Tests for Stage 2:

- New tests in `application/python/tests`, e.g.
  `test_application_actions_endpoints.py`:
  - Use a dummy app plugin (similar to Stage 1) wired into a test
    `AgentApplication` used by FastAPI dependency injection.
  - Test `GET /application/actions`:
    - Returns the dummy action and honors `plugin` filter.
  - Test `GET /application/ui-schema`:
    - Returns dummy UI element and honors `plugin` filter.
  - Test `POST /actions` happy path:
    - Valid `plugin`, `action_id`, `inputs` → success, `status="ok"`,
      and plugin-specific `result`.
  - Test `POST /actions` validation failures:
    - Missing required parameter.
    - Wrong type.
    - Unknown plugin.
    - Unknown action.
  - Test that response payload **does not** contain any session objects
    (e.g. assert that there is no `"session"` key at top level or in
    result; plugin tests should not return them).

- Additional tests in `application/python/tests`, e.g.
  `test_server_sessions_list_metadata.py`:
  - Create a couple of sessions (with metadata including a title).
  - Call `GET /sessions`.
  - Assert:
    - Each item has `session_id`, `modified`, `preview`, `metadata`.
    - `metadata` matches what was persisted (but no `messages`).

- If a builtin session-list field plugin is added, test that
  `GET /application/ui-schema` returns `session_list_field` entries
  referencing `preview` and `modified`.

Verification:

- Run `pytest application/python/tests -q` and ensure new and existing
  tests pass.


### Stage 3 – SessionActionsAppPlugin (Copy/Fork/Delete) + Mobile Integration

Code changes:

- Implement `SessionActionsAppPlugin` in
  `core/python/plugins/session_actions_app.py`:
  - Provide `get_actions` definitions for copy/fork/delete actions.
  - Provide `get_ui_elements` definitions for action UI elements across
    session view, session list, and messages.
  - Implement `execute_action` using existing logic in
    `TerminalApplication` and `server.py` as behavioral reference.
  - Ensure `execute_action` only returns ids (e.g.
    `created_session_ids`, `updated_session_ids`, `deleted_session_ids`)
    and does not return baked-in sessions.

- Wire the plugin into the main config used by the terminal/HTTP app.

- Optionally refactor legacy endpoints:
  - `/sessions/{id}/fork` and `DELETE /sessions/{id}/messages` to
    construct `inputs` and call `execute_application_action` rather than
    duplicating logic.

Tests for Stage 4:

- New tests in `core/python/tests`, e.g.
  `test_session_actions_app_plugin_unit.py`:
  - Build a minimal `AgentApplication` with a dummy provider.
  - Register `SessionActionsAppPlugin` and create sessions.
  - Call `execute_application_action` directly with appropriate
    `inputs`:
    - `copy_session` → assert a new session id exists in the store.
    - `fork_session_at` → assert messages up to index copied.
    - `delete_messages` → assert messages removed.
  - Assert plugin result includes correct id lists and no sessions.

- New or updated server tests, e.g.
  `test_server_actions_session_actions_integration.py`:
  - Use `POST /actions` with `session_actions` plugin to perform copy,
    fork, and deletions.
  - Confirm that sessions are updated as expected when reloaded via
    `/sessions/{id}/messages`.
  - Confirm no sessions are embedded in `POST /actions` responses.
  - If `/sessions/{id}/fork` and delete endpoints are refactored to use
    the plugin, confirm they still behave as before by reusing existing
    expectations.

Additionally, at this stage begin **mobile integration** for the
SessionActions plugin:

- Add the new `/application/actions`, `/application/ui-schema`, and
  `/actions` calls to `mobile/.../src/api.ts`.
- In `SessionsScreen.tsx`, render buttons for any
  `session_list_action` elements coming from the SessionActions plugin
  (e.g. copy/delete), and wire them to `apiExecuteAction`.
- Keep the UI minimal but ensure the flow is end-to-end testable.

Mobile tests:

- Jest tests that mock the HTTP adapter and:
  - Provide synthetic UI schema via `/application/ui-schema`.
  - Confirm that `SessionsScreen` renders SessionActions buttons.
  - Confirm that pressing a button calls `apiExecuteAction` with the
    expected `plugin`, `action_id`, and `inputs`.

Verification:

- Run core and application tests.
- Run mobile Jest tests.


### Stage 4 – SummarizeRangeAppPlugin + Mobile Integration

Code changes:

- Implement `SummarizeRangeAppPlugin` as described in section 8.2.

Tests for Stage 5:

- New tests in `core/python/tests`, e.g.
  `test_summarize_range_app_plugin_unit.py`:
  - Use a dummy provider that returns deterministic summaries so tests
    don’t require external APIs.
  - Create a session with a few messages.
  - Call `execute_application_action("summarize_range", ...)`.
  - Assert that messages in `[start:end]` are replaced by exactly one
    summary message and others remain.
  - Assert `updated_session_ids` includes the original session id.

- New server-level test in `application/python/tests`, e.g.
  `test_server_actions_summarize_range.py`:
  - Wire the plugin into a test config.
  - POST to `/actions` with `plugin="summarize_range"`, appropriate
    `inputs`.
  - Reload messages via `/sessions/{id}/messages` and verify the
    summary replacement occurred.
  - Assert error handling when indices are invalid or beyond
    `max_range_length`.

Mobile integration at this stage:

- Extend mobile API/types to understand `summarize_range` action
  definitions and UI schema entries.
- In the session view screen (or a dedicated UI), show an action for
  `summarize_range` when appropriate and call `apiExecuteAction`.
- For tests, use dummy providers to avoid external calls.

Verification:

- Run `pytest` suites covering core and application tests.
- Run mobile Jest tests that:
  - Render the session view with a fake `summarize_range` UI element.
  - Trigger the action and assert correct HTTP calls.


### Stage 5 – GenerateTitleAppPlugin & Session-List Titles + Mobile Integration

Code changes:

- Implement `GenerateTitleAppPlugin` as in section 8.3.
- Ensure it contributes a `session_list_field` element for
  `metadata.title`.

Tests for Stage 6:

- New core-level tests:
  - Ensure `execute_application_action("generate_title_for_session")`
    updates `metadata.title` and returns `updated_session_ids`.

- New server-level tests:
  - After running `/actions` to generate a title, call `GET /sessions`
    and verify that the summary for that session now has `metadata`
    containing the new title.
  - Confirm that UI schema includes the `session_list_field` entry
    referencing `metadata.title`.

Mobile integration at this stage:

- Extend mobile API/types to understand `generate_title_for_session`
  and associated UI schema entries.
- In `SessionsScreen`, add a “Generate title” action using the
  SessionList action element from `GenerateTitleAppPlugin`.
- Confirm that after running the action and refreshing `/sessions`, the
  new `metadata.title` is honored by any UI logic for picking the
  session title.

Verification:

- Run application tests.
- Run mobile Jest tests that:
  - Provide a UI schema with a `session_list_action` for
    `generate_title_for_session` and a `session_list_field` for
    `metadata.title`.
  - Trigger the action and confirm the title is updated in the list.


### Stage 6 – Terminal UI Adoption

Code changes (terminal only at this stage):

- Add new commands or menus to list available actions for the current
  context (session, message) using `get_application_ui_schema()`.
- When an action is selected, gather any required inputs (using
  `dialog` config) and construct the `inputs` object.
- Call `execute_application_action` directly rather than re-implement
  logic.

Tests for Stage 6:

- Terminal tests:
  - Extend or add tests in `application/python/tests` validating that
    invoking new commands (copy/summarize/title) results in calls to
    the appropriate actions and that sessions/events update as
    expected.

Verification:

- Run Python tests.
- Manually verify behavior in the terminal UI, ensuring action flows
  work end-to-end and no APIs return full sessions from `POST /actions`.


11. No Full Sessions in Action Responses
----------------------------------------

Throughout all stages, maintain the invariant that **no new action
responses include full sessions**:

- `POST /actions` must never embed session objects; only session ids
  and small scalar metadata are allowed.
- Existing endpoints like `GET /sessions/{id}/messages` and
  `GET /sessions` remain the authoritative sources for session
  contents and summaries.
- Add tests that explicitly assert the absence of `"session"` keys in
  `POST /actions` responses to prevent regressions.
