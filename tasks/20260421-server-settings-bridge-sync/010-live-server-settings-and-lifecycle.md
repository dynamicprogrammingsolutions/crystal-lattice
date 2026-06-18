# Stage 1: Live Server Settings And Lifecycle
Build a complete live server-settings slice that is testable from the mobile UI over an active connection, while also adding lifecycle hooks for both session and server settings changes.

## Requirements checklist

- [x] Add `AgentApplication`-owned persisted server settings helpers instead of storing server-global settings in FastAPI route code.
- [x] Refactor session override mutation paths so session settings writes go through `AgentApplication` helpers and can fire lifecycle triggers.
- [x] Add lifecycle support for `session_settings_changed` and `server_settings_changed` with useful JSON-serializable context.
- [x] Add live server settings HTTP routes that mirror the existing session settings routes.
- [x] Extend the frontend SDK with server settings backend methods and a live server settings controller modeled after the session settings controller.
- [x] Add a minimal mobile server settings modal reachable from the connected sessions screen.
- [x] Implement the first application plugin consumer: sleep prevention with `caffeinate` on macOS and `wakepy` elsewhere.
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

## Follow-up: application UI context and shared modal frame

Added after user approval as a follow-up plan. Stop before implementation until final implementation approval.

This follow-up corrects the server settings UI schema semantics and standardizes the mobile modal layout.

The current server settings UI path must not treat server settings as `config`. Config remains real agent/session configuration. Server settings should be available to application plugins through the shared context channel used by other plugin methods.

### Follow-up implementation checklist

- [x] Update the application-plugin UI schema protocol and wrapper to support the new `get_ui_elements(config, context=None)`-style shape while preserving old signatures.
- [x] Build application UI context consistently, including `config`, `tags`, `models`, and server settings where applicable.
- [x] Add an app-layer server settings UI schema method and thin HTTP route.
- [x] Extend the frontend SDK backend interface and REST backend for server settings UI schema.
- [x] Fix server settings controller mutation/reload semantics to mirror session settings.
- [x] Update the dummy settings app plugin to use plugin-side dynamic UI based on context.
- [x] Add shared React Native modal frame components and migrate the relevant popups.
- [x] Update canonical plugin documentation for the new application UI context contract.
- [x] Add Python, SDK, and React Native tests for the follow-up behavior.

### 1. Update application-plugin UI schema protocol shape

Change the application plugin UI method toward the same modern shape as core plugin UI methods:

```python
def get_ui_elements(
    self,
    config: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    ...
```

For application plugins, `config` may still be `{}` when the UI surface is not tied to an agent/session config, but it remains config, not settings.

Keep backward compatibility in the wrapper for existing signatures:

- `get_ui_elements()`
- `get_ui_elements(state)`
- `get_ui_elements(state, config)`
- `get_ui_elements(state, config, tags, models)`
- the new preferred shape with context support

Because application plugins currently receive `state` first, the wrapper remains the compatibility adapter. The preferred plugin author shape should be documented clearly as:

```python
def get_ui_elements(
    self,
    state: dict[str, Any],
    config: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    ...
```

Avoid keeping `tags` and `models` as preferred positional arguments. They should live in `context`, while old positional `tags`/`models` remain supported for compatibility.

### 2. Prepare context consistently

Add an application UI context builder, similar to the existing lifecycle/tool/action context builders.

For ordinary application UI schema:

```python
context = {
    "app": app,
    "application": app,
    "trigger_source": "application",
    "ui_context": "application",
    "config": config,
    "tags": tags,
    "models": models,
}
```

For session application UI schema:

```python
context = {
    "app": app,
    "application": app,
    "trigger_source": "application",
    "ui_context": "session",
    "session": session.to_dict(),
    "session_id": session.session_id,
    "config": effective_config,
    "base_config": base_config,
    "tags": tags,
    "models": models,
}
```

For server settings UI schema:

```python
context = {
    "app": app,
    "application": app,
    "trigger_source": "application",
    "ui_context": "server_settings",
    "settings_scope": "server",
    "config": {},
    "tags": [],
    "models": [],
    "settings": server_settings,
    "server_settings": server_settings,
}
```

This gives plugins a clean semantic split:

- `config`: actual agent/session config
- `tags`: capability tags
- `models`: model descriptors
- `server_settings`: persisted server settings
- `settings`: generic alias for the active settings scope

### 3. Add app-layer method for server settings UI schema

Add:

```python
AgentApplication.get_server_settings_ui_schema()
```

It should:

- call `get_server_settings()`
- build the server settings UI context
- call `get_application_ui_schema(config={}, context=context)`
- return normalized application plugin UI elements

No logic should live in HTTP besides response/error formatting.

### 4. Add dedicated HTTP endpoint

Add:

```text
GET /server/settings/ui-schema
```

It returns:

```json
{
  "elements": []
}
```

This avoids overloading `/application/ui-schema` and avoids query params with ambiguous `scope`.

### 5. Update frontend SDK backend

Add optional backend method:

```ts
listServerSettingsUiSchema?(): Promise<ApplicationUiElement[]>
```

