# Stage 1: Live Server Settings And Lifecycle
Build a complete live server-settings slice that is testable from the mobile UI over an active connection, while also adding lifecycle hooks for both session and server settings changes.

## Requirements checklist

- [ ] Add `AgentApplication`-owned persisted server settings helpers instead of storing server-global settings in FastAPI route code.
- [ ] Refactor session override mutation paths so session settings writes go through `AgentApplication` helpers and can fire lifecycle triggers.
- [ ] Add lifecycle support for `session_settings_changed` and `server_settings_changed` with useful JSON-serializable context.
- [ ] Add live server settings HTTP routes that mirror the existing session settings routes.
- [ ] Extend the frontend SDK with server settings backend methods and a live server settings controller modeled after the session settings controller.
- [ ] Add a minimal mobile server settings modal reachable from the connected sessions screen.
- [ ] Implement the first application plugin consumer: sleep prevention with `caffeinate` on macOS and `wakepy` elsewhere.
- [ ] Add tests and docs covering the new server settings and lifecycle model.

Parent Task: `tasks/20260421-server-settings-bridge-sync/000-main.md`

## Scope

- This stage must be usable end to end without bridge or offline behavior.
- The live UI path should be testable from the mobile sessions screen before Stage 2 starts.
- Server settings UI schema should come from `/application/ui-schema`, filtered to config-like elements with `scope: "server"`.

## Existing Relevant Code

- Application-plugin protocol and UI hooks:
  - `core/python/agent_app/app_plugins.py:22-210`
  - `core/python/agent_app/application_future.py:1682-1726`
- Existing lifecycle runner and context builder:
  - `core/python/agent_app/application_future.py:1071-1227`
- Current session override HTTP ownership that should move behind `AgentApplication` helpers:
  - `application/python/agent_terminal_app/server.py:1404-1432`
  - `application/python/agent_terminal_app/server.py:1572-1652`
  - `application/python/agent_terminal_app/server.py:1704-1765`
- Backend interface seams to extend:
  - `packages/frontend-sdk/src/backend/backend.ts:179-214`
  - `packages/frontend-sdk/src/backend/restBackend.ts:468-577`
- Best frontend behavior template:
  - `packages/frontend-sdk/src/sessionSettings/sessionSettingsController.ts:134-380`
  - `mobile/crystal-lattice-control-rn/src/components/SessionSettingsModal.tsx:29-220`
- Best current place to expose the live settings entrypoint:
  - `mobile/crystal-lattice-control-rn/src/SessionsScreen.tsx:177-216`

## Implementation Notes

- Add `AgentApplication` helpers for:
  - get server settings
  - patch server settings
  - delete server setting
- Add an application-level lifecycle runner for server settings changes since `run_session_lifecycle()` is session-bound.
- For both session and server settings change events, context should include at least:
  - `scope`
  - `old_settings`
  - `new_settings`
  - `changed_keys`
  - `source`
- Keep the server HTTP layer thin:
  - validate request payloads
  - call `AgentApplication` helpers
  - return normalized JSON results
- Reuse the session settings UI model rather than inventing a separate rendering system.
- The sleep-prevention plugin should be an application plugin, not a feature plugin:
  - it provides server-scoped config UI
  - it reacts to `server_settings_changed`
  - it should also replay persisted current settings once on startup so the plugin enforces state after restart

## Suggested Tests

- `core/python/tests`
  - server settings persistence helpers
  - `server_settings_changed` lifecycle dispatch
  - `session_settings_changed` lifecycle dispatch
- `application/python/tests`
  - `GET/PATCH/DELETE /server/settings`
  - session override routes now flowing through `AgentApplication`
- plugin unit tests
  - mock subprocess/process ownership for `caffeinate`
  - mock `wakepy` activation/deactivation
- frontend SDK tests
  - server settings controller load / optimistic patch / delete / refresh behavior
- mobile/UI tests
  - connected sessions screen can open the modal and save a live server setting

## Acceptance Notes

- A direct HTTP connection should be enough to prove the feature works.
- No bridge or offline cache behavior is required in this stage.