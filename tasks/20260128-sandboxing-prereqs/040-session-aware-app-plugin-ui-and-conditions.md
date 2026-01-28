Parent Task: tasks/20260128-sandboxing-prereqs/000-main.md

# Session-aware Application Plugin UI and Conditions

Enable application plugins (like the sandbox plugin) to contribute UI elements/actions whose availability depends on the current session state (e.g., “Enter sandbox” vs “Exit sandbox”).

## Current state

- Application plugin UI elements are global/static: `ApplicationPlugin.get_ui_elements(state)` has no `session` context.
  - Protocol: `core/python/agent_app/app_plugins.py:22`
  - Application UI schema endpoint: `application/python/agent_terminal_app/server.py:1951`

- Frontends can evaluate simple conditions for config UI elements (example: `feature-web-context` uses `condition`).
  - `plugins/feature-web-context/src/feature_web_context/web_context_feature.py:163`

But there is no defined convention for conditions based on `session.metadata` (for application plugin action UI).

## Goal

Provide a clean mechanism so an application plugin can express:

- “Show `Enter sandbox` action only when `session.metadata.sandbox.active != true`.”
- “Show `Exit sandbox` / `Export changes` action only when active.”

## Design options

1) **Extend application plugin protocol** to allow session-aware UI schema:

- Add a new optional method:
  - `get_session_ui_elements(app, session, state) -> List[Dict[str, Any]]`
  - Keep `get_ui_elements(state)` for global UI.

2) **Define a standard `condition` mini-language** for application UI elements.

- Keep protocol unchanged, but standardize that app UI elements may include:
  - `condition: { "session.metadata.<key>": <value> }`
- Requires updating frontends to evaluate the condition.

3) **Do nothing in core** and let frontends hide/show based on ad-hoc rules.

- Not recommended: leaks sandbox semantics into UI code.

## Recommended direction

Option (1) + optionally also support `condition`.

- Server can expose `GET /sessions/{id}/application/ui-schema` that is computed per-session.
- Mobile/terminal can render those actions with no extra hardcoding.

## Acceptance criteria

- There is a way for a sandbox application plugin to expose session-scoped UI without modifying the mobile/terminal app for each new plugin.
- The mechanism supports reading `session.metadata` at minimum.