Implement in `RestAgentBackend` against:

```text
GET /server/settings/ui-schema
```

Keep `listApplicationUiSchema()` unchanged.

### 6. Fix server settings controller reload behavior

Update `ServerSettingsController.load()` to fetch:

- `getServerSettings()`
- `listServerSettingsUiSchema()`

The UI schema endpoint itself reads current server settings and passes them as context, so it may be loaded in parallel with settings. After mutation, the controller must wait for persistence first.

Fix the current race:

```ts
await backend.patchServerSettings(...)
await backend.deleteServerSetting(...)
```

Then:

- mark saved
- trigger background `load()`

This should mirror the session settings controller.

Optionally add server settings invalidation parity:

- `emitServerSettingsInvalidated`
- `subscribeServerSettingsInvalidated`
- REST backend emits after patch/delete
- `useServerSettingsController` subscribes and reloads

### 7. Update dummy settings plugin

Change `DummySettingsAppPlugin.get_ui_elements` to use the new context shape.

Example:

```python
def get_ui_elements(
    self,
    state: dict[str, Any],
    config: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    ctx = context or {}
    server_settings = ctx.get("server_settings") or {}
    show_more = bool(server_settings.get("dummy_show_more_parameters"))
```

Always return:

- `dummy_show_more_parameters`

Return many extra server-scoped controls only when `show_more` is true.

Do not use frontend-side `condition` for this behavior. The plugin decides what schema to return.

### 8. Shared modal frame

Create reusable React Native modal pieces:

- centered fade modal surface
- panel/header frame using the session-actions close style

Use them for:

- `SessionSettingsModal`
- `SessionPluginsModal`
- `ServerSettingsModal`

Close style:

- title left
- `Close` text button right
- primary text
- divider below header, matching the session actions modal

For `ApplicationActionDialog`, only reuse the lower-level centered modal surface if practical:

- keep OK/Cancel behavior
- keep keyboard avoiding
- avoid adding another close mechanism

### 9. Documentation

Update canonical docs in `plugins/docs`:

- `application-plugins.md`
  - document new preferred `get_ui_elements(state, config=None, context=None)` shape
  - document backward-compatible signatures
  - document `context["config"]`, `context["tags"]`, `context["models"]`, and `context["server_settings"]`
- `ui-elements.md`
  - document server settings UI schema endpoint
  - clarify plugin-side dynamic UI via context, not frontend-side conditions
- `actions.md`
  - update only if needed for lifecycle cross-reference

### 10. Tests

Python:

- application plugin wrapper passes `context` into a new-shape plugin
- old-shape app plugins still work
- `AgentApplication.get_server_settings_ui_schema()` includes `server_settings` in context
- `GET /server/settings/ui-schema` returns dynamic dummy plugin controls
- dummy plugin extras appear only after `dummy_show_more_parameters=true`

SDK:

- REST backend calls `/server/settings/ui-schema`
- `ServerSettingsController` awaits patch/delete before reload
- schema changes after server settings mutation

Mobile:

- modal frame renders header `Close`
- session settings/plugins still render
- server settings modal is centered, not bottom sheet
- dummy extras hidden initially
- toggling `Show more parameters` causes reload and shows extras
- scroll body exists when extras are visible

This keeps the contract clean: `config` remains config, dynamic server settings UI uses `context`, and the wrapper preserves old plugin signatures.

## Follow-up Completion Notes

Added during follow-up implementation.

- Application plugin UI schema now receives layered application context, with backward compatibility for old UI element signatures.
- Server settings UI schema is exposed through `AgentApplication.get_server_settings_ui_schema()` and `GET /server/settings/ui-schema`; HTTP remains a thin formatter.
- Frontend SDK and REST backend now have `listServerSettingsUiSchema()`, plus server settings invalidation matching the session UI schema invalidation pattern.
- `ServerSettingsController` now awaits patch/delete mutations before scheduling reload, so plugin-driven schema changes can appear after settings changes.
- `DummySettingsAppPlugin` now uses `context["server_settings"]` to decide whether to return extra server-scoped controls.
- Mobile server/session settings and plugins popups now share a centered modal frame with the session-actions-style header close button. The action dialog was left unchanged because it lives in the shared RN package and has OK/Cancel form semantics.
- Canonical plugin docs in `plugins/docs` were updated for the context-aware application UI contract and server settings schema endpoint.
- Follow-up verification passed for targeted Python tests, SDK tests, React hook tests, mobile component tests, and the real-backend mobile component integration. Mobile `tsc` still fails on the pre-existing `AnimatedSplashScreen`/`AppLogoProps` issue.
- After review, session application UI schema assembly was centralized in `AgentApplication`; HTTP and terminal callers now delegate instead of resolving config/tags/models themselves.
- The remaining sleep-prevention consumer was split into and completed through `tasks/20260421-server-settings-bridge-sync/015-sleep-prevention-app.md`.
- Snapshot popup follow-up extracted the snapshots modal to the shared popup frame and restored the pre-`25d3b9aa` vertical snapshot item layout while keeping per-snapshot action buttons horizontal.