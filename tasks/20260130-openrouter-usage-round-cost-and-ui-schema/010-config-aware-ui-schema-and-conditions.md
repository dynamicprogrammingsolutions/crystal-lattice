Parent Task: tasks/20260130-openrouter-usage-round-cost-and-ui-schema/000-main.md

# Config-aware UI schema + lightweight conditions

Add a config-aware (and session-override-aware) UI schema mechanism across plugin types, so UI elements can be turned on/off per session by config overrides.

This task is related to sandboxing’s session-aware app plugin UI work, but it is intentionally separate:

- Reference: `tasks/20260128-sandboxing-prereqs/040-session-aware-app-plugin-ui-and-conditions.md`

## Problem

- Core plugins (providers/extensions/features/tools) originally exposed UI elements via `get_ui_elements()` with **no config input**.
  - Protocol: `core/python/agent_core/types.py` (see `BasePlugin.get_ui_elements`)
- Core UI schema aggregation (`AgentCore.get_ui_schema`) was also **configless**.
  - `core/python/agent_core/core.py`
- Per-session overrides exist (`session.metadata["overrides"]`) and are merged into effective config for requests.
  - Merge helper: `core/python/agent_app/config.py:131`

Result: even if a user toggles a config override, the UI schema returned by the server remains unchanged, so message footers/status bars can’t be enabled/disabled per-session.

## Goals

1) Allow plugins to generate UI elements dynamically based on effective config (base + session overrides).
2) Keep `condition` support for message/status rendering (message-specific rules still need runtime evaluation).
3) Keep backwards compatibility for existing plugins.

## Proposed protocol & API changes

### A) Core plugins: config-aware UI elements

Adopt a context-aware UI hook for core plugin types:

- `get_ui_elements(self, config: Dict[str, Any], tags: List[str], models: List[Dict[str, Any]]) -> List[Dict[str, Any]]`

Notes:

- The core computes `tags` and `models` from the effective config and passes them to plugins.
- For backward compatibility, adapters may fall back to calling a legacy `get_ui_elements()` implementation with no arguments.

Where this hooks in:

- Provider wrapper: `core/python/agent_core/plugin/provider.py`
- Extension wrapper: `core/python/agent_core/plugin/extension.py`
- Feature wrapper: `core/python/agent_core/plugin/feature.py`
- Tool wrapper: `core/python/agent_core/plugin/tool.py`

### B) Core: config-aware schema aggregation

Expose UI schema aggregation as:
- `AgentCore.get_ui_schema(config: Dict[str, Any]) -> List[Dict[str, Any]]`

Implementation idea:

- The core resolves enabled plugins for `config`, computes `tags` and `models`, then gathers UI elements via `get_ui_elements(config, tags, models)`.

### C) Server/UI schema endpoints must use effective per-session config

Update the session UI schema endpoint to compute effective config:

- Endpoint: `application/python/agent_terminal_app/server.py:617` (`GET /sessions/{session_id}/ui-schema`)
- Callers should pass an effective config to `core.get_ui_schema(effective_config)`.

Desired:

- Load session.
- Extract `session.metadata["overrides"]`.
- Compute `effective_config = resolve_request_config(base_config, overrides)`.
- Return `core.get_ui_schema(effective_config)`.

Also consider TerminalApplication local UI calls (terminal-only UI schema access):
- `application/python/agent_terminal_app/terminal_app.py` should call `core.get_ui_schema(effective_config)`.

(With the updated API, callers should pass the effective config.)

### D) Application plugins

This task is primarily about core plugin UI schema (needed for OpenRouter usage toggles), but it is worth aligning with sandboxing work:

- Application plugins currently have `get_ui_elements(state)` and no session/config inputs.
  - Protocol: `core/python/agent_app/app_plugins.py:47`
- Existing sandboxing task proposes a session-aware method.
But note: sandboxing’s “Enter/Exit sandbox” needs session metadata as well, so app-plugin UI likely still needs a session-aware method from the sandboxing task rather than a config-only hook.

## Lightweight `condition` spec (for message_footer/status_bar)

Dynamic schema solves config-based toggles, but message/status elements still need message-specific visibility rules.

### Requirement

The spec must work in:

- Terminal footer renderer: `application/python/agent_terminal_app/event_rendering.py:200`
- RN message renderer: `mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx:58`

### Proposed minimal `condition` shape

Allow `condition` on any UI element dict, especially `ui_type in {"message_footer", "status_bar"}`.

Recommended minimal format (easy to implement in both Python and TypeScript):

```json
{
  "condition": {
    "all": [
      {"path": "role", "eq": "assistant"},
      {"path": "metadata.tool_calls", "empty": true}
    ]
  }
}
```

Leaf condition operators (keep it small):

- `eq`: strict equality
- `exists`: boolean
- `empty`: boolean (treat `null`, `undefined`, `""`, `[]`, `{}` as empty)
- Composition: `all`, `any`, `not`

Evaluation context:

- For `message_footer`: evaluate against the core message dict being rendered.
- For `status_bar`: evaluate against the last assistant message dict used for status bar extraction.

### Implementation notes

- Terminal:
  - Add condition evaluation in the existing loops that already have `msg`.
  - Message footer: `application/python/agent_terminal_app/event_rendering.py:211`
  - Status bar: `application/python/agent_terminal_app/terminal.py:214`
- RN:
  - Add condition evaluation in the per-message footer loop in `MessageBubble.tsx`.
  - For status bar, condition evaluation likely belongs where status bar parts are derived (search for `deriveChatStatusBarParts`).

## Acceptance criteria

- `GET /sessions/{id}/ui-schema` returns different element sets when overrides change.
- A plugin (e.g. OpenRouter usage extension) can expose UI toggles as config and have those toggles enable/disable message footers/status bars per session.
- Message/status `condition` can be expressed with the minimal operators above and evaluated by both terminal and RN.
