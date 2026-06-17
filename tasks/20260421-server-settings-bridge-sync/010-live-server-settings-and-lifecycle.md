# Stage 1: Live Server Settings And Lifecycle
Build a complete live server-settings slice that is testable from the mobile UI over an active connection, while also adding lifecycle hooks for both session and server settings changes.

## Requirements checklist

- [x] Add `AgentApplication`-owned persisted server settings helpers instead of storing server-global settings in FastAPI route code.
- [x] Refactor session override mutation paths so session settings writes go through `AgentApplication` helpers and can fire lifecycle triggers.
- [x] Add lifecycle support for `session_settings_changed` and `server_settings_changed` with useful JSON-serializable context.
- [x] Add live server settings HTTP routes that mirror the existing session settings routes.
- [x] Extend the frontend SDK with server settings backend methods and a live server settings controller modeled after the session settings controller.
- [x] Add a minimal mobile server settings modal reachable from the connected sessions screen.
- [ ] Implement the first application plugin consumer: sleep prevention with `caffeinate` on macOS and `wakepy` elsewhere.
- [x] Add tests and docs covering the new server settings and lifecycle model.

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

## Execution plan

Added during completion after user approval.

- Implement server/session settings ownership in `AgentApplication` first:
  - add application-owned persisted server settings helpers
  - route session override mutations through application helpers
  - fire `server_settings_changed` and `session_settings_changed` lifecycle triggers with JSON-serializable context
- Keep FastAPI route logic thin:
  - HTTP handlers should validate/format request and error envelopes only
  - all settings reads, writes, persistence, changed-key calculation, and lifecycle dispatch should live below the HTTP layer
- Add live server settings routes:
  - `GET /server/settings`
  - `PATCH /server/settings`
  - `DELETE /server/settings/{key}`
- Add a sample dummy application plugin/test fixture for generic behavior tests:
  - contribute server-scoped config UI schema
  - record settings lifecycle calls for assertions
  - avoid coupling generic settings behavior tests to sleep-prevention semantics
- Extend the frontend SDK:
  - backend interface and REST backend methods for server settings
  - live server settings controller modeled after the session settings controller
  - filter config-like `/application/ui-schema` elements with `scope: "server"`
- Add the connected mobile UI path:
  - server settings modal reachable from the connected sessions screen
  - component tests plus real-backend component integration using the dummy plugin
  - first human checkpoint occurs after this UI path exists so behavior can be verified in the UI
- Implement sleep-prevention as an application plugin consumer:
  - server-scoped UI
  - lifecycle reaction
  - mocked tests for process/wakepy ownership
  - do not use it as the generic connection behavior test vehicle
- Verification focus for this environment:
  - targeted `AgentApplication` tests
  - targeted HTTP tests
  - SDK tests after local Node install under ignored `tmp/`
  - React Native component and real-backend component integration tests after local Node install

## Checkpoint Notes

Added during completion at the first requested human checkpoint.

- Implemented the generic live server-settings connection path through the connected mobile UI.
- The UI path is testable with `DummySettingsAppPlugin`, which contributes server-scoped config controls and records lifecycle calls.
- `DummySettingsAppPlugin` is available as a runtime-loadable demo plugin at `plugins/dummy-settings-app` and can be referenced from config with `path:${env:BUILTIN_PLUGINS}/dummy-settings-app`.
- Automated UI confidence currently includes:
  - mocked React Native component test for rendering and mutation
  - real-backend React Native component integration that starts the Python server, renders server-scoped dummy settings, excludes a session-scoped dummy setting, and patches `/server/settings`
- Remaining Stage 1 work after this checkpoint:
  - sleep-prevention application plugin consumer
  - docs/final documentation updates