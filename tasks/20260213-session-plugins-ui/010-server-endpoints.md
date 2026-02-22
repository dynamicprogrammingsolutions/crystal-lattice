# Server: session plugin endpoints (/plugins parity)

Parent Task: tasks/20260213-session-plugins-ui/000-main.md

## Description

Add HTTP endpoints to `application/python/agent_terminal_app/server.py` so mobile/desktop can list and toggle plugins for a session, matching terminal `/plugins` behavior.

## Background / existing code to reuse

Terminal logic already exists and should be reused to avoid subtle behavior drift:

- `application/python/agent_terminal_app/terminal_app.py`:
  - `list_plugins_for_session()` (~1014+) returns plugin metadata enriched with:
    - `enabled`: based on `session.metadata["plugins"]`, agent defaults, or implicit all-enabled
    - `source`: `session` | `agent` | `implicit`
    - `active`: computed from `core.get_plugins_for_config(resolve_request_config(base_config, overrides))`
  - `set_session_plugins(enabled_ids)` (~1091+) persists and reloads core/session
  - `clear_session_plugins()` (~1132+) clears overrides and reloads core/session

The repository’s parity plan already lists these as NEW endpoints:
`application/python/agent_terminal_app/server_endpoints_parity.md` (Plugin management section).

## API contract

### 1) `GET /sessions/{session_id}/plugins`

- Response: `{ "plugins": [ ... ] }`
- Each entry should match `TerminalApplication.list_plugins_for_session()` output.
  - Typical fields include: `id`, `kind`, optional `name`, `class_path`, `class_name`, plus `enabled`, `source`, `active`.

### 2) `PUT /sessions/{session_id}/plugins`

- Body: `{ "enabled": ["plugin_id", ...] }`
- Behavior:
  - Set **explicit** enabled list on the session (`session.metadata["plugins"]`).
  - Normalize to unique string ids, preserving order (same as terminal).
- Response: `{ "session": <Session.to_dict()>, "plugins": [ ... ] }` (recommended)
  - Returning the new plugins list helps UIs avoid an immediate reload.

### 3) `DELETE /sessions/{session_id}/plugins`

- Behavior: clear `session.metadata["plugins"]`.
- Response: `{ "session": <Session.to_dict()>, "plugins": [ ... ] }` (recommended)

## Implementation notes

### Where to implement

- `application/python/agent_terminal_app/server.py`
  - Follow existing patterns:
    - Load session via `app_instance.load_session(session_id)`.
    - Wrap mutations with `with app_instance.acquire_session_lock(session_id):`.
    - Return 404 when session is missing.

### Avoid code duplication

You have two viable approaches:

1) **Delegate to `TerminalApplication`** for list/set/clear behavior.
   - Pros: exact parity.
   - Cons: server routes currently mostly talk directly to `AgentApplication` + `AgentCore`; terminal app is more “UI-ish”.

2) **Copy the logic but keep it small**, using the same primitives (`list_plugins()`, `get_agent_plugins()`, `resolve_request_config`, `core.get_plugins_for_config`, `session.metadata`).
   - Pros: keeps server independent of terminal UI types.
   - Cons: risk of drift if terminal logic changes.

Recommendation: for list computation, implement a small helper in `server.py` mirroring `TerminalApplication.list_plugins_for_session()`.
For set/clear, mutate session metadata and reload via `app_instance.load_session(...)` the same way terminal does (i.e., ensure subsequent sends use updated plugin set).

### “active” vs “enabled”

`enabled` is user-controlled. `active` is determined by config:
- It’s possible for an enabled plugin to be inactive due to the config state; UIs should display that.

The terminal computes `active` via:
- base config + session overrides (`session.metadata["overrides"]`)
- `resolve_request_config(base_config, overrides)`
- `core.get_plugins_for_config(config)`

### Provider safety warning

Terminal prints a warning if disabling a provider would leave **no providers enabled**.
HTTP API probably should **not** block this; just allow it.
If you want parity, consider adding a boolean in the response like `{ warnings: ["no_providers_enabled"] }` but this is optional.

## Tests

Add/extend tests under `application/python/tests/`:

- Suggested location: `application/python/tests/test_agent_terminal_app_server.py`
  - Add a test that:
    1. Creates a session.
    2. Calls `GET /sessions/{id}/plugins` and asserts shape includes `enabled` boolean per plugin.
    3. Calls `PUT /sessions/{id}/plugins` with a subset.
    4. Calls `GET` again and verifies enabled flags reflect the subset and `source == "session"`.
    5. Calls `DELETE` and verifies `source` becomes `agent` or `implicit` again.

If existing tests already create sessions with plugins configured, reuse those fixtures/patterns.

## Done when

- Endpoints behave consistently with terminal:
  - explicit list is stored in `session.metadata["plugins"]`
  - clearing removes the key
  - list includes `enabled`, `source`, `active`
- Tests pass.

## Completion notes (2026-02-13)

- Implemented session plugin routes in `application/python/agent_terminal_app/server.py`:
  - `GET /sessions/{session_id}/plugins`
  - `PUT /sessions/{session_id}/plugins`
  - `DELETE /sessions/{session_id}/plugins`
- Added `_list_plugins_for_session(...)` helper mirroring terminal logic.
- Added regression test `test_session_plugins_endpoints_roundtrip` in `application/python/tests/test_agent_terminal_app_server.py`.
