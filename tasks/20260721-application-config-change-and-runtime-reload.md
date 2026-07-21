# Support Application Configuration Changes and Runtime Reload

Enable applications and HTTP clients to change application-level configuration and reload the `AgentApplication` runtime. Support both first-class configuration capabilities and plugin-driven application actions, including a UI path for setting provider API keys whose changes take effect after reload. The implementation approach is intentionally open.

## Requirements checklist

- [ ] Provide an `AgentApplication`-level capability to change application configuration while the application is running.
- [ ] Provide a public server/API path to perform the supported configuration change and reload flow.
- [ ] Provide runtime reload support so successfully applied application configuration changes affect subsequent application behavior.
- [ ] Define and implement clear success, validation-failure, and reload-failure behavior for configuration changes.
- [ ] Ensure configuration changes can affect application-level concerns, including available agents, rather than being limited to per-session overrides.
- [ ] Support plugin-driven custom application logic through application-level actions alongside any first-class configuration/update capability.
- [ ] Assess and extend the existing application-action protocol, action execution path, HTTP action support, and UI-schema support where needed; do not require configuration changes themselves to be exclusively plugin-driven.
- [ ] Provide a UI-supported flow for setting a provider API key, applying the corresponding application-level configuration change, and reloading so that the changed key is used by the applicable runtime configuration.
- [ ] Preserve the existing configuration-resolution behavior for API keys and other environment-backed configuration inputs unless the chosen implementation intentionally changes it and documents the compatibility implications.
- [ ] Verify the capability through application-layer tests, HTTP/server tests, and a frontend flow using the production backend adapter.
- [ ] Document the public application and server interfaces, reload behavior, and any relevant configuration lifecycle constraints.

## Scope and Design Freedom

This task defines outcomes, not a required design. The implementation may use first-class `AgentApplication` APIs, application-plugin actions, server settings, another supported configuration representation, or a combination of these.

The task does not prescribe endpoint names, configuration storage, secret handling, UI layout, reload internals, or which configuration fields must be mutable beyond the required API-key and application-level agent-availability scenarios.

## Existing Architecture and Research

`AgentApplication` currently reads and resolves its configuration during construction, initializes plugins, and derives agent/runtime caches at startup. It has no general application-configuration update or runtime-reload operation. Relevant code:

- `core/python/agent_app/application_future.py:328-686`
- `core/python/agent_app/config.py:30-80`

The constructor accepts `env_overrides`, but those values are used during initial configuration resolution and runtime environment overlay setup. This task must account for that existing environment-backed configuration path without assuming a particular replacement or persistence mechanism.

Application-level plugins and actions already exist. `ApplicationPlugin` supplies action definitions and action execution; `AgentApplication` exposes action discovery/execution; and the terminal HTTP server lists application actions at `/application/actions` and executes actions at `/actions`. Relevant code:

- `core/python/agent_app/app_plugins.py:22-119`
- `core/python/agent_app/application_future.py:2332-2411`
- `application/python/agent_terminal_app/server.py:2700-2759`
- `application/python/agent_terminal_app/server.py:2881-2913`

The existing server-settings facility is separately persisted and exposed through `/server/settings`. It emits a `server_settings_changed` application lifecycle event, but does not change the resolved application configuration or reload the application runtime. Relevant code:

- `core/python/agent_app/application_future.py:1609-1737`
- `application/python/agent_terminal_app/server.py:1307-1554`
- `packages/frontend-sdk/src/backend/restBackend.ts:562-607`
- `mobile/crystal-lattice-control-rn/src/components/ServerSettingsModal.tsx:44-244`

Existing session overrides are not a substitute for this task: they are stored on one session and merged into that session's request configuration. Application-level agent availability derives from the resolved top-level configuration. Relevant code:

- `core/python/agent_app/application_future.py:1165-1194`
- `core/python/agent_app/application_future.py:2240-2247`
- `core/python/agent_app/config.py:687-699`

## Related Work

The iOS App Review local-runtime task depends on this generic capability:

- `tasks/20260614-ios-testflight-github-fastlane/085-app-review-local-runtime-and-testable-mode.md`