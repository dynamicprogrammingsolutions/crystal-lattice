# Server Settings And Bridge Sync
Add server-scoped settings with lifecycle hooks, a live mobile UI path, bridge-backed desired/last-known state sync, and a sleep-prevention application plugin.

## Task checklist

- [ ] `tasks/20260421-server-settings-bridge-sync/010-live-server-settings-and-lifecycle.md`
- [ ] `tasks/20260421-server-settings-bridge-sync/020-bridge-server-state-and-sync.md`
- [ ] `tasks/20260421-server-settings-bridge-sync/030-offline-server-settings-ui-and-cache.md`

## Goals

- Introduce server-global settings as an `AgentApplication` capability, not ad hoc FastAPI state and not plugin-owned persistence.
- Keep the UI schema generic by using config-like application UI elements with `scope: "server"`.
- Reuse the existing lifecycle-trigger model by adding `server_settings_changed` and `session_settings_changed`.
- Keep sleep prevention plugin-provided:
  - macOS uses `caffeinate`
  - other platforms use `wakepy`
- Support normal live settings edits over direct HTTP/manual/discovery connections.
- Support offline desired-state edits only for bridge connections.
- Keep the bridge generic by storing per-server state documents, not sleep-specific commands.

## Approved Decisions

- Server settings live in `AgentApplication` and are persisted by application-owned helpers.
- Server HTTP routes should mirror session settings routes:
  - `GET /server/settings`
  - `PATCH /server/settings`
  - `DELETE /server/settings/{key}`
- Application plugins provide server settings UI via normal config-like elements plus `scope: "server"`.
- The frontend should filter server-scoped elements from `/application/ui-schema`.
- The bridge should store:
  - `desired_settings`
  - `last_known_settings`
- The frontend should show the latest known values immediately, then refresh, similar to the current session settings flow.
- A `Pending sync` warning is shown when bridge `desired_settings` and `last_known_settings` differ.
- macOS scheduled wake + poll belongs to the server/transport layer, not the sleep-prevention plugin itself.

## Existing System Notes

- Application-plugin UI schema already exists and is flattened in `AgentApplication.get_application_ui_schema()` at `core/python/agent_app/application_future.py:1702-1726`.
- Application-plugin lifecycle-trigger execution already exists for session-bound lifecycles in `AgentApplication.run_session_lifecycle()` at `core/python/agent_app/application_future.py:1151-1227`.
- Lifecycle context currently includes `lifecycle`, `trigger_source`, `session`, `config`, `app`, `application`, and `base_config` in `core/python/agent_app/application_future.py:1091-1108`.
- Session settings writes do not currently go through lifecycle helpers; the HTTP layer mutates `session.metadata["overrides"]` directly in:
  - `application/python/agent_terminal_app/server.py:1572-1652`
  - `application/python/agent_terminal_app/server.py:1704-1765`
- Application-plugin protocol and wrapper live in `core/python/agent_app/app_plugins.py:22-210`.
- Session settings frontend behavior is a strong template for the new server settings controller:
  - cache hydration, optimistic mutation, and refresh behavior in `packages/frontend-sdk/src/sessionSettings/sessionSettingsController.ts:134-380`
  - current session settings modal in `mobile/crystal-lattice-control-rn/src/components/SessionSettingsModal.tsx:29-220`
- Application UI schema caching currently exists only in-memory via `packages/frontend-sdk/src/plugins/pluginsRegistry.ts:24-161`.
- The sessions screen is the natural home for the live connected server-settings gear:
  - `mobile/crystal-lattice-control-rn/src/SessionsScreen.tsx:99-216`
- The connection screen is currently minimal and is the natural home for the future offline bridge gear:
  - `mobile/crystal-lattice-control-rn/src/ConnectionScreen.tsx:6-137`
- Backend and REST seams that need extending:
  - backend interface in `packages/frontend-sdk/src/backend/backend.ts:41-214`
  - session settings and application UI calls in `packages/frontend-sdk/src/backend/restBackend.ts:468-577`
- The bridge is currently an HTTP tunnel plus pairing/session management:
  - app side in `bridge-elixir/lib/bridge/app_channel.ex:57-260`
  - server side in `bridge-elixir/lib/bridge/server_channel.ex:5-175`
  - frontend transport assumes a live paired session for normal requests in `packages/frontend-sdk/src/transport/bridgeTransport.ts:154-260`

## Stage Summary

- Stage 1 builds a complete live vertical slice:
  - storage
  - lifecycle
  - HTTP API
  - frontend controller
  - mobile settings modal
  - sleep-prevention plugin
- Stage 2 adds bridge-side per-server state, Python bridge-client reconciliation, and macOS scheduled wake/sync plumbing.
- Stage 3 adds persisted connection-scoped cache plus offline bridge settings UI from the connection screen.

## Risks To Watch

- Avoid splitting settings persistence between FastAPI, plugins, and `AgentApplication`; keep one owner.
- Keep bridge extensions generic enough to support future server-global settings beyond sleep prevention.
- Ensure session settings lifecycle additions do not change the semantics of request-time config resolution.
- Avoid mixing desired state with applied state in the UI; the pending-sync state depends on preserving both.