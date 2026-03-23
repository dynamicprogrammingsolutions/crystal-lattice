# Session Plugins UI (mobile + desktop) + server endpoints

## Goal

Add a “Plugins” UI to the **mobile** and **desktop** apps that mirrors the terminal’s `/plugins` command:

- Placement: in the **session actions bar**, alongside “Session settings”.
- UI: list plugins with **switches** (enabled/disabled), show whether a plugin is **inactive** due to config, and support **reset to defaults**.

This requires adding session plugin endpoints to the Python FastAPI server, extending the shared frontend SDK, creating reusable UI/controller code, and wiring it into mobile/desktop.

## What’s already known (research summary)

### Terminal implementation

- `/plugins` command lives in `application/python/agent_terminal_app/terminal.py` around lines ~1157+.
  - Lists plugins using `TerminalApplication.list_plugins_for_session()`.
  - Toggling uses `TerminalApplication.set_session_plugins([...])` and reset uses `clear_session_plugins()`.

- The underlying session plugin logic is in `application/python/agent_terminal_app/terminal_app.py`:
  - `list_plugins_for_session()` (~1014+) computes:
    - `enabled`: derived from `session.metadata["plugins"]` or agent defaults or implicit all-enabled
    - `source`: `session` | `agent` | `implicit`
    - `active`: computed via `core.get_plugins_for_config(resolve_request_config(base_config, overrides))`
  - `set_session_plugins(enabled_ids)` persists an explicit list to `session.metadata["plugins"]` and reloads the session/core.
  - `clear_session_plugins()` removes `session.metadata["plugins"]`.

### Server state

- Current FastAPI routes are in `application/python/agent_terminal_app/server.py`.
- Session settings (UI schema + overrides) endpoints already exist and are used by mobile/desktop.
- The repository already contains an explicit parity plan that lists the plugin endpoints as *NEW*:
  - `application/python/agent_terminal_app/server_endpoints_parity.md` (Plugin management section).

### Mobile/desktop UI patterns to reuse

- Mobile uses `SessionActionsBar` and built-in action keys from `packages/frontend-rn-components/src/sessionActions.ts`.
  - `SessionChatScreen.tsx` handles action `'settings'` by opening `SessionSettingsModal`.
  - `SessionsScreen.tsx` also exposes session actions per session row (currently `agentSwitch`, `settings`).

- Desktop uses a custom session action bar in `desktop/.../src/chat/ChatPane.tsx` (built-in actions list includes `'settings'`).
  - `'settings'` opens a dedicated window (`SessionSettingsWindow.tsx` + coordinator).

## Deliverables / acceptance criteria

1. Server implements:
   - `GET /sessions/{session_id}/plugins`
   - `PUT /sessions/{session_id}/plugins` with `{enabled: string[]}`
   - `DELETE /sessions/{session_id}/plugins`
2. Shared frontend SDK exposes a typed API for those endpoints, and capabilities advertise support.
3. Shared reusable UI/controller exists so mobile + desktop do not duplicate plugin toggle logic.
4. Mobile:
   - A “Plugins” session action opens a modal with switches + reset.
   - Works from both chat screen session actions and sessions list actions.
5. Desktop:
   - A “Plugins…” session action opens a UI with switches + reset (modal or window per subtask choice).
6. Tests:
   - Server endpoints have test coverage (at least list + set + clear flows).

## Subtasks

- [x] `tasks/20260213-session-plugins-ui/010-server-endpoints.md`
- [x] `tasks/20260213-session-plugins-ui/020-shared-frontend-sdk.md`
- [x] `tasks/20260213-session-plugins-ui/030-shared-ui-and-controller.md`
- [ ] `tasks/20260213-session-plugins-ui/040-mobile-integration.md`
- [x] `tasks/20260213-session-plugins-ui/050-desktop-integration.md`

---

## Implementation notes (added during completion, 2026-02-13)

- Subtask `tasks/20260213-session-plugins-ui/030-shared-ui-and-controller.md` implemented shared hook + UI building blocks:
  - `packages/frontend-sdk-react/src/useSessionPluginsController.ts`
  - `packages/frontend-rn-components/src/SessionPluginsList.tsx`
  - `packages/frontend-rn-components/src/sessionActions.ts` (new `plugins` action)

---

## Progress Notes (as of 2026-02-13)

- `tasks/20260213-session-plugins-ui/020-shared-frontend-sdk.md` completed.
  - SDK now supports session plugin endpoints via `AgentBackend` + `RestAgentBackend`.
  - Capability flag added: `BackendCapabilities.sessionPlugins`.
  - Types/methods/tests added in `packages/frontend-sdk/` (see the subtask file for the complete file list).
