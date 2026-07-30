# Sleep Prevention Application Plugin
Implement the first real server-settings application plugin consumer: a sleep-prevention plugin that can be toggled from live server settings and uses `caffeinate` on macOS or `wakepy` elsewhere.

## Requirements checklist

- [x] Add a first-party `plugins/sleep-prevention-app` application plugin package.
- [x] Expose a server-scoped `sleep_prevention_enabled` setting through application plugin UI schema.
- [x] React idempotently to `server_settings_changed` lifecycle events and startup replay.
- [x] Use macOS `caffeinate` with configurable flags from application config and default `-is`.
- [x] Use `wakepy` on non-macOS platforms without requiring it on macOS.
- [x] Release any active sleep-prevention hold when the application/plugin closes.
- [x] Add unit and integration-style tests with OS/process behavior mocked.
- [x] Document configuration, setting key, and platform behavior.

Parent Task: `tasks/20260421-server-settings-bridge-sync/000-main.md`

Depends On: `tasks/20260421-server-settings-bridge-sync/010-live-server-settings-and-lifecycle.md`

## Execution plan

Added during completion after user approval.

1. Create a standard first-party plugin project at `plugins/sleep-prevention-app` with `agent_plugin.json`, `pyproject.toml`, README, source package, and tests.
2. Implement `SleepPreventionAppPlugin` as an application plugin:
   - `get_ui_elements(...)` returns a server-scoped checkbox keyed `sleep_prevention_enabled`.
   - `get_actions(...)` registers an `apply_sleep_prevention` action triggered by `server_settings_changed`.
   - `execute_action(...)` reads `context["new_settings"]` or falls back to `app.get_server_settings()`, then applies the desired enabled state idempotently.
3. Add a small sleep-prevention controller layer:
   - macOS controller starts `caffeinate` through `subprocess.Popen`.
   - default macOS flags are `-is`.
   - flags can be overridden from application plugin config.
   - non-macOS controller lazy-imports `wakepy` and activates/releases it.
4. Add backward-compatible plugin cleanup support:
   - `ApplicationPluginWrapper.close()` calls optional plugin close hooks.
   - `AgentApplication.close()` closes application plugins before runtime resources.
   - FastAPI shutdown closes the global `AgentApplication` so server mode releases holds.
5. Add tests:
   - plugin UI schema and lifecycle idempotency.
   - configurable `caffeinate` flags and process release with mocked `Popen`.
   - wakepy activation/release with mocked import/controller behavior.
   - application/plugin close releases an active hold.
   - plugin can be loaded by `path:${env:BUILTIN_PLUGINS}/sleep-prevention-app` and responds to server settings lifecycle.
6. Update docs:
   - plugin README with config example and platform behavior.
   - canonical plugin docs only if cleanup hook or lifecycle behavior needs a central mention.
7. Run targeted verification:
   - plugin tests.
   - core application plugin/server-settings tests.
   - application server settings tests if shutdown/route behavior changes.

## Implementation notes

- Keep bridge sync and macOS scheduled wake out of this plugin; those belong to later subtasks.
- The plugin owns only live OS sleep-prevention behavior for the current server process.
- Generic server-settings UI behavior remains tested with `DummySettingsAppPlugin`, not this plugin.

## Completion Notes

Added during completion.

- Added `plugins/sleep-prevention-app` as a first-party application plugin package.
- The plugin exposes `sleep_prevention_enabled` as a server-scoped checkbox and applies it from `server_settings_changed`.
- macOS uses `caffeinate` with configurable application config flags:
  - flat: `application.sleep_prevention_caffeinate_flags`
  - nested: `application.sleep_prevention.caffeinate_flags`
  - default: `-is`
- Non-macOS uses a lazy `wakepy.keep.running()` controller so macOS does not need wakepy installed.
- Added optional app-plugin cleanup support through `ApplicationPluginWrapper.close()` and `AgentApplication.close()`, and FastAPI shutdown now closes the global application.
- Added mocked tests for plugin UI schema, lifecycle toggling, startup replay context, `caffeinate`, `wakepy`, path loading, and cleanup.

## Follow-up Completion Notes

Added during follow-up for unreliable `caffeinate` stopping.

- Fixed combined `--console --server` ownership so only the server-side `AgentApplication` replays persisted server settings on startup; the terminal companion app no longer starts a duplicate sleep-prevention hold.
- Added deterministic close paths for contributed commands, console-only mode, and combined console/server mode, plus idempotent `AgentApplication.close()`.
- Added a subprocess CLI integration fixture using a dummy application plugin to verify generic startup lifecycle replay and close behavior.
- Added a macOS CLI integration test that starts with persisted `sleep_prevention_enabled`, toggles it off through the HTTP server settings route, and verifies all child `caffeinate` processes are released.
- Added a real macOS `CaffeinateSleepPreventionController` integration test gated by platform and `caffeinate` availability.
